"""Phase 3 records: simulations, similarity dismissals, fraud incidents,
official domains and reputation feedback."""
import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base


class SimulationRun(Base):
    """A hypothetical what-if. Never linked to changes of the real campaign."""
    __tablename__ = "simulation_runs"
    __table_args__ = (Index("ix_sim_org_created", "org_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id"), nullable=False)
    submission_version: Mapped[int] = mapped_column(Integer, nullable=False)
    scenario: Mapped[str] = mapped_column(String(40), nullable=False)
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class SimilarityDismissal(Base):
    """An investigator marked a similarity match as a false positive."""
    __tablename__ = "similarity_dismissals"
    __table_args__ = (UniqueConstraint("org_id", "pair_key", name="uq_sim_dismiss_pair"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    pair_key: Mapped[str] = mapped_column(String(200), nullable=False)   # sorted "kind:id|kind:id" or "text:<sha>|kind:id"
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    dismissed_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class OfficialDomain(Base):
    __tablename__ = "official_domains"
    __table_args__ = (UniqueConstraint("org_id", "domain", name="uq_official_domain"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    added_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


INCIDENT_STATUSES = ("Under Investigation", "Confirmed", "False Positive", "Resolved", "Escalated")


class FraudIncident(Base):
    __tablename__ = "fraud_incidents"
    __table_args__ = (Index("ix_incident_org_created", "org_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)    # BV-INC-XXXXXX
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    source_kind: Mapped[str] = mapped_column(String(20), nullable=False)             # url | text | image | mixed
    evidence_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # preserved screenshot/image
    evidence_mime: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    evidence_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    text_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    detected_issue: Mapped[str] = mapped_column(Text, nullable=False)
    findings: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    risk: Mapped[str] = mapped_column(String(20), nullable=False)                     # high | medium | low
    status: Mapped[str] = mapped_column(String(30), default="Under Investigation")
    recommended_response: Mapped[str] = mapped_column(Text, nullable=False)
    history: Mapped[list] = mapped_column(JSON, default=list)                         # append-only status log
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class FeedbackRecord(Base):
    __tablename__ = "feedback_records"
    __table_args__ = (Index("ix_feedback_org_date", "org_id", "feedback_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    batch_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)           # file name or "manual"
    channel: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    product: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False)         # positive | neutral | negative
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_engine: Mapped[str] = mapped_column(String(40), default="lexicon")
    categories: Mapped[list] = mapped_column(JSON, default=list)
    uploaded_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
