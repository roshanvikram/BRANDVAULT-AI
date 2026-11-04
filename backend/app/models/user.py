import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base

# Role-based access control roles.
ROLE_ADMIN = "Administrator"
ROLE_CREATOR = "Creator"
ROLE_REVIEWER = "Reviewer"
VALID_ROLES = {ROLE_ADMIN, ROLE_CREATOR, ROLE_REVIEWER}


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role: Mapped[str] = mapped_column(String(40), default=ROLE_CREATOR)  # see VALID_ROLES
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    # PBKDF2-HMAC-SHA256 credential material (never the plaintext). Nullable so
    # that federated (Google OAuth) accounts, which have no local password, can
    # exist — for those we still store high-entropy unusable values as defence
    # in depth so the password-login path can never match.
    salt: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    # How this account authenticates: "password" (local) or "google" (federated).
    auth_provider: Mapped[str] = mapped_column(String(20), default="password")
    # Google's stable subject id, set only for google-provisioned accounts.
    google_sub: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
