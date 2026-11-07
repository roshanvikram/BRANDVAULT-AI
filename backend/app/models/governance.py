"""Phase 2 governance records: launch-readiness configuration and reports."""
import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base


class LaunchCheckConfig(Base):
    """Per-organisation launch policy. One row per org (admin-editable)."""
    __tablename__ = "launch_check_configs"

    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), primary_key=True)
    mandatory: Mapped[list] = mapped_column(JSON, default=list)          # check keys that block launch
    approval_validity_days: Mapped[int] = mapped_column(Integer, default=90)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class LaunchReadinessReport(Base):
    """A persisted readiness evaluation of one campaign version."""
    __tablename__ = "launch_readiness_reports"
    __table_args__ = (Index("ix_launch_reports_sub", "submission_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id"), nullable=False)
    submission_version: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(40), nullable=False)
    report: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
