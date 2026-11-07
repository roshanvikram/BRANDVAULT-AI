"""Campaign integrity checks — an append-only audit trail.

Rows are only ever inserted. There is deliberately no update or delete path in
the API, so the history of every verification is preserved.
"""
import datetime
from typing import Optional
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base

VERIFIED = "Verified Match"
MODIFIED = "Modified After Approval"
UNKNOWN_VERSION = "Unknown Version"
NEW_UNAPPROVED = "New Unapproved Campaign"
UNABLE = "Unable to Verify"


class CampaignIntegrityCheck(Base):
    __tablename__ = "campaign_integrity_checks"
    __table_args__ = (Index("ix_integrity_org_created", "org_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    checked_by: Mapped[str] = mapped_column(String(100), nullable=False)
    input_kind: Mapped[str] = mapped_column(String(20), nullable=False)  # text | file
    input_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    input_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    result: Mapped[str] = mapped_column(String(40), nullable=False)
    similarity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    matched_passport_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    matched_submission_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
