from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.brand import router as brand_router
from backend.app.api.v1.content import router as content_router
from backend.app.api.v1.claim import router as claim_router
from backend.app.api.v1.approval import router as approval_router
from backend.app.api.v1.passport import router as passport_router
from backend.app.api.v1.agent import router as agent_router
from backend.app.api.v1.radar import router as radar_router
from backend.app.api.v1.rag import router as rag_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.visual import router as visual_router
from backend.app.api.v1.graph import router as graph_router
from backend.app.api.v1.onboarding import router as onboarding_router
from backend.app.api.v1.twin import router as twin_router
from backend.app.api.v1.copystudio import router as copystudio_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(visual_router)
api_router.include_router(brand_router)
api_router.include_router(content_router)
api_router.include_router(claim_router)
api_router.include_router(approval_router)
api_router.include_router(passport_router)
api_router.include_router(agent_router)
api_router.include_router(radar_router)
api_router.include_router(rag_router)
api_router.include_router(graph_router)
api_router.include_router(onboarding_router)
api_router.include_router(twin_router)
api_router.include_router(copystudio_router)

