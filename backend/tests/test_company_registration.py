"""Tests for company registration endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models import (
    Company,
    CompanyRegistrationRequest,
    CompanyStatus,
    CompanyMembership,
    MembershipRole,
    User,
)


def _auth_header(user: User, settings) -> dict:
    """Create Authorization header for a user."""
    token = create_access_token(user_id=user.id, telegram_id=user.telegram_id, settings=settings)
    return {"Authorization": f"Bearer {token}"}


def _make_init_data(bot_token: str, user_id: int = 123456789) -> str:
    """Generate a valid initData string for testing."""
    import hashlib
    import hmac
    import json
    import time
    from urllib.parse import quote

    auth_date = int(time.time())
    user_data = {
        "id": user_id,
        "first_name": "Test",
        "last_name": "User",
        "username": f"testuser{user_id}",
        "language_code": "en",
        "is_premium": False,
        "allows_write_to_pm": True,
    }
    user_json = json.dumps(user_data, separators=(",", ":"))

    pairs = {
        "query_id": f"test_query_{user_id}",
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


def _get_token(client: TestClient, bot_token: str, user_id: int = 123456789) -> str:
    """Get auth token for a user."""
    init_data = _make_init_data(bot_token, user_id)
    response = client.post("/api/v1/auth/telegram", json={"init_data": init_data})
    return response.json()["access_token"]


class TestCompanyRegistration:
    """Tests for company registration endpoints."""

    def test_register_company_success(self, client: TestClient, test_settings, db_session: Session):
        """Test successful company registration request."""
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN)

        response = client.post(
            "/api/v1/companies/register",
            json={
                "name": "Test Company",
                "industry": "Technology",
                "website": "https://example.com",
                "country": "US",
                "contact_email": "admin@example.com",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Company"
        assert data["normalized_name"] == "test company"
        assert data["industry"] == "Technology"
        assert data["status"] == "pending"
        assert "id" in data

        # Verify in database
        req = db_session.query(CompanyRegistrationRequest).filter(CompanyRegistrationRequest.id == data["id"]).first()
        assert req is not None
        assert req.user_id is not None
        assert req.status == CompanyStatus.PENDING

    def test_register_company_duplicate_pending_fails(self, client: TestClient, test_settings, db_session: Session):
        """Test that duplicate pending registration for same name fails."""
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN)

        # First registration
        response1 = client.post(
            "/api/v1/companies/register",
            json={"name": "Test Company"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response1.status_code == 201

        # Second registration with same name
        response2 = client.post(
            "/api/v1/companies/register",
            json={"name": "Test Company"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response2.status_code == 409
        data = response2.json()
        assert data["error"]["code"] == "CONFLICT"

    def test_register_company_duplicate_different_owner_allowed(self, client: TestClient, test_settings, db_session: Session):
        """Test that different users can register same company name."""
        token1 = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, user_id=111111111)
        token2 = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, user_id=222222222)

        response1 = client.post(
            "/api/v1/companies/register",
            json={"name": "Test Company"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert response1.status_code == 201

        response2 = client.post(
            "/api/v1/companies/register",
            json={"name": "Test Company"},
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response2.status_code == 201

    def test_register_company_validation_errors(self, client: TestClient, test_settings):
        """Test validation errors for company registration."""
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN)

        # Empty name
        response = client.post(
            "/api/v1/companies/register",
            json={"name": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

        # Invalid website
        response = client.post(
            "/api/v1/companies/register",
            json={"name": "Test", "website": "not-a-url"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

        # Invalid email
        response = client.post(
            "/api/v1/companies/register",
            json={"name": "Test", "contact_email": "not-an-email"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

        # Invalid country code
        response = client.post(
            "/api/v1/companies/register",
            json={"name": "Test", "country": "USA"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_register_company_unauthorized(self, client: TestClient):
        """Test that unauthenticated request fails."""
        response = client.post(
            "/api/v1/companies/register",
            json={"name": "Test Company"},
        )
        assert response.status_code == 401

    def test_list_my_registrations(self, client: TestClient, test_settings, db_session: Session):
        """Test listing user's registration requests."""
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN)

        # Create multiple requests
        client.post("/api/v1/companies/register", json={"name": "Company A"}, headers={"Authorization": f"Bearer {token}"})
        client.post("/api/v1/companies/register", json={"name": "Company B"}, headers={"Authorization": f"Bearer {token}"})

        response = client.get(
            "/api/v1/companies/registrations/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Company B"  # Most recent first
        assert data[1]["name"] == "Company A"

    def test_get_company_requires_membership(self, client: TestClient, test_settings, db_session: Session):
        """Test that getting company details requires membership."""
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN)

        # Create a registration and approve it manually
        reg = CompanyRegistrationRequest(
            user_id=db_session.query(User).first().id,
            name="Test Company",
            normalized_name="test company",
            status=CompanyStatus.PENDING,
        )
        db_session.add(reg)
        db_session.commit()

        # Try to get company without membership
        response = client.get(
            f"/api/v1/companies/{reg.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Should return 404 (not found) because no membership
        assert response.status_code == 404


class TestCompanyRegistrationBusinessRules:
    """Tests for business rules around company registration."""

    def test_cannot_register_if_active_company_exists(self, client: TestClient, test_settings, db_session: Session):
        """Test that user cannot register a company with same name as active one."""
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN)
        user = db_session.query(User).filter(User.telegram_id == 123456789).first()

        # Create an active company
        company = Company(
            name="Existing Company",
            normalized_name="existing company",
            status=CompanyStatus.ACTIVE,
            owner_user_id=user.id,
        )
        db_session.add(company)
        db_session.commit()

        # Try to register same name
        response = client.post(
            "/api/v1/companies/register",
            json={"name": "Existing Company"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "CONFLICT"

    def test_cannot_register_if_pending_company_exists(self, client: TestClient, test_settings, db_session: Session):
        """Test that user cannot register a company with same name as pending one."""
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN)
        user = db_session.query(User).filter(User.telegram_id == 123456789).first()

        # Create a pending company
        company = Company(
            name="Pending Company",
            normalized_name="pending company",
            status=CompanyStatus.PENDING,
            owner_user_id=user.id,
        )
        db_session.add(company)
        db_session.commit()

        # Try to register same name
        response = client.post(
            "/api/v1/companies/register",
            json={"name": "Pending Company"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 409