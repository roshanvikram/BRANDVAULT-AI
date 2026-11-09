"""Durable file storage (uploaded assets, investigation images, incident evidence).

Files live in the database so they survive container restarts on hosts with a
temporary disk (e.g. Render's free plan) and move with the database to
PostgreSQL. Every row is scoped to one organisation.
"""
import datetime
import uuid

from sqlalchemy import DateTime, Integer, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class StoredFile(Base):
    __tablename__ = "stored_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    folder: Mapped[str] = mapped_column(String(40), nullable=False)
    mime: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
