import os
import re
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
from backend.app.models.user import User, ROLE_ADMIN
from backend.app.api.deps import get_current_user, require_roles, resolve_org, ensure_same_org


def _audit(db: Session, org_id: str, action: str, actor: User, details: str) -> None:
    db.add(AuditLog(id=str(uuid.uuid4()), org_id=org_id, action=action,
                    actor=f"{actor.full_name} ({actor.role})", details=details))

router = APIRouter(prefix="/brand", tags=["Brand DNA Studio"])

PAGE_MARKER = re.compile(r"---\s*Page\s+(\d+)\s*---")

@router.get("/workspaces", response_model=List[OrganizationResponse])
def get_workspaces(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    # Auto-seed sample brand if empty
    seed_sample_brand(db)
    # Tenant isolation: a user only sees their own organisation.
    orgs = db.query(Organization).filter(Organization.id == current.org_id).all()
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
def create_workspace(payload: OrganizationCreate, db: Session = Depends(get_db),
                     current: User = Depends(require_roles(ROLE_ADMIN))):
    existing = db.query(Organization).filter(Organization.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization with this slug already exists.")
    
    org = Organization(
        id=str(uuid.uuid4()),
        name=payload.name,
        slug=payload.slug
    )
    db.add(org)
    _audit(db, org.id, "WORKSPACE_CREATED", current, f"Created workspace '{org.name}'.")
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
def get_guidelines(org_id: Optional[str] = None, db: Session = Depends(get_db),
                   current: User = Depends(get_current_user)):
    org_id = resolve_org(org_id, current)
    return db.query(BrandGuideline).filter(BrandGuideline.org_id == org_id).all()

@router.post("/guidelines/upload", response_model=BrandGuidelineResponse)
async def upload_guideline(
    org_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    replaces: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current: User = Depends(require_roles(ROLE_ADMIN)),
):
    org_id = resolve_org(org_id, current)
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Upload hardening: restrict type and size.
    from backend.app.services import ingest
    MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB
    try:
        ingest.file_type(file.filename or "")
    except ingest.IngestError as e:
        raise HTTPException(status_code=400, detail=str(e))

    content_bytes = await file.read()
    if len(content_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 15 MB upload limit.")
    if len(content_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    try:
        kind, sections, passages, raw_text = ingest.ingest(file.filename, content_bytes)
    except ingest.IngestError as e:
        raise HTTPException(status_code=422, detail=str(e))

    old = None
    if replaces:
        old = db.query(BrandGuideline).filter(BrandGuideline.id == replaces, BrandGuideline.org_id == org_id).first()
        if old is None:
            raise HTTPException(status_code=404, detail="The guideline being replaced was not found.")

    guideline_id = str(uuid.uuid4())
    guideline = BrandGuideline(
        id=guideline_id,
        org_id=org_id,
        filename=file.filename,
        file_path=f"/uploads/{file.filename}",
        file_type=kind,
        file_size_bytes=len(content_bytes),
        total_pages=len(sections),
        status="processed",
        raw_text=raw_text
    )
    db.add(guideline)
    if old is not None:
        # Version history: the old document stays on record but is no longer cited as evidence.
        old.status = "superseded"
        old.superseded_by_id = guideline_id
        old.superseded_at = datetime.datetime.utcnow()

    for idx, ps in enumerate(passages):
        db.add(DocumentChunk(id=str(uuid.uuid4()), guideline_id=guideline_id, page_number=ps["n"], chunk_index=idx,
                             content=ps["text"], section_label=ps["label"]))
        para = ps["text"]
        # Candidate rules stay unconfirmed until an administrator confirms them (human gate #1).
        if kind not in ("csv", "xlsx") and any(w in para.lower() for w in ["must", "prohibited", "strictly", "price", "forbidden", "standard"]):
            db.add(BrandRule(
                id=str(uuid.uuid4()), org_id=org_id,
                category="Pricing" if "price" in para.lower() else "Guideline Rule",
                title=f"Extracted Policy #{idx + 1}", rule_text=para[:300],
                severity="CRITICAL" if any(w in para.lower() for w in ["strictly", "prohibited"]) else "WARNING",
                source_document=file.filename, page_reference=ps["n"], is_active=True, is_confirmed=False,
            ))
    proposed = _propose_price_facts(db, org_id, kind, sections, file.filename, current) if kind in ("csv", "xlsx") else 0
    total_pages = len(sections)

    db.add(AuditLog(
        id=str(uuid.uuid4()),
        org_id=org_id,
        action="GUIDELINE_UPLOADED",
        actor=f"{current.full_name} ({current.role})",
        details=f"Uploaded and parsed '{file.filename}' ({kind}, {len(content_bytes)} bytes, {total_pages} sections, "
                f"{len(passages)} passages{f', {proposed} price fact(s) proposed' if proposed else ''}"
                f"{f'; replaces {old.filename}' if old is not None else ''})."
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
def get_rules(org_id: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db),
              current: User = Depends(get_current_user)):
    org_id = resolve_org(org_id, current)
    query = db.query(BrandRule).filter(BrandRule.org_id == org_id)
    if category:
        query = query.filter(BrandRule.category == category)
    return query.order_by(BrandRule.created_at.desc()).all()

@router.post("/rules", response_model=BrandRuleResponse)
def create_rule(payload: BrandRuleCreate, org_id: Optional[str] = None, db: Session = Depends(get_db),
                current: User = Depends(require_roles(ROLE_ADMIN))):
    org_id = resolve_org(org_id, current)
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
    _audit(db, org_id, "RULE_CREATED", current, f"Created rule '{rule.title}' ({rule.category}).")
    db.commit()
    db.refresh(rule)
    return rule

@router.patch("/rules/{rule_id}/confirm", response_model=BrandRuleResponse)
def confirm_rule(rule_id: str, db: Session = Depends(get_db),
                 current: User = Depends(require_roles(ROLE_ADMIN))):
    rule = db.query(BrandRule).filter(BrandRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    ensure_same_org(current, rule.org_id)
    rule.is_confirmed = True
    rule.is_active = True
    _audit(db, rule.org_id, "RULE_CONFIRMED", current, f"Confirmed rule '{rule.title}'.")
    db.commit()
    db.refresh(rule)
    return rule

@router.get("/facts", response_model=List[ApprovedFactResponse])
def get_facts(org_id: Optional[str] = None, db: Session = Depends(get_db),
              current: User = Depends(get_current_user)):
    org_id = resolve_org(org_id, current)
    return db.query(ApprovedFact).filter(ApprovedFact.org_id == org_id).all()

@router.post("/facts", response_model=ApprovedFactResponse)
def create_fact(payload: ApprovedFactCreate, org_id: Optional[str] = None, db: Session = Depends(get_db),
                current: User = Depends(require_roles(ROLE_ADMIN))):
    org_id = resolve_org(org_id, current)
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
    _audit(db, org_id, "FACT_CREATED", current, f"Created approved fact '{fact.fact_key}'.")
    db.commit()
    db.refresh(fact)
    return fact

@router.get("/terms", response_model=List[TerminologyRuleResponse])
def get_terms(org_id: Optional[str] = None, db: Session = Depends(get_db),
              current: User = Depends(get_current_user)):
    org_id = resolve_org(org_id, current)
    return db.query(TerminologyRule).filter(TerminologyRule.org_id == org_id).all()

def _propose_price_facts(db: Session, org_id: str, kind: str, sections, filename: str, current: User) -> int:
    """Price lists: rows naming a known product and a price become *pending* Product Truth facts.
    Nothing is approved automatically; an administrator reviews them in Product Truth."""
    import re as _re
    from backend.app.models.product import Product, ProductFact, FACT_PENDING, FACT_APPROVED
    from backend.app.services import product_truth as pt
    pt.bootstrap_products(db, org_id)
    products = {p.name.lower(): p for p in db.query(Product).filter(Product.org_id == org_id).all() if p.name}
    made = 0
    for s in sections:
        row = s["text"]
        cells = dict((k.strip().lower(), v.strip()) for k, v in (c.split(":", 1) for c in _re.sub(r"^Row \d+:\s*", "", row).rstrip(".").split(" | ") if ":" in c))
        name = next((v for k, v in cells.items() if "product" in k or "model" in k or k == "name"), None)
        price = next((v for k, v in cells.items() if "price" in k or "mrp" in k), None)
        prod = products.get((name or "").lower())
        if not prod or not price:
            continue
        num, unit, qual = pt.parse_fact_value("price", price if _re.search(r"₹|rs|inr", price, _re.I) else f"₹{price}")
        if num is None:
            continue
        dup = db.query(ProductFact).filter(ProductFact.org_id == org_id, ProductFact.product_id == prod.id, ProductFact.attribute == "price",
                                           ProductFact.value_num == num, ProductFact.status.in_([FACT_PENDING, FACT_APPROVED])).first()
        if dup:
            continue
        db.add(ProductFact(id=str(uuid.uuid4()), org_id=org_id, product_id=prod.id, attribute="price",
                           value_text=f"₹{num:,.0f}" if unit == "INR" else price, value_num=num, unit=unit, qualifier=qual,
                           source_document=filename, page_reference=s["n"], evidence_excerpt=row[:300], status=FACT_PENDING,
                           origin="spreadsheet", created_by=f"{current.full_name} ({current.role})"))
        made += 1
    return made
