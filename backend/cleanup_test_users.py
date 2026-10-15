from app.db.session import engine
from sqlalchemy import text

# Remove test artifacts created by an earlier test run (not real user data)
with engine.begin() as conn:
    result = conn.execute(
        text("DELETE FROM users WHERE telegram_id IN (123456789, 999888777)")
    )
    print("Deleted rows:", result.rowcount)

with engine.connect() as conn:
    users = conn.execute(text("SELECT telegram_id, username, display_name FROM users")).fetchall()
    print("Remaining users:", users)