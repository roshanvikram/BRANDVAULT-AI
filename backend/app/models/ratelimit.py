"""Shared rate-limit counters (one row per bucket, client and minute)."""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class RateLimitCounter(Base):
    __tablename__ = "rate_limit_counters"

    bucket: Mapped[str] = mapped_column(String(40), primary_key=True)
    client: Mapped[str] = mapped_column(String(120), primary_key=True)
    window: Mapped[int] = mapped_column(Integer, primary_key=True)  # unix minute
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
