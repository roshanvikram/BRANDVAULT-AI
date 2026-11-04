import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    guidelines: Mapped[list["BrandGuideline"]] = relationship("BrandGuideline", back_populates="organization", cascade="all, delete-orphan")
    rules: Mapped[list["BrandRule"]] = relationship("BrandRule", back_populates="organization", cascade="all, delete-orphan")
    facts: Mapped[list["ApprovedFact"]] = relationship("ApprovedFact", back_populates="organization", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="organization", cascade="all, delete-orphan")


class BrandGuideline(Base):
    __tablename__ = "brand_guidelines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    file_type: Mapped[str] = mapped_column(String(50), default="pdf")
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    total_pages: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="processed") # uploaded, processing, processed, error
    raw_text: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="guidelines")
    chunks: Mapped[list["DocumentChunk"]] = relationship("DocumentChunk", back_populates="guideline", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    guideline_id: Mapped[str] = mapped_column(String(36), ForeignKey("brand_guidelines.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # store vector representation

    guideline: Mapped["BrandGuideline"] = relationship("BrandGuideline", back_populates="chunks")


class BrandRule(Base):
    __tablename__ = "brand_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="Tone & Voice") # Tone, Terminology, Pricing, Claim, Visual
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_text: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), default="CRITICAL") # CRITICAL, WARNING, SUGGESTION
    source_document: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_reference: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=True) # Admin confirmation
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="rules")


class ApprovedFact(Base):
    __tablename__ = "approved_facts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="Product") # Product, Pricing, Specification, Legal, Company
    fact_key: Mapped[str] = mapped_column(String(255), nullable=False)
    fact_value: Mapped[str] = mapped_column(Text, nullable=False)
    verification_source: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="facts")


class TerminologyRule(Base):
    __tablename__ = "terminology_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False)
    prohibited_term: Mapped[str] = mapped_column(String(255), nullable=False)
    preferred_term: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)


from backend.app.models.submission import Submission
