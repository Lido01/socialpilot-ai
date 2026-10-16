"""Telegram Channel management endpoints."""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any
from fastapi import APIRouter, HTTPException, status

from app.schemas.channel import (
    ChannelCreateRequest,
    ChannelResponse,
    ChannelSettings,
    ChannelUpdateRequest,
)

router = APIRouter(tags=["channels"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
CHANNELS_FILE = os.path.join(DATA_DIR, "company_channels.json")
_lock = threading.Lock()

INITIAL_CHANNELS: list[dict[str, Any]] = [
    {
        "id": "chan-1",
        "company_id": "comp-1",
        "title": "SocialPilot AI Official",
        "username": "@socialpilot_ai",
        "telegram_chat_id": "-10022446688",
        "subscriber_count": 1420,
        "is_connected": True,
        "bot_is_admin": True,
        "settings": {
            "auto_sign": True,
            "signature": "📢 Powered by SocialPilot AI",
            "allow_discussion_forward": True,
        },
        "created_at": "2026-10-06T12:00:00Z",
    },
    {
        "id": "chan-2",
        "company_id": "comp-1",
        "title": "Tech & AI Insights Daily",
        "username": "@tech_ai_insights",
        "telegram_chat_id": "-10033557799",
        "subscriber_count": 890,
        "is_connected": True,
        "bot_is_admin": True,
        "settings": {
            "auto_sign": False,
            "signature": "",
            "allow_discussion_forward": False,
        },
        "created_at": "2026-10-12T12:00:00Z",
    },
]


def _load_channels() -> list[dict[str, Any]]:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CHANNELS_FILE):
        _save_channels(INITIAL_CHANNELS)
        return list(INITIAL_CHANNELS)
    try:
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return list(INITIAL_CHANNELS)


def _save_channels(items: list[dict[str, Any]]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)


@router.get(
    "/companies/{company_id}/channels",
    response_model=list[ChannelResponse],
)
def list_company_channels(company_id: str) -> list[ChannelResponse]:
    """List connected Telegram channels for a company workspace."""
    with _lock:
        items = _load_channels()

    result: list[ChannelResponse] = []
    for item in items:
        if item.get("company_id") == company_id:
            result.append(
                ChannelResponse(
                    id=item["id"],
                    company_id=company_id,
                    title=item["title"],
                    username=item["username"],
                    telegram_chat_id=item["telegram_chat_id"],
                    subscriber_count=item.get("subscriber_count", 0),
                    is_connected=item.get("is_connected", True),
                    bot_is_admin=item.get("bot_is_admin", True),
                    settings=ChannelSettings(**item.get("settings", {})),
                    created_at=item.get("created_at", "2026-10-16T12:00:00Z"),
                )
            )
    return result


@router.post(
    "/companies/{company_id}/channels",
    response_model=ChannelResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_company_channel(
    company_id: str,
    request: ChannelCreateRequest,
) -> ChannelResponse:
    """Connect a real Telegram channel to the company workspace."""
    clean_username = request.username.strip()
    if not clean_username.startswith("@"):
        clean_username = f"@{clean_username}"

    chan_id = f"chan-{int(time.time() * 1000)}"
    new_chan_dict: dict[str, Any] = {
        "id": chan_id,
        "company_id": company_id,
        "title": request.title.strip(),
        "username": clean_username,
        "telegram_chat_id": request.telegram_chat_id.strip() or "-1000000000",
        "subscriber_count": 0,
        "is_connected": True,
        "bot_is_admin": True,
        "settings": request.settings.model_dump(),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    with _lock:
        items = _load_channels()
        items.append(new_chan_dict)
        _save_channels(items)

    return ChannelResponse(
        id=chan_id,
        company_id=company_id,
        title=new_chan_dict["title"],
        username=new_chan_dict["username"],
        telegram_chat_id=new_chan_dict["telegram_chat_id"],
        subscriber_count=0,
        is_connected=True,
        bot_is_admin=True,
        settings=request.settings,
        created_at=new_chan_dict["created_at"],
    )


@router.patch(
    "/companies/{company_id}/channels/{channel_id}",
    response_model=ChannelResponse,
)
def update_company_channel(
    company_id: str,
    channel_id: str,
    request: ChannelUpdateRequest,
) -> ChannelResponse:
    """Update settings or connection details for a Telegram channel."""
    with _lock:
        items = _load_channels()
        target = None
        for item in items:
            if item.get("id") == channel_id and item.get("company_id") == company_id:
                target = item
                break

        if not target:
            raise HTTPException(status_code=404, detail="Channel not found")

        if request.title is not None:
            target["title"] = request.title.strip()
        if request.username is not None:
            clean_u = request.username.strip()
            target["username"] = clean_u if clean_u.startswith("@") else f"@{clean_u}"
        if request.telegram_chat_id is not None:
            target["telegram_chat_id"] = request.telegram_chat_id.strip()
        if request.is_connected is not None:
            target["is_connected"] = request.is_connected
        if request.bot_is_admin is not None:
            target["bot_is_admin"] = request.bot_is_admin
        if request.settings is not None:
            target["settings"] = request.settings.model_dump()

        _save_channels(items)

    return ChannelResponse(
        id=target["id"],
        company_id=company_id,
        title=target["title"],
        username=target["username"],
        telegram_chat_id=target["telegram_chat_id"],
        subscriber_count=target.get("subscriber_count", 0),
        is_connected=target.get("is_connected", True),
        bot_is_admin=target.get("bot_is_admin", True),
        settings=ChannelSettings(**target.get("settings", {})),
        created_at=target.get("created_at", "2026-10-16T12:00:00Z"),
    )


@router.delete(
    "/companies/{company_id}/channels/{channel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_company_channel(company_id: str, channel_id: str) -> None:
    """Disconnect and delete a Telegram channel from the company workspace."""
    with _lock:
        items = _load_channels()
        items = [c for c in items if not (c.get("id") == channel_id and c.get("company_id") == company_id)]
        _save_channels(items)
