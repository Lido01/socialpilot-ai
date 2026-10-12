"""User model — platform-level user record, one per Telegram account."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.company_membership import CompanyMembership
    from app.models.company_registration_request import CompanyRegistrationRequest


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    language_code: Mapped[str | None] = mapped_column(String(8), nullable=True)

    memberships: Mapped[list["CompanyMembership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    owned_companies: Mapped[list["Company"]] = relationship(
        back_populates="owner",
        foreign_keys="Company.owner_user_id",
    )
    registration_requests: Mapped[list["CompanyRegistrationRequest"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="CompanyRegistrationRequest.user_id",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id})>"
