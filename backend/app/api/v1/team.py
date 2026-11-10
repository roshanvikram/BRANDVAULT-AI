"""Team management for a company workspace: members, roles, invitations and the security log.

Administrators invite people by email with a role (Creator, Reviewer or
Administrator). The invitation link holds a random token; only its SHA-256 is
stored. A workspace always keeps at least one active Administrator, and a role
change or deactivation signs that person out everywhere.
"""
from __future__ import annotations

import datetime
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles
from backend.app.api.v1.auth import invite_hash
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.models.account import Invite, SecurityEvent
from backend.app.models.brand import Organization
from backend.app.models.user import ROLE_ADMIN, VALID_ROLES, User
from backend.app.schemas.auth import _EMAIL_RE
from backend.app.services import audit, events

router = APIRouter(prefix="/team", tags=["Team"])
ADMIN = require_roles(ROLE_ADMIN)


def _iso(d: Optional[datetime.datetime]) -> Optional[str]:
    return d.isoformat() + "Z" if d else None


def _member(u: User) -> dict:
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role, "active": bool(u.is_active),
            "auth_provider": u.auth_provider, "mfa_enabled": bool(u.mfa_enabled),
            "last_login_at": _iso(u.last_login_at), "created_at": _iso(u.created_at)}


def _invite(i: Invite) -> dict:
    now = datetime.datetime.utcnow()
    state = ("accepted" if i.accepted_at else "revoked" if i.revoked_at else "expired" if i.expires_at < now else "pending")
    return {"id": i.id, "email": i.email, "role": i.role, "status": state, "created_by": i.created_by,
            "created_at": _iso(i.created_at), "expires_at": _iso(i.expires_at), "email_status": i.email_status}


@router.get("/members")
def members(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    rows = db.query(User).filter(User.org_id == current.org_id).order_by(User.created_at).all()
    return {"members": [_member(u) for u in rows], "can_manage": current.role == ROLE_ADMIN}


class MemberChange(BaseModel):
    role: Optional[str] = None
    active: Optional[bool] = None


def _active_admins(db: Session, org_id: str) -> int:
    return db.query(User).filter(User.org_id == org_id, User.role == ROLE_ADMIN, User.is_active == True).count()  # noqa: E712


@router.patch("/members/{user_id}")
def change_member(user_id: str, body: MemberChange, request: Request, db: Session = Depends(get_db),
                  current: User = Depends(ADMIN)):
    u = db.query(User).filter(User.id == user_id, User.org_id == current.org_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Member not found.")
    if body.role is not None and body.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"Role must be one of: {', '.join(sorted(VALID_ROLES))}.")
    loses_admin = u.role == ROLE_ADMIN and u.is_active and (
        (body.role is not None and body.role != ROLE_ADMIN) or body.active is False)
    if loses_admin and _active_admins(db, current.org_id) <= 1:
        raise HTTPException(status_code=400, detail="The workspace needs at least one active Administrator. Make someone else an Administrator first.")
    changes = {}
    if body.role is not None and body.role != u.role:
        changes["role"] = [u.role, body.role]
        u.role = body.role
    if body.active is not None and body.active != bool(u.is_active):
        changes["active"] = [bool(u.is_active), body.active]
        u.is_active = body.active
    if changes:
        u.token_version = int(u.token_version or 0) + 1  # their current sessions end
        db.commit()
        audit.record(db, "member.changed", org_id=current.org_id, actor=current.email, target=u.email,
                     detail=changes, request=request)
    return _member(u)


@router.post("/members/{user_id}/unlock")
def unlock_member(user_id: str, request: Request, db: Session = Depends(get_db), current: User = Depends(ADMIN)):
    """Clear a sign-in lockout (after too many wrong passwords)."""
    u = db.query(User).filter(User.id == user_id, User.org_id == current.org_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Member not found.")
    u.locked_until, u.failed_logins = None, 0
    db.commit()
    audit.record(db, "member.unlocked", org_id=current.org_id, actor=current.email, target=u.email, request=request)
    return _member(u)


class InviteIn(BaseModel):
    email: str
    role: str = "Creator"

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Enter a valid email address.")
        return v


@router.get("/invites")
def list_invites(db: Session = Depends(get_db), current: User = Depends(ADMIN)):
    rows = db.query(Invite).filter(Invite.org_id == current.org_id).order_by(Invite.created_at.desc()).limit(200).all()
    return {"invites": [_invite(i) for i in rows], "email_configured": events.email_configured()}


@router.post("/invites")
def create_invite(body: InviteIn, request: Request, db: Session = Depends(get_db), current: User = Depends(ADMIN)):
    if body.role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"Role must be one of: {', '.join(sorted(VALID_ROLES))}.")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Someone already has a BrandVault account with this email.")
    now = datetime.datetime.utcnow()
    for old in db.query(Invite).filter(Invite.org_id == current.org_id, Invite.email == body.email,
                                       Invite.accepted_at.is_(None), Invite.revoked_at.is_(None)).all():
        old.revoked_at = now  # one live invitation per address
    token = secrets.token_urlsafe(32)
    inv = Invite(org_id=current.org_id, email=body.email, role=body.role, token_hash=invite_hash(token),
                 created_by=current.email, expires_at=now + datetime.timedelta(days=settings.INVITE_DAYS))
    db.add(inv)
    db.commit()
    link = f"{settings.FRONTEND_URL.rstrip('/')}/signup?invite={token}"
    org = db.query(Organization).filter(Organization.id == current.org_id).first()
    if events.email_configured():
        try:
            events._send_email(body.email, f"You're invited to {org.name if org else 'a workspace'} on BrandVault",
                               f"{current.full_name} invited you to join {org.name if org else 'their workspace'} on BrandVault AI "
                               f"as {body.role}.\n\nAccept the invitation (valid {settings.INVITE_DAYS} days):\n{link}\n")
            inv.email_status = "sent"
        except Exception as exc:  # noqa: BLE001
            inv.email_status = f"failed: {type(exc).__name__}"[:60]
    else:
        inv.email_status = "email not configured"
    db.commit()
    audit.record(db, "invite.created", org_id=current.org_id, actor=current.email, target=body.email,
                 detail={"role": body.role}, request=request)
    # The link is shown once so it can be shared directly when email is not set up.
    return {"invite": _invite(inv), "link": link}


@router.delete("/invites/{invite_id}")
def revoke_invite(invite_id: str, request: Request, db: Session = Depends(get_db), current: User = Depends(ADMIN)):
    inv = db.query(Invite).filter(Invite.id == invite_id, Invite.org_id == current.org_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found.")
    if not inv.accepted_at and not inv.revoked_at:
        inv.revoked_at = datetime.datetime.utcnow()
        db.commit()
        audit.record(db, "invite.revoked", org_id=current.org_id, actor=current.email, target=inv.email, request=request)
    return _invite(inv)


@router.get("/audit")
def security_log(action: Optional[str] = None, limit: int = 200, db: Session = Depends(get_db),
                 current: User = Depends(ADMIN)):
    q = db.query(SecurityEvent).filter(SecurityEvent.org_id == current.org_id)
    if action:
        q = q.filter(SecurityEvent.action.like(f"{action}%"))
    rows = q.order_by(SecurityEvent.created_at.desc()).limit(max(1, min(limit, 1000))).all()
    return {"events": [{"id": e.id, "action": e.action, "actor": e.actor, "target": e.target, "detail": e.detail or {},
                        "ip": e.ip, "created_at": _iso(e.created_at)} for e in rows]}
