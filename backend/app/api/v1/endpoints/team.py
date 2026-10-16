"""Team management and creator invitation endpoints."""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any
from fastapi import APIRouter, Depends, Query, status

from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.team import (
    CheckInviteResponse,
    TeamMemberInviteRequest,
    TeamMemberPermissions,
    TeamMemberResponse,
)

router = APIRouter(tags=["team"])

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
INVITATIONS_FILE = os.path.join(DATA_DIR, "team_invitations.json")
_lock = threading.Lock()

INITIAL_INVITATIONS: list[dict[str, Any]] = [
    {
        "id": "member-1",
        "company_id": "comp-1",
        "company_name": "Apex Media Group",
        "display_name": "Alex Rivers",
        "username": "alex_rivers",
        "telegram_id": 5298799880,
        "role": "company_admin",
        "is_active": True,
        "assigned_channels": ["chan-1", "chan-2"],
        "permissions": {
            "can_create_posts": True,
            "can_use_ai": True,
            "can_auto_publish": True,
        },
        "joined_at": "2026-10-06T12:00:00Z",
    },
    {
        "id": "member-2",
        "company_id": "comp-1",
        "company_name": "Apex Media Group",
        "display_name": "Jordan Lee",
        "username": "jordan_creator",
        "telegram_id": 123456789,
        "role": "content_owner",
        "is_active": True,
        "assigned_channels": ["chan-1"],
        "permissions": {
            "can_create_posts": True,
            "can_use_ai": True,
            "can_auto_publish": False,
        },
        "joined_at": "2026-10-12T12:00:00Z",
    },
    {
        "id": "member-3",
        "company_id": "comp-1",
        "company_name": "Apex Media Group",
        "display_name": "Elena Rostova",
        "username": "elena_growth",
        "telegram_id": 987654321,
        "role": "content_owner",
        "is_active": True,
        "assigned_channels": ["chan-2"],
        "permissions": {
            "can_create_posts": True,
            "can_use_ai": True,
            "can_auto_publish": False,
        },
        "joined_at": "2026-10-14T12:00:00Z",
    },
]


def _load_invitations() -> list[dict[str, Any]]:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(INVITATIONS_FILE):
        _save_invitations(INITIAL_INVITATIONS)
        return list(INITIAL_INVITATIONS)
    try:
        with open(INVITATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return list(INITIAL_INVITATIONS)


def _save_invitations(items: list[dict[str, Any]]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(INVITATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)


@router.get(
    "/team/check-invite",
    response_model=CheckInviteResponse,
)
def check_invitation(
    username: str | None = Query(default=None),
    telegram_id: int | None = Query(default=None),
) -> CheckInviteResponse:
    """Check if a Telegram username or numeric ID has an active invitation to a company."""
    clean_user = username.replace("@", "").lower().strip() if username else None

    with _lock:
        items = _load_invitations()

    for item in items:
        if not item.get("is_active", True):
            continue

        item_user = item.get("username")
        clean_item_user = item_user.replace("@", "").lower().strip() if item_user else None

        matches_user = bool(clean_user and clean_item_user and clean_user == clean_item_user)
        matches_id = bool(telegram_id and item.get("telegram_id") == telegram_id)

        if matches_user or matches_id:
            return CheckInviteResponse(
                is_invited=True,
                role=item.get("role", "content_owner"),
                company_id=item.get("company_id", "comp-1"),
                company_name=item.get("company_name", "Apex Media Group"),
                member=TeamMemberResponse(
                    id=item["id"],
                    company_id=item.get("company_id", "comp-1"),
                    display_name=item["display_name"],
                    username=item.get("username"),
                    telegram_id=item.get("telegram_id"),
                    role=item.get("role", "content_owner"),
                    is_active=item.get("is_active", True),
                    assigned_channels=item.get("assigned_channels", ["chan-1"]),
                    permissions=TeamMemberPermissions(**item.get("permissions", {})),
                    joined_at=item.get("joined_at", "2026-10-16T12:00:00Z"),
                ),
            )

    return CheckInviteResponse(is_invited=False)


@router.get(
    "/companies/{company_id}/team",
    response_model=list[TeamMemberResponse],
)
def list_company_team(company_id: str) -> list[TeamMemberResponse]:
    """List team members for a company workspace."""
    with _lock:
        items = _load_invitations()

    result: list[TeamMemberResponse] = []
    for item in items:
        if item.get("company_id") == company_id:
            result.append(
                TeamMemberResponse(
                    id=item["id"],
                    company_id=company_id,
                    display_name=item["display_name"],
                    username=item.get("username"),
                    telegram_id=item.get("telegram_id"),
                    role=item.get("role", "content_owner"),
                    is_active=item.get("is_active", True),
                    assigned_channels=item.get("assigned_channels", ["chan-1"]),
                    permissions=TeamMemberPermissions(**item.get("permissions", {})),
                    joined_at=item.get("joined_at", "2026-10-16T12:00:00Z"),
                )
            )
    return result


@router.post(
    "/companies/{company_id}/team/invite",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def invite_team_member(
    company_id: str,
    request: TeamMemberInviteRequest,
) -> TeamMemberResponse:
    """Invite a creator or admin by Telegram username or ID."""
    clean_username = request.username.replace("@", "").strip() if request.username else None
    member_id = f"member-{int(time.time() * 1000)}"

    new_member_dict: dict[str, Any] = {
        "id": member_id,
        "company_id": company_id,
        "company_name": "Apex Media Group",
        "display_name": request.display_name.strip(),
        "username": clean_username,
        "telegram_id": request.telegram_id,
        "role": request.role,
        "is_active": True,
        "assigned_channels": request.assigned_channels,
        "permissions": request.permissions.model_dump(),
        "joined_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    with _lock:
        items = _load_invitations()
        # Remove any existing membership for same username to avoid duplicates
        if clean_username:
            items = [
                m
                for m in items
                if not (
                    m.get("username")
                    and m.get("username").replace("@", "").lower().strip() == clean_username.lower()
                )
            ]
        items.append(new_member_dict)
        _save_invitations(items)

    return TeamMemberResponse(
        id=member_id,
        company_id=company_id,
        display_name=request.display_name.strip(),
        username=clean_username,
        telegram_id=request.telegram_id,
        role=request.role,
        is_active=True,
        assigned_channels=request.assigned_channels,
        permissions=request.permissions,
        joined_at=new_member_dict["joined_at"],
    )


@router.delete(
    "/companies/{company_id}/team/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_team_member(company_id: str, member_id: str) -> None:
    """Remove a team member from the company workspace."""
    with _lock:
        items = _load_invitations()
        items = [m for m in items if m.get("id") != member_id]
        _save_invitations(items)
