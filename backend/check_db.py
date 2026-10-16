from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    users = conn.execute(text("SELECT telegram_id, username, display_name FROM users ORDER BY telegram_id")).fetchall()
    print("USERS:", users)
    companies = conn.execute(text("SELECT name, normalized_name, status FROM companies")).fetchall()
    print("COMPANIES:", companies)
    reqs = conn.execute(text("SELECT name, status FROM company_registration_requests")).fetchall()
    print("REG REQUESTS:", reqs)
    audits = conn.execute(text("SELECT action, entity_type FROM audit_logs")).fetchall()
    print("AUDITS:", audits)