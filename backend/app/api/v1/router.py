"""API v1 router aggregating all endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import ai, auth, channels, company, health, platform, team

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(company.router)
api_router.include_router(platform.router)
api_router.include_router(ai.router)
api_router.include_router(team.router)
api_router.include_router(channels.router)

