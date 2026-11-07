from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.services.rag import RagRetriever
from backend.app.services.seed import NOVA_ORG_ID

from backend.app.models.user import User
from backend.app.api.deps import get_current_user, resolve_org, ensure_same_org

router = APIRouter(prefix="/rag", tags=["RAG Retrieval"])


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    org_id: Optional[str] = None
    top_k: int = Field(default=3, ge=1, le=20)


class RagSearchResponse(BaseModel):
    query: str
    org_id: str
    embedder: str
    count: int
    results: List[Dict[str, Any]]


@router.post("/search", response_model=RagSearchResponse)
def rag_search(payload: RagSearchRequest, db: Session = Depends(get_db),
               current: User = Depends(get_current_user)):
    """Hybrid (TF-IDF cosine + keyword) retrieval over org-isolated guideline
    chunks. Returns ranked passages with real page citations and scores."""
    payload.org_id = resolve_org(payload.org_id, current)
    retriever = RagRetriever(db)
    results = retriever.search(payload.org_id, payload.query, top_k=payload.top_k)
    return RagSearchResponse(
        query=payload.query,
        org_id=payload.org_id,
        embedder=retriever.embedder.name,
        count=len(results),
        results=results,
    )
