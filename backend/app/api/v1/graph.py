"""Brand Knowledge Graph API (Round 2 / R2-2)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.graph import build_brand_graph
from backend.app.services.seed import NOVA_ORG_ID

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


@router.get("/brand")
def brand_graph(org_id: str = NOVA_ORG_ID, db: Session = Depends(get_db)):
    """Return the brand knowledge graph (nodes + edges) built from real records."""
    graph = build_brand_graph(db, org_id)
    if graph is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return graph
