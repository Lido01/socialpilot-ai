"""Shared pytest fixtures for the backend test suite."""

from __future__ import annotations

import os
import sys
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import Settings
from app.db.base import Base
from app.main import app
from app.models import (  # noqa: F401
    Company,
    CompanyMembership,
    CompanyRegistrationRequest,
    User,
)


@pytest.fixture(autouse=True)
def _isolate_environment(monkeypatch) -> None:
    """Make tests hermetic: ignore the developer's real .env and shell env.

    Without this, Settings() inside unit tests picks up backend/.env
    (APP_ENV, DEBUG, PLATFORM_OWNER_TELEGRAM_ID, real DATABASE_URL, ...) and
    produces misleading failures.
    """
    for var in [
        "APP_ENV",
        "DEBUG",
        "APP_NAME",
        "LOG_LEVEL",
        "LOG_JSON",
        "DATABASE_URL",
        "DATABASE_POOL_SIZE",
        "DATABASE_MAX_OVERFLOW",
        "DATABASE_POOL_TIMEOUT",
        "DATABASE_ECHO",
        "SECRET_KEY",
        "JWT_ALGORITHM",
        "JWT_ACCESS_TTL_MINUTES",
        "JWT_REFRESH_TTL_DAYS",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_BOT_USERNAME",
        "TELEGRAM_INITDATA_MAX_AGE_SECONDS",
        "TELEGRAM_NONCE_TTL_SECONDS",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "IMAGE_GENERATION_PROVIDER",
        "MEDIA_STORAGE_ROOT",
        "MEDIA_SERVE_PATH",
        "CORS_ORIGINS",
        "RATE_LIMIT_PER_MINUTE",
        "PLATFORM_OWNER_TELEGRAM_ID",
        "COMPANY_REGISTRATION_MODE",
        "INVITATION_TTL_HOURS",
        "AUDIT_LOG_RETENTION_DAYS",
        "SENTRY_DSN",
        "METRICS_ENABLED",
    ]:
        monkeypatch.delenv(var, raising=False)

    monkeypatch.setattr(
        Settings,
        "model_config",
        {**Settings.model_config, "env_file": None},
    )


@pytest.fixture()
def test_settings() -> Settings:
    return Settings(
        DATABASE_URL="sqlite:///:memory:",
        SECRET_KEY="test-secret-key-for-testing-only",
        TELEGRAM_BOT_TOKEN="test_bot_token_12345",
        TELEGRAM_INITDATA_MAX_AGE_SECONDS=3600,
        PLATFORM_OWNER_TELEGRAM_ID=999999999,
        APP_ENV="development",
        DEBUG=True,
    )


@pytest.fixture()
def db_engine(test_settings: Settings):
    engine = create_engine(
        test_settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(
    test_settings: Settings,
    db_session: Session,
    db_engine,
) -> Generator[TestClient, None, None]:
    import app.core.deps as deps_module
    from app.core.config import get_settings
    from app.db.session import get_db as session_get_db
    from app.main import app

    # Endpoints resolve their session two ways:
    # 1. Route signature `Depends(get_db)` -> dependency_overrides applies.
    # 2. Nested lookups inside get_current_user*, which captured SessionLocal
    #    at import time -> patch the module attribute instead.
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[deps_module.get_db] = lambda: db_session
    app.dependency_overrides[session_get_db] = lambda: db_session

    original_session_local = deps_module.SessionLocal
    deps_module.SessionLocal = TestSessionLocal
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        deps_module.SessionLocal = original_session_local
        app.dependency_overrides.clear()


@pytest.fixture()
def sample_user(db_session: Session) -> User:
    user = User(
        telegram_id=123456789,
        username="testuser",
        display_name="Test User",
        language_code="en",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def sample_company(db_session: Session, sample_user: User) -> Company:
    company = Company(
        name="Test Company",
        normalized_name="test company",
        industry="Technology",
        status="active",
        owner_user_id=sample_user.id,
    )
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    return company


@pytest.fixture()
def sample_membership(db_session: Session, sample_company: Company, sample_user: User) -> CompanyMembership:
    membership = CompanyMembership(
        company_id=sample_company.id,
        user_id=sample_user.id,
        role="company_admin",
        is_active=True,
    )
    db_session.add(membership)
    db_session.commit()
    db_session.refresh(membership)
    return membership


@pytest.fixture()
def sample_registration_request(db_session: Session, sample_user: User) -> CompanyRegistrationRequest:
    request = CompanyRegistrationRequest(
        user_id=sample_user.id,
        name="New Company",
        normalized_name="new company",
        industry="E-commerce",
        status="pending",
    )
    db_session.add(request)
    db_session.commit()
    db_session.refresh(request)
    return request
