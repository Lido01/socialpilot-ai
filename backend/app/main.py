"""FastAPI application factory."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppException

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="SocialPilot AI — Multi-tenant Telegram Mini App SaaS",
        debug=settings.DEBUG,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "details": [],
                }
            },
        )

    app.include_router(api_router)

    frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
    target_dir = frontend_dist if frontend_dist.is_dir() else (frontend_dir if frontend_dir.is_dir() else None)
    if target_dir:
        app.mount("/app", StaticFiles(directory=str(target_dir), html=True), name="miniapp")

    @app.on_event("startup")
    async def startup_event() -> None:
        logger.info("Starting %s in %s mode", settings.APP_NAME, settings.APP_ENV)

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        logger.info("Shutting down %s", settings.APP_NAME)

    return app


app = create_app()
