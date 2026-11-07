"""Product Truth API — product knowledge management + claim verification."""
import datetime
import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_roles, resolve_org, ensure_same_org
from backend.app.core.config import settings
from backend.app.core.ratelimit import rate_limit
from backend.app.db.session import get_db
from backend.app.models.job import Job
from backend.app.models.passport import AgentRun, AuditLog
from backend.app.models.product import (
    Product, ProductFact, PRODUCT_ATTRIBUTES, FACT_APPROVED, FACT_PENDING, FACT_REJECTED, FACT_SUPERSEDED,
)
from backend.app.models.user import User, ROLE_ADMIN
from backend.app.services import jobs as jobs_svc
from backend.app.services import product_truth as pt
from backend.app.services.llm import get_llm_provider

router = APIRouter(prefix="/products", tags=["Product Truth"])


def _audit(db: Session, org_id: str, action: str, user: User, details: str) -> None:
    db.add(AuditLog(id=str(uuid.uuid4()), org_id=org_id, action=action,
                    actor=f"{user.full_name} ({user.role})", details=details))


def _fact_out(f: ProductFact) -> dict:
    now = datetime.datetime.utcnow()
    expired = f.valid_until is not None and f.valid_until <= now
    return {
        "id": f.id, "attribute": f.attribute, "attribute_label": PRODUCT_ATTRIBUTES.get(f.attribute, f.attribute),
        "value_text": f.value_text, "value_num": f.value_num, "unit": f.unit, "qualifier": f.qualifier,
        "source_document": f.source_document, "page_reference": f.page_reference, "evidence_excerpt": f.evidence_excerpt,
        "status": f.status, "is_current": f.status == FACT_APPROVED and not expired, "expired": expired,
        "origin": f.origin, "valid_until": f.valid_until.isoformat() if f.valid_until else None,
        "approved_by": f.approved_by, "approved_at": f.approved_at.isoformat() if f.approved_at else None,
        "created_by": f.created_by, "created_at": f.created_at.isoformat() if f.created_at else None,
    }


def _product_out(p: Product) -> dict:
    return {
        "id": p.id, "name": p.name, "model_number": p.model_number, "category": p.category, "status": p.status,
        "facts": [_fact_out(f) for f in sorted(p.facts, key=lambda x: (x.attribute, x.created_at or datetime.datetime.min))],
    }


def _own_product(db: Session, product_id: str, user: User) -> Product:
    p = db.query(Product).filter(Product.id == product_id).first()
    if p is None or p.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


def _own_fact(db: Session, fact_id: str, user: User) -> ProductFact:
    f = db.query(ProductFact).filter(ProductFact.id == fact_id).first()
    if f is None or f.org_id != user.org_id:
        raise HTTPException(status_code=404, detail="Fact not found")
    return f


# ------------------------------- reads -------------------------------------
@router.get("")
def list_products(org_id: Optional[str] = None, db: Session = Depends(get_db),
                  current: User = Depends(get_current_user)):
    org_id = resolve_org(org_id, current)
    pt.bootstrap_products(db, org_id)
    rows = db.query(Product).filter(Product.org_id == org_id).order_by(Product.name).all()
    return {"products": [_product_out(p) for p in rows], "attributes": PRODUCT_ATTRIBUTES,
            "ai_extraction_available": get_llm_provider(settings).available}


# ------------------------------- verification ------------------------------
class VerifyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    org_id: Optional[str] = None


@router.post("/verify", dependencies=[Depends(rate_limit("ai", settings.RATE_LIMIT_AI_PER_MIN))])
def verify(payload: VerifyRequest, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    org_id = resolve_org(payload.org_id, current)
    t0 = time.perf_counter()
    result = pt.verify_text(db, org_id, payload.text)
    el = time.perf_counter() - t0
    db.add(AgentRun(
        id=str(uuid.uuid4()), org_id=org_id, agent_name="Product Truth Agent",
        task_name="Verify product statements against approved product facts", status="COMPLETED",
        execution_time_ms=round(el * 1000), execution_time_us=max(1, round(el * 1_000_000)), tokens_used=0,
        input_preview=payload.text[:120],
        output_preview=f"{len(result['claims'])} claims; verdict: {result['verdict']}.",
        event_details={"summary": result["summary"]}, created_at=datetime.datetime.utcnow(),
    ))
    db.commit()
    return result


# ------------------------------- admin writes ------------------------------
class ProductIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    model_number: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=100)


@router.post("")
def create_product(payload: ProductIn, db: Session = Depends(get_db),
                   current: User = Depends(require_roles(ROLE_ADMIN))):
    if db.query(Product).filter(Product.org_id == current.org_id, Product.name.ilike(payload.name.strip())).first():
        raise HTTPException(status_code=409, detail="A product with this name already exists.")
    p = Product(id=str(uuid.uuid4()), org_id=current.org_id, name=payload.name.strip(),
                model_number=payload.model_number, category=payload.category, status="active")
    db.add(p)
    _audit(db, current.org_id, "PRODUCT_CREATED", current, f"Created product '{p.name}'.")
    db.commit()
    db.refresh(p)
    return _product_out(p)


class FactIn(BaseModel):
    attribute: str
    value_text: str = Field(min_length=1, max_length=300)
    source_document: str = Field(min_length=2, max_length=255)
    page_reference: Optional[int] = Field(default=None, ge=1)
    evidence_excerpt: Optional[str] = Field(default=None, max_length=1000)
    valid_until: Optional[datetime.datetime] = None


def _supersede_others(db: Session, fact: ProductFact) -> int:
    n = 0
    for other in db.query(ProductFact).filter(ProductFact.product_id == fact.product_id,
                                              ProductFact.attribute == fact.attribute,
                                              ProductFact.status == FACT_APPROVED,
                                              ProductFact.id != fact.id).all():
        other.status = FACT_SUPERSEDED
        other.valid_until = other.valid_until or datetime.datetime.utcnow()
        n += 1
    return n


@router.post("/{product_id}/facts")
def add_fact(product_id: str, payload: FactIn, db: Session = Depends(get_db),
             current: User = Depends(require_roles(ROLE_ADMIN))):
    """Administrators add an official fact; it is approved immediately and any
    earlier approved value for the same attribute is superseded (kept as history)."""
    p = _own_product(db, product_id, current)
    if payload.attribute not in PRODUCT_ATTRIBUTES:
        raise HTTPException(status_code=400, detail=f"Unknown attribute. Use one of: {', '.join(PRODUCT_ATTRIBUTES)}")
    num, unit, qual = pt.parse_fact_value(payload.attribute, payload.value_text)
    now = datetime.datetime.utcnow()
    f = ProductFact(id=str(uuid.uuid4()), org_id=p.org_id, product_id=p.id, attribute=payload.attribute,
                    value_text=payload.value_text.strip(), value_num=num, unit=unit, qualifier=qual,
                    source_document=payload.source_document, page_reference=payload.page_reference,
                    evidence_excerpt=payload.evidence_excerpt, status=FACT_APPROVED, origin="manual",
                    valid_until=payload.valid_until, approved_by=current.full_name, approved_at=now,
                    created_by=current.full_name)
    db.add(f)
    db.flush()
    superseded = _supersede_others(db, f)
    _audit(db, p.org_id, "PRODUCT_FACT_APPROVED", current,
           f"{p.name}: {payload.attribute} = '{f.value_text}' (source {f.source_document}); superseded {superseded}.")
    db.commit()
    return _fact_out(f)


@router.post("/facts/{fact_id}/approve")
def approve_fact(fact_id: str, db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    f = _own_fact(db, fact_id, current)
    if f.status != FACT_PENDING:
        raise HTTPException(status_code=409, detail=f"Fact is already {f.status}.")
    f.status = FACT_APPROVED
    f.approved_by, f.approved_at = current.full_name, datetime.datetime.utcnow()
    superseded = _supersede_others(db, f)
    _audit(db, f.org_id, "PRODUCT_FACT_APPROVED", current,
           f"Approved {f.attribute} = '{f.value_text}' ({f.origin}); superseded {superseded}.")
    db.commit()
    return _fact_out(f)


@router.post("/facts/{fact_id}/reject")
def reject_fact(fact_id: str, db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    f = _own_fact(db, fact_id, current)
    if f.status != FACT_PENDING:
        raise HTTPException(status_code=409, detail=f"Fact is already {f.status}.")
    f.status = FACT_REJECTED
    _audit(db, f.org_id, "PRODUCT_FACT_REJECTED", current, f"Rejected {f.attribute} = '{f.value_text}' ({f.origin}).")
    db.commit()
    return _fact_out(f)


# ------------------------------- AI extraction (background job) ------------
@jobs_svc.register_handler("product_extraction")
def _extraction_job(db: Session, job: Job) -> Optional[str]:
    provider = get_llm_provider(settings)
    result = pt.extract_from_documents(db, job.org_id, provider, actor=(job.input_data or {}).get("actor", "AI"))
    job.input_data = {**(job.input_data or {}), "result": result}
    db.commit()
    return None


@router.post("/extract")
def extract(db: Session = Depends(get_db), current: User = Depends(require_roles(ROLE_ADMIN))):
    """Start an AI pass that proposes product facts from uploaded guidelines.
    Proposals are pending until an Administrator approves each one."""
    if not get_llm_provider(settings).available:
        raise HTTPException(status_code=503, detail="No AI model is configured (set GROQ_API_KEY or ANTHROPIC_API_KEY). "
                                                    "Add product facts manually instead.")
    job, _ = jobs_svc.create_job(db, org_id=current.org_id, kind="product_extraction", created_by=current.id,
                                 input_data={"actor": f"{current.full_name} (AI extraction)"}, max_attempts=1)
    out = jobs_svc.job_to_dict(job)
    out["job_id"] = job.id
    return out


@router.get("/extract/{job_id}")
def extract_status(job_id: str, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None or job.org_id != current.org_id or job.kind != "product_extraction":
        raise HTTPException(status_code=404, detail="Job not found")
    out = jobs_svc.job_to_dict(job)
    out["result"] = (job.input_data or {}).get("result")
    return out


# ------------------------------- knowledge gaps ----------------------------
@router.get("/knowledge-gaps")
def knowledge_gaps(org_id: Optional[str] = None, db: Session = Depends(get_db),
                   current: User = Depends(get_current_user)):
    """Missing, conflicting, weakly-sourced or stale Brand DNA, prioritised."""
    from backend.app.services.knowledge_gaps import detect_gaps
    org_id = resolve_org(org_id, current)
    result = detect_gaps(db, org_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return result
