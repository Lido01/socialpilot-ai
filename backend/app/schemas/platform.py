"""Platform Owner admin schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PendingCompanyResponse(BaseModel):
    """Response for a pending company registration."""

    id: str
    name: str
    normalized_name: str
    industry: str | None
    website: str | None
    country: str | None
    contact_email: str | None
    status: str
    user_id: str
    user_telegram_id: int
    user_display_name: str
    user_username: str | None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ApproveCompanyRequest(BaseModel):
    """Request to approve a company registration."""

    pass


class RejectCompanyRequest(BaseModel):
    """Request to reject a company registration."""

    reason: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Rejection reason",
    )


class PlatformActionResponse(BaseModel):
    """Response for platform owner actions."""

    success: bool
    message: str
    company_id: str | None = None
    company_status: str | None = None