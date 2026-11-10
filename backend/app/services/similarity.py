"""
Content Similarity Detector.

Finds duplicate, near-duplicate and reused marketing content inside an
organisation: campaign submissions, approved passport versions and translation
sources — plus image near-duplicates against stored assets and investigation
uploads. Methods are explicit and reported per match:

  exact       canonical SHA-256 of the normalised text
  shingles    Jaccard overlap of 3-word sequences (near-duplicate wording)
  tfidf       cosine similarity of TF-IDF vectors (same topic / vocabulary)
  sentences   identical or near-identical sentences (reused taglines, headlines)
  image       perceptual + difference hash distance

Similarity is evidence for investigation, not a copyright or plagiarism ruling.
"""
from __future__ import annotations

import difflib
import math
import re
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from backend.app.models.intelligence import SimilarityDismissal
from backend.app.models.multilingual import MultilingualCampaign
from backend.app.models.passport import BrandPassport
from backend.app.models.submission import Submission
from backend.app.services.passport_service import normalise_content, content_sha256

_WORD = re.compile(r"[\w₹%]+", re.UNICODE)
_SENT = re.compile(r"(?<=[.!?।。])\s+|\n+")
_STOP = set("the a an and or of to in for on with at by is are be this that it your our you we from as now only".split())

NEAR_DUP = 0.5      # shingle Jaccard
SIMILAR = 0.35      # tf-idf cosine
SENT_MATCH = 0.9    # sentence ratio


def _tokens(t: str) -> List[str]:
    return [w.lower() for w in _WORD.findall(t)]


def _shingles(t: str, n: int = 3) -> Set[Tuple[str, ...]]:
    w = _tokens(t)
    return {tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1))} or ({tuple(w)} if w else set())


def _jaccard(a: Set, b: Set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _sentences(t: str) -> List[str]:
    return [s.strip() for s in _SENT.split(t) if len(_tokens(s)) >= 4]


class Corpus:
    """Org-scoped comparison corpus with an in-memory TF-IDF model."""

    def __init__(self, db: Session, org_id: str):
        self.docs: List[dict] = []
        for s in db.query(Submission).filter(Submission.org_id == org_id).all():
            self.docs.append({"kind": "submission", "id": s.id, "title": s.title, "text": s.content, "status": s.status,
                              "date": s.created_at.isoformat() if s.created_at else None, "author": s.author_name})
        for p in (db.query(BrandPassport).join(Submission, BrandPassport.submission_id == Submission.id)
                  .filter(Submission.org_id == org_id).all()):
            content = (p.passport_data or {}).get("content")
            if content:
                self.docs.append({"kind": "passport", "id": p.id, "title": f"{p.passport_number} · {p.content_title}",
                                  "text": content, "status": p.verification_status,
                                  "date": p.issued_at.isoformat() if p.issued_at else None, "author": p.audited_by,
                                  "submission_id": p.submission_id})
        for c in db.query(MultilingualCampaign).filter(MultilingualCampaign.org_id == org_id).all():
            self.docs.append({"kind": "translation_source", "id": c.id, "title": c.title, "text": c.source_text,
                              "status": c.verdict, "date": c.created_at.isoformat() if c.created_at else None,
                              "author": c.created_by_name})
        for d in self.docs:
            d["sha"] = content_sha256(d["text"])
            d["shingles"] = _shingles(d["text"])
            d["sentences"] = _sentences(d["text"])
        df = Counter()
        for d in self.docs:
            df.update({w for w in _tokens(d["text"]) if w not in _STOP})
        self.n = max(1, len(self.docs))
        self.idf = {w: math.log((1 + self.n) / (1 + c)) + 1 for w, c in df.items()}
        for d in self.docs:
            d["vec"] = self.vector(d["text"])

    def vector(self, text: str) -> Dict[str, float]:
        tf = Counter(w for w in _tokens(text) if w not in _STOP)
        v = {w: c * self.idf.get(w, math.log(1 + self.n) + 1) for w, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {w: x / norm for w, x in v.items()}


def _cos(a: Dict[str, float], b: Dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(w, 0.0) for w, x in a.items())


def pair_key(a: str, b: str) -> str:
    return "|".join(sorted([a, b]))


def _matching_sentences(src: List[str], other: List[str]) -> List[dict]:
    out = []
    for s in src:
        for o in other:
            r = difflib.SequenceMatcher(None, s.lower(), o.lower()).ratio()
            if r >= SENT_MATCH:
                out.append({"submitted": s, "existing": o, "similarity": round(r, 3)})
                break
    return out[:6]


def classify(exact: bool, jac: float, cos: float, sents: List[dict]) -> Optional[str]:
    if exact:
        return "Exact duplicate"
    if jac >= NEAR_DUP:
        return "Near-duplicate"
    if sents:
        return "Reused tagline or sentence"
    if cos >= SIMILAR:
        return "Similar content"
    return None


def check_text(db: Session, org_id: str, text: str, exclude: Optional[Set[str]] = None,
               self_key: Optional[str] = None, include_dismissed: bool = False) -> dict:
    corpus = Corpus(db, org_id)
    exclude = exclude or set()
    sha = content_sha256(text)
    sh, sents, vec = _shingles(text), _sentences(text), corpus.vector(text)
    me = self_key or f"text:{sha}"
    dismissed = {d.pair_key: d for d in db.query(SimilarityDismissal).filter(SimilarityDismissal.org_id == org_id).all()}
    matches = []
    for d in corpus.docs:
        ref = f"{d['kind']}:{d['id']}"
        if ref in exclude:
            continue
        exact = d["sha"] == sha
        jac, cos = _jaccard(sh, d["shingles"]), _cos(vec, d["vec"])
        ms = _matching_sentences(sents, d["sentences"])
        label = classify(exact, jac, cos, ms)
        if not label:
            continue
        pk = pair_key(me, ref)
        dis = dismissed.get(pk)
        if dis and not include_dismissed:
            continue
        overall = 1.0 if exact else round(max(jac, cos), 3)
        matches.append({
            "kind": d["kind"], "id": d["id"], "ref": ref, "pair_key": pk, "title": d["title"], "status": d["status"],
            "date": d["date"], "author": d.get("author"), "submission_id": d.get("submission_id", d["id"] if d["kind"] == "submission" else None),
            "label": label, "similarity": overall,
            "methods": {"exact": exact, "shingle_jaccard": round(jac, 3), "tfidf_cosine": round(cos, 3), "matching_sentences": len(ms)},
            "matching_sentences": ms, "excerpt": d["text"][:300],
            "dismissed": bool(dis), "dismissed_reason": dis.reason if dis else None,
            "recommendation": _recommend(label, d),
        })
    order = {"Exact duplicate": 0, "Near-duplicate": 1, "Reused tagline or sentence": 2, "Similar content": 3}
    matches.sort(key=lambda m: (order[m["label"]], -m["similarity"]))
    return {"sha256": sha, "matches": matches, "compared": len(corpus.docs) - len(exclude),
            "thresholds": {"near_duplicate_jaccard": NEAR_DUP, "similar_tfidf_cosine": SIMILAR, "sentence_ratio": SENT_MATCH},
            "note": "Similarity is evidence for investigation, not a copyright or plagiarism determination."}


def _recommend(label: str, d: dict) -> str:
    if label == "Exact duplicate":
        return ("This exact text already exists" + (" and is approved — reuse the approved version instead of re-submitting."
                                                  if d["kind"] == "passport" else ". Check whether this is an accidental re-submission."))
    if label == "Near-duplicate":
        return "Mostly the same wording as an existing campaign. Confirm the differences are intended and re-check claims that changed."
    if label == "Reused tagline or sentence":
        return "A sentence is reused. Reuse is fine for approved taglines; otherwise confirm it is meant to repeat."
    return "Covers the same topic and vocabulary. Usually fine — check it does not repeat a rejected or outdated message."


def _similar_pairs(docs: List[dict], threshold: float):
    """Pairs (i, j) with identical text or shingle Jaccard >= threshold.

    Prefix filtering: order each set's shingles from rarest to most common; two sets
    with Jaccard >= t must share a shingle within the first |s| - ceil(t*|s|) + 1 of
    each. Only those candidates are compared exactly, so the result equals the
    all-pairs comparison while skipping almost every pair.
    """
    by_sha: Dict[str, int] = {}
    for i, d in enumerate(docs):
        if d["sha"] in by_sha:
            yield by_sha[d["sha"]], i
        else:
            by_sha[d["sha"]] = i
    freq = Counter(sh for d in docs for sh in d["shingles"])
    index: Dict[tuple, List[int]] = {}
    for i, d in enumerate(docs):
        s = d["shingles"]
        if not s:
            continue
        ordered = sorted(s, key=lambda sh: (freq[sh], sh))
        prefix = ordered[:len(s) - math.ceil(threshold * len(s)) + 1]
        seen = set()
        for sh in prefix:
            for j in index.get(sh, ()):
                if j in seen:
                    continue
                seen.add(j)
                o = docs[j]["shingles"]
                if min(len(s), len(o)) >= threshold * max(len(s), len(o)) and _jaccard(s, o) >= threshold:
                    yield j, i
            index.setdefault(sh, []).append(i)


def clusters(db: Session, org_id: str, threshold: float = NEAR_DUP) -> List[dict]:
    """Groups of submissions with near-duplicate wording (union-find)."""
    corpus = Corpus(db, org_id)
    subs = [d for d in corpus.docs if d["kind"] == "submission"]
    parent = list(range(len(subs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in _similar_pairs(subs, threshold):
        parent[find(i)] = find(j)
    groups: Dict[int, List[dict]] = {}
    for i, d in enumerate(subs):
        groups.setdefault(find(i), []).append(d)
    out = []
    for g in groups.values():
        if len(g) < 2:
            continue
        g.sort(key=lambda d: d["date"] or "")
        exact = len({d["sha"] for d in g}) == 1
        out.append({"size": len(g), "exact_duplicates": exact, "first_seen": g[0]["date"],
                    "representative": g[0]["text"][:200],
                    "members": [{"id": d["id"], "title": d["title"], "status": d["status"], "date": d["date"]} for d in g]})
    return sorted(out, key=lambda c: -c["size"])
