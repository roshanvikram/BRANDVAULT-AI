import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.submission import Submission

class BrandPassport(Base):
    __tablename__ = "brand_passports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    passport_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # e.g. BV-2026-8941
    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id"), unique=True, nullable=False)
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False) # SHA-256
    guideline_version: Mapped[str] = mapped_column(String(50), default="v2.4")
    verification_status: Mapped[str] = mapped_column(String(50), default="PASSED") # PASSED, CONDITIONALLY_PASSED, REJECTED
    final_score: Mapped[int] = mapped_column(Integer, default=100)
    audited_by: Mapped[str] = mapped_column(String(100), default="BRANDVAULT Governance Engine & Reviewer")
    passport_data: Mapped[dict] = mapped_column(JSON, default=dict) # Full snapshot of rules, claims, findings, decisions
    issued_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="passport")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False) # Orchestrator, Brand Voice, Terminology, ClaimDNA, Suggestion, Guideline Gap
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED") # RUNNING, COMPLETED, FAILED
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    input_preview: Mapped[str] = mapped_column(Text, nullable=False)
    output_preview: Mapped[str] = mapped_column(Text, nullable=False)
    event_details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. GUIDELINE_UPLOADED, RULE_CONFIRMED, CONTENT_ANALYZED, APPROVED
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), default="127.0.0.1")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
