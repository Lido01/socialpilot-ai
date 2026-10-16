"""Authentication endpoints: Telegram initData validation and JWT issuance."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.deps import get_db
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    upsert_user_from_telegram,
    validate_init_data,
)
from app.schemas.auth import TelegramAuthRequest, TelegramAuthResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=TelegramAuthResponse)
def authenticate_telegram(
    request: TelegramAuthRequest,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> TelegramAuthResponse:
    """Validate Telegram initData and issue a JWT access token.

    This endpoint implements the official Telegram Mini Apps validation algorithm:
    1. Parse initData and extract hash
    2. Compute HMAC-SHA256 using bot token as secret
    3. Verify hash matches (constant-time comparison)
    4. Verify auth_date is within allowed window (24 hours + 5s skew)
    5. Check replay protection
    6. Upsert user in database
    7. Issue JWT
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise AuthenticationError("Telegram bot not configured")

    # Specific initData errors (INIT_DATA_INVALID / _EXPIRED / _REPLAYED) must
    # propagate with their own codes so the client can react appropriately.
    user_data = validate_init_data(
        init_data=request.init_data,
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        max_age_seconds=settings.TELEGRAM_INITDATA_MAX_AGE_SECONDS,
    )

    user = upsert_user_from_telegram(db, user_data)
    db.commit()

    access_token = create_access_token(
        user_id=user.id,
        telegram_id=user.telegram_id,
        settings=settings,
    )

    return TelegramAuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TTL_MINUTES * 60,
    )