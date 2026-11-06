"""
Predictive Brand Risk Intelligence (Round 2 / R2-5).

Turns the organisation's real governance history into explained risk
*indicators*. Honesty contract:

  * Every indicator is a TRANSPARENT, rules-based index computed from real
    persisted records (submissions, findings, claims, approvals, rules,
    terminology). Each carries the exact numbers that drive it (`drivers`) and a
    plain-language `rationale`, so a human can audit the score.
  * These are descriptive risk indices over history — NOT machine-learned
    forecasts, and they are labelled as such. Nothing is predicted or invented.
"""
from __future__ import annotations

import datetime
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.models.brand import Organization, BrandRule, ApprovedFact, TerminologyRule
from backend.app.models.submission import Submission, Finding, ClaimVerification, ApprovalRecord


def _level(score: int) -> str:
    return "High" if score >= 60 else ("Medium" if score >= 30 else "Low")


def _indicator(key, label, score, rationale, drivers, recommendation) -> dict:
    score = max(0, min(100, int(round(score))))
    return {"key": key, "label": label, "score": score, "level": _level(score),
            "rationale": rationale, "drivers": drivers, "recommendation": recommendation}


def _pct(part: int, whole: int) -> float:
    return (part / whole) if whole else 0.0


def compute_risk_intelligence(db: Session, org_id: str) -> Optional[dict]:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if org is None:
        return None

    subs = db.query(Submission).filter(Submission.org_id == org_id).all()
    findings = db.query(Finding).join(Finding.submission).filter(Submission.org_id == org_id).all()
    claims = db.query(ClaimVerification).join(ClaimVerification.submission).filter(Submission.org_id == org_id).all()
    approvals = db.query(ApprovalRecord).join(ApprovalRecord.submission).filter(Submission.org_id == org_id).all()
    rules = db.query(BrandRule).filter(BrandRule.org_id == org_id).all()
    facts = db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all()
    terms = db.query(TerminologyRule).filter(TerminologyRule.org_id == org_id).all()

    n_sub = len(subs)
    indicators = []

    # --- Content Risk: density & spread of critical findings ----------------
    crit = sum(1 for f in findings if f.severity == "CRITICAL")
    warn = sum(1 for f in findings if f.severity == "WARNING")
    subs_with_crit = len({f.submission_id for f in findings if f.severity == "CRITICAL"})
    content_score = _pct(subs_with_crit, n_sub) * 70 + min(30, crit * 2)
    indicators.append(_indicator(
        "content", "Content Risk", content_score,
        rationale=(f"{crit} critical and {warn} warning findings across {n_sub} analysed submission(s); "
                   f"{subs_with_crit} submission(s) carry at least one critical issue."),
        drivers=[{"label": "Critical findings", "value": crit},
                 {"label": "Warning findings", "value": warn},
                 {"label": "Submissions with a critical issue", "value": f"{subs_with_crit}/{n_sub}"}],
        recommendation="Prioritise rewriting the submissions with critical findings; use AI Copy Studio for compliant rewrites.",
    ))

    # --- Claim Risk: share of claims that are not supported ------------------
    n_claims = len(claims)
    bad = sum(1 for c in claims if c.status in ("Unsupported", "Contradicted", "Outdated"))
    contradicted = sum(1 for c in claims if c.status == "Contradicted")
    claim_score = _pct(bad, n_claims) * 100
    indicators.append(_indicator(
        "claim", "Claim Risk", claim_score,
        rationale=(f"{bad} of {n_claims} verified claim(s) are unsupported, contradicted or outdated "
                   f"({contradicted} directly contradict an approved fact)."),
        drivers=[{"label": "Unsupported / contradicted / outdated", "value": f"{bad}/{n_claims}"},
                 {"label": "Directly contradicted", "value": contradicted}],
        recommendation="Add approved evidence for recurring claims, or correct the copy to match approved facts.",
    ))

    # --- Guideline Conflict Risk: unconfirmed policies & knowledge gaps ------
    unconfirmed = sum(1 for r in rules if not r.is_confirmed)
    gaps = sum(1 for present in (rules, facts, terms) if len(present) == 0)
    guideline_score = _pct(unconfirmed, len(rules)) * 70 + gaps * 20
    indicators.append(_indicator(
        "guideline", "Guideline Conflict Risk", guideline_score,
        rationale=(f"{unconfirmed} of {len(rules)} brand rule(s) are not yet confirmed/active; "
                   f"{gaps} core knowledge area(s) (rules/facts/terminology) are empty."),
        drivers=[{"label": "Unconfirmed rules", "value": f"{unconfirmed}/{len(rules)}"},
                 {"label": "Approved facts", "value": len(facts)},
                 {"label": "Terminology rules", "value": len(terms)}],
        recommendation="Confirm extracted rules in Brand DNA Studio and fill empty knowledge areas.",
    ))

    # --- Governance Process Risk: review backlog & negative-decision rate ----
    pending = sum(1 for s in subs if s.status in ("Pending Review", "Analysed"))
    decided = len(approvals)
    negative = sum(1 for a in approvals if a.decision in ("Rejected", "Revision Requested"))
    process_score = _pct(pending, n_sub) * 55 + _pct(negative, decided) * 45
    indicators.append(_indicator(
        "process", "Governance Process Risk", process_score,
        rationale=(f"{pending} submission(s) are awaiting human review; of {decided} recorded decision(s), "
                   f"{negative} were a rejection or revision request."),
        drivers=[{"label": "Awaiting review", "value": f"{pending}/{n_sub}"},
                 {"label": "Rejections / revisions", "value": f"{negative}/{decided}"}],
        recommendation="Clear the review queue in the Approval Hub; recurring rejections may signal an unclear policy.",
    ))

    # --- Visual Risk: visual findings seen in analysis ----------------------
    visual_findings = sum(1 for f in findings if f.issue_category == "Visual")
    visual_score = min(100, visual_findings * 15)
    indicators.append(_indicator(
        "visual", "Visual Risk", visual_score,
        rationale=(f"{visual_findings} visual finding(s) recorded. Visual DNA checks measured colour/contrast; "
                   "logo and OCR brand-mark matching are not yet automated, so visual risk is partially observed."),
        drivers=[{"label": "Visual findings", "value": visual_findings}],
        recommendation="Run creative assets through Visual DNA; treat visual risk as partial pending logo/OCR matching.",
    ))

    overall = int(round(sum(i["score"] for i in indicators) / len(indicators))) if indicators else 0

    return {
        "org": {"id": org.id, "name": org.name},
        "overall_score": overall,
        "overall_level": _level(overall),
        "indicators": indicators,
        "basis": ("Transparent, rules-based indices computed from your real governance history "
                  "(not machine-learned forecasts). Each indicator shows the numbers that drive it."),
        "history": {"submissions": n_sub, "findings": len(findings), "claims": n_claims, "decisions": len(approvals)},
    }
