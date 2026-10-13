"""Authentication schemas for Telegram initData validation and JWT tokens."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    """Request to authenticate via Telegram Mini App initData."""

    init_data: str = Field(
        ...,
        description="Raw initData string from Telegram.WebApp.initData",
        min_length=1,
    )


class TelegramAuthResponse(BaseModel):
    """Response containing JWT access token."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token lifetime in seconds")


class TelegramUserData(BaseModel):
    """Validated Telegram user data from initData."""

    id: int = Field(..., description="Telegram user ID")
    first_name: str = Field(..., description="First name")
    last_name: str | None = Field(default=None, description="Last name")
    username: str | None = Field(default=None, description="Telegram username")
    language_code: str | None = Field(default=None, description="Language code")
    is_premium: bool | None = Field(default=None, description="Premium status")
    allows_write_to_pm: bool | None = Field(default=None, description="Can write to PM")