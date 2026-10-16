"""Tests for Platform Owner endpoints."""

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
    RegistrationStatus,
    User,
    AuditLog,
)


def _get_token(client: TestClient, bot_token: str, user_id: int) -> str:
    """Get auth token for a user."""
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

    init_data = "&".join(f"{k}={quote(v)}" for k, v in pairs.items())

    response = client.post("/api/v1/auth/telegram", json={"init_data": init_data})
    return response.json()["access_token"]


class TestPlatformOwnerEndpoints:
    """Tests for Platform Owner admin endpoints."""

    def test_list_pending_companies_success(self, client: TestClient, test_settings, db_session: Session):
        """Test Platform Owner can list pending registrations."""
        platform_owner_id = test_settings.PLATFORM_OWNER_TELEGRAM_ID
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, platform_owner_id)

        # Create some pending requests
        user1 = db_session.query(User).filter(User.telegram_id == 111111111).first()
        if not user1:
            user1 = User(telegram_id=111111111, username="user1", display_name="User 1")
            db_session.add(user1)
            db_session.commit()

        user2 = db_session.query(User).filter(User.telegram_id == 222222222).first()
        if not user2:
            user2 = User(telegram_id=222222222, username="user2", display_name="User 2")
            db_session.add(user2)
            db_session.commit()

        req1 = CompanyRegistrationRequest(
            user_id=user1.id,
            name="Company A",
            normalized_name="company a",
            status=CompanyStatus.PENDING,
        )
        req2 = CompanyRegistrationRequest(
            user_id=user2.id,
            name="Company B",
            normalized_name="company b",
            status=CompanyStatus.PENDING,
        )
        db_session.add_all([req1, req2])
        db_session.commit()

        response = client.get(
            "/api/v1/owner-admin/companies/pending",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Company A"
        assert data[1]["name"] == "Company B"
        assert data[0]["user_telegram_id"] == 111111111
        assert data[1]["user_telegram_id"] == 222222222

    def test_list_pending_companies_forbidden_for_non_owner(self, client: TestClient, test_settings, db_session: Session):
        """Test that non-platform-owner cannot list pending registrations."""
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 123456789)

        response = client.get(
            "/api/v1/owner-admin/companies/pending",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "UNAUTHENTICATED"

    def test_approve_company_success(self, client: TestClient, test_settings, db_session: Session):
        """Test Platform Owner can approve a pending registration."""
        platform_owner_id = test_settings.PLATFORM_OWNER_TELEGRAM_ID
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, platform_owner_id)

        user = db_session.query(User).filter(User.telegram_id == 333333333).first()
        if not user:
            user = User(telegram_id=333333333, username="user3", display_name="User 3")
            db_session.add(user)
            db_session.commit()

        reg_request = CompanyRegistrationRequest(
            user_id=user.id,
            name="New Company",
            normalized_name="new company",
            industry="Tech",
            status=CompanyStatus.PENDING,
        )
        db_session.add(reg_request)
        db_session.commit()

        response = client.post(
            f"/api/v1/owner-admin/companies/{reg_request.id}/approve",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["company_id"] is not None
        assert data["company_status"] == "active"

        # Verify company created and active
        company = db_session.query(Company).filter(Company.id == data["company_id"]).first()
        assert company is not None
        assert company.status == CompanyStatus.ACTIVE
        assert company.owner_user_id == user.id

        # Verify membership created
        membership = db_session.query(CompanyMembership).filter(
            CompanyMembership.company_id == company.id,
            CompanyMembership.user_id == user.id,
        ).first()
        assert membership is not None
        assert membership.role == MembershipRole.COMPANY_ADMIN
        assert membership.is_active is True

        # Verify registration request updated
        db_session.refresh(reg_request)
        assert reg_request.status == RegistrationStatus.APPROVED
        assert reg_request.company_id == company.id

    def test_approve_company_creates_audit_log(self, client: TestClient, test_settings, db_session: Session):
        """Test that approving a company creates an audit log entry."""
        platform_owner_id = test_settings.PLATFORM_OWNER_TELEGRAM_ID
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, platform_owner_id)

        user = User(telegram_id=444444444, username="user4", display_name="User 4")
        db_session.add(user)
        db_session.commit()

        reg_request = CompanyRegistrationRequest(
            user_id=user.id,
            name="Audit Company",
            normalized_name="audit company",
            status=CompanyStatus.PENDING,
        )
        db_session.add(reg_request)
        db_session.commit()

        response = client.post(
            f"/api/v1/owner-admin/companies/{reg_request.id}/approve",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        audit = db_session.query(AuditLog).filter(
            AuditLog.action == "company.approved",
            AuditLog.entity_id == response.json()["company_id"],
        ).first()
        assert audit is not None
        assert audit.actor_user_id == db_session.query(User).filter(User.telegram_id == platform_owner_id).first().id
        assert audit.entity_type == "company"
        assert audit.company_id == response.json()["company_id"]
        assert "registration_request_id" in audit.meta

    def test_approve_nonexistent_request_fails(self, client: TestClient, test_settings):
        """Test that approving non-existent request returns 404."""
        platform_owner_id = test_settings.PLATFORM_OWNER_TELEGRAM_ID
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, platform_owner_id)

        response = client.post(
            "/api/v1/owner-admin/companies/non-existent-id/approve",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_approve_already_processed_request_fails(self, client: TestClient, test_settings, db_session: Session):
        """Test that approving already processed request returns 404."""
        platform_owner_id = test_settings.PLATFORM_OWNER_TELEGRAM_ID
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, platform_owner_id)

        user = User(telegram_id=555555555, username="user5", display_name="User 5")
        db_session.add(user)
        db_session.commit()

        reg_request = CompanyRegistrationRequest(
            user_id=user.id,
            name="Processed Company",
            normalized_name="processed company",
            status=RegistrationStatus.APPROVED,  # Already approved
        )
        db_session.add(reg_request)
        db_session.commit()

        response = client.post(
            f"/api/v1/owner-admin/companies/{reg_request.id}/approve",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    def test_approve_duplicate_company_prevented(self, client: TestClient, test_settings, db_session: Session):
        """Test that approving duplicate company name for same user is prevented."""
        platform_owner_id = test_settings.PLATFORM_OWNER_TELEGRAM_ID
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, platform_owner_id)

        user = User(telegram_id=666666666, username="user6", display_name="User 6")
        db_session.add(user)
        db_session.commit()

        # Create an active company with this name
        existing = Company(
            name="Duplicate Company",
            normalized_name="duplicate company",
            status=CompanyStatus.ACTIVE,
            owner_user_id=user.id,
        )
        db_session.add(existing)
        db_session.commit()

        # Create pending request with same name
        reg_request = CompanyRegistrationRequest(
            user_id=user.id,
            name="Duplicate Company",
            normalized_name="duplicate company",
            status=CompanyStatus.PENDING,
        )
        db_session.add(reg_request)
        db_session.commit()

        response = client.post(
            f"/api/v1/owner-admin/companies/{reg_request.id}/approve",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "CONFLICT"

    def test_reject_company_success(self, client: TestClient, test_settings, db_session: Session):
        """Test Platform Owner can reject a pending registration."""
        platform_owner_id = test_settings.PLATFORM_OWNER_TELEGRAM_ID
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, platform_owner_id)

        user = User(telegram_id=777777777, username="user7", display_name="User 7")
        db_session.add(user)
        db_session.commit()

        reg_request = CompanyRegistrationRequest(
            user_id=user.id,
            name="Rejected Company",
            normalized_name="rejected company",
            status=CompanyStatus.PENDING,
        )
        db_session.add(reg_request)
        db_session.commit()

        response = client.post(
            f"/api/v1/owner-admin/companies/{reg_request.id}/reject",
            json={"reason": "Invalid industry"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["company_status"] == "rejected"

        db_session.refresh(reg_request)
        assert reg_request.status == RegistrationStatus.REJECTED
        assert reg_request.rejection_reason == "Invalid industry"
        assert reg_request.reviewed_by is not None

    def test_reject_company_creates_audit_log(self, client: TestClient, test_settings, db_session: Session):
        """Test that rejecting a company creates an audit log entry."""
        platform_owner_id = test_settings.PLATFORM_OWNER_TELEGRAM_ID
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, platform_owner_id)

        user = User(telegram_id=888888888, username="user8", display_name="User 8")
        db_session.add(user)
        db_session.commit()

        reg_request = CompanyRegistrationRequest(
            user_id=user.id,
            name="Reject Audit Company",
            normalized_name="reject audit company",
            status=CompanyStatus.PENDING,
        )
        db_session.add(reg_request)
        db_session.commit()

        response = client.post(
            f"/api/v1/owner-admin/companies/{reg_request.id}/reject",
            json={"reason": "Spam"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        audit = db_session.query(AuditLog).filter(
            AuditLog.action == "company.rejected",
            AuditLog.entity_id == reg_request.id,
        ).first()
        assert audit is not None
        assert audit.company_id is None  # Platform-level action
        assert audit.meta["reason"] == "Spam"

    def test_request_info_success(self, client: TestClient, test_settings, db_session: Session):
        """Test Platform Owner can request more info."""
        platform_owner_id = test_settings.PLATFORM_OWNER_TELEGRAM_ID
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, platform_owner_id)

        user = User(telegram_id=999999991, username="user9", display_name="User 9")
        db_session.add(user)
        db_session.commit()

        reg_request = CompanyRegistrationRequest(
            user_id=user.id,
            name="Info Requested Company",
            normalized_name="info requested company",
            status=CompanyStatus.PENDING,
        )
        db_session.add(reg_request)
        db_session.commit()

        response = client.post(
            f"/api/v1/owner-admin/companies/{reg_request.id}/request-info",
            json={"reason": "Please provide website URL"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["company_status"] == "info_requested"

        db_session.refresh(reg_request)
        assert reg_request.status == RegistrationStatus.INFO_REQUESTED

    def test_reject_invalid_reason(self, client: TestClient, test_settings):
        """Test that rejection requires a reason."""
        platform_owner_id = test_settings.PLATFORM_OWNER_TELEGRAM_ID
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, platform_owner_id)

        response = client.post(
            "/api/v1/owner-admin/companies/some-id/reject",
            json={"reason": ""},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422


class TestPlatformOwnerSecurity:
    """Tests for Platform Owner authorization."""

    def test_regular_user_cannot_approve(self, client: TestClient, test_settings, db_session: Session):
        """Test that regular user cannot approve companies."""
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 123456789)

        response = client.post(
            "/api/v1/owner-admin/companies/some-id/approve",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401

    def test_company_admin_cannot_approve(self, client: TestClient, test_settings, db_session: Session):
        """Test that company admin cannot approve companies."""
        # Create a user who is a company admin
        user = User(telegram_id=101010101, username="admin", display_name="Admin")
        db_session.add(user)
        db_session.commit()

        company = Company(
            name="Admin Company",
            normalized_name="admin company",
            status=CompanyStatus.ACTIVE,
            owner_user_id=user.id,
        )
        db_session.add(company)
        db_session.commit()

        membership = CompanyMembership(
            company_id=company.id,
            user_id=user.id,
            role=MembershipRole.COMPANY_ADMIN,
            is_active=True,
        )
        db_session.add(membership)
        db_session.commit()

        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 101010101)

        response = client.post(
            "/api/v1/owner-admin/companies/some-id/approve",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401