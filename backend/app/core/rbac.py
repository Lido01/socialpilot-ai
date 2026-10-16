"""Role-Based Access Control with explicit permissions.

Three roles:
- Platform Owner: global scope (platform_* permissions)
- Company Admin: company scope (all company permissions)
- Content Creator: company scope (content creation permissions)
"""

from __future__ import annotations

from enum import Enum
from functools import wraps
from typing import Callable

from fastapi import Depends

from app.core.exceptions import PermissionDeniedError


class Role(str, Enum):
    PLATFORM_OWNER = "platform_owner"
    COMPANY_ADMIN = "company_admin"
    CONTENT_CREATOR = "content_owner"


class Permission(str, Enum):
    COMPANY_VIEW = "company:view"
    COMPANY_UPDATE = "company:update"
    COMPANY_DEACTIVATE = "company:deactivate"
    BRAND_VIEW = "brand:view"
    BRAND_UPDATE = "brand:update"
    MEMBER_INVITE = "member:invite"
    MEMBER_LIST = "member:list"
    MEMBER_ROLE_UPDATE = "member:role:update"
    MEMBER_REMOVE = "member:remove"
    CHANNEL_CONNECT = "channel:connect"
    CHANNEL_VERIFY = "channel:verify"
    CHANNEL_LIST = "channel:list"
    CHANNEL_DISCONNECT = "channel:disconnect"
    POST_CREATE = "post:create"
    POST_LIST = "post:list"
    POST_VIEW = "post:view"
    POST_UPDATE = "post:update"
    POST_DELETE = "post:delete"
    AI_TEXT_GENERATE = "ai:text:generate"
    AI_IMAGE_GENERATE = "ai:image:generate"
    MEDIA_UPLOAD = "media:upload"
    MEDIA_LIST = "media:list"
    MEDIA_DELETE = "media:delete"
    APPROVAL_SUBMIT = "approval:submit"
    APPROVAL_REVIEW = "approval:review"
    PUBLISH_EXECUTE = "publish:execute"
    SCHEDULE_MANAGE = "schedule:manage"
    USAGE_VIEW = "usage:view"
    AUDIT_VIEW = "audit:view"
    NOTIFICATION_VIEW = "notification:view"
    PLATFORM_COMPANY_APPROVE = "platform:company:approve"
    PLATFORM_COMPANY_SUSPEND = "platform:company:suspend"
    PLATFORM_COMPANY_REACTIVATE = "platform:company:reactivate"
    PLATFORM_PROVIDER_CONFIGURE = "platform:provider:configure"
    PLATFORM_METRICS_VIEW = "platform:metrics:view"


PLATFORM_OWNER_PERMISSIONS: set[Permission] = {
    Permission.PLATFORM_COMPANY_APPROVE,
    Permission.PLATFORM_COMPANY_SUSPEND,
    Permission.PLATFORM_COMPANY_REACTIVATE,
    Permission.PLATFORM_PROVIDER_CONFIGURE,
    Permission.PLATFORM_METRICS_VIEW,
}

COMPANY_ADMIN_PERMISSIONS: set[Permission] = {
    Permission.COMPANY_VIEW,
    Permission.COMPANY_UPDATE,
    Permission.COMPANY_DEACTIVATE,
    Permission.BRAND_VIEW,
    Permission.BRAND_UPDATE,
    Permission.MEMBER_INVITE,
    Permission.MEMBER_LIST,
    Permission.MEMBER_ROLE_UPDATE,
    Permission.MEMBER_REMOVE,
    Permission.CHANNEL_CONNECT,
    Permission.CHANNEL_VERIFY,
    Permission.CHANNEL_LIST,
    Permission.CHANNEL_DISCONNECT,
    Permission.POST_CREATE,
    Permission.POST_LIST,
    Permission.POST_VIEW,
    Permission.POST_UPDATE,
    Permission.POST_DELETE,
    Permission.AI_TEXT_GENERATE,
    Permission.AI_IMAGE_GENERATE,
    Permission.MEDIA_UPLOAD,
    Permission.MEDIA_LIST,
    Permission.MEDIA_DELETE,
    Permission.APPROVAL_SUBMIT,
    Permission.APPROVAL_REVIEW,
    Permission.PUBLISH_EXECUTE,
    Permission.SCHEDULE_MANAGE,
    Permission.USAGE_VIEW,
    Permission.AUDIT_VIEW,
    Permission.NOTIFICATION_VIEW,
}

CONTENT_CREATOR_PERMISSIONS: set[Permission] = {
    Permission.COMPANY_VIEW,
    Permission.BRAND_VIEW,
    Permission.POST_CREATE,
    Permission.POST_LIST,
    Permission.POST_VIEW,
    Permission.POST_UPDATE,
    Permission.POST_DELETE,
    Permission.AI_TEXT_GENERATE,
    Permission.AI_IMAGE_GENERATE,
    Permission.MEDIA_UPLOAD,
    Permission.MEDIA_LIST,
    Permission.APPROVAL_SUBMIT,
    Permission.CHANNEL_LIST,
    Permission.NOTIFICATION_VIEW,
}

ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.PLATFORM_OWNER: PLATFORM_OWNER_PERMISSIONS,
    Role.COMPANY_ADMIN: COMPANY_ADMIN_PERMISSIONS,
    Role.CONTENT_CREATOR: CONTENT_CREATOR_PERMISSIONS,
}


def get_permissions_for_role(role: Role) -> set[Permission]:
    """Return the permission set for a given role."""
    return ROLE_PERMISSIONS.get(role, set())


def require_permission(permission: Permission):
    """Dependency factory that enforces a specific permission."""

    def dependency(
        current_user=Depends("get_current_user"),
        current_membership=Depends("get_current_membership"),
    ) -> None:
        if current_membership is None:
            raise PermissionDeniedError()

        role = current_membership.role
        permissions = get_permissions_for_role(role)

        if permission not in permissions:
            raise PermissionDeniedError(
                f"Role '{role}' does not have permission '{permission.value}'"
            )

    return dependency
