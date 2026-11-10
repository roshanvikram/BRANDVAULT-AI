import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import engine, SessionLocal
from backend.app.db.migrations import run_light_migrations
from backend.app.api.v1 import api_router
from backend.app.services.seed import seed_sample_brand, augment_integrity_demo, seed_demo_users, seed_vortexa_brand

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables, apply additive migrations, seed baseline brand
    Base.metadata.create_all(bind=engine)
    run_light_migrations(engine)
    from backend.app.db.migrations import fix_chunk_page_numbers
    fix_chunk_page_numbers(engine)
    db = SessionLocal()
    try:
        seed_sample_brand(db)
        seed_vortexa_brand(db)
        augment_integrity_demo(db)
        seed_demo_users(db)
        from backend.app.services.seed import apply_demo_account_policy
        apply_demo_account_policy(db, settings.DEMO_ACCOUNTS_ENABLED)
        # Build/refresh RAG vector embeddings for every org's guideline chunks.
        from backend.app.models.brand import Organization
        from backend.app.services.rag import RagRetriever
        retriever = RagRetriever(db)
        for org in db.query(Organization).all():
            retriever.index_org(org.id)
        # Demo campaigns for an empty workspace (fresh deploys). Never touches existing data.
        if settings.SEED_DEMO_CONTENT:
            from backend.app.services.demo_content import seed_demo_campaigns
            try:
                seed_demo_campaigns(db)
            except Exception as exc:  # demo data must never block startup
                db.rollback()
                print(f"[startup] demo campaign seed skipped: {exc}")
        # Durable jobs: re-run (or fail) anything a previous process left unfinished.
        from backend.app.services.jobs import resume_unfinished
        resume_unfinished(db)
    finally:
        db.close()
    from backend.app.services import keepawake
    awake_task = keepawake.start(list(settings.BACKEND_CORS_ORIGINS))
    yield
    # Shutdown
    if awake_task is not None:
        awake_task.cancel()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="BRANDVAULT AI — Protect Every Word. Preserve Every Identity. Enterprise Agentic Brand Governance & ClaimDNA Platform.",
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    # Stateless bearer-token API (no cookies), so credentials are off — this
    # keeps explicit origins valid and avoids the insecure "*"+credentials combo.
    allow_credentials=False,
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

