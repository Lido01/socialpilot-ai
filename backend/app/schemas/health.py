"""Health endpoint response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    app_name: str
    app_env: str
    version: str = Field(default="0.1.0")
