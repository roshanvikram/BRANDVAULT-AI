"""Brand Digital Twin Q&A API (Round 2 / R2-3)."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.twin import answer_question, SUGGESTIONS
from backend.app.services.seed import NOVA_ORG_ID

router = APIRouter(prefix="/twin", tags=["Brand Digital Twin"])


class AskRequest(BaseModel):
    question: str
    org_id: str = NOVA_ORG_ID


@router.get("/suggestions")
def suggestions():
    return {"suggestions": SUGGESTIONS}


@router.post("/ask")
def ask(payload: AskRequest, db: Session = Depends(get_db)):
    """Answer a natural-language question grounded only in the org's approved data."""
    result = answer_question(db, payload.org_id, payload.question)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return result
