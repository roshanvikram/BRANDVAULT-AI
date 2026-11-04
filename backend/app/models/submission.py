import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.brand import Organization
    from backend.app.models.passport import BrandPassport

class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="Draft") # Draft, Submitted, Analysing, Analysed, Pending Review, Approved, Rejected, Revision Requested
    author_name: Mapped[str] = mapped_column(String(100), default="Marketing Creator")
    author_role: Mapped[str] = mapped_column(String(50), default="Creator")
    overall_score: Mapped[int] = mapped_column(Integer, default=100) # 0-100 Brand Health / Compliance Score
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="submissions")
    findings: Mapped[list["Finding"]] = relationship("Finding", back_populates="submission", cascade="all, delete-orphan")
    claim_verifications: Mapped[list["ClaimVerification"]] = relationship("ClaimVerification", back_populates="submission", cascade="all, delete-orphan")
    approvals: Mapped[list["ApprovalRecord"]] = relationship("ApprovalRecord", back_populates="submission", cascade="all, delete-orphan")
    revisions: Mapped[list["Revision"]] = relationship("Revision", back_populates="submission", cascade="all, delete-orphan")
    passport: Mapped[Optional["BrandPassport"]] = relationship("BrandPassport", back_populates="submission", uselist=False, cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id"), nullable=False)
    issue_category: Mapped[str] = mapped_column(String(100), default="Terminology") # Tone, Terminology, Messaging, Pricing, Promotional Claim, Visual
    severity: Mapped[str] = mapped_column(String(50), default="CRITICAL") # CRITICAL, WARNING, SUGGESTION
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    rule_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_source: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.95)
    suggested_correction: Mapped[str] = mapped_column(Text, nullable=False)
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="findings")


class ClaimVerification(Base):
    __tablename__ = "claim_verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id"), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Unsupported") # Supported, Unsupported, Contradicted, Outdated, Needs Human Review
    category: Mapped[str] = mapped_column(String(100), default="Performance") # Performance, Comparative, Pricing, Feature, Environmental
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.90)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="claim_verifications")


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id"), nullable=False)
    reviewer_name: Mapped[str] = mapped_column(String(100), default="Brand Governance Lead")
    reviewer_role: Mapped[str] = mapped_column(String(50), default="Reviewer")
    decision: Mapped[str] = mapped_column(String(50), nullable=False) # Approved, Rejected, Revision Requested
    comments: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="approvals")


class Revision(Base):
    __tablename__ = "revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[str] = mapped_column(String(100), default="Creator")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="revisions")
