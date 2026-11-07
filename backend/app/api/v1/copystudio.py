"""AI Copy Studio API (Round 2 / R2-AI)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.services.copystudio import rewrite_content
from backend.app.services.llm import get_llm_provider
from backend.app.services.seed import NOVA_ORG_ID

from backend.app.models.user import User
from backend.app.core.ratelimit import rate_limit
from backend.app.api.deps import get_current_user, resolve_org, ensure_same_org

router = APIRouter(prefix="/copy-studio", tags=["AI Copy Studio"])


class RewriteRequest(BaseModel):
    content: str
    org_id: Optional[str] = None


@router.get("/status")
def status_():
    """Honestly report whether real generative AI is live or the rewrite falls
    back to the deterministic engine."""
    p = get_llm_provider(settings)
    return {"llm_available": p.available, "provider": p.name if p.available else "none",
            "model": p.model if p.available else ""}


@router.post("/rewrite", dependencies=[Depends(rate_limit("ai", settings.RATE_LIMIT_AI_PER_MIN))])
def rewrite(payload: RewriteRequest, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    payload.org_id = resolve_org(payload.org_id, current)
    result = rewrite_content(db, payload.org_id, payload.content)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return result
