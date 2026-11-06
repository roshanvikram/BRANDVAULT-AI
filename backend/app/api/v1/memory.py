"""Brand Memory API (Round 2 / R2-4)."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.brand import TerminologyRule
from backend.app.models.user import User, ROLE_ADMIN
from backend.app.api.deps import require_roles, ensure_same_org
from backend.app.services.memory import compute_memory
from backend.app.services.seed import NOVA_ORG_ID

router = APIRouter(prefix="/memory", tags=["Brand Memory"])


class ApplyTerminology(BaseModel):
    org_id: str
    prohibited_term: str
    preferred_term: str
    explanation: str = ""


@router.get("/insights")
def insights(org_id: str = NOVA_ORG_ID, db: Session = Depends(get_db)):
    """Learned insights + proposed policy improvements from real history."""
    result = compute_memory(db, org_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return result


@router.post("/apply-terminology")
def apply_terminology(
    payload: ApplyTerminology,
    db: Session = Depends(get_db),
    current: User = Depends(require_roles(ROLE_ADMIN)),
):
    """Apply a proposed terminology entry into the live Brand DNA. Administrator-
    only and tenant-isolated — the human explicitly accepts the proposal; the
    system never applies it automatically."""
    ensure_same_org(current, payload.org_id)
    prohibited = payload.prohibited_term.strip()
    preferred = payload.preferred_term.strip()
    if not prohibited or not preferred:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both terms are required.")
    # Idempotent: don't duplicate an existing prohibited term.
    existing = (
        db.query(TerminologyRule)
        .filter(TerminologyRule.org_id == payload.org_id, TerminologyRule.prohibited_term.ilike(prohibited))
        .first()
    )
    if existing:
        return {"created": False, "id": existing.id, "message": "This terminology rule already exists."}
    rule = TerminologyRule(
        id=str(uuid.uuid4()),
        org_id=payload.org_id,
        prohibited_term=prohibited,
        preferred_term=preferred,
        explanation=payload.explanation or f"Added from Brand Memory by {current.full_name}.",
        is_active=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"created": True, "id": rule.id, "prohibited_term": rule.prohibited_term, "preferred_term": rule.preferred_term}
