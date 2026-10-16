"""Company model — a tenant workspace, the root of all company-owned data."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company_membership import CompanyMembership
    from app.models.company_registration_request import CompanyRegistrationRequest
    from app.models.user import User


class CompanyStatus:
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REJECTED = "rejected"
    INFO_REQUESTED = "info_requested"
    CANCELLED = "cancelled"

    ALL = {PENDING, ACTIVE, SUSPENDED, REJECTED, INFO_REQUESTED, CANCELLED}


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("normalized_name", "owner_user_id", name="uq_company_name_owner"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=CompanyStatus.PENDING,
    )
    owner_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    owner: Mapped["User"] = relationship(
        back_populates="owned_companies",
        foreign_keys=[owner_user_id],
    )
    memberships: Mapped[list["CompanyMembership"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )
    registration_requests: Mapped[list["CompanyRegistrationRequest"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name}, status={self.status})>"
