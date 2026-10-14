"""API v1 router aggregating all endpoint routers."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
