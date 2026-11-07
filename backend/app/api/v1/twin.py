"""Brand Digital Twin Q&A API (Round 2 / R2-3)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.twin import answer_question, SUGGESTIONS
from backend.app.services.seed import NOVA_ORG_ID

from backend.app.models.user import User
from backend.app.core.ratelimit import rate_limit
from backend.app.core.config import settings
from backend.app.api.deps import get_current_user, resolve_org, ensure_same_org

router = APIRouter(prefix="/twin", tags=["Brand Digital Twin"])


class AskRequest(BaseModel):
    question: str
    org_id: Optional[str] = None


@router.get("/suggestions")
def suggestions():
    return {"suggestions": SUGGESTIONS}


@router.post("/ask", dependencies=[Depends(rate_limit("ai", settings.RATE_LIMIT_AI_PER_MIN))])
def ask(payload: AskRequest, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    payload.org_id = resolve_org(payload.org_id, current)
    """Answer a natural-language question grounded only in the org's approved data."""
    result = answer_question(db, payload.org_id, payload.question)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return result
