"""Security utilities: JWT encoding/decoding and Telegram initData validation."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any
from urllib.parse import parse_qsl

import jwt

from app.core.config import Settings
from app.core.exceptions import (
    InitDataExpiredError,
    InitDataInvalidError,
    InitDataReplayedError,
    TokenExpiredError,
    TokenInvalidError,
)

logger = logging.getLogger(__name__)

JWT_ISSUER = "socialpilot-ai"
JWT_AUDIENCE = "socialpilot-api"
JWT_TYPE_ACCESS = "access"


def create_access_token(
    user_id: str,
    telegram_id: int,
    settings: Settings,
) -> str:
    """Create a JWT access token."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "tid": telegram_id,
        "iat": now,
        "exp": now + (settings.JWT_ACCESS_TTL_MINUTES * 60),
        "type": JWT_TYPE_ACCESS,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidTokenError:
        raise TokenInvalidError()

    if payload.get("type") != JWT_TYPE_ACCESS:
        raise TokenInvalidError("Invalid token type")

    return payload


def validate_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 3600,
    nonce_cache: set[str] | None = None,
) -> dict[str, Any]:
    """Validate Telegram initData using HMAC-SHA256.

    Returns the validated user data dictionary.
    Raises InitDataInvalidError, InitDataExpiredError, or InitDataReplayedError.
    """
    if not init_data or not init_data.strip():
        raise InitDataInvalidError("initData is empty")

    # Parse query string. Values must be URL-decoded (RFC 3986 / qs rules)
    # because the data_check_string that Telegram signs uses decoded values.
    pairs: dict[str, str] = {
        key: value for key, value in parse_qsl(init_data, keep_blank_values=True)
    }

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InitDataInvalidError("Missing hash")

    data_check_string = "\n".join(
        f"{key}={pairs[key]}" for key in sorted(pairs.keys())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    expected_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise InitDataInvalidError("Hash mismatch")

    auth_date_str = pairs.get("auth_date", "")
    try:
        auth_date = int(auth_date_str)
    except (ValueError, TypeError):
        raise InitDataInvalidError("Missing or invalid auth_date")

    now = int(time.time())
    if abs(now - auth_date) > max_age_seconds + 5:
        raise InitDataExpiredError()

    if nonce_cache is not None:
        replay_key = hashlib.sha256(init_data.encode("utf-8")).hexdigest()
        if replay_key in nonce_cache:
            raise InitDataReplayedError()
        nonce_cache.add(replay_key)

    user_json = pairs.get("user")
    if not user_json:
        raise InitDataInvalidError("Missing user field")

    try:
        user_data = json.loads(user_json)
    except (json.JSONDecodeError, TypeError):
        raise InitDataInvalidError("Invalid user JSON")

    if "id" not in user_data:
        raise InitDataInvalidError("Missing user id")

    return user_data


def is_platform_owner(telegram_id: int, settings: Settings) -> bool:
    """Check if a Telegram user ID belongs to the platform owner."""
    return (
        settings.PLATFORM_OWNER_TELEGRAM_ID is not None
        and telegram_id == settings.PLATFORM_OWNER_TELEGRAM_ID
    )


def upsert_user_from_telegram(
    db: "Session",
    telegram_user: dict[str, Any],
) -> "User":
    """Upsert a user from validated Telegram data.

    Creates a new user if not found, or updates existing user's display info.
    Returns the user record.
    """
    from app.models.user import User

    telegram_id = telegram_user["id"]
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if user:
        user.username = telegram_user.get("username")
        user.display_name = f"{telegram_user.get('first_name', '')} {telegram_user.get('last_name', '')}".strip()
        user.language_code = telegram_user.get("language_code")
        db.flush()
    else:
        user = User(
            telegram_id=telegram_id,
            username=telegram_user.get("username"),
            display_name=f"{telegram_user.get('first_name', '')} {telegram_user.get('last_name', '')}".strip(),
            language_code=telegram_user.get("language_code"),
        )
        db.add(user)
        db.flush()

    return user
