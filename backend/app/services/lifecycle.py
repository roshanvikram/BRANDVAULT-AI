"""
Asset Lifecycle & Expiry Intelligence.

One view of everything in Brand DNA that can go out of date — brand assets,
product facts (prices, specs), approved facts (e.g. promotions), guideline
documents and approvals — with a computed lifecycle state, upcoming expiries,
where superseded assets were still seen, and which campaigns still use
outdated information. States are derived from stored dates and statuses only.
"""
from __future__ import annotations

import datetime
import re
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from backend.app.models.asset import BrandAsset, AssetInvestigation, CURRENT_STATUSES
from backend.app.models.brand import ApprovedFact, BrandGuideline
from backend.app.models.product import Product, ProductFact, PRODUCT_ATTRIBUTES
from backend.app.models.submission import Submission
from backend.app.services import product_truth as pt
from backend.app.services.launch_readiness import get_config

EXPIRING_DAYS = 30
STATES = ["Draft", "Pending Approval", "Approved", "Active", "Expiring Soon", "Expired", "Superseded", "Archived"]


def asset_state(status: str, valid_until: Optional[datetime.datetime], now: datetime.datetime,
                expiring_days: int = EXPIRING_DAYS) -> str:
    s = (status or "").lower()
    if s == "archived":
        return "Archived"
    if s == "superseded":
        return "Superseded"
    if s == "draft":
        return "Draft"
    if s == "pending":
        return "Pending Approval"
    if s == "expired":
        return "Expired"
    if valid_until is not None:
        if valid_until <= now:
            return "Expired"
        if valid_until <= now + datetime.timedelta(days=expiring_days):
            return "Expiring Soon"
    return "Active" if s == "active" else "Approved"


def _iso(d):
    return d.isoformat() + "Z" if d else None


def lifecycle(db: Session, org_id: str, scan_campaigns: bool = True) -> dict:
    now = datetime.datetime.utcnow()
    items: List[dict] = []

    # ---- brand assets + usage seen in investigations
    usage: Dict[str, dict] = {}
    for inv in db.query(AssetInvestigation).filter(AssetInvestigation.org_id == org_id).all():
        for m in (inv.result or {}).get("matches", []):
            u = usage.setdefault(m.get("asset_id"), {"seen": 0, "last_seen": None, "investigations": []})
            u["seen"] += 1
            if not u["last_seen"] or (inv.created_at and inv.created_at.isoformat() > u["last_seen"]):
                u["last_seen"] = inv.created_at.isoformat() if inv.created_at else None
            u["investigations"].append({"id": inv.id, "file_name": inv.file_name, "risk": inv.risk})
    for a in db.query(BrandAsset).filter(BrandAsset.org_id == org_id).all():
        st = asset_state(a.status, a.valid_until, now)
        u = usage.get(a.id, {"seen": 0, "last_seen": None, "investigations": []})
        items.append({
            "kind": "asset", "id": a.id, "name": f"{a.name} {a.version_label}", "category": a.kind.replace("_", " "),
            "state": st, "valid_until": _iso(a.valid_until), "effective_from": _iso(a.effective_from),
            "detail": f"{a.width}×{a.height} {a.mime}", "usage": u["seen"], "last_seen": u["last_seen"],
            "seen_in": u["investigations"][:5],
            "replacement_available": st in ("Superseded", "Expired", "Archived") and bool(
                [x for x in db.query(BrandAsset).filter(BrandAsset.org_id == org_id, BrandAsset.name == a.name,
                                                         BrandAsset.kind == a.kind).all()
                 if asset_state(x.status, x.valid_until, now) in ("Active", "Approved", "Expiring Soon")]),
            "href": "/visual-dna/forensics",
        })

    # ---- product facts
    names = {p.id: p.name for p in db.query(Product).filter(Product.org_id == org_id).all()}
    for f in db.query(ProductFact).filter(ProductFact.org_id == org_id, ProductFact.status != "rejected").all():
        st = asset_state({"approved": "active", "pending": "pending", "superseded": "superseded"}.get(f.status, f.status),
                         f.valid_until, now)
        items.append({"kind": "product_fact", "id": f.id,
                      "name": f"{names.get(f.product_id, 'Product')} — {PRODUCT_ATTRIBUTES.get(f.attribute, f.attribute)}",
                      "category": "product fact", "state": st, "valid_until": _iso(f.valid_until), "detail": f.value_text,
                      "usage": None, "last_seen": None, "seen_in": [], "replacement_available": None,
                      "href": "/brand-dna/products"})

    # ---- approved facts (promotions, legacy Brand DNA facts)
    for f in db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all():
        st = "Superseded" if f.superseded_by and (f.valid_until is None or f.valid_until <= now) else asset_state("active", f.valid_until, now)
        items.append({"kind": "approved_fact", "id": f.id, "name": f.fact_key, "category": (f.category or "fact").lower(),
                      "state": st, "valid_until": _iso(f.valid_until), "detail": f.fact_value[:120],
                      "usage": None, "last_seen": None, "seen_in": [],
                      "replacement_available": None, "superseded_by": f.superseded_by, "href": "/brand-dna"})

    # ---- guideline documents: the newest is current, older ones are superseded
    gl = db.query(BrandGuideline).filter(BrandGuideline.org_id == org_id).order_by(BrandGuideline.created_at.desc()).all()
    for i, g in enumerate(gl):
        items.append({"kind": "guideline", "id": g.id, "name": g.filename, "category": "guideline",
                      "state": "Active" if i == 0 else "Superseded", "valid_until": None,
                      "detail": f"uploaded {g.created_at:%d %b %Y}" if g.created_at else "", "usage": None,
                      "last_seen": None, "seen_in": [], "replacement_available": None, "href": "/brand-dna"})

    # ---- approvals that have lapsed (validity window from launch policy)
    cfg = get_config(db, org_id)
    subs = db.query(Submission).filter(Submission.org_id == org_id).all()
    for s in subs:
        appr = [a for a in s.approvals if a.decision == "Approved"]
        if not appr:
            continue
        a = max(appr, key=lambda x: x.created_at or now)
        until = (a.created_at + datetime.timedelta(days=cfg.approval_validity_days)) if a.created_at else None
        st = "Superseded" if a.submission_version not in (None, s.version) else asset_state("active", until, now)
        items.append({"kind": "approval", "id": a.id, "name": s.title, "category": "approval", "state": st,
                      "valid_until": _iso(until),
                      "detail": f"v{a.submission_version or '?'} approved by {a.reviewer_name}" +
                                (f"; campaign is now v{s.version}" if st == "Superseded" else ""),
                      "usage": None, "last_seen": None, "seen_in": [], "replacement_available": None,
                      "href": "/approval-hub"})

    # ---- campaigns still using outdated product information
    affected: List[dict] = []
    if scan_campaigns:
        for s in subs:
            r = pt.verify_text(db, org_id, s.content)
            old = [c for c in r["claims"] if c["status"] == "Outdated"]
            if old:
                affected.append({"submission_id": s.id, "title": s.title, "status": s.status,
                                 "outdated": [f"{c['submitted_value']} (now {c['approved_value']})" for c in old]})
        promos = [f for f in db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all()
                  if f.valid_until and f.valid_until <= now]
        for f in promos:
            # Product-style names in the expired fact (e.g. "NovaSleeve") identify reuse.
            key_terms = [w.strip(".,()") for w in f.fact_value.split() if re.search(r"[a-z][A-Z]", w)][:2]
            for s in subs:
                if key_terms and all(t.lower() in s.content.lower() for t in key_terms):
                    affected.append({"submission_id": s.id, "title": s.title, "status": s.status,
                                     "outdated": [f"mentions expired “{f.fact_key}”"]})

    counts = {st: sum(1 for i in items if i["state"] == st) for st in STATES}
    soon = sorted([i for i in items if i["state"] == "Expiring Soon"], key=lambda i: i["valid_until"] or "")
    alerts = []
    for i in soon:
        alerts.append({"level": "warning", "text": f"{i['name']} expires on {i['valid_until'][:10]}.", "href": i["href"]})
    for i in items:
        if i["kind"] == "asset" and i["state"] in ("Superseded", "Expired") and i["usage"]:
            alerts.append({"level": "critical",
                           "text": f"{i['name']} is {i['state'].lower()} but was found in {i['usage']} investigated image(s).",
                           "href": i["href"]})
    for a in affected:
        alerts.append({"level": "critical", "text": f"“{a['title']}” uses outdated information: {', '.join(a['outdated'])}.",
                       "href": "/content-intelligence"})
    order = {s: n for n, s in enumerate(["Expired", "Expiring Soon", "Superseded", "Pending Approval", "Draft", "Active", "Approved", "Archived"])}
    items.sort(key=lambda i: (order.get(i["state"], 9), i["kind"], i["name"]))
    return {"counts": counts, "items": items, "alerts": alerts, "affected_campaigns": affected,
            "expiring_window_days": EXPIRING_DAYS, "approval_validity_days": cfg.approval_validity_days,
            "generated_at": now.isoformat() + "Z"}
