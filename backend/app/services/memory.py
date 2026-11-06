"""
Brand Memory Engine (Round 2 / R2-4).

Learns from the organisation's real governance history and derives:
  * INSIGHTS — accepted corrections, recurring violations, and repeated
    contradictions, each backed by real counts.
  * PROPOSALS — suggested policy improvements (e.g. a new terminology entry for a
    recurring flagged phrase that isn't yet formalised).

Honesty contract: this NEVER edits the official Brand DNA. Proposals are
surfaced for an administrator to review and explicitly apply; nothing is changed
automatically, and every insight carries the evidence that produced it.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.models.brand import Organization, TerminologyRule
from backend.app.models.submission import Submission, Finding, ClaimVerification


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def compute_memory(db: Session, org_id: str) -> Optional[dict]:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if org is None:
        return None

    findings = db.query(Finding).join(Finding.submission).filter(Submission.org_id == org_id).all()
    claims = db.query(ClaimVerification).join(ClaimVerification.submission).filter(Submission.org_id == org_id).all()
    terms = db.query(TerminologyRule).filter(TerminologyRule.org_id == org_id).all()
    existing_terms = {_norm(t.prohibited_term) for t in terms}

    insights = []

    # 1) Accepted corrections — what reviewers actually applied (is_applied).
    applied = [f for f in findings if f.is_applied]
    applied_counter = Counter((_norm(f.original_text), _norm(f.suggested_correction)) for f in applied)
    for (orig, corr), n in applied_counter.most_common(5):
        if orig and corr:
            insights.append({
                "type": "accepted_correction",
                "title": "Correction consistently accepted",
                "detail": f'Reviewers applied the fix "{orig}" → "{corr}" {n} time(s). This approved alternative is working.',
                "count": n,
            })

    # 2) Recurring violations — flagged repeatedly despite an active rule.
    viol_counter = Counter()
    viol_meta = {}
    for f in findings:
        key = (f.issue_category, _norm(f.original_text))
        viol_counter[key] += 1
        viol_meta[key] = f
    for (cat, orig), n in viol_counter.most_common(8):
        if n >= 2 and orig:
            insights.append({
                "type": "recurring_violation",
                "title": f"Recurring {cat} issue",
                "detail": f'"{orig}" has been flagged {n} times across submissions — the rule is catching it, but it keeps appearing in drafts.',
                "count": n,
            })

    # 3) Repeated contradictions — an approved fact is being violated again and again.
    contra = Counter(_norm(c.claim_text) for c in claims if c.status == "Contradicted")
    for claim_text, n in contra.most_common(4):
        if n >= 1 and claim_text:
            insights.append({
                "type": "contradiction",
                "title": "Approved fact repeatedly contradicted",
                "detail": f'The claim "{claim_text}" contradicts an approved fact and has appeared {n} time(s).',
                "count": n,
            })

    # --- Proposals: a recurring flagged WORD-PHRASE not yet formalised as
    # terminology. Pricing (numeric) and descriptive findings are excluded —
    # those are rule/fact matters, not terminology entries.
    _DESCRIPTIVE = {"copy", "used", "mark", "marks", "exclamation", "tone", "sentence", "multiple"}
    proposals = []
    seen = set()
    for (cat, orig), n in viol_counter.most_common(20):
        norm = _norm(orig)
        if n < 2 or not orig or norm in existing_terms or norm in seen:
            continue
        if cat not in ("Terminology", "Promotional Claim"):
            continue
        # Must be a short word-phrase: not a price/number, not a description.
        if len(orig) > 45 or len(orig.split()) > 6:
            continue
        if re.search(r"[₹$]|\d{3,}", orig):
            continue
        if set(norm.split()) & _DESCRIPTIVE:
            continue
        f = viol_meta[(cat, orig)]
        preferred = (f.suggested_correction or "").strip()
        if not preferred or re.search(r"[₹$]|\d{3,}", preferred):
            continue
        seen.add(norm)
        proposals.append({
            "kind": "terminology",
            "prohibited_term": f.original_text.strip(),
            "preferred_term": preferred,
            "reason": f"Flagged {n} times as a {cat} issue but not yet in your terminology list.",
            "occurrences": n,
        })

    return {
        "org": {"id": org.id, "name": org.name},
        "insights": insights,
        "proposals": proposals[:6],
        "summary": {
            "applied_corrections": len(applied),
            "recurring_patterns": sum(1 for v in viol_counter.values() if v >= 2),
            "contradictions": sum(contra.values()),
            "proposals": len(proposals[:6]),
        },
        "note": ("Learned from your real history. BrandVault never edits official brand policy automatically — "
                 "proposals require an administrator to review and apply."),
    }
