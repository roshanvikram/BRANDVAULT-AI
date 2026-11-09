"""
Event hub (Round 3 · Improvement 2).

``emit(db, org_id, event, data)`` is called when something happens (analysis
completed, review decided, passport issued/superseded, incident opened). It:

1. stores an in-app notification for the roles that need to act;
2. queues a signed webhook delivery for every active webhook subscribed to the event;
3. posts to Slack / sends email when the organisation has configured them.

External deliveries run on a background thread with retries, so a slow or
failing receiver never blocks a reviewer. Every webhook attempt is logged in
``webhook_deliveries``. Nothing is sent to an address that is not a public
HTTPS host (local addresses are allowed only outside production).
"""
from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import smtplib
import threading
import time
import uuid
from email.message import EmailMessage
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.models.integration import Notification, Webhook, WebhookDelivery
from backend.app.models.user import ROLE_ADMIN, ROLE_CREATOR, ROLE_REVIEWER

EVENTS: Dict[str, Dict] = {
    "analysis.completed": {"label": "Analysis completed — ready for review", "roles": [ROLE_REVIEWER, ROLE_ADMIN]},
    "review.decided": {"label": "Review decision recorded", "roles": [ROLE_CREATOR, ROLE_REVIEWER, ROLE_ADMIN]},
    "passport.issued": {"label": "Brand Passport issued", "roles": []},
    "passport.superseded": {"label": "Brand Passport superseded by an edit", "roles": [ROLE_REVIEWER, ROLE_ADMIN]},
    "publish_gate.blocked": {"label": "Publishing gate blocked unapproved copy", "roles": [ROLE_REVIEWER, ROLE_ADMIN]},
    "incident.opened": {"label": "Suspected impersonation incident opened", "roles": [ROLE_REVIEWER, ROLE_ADMIN]},
}

# Swappable for tests.
session_factory: Callable[[], Session] = SessionLocal
SYNC = False                       # deliver inline instead of on a thread (tests)
RETRY_DELAYS = (0.0, 2.0, 8.0)     # three attempts


def _post(url: str, body: bytes, headers: Dict[str, str], timeout: float = 6.0) -> Tuple[int, str]:
    import httpx
    r = httpx.post(url, content=body, headers=headers, timeout=timeout, follow_redirects=False)
    return r.status_code, r.text[:300]


sender: Callable[[str, bytes, Dict[str, str]], Tuple[int, str]] = _post


def url_allowed(url: str) -> Tuple[bool, str]:
    """HTTPS to a public host. Plain HTTP/localhost only outside production (for local testing)."""
    try:
        u = urlparse(url)
    except ValueError:
        return False, "Not a valid URL."
    if not u.hostname:
        return False, "The URL has no host."
    prod = settings.ENVIRONMENT.lower() == "production"
    if u.scheme != "https" and (prod or u.scheme != "http"):
        return False, "Webhook URLs must use https."
    from backend.app.services.fraud import _public_host
    if not _public_host(u.hostname):
        if prod or u.hostname not in ("localhost", "127.0.0.1"):
            return False, "The host must be a public internet address."
    return True, ""


def sign(secret: str, timestamp: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()


def _deliver(delivery_id: str, caller_db: Optional[Session] = None) -> None:
    """Send one delivery with retries. Threads use their own session; synchronous
    mode (tests) reuses the caller's session so no second connection is needed."""
    db = caller_db or session_factory()
    try:
        d = db.get(WebhookDelivery, delivery_id)
        hook = db.get(Webhook, d.webhook_id) if d else None
        if not d or not hook:
            return
        body = json.dumps(d.payload, separators=(",", ":"), default=str).encode()
        for i, delay in enumerate(RETRY_DELAYS):
            if delay and not SYNC:
                time.sleep(delay)
            ts = str(int(time.time()))
            headers = {"Content-Type": "application/json", "User-Agent": "BrandVault-Webhooks/1.0",
                       "X-BrandVault-Event": d.event, "X-BrandVault-Delivery": d.id, "X-BrandVault-Timestamp": ts,
                       "X-BrandVault-Signature": sign(hook.secret, ts, body)}
            d.attempts = i + 1
            try:
                code, text = sender(hook.url, body, headers)
                d.status_code = code
                if 200 <= code < 300:
                    d.status, d.error, d.delivered_at = "delivered", None, datetime.datetime.utcnow()
                    db.commit()
                    return
                d.error = f"HTTP {code}: {text}"
            except Exception as exc:  # network errors are recorded, never raised to the user
                d.error = f"{type(exc).__name__}: {exc}"[:500]
            db.commit()
        d.status = "failed"
        db.commit()
    finally:
        if caller_db is None:
            db.close()


def _run(fn, *args, db: Optional[Session] = None) -> None:
    if SYNC:
        fn(*args, db) if db is not None else fn(*args)
    else:
        threading.Thread(target=fn, args=args, daemon=True).start()


# ------------------------------ Slack / email ---------------------------------
def email_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


def _send_email(to: str, subject: str, text: str) -> None:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = settings.SMTP_FROM, to, subject
    msg.set_content(text)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
        s.starttls()
        if settings.SMTP_USER:
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        s.send_message(msg)


def _external(notification_id: str, slack_url: str, email_to: str, title: str, text: str) -> None:
    status: Dict[str, str] = {}
    if slack_url:
        try:
            code, _ = sender(slack_url, json.dumps({"text": f"*{title}*\n{text}"}).encode(), {"Content-Type": "application/json"})
            status["slack"] = "sent" if 200 <= code < 300 else f"failed (HTTP {code})"
        except Exception as exc:
            status["slack"] = f"failed ({type(exc).__name__})"
    if email_to:
        if not email_configured():
            status["email"] = "not configured (SMTP settings missing)"
        else:
            try:
                _send_email(email_to, f"[BrandVault] {title}", text)
                status["email"] = "sent"
            except Exception as exc:
                status["email"] = f"failed ({type(exc).__name__})"
    if status:
        db = session_factory()
        try:
            n = db.get(Notification, notification_id)
            if n:
                n.channels = status
                db.commit()
        finally:
            db.close()


# ----------------------------------- emit -------------------------------------
def emit(db: Session, org_id: str, event: str, data: Dict, *, title: str, body: str = "",
         link: Optional[str] = None, roles: Optional[List[str]] = None) -> Notification:
    """Record the event and fan it out. Commits its own rows."""
    from backend.app.services import org_settings
    spec = EVENTS.get(event, {"roles": []})
    n = Notification(id=str(uuid.uuid4()), org_id=org_id, event=event, title=title[:255], body=body, link=link,
                     roles=list(spec["roles"] if roles is None else roles), read_by=[], channels={})
    db.add(n)
    payload = {"id": str(uuid.uuid4()), "event": event, "created_at": datetime.datetime.utcnow().isoformat() + "Z",
               "organization_id": org_id, "data": data}
    deliveries = []
    for hook in db.query(Webhook).filter(Webhook.org_id == org_id, Webhook.active == True).all():  # noqa: E712
        if event in (hook.events or []) or "*" in (hook.events or []):
            d = WebhookDelivery(id=str(uuid.uuid4()), org_id=org_id, webhook_id=hook.id, event=event, payload=payload)
            db.add(d)
            deliveries.append(d.id)
    db.commit()
    for did in deliveries:
        _run(_deliver, did, db=db)
    prefs = org_settings.get(db, org_id).get("notifications", {})
    if event in prefs.get("events", []) and (prefs.get("slack_webhook_url") or prefs.get("email")):
        slack = prefs.get("slack_webhook_url") or ""
        if slack and not url_allowed(slack)[0]:
            slack = ""
        _run(_external, n.id, slack, prefs.get("email") or "", title, body)
    return n


def test_delivery(db: Session, hook: Webhook) -> WebhookDelivery:
    d = WebhookDelivery(id=str(uuid.uuid4()), org_id=hook.org_id, webhook_id=hook.id, event="webhook.test",
                        payload={"id": str(uuid.uuid4()), "event": "webhook.test", "organization_id": hook.org_id,
                                 "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                                 "data": {"message": "Test delivery from BrandVault AI"}})
    db.add(d)
    db.commit()
    _run(_deliver, d.id, db=db)
    return d
