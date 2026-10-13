"""Tests for Telegram authentication."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from app.core.security import validate_init_data
from app.models import User


def _make_init_data(
    bot_token: str,
    user_id: int = 123456789,
    first_name: str = "Test",
    last_name: str = "User",
    username: str = "testuser",
    language_code: str = "en",
    auth_date: int | None = None,
) -> str:
    """Generate a valid initData string for testing."""
    if auth_date is None:
        auth_date = int(time.time())

    user_data = {
        "id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "language_code": language_code,
        "is_premium": False,
        "allows_write_to_pm": True,
    }
    user_json = json.dumps(user_data, separators=(",", ":"))

    pairs = {
        "query_id": "test_query_123",
        "user": user_json,
        "auth_date": str(auth_date),
    }

    data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs.keys()))

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

    pairs["hash"] = expected_hash

    return "&".join(f"{k}={quote(v)}" for k, v in pairs.items())


class TestTelegramAuthValidation:
    """Tests for initData validation logic."""

    def test_validate_valid_init_data(self, test_settings):
        """Test that valid initData passes validation."""
        init_data = _make_init_data(test_settings.TELEGRAM_BOT_TOKEN)
        user_data = validate_init_data(
            init_data=init_data,
            bot_token=test_settings.TELEGRAM_BOT_TOKEN,
            max_age_seconds=test_settings.TELEGRAM_INITDATA_MAX_AGE_SECONDS,
        )
        assert user_data["id"] == 123456789
        assert user_data["first_name"] == "Test"
        assert user_data["username"] == "testuser"

    def test_validate_invalid_hash(self, test_settings):
        """Test that invalid hash is rejected."""
        init_data = _make_init_data(test_settings.TELEGRAM_BOT_TOKEN)
        # Corrupt the hash
        init_data = init_data.replace("hash=", "hash=invalid")
        with pytest.raises(Exception) as exc:
            validate_init_data(
                init_data=init_data,
                bot_token=test_settings.TELEGRAM_BOT_TOKEN,
                max_age_seconds=test_settings.TELEGRAM_INITDATA_MAX_AGE_SECONDS,
            )
        assert "Hash mismatch" in str(exc.value)

    def test_validate_expired_init_data(self, test_settings):
        """Test that expired initData is rejected."""
        old_auth_date = int(time.time()) - 7200  # 2 hours ago
        init_data = _make_init_data(test_settings.TELEGRAM_BOT_TOKEN, auth_date=old_auth_date)
        with pytest.raises(Exception) as exc:
            validate_init_data(
                init_data=init_data,
                bot_token=test_settings.TELEGRAM_BOT_TOKEN,
                max_age_seconds=3600,  # 1 hour max age
            )
        assert "expired" in str(exc.value).lower()

    def test_validate_empty_init_data(self, test_settings):
        """Test that empty initData is rejected."""
        with pytest.raises(Exception) as exc:
            validate_init_data(
                init_data="",
                bot_token=test_settings.TELEGRAM_BOT_TOKEN,
                max_age_seconds=test_settings.TELEGRAM_INITDATA_MAX_AGE_SECONDS,
            )
        assert "empty" in str(exc.value).lower()

    def test_validate_missing_user_field(self, test_settings):
        """Test that missing user field is rejected."""
        auth_date = int(time.time())
        pairs = {
            "query_id": "test_query_123",
            "auth_date": str(auth_date),
        }
        data_check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs.keys()))
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=test_settings.TELEGRAM_BOT_TOKEN.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        expected_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        pairs["hash"] = expected_hash
        init_data = "&".join(f"{k}={v}" for k, v in pairs.items())

        with pytest.raises(Exception) as exc:
            validate_init_data(
                init_data=init_data,
                bot_token=test_settings.TELEGRAM_BOT_TOKEN,
                max_age_seconds=test_settings.TELEGRAM_INITDATA_MAX_AGE_SECONDS,
            )
        assert "Missing user field" in str(exc.value)

    def test_validate_tampered_user_data(self, test_settings):
        """Test that tampered user data (different user id) is rejected."""
        init_data = _make_init_data(test_settings.TELEGRAM_BOT_TOKEN, user_id=123456789)
        # Try to use with different bot token (simulating tampering)
        with pytest.raises(Exception) as exc:
            validate_init_data(
                init_data=init_data,
                bot_token="different_bot_token",
                max_age_seconds=test_settings.TELEGRAM_INITDATA_MAX_AGE_SECONDS,
            )
        assert "Hash mismatch" in str(exc.value)

    def test_replay_protection(self, test_settings):
        """Test that replayed initData is rejected."""
        init_data = _make_init_data(test_settings.TELEGRAM_BOT_TOKEN)
        nonce_cache: set[str] = set()

        # First use should succeed
        validate_init_data(
            init_data=init_data,
            bot_token=test_settings.TELEGRAM_BOT_TOKEN,
            max_age_seconds=test_settings.TELEGRAM_INITDATA_MAX_AGE_SECONDS,
            nonce_cache=nonce_cache,
        )

        # Second use should fail
        with pytest.raises(Exception) as exc:
            validate_init_data(
                init_data=init_data,
                bot_token=test_settings.TELEGRAM_BOT_TOKEN,
                max_age_seconds=test_settings.TELEGRAM_INITDATA_MAX_AGE_SECONDS,
                nonce_cache=nonce_cache,
            )
        assert "replayed" in str(exc.value).lower()


class TestAuthEndpoint:
    """Tests for POST /api/v1/auth/telegram endpoint."""

    def test_auth_telegram_success(self, client: TestClient, test_settings):
        """Test successful Telegram authentication returns JWT."""
        init_data = _make_init_data(test_settings.TELEGRAM_BOT_TOKEN)

        response = client.post(
            "/api/v1/auth/telegram",
            json={"init_data": init_data},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

        # Verify token can be decoded
        from app.core.security import decode_access_token
        payload = decode_access_token(data["access_token"], test_settings)
        assert "sub" in payload
        assert "tid" in payload
        assert payload["type"] == "access"

    def test_auth_telegram_invalid_init_data(self, client: TestClient, test_settings):
        """Test that invalid initData returns 401."""
        response = client.post(
            "/api/v1/auth/telegram",
            json={"init_data": "invalid_init_data"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "INIT_DATA_INVALID"

    def test_auth_telegram_missing_init_data(self, client: TestClient):
        """Test that missing initData returns 422."""
        response = client.post(
            "/api/v1/auth/telegram",
            json={},
        )

        assert response.status_code == 422

    def test_auth_telegram_creates_user(self, client: TestClient, test_settings, db_session):
        """Test that authentication creates a user record."""
        init_data = _make_init_data(test_settings.TELEGRAM_BOT_TOKEN, user_id=999888777)

        response = client.post(
            "/api/v1/auth/telegram",
            json={"init_data": init_data},
        )

        assert response.status_code == 200

        user = db_session.query(User).filter(User.telegram_id == 999888777).first()
        assert user is not None
        assert user.username == "testuser"
        assert user.display_name == "Test User"

    def test_auth_telegram_upserts_existing_user(self, client: TestClient, test_settings, db_session):
        """Test that authentication updates existing user."""
        init_data = _make_init_data(test_settings.TELEGRAM_BOT_TOKEN, user_id=123456789, username="olduser")

        response = client.post(
            "/api/v1/auth/telegram",
            json={"init_data": init_data},
        )

        assert response.status_code == 200

        user = db_session.query(User).filter(User.telegram_id == 123456789).first()
        assert user is not None
        assert user.username == "testuser"  # Updated from initData

    def test_auth_telegram_no_bot_token_configured(self, client: TestClient, db_session):
        """Test that missing bot token returns 401."""
        from app.core.config import get_settings
        from app.main import app

        # Override settings with no bot token
        def no_bot_token_settings():
            from app.core.config import Settings
            return Settings(
                DATABASE_URL="sqlite:///:memory:",
                SECRET_KEY="test-secret-key-for-testing-only",
                TELEGRAM_BOT_TOKEN="",
                TELEGRAM_INITDATA_MAX_AGE_SECONDS=3600,
                PLATFORM_OWNER_TELEGRAM_ID=999999999,
                APP_ENV="development",
                DEBUG=True,
            )

        app.dependency_overrides[get_settings] = no_bot_token_settings
        try:
            init_data = "query_id=test&user=%7B%22id%22%3A123%7D&auth_date=1234567890&hash=abc"
            response = client.post(
                "/api/v1/auth/telegram",
                json={"init_data": init_data},
            )

            assert response.status_code == 401
            data = response.json()
            assert data["error"]["code"] == "UNAUTHENTICATED"
        finally:
            app.dependency_overrides.clear()