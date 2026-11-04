import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import engine, SessionLocal
from backend.app.db.migrations import run_light_migrations
from backend.app.api.v1 import api_router
from backend.app.services.seed import seed_sample_brand, augment_integrity_demo, seed_demo_users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables, apply additive migrations, seed baseline brand
    Base.metadata.create_all(bind=engine)
    run_light_migrations(engine)
    db = SessionLocal()
    try:
        seed_sample_brand(db)
        augment_integrity_demo(db)
        seed_demo_users(db)
        # Build/refresh RAG vector embeddings for every org's guideline chunks.
        from backend.app.models.brand import Organization
        from backend.app.services.rag import RagRetriever
        retriever = RagRetriever(db)
        for org in db.query(Organization).all():
            retriever.index_org(org.id)
    finally:
        db.close()
    yield
    # Shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="BRANDVAULT AI — Protect Every Word. Preserve Every Identity. Enterprise Agentic Brand Governance & ClaimDNA Platform.",
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def get_root():
    return {
        "product": "BRANDVAULT AI",
        "tagline": "Protect Every Word. Preserve Every Identity.",
        "category": "Agentic AI, Brand Governance, RAG, Multimodal AI, Enterprise SaaS",
        "team_leader": "Deepak Mouriya M",
        "team_members": [
            "Deepak Mouriya M",
            "Roshan Vikram AV",
            "Preethish",
            "Aishwarya R M"
        ],
        "api_docs": "/docs",
        "api_v1": settings.API_V1_STR,
        "status": "ONLINE"
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

