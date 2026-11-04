from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.brand import router as brand_router
from backend.app.api.v1.content import router as content_router
from backend.app.api.v1.claim import router as claim_router
from backend.app.api.v1.approval import router as approval_router
from backend.app.api.v1.passport import router as passport_router
from backend.app.api.v1.agent import router as agent_router
from backend.app.api.v1.radar import router as radar_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(brand_router)
api_router.include_router(content_router)
api_router.include_router(claim_router)
api_router.include_router(approval_router)
api_router.include_router(passport_router)
api_router.include_router(agent_router)
api_router.include_router(radar_router)

