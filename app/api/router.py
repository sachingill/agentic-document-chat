from __future__ import annotations

import logging

from fastapi import APIRouter

from app.routers import user, predict
from app.routers.agent import router as agent_router
from app.routers.agentic import router as agentic_router
from app.routers.rca import router as rca_router
from app.routers.features import router as features_router

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Core app routers
api_router.include_router(user.router)
api_router.include_router(predict.router)
api_router.include_router(agent_router)
api_router.include_router(agentic_router)
api_router.include_router(rca_router)
api_router.include_router(features_router)

# Multi-agent router (optional)
try:
    from multiagent.app.routers.multiagent import router as multiagent_router

    api_router.include_router(multiagent_router, prefix="/multiagent", tags=["multiagent"])
    logger.info("Multi-agent router registered successfully")
except Exception as e:
    logger.warning(f"Failed to register multi-agent router: {e}")


