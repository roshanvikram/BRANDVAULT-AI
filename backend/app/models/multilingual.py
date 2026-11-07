"""Translation Guard records: a multilingual campaign and its translations."""
import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


class MultilingualCampaign(Base):
    __tablename__ = "multilingual_campaigns"
    __table_args__ = (Index("ix_mlc_org_created", "org_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_lang: Mapped[str] = mapped_column(String(10), nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, default=100)  # lowest translation score
    verdict: Mapped[str] = mapped_column(String(40), default="Consistent")
    engine: Mapped[str] = mapped_column(String(60), default="deterministic")
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_by_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    translations: Mapped[list["CampaignTranslation"]] = relationship(
        "CampaignTranslation", back_populates="campaign", cascade="all, delete-orphan",
        order_by="CampaignTranslation.position")


class CampaignTranslation(Base):
    __tablename__ = "campaign_translations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("multilingual_campaigns.id"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    label: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    detected_lang: Mapped[str] = mapped_column(String(10), nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, default=100)
    verdict: Mapped[str] = mapped_column(String(40), default="Consistent")
    result: Mapped[dict] = mapped_column(JSON, default=dict)  # scores, findings, numbers, corrected text
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    campaign: Mapped["MultilingualCampaign"] = relationship("MultilingualCampaign", back_populates="translations")
