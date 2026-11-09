"""
Brand Digital Twin Q&A (Round 2 / R2-3).

Answers natural-language questions about an organisation's brand **only from its
approved data** — brand rules, approved facts, terminology, guideline evidence,
and the organisation's own analysis history. It is grounded and honest:

  * Deterministic keyword intent-routing (no hidden model); every answer is
    assembled from real records and carries citations to them.
  * When nothing in the approved data matches, it says so plainly instead of
    inventing an answer.
  * Read-only and organisation-scoped (tenant isolation) — it never performs an
    action and never reaches outside the org's approved knowledge.

An LLM could later *phrase* these grounded answers (behind the existing
`services/llm.py` fallback) without changing the evidence contract; the default
here is fully deterministic.
"""
from __future__ import annotations

import datetime
import re
from collections import Counter
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.brand import Organization, BrandRule, ApprovedFact, TerminologyRule
from backend.app.models.submission import Submission
from backend.app.services.rag import RagRetriever
from backend.app.services import claim_patterns as cp
from backend.app.services.llm import get_llm_provider

SUGGESTIONS = [
    "What is the approved launch price?",
    "Which brand rules are most often violated?",
    "What terms are prohibited?",
    "Which claims and facts are approved?",
    "Explain our brand voice and tone.",
    "What are our active brand rules?",
]


def _ev(label: str, detail: str = "", source: str = "", href: str = "/brand-dna", page: Optional[int] = None) -> dict:
    return {"label": label, "detail": detail, "source": source, "href": href, "page": page}


def _has(q: str, *terms: str) -> bool:
    return any(t in q for t in terms)


_STOPWORDS = {
    "what", "which", "where", "when", "whom", "whose", "does", "do", "did", "is", "are", "was",
    "were", "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "our", "we", "us",
    "you", "your", "about", "tell", "me", "say", "says", "with", "that", "this", "it", "can",
    "how", "why", "who", "has", "have", "be", "will", "would", "should", "could", "from", "at",
    # conversational filler that says nothing about the topic
    "quick", "check", "please", "cite", "source", "sources", "hello", "thanks", "thank", "kindly", "just",
    "next", "last", "this", "there", "here", "some", "many", "much",
}


def _stems(words: set) -> set:
    return {w[:5] for w in words}


def _relevant(qwords: set, passage: str) -> bool:
    """A passage answers the question only if it shares at least two topic words
    with it (or the only one, for a one-topic-word question)."""
    overlap = _stems(qwords) & _stems(_content_words(passage))
    return len(overlap) >= min(2, len(qwords)) and bool(overlap)


_NOT_OUR_PRICE = re.compile(r"\b(stock|share)\s+price\b|\bmarket\s+cap|\bshare\s+value\b")


def _content_words(text: str) -> set:
    """Meaningful (non-stopword) terms of length >= 4 — used to gate retrieval
    relevance so stopword-only overlap never counts as a grounded answer."""
    return {w for w in re.findall(r"[a-z0-9']+", (text or "").lower()) if len(w) >= 4 and w not in _STOPWORDS}


_PHRASE_SYSTEM = (
    "You rephrase a brand-governance answer so it reads naturally and concisely. "
    "STRICT RULES: use ONLY the information in the provided answer and sources. Do "
    "NOT add, infer, invent or change any fact, number, name, price or claim. If "
    "something isn't in the provided text, don't say it. Keep it accurate, "
    "professional and under about four sentences. Return only the rephrased answer "
    "text — no preamble, no markdown."
)


def _llm_phrase(provider, question: str, answer: str, evidence: list) -> Optional[str]:
    """Ask the LLM to rephrase a grounded answer — never to add information.
    Returns the rephrased text, or None on any failure (caller keeps the
    deterministic answer)."""
    try:
        src = "\n".join(
            f"- {e.get('label','')}: {e.get('detail','')}" + (f" (source: {e.get('source')})" if e.get("source") else "")
            for e in (evidence or [])[:8]
        ) or "(no additional sources)"
        user = (
            f"User question: {question}\n\n"
            f"Grounded answer to rephrase (do not add anything beyond this):\n{answer}\n\n"
            f"Sources (context only — do not fabricate beyond these):\n{src}"
        )
        text = provider.analyze(_PHRASE_SYSTEM, user)
        if not text:
            return None
        text = text.strip().strip("`").strip()
        # Guard against the model returning something empty or absurdly long.
        if len(text) < 2 or len(text) > 4000:
            return None
        return text
    except Exception:
        return None


def answer_question(db: Session, org_id: str, question: str) -> Optional[dict]:
    """Grounded answer, then (optionally) phrased by the LLM. The evidence and
    grounding are computed deterministically from real records; the LLM only
    makes the prose natural and never adds facts. Falls back to the deterministic
    answer if no LLM is configured or the call fails."""
    result = _grounded_answer(db, org_id, question)
    if result is None:
        return None
    # Only rephrase real, grounded answers — never the honest "not in approved
    # data" refusals, and never when there's nothing to say.
    if result.get("grounded") and result.get("intent") not in ("empty",):
        provider = get_llm_provider(settings)
        if provider.available:
            phrased = _llm_phrase(provider, question, result["answer"], result.get("evidence", []))
            if phrased:
                result["answer"] = phrased
                result["phrased_by"] = f"llm:{provider.name}"
                result["model"] = provider.model
    return result


def _grounded_answer(db: Session, org_id: str, question: str) -> Optional[dict]:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return None

    q = (question or "").lower().strip()
    if not q:
        return {"intent": "empty", "grounded": False, "question": question,
                "answer": "Ask me a question about your brand — pricing, approved claims, rules, or prohibited terms.",
                "evidence": [], "suggestions": SUGGESTIONS}

    facts = db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all()
    rules = db.query(BrandRule).filter(BrandRule.org_id == org_id).all()
    terms = db.query(TerminologyRule).filter(TerminologyRule.org_id == org_id).all()
    now = datetime.datetime.utcnow()

    # ---- out of scope: company finance, future plans ---------------------- #
    if _NOT_OUR_PRICE.search(q):
        return _ungrounded(question, "Company stock and financial figures are not part of your approved brand data.")
    future = [y for y in re.findall(r"\b(20\d\d)\b", q) if int(y) > now.year]
    future += re.findall(r"\bnext (?:year|month|quarter|week|season)\b|\bupcoming\b|\bplanning\b|\broadmap\b", q)
    if future:
        return _ungrounded(question, f"Nothing about “{future[0]}” is on record. Approved brand data covers current, "
                                     "approved facts only, so future prices or plans cannot be answered.")

    # ---- intent: is this specific wording allowed? ------------------------ #
    confirmed = [r for r in rules if r.is_active and r.is_confirmed is not False]
    banned = [(t.prohibited_term, t.preferred_term, t.explanation) for t in terms if t.is_active]
    banned += [(term, None, rule.rule_text) for term, rule in
               cp.rule_forbidden_terms(confirmed, [t.prohibited_term for t in terms])]
    nq = cp.normalise(q)
    asked = [b for b in banned if re.search(r"\b" + re.escape(cp.normalise(b[0]).lower()) + r"\b", nq)]
    if asked:
        lines = [f"“{bad}” is not allowed." + (f" Use “{good}” instead." if good else f" Rule: {why}")
                 for bad, good, why in asked]
        ev = [_ev(bad, f"→ {good}" if good else why, why if good else "Brand rule", "/brand-dna") for bad, good, why in asked]
        return {"intent": "terminology", "grounded": True, "question": question,
                "answer": "\n".join(lines), "evidence": ev, "suggestions": SUGGESTIONS}

    # ---- intent: pricing -------------------------------------------------- #
    if _has(q, "price", "pricing", "cost", "how much", "₹", "rs ", "inr"):
        priced = [f for f in facts if f.category.lower() == "pricing" or "price" in f.fact_key.lower()]
        if priced:
            ev = []
            lines = []
            for f in priced:
                outdated = bool(f.valid_until and f.valid_until < now)
                lines.append(f"{f.fact_key}: {f.fact_value}" + (" (OUTDATED)" if outdated else ""))
                ev.append(_ev(f.fact_key, f.fact_value, f.verification_source, "/claim-dna"))
            return {"intent": "pricing", "grounded": True, "question": question,
                    "answer": "Approved pricing on record:\n• " + "\n• ".join(lines),
                    "evidence": ev, "suggestions": SUGGESTIONS}
        return _ungrounded(question, "No approved pricing fact is on record for this workspace.")

    # ---- intent: most violated rules / recurring issues ------------------- #
    if _has(q, "violat", "recurring", "most common", "common issue", "frequent", "breach", "risk"):
        subs = db.query(Submission).filter(Submission.org_id == org_id).all()
        cat = Counter()
        refs = Counter()
        analysed = 0
        for s in subs:
            if s.findings:
                analysed += 1
            for fd in s.findings:
                cat[fd.issue_category] += 1
                if fd.rule_reference:
                    refs[fd.rule_reference] += 1
        if cat:
            top = cat.most_common(5)
            lines = [f"{name} — flagged {n} time{'s' if n != 1 else ''}" for name, n in top]
            ev = [_ev(ref, f"cited {n} times", href="/content-intelligence") for ref, n in refs.most_common(4)]
            return {"intent": "violations", "grounded": True, "question": question,
                    "answer": f"Across {analysed} analysed submission(s), your most frequently flagged issue categories are:\n• "
                              + "\n• ".join(lines),
                    "evidence": ev, "suggestions": SUGGESTIONS}
        return _ungrounded(question, "No findings have been recorded yet, so there are no violation patterns to report.")

    # ---- intent: prohibited terminology ----------------------------------- #
    if _has(q, "prohibit", "avoid", "forbidden", "banned", "terminology", "what words", "which words", "don't say", "do not say"):
        if terms:
            lines = [f"Avoid \"{t.prohibited_term}\" → use \"{t.preferred_term}\"" for t in terms]
            ev = [_ev(t.prohibited_term, f"→ {t.preferred_term}", t.explanation, "/brand-dna") for t in terms]
            return {"intent": "terminology", "grounded": True, "question": question,
                    "answer": "Prohibited terms and their approved alternatives:\n• " + "\n• ".join(lines),
                    "evidence": ev, "suggestions": SUGGESTIONS}
        return _ungrounded(question, "No terminology rules are defined for this workspace.")

    # ---- intent: approved claims / facts ---------------------------------- #
    if _has(q, "claim", "fact", "approved", "verified", "what can we say", "spec", "warranty", "battery"):
        if facts:
            lines = [f"{f.fact_key}: {f.fact_value}" for f in facts]
            ev = [_ev(f.fact_key, f.fact_value, f.verification_source, "/claim-dna") for f in facts]
            return {"intent": "approved_facts", "grounded": True, "question": question,
                    "answer": "These are your approved facts — the ground truth ClaimDNA verifies against:\n• " + "\n• ".join(lines),
                    "evidence": ev, "suggestions": SUGGESTIONS}
        return _ungrounded(question, "No approved facts are on record for this workspace.")

    # ---- intent: brand identity / voice / tone ---------------------------- #
    if _has(q, "identity", "voice", "tone", "positioning", "personality", "who are we", "explain our brand", "brand dna"):
        tone_rules = [r for r in rules if "tone" in r.category.lower() or "voice" in r.category.lower()]
        hits = RagRetriever(db).search(org_id, "brand voice tone identity positioning", top_k=2)
        ev = [_ev(r.title, r.rule_text, r.source_document or "", "/brand-dna", r.page_reference) for r in tone_rules]
        ev += [_ev(h["filename"], h["content"][:220], h["citation"], "/brand-dna", h["page"]) for h in hits]
        if ev:
            parts = [r.rule_text for r in tone_rules] or [hits[0]["content"]] if hits else []
            body = " ".join(parts)[:500] if parts else "See the cited brand-voice guidance."
            return {"intent": "identity", "grounded": True, "question": question,
                    "answer": f"Your brand voice, per approved guidance: {body}",
                    "evidence": ev, "suggestions": SUGGESTIONS}
        return _ungrounded(question, "No brand-voice guidance is on record yet.")

    # ---- intent: rules / policies ----------------------------------------- #
    if _has(q, "rule", "policy", "polic", "guideline", "standard", "allowed", "requirement",
            "product name", "naming", "name be written", "compare", "comparison"):
        if rules:
            lines = [f"[{r.severity}] {r.title}" for r in rules]
            ev = [_ev(r.title, r.rule_text, (r.source_document or ""), "/brand-dna", r.page_reference) for r in rules]
            return {"intent": "rules", "grounded": True, "question": question,
                    "answer": "Your active brand rules:\n• " + "\n• ".join(lines),
                    "evidence": ev, "suggestions": SUGGESTIONS}
        return _ungrounded(question, "No brand rules are defined for this workspace.")

    # ---- fallback: grounded retrieval over approved knowledge -------------- #
    # An off-topic question (e.g. "capital of France") can share only stopwords
    # with the corpus, which still yields a non-zero score. To stay honest we
    # require a real *content-word* overlap with the retrieved passage before
    # treating it as an answer; otherwise we report it as not-in-scope.
    qwords = _content_words(q)
    raw_hits = RagRetriever(db).search(org_id, question, top_k=3)
    hits = [h for h in raw_hits if _relevant(qwords, h["content"])]
    fact_hit = next((f for f in facts if _relevant(qwords, f"{f.fact_key} {f.fact_value}")), None)
    if hits:
        ev = [_ev(h["filename"], h["content"][:220], h["citation"], "/brand-dna", h["page"]) for h in hits]
        if fact_hit:
            ev.append(_ev(fact_hit.fact_key, fact_hit.fact_value, fact_hit.verification_source, "/claim-dna"))
        return {"intent": "retrieval", "grounded": True, "question": question,
                "answer": f"Here is what your approved brand data says:\n{hits[0]['content']}",
                "evidence": ev, "suggestions": SUGGESTIONS}
    if fact_hit:
        return {"intent": "retrieval", "grounded": True, "question": question,
                "answer": f"{fact_hit.fact_key}: {fact_hit.fact_value}",
                "evidence": [_ev(fact_hit.fact_key, fact_hit.fact_value, fact_hit.verification_source, "/claim-dna")],
                "suggestions": SUGGESTIONS}

    return _ungrounded(
        question,
        "I can only answer from your organisation's approved brand data (guidelines, rules, approved facts and "
        "terminology), and I couldn't find anything about that. Try asking about pricing, approved claims, brand "
        "rules, prohibited terms, or your brand voice.",
    )


def _ungrounded(question: str, message: str) -> dict:
    return {"intent": "ungrounded", "grounded": False, "question": question,
            "answer": message, "evidence": [], "suggestions": SUGGESTIONS}
