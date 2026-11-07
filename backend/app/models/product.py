"""Product Truth records: authoritative product knowledge per organisation.

A Product groups structured ProductFacts (price, battery, processor, ...).
Every fact carries its evidence (source document, page, excerpt) and a status.
Only `approved` facts that are currently valid are used as ground truth; facts
extracted by AI start as `pending` until an Administrator approves them.
"""
import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

FACT_PENDING = "pending"
FACT_APPROVED = "approved"
FACT_REJECTED = "rejected"
FACT_SUPERSEDED = "superseded"
FACT_STATUSES = {FACT_PENDING, FACT_APPROVED, FACT_REJECTED, FACT_SUPERSEDED}

# The product attributes the engine knows how to verify. Keep keys stable: they
# are stored in the DB and used by the Knowledge Gap Detector.
PRODUCT_ATTRIBUTES = {
    "price": "Approved price",
    "model_number": "Model number",
    "category": "Product category",
    "battery": "Battery",
    "processor": "Processor",
    "ai_performance": "AI performance (TOPS)",
    "memory": "Memory (RAM)",
    "storage": "Storage",
    "display": "Display",
    "weight": "Weight",
    "dimensions": "Dimensions",
    "warranty": "Warranty",
    "certification": "Certifications",
    "feature": "Supported feature",
    "performance_claim": "Approved performance claim",
    "availability": "Availability",
}


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (Index("ix_products_org_name", "org_id", "name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")  # active | discontinued
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    facts: Mapped[list["ProductFact"]] = relationship("ProductFact", back_populates="product", cascade="all, delete-orphan")


class ProductFact(Base):
    __tablename__ = "product_facts"
    __table_args__ = (Index("ix_pfacts_product_attr", "product_id", "attribute"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), nullable=False)
    attribute: Mapped[str] = mapped_column(String(40), nullable=False)
    value_text: Mapped[str] = mapped_column(Text, nullable=False)
    value_num: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    qualifier: Mapped[str] = mapped_column(String(10), default="exact")  # max | min | approx | exact
    source_document: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_reference: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    evidence_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=FACT_PENDING)
    origin: Mapped[str] = mapped_column(String(40), default="manual")  # manual | approved_fact | llm:<provider>
    valid_from: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    product: Mapped["Product"] = relationship("Product", back_populates="facts")
