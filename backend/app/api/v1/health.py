import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.schemas.common import HealthResponse
from backend.app.services.llm import get_llm_provider

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    provider = get_llm_provider(settings)
    llm_status = {
        "enabled": settings.LLM_ENABLED,
        "provider": getattr(provider, "name", "none"),
        "available": getattr(provider, "available", False),
        "model": getattr(provider, "model", "") or None,
        "mode": "llm+heuristic" if getattr(provider, "available", False) else "heuristic-only",
    }

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service=settings.PROJECT_NAME,
        tagline=settings.PROJECT_TAGLINE,
        version=settings.VERSION,
        database=db_status,
        timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        llm=llm_status,
    )



@router.get("/capabilities")
def get_capabilities(db: Session = Depends(get_db)):
    """Which optional engines are live on this server (shown in Settings; never assumed)."""
    from backend.app.services import embeddings, events, ocr
    from backend.app.services import rag
    dialect = db.get_bind().dialect.name
    return {
        "database": dialect,
        "pgvector": bool(dialect == "postgresql" and any(rag._PGV_READY.values())),
        "ocr": ocr.status(),
        "embeddings": embeddings.status(),
        "retrieval_mode": settings.RAG_MODE,
        "email_notifications": events.email_configured(),
        "demo_accounts": settings.DEMO_ACCOUNTS_ENABLED,
    }
