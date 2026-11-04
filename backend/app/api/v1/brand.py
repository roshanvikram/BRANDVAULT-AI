import os
import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pypdf import PdfReader
from backend.app.db.session import get_db
from backend.app.models.brand import Organization, BrandGuideline, DocumentChunk, BrandRule, ApprovedFact, TerminologyRule
from backend.app.models.passport import AuditLog
from backend.app.schemas.brand import (
    OrganizationCreate, OrganizationResponse,
    BrandRuleCreate, BrandRuleResponse,
    ApprovedFactCreate, ApprovedFactResponse,
    TerminologyRuleCreate, TerminologyRuleResponse,
    BrandGuidelineResponse
)
from backend.app.services.seed import seed_sample_brand, NOVA_ORG_ID

router = APIRouter(prefix="/brand", tags=["Brand DNA Studio"])

@router.get("/workspaces", response_model=List[OrganizationResponse])
def get_workspaces(db: Session = Depends(get_db)):
    # Auto-seed sample brand if empty
    seed_sample_brand(db)
    orgs = db.query(Organization).all()
    results = []
    for org in orgs:
        results.append(OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at,
            guidelines_count=len(org.guidelines),
            rules_count=len(org.rules),
            facts_count=len(org.facts)
        ))
    return results

@router.post("/workspaces", response_model=OrganizationResponse)
def create_workspace(payload: OrganizationCreate, db: Session = Depends(get_db)):
    existing = db.query(Organization).filter(Organization.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization with this slug already exists.")
    
    org = Organization(
        id=str(uuid.uuid4()),
        name=payload.name,
        slug=payload.slug
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        created_at=org.created_at,
        guidelines_count=0,
        rules_count=0,
        facts_count=0
    )

@router.get("/guidelines", response_model=List[BrandGuidelineResponse])
def get_guidelines(org_id: str = NOVA_ORG_ID, db: Session = Depends(get_db)):
    return db.query(BrandGuideline).filter(BrandGuideline.org_id == org_id).all()

@router.post("/guidelines/upload", response_model=BrandGuidelineResponse)
async def upload_guideline(
    org_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    content_bytes = await file.read()
    raw_text = ""
    total_pages = 1

    if file.filename.lower().endswith(".pdf"):
        import io
        pdf_reader = PdfReader(io.BytesIO(content_bytes))
        total_pages = len(pdf_reader.pages)
        for page_idx, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text() or ""
            raw_text += f"\n--- Page {page_idx + 1} ---\n" + page_text
    else:
        raw_text = content_bytes.decode("utf-8", errors="ignore")

    guideline_id = str(uuid.uuid4())
    guideline = BrandGuideline(
        id=guideline_id,
        org_id=org_id,
        filename=file.filename,
        file_path=f"/uploads/{file.filename}",
        file_type="pdf" if file.filename.lower().endswith(".pdf") else "txt",
        file_size_bytes=len(content_bytes),
        total_pages=total_pages,
        status="processed",
        raw_text=raw_text
    )
    db.add(guideline)

    # Chunking & Rule Extraction
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 30]
    for idx, para in enumerate(paragraphs[:10]):
        chunk = DocumentChunk(
            id=str(uuid.uuid4()),
            guideline_id=guideline_id,
            page_number=(idx // 3) + 1,
            chunk_index=idx,
            content=para
        )
        db.add(chunk)

        # Automatically extract candidate rules if policy words found
        if any(w in para.lower() for w in ["must", "prohibited", "strictly", "price", "forbidden", "standard"]):
            candidate_rule = BrandRule(
                id=str(uuid.uuid4()),
                org_id=org_id,
                category="Pricing" if "price" in para.lower() else "Guideline Rule",
                title=f"Extracted Policy #{idx + 1}",
                rule_text=para[:300],
                severity="CRITICAL" if any(w in para.lower() for w in ["strictly", "prohibited"]) else "WARNING",
                source_document=file.filename,
                page_reference=(idx // 3) + 1,
                is_active=True,
                is_confirmed=False # Requires admin confirmation!
            )
            db.add(candidate_rule)

    db.add(AuditLog(
        id=str(uuid.uuid4()),
        org_id=org_id,
        action="GUIDELINE_UPLOADED",
        actor="Administrator",
        details=f"Uploaded and parsed '{file.filename}' ({len(content_bytes)} bytes, {total_pages} pages)."
    ))

    db.commit()

    # Embed and persist vectors for the newly ingested chunks (RAG ingestion).
    try:
        from backend.app.services.rag import RagRetriever
        RagRetriever(db).index_org(org_id)
    except Exception:
        pass  # ingestion still succeeds even if indexing fails

    db.refresh(guideline)
    return guideline

@router.get("/rules", response_model=List[BrandRuleResponse])
def get_rules(org_id: str = NOVA_ORG_ID, category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(BrandRule).filter(BrandRule.org_id == org_id)
    if category:
        query = query.filter(BrandRule.category == category)
    return query.order_by(BrandRule.created_at.desc()).all()

@router.post("/rules", response_model=BrandRuleResponse)
def create_rule(org_id: str, payload: BrandRuleCreate, db: Session = Depends(get_db)):
    rule = BrandRule(
        id=str(uuid.uuid4()),
        org_id=org_id,
        category=payload.category,
        title=payload.title,
        rule_text=payload.rule_text,
        severity=payload.severity,
        source_document=payload.source_document,
        page_reference=payload.page_reference,
        is_active=payload.is_active,
        is_confirmed=payload.is_confirmed
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.patch("/rules/{rule_id}/confirm", response_model=BrandRuleResponse)
def confirm_rule(rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(BrandRule).filter(BrandRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_confirmed = True
    rule.is_active = True
    db.commit()
    db.refresh(rule)
    return rule

@router.get("/facts", response_model=List[ApprovedFactResponse])
def get_facts(org_id: str = NOVA_ORG_ID, db: Session = Depends(get_db)):
    return db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all()

@router.post("/facts", response_model=ApprovedFactResponse)
def create_fact(org_id: str, payload: ApprovedFactCreate, db: Session = Depends(get_db)):
    fact = ApprovedFact(
        id=str(uuid.uuid4()),
        org_id=org_id,
        category=payload.category,
        fact_key=payload.fact_key,
        fact_value=payload.fact_value,
        verification_source=payload.verification_source,
        notes=payload.notes
    )
    db.add(fact)
    db.commit()
    db.refresh(fact)
    return fact

@router.get("/terms", response_model=List[TerminologyRuleResponse])
def get_terms(org_id: str = NOVA_ORG_ID, db: Session = Depends(get_db)):
    return db.query(TerminologyRule).filter(TerminologyRule.org_id == org_id).all()

