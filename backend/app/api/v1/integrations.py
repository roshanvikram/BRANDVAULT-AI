"""
Integrations (Round 3 · Improvement 2).

Signed-in routes:  API keys and webhooks (Administrator), notifications, channel checks.
Public routes:     /public/* authenticated with an organisation API key (X-API-Key) — the
                   Check API, the publishing gate and read-only lookups used by CI/CMS
                   scripts and the MCP server. No public route can approve or publish.
"""
from __future__ import annotations

from backend.app.db.rls import set_tenant

import datetime
import hashlib
import secrets
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.core.config import settings
from backend.app.core.ratelimit import rate_limit
from backend.app.db.session import get_db
from backend.app.models.brand import ApprovedFact, Organization, TerminologyRule
from backend.app.models.integration import ApiKey, Notification, Webhook, WebhookDelivery
from backend.app.models.product import Product
from backend.app.models.submission import Submission
from backend.app.models.user import ROLE_ADMIN, User
from backend.app.services import channels as channel_svc
from backend.app.services import events, integrity, org_settings
from backend.app.services.analyzer import ContentAnalyzerService

router = APIRouter(tags=["Integrations"])
AI_LIMIT = [Depends(rate_limit("ai", settings.RATE_LIMIT_AI_PER_MIN))]
SCOPES = {"check": "Run brand checks", "gate": "Publishing gate", "read": "Read brand facts and review status"}


# ---------------------------------------------------------------- API keys ----
def _hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def _key_out(k: ApiKey) -> Dict[str, Any]:
    return {"id": k.id, "name": k.name, "prefix": k.prefix, "scopes": k.scopes, "created_by": k.created_by,
            "created_at": k.created_at.isoformat() if k.created_at else None,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "use_count": k.use_count, "revoked": k.revoked_at is not None}


class KeyIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    scopes: List[str] = Field(default_factory=lambda: ["check", "gate", "read"])


@router.get("/integrations/api-keys")
def list_keys(db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    rows = db.query(ApiKey).filter(ApiKey.org_id == current.org_id).order_by(ApiKey.created_at.desc()).all()
    return {"keys": [_key_out(k) for k in rows], "scopes": SCOPES}


@router.post("/integrations/api-keys")
def create_key(payload: KeyIn, db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    bad = [s for s in payload.scopes if s not in SCOPES]
    if bad or not payload.scopes:
        raise HTTPException(status_code=422, detail=f"Scopes must be chosen from: {', '.join(SCOPES)}.")
    raw = "bv_" + secrets.token_hex(24)
    k = ApiKey(id=str(uuid.uuid4()), org_id=current.org_id, name=payload.name.strip(), prefix=raw[:10],
               key_hash=_hash(raw), scopes=sorted(set(payload.scopes)), created_by=f"{current.full_name} ({current.role})")
    db.add(k)
    db.commit()
    return {"key": raw, "api_key": _key_out(k), "note": "Copy this key now. BrandVault stores only a hash and cannot show it again."}


@router.delete("/integrations/api-keys/{key_id}")
def revoke_key(key_id: str, db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    k = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.org_id == current.org_id).first()
    if not k:
        raise HTTPException(status_code=404, detail="Key not found")
    k.revoked_at = k.revoked_at or datetime.datetime.utcnow()
    db.commit()
    return _key_out(k)


def api_key_org(scope: str):
    def dep(x_api_key: Optional[str] = Header(default=None), db: Session = Depends(get_db)) -> ApiKey:
        if not x_api_key:
            raise HTTPException(status_code=401, detail="Missing X-API-Key header.")
        k = db.query(ApiKey).filter(ApiKey.key_hash == _hash(x_api_key.strip())).first()
        if k is None or k.revoked_at is not None:
            raise HTTPException(status_code=401, detail="Invalid or revoked API key.")
        if scope not in (k.scopes or []):
            raise HTTPException(status_code=403, detail=f"This API key does not have the '{scope}' scope.")
        k.last_used_at = datetime.datetime.utcnow()
        k.use_count = (k.use_count or 0) + 1
        db.commit()
        set_tenant(db, k.org_id)  # database-level isolation for the rest of the request
        return k
    return dep


# ---------------------------------------------------------------- webhooks ----
class HookIn(BaseModel):
    url: str = Field(min_length=8, max_length=500)
    events: List[str] = Field(default_factory=lambda: list(events.EVENTS))


def _hook_out(h: Webhook, db: Session) -> Dict[str, Any]:
    last = (db.query(WebhookDelivery).filter(WebhookDelivery.webhook_id == h.id)
            .order_by(WebhookDelivery.created_at.desc()).first())
    return {"id": h.id, "url": h.url, "events": h.events, "active": h.active, "created_by": h.created_by,
            "created_at": h.created_at.isoformat() if h.created_at else None,
            "secret_hint": h.secret[:6] + "…", "last_status": last.status if last else None}


@router.get("/integrations/webhooks")
def list_hooks(db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    rows = db.query(Webhook).filter(Webhook.org_id == current.org_id).order_by(Webhook.created_at.desc()).all()
    return {"webhooks": [_hook_out(h, db) for h in rows],
            "events": {k: v["label"] for k, v in events.EVENTS.items()}}


@router.post("/integrations/webhooks")
def create_hook(payload: HookIn, db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    ok, why = events.url_allowed(payload.url.strip())
    if not ok:
        raise HTTPException(status_code=422, detail=why)
    bad = [e for e in payload.events if e not in events.EVENTS and e != "*"]
    if bad or not payload.events:
        raise HTTPException(status_code=422, detail=f"Unknown event(s): {', '.join(bad) or 'none selected'}.")
    h = Webhook(id=str(uuid.uuid4()), org_id=current.org_id, url=payload.url.strip(), secret="whsec_" + secrets.token_hex(20),
                events=payload.events, created_by=f"{current.full_name} ({current.role})")
    db.add(h)
    db.commit()
    return {"webhook": _hook_out(h, db), "secret": h.secret,
            "note": "Verify X-BrandVault-Signature = sha256=HMAC_SHA256(secret, timestamp + '.' + body)."}


@router.delete("/integrations/webhooks/{hook_id}")
def delete_hook(hook_id: str, db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    h = db.query(Webhook).filter(Webhook.id == hook_id, Webhook.org_id == current.org_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Webhook not found")
    h.active = False  # kept for the delivery history
    db.commit()
    return _hook_out(h, db)


@router.post("/integrations/webhooks/{hook_id}/test")
def test_hook(hook_id: str, db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    h = db.query(Webhook).filter(Webhook.id == hook_id, Webhook.org_id == current.org_id, Webhook.active == True).first()  # noqa: E712
    if not h:
        raise HTTPException(status_code=404, detail="Webhook not found")
    d = events.test_delivery(db, h)
    return {"delivery_id": d.id, "status": "queued"}


@router.get("/integrations/deliveries")
def list_deliveries(db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    rows = (db.query(WebhookDelivery).filter(WebhookDelivery.org_id == current.org_id)
            .order_by(WebhookDelivery.created_at.desc()).limit(50).all())
    return [{"id": d.id, "webhook_id": d.webhook_id, "event": d.event, "status": d.status, "status_code": d.status_code,
             "attempts": d.attempts, "error": d.error, "created_at": d.created_at.isoformat() if d.created_at else None,
             "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None} for d in rows]


# ----------------------------------------------------------- notifications ----
def _visible(n: Notification, user: User) -> bool:
    return not n.roles or user.role in n.roles


@router.get("/notifications")
def list_notifications(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    rows = (db.query(Notification).filter(Notification.org_id == current.org_id)
            .order_by(Notification.created_at.desc()).limit(100).all())
    mine = [n for n in rows if _visible(n, current)][:40]
    return {"unread": sum(1 for n in mine if current.id not in (n.read_by or [])),
            "email_configured": events.email_configured(),
            "items": [{"id": n.id, "event": n.event, "title": n.title, "body": n.body, "link": n.link,
                       "read": current.id in (n.read_by or []), "channels": n.channels or {},
                       "created_at": n.created_at.isoformat() if n.created_at else None} for n in mine]}


@router.post("/notifications/read")
def mark_read(ids: Optional[List[str]] = None, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    q = db.query(Notification).filter(Notification.org_id == current.org_id)
    if ids:
        q = q.filter(Notification.id.in_(ids))
    n_marked = 0
    for n in q.all():
        if _visible(n, current) and current.id not in (n.read_by or []):
            n.read_by = list(n.read_by or []) + [current.id]
            n_marked += 1
    db.commit()
    return {"marked": n_marked}


# ------------------------------------------------------------ browser push ----
class PushKeys(BaseModel):
    p256dh: str = Field(min_length=20, max_length=200)
    auth: str = Field(min_length=8, max_length=60)


class PushSubIn(BaseModel):
    endpoint: str = Field(min_length=12, max_length=1000)
    keys: PushKeys


def _push_endpoint_ok(url: str) -> bool:
    from urllib.parse import urlparse
    u = urlparse(url)
    return u.scheme == "https" and bool(u.netloc)


@router.get("/push/public-key")
def push_public_key(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    from backend.app.models.push import PushSubscription
    from backend.app.services import webpush
    n = db.query(PushSubscription).filter(PushSubscription.user_id == current.id).count()
    return {"public_key": webpush.public_key(db), "subscriptions": n}


@router.post("/push/subscribe")
def push_subscribe(payload: PushSubIn, user_agent: Optional[str] = Header(default=None),
                   db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    from backend.app.models.push import PushSubscription
    if not _push_endpoint_ok(payload.endpoint):
        raise HTTPException(status_code=400, detail="Push endpoint must be an https URL from the browser.")
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == payload.endpoint).first()
    if sub is None:
        sub = PushSubscription(endpoint=payload.endpoint, org_id=current.org_id, user_id=current.id,
                               p256dh=payload.keys.p256dh, auth=payload.keys.auth, user_agent=(user_agent or "")[:300])
        db.add(sub)
    else:  # the same browser, possibly a different user now
        sub.org_id, sub.user_id, sub.p256dh, sub.auth = current.org_id, current.id, payload.keys.p256dh, payload.keys.auth
    db.commit()
    return {"subscribed": True}


@router.post("/push/unsubscribe")
def push_unsubscribe(payload: PushSubIn, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    from backend.app.models.push import PushSubscription
    n = db.query(PushSubscription).filter(PushSubscription.endpoint == payload.endpoint,
                                          PushSubscription.user_id == current.id).delete()
    db.commit()
    return {"removed": n}


@router.post("/push/test")
def push_test(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    """Send a test notification to this user's own browsers."""
    from backend.app.models.push import PushSubscription
    from backend.app.services import webpush
    subs = db.query(PushSubscription).filter(PushSubscription.user_id == current.id).all()
    if not subs:
        raise HTTPException(status_code=400, detail="Turn on browser notifications first.")
    sent = 0
    for sub in subs:
        try:
            code, _ = webpush.send(db, sub, {"title": "BrandVault test notification",
                                             "body": "Browser notifications are working.", "link": "/settings"},
                                   poster=events.push_poster)
        except Exception:
            continue
        if code in (404, 410):
            db.delete(sub)
        elif 200 <= code < 300:
            sent += 1
    db.commit()
    return {"sent": sent, "devices": len(subs)}


# ---------------------------------------------------------- channel checks ----
class ChannelIn(BaseModel):
    text: str = Field(default="", max_length=20000)
    channels: List[str] = Field(default_factory=list)
    region: Optional[str] = Field(default=None, max_length=10)
    width: Optional[int] = None
    height: Optional[int] = None


def _channel_report(db: Session, org_id: str, p: ChannelIn) -> Dict[str, Any]:
    cfg = org_settings.get(db, org_id)
    ch = channel_svc.check_channels(p.text, cfg["channels"], p.channels, p.width, p.height)
    dis = channel_svc.check_disclaimers(p.text, cfg["disclaimers"], p.region)
    return {"channels": ch, "disclaimers": dis,
            "ok": all(c["ok"] for c in ch) and all(d["ok"] for d in dis),
            "available_channels": {k: v["label"] for k, v in cfg["channels"].items()}}


@router.post("/channels/check")
def channel_check(payload: ChannelIn, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return _channel_report(db, current.org_id, payload)


# ------------------------------------------------------------- public API ----
class CheckIn(ChannelIn):
    title: Optional[str] = Field(default=None, max_length=255)
    persist: bool = False
    department: Optional[str] = Field(default=None, max_length=100)


def _analysis(db: Session, org_id: str, p: CheckIn, actor: str) -> Dict[str, Any]:
    if len(p.text.strip()) < 3:
        raise HTTPException(status_code=422, detail="Provide the copy to check in 'text'.")
    svc = ContentAnalyzerService(db)
    title = p.title or "API check"
    if p.persist:
        sub = svc.analyze_submission(org_id, title, p.text, author_name=actor)
        sub.department = p.department
        db.commit()  # the analyzer already notified reviewers and webhooks
        result = {"submission_id": sub.id, "score": sub.overall_score, "status": sub.status,
                  "findings": [{"category": f.issue_category, "severity": f.severity, "text": f.original_text,
                                "explanation": f.explanation, "suggestion": f.suggested_correction} for f in sub.findings],
                  "claims": [{"text": c.claim_text, "status": c.status, "category": c.category} for c in sub.claim_verifications]}
    else:
        snap = svc.analyze_submission(org_id, title, p.text, author_name=actor, dry_run=True)
        result = {"submission_id": None, "score": snap["score"], "status": "not saved (persist=false)",
                  "findings": [{k: f[k] for k in ("category", "severity", "text", "explanation", "suggestion")} for f in snap["findings"]],
                  "claims": [{k: c[k] for k in ("text", "status", "category")} for c in snap["claims"]]}
    result.update(_channel_report(db, org_id, p))
    result["publishable"] = False
    result["note"] = "Checks advise only. Publishing requires an approved Brand Passport (use the publishing gate)."
    return result


@router.post("/public/check", dependencies=AI_LIMIT)
def public_check(payload: CheckIn, db: Session = Depends(get_db), key: ApiKey = Depends(api_key_org("check"))):
    return _analysis(db, key.org_id, payload, f"API: {key.name}")


class GateIn(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    reference: Optional[str] = Field(default=None, max_length=255)


@router.post("/public/gate")
def public_gate(payload: GateIn, db: Session = Depends(get_db), key: ApiKey = Depends(api_key_org("gate"))):
    """Allow publishing only when the copy is identical to a current Brand Passport."""
    row = integrity.verify_campaign(db, key.org_id, text=payload.text, file_name=payload.reference, file_bytes=None,
                                    checked_by=f"Publishing gate (API key {key.prefix}…)")
    allowed = row.result == integrity.VERIFIED
    if not allowed:
        events.emit(db, key.org_id, "publish_gate.blocked",
                    {"result": row.result, "reference": payload.reference, "check_id": row.id},
                    title=f"Publishing blocked: {row.result}", body=row.explanation, link="/brand-passport/verify")
    return {"allowed": allowed, "result": row.result, "explanation": row.explanation,
            "passport_number": row.matched_passport_number, "check_id": row.id,
            "diff": (row.details or {}).get("diff") if not allowed else None}


@router.get("/public/brand")
def public_brand(db: Session = Depends(get_db), key: ApiKey = Depends(api_key_org("read"))):
    org = db.get(Organization, key.org_id)
    return {"organization": org.name if org else None,
            "products": [p.name for p in db.query(Product).filter(Product.org_id == key.org_id).all()],
            "approved_facts": [{"key": f.fact_key, "value": f.fact_value, "source": f.verification_source}
                               for f in db.query(ApprovedFact).filter(ApprovedFact.org_id == key.org_id).all()],
            "terminology": [{"avoid": t.prohibited_term, "use": t.preferred_term}
                            for t in db.query(TerminologyRule).filter(TerminologyRule.org_id == key.org_id).all()]}


class SearchIn(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    top_k: int = Field(default=3, ge=1, le=8)


@router.post("/public/search")
def public_search(payload: SearchIn, db: Session = Depends(get_db), key: ApiKey = Depends(api_key_org("read"))):
    from backend.app.services.rag import RagRetriever
    return {"results": RagRetriever(db).search(key.org_id, payload.query, top_k=payload.top_k)}


@router.get("/public/submissions/{submission_id}")
def public_submission(submission_id: str, db: Session = Depends(get_db), key: ApiKey = Depends(api_key_org("read"))):
    sub = db.query(Submission).filter(Submission.id == submission_id, Submission.org_id == key.org_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    p = sub.passport
    return {"id": sub.id, "title": sub.title, "status": sub.status, "version": sub.version, "score": sub.overall_score,
            "passport": {"number": p.passport_number, "status": p.verification_status} if p else None}
