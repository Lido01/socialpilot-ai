"""CompanyRegistrationRequest model — tracks the lifecycle of a company registration.

This table is an addition to the documented database design (docs/05).
It provides a dedicated audit trail for registration decisions.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User


class RegistrationStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    INFO_REQUESTED = "info_requested"

    ALL = {PENDING, APPROVED, REJECTED, INFO_REQUESTED}


class CompanyRegistrationRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "company_registration_requests"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[str | None] = mapped_column(
        ForeignKey("companies.id"),
        nullable=True,
        index=True,
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
        default=RegistrationStatus.PENDING,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="registration_requests",
        foreign_keys=[user_id],
    )
    company: Mapped["Company | None"] = relationship(
        back_populates="registration_requests",
        foreign_keys=[company_id],
    )
    reviewer: Mapped["User | None"] = relationship(
        foreign_keys=[reviewed_by],
        lazy="joined",
    )

    def __repr__(self) -> str:
        return (
            f"<CompanyRegistrationRequest(id={self.id}, "
            f"name={self.name}, status={self.status})>"
        )
