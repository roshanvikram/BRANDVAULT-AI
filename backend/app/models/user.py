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
    # PBKDF2-HMAC-SHA256 credential material (never the plaintext).
    salt: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
