from fastapi import APIRouter

from app.api.v1.adjustments import router as adjustments_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.core_business import router as core_business_router
from app.api.v1.health import router as health_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.media import router as media_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.outfits import router as outfits_router
from app.api.v1.planning import router as planning_router
from app.api.v1.search import router as search_router
from app.api.v1.spots import router as spots_router
from app.api.v1.versions import router as versions_router
from app.api.v1.ws import router as ws_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(core_business_router)
api_router.include_router(planning_router, prefix="/planning", tags=["planning"])
api_router.include_router(media_router, prefix="/media", tags=["media"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(outfits_router, tags=["outfits"])
api_router.include_router(spots_router, tags=["spots"])
api_router.include_router(adjustments_router, tags=["adjustments"])
api_router.include_router(versions_router, tags=["trip-versions"])
api_router.include_router(search_router, tags=["search"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(ws_router, tags=["websocket"])

# Agent router is optional (requires langgraph dependencies not in base install)
try:
    from app.integrations.agent import router as agent_router

    api_router.include_router(agent_router, tags=["agent"])
except ImportError:
    pass
