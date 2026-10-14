"""CompanyMembership model — join table linking users to companies with roles.

Three-role system:
- Company Admin: full workspace control
- Content Creator: content creation and submission
- Platform Owner: global scope, not stored as a company membership
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User


class MembershipRole:
    COMPANY_ADMIN = "company_admin"
    CONTENT_CREATOR = "content_owner"

    ALL = {COMPANY_ADMIN, CONTENT_CREATOR}


class CompanyMembership(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "company_memberships"
    __table_args__ = (
        UniqueConstraint("company_id", "user_id", name="uq_membership_company_user"),
    )

    company_id: Mapped[str] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=MembershipRole.CONTENT_CREATOR,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    company: Mapped["Company"] = relationship(
        back_populates="memberships",
    )
    user: Mapped["User"] = relationship(
        back_populates="memberships",
    )

    def __repr__(self) -> str:
        return (
            f"<CompanyMembership(id={self.id}, "
            f"company_id={self.company_id}, user_id={self.user_id}, "
            f"role={self.role})>"
        )
