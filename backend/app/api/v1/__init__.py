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
from backend.app.api.v1.memory import router as memory_router
from backend.app.api.v1.translation_guard import router as translation_guard_router
from backend.app.api.v1.products import router as products_router
from backend.app.api.v1.assets import router as assets_router
from backend.app.api.v1.governance import router as governance_router
from backend.app.api.v1.intelligence import router as intelligence_router
from backend.app.api.v1.creative import router as creative_router
from backend.app.api.v1.integrations import router as integrations_router

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
api_router.include_router(memory_router)
api_router.include_router(translation_guard_router)
api_router.include_router(products_router)
api_router.include_router(assets_router)
api_router.include_router(governance_router)
api_router.include_router(intelligence_router)
api_router.include_router(creative_router)
api_router.include_router(integrations_router)

