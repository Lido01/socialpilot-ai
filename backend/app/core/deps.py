"""FastAPI dependency injection for database sessions, auth, and RBAC."""

from __future__ import annotations

import logging
from typing import AsyncGenerator, Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, ResourceNotFoundError
from app.core.security import decode_access_token, is_platform_owner
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.company_membership import CompanyMembership
from app.models.user import User

logger = logging.getLogger(__name__)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate JWT from Authorization header, return user."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")

    token = auth_header[7:]
    payload = decode_access_token(token, settings)

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise AuthenticationError("User not found")

    return user


def get_current_membership(
    company_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CompanyMembership | None:
    """Return the user's membership in the specified company, or None."""
    membership = (
        db.query(CompanyMembership)
        .filter(
            CompanyMembership.company_id == company_id,
            CompanyMembership.user_id == current_user.id,
            CompanyMembership.is_active == True,
        )
        .first()
    )
    return membership


def require_company_membership(
    company_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CompanyMembership:
    """Require an active membership in the specified company."""
    membership = (
        db.query(CompanyMembership)
        .filter(
            CompanyMembership.company_id == company_id,
            CompanyMembership.user_id == current_user.id,
            CompanyMembership.is_active == True,
        )
        .first()
    )
    if not membership:
        raise ResourceNotFoundError()
    return membership


def get_platform_owner(
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> User:
    """Require the current user to be the platform owner."""
    if not is_platform_owner(current_user.telegram_id, settings):
        raise AuthenticationError("Platform owner access required")
    return current_user
