"""
Campaign Launch Readiness.

Evaluates one campaign version against the governance checks required before
publication, using records that already exist: the content analysis, Product
Truth verification, ClaimDNA results, Translation Guard runs, approval history
and guideline dates. It never publishes and never approves: the best possible
state is "Approved for Launch", which itself requires a human approval of the
current version.

Check statuses: pass | fail | warn | pending | not_applicable | unavailable
("unavailable" means BrandVault lacks the data to judge — reported, not faked).
"""
from __future__ import annotations

import datetime
import re
import uuid
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from backend.app.models.brand import BrandGuideline, BrandRule
from backend.app.models.governance import LaunchCheckConfig, LaunchReadinessReport
from backend.app.models.multilingual import MultilingualCampaign
from backend.app.models.submission import Submission, ApprovalRecord
from backend.app.models.passport import BrandPassport
from backend.app.services import product_truth as pt
from backend.app.services.passport_service import normalise_content

PASS, FAIL, WARN, PENDING, NA, UNAVAILABLE = "pass", "fail", "warn", "pending", "not_applicable", "unavailable"

CHECKS = [
    ("brand_identity", "Brand identity verified"),
    ("approved_logo", "Approved logo used"),
    ("brand_colours", "Correct brand colours"),
    ("product_name", "Product name verified"),
    ("product_specs", "Product specifications verified"),
    ("pricing", "Pricing verified"),
    ("claims", "Marketing claims verified"),
    ("disclaimers", "Mandatory disclaimers present"),
    ("visual_assets", "Visual assets approved"),
    ("translations", "Translation checks completed"),
    ("approvals", "Required approvals completed"),
    ("guideline_version", "Current guideline version applied"),
]
CHECK_LABELS = dict(CHECKS)
DEFAULT_MANDATORY = ["pricing", "claims", "product_specs", "approvals", "guideline_version", "brand_identity"]

READY, BLOCKED, PENDING_APPROVAL, APPROVED, EXPIRED, REANALYSE = (
    "Ready for Review", "Blocked by Critical Issues", "Pending Approval", "Approved for Launch",
    "Expired Approval", "Requires Reanalysis")

_DISCLAIMER_RE = re.compile(r"(\*|t\s*&\s*c|terms\s+(and|&)\s+conditions|conditions\s+apply|terms\s+apply|disclaimer)", re.I)


def get_config(db: Session, org_id: str) -> LaunchCheckConfig:
    cfg = db.query(LaunchCheckConfig).filter(LaunchCheckConfig.org_id == org_id).first()
    if cfg is None:
        cfg = LaunchCheckConfig(org_id=org_id, mandatory=list(DEFAULT_MANDATORY), approval_validity_days=90)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _check(key: str, status: str, detail: str, evidence: Optional[List[str]] = None,
           route: Optional[str] = None) -> dict:
    return {"key": key, "label": CHECK_LABELS[key], "status": status, "detail": detail,
            "evidence": evidence or [], "route_to": route}


def _is_visual(sub: Submission) -> bool:
    return sub.title.lower().startswith("visual asset") or any(f.issue_category in ("Visual", "Accessibility") for f in sub.findings)


def evaluate(db: Session, sub: Submission, actor: str, persist: bool = True) -> dict:
    now = datetime.datetime.utcnow()
    cfg = get_config(db, sub.org_id)
    mandatory = set(cfg.mandatory or [])
    open_findings = [f for f in sub.findings if not f.is_applied]
    checks: List[dict] = []
    truth = pt.verify_text(db, sub.org_id, sub.content)
    tclaims = truth["claims"]

    # 1 brand identity: no open terminology / naming findings
    term = [f for f in open_findings if f.issue_category == "Terminology"]
    checks.append(_check("brand_identity", FAIL if any(f.severity == "CRITICAL" for f in term) else WARN if term else PASS,
                         f"{len(term)} open terminology finding(s)." if term else "No open terminology or naming findings.",
                         [f"“{f.original_text}” → {f.suggested_correction}" for f in term[:4]], "Content creator"))

    visual = _is_visual(sub)
    vis_open = [f for f in open_findings if f.issue_category in ("Visual", "Accessibility")]
    # 2 / 3 / 9 visual checks only apply to visual campaigns
    if not visual:
        for k in ("approved_logo", "brand_colours", "visual_assets"):
            checks.append(_check(k, NA, "Text-only campaign: no image asset is attached."))
    else:
        checks.append(_check("approved_logo", UNAVAILABLE,
                             "Logo use is not linked to this submission. Run the creative through Asset Forensics.",
                             route="Brand reviewer"))
        checks.append(_check("brand_colours", FAIL if vis_open else PASS,
                             f"{len(vis_open)} open colour/contrast finding(s)." if vis_open else "Measured palette met the colour rules.",
                             [f.original_text for f in vis_open[:3]], "Design team"))
        checks.append(_check("visual_assets", UNAVAILABLE, "Asset approval status is not linked to this submission yet."))

    # 4 product name
    if truth["products_detected"] and not truth["product_inferred"]:
        checks.append(_check("product_name", PASS, f"Names an approved product: {', '.join(truth['products_detected'])}."))
    elif truth["product_inferred"]:
        checks.append(_check("product_name", WARN, "The copy does not name the product exactly; the only product on record was assumed.",
                             route="Content creator"))
    else:
        checks.append(_check("product_name", WARN if tclaims else NA,
                             "No approved product name appears in the copy." if tclaims else "The copy makes no product statements."))

    # 5 specs / 6 pricing from Product Truth
    def truth_check(key, claims, label):
        if not claims:
            return _check(key, NA, f"No {label} statements in the copy.")
        bad = [c for c in claims if c["status"] in ("Contradicted", "Outdated")]
        unsup = [c for c in claims if c["status"] in ("Unsupported", "Needs Human Review")]
        ev = [f"{c['submitted_value']} — {c['status']}" + (f" (approved {c['approved_value']}, {c['source_document']})" if c["approved_value"] else "")
              for c in (bad + unsup)[:4]]
        if bad:
            return _check(key, FAIL, f"{len(bad)} {label} statement(s) contradict or use outdated approved facts.", ev, "Brand administrator")
        if unsup:
            return _check(key, WARN, f"{len(unsup)} {label} statement(s) have no approved fact to verify against.", ev, "Brand administrator")
        return _check(key, PASS, f"All {len(claims)} {label} statement(s) match approved facts.",
                      [f"{c['submitted_value']} ✓ {c['source_document']}" for c in claims[:3]])
    checks.append(truth_check("product_specs", [c for c in tclaims if c["attribute"] != "price"], "specification"))
    checks.append(truth_check("pricing", [c for c in tclaims if c["attribute"] == "price"], "price"))

    # 7 claims from ClaimDNA
    cv = sub.claim_verifications
    bad = [c for c in cv if c.status in ("Contradicted", "Unsupported", "Outdated")]
    review = [c for c in cv if c.status == "Needs Human Review"]
    checks.append(_check("claims", FAIL if bad else WARN if review else PASS if cv else NA,
                         (f"{len(bad)} claim(s) are contradicted, unsupported or outdated." if bad else
                          f"{len(review)} claim(s) need human review." if review else
                          f"All {len(cv)} verified claim(s) are supported." if cv else "No promotional claims detected."),
                         [f"“{c.claim_text}” — {c.status}" for c in (bad + review)[:4]], "Legal / claims reviewer"))

    # 8 disclaimers
    rules = db.query(BrandRule).filter(BrandRule.org_id == sub.org_id, BrandRule.is_confirmed == True).all()  # noqa: E712
    disc_rules = [r for r in rules if "disclaimer" in f"{r.title} {r.rule_text}".lower()]
    if not disc_rules:
        checks.append(_check("disclaimers", UNAVAILABLE, "No disclaimer requirement is defined in Brand DNA, so this cannot be checked.",
                             route="Brand administrator"))
    else:
        has = bool(_DISCLAIMER_RE.search(sub.content))
        checks.append(_check("disclaimers", PASS if has else FAIL,
                             "A disclaimer marker is present." if has else "Disclaimer rules exist but the copy contains no disclaimer.",
                             [r.title for r in disc_rules[:3]], "Legal / claims reviewer"))

    # 10 translations linked by identical source text
    src = normalise_content(sub.content)
    tg_runs = [c for c in db.query(MultilingualCampaign).filter(MultilingualCampaign.org_id == sub.org_id).all()
               if normalise_content(c.source_text) == src]
    if not tg_runs:
        checks.append(_check("translations", NA, "No translated versions of this copy have been checked."))
    else:
        last = max(tg_runs, key=lambda c: c.created_at)
        st = {"Consistent": PASS, "Review recommended": WARN, "Needs revision": FAIL}.get(last.verdict, WARN)
        checks.append(_check("translations", st, f"Latest Translation Guard run: {last.verdict} ({len(last.translations)} language(s)).",
                             [f"{t.detected_lang}: {t.verdict}" for t in last.translations], "Multilingual reviewer"))

    # 11 approvals: version-locked human decision
    approvals = sorted(sub.approvals, key=lambda a: a.created_at or now)
    last_auth = next((a for a in reversed(approvals) if a.decision in ("Approved", "Rejected", "Revision Requested")), None)
    approval_state = None
    if last_auth is None:
        checks.append(_check("approvals", PENDING, "No reviewer decision yet.", route="Brand reviewer"))
    elif last_auth.decision != "Approved":
        checks.append(_check("approvals", FAIL, f"Latest decision: {last_auth.decision} by {last_auth.reviewer_name}.",
                             [last_auth.comments[:160]], "Content creator"))
    elif last_auth.submission_version not in (None, sub.version):
        approval_state = EXPIRED
        checks.append(_check("approvals", FAIL, f"Approval covered version {last_auth.submission_version}; the campaign is now version {sub.version}.",
                             route="Brand reviewer"))
    elif last_auth.created_at and (now - last_auth.created_at).days > cfg.approval_validity_days:
        approval_state = EXPIRED
        checks.append(_check("approvals", FAIL, f"Approved {(now - last_auth.created_at).days} days ago; approvals are valid for {cfg.approval_validity_days} days.",
                             route="Brand reviewer"))
    else:
        approval_state = APPROVED
        checks.append(_check("approvals", PASS, f"Approved by {last_auth.reviewer_name} ({last_auth.reviewer_role}) for version {sub.version}."))

    # 12 guideline version: was the analysis run after the latest guideline?
    latest_g = (db.query(BrandGuideline).filter(BrandGuideline.org_id == sub.org_id)
                .order_by(BrandGuideline.created_at.desc()).first())
    needs_reanalysis = bool(latest_g and latest_g.created_at and sub.updated_at and latest_g.created_at > sub.updated_at)
    checks.append(_check("guideline_version", FAIL if needs_reanalysis else PASS if latest_g else UNAVAILABLE,
                         (f"“{latest_g.filename}” was uploaded after this campaign was last analysed. Re-run the analysis." if needs_reanalysis else
                          f"Analysed against the current guideline “{latest_g.filename}”." if latest_g else "No guideline uploaded."),
                         route="Content creator" if needs_reanalysis else None))

    for c in checks:
        c["mandatory"] = c["key"] in mandatory
    blocking = [c for c in checks if c["mandatory"] and c["status"] == FAIL and c["key"] not in ("approvals", "guideline_version")]
    if needs_reanalysis:
        state = REANALYSE
    elif approval_state == EXPIRED:
        state = EXPIRED
    elif blocking:
        state = BLOCKED
    elif approval_state == APPROVED and not [c for c in checks if c["mandatory"] and c["status"] in (FAIL, PENDING)]:
        state = APPROVED
    elif sub.status == "Pending Review":
        state = PENDING_APPROVAL
    else:
        state = READY

    routes = sorted({c["route_to"] for c in checks if c["route_to"] and c["status"] in (FAIL, WARN, PENDING, UNAVAILABLE)})
    report = {
        "submission": {"id": sub.id, "title": sub.title, "version": sub.version, "status": sub.status,
                       "score": sub.overall_score, "author": sub.author_name},
        "state": state, "checks": checks,
        "counts": {s: sum(1 for c in checks if c["status"] == s) for s in (PASS, FAIL, WARN, PENDING, NA, UNAVAILABLE)},
        "unresolved_findings": [{"id": f.id, "category": f.issue_category, "severity": f.severity,
                                 "text": f.original_text, "suggestion": f.suggested_correction} for f in open_findings],
        "blocking": [c["key"] for c in blocking],
        "route_to": routes,
        "mandatory": sorted(mandatory),
        "note": "Launch readiness never publishes or approves. A human approval of the current version is always required.",
        "evaluated_at": now.isoformat() + "Z",
    }
    if persist:
        row = LaunchReadinessReport(id=str(uuid.uuid4()), org_id=sub.org_id, submission_id=sub.id,
                                    submission_version=sub.version, state=state, report=report, created_by=actor)
        db.add(row)
        db.commit()
        report["id"] = row.id
    return report
