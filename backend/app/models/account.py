"""Company readiness: team invitations, the security audit trail, server errors
and Certificate Transparency watch hits."""
import datetime
import uuid
from typing import Optional

from sqlalchemy import JSON, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def _id() -> str:
    return uuid.uuid4().hex


class Invite(Base):
    """An administrator's invitation for one email address to join the workspace with a role."""
    __tablename__ = "invites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # sha256; the link holds the token
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    accepted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    email_status: Mapped[str] = mapped_column(String(60), default="not sent")


class SecurityEvent(Base):
    """Append-only security audit trail: sign-ins, lockouts, MFA, role changes, exports, deletions."""
    __tablename__ = "security_events"
    __table_args__ = (Index("ix_security_org_created", "org_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    actor: Mapped[str] = mapped_column(String(255), default="")      # email of who did it
    action: Mapped[str] = mapped_column(String(60), nullable=False)  # e.g. login.failed
    target: Mapped[str] = mapped_column(String(255), default="")
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    ip: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, index=True)


class ErrorEvent(Base):
    """An unhandled server error, kept so administrators can see failures without server logs."""
    __tablename__ = "error_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    request_id: Mapped[str] = mapped_column(String(40), default="")
    method: Mapped[str] = mapped_column(String(10), default="")
    path: Mapped[str] = mapped_column(String(300), default="")
    error_type: Mapped[str] = mapped_column(String(120), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, index=True)


class DomainWatchHit(Base):
    """A newly certified domain (public Certificate Transparency logs) that looks like the brand."""
    __tablename__ = "domain_watch_hits"
    __table_args__ = (UniqueConstraint("org_id", "host", name="uq_watch_org_host"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    matched_term: Mapped[str] = mapped_column(String(100), default="")
    issuer: Mapped[str] = mapped_column(String(300), default="")
    cert_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    not_before: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    findings: Mapped[list] = mapped_column(JSON, default=list)
    risk: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="new")  # new | dismissed | incident
    incident_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    first_seen: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
