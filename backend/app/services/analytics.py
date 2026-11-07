"""
Brand Consistency analytics (Command Center heatmap + trends).

Every number is a query over stored records — submissions, findings, claim
verifications, approval decisions and asset investigations. Nothing is
estimated or projected. When there is little history the response says so.
"""
from __future__ import annotations

import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from backend.app.models.asset import AssetInvestigation
from backend.app.models.brand import Organization
from backend.app.models.product import Product
from backend.app.models.submission import Submission

DEMO_ORGS = {"nova-tech-org-001", "vortexa-tech-org-002"}
NO_PRODUCT = "No product named"
UNASSIGNED = "Unassigned"
LOGO_TYPES = ("outdated_logo", "stretched", "rotated", "cropped", "recoloured", "near_duplicate", "identical_outdated")


def _month(d: Optional[datetime.datetime]) -> str:
    return d.strftime("%Y-%m") if d else "unknown"


def _parse_date(s: Optional[str], end: bool = False) -> Optional[datetime.datetime]:
    if not s:
        return None
    d = datetime.datetime.fromisoformat(s[:10])
    return d + datetime.timedelta(days=1) if end else d


def consistency(db: Session, org_id: str, *, date_from: Optional[str] = None, date_to: Optional[str] = None,
                severity: Optional[str] = None, category: Optional[str] = None, product: Optional[str] = None,
                department: Optional[str] = None) -> Optional[dict]:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if org is None:
        return None
    start, end = _parse_date(date_from), _parse_date(date_to, end=True)
    products = [p.name for p in db.query(Product).filter(Product.org_id == org_id).all()]

    q = db.query(Submission).filter(Submission.org_id == org_id)
    if start:
        q = q.filter(Submission.created_at >= start)
    if end:
        q = q.filter(Submission.created_at < end)
    subs_all = q.order_by(Submission.created_at).all()

    def products_of(s: Submission) -> List[str]:
        hit = [n for n in products if n.lower() in s.content.lower() or n.lower() in s.title.lower()]
        return hit or [NO_PRODUCT]

    all_categories = sorted({f.issue_category for s in subs_all for f in s.findings})
    all_departments = sorted({(s.department or UNASSIGNED) for s in subs_all})
    subs = [s for s in subs_all
            if (not product or product in products_of(s))
            and (not department or (s.department or UNASSIGNED) == department)]

    def keep(f) -> bool:
        return (not severity or f.severity == severity) and (not category or f.issue_category == category)

    findings = [(s, f) for s in subs for f in s.findings if keep(f)]

    # ---------- heatmaps
    def heat(row_of) -> dict:
        grid: Dict[str, Counter] = defaultdict(Counter)
        for s, f in findings:
            for r in row_of(s):
                grid[r][f.issue_category] += 1
        cols = sorted({c for row in grid.values() for c in row})
        rows = sorted(grid, key=lambda r: -sum(grid[r].values()))
        return {"rows": rows, "columns": cols, "cells": [[grid[r][c] for c in cols] for r in rows],
                "max": max([v for row in grid.values() for v in row.values()] or [0])}

    by_product = heat(products_of)
    by_department = heat(lambda s: [s.department or UNASSIGNED])
    by_month = heat(lambda s: [_month(s.created_at)])

    # ---------- compliance tables
    def group_scores(key_of) -> List[dict]:
        g: Dict[str, list] = defaultdict(list)
        for s in subs:
            for k in key_of(s):
                g[k].append(s)
        out = []
        for k, ss in g.items():
            crit = sum(1 for s in ss for f in s.findings if f.severity == "CRITICAL" and keep(f))
            out.append({"name": k, "campaigns": len(ss), "avg_score": round(sum(s.overall_score for s in ss) / len(ss)),
                        "critical_findings": crit})
        return sorted(out, key=lambda x: x["avg_score"])

    campaigns = sorted([{
        "id": s.id, "title": s.title, "score": s.overall_score, "status": s.status, "version": s.version,
        "products": products_of(s), "department": s.department or UNASSIGNED,
        "findings": sum(1 for f in s.findings if keep(f)),
        "critical": sum(1 for f in s.findings if keep(f) and f.severity == "CRITICAL"),
        "created_at": s.created_at.isoformat() if s.created_at else None,
    } for s in subs], key=lambda x: x["score"])

    # ---------- repeated terminology mistakes
    term = Counter()
    fix: Dict[str, str] = {}
    for s, f in findings:
        if f.issue_category == "Terminology":
            k = f.original_text.strip().lower()
            term[k] += 1
            fix[k] = f.suggested_correction
    terminology = [{"term": k, "count": n, "suggested": fix[k]} for k, n in term.most_common(8)]

    # ---------- trends
    claim_trend: Dict[str, Counter] = defaultdict(Counter)
    for s in subs:
        for c in s.claim_verifications:
            claim_trend[_month(s.created_at)][c.status] += 1
    approval_trend: Dict[str, Counter] = defaultdict(Counter)
    for s in subs:
        for a in s.approvals:
            if a.decision in ("Approved", "Rejected", "Revision Requested"):
                if (not start or (a.created_at and a.created_at >= start)) and (not end or (a.created_at and a.created_at < end)):
                    approval_trend[_month(a.created_at)][a.decision] += 1
    score_trend = defaultdict(list)
    for s in subs:
        score_trend[_month(s.created_at)].append(s.overall_score)

    # ---------- visual / logo signals
    visual_trend = Counter(_month(s.created_at) for s, f in findings if f.issue_category in ("Visual", "Accessibility"))
    logo_counts: Counter = Counter()
    colour_deviation = sum(1 for s, f in findings if f.issue_category == "Visual")
    invs = db.query(AssetInvestigation).filter(AssetInvestigation.org_id == org_id).all()
    for inv in invs:
        if (start and inv.created_at and inv.created_at < start) or (end and inv.created_at and inv.created_at >= end):
            continue
        for m in (inv.result or {}).get("matches", []):
            for f in m.get("findings", []):
                if f["type"] in LOGO_TYPES:
                    logo_counts[f["type"]] += 1
                if f["type"] == "recoloured":
                    colour_deviation += 1

    # ---------- unresolved
    unresolved: Dict[str, Counter] = defaultdict(Counter)
    for s, f in findings:
        if not f.is_applied and s.status != "Approved":
            unresolved[f.issue_category][f.severity] += 1

    months = sorted({_month(s.created_at) for s in subs if s.created_at})
    decisions = [a for s in subs for a in s.approvals if a.decision in ("Approved", "Rejected", "Revision Requested")]
    return {
        "org": {"id": org.id, "name": org.name},
        "filters": {"date_from": date_from, "date_to": date_to, "severity": severity, "category": category,
                    "product": product, "department": department},
        "options": {"categories": all_categories, "severities": ["CRITICAL", "WARNING", "SUGGESTION"],
                    "products": products + [NO_PRODUCT], "departments": all_departments},
        "kpis": {
            "campaigns": len(subs), "findings": len(findings),
            "critical": sum(1 for _, f in findings if f.severity == "CRITICAL"),
            "unresolved": sum(sum(c.values()) for c in unresolved.values()),
            "avg_score": round(sum(s.overall_score for s in subs) / len(subs)) if subs else None,
            "decisions": len(decisions),
            "approval_rate": round(100 * sum(1 for a in decisions if a.decision == "Approved") / len(decisions)) if decisions else None,
        },
        "heatmaps": {"product": by_product, "department": by_department, "month": by_month},
        "compliance": {"campaigns": campaigns, "products": group_scores(products_of),
                       "departments": group_scores(lambda s: [s.department or UNASSIGNED])},
        "terminology_repeats": terminology,
        "trends": {
            "months": months,
            "score": [{"month": m, "avg_score": round(sum(v) / len(v))} for m, v in sorted(score_trend.items())],
            "claims": [{"month": m, **dict(c)} for m, c in sorted(claim_trend.items())],
            "approvals": [{"month": m, **dict(c)} for m, c in sorted(approval_trend.items())],
            "visual_findings": [{"month": m, "count": n} for m, n in sorted(visual_trend.items())],
        },
        "visual": {"logo_misuse": dict(logo_counts), "colour_deviations": colour_deviation, "investigations": len(invs)},
        "unresolved": [{"category": k, **dict(v)} for k, v in sorted(unresolved.items(), key=lambda kv: -sum(kv[1].values()))],
        "basis": {
            "months_covered": len(months), "first": months[0] if months else None, "last": months[-1] if months else None,
            "demonstration_data": org_id in DEMO_ORGS,
            "note": ("Calculated from stored records only. "
                     + ("No campaigns match these filters. " if not months else
                        "Only one month of history exists, so trends are not yet meaningful. " if len(months) == 1 else "")
                     + ("Submissions do not yet record a department; they appear as Unassigned." if all_departments == [UNASSIGNED] else "")).strip(),
        },
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    }
