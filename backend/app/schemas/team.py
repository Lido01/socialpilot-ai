"""Team member and invitation schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TeamMemberPermissions(BaseModel):
    can_create_posts: bool = True
    can_use_ai: bool = True
    can_auto_publish: bool = False


class TeamMemberInviteRequest(BaseModel):
    display_name: str
    username: str | None = None
    telegram_id: int | None = None
    role: str = "content_owner"
    assigned_channels: list[str] = Field(default_factory=lambda: ["chan-1"])
    permissions: TeamMemberPermissions = Field(default_factory=TeamMemberPermissions)


class TeamMemberResponse(BaseModel):
    id: str
    company_id: str
    display_name: str
    username: str | None = None
    telegram_id: int | None = None
    role: str
    is_active: bool = True
    assigned_channels: list[str] = Field(default_factory=list)
    permissions: TeamMemberPermissions
    joined_at: str


class CheckInviteResponse(BaseModel):
    is_invited: bool
    role: str | None = None
    member: TeamMemberResponse | None = None
    company_id: str | None = None
    company_name: str | None = None
