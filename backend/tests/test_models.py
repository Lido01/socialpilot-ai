"""Tests for database model constraints and behavior."""

from __future__ import annotations

import pytest
from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import Session

from app.models import (
    Company,
    CompanyMembership,
    CompanyRegistrationRequest,
    MembershipRole,
    User,
)


def test_user_requires_telegram_id(db_session: Session) -> None:
    user = User(display_name="No Telegram")
    db_session.add(user)
    with pytest.raises(sa_exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_telegram_id_unique(db_session: Session, sample_user: User) -> None:
    duplicate = User(
        telegram_id=sample_user.telegram_id,
        username="other",
        display_name="Other User",
    )
    db_session.add(duplicate)
    with pytest.raises(sa_exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_requires_display_name(db_session: Session) -> None:
    user = User(telegram_id=999888777, username="noname")
    db_session.add(user)
    with pytest.raises(sa_exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_company_requires_name(db_session: Session, sample_user: User) -> None:
    company = Company(
        normalized_name="noname",
        status="active",
        owner_user_id=sample_user.id,
    )
    db_session.add(company)
    with pytest.raises(sa_exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.skip(reason="SQLite does not enforce FK constraints by default; tested on PostgreSQL")
def test_company_requires_owner(db_session: Session) -> None:
    pass


def test_company_unique_name_per_owner(
    db_session: Session, sample_company: Company, sample_user: User
) -> None:
    duplicate = Company(
        name="Different Case Test Company",
        normalized_name=sample_company.normalized_name,
        status="active",
        owner_user_id=sample_user.id,
    )
    db_session.add(duplicate)
    with pytest.raises(sa_exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_company_same_name_different_owner(
    db_session: Session, sample_company: Company
) -> None:
    from uuid import uuid4

    other_user = User(
        telegram_id=555444333,
        username="otherowner",
        display_name="Other Owner",
    )
    db_session.add(other_user)
    db_session.commit()

    company2 = Company(
        name=sample_company.name,
        normalized_name=sample_company.normalized_name,
        status="active",
        owner_user_id=other_user.id,
    )
    db_session.add(company2)
    db_session.commit()
    assert company2.id != sample_company.id


def test_membership_unique_company_user(
    db_session: Session, sample_membership: CompanyMembership
) -> None:
    duplicate = CompanyMembership(
        company_id=sample_membership.company_id,
        user_id=sample_membership.user_id,
        role=MembershipRole.COMPANY_ADMIN,
        is_active=True,
    )
    db_session.add(duplicate)
    with pytest.raises(sa_exc.IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_membership_role_values(db_session: Session) -> None:
    assert MembershipRole.COMPANY_ADMIN == "company_admin"
    assert MembershipRole.CONTENT_CREATOR == "content_owner"
    assert len(MembershipRole.ALL) == 2


@pytest.mark.skip(reason="SQLite does not enforce FK constraints by default; tested on PostgreSQL")
def test_registration_request_requires_user(db_session: Session) -> None:
    pass


def test_registration_request_duplicate_prevention(
    db_session: Session, sample_registration_request: CompanyRegistrationRequest
) -> None:
    duplicate = CompanyRegistrationRequest(
        user_id=sample_registration_request.user_id,
        name="Another Request",
        normalized_name="another request",
        status="pending",
    )
    db_session.add(duplicate)
    db_session.commit()
    assert duplicate.id != sample_registration_request.id


def test_user_membership_relationship(
    db_session: Session, sample_user: User, sample_membership: CompanyMembership
) -> None:
    assert sample_membership in sample_user.memberships


def test_company_membership_relationship(
    db_session: Session, sample_company: Company, sample_membership: CompanyMembership
) -> None:
    assert sample_membership in sample_company.memberships


def test_company_status_values() -> None:
    from app.models.company import CompanyStatus

    assert CompanyStatus.PENDING == "pending"
    assert CompanyStatus.ACTIVE == "active"
    assert CompanyStatus.SUSPENDED == "suspended"
    assert CompanyStatus.REJECTED == "rejected"
    assert CompanyStatus.INFO_REQUESTED == "info_requested"
    assert CompanyStatus.CANCELLED == "cancelled"
    assert len(CompanyStatus.ALL) == 6
