"""Administrator views of the running service, and the look-alike domain watch."""
from __future__ import annotations

import datetime
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.core import observability
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.account import DomainWatchHit, ErrorEvent
from backend.app.models.intelligence import FraudIncident
from backend.app.models.user import ROLE_ADMIN, ROLE_REVIEWER, User
from backend.app.services import ctwatch
from backend.app.services.llm import get_llm_provider

router = APIRouter(tags=["System"])


def _iso(d: Optional[datetime.datetime]) -> Optional[str]:
    return d.isoformat() + "Z" if d else None


@router.get("/system/status")
def system_status(db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    """Live service numbers (since the last restart) and your workspace's recent server errors."""
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False
    since = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    errors = (db.query(ErrorEvent).filter(ErrorEvent.org_id == current.org_id, ErrorEvent.created_at >= since)
              .order_by(ErrorEvent.created_at.desc()).limit(50).all())
    p = get_llm_provider(settings)
    return {
        "version": settings.VERSION, "environment": settings.ENVIRONMENT,
        "database": {"ok": db_ok, "engine": db.get_bind().dialect.name},
        "ai": {"available": bool(getattr(p, "available", False)), "chain": getattr(p, "chain", [getattr(p, "name", "none")]),
               "cache_seconds": settings.LLM_CACHE_SECONDS},
        "traffic": observability.snapshot(),
        "recent_errors": [{"id": e.id, "request_id": e.request_id, "method": e.method, "path": e.path,
                           "error_type": e.error_type, "message": e.message[:500], "at": _iso(e.created_at)} for e in errors],
        "domain_watch": {"enabled": settings.CT_MONITOR_ENABLED, "every_hours": settings.CT_MONITOR_HOURS,
                         "scheduled": settings.CT_MONITOR_ENABLED and settings.ENVIRONMENT.lower() == "production",
                         **ctwatch.state.get(current.org_id, {})},
    }


# ------------------------------------------------------------ domain watch
def _hit(h: DomainWatchHit) -> dict:
    return {"id": h.id, "host": h.host, "matched_term": h.matched_term, "issuer": h.issuer, "cert_id": h.cert_id,
            "cert_url": f"https://crt.sh/?id={h.cert_id}" if h.cert_id else None,
            "not_before": _iso(h.not_before), "findings": h.findings or [], "risk": h.risk, "status": h.status,
            "incident_id": h.incident_id, "first_seen": _iso(h.first_seen)}


@router.get("/fraud/watch")
def watch_hits(status: Optional[str] = None, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    q = db.query(DomainWatchHit).filter(DomainWatchHit.org_id == current.org_id)
    if status:
        q = q.filter(DomainWatchHit.status == status)
    rows = q.order_by(DomainWatchHit.first_seen.desc()).limit(300).all()
    terms, official = ctwatch.search_terms(db, current.org_id)
    return {"hits": [_hit(h) for h in rows], "terms": terms, "official_domains": official,
            "scan": ctwatch.state.get(current.org_id), "source": "Certificate Transparency logs (crt.sh)"}


@router.post("/fraud/watch/scan")
def watch_scan(db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN, ROLE_REVIEWER))):
    """Start a search of the public certificate logs in the background (it can take a few
    minutes). Poll GET /fraud/watch: `scan.running` turns false and `scan.summary` holds the result."""
    terms, _ = ctwatch.search_terms(db, current.org_id)
    if not terms:
        raise HTTPException(status_code=400, detail="Add your official domains first: the watch searches for names like them.")
    started = ctwatch.start_scan(current.org_id)
    return {"started": started, "already_running": not started, "terms": terms}


class HitStatus(BaseModel):
    status: str  # new | dismissed | incident


@router.post("/fraud/watch/{hit_id}")
def watch_update(hit_id: str, body: HitStatus, db: Session = Depends(get_db),
                 current: User = Depends(require_roles(ROLE_ADMIN, ROLE_REVIEWER))):
    h = db.query(DomainWatchHit).filter(DomainWatchHit.id == hit_id, DomainWatchHit.org_id == current.org_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Watch hit not found.")
    if body.status not in ("new", "dismissed", "incident"):
        raise HTTPException(status_code=422, detail="Status must be new, dismissed or incident.")
    if body.status == "incident" and not h.incident_id:
        now = datetime.datetime.utcnow()
        who = f"{current.full_name} ({current.role})"
        top = max(h.findings or [{}], key=lambda f: f.get("confidence", 0))
        inc = FraudIncident(
            id=str(uuid.uuid4()), number=f"BV-INC-{uuid.uuid4().hex[:6].upper()}", org_id=current.org_id,
            source_url=f"https://{h.host}", source_kind="url",
            detected_issue=f"Look-alike domain {h.host} received an HTTPS certificate: {top.get('title', 'possible impersonation')}",
            findings=h.findings or [], confidence=float(top.get("confidence", 0.5)), risk=h.risk, status="Under Investigation",
            recommended_response="Check the site. If it impersonates the brand, report it to the registrar and hosting provider, "
                                 "and file a takedown with the certificate issuer.",
            created_by=who, history=[{"status": "Under Investigation", "by": who, "note": "Opened from the domain watch",
                                      "at": now.isoformat() + "Z"}], created_at=now, updated_at=now)
        db.add(inc)
        h.incident_id = inc.id
    h.status = body.status
    db.commit()
    return _hit(h)
