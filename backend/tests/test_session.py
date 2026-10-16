from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def test_session_local_creation(db_session: Session) -> None:
    assert db_session is not None
    assert isinstance(db_session, Session)


def test_engine_connection(db_engine) -> None:
    with db_engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_session_rollback(db_session: Session) -> None:
    from app.models import User

    user = User(
        telegram_id=111222333,
        username="rollbacktest",
        display_name="Rollback Test",
    )
    db_session.add(user)
    db_session.flush()
    db_session.rollback()

    result = db_session.query(User).filter(User.telegram_id == 111222333).first()
    assert result is None


def test_session_commit_persists(db_session: Session) -> None:
    from app.models import User

    user = User(
        telegram_id=444555666,
        username="committest",
        display_name="Commit Test",
    )
    db_session.add(user)
    db_session.commit()

    result = db_session.query(User).filter(User.telegram_id == 444555666).first()
    assert result is not None
    assert result.display_name == "Commit Test"
