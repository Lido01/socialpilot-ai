"""Tests for application configuration and settings validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.APP_ENV == "development"
    assert settings.DEBUG is False
    assert settings.APP_NAME == "SocialPilot AI"


def test_settings_app_env_validation() -> None:
    with pytest.raises(ValidationError):
        Settings(APP_ENV="invalid_env")


def test_settings_valid_app_envs() -> None:
    for env in ["development", "staging", "production"]:
        settings = Settings(APP_ENV=env)
        assert settings.APP_ENV == env


def test_settings_database_url_default() -> None:
    settings = Settings()
    assert "postgresql" in settings.DATABASE_URL or "sqlite" in settings.DATABASE_URL


def test_settings_cors_origins_parsing() -> None:
    settings = Settings(CORS_ORIGINS="https://a.com, https://b.com")
    assert "https://a.com" in settings.cors_origins_list
    assert "https://b.com" in settings.cors_origins_list


def test_settings_jwt_defaults() -> None:
    settings = Settings()
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.JWT_ACCESS_TTL_MINUTES == 60
    assert settings.JWT_REFRESH_TTL_DAYS == 30


def test_settings_platform_owner_none_by_default() -> None:
    settings = Settings()
    assert settings.PLATFORM_OWNER_TELEGRAM_ID is None


def test_settings_platform_owner_with_value() -> None:
    settings = Settings(PLATFORM_OWNER_TELEGRAM_ID=123456789)
    assert settings.PLATFORM_OWNER_TELEGRAM_ID == 123456789
