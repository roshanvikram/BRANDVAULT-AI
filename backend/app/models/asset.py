"""Brand Asset Library + asset forensics investigations.

Files live on disk under backend/storage/ (never as DB blobs); the DB keeps the
metadata, hashes and visual fingerprints used for comparison.
"""
import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base

ASSET_KINDS = ("logo", "product_image", "creative", "template", "illustration", "other")
ASSET_STATUSES = ("draft", "pending", "approved", "active", "superseded", "archived", "expired")
CURRENT_STATUSES = ("approved", "active")


class BrandAsset(Base):
    __tablename__ = "brand_assets"
    __table_args__ = (Index("ix_assets_org_kind", "org_id", "kind"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), default="logo")
    version_label: Mapped[str] = mapped_column(String(40), default="v1")
    status: Mapped[str] = mapped_column(String(20), default="approved")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime: Mapped[str] = mapped_column(String(50), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    phash: Mapped[str] = mapped_column(String(16), nullable=False)
    dhash: Mapped[str] = mapped_column(String(16), nullable=False)
    colours: Mapped[dict] = mapped_column(JSON, default=dict)  # dominant colours + mean Lab
    supersedes_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    superseded_by_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    effective_from: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[str] = mapped_column(String(100), nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


class AssetInvestigation(Base):
    __tablename__ = "asset_investigations"
    __table_args__ = (Index("ix_asset_inv_org_created", "org_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # preserved evidence
    mime: Mapped[str] = mapped_column(String(50), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    phash: Mapped[str] = mapped_column(String(16), nullable=False)
    risk: Mapped[str] = mapped_column(String(20), nullable=False)  # high | medium | low | none
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    elapsed_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    investigated_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
