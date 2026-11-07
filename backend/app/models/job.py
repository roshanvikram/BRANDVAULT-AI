"""Durable background job record (Phase 1a).

Job state lives in the database, so a page refresh or a server restart never
loses it. Status values are real transitions written by the worker:
queued -> processing -> completed | failed, or queued -> cancelled.
"""
import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, JSON, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base

JOB_QUEUED = "queued"
JOB_PROCESSING = "processing"
JOB_COMPLETED = "completed"
JOB_FAILED = "failed"
JOB_CANCELLED = "cancelled"
TERMINAL_STATES = {JOB_COMPLETED, JOB_FAILED, JOB_CANCELLED}


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("org_id", "idempotency_key", name="uq_jobs_org_idempotency"),
        Index("ix_jobs_org_created", "org_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. content_analysis
    status: Mapped[str] = mapped_column(String(20), default=JOB_QUEUED, nullable=False)
    stage: Mapped[str] = mapped_column(String(255), default="Queued")
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=2)
    input_data: Mapped[dict] = mapped_column(JSON, default=dict)
    result_ref: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # e.g. submission id
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
