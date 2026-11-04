"""
Retrieval-Augmented Generation layer for BRANDVAULT AI (Milestone C).

What this is, honestly:
- Real vector-space retrieval over persisted `document_chunks`: each chunk is
  embedded as an L2-normalized TF-IDF sparse vector; queries are embedded the
  same way; ranking is brute-force cosine similarity combined with a keyword
  overlap score (hybrid retrieval). Results are filtered by organisation and
  guideline status (tenant isolation).
- This is a *statistical* embedding (TF-IDF), not a neural sentence embedding.
  It is deterministic, offline, and dependency-free — a genuine improvement over
  plain token-overlap (IDF weighting + cosine normalisation), but it is not a
  semantic transformer model. Labelled as such everywhere it surfaces.

Swap path (Roadmap): the `Embedder` interface and `RagRetriever` are written so a
neural embedder (sentence-transformers / provider embeddings) or a pgvector-backed
store can replace the default without changing callers — implement `Embedder.embed`
and the vector persistence, keep the same `search()` contract.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.models.brand import DocumentChunk, BrandGuideline

_TOKEN_RE = re.compile(r"[a-z0-9']+")
_ACTIVE_STATUSES = ("processed", "active", "uploaded")


def tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall((text or "").lower())


class Embedder:
    """Embedder interface. Returns an L2-normalized sparse vector (token -> weight)."""
    name: str = "base"

    def embed(self, text: str, idf: Dict[str, float]) -> Dict[str, float]:
        raise NotImplementedError


class TfidfEmbedder(Embedder):
    """TF-IDF embedder: sublinear TF * IDF, L2-normalized. Keyed by token for
    reproducible persistence (no per-process hash salt)."""
    name = "tfidf"

    def embed(self, text: str, idf: Dict[str, float]) -> Dict[str, float]:
        tokens = tokenize(text)
        if not tokens:
            return {}
        tf = Counter(tokens)
        default_idf = max(idf.values()) if idf else 1.0
        vec: Dict[str, float] = {}
        for term, count in tf.items():
            weight = (1.0 + math.log(count)) * idf.get(term, default_idf)
            if weight:
                vec[term] = weight
        norm = math.sqrt(sum(w * w for w in vec.values()))
        if norm == 0:
            return {}
        return {t: w / norm for t, w in vec.items()}


def cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Dot product of two L2-normalized sparse vectors == cosine similarity."""
    if not a or not b:
        return 0.0
    # iterate the smaller dict
    if len(a) > len(b):
        a, b = b, a
    return sum(w * b.get(t, 0.0) for t, w in a.items())


class RagRetriever:
    def __init__(self, db: Session, embedder: Optional[Embedder] = None, keyword_weight: float = 0.35):
        self.db = db
        self.embedder = embedder or TfidfEmbedder()
        self.keyword_weight = keyword_weight

    def _corpus(self, org_id: str) -> List[DocumentChunk]:
        """Org-isolated, status-filtered chunk corpus."""
        return (
            self.db.query(DocumentChunk)
            .join(DocumentChunk.guideline)
            .filter(
                DocumentChunk.guideline.has(org_id=org_id),
                DocumentChunk.guideline.has(BrandGuideline.status.in_(_ACTIVE_STATUSES)),
            )
            .all()
        )

    def _build_idf(self, chunks: List[DocumentChunk]) -> Dict[str, float]:
        n = len(chunks)
        df: Counter = Counter()
        for ch in chunks:
            for term in set(tokenize(ch.content)):
                df[term] += 1
        # smoothed idf, always >= 1
        return {term: math.log((1 + n) / (1 + d)) + 1.0 for term, d in df.items()}

    def _vectorize_corpus(self, org_id: str) -> Tuple[Dict[str, float], List[Tuple[DocumentChunk, Dict[str, float]]]]:
        chunks = self._corpus(org_id)
        idf = self._build_idf(chunks)
        vectors = [(ch, self.embedder.embed(ch.content, idf)) for ch in chunks]
        return idf, vectors

    def index_org(self, org_id: str) -> int:
        """Persist each chunk's embedding into document_chunks.embedding_json.
        Returns the number of chunks indexed. Satisfies 'store vectors'."""
        idf, vectors = self._vectorize_corpus(org_id)
        count = 0
        for ch, vec in vectors:
            payload = {
                "embedder": self.embedder.name,
                "dims": len(vec),
                # round to keep the stored vector compact
                "vector": {t: round(w, 5) for t, w in sorted(vec.items(), key=lambda kv: -kv[1])[:40]},
            }
            ch.embedding_json = json.dumps(payload)
            count += 1
        self.db.commit()
        return count

    def search(self, org_id: str, query: str, top_k: int = 3) -> List[Dict]:
        """Hybrid (cosine + keyword) ranked retrieval, org-isolated."""
        idf, vectors = self._vectorize_corpus(org_id)
        if not vectors:
            return []
        q_vec = self.embedder.embed(query, idf)
        q_tokens = set(tokenize(query))
        results = []
        for ch, c_vec in vectors:
            cos = cosine(q_vec, c_vec)
            c_tokens = set(tokenize(ch.content))
            kw = (len(q_tokens & c_tokens) / len(q_tokens)) if q_tokens else 0.0
            score = (1 - self.keyword_weight) * cos + self.keyword_weight * kw
            if score <= 0:
                continue
            guideline = ch.guideline
            filename = guideline.filename if guideline else "Brand Guideline"
            results.append({
                "chunk_id": ch.id,
                "filename": filename,
                "page": ch.page_number,
                "content": ch.content,
                "citation": f"{filename} (Page {ch.page_number})",
                "score": round(score, 4),
                "cosine": round(cos, 4),
                "keyword": round(kw, 4),
                "embedder": self.embedder.name,
            })
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]

    def best(self, org_id: str, query: str) -> Optional[Dict]:
        hits = self.search(org_id, query, top_k=1)
        return hits[0] if hits else None
