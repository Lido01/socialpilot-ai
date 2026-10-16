"""AuditLog model — security-relevant action log."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Security-relevant action log for audit trail.

    Column types use ``with_variant`` so production PostgreSQL gets the
    documented ``JSONB``/``INET`` types, while the SQLite-backed test database
    falls back to portable ``JSON``/``TEXT``.
    """

    __tablename__ = "audit_logs"

    company_id: Mapped[str | None] = mapped_column(
        ForeignKey("companies.id"),
        nullable=True,
        index=True,
    )
    actor_user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(nullable=True, index=True)
    meta: Mapped[dict | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        Text().with_variant(INET(), "postgresql"),
        nullable=True,
    )

    company: Mapped["Company | None"] = relationship(
        foreign_keys=[company_id],
    )
    actor: Mapped["User"] = relationship(
        foreign_keys=[actor_user_id],
    )

    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action}, entity={self.entity_type}:{self.entity_id})>"