"""Round 3 · Improvement 2 models: API keys, webhooks, deliveries, in-app notifications."""
import datetime
import uuid
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def _id() -> str:
    return str(uuid.uuid4())


class ApiKey(Base):
    """Organisation API key for the public Check API, publish gate and MCP server.
    Only a SHA-256 hash is stored; the full key is shown once at creation."""
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    scopes: Mapped[list] = mapped_column(JSON, default=list)          # check | gate | read
    created_by: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    last_used_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(80), nullable=False)    # HMAC signing secret
    events: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    webhook_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    event: Mapped[str] = mapped_column(String(60), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | delivered | failed
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    delivered_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)


class Notification(Base):
    """In-app notification for an organisation; `roles` limits who sees it (empty = everyone)."""
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_id)
    org_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    event: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")
    link: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    roles: Mapped[list] = mapped_column(JSON, default=list)
    read_by: Mapped[list] = mapped_column(JSON, default=list)
    channels: Mapped[dict] = mapped_column(JSON, default=dict)          # email/slack delivery status
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
