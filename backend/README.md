# SocialPilot AI — Backend

FastAPI backend foundation for a multi-tenant Telegram Mini App SaaS.

## Prerequisites

- Python 3.11+ (3.12 recommended)
- PostgreSQL 15+ (for production; SQLite for tests)
- pip

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Configuration

Edit `.env` with your values. Required variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key (32+ random bytes) |
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather |
| `PLATFORM_OWNER_TELEGRAM_ID` | Your Telegram user ID |

## Database Migrations

```powershell
alembic upgrade head
alembic revision --autogenerate -m "description"
alembic downgrade -1
```

## Running

```powershell
uvicorn app.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`.

## Testing

```powershell
pytest tests/ -v
pytest tests/ -v -k "test_health"
```

Tests use SQLite in-memory database. PostgreSQL-specific tests require a running PostgreSQL instance.

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── core/                # Config, security, deps, rbac, exceptions
│   ├── db/                  # Engine, session, base
│   ├── models/              # SQLAlchemy ORM models
│   ├── api/v1/              # API routers and endpoints
│   └── schemas/             # Pydantic request/response schemas
├── tests/                   # pytest test suite
├── migrations/              # Alembic migrations
├── alembic.ini
├── requirements.txt
└── .env.example
```

## Security

- Telegram initData validated server-side (HMAC-SHA256)
- JWT access tokens (HS256, 60min expiry)
- RBAC with explicit permissions (3 roles)
- Tenant isolation via company_id on all queries
- Secrets in environment variables only

## Roles

| Role | Scope | Description |
|------|-------|-------------|
| Platform Owner | Global | Platform admin, company approval/rejection, suspension |
| Company Admin | Company | Full workspace control, team, channels, approvals, publishing |
| Content Creator | Company | AI content, media uploads, drafts, submit for approval |
