"""Telegram channel management schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChannelSettings(BaseModel):
    auto_sign: bool = False
    signature: str = ""
    allow_discussion_forward: bool = True


class ChannelCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=1, max_length=255)
    telegram_chat_id: str = Field(default="-1000000000", max_length=64)
    settings: ChannelSettings = Field(default_factory=ChannelSettings)


class ChannelUpdateRequest(BaseModel):
    title: str | None = None
    username: str | None = None
    telegram_chat_id: str | None = None
    is_connected: bool | None = None
    bot_is_admin: bool | None = None
    settings: ChannelSettings | None = None


class ChannelResponse(BaseModel):
    id: str
    company_id: str
    title: str
    username: str
    telegram_chat_id: str
    subscriber_count: int = 0
    is_connected: bool = True
    bot_is_admin: bool = True
    settings: ChannelSettings
    created_at: str
