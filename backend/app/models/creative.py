"""Round 3 models: creative inspections and per-organisation settings."""
import datetime
import uuid
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class CreativeInspection(Base):
    """OCR + brand checks on an image, PDF deck or video (Improvement 1)."""
    __tablename__ = "creative_inspections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    submission_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_ref: Mapped[str] = mapped_column(String(80), nullable=False)
    mime: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)          # image | pdf | video
    pages: Mapped[list] = mapped_column(JSON, default=list)                # [{index,label,width,height,image_ref,source,lines}]
    corrections: Mapped[list] = mapped_column(JSON, default=list)         # brand-vocabulary OCR fixes
    regions: Mapped[list] = mapped_column(JSON, default=list)             # finding/claim -> page + box
    logo_checks: Mapped[list] = mapped_column(JSON, default=list)
    text_found: Mapped[bool] = mapped_column(Boolean, default=False)
    engine: Mapped[str] = mapped_column(String(60), default="")
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    elapsed_ms: Mapped[float] = mapped_column(Float, default=0.0)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class OrgSetting(Base):
    """Administrator-managed settings for one organisation (JSON document)."""
    __tablename__ = "org_settings"

    org_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
