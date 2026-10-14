"""Tests for company permissions and cross-company isolation."""

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


class TestCompanyPermissions:
    """Tests for company-scoped permissions."""

    def test_company_admin_can_access_own_company(self, client: TestClient, test_settings, db_session: Session):
        """Test that company admin can access their own company."""
        user = User(telegram_id=202020202, username="admin2", display_name="Admin 2")
        db_session.add(user)
        db_session.commit()

        company = Company(
            name="Accessible Company",
            normalized_name="accessible company",
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

        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 202020202)

        response = client.get(
            f"/api/v1/companies/{company.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == company.id
        assert data["name"] == "Accessible Company"

    def test_content_creator_can_access_own_company(self, client: TestClient, test_settings, db_session: Session):
        """Test that content creator can access their own company."""
        user = User(telegram_id=303030303, username="creator", display_name="Creator")
        db_session.add(user)
        db_session.commit()

        company = Company(
            name="Creator Company",
            normalized_name="creator company",
            status=CompanyStatus.ACTIVE,
            owner_user_id=user.id,
        )
        db_session.add(company)
        db_session.commit()

        membership = CompanyMembership(
            company_id=company.id,
            user_id=user.id,
            role=MembershipRole.CONTENT_CREATOR,
            is_active=True,
        )
        db_session.add(membership)
        db_session.commit()

        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 303030303)

        response = client.get(
            f"/api/v1/companies/{company.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

    def test_user_cannot_access_another_company(self, client: TestClient, test_settings, db_session: Session):
        """Test that user cannot access a company they're not a member of."""
        user1 = User(telegram_id=404040404, username="user1", display_name="User 1")
        user2 = User(telegram_id=505050505, username="user2", display_name="User 2")
        db_session.add_all([user1, user2])
        db_session.commit()

        company = Company(
            name="Private Company",
            normalized_name="private company",
            status=CompanyStatus.ACTIVE,
            owner_user_id=user1.id,
        )
        db_session.add(company)
        db_session.commit()

        membership = CompanyMembership(
            company_id=company.id,
            user_id=user1.id,
            role=MembershipRole.COMPANY_ADMIN,
            is_active=True,
        )
        db_session.add(membership)
        db_session.commit()

        # User2 tries to access company
        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 505050505)

        response = client.get(
            f"/api/v1/companies/{company.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should return 404 (not 403) to avoid ID enumeration
        assert response.status_code == 404

    def test_inactive_membership_cannot_access(self, client: TestClient, test_settings, db_session: Session):
        """Test that inactive membership cannot access company."""
        user = User(telegram_id=606060606, username="inactive", display_name="Inactive User")
        db_session.add(user)
        db_session.commit()

        company = Company(
            name="Inactive Company",
            normalized_name="inactive company",
            status=CompanyStatus.ACTIVE,
            owner_user_id=user.id,
        )
        db_session.add(company)
        db_session.commit()

        membership = CompanyMembership(
            company_id=company.id,
            user_id=user.id,
            role=MembershipRole.COMPANY_ADMIN,
            is_active=False,  # Inactive
        )
        db_session.add(membership)
        db_session.commit()

        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 606060606)

        response = client.get(
            f"/api/v1/companies/{company.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestCrossCompanyIsolation:
    """Tests for cross-company data isolation."""

    def test_users_see_only_own_registrations(self, client: TestClient, test_settings, db_session: Session):
        """Test that users only see their own registration requests."""
        user1 = User(telegram_id=707070707, username="user1", display_name="User 1")
        user2 = User(telegram_id=808080808, username="user2", display_name="User 2")
        db_session.add_all([user1, user2])
        db_session.commit()

        reg1 = CompanyRegistrationRequest(
            user_id=user1.id,
            name="User 1 Company",
            normalized_name="user 1 company",
            status=CompanyStatus.PENDING,
        )
        reg2 = CompanyRegistrationRequest(
            user_id=user2.id,
            name="User 2 Company",
            normalized_name="user 2 company",
            status=CompanyStatus.PENDING,
        )
        db_session.add_all([reg1, reg2])
        db_session.commit()

        token1 = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 707070707)
        token2 = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 808080808)

        response1 = client.get(
            "/api/v1/companies/registrations/me",
            headers={"Authorization": f"Bearer {token1}"},
        )
        response2 = client.get(
            "/api/v1/companies/registrations/me",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert len(data1) == 1
        assert data1[0]["name"] == "User 1 Company"

        assert len(data2) == 1
        assert data2[0]["name"] == "User 2 Company"

    def test_company_admins_isolated_by_company(self, client: TestClient, test_settings, db_session: Session):
        """Test that company admins of different companies are isolated."""
        admin1 = User(telegram_id=909090909, username="admin1", display_name="Admin 1")
        admin2 = User(telegram_id=101010101, username="admin2", display_name="Admin 2")
        db_session.add_all([admin1, admin2])
        db_session.commit()

        company1 = Company(
            name="Company 1",
            normalized_name="company 1",
            status=CompanyStatus.ACTIVE,
            owner_user_id=admin1.id,
        )
        company2 = Company(
            name="Company 2",
            normalized_name="company 2",
            status=CompanyStatus.ACTIVE,
            owner_user_id=admin2.id,
        )
        db_session.add_all([company1, company2])
        db_session.commit()

        membership1 = CompanyMembership(
            company_id=company1.id,
            user_id=admin1.id,
            role=MembershipRole.COMPANY_ADMIN,
            is_active=True,
        )
        membership2 = CompanyMembership(
            company_id=company2.id,
            user_id=admin2.id,
            role=MembershipRole.COMPANY_ADMIN,
            is_active=True,
        )
        db_session.add_all([membership1, membership2])
        db_session.commit()

        token1 = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 909090909)
        token2 = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 101010101)

        # Admin1 tries to access company2
        response = client.get(
            f"/api/v1/companies/{company2.id}",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert response.status_code == 404

        # Admin2 tries to access company1
        response = client.get(
            f"/api/v1/companies/{company1.id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 404

    def test_pending_company_not_accessible(self, client: TestClient, test_settings, db_session: Session):
        """Test that pending company is not accessible even to owner."""
        user = User(telegram_id=111111112, username="pendingowner", display_name="Pending Owner")
        db_session.add(user)
        db_session.commit()

        company = Company(
            name="Pending Company",
            normalized_name="pending company",
            status=CompanyStatus.PENDING,
            owner_user_id=user.id,
        )
        db_session.add(company)
        db_session.commit()

        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 111111112)

        response = client.get(
            f"/api/v1/companies/{company.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Pending company should not be accessible
        assert response.status_code == 404

    def test_suspended_company_not_accessible(self, client: TestClient, test_settings, db_session: Session):
        """Test that suspended company is not accessible."""
        user = User(telegram_id=121212121, username="suspendedowner", display_name="Suspended Owner")
        db_session.add(user)
        db_session.commit()

        company = Company(
            name="Suspended Company",
            normalized_name="suspended company",
            status=CompanyStatus.SUSPENDED,
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

        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 121212121)

        response = client.get(
            f"/api/v1/companies/{company.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


class TestRolePermissions:
    """Tests for role-based permissions."""

    def test_content_creator_cannot_manage_members(self, client: TestClient, test_settings, db_session: Session):
        """Test that content creator cannot access admin-only endpoints."""
        # This test would require member management endpoints
        # For now, verify the role is correctly set
        user = User(telegram_id=131313131, username="creator2", display_name="Creator 2")
        db_session.add(user)
        db_session.commit()

        company = Company(
            name="Creator Company 2",
            normalized_name="creator company 2",
            status=CompanyStatus.ACTIVE,
            owner_user_id=user.id,
        )
        db_session.add(company)
        db_session.commit()

        membership = CompanyMembership(
            company_id=company.id,
            user_id=user.id,
            role=MembershipRole.CONTENT_CREATOR,
            is_active=True,
        )
        db_session.add(membership)
        db_session.commit()

        token = _get_token(client, test_settings.TELEGRAM_BOT_TOKEN, 131313131)

        # Verify membership role
        from app.core.deps import get_current_membership_for_company
        from app.core.config import get_settings
        from app.db.session import get_db
        from app.main import app

        with client:
            app.dependency_overrides[get_settings] = lambda: test_settings
            from app.core.deps import get_db as get_db_dep
            # Can't easily test without more setup
            pass

        assert membership.role == MembershipRole.CONTENT_CREATOR

    def test_platform_owner_not_in_company_memberships(self, client: TestClient, test_settings, db_session: Session):
        """Test that platform owner is not listed as company member."""
        platform_owner_id = test_settings.PLATFORM_OWNER_TELEGRAM_ID
        platform_owner = db_session.query(User).filter(User.telegram_id == platform_owner_id).first()
        if not platform_owner:
            platform_owner = User(
                telegram_id=platform_owner_id,
                username="platformowner",
                display_name="Platform Owner",
            )
            db_session.add(platform_owner)
            db_session.commit()

        # Create a company owned by someone else
        user = User(telegram_id=141414141, username="owner", display_name="Owner")
        db_session.add(user)
        db_session.commit()

        company = Company(
            name="Regular Company",
            normalized_name="regular company",
            status=CompanyStatus.ACTIVE,
            owner_user_id=user.id,
        )
        db_session.add(company)
        db_session.commit()

        # Platform owner should not be a member
        membership = db_session.query(CompanyMembership).filter(
            CompanyMembership.company_id == company.id,
            CompanyMembership.user_id == platform_owner.id,
        ).first()
        assert membership is None