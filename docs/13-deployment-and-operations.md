# 13 — Deployment and Operations

This document describes how to run SocialPilot AI locally on Windows/PowerShell, how to deploy it to production with Docker or hosted platforms, and how to operate it cost-consciously at small scale. It is written for a solo developer acting as operator. For architecture context, see [04-system-architecture.md](04-system-architecture.md); for cost-driving features (rate limits, quotas, usage tracking), see [02-software-requirements.md](02-software-requirements.md) and [03-user-roles-and-use-cases.md](03-user-roles-and-use-cases.md).

> **Current repository state:** the repository today contains the single-admin bot prototype (`app/bot.py`, `app/ai_service.py`, `app/database.py`) backed by SQLite, with its own minimal `.env.example`. The layouts and environment files described in this document describe the **target** multi-tenant architecture introduced in Phase 0 of the [implementation roadmap](14-implementation-roadmap.md).

---

## 1. Architecture Overview

```mermaid
flowchart LR
    subgraph Local Development — Windows
        FE["React + Vite<br/>localhost:5173"] -->|proxy /api, /media| BE["FastAPI + Uvicorn<br/>localhost:8000"]
        BE --> PG[("PostgreSQL 15+<br/>localhost:5432")]
        BE --> TG["Telegram API"]
        BOT["Bot poller<br/>python-telegram-bot"] --> PG
        BOT --> TG
    end
```

```mermaid
flowchart LR
    subgraph Production
        U["Telegram client"] -->|"HTTPS (required for Mini App)"| RP["Reverse proxy<br/>nginx / Caddy + TLS"]
        RP -->|static assets| FE["Frontend container<br/>nginx serving Vite build"]
        RP -->|/api, /media| BE["Backend container<br/>uvicorn / gunicorn"]
        BE --> PG[("PostgreSQL")]
        BE --> TG["Telegram API"]
        BE --> FS[("Media volume")]
        BOT["Bot poller container"] --> PG
        BOT --> TG
    end
```

**Component summary**

| Component | Local | Production | Notes |
|-----------|-------|------------|-------|
| Backend (FastAPI) | uvicorn, port 8000 | container or hosted platform | Single deployable; see ADR-001 |
| Frontend (React/Vite) | Vite dev server, port 5173 | static build behind nginx or static host | Must be served over HTTPS for Mini App; see ADR-010 |
| Bot poller | separate Python process | container or hosted worker | Single polling instance only; see ADR-009 |
| PostgreSQL | local instance 15+ | container or hosted managed DB | Required service; see ADR-002 |
| Media storage | local directory | Docker volume (MVP) | S3-compatible later; see ADR-008 |

---

## 2. Local Development (Windows / PowerShell)

### 2.1 Required Tools

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| Python | 3.11+ (3.12 recommended) | Backend, bot, migrations | Use the Windows installer; enable "Add to PATH" |
| Node.js | 18+ LTS (20 recommended) | Frontend build/dev server | Includes npm |
| PostgreSQL | 15+ | Database | EDB Windows installer or portable binaries |
| Git | Any recent | Source control | |
| Docker Desktop | Latest | Optional | Only needed to rehearse the production container layout locally |
| PowerShell | 5.1+ (default) | All commands below | Run as a normal user; no admin rights needed |

### 2.2 Expected Repository Layout (post Phase 0)

```
socialpilot-ai/
├── backend/            # FastAPI application, domain modules, Alembic
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.example
├── frontend/           # Vite + React + TypeScript Mini App
│   ├── src/
│   ├── index.html
│   ├── package.json
│   └── .env.example
├── bot/                # python-telegram-bot polling worker
│   ├── bot/
│   ├── requirements.txt
│   └── .env.example
├── docs/
├── .env                # Git-ignored; per-component secrets live here
└── docker-compose.yml  # Production rehearsal (optional locally)
```

### 2.3 Environment Variables

All components read configuration from environment variables (12-factor). In development, load them from a git-ignored `.env` file next to each component's entry point; `pydantic-settings` (backend) and Vite (`VITE_*` prefix) handle loading.

#### 2.3.1 Backend

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_ENV` | Yes | `development` | `development`, `staging`, or `production` |
| `DEBUG` | No | `false` | Debug mode; **must be false in production** |
| `APP_NAME` | No | `SocialPilot AI` | Service name in logs and health output |
| `LOG_LEVEL` | No | `INFO` | Root log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_JSON` | No | `true` | Emit structured JSON logs (always on in production) |
| `DATABASE_URL` | Yes | — | PostgreSQL connection URL (see 2.4) |
| `DATABASE_POOL_SIZE` | No | `10` | SQLAlchemy connection pool size |
| `DATABASE_MAX_OVERFLOW` | No | `20` | Extra connections allowed under load |
| `DATABASE_POOL_TIMEOUT` | No | `30` | Seconds to wait for a pooled connection |
| `DATABASE_ECHO` | No | `false` | Log all SQL statements (dev only) |
| `SECRET_KEY` | Yes (prod) | — | HMAC secret for JWT signing; generate with 32+ random bytes |
| `JWT_ALGORITHM` | No | `HS256` | Token signing algorithm |
| `JWT_ACCESS_TTL_MINUTES` | No | `60` | Access token lifetime |
| `JWT_REFRESH_TTL_DAYS` | No | `30` | Refresh token lifetime |
| `TELEGRAM_BOT_TOKEN` | Yes | — | Bot token from BotFather (Mini App host + publisher) |
| `TELEGRAM_BOT_USERNAME` | Yes | — | Bot username without `@` |
| `TELEGRAM_INITDATA_MAX_AGE_SECONDS` | No | `3600` | Reject `initData` older than this (replay protection) |
| `TELEGRAM_NONCE_TTL_SECONDS` | No | `86400` | How long consumed `initData` nonces are remembered |
| `GEMINI_API_KEY` | Yes (AI) | — | Google AI Studio / Vertex API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash-lite` | Model used for text generation (cheapest tier by default) |
| `GEMINI_MAX_OUTPUT_TOKENS` | No | `1024` | Cap on generated tokens |
| `GEMINI_TIMEOUT_SECONDS` | No | `30` | Request timeout |
| `GEMINI_DAILY_QUOTA_PER_COMPANY` | No | `200` | Safety cap per company per day; `0` = unlimited |
| `IMAGE_GENERATION_PROVIDER` | No | `none` | `none`, `replicate`, `fal`, `openai`, `local` |
| `IMAGE_GENERATION_API_KEY` | No | — | Provider API key |
| `IMAGE_GENERATION_MODEL` | No | — | Provider model ID |
| `IMAGE_GENERATION_DEFAULT_SIZE` | No | `1024x1024` | Default output size |
| `IMAGE_GENERATION_TIMEOUT_SECONDS` | No | `60` | Request timeout |
| `IMAGE_GENERATION_QUOTA_PER_COMPANY_MONTH` | No | `50` | Monthly cap per company; `0` = unlimited |
| `MEDIA_STORAGE_ROOT` | Yes (prod) | `./data/media` | Absolute path to the media storage root |
| `MEDIA_MAX_UPLOAD_MB` | No | `10` | Per-file upload limit |
| `MEDIA_ALLOWED_EXTENSIONS` | No | `jpg,jpeg,png,webp,gif,mp4` | Comma-separated allow-list |
| `MEDIA_SERVE_PATH` | No | `/media` | URL prefix under which media is served |
| `CORS_ORIGINS` | Yes (prod) | — | Comma-separated allowed HTTP origins |
| `RATE_LIMIT_PER_MINUTE` | No | `100` | Default per-user API rate limit |
| `INVITATION_TTL_HOURS` | No | `72` | Team invitation link expiry |
| `AUDIT_LOG_RETENTION_DAYS` | No | `365` | Audit log retention |
| `PLATFORM_OWNER_TELEGRAM_ID` | Yes (bootstrap) | — | Telegram ID bootstrapped as the first platform owner |
| `COMPANY_REGISTRATION_MODE` | No | `approval` | `approval` (MVP) or `open` |
| `SENTRY_DSN` | No | — | Optional server-side error tracking |
| `METRICS_ENABLED` | No | `false` | Expose Prometheus `/metrics` |

#### 2.3.2 Frontend (Vite)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000` | Backend origin. Dev can rely on the Vite proxy instead |
| `VITE_TELEGRAM_BOT_USERNAME` | Yes | — | Bot that hosts the Mini App (opens it from a menu/button) |
| `VITE_MINI_APP_VERSION` | No | `8.0` | Minimum Telegram client version to target |
| `VITE_SENTRY_DSN` | No | — | Optional client-side error tracking |
| `VITE_ENABLE_MOCKS` | No | `false` | Enable API mocks for UI development |

> **Security note:** `VITE_*` variables are inlined into the client bundle at build time and are **public**. Never place secrets in frontend environment variables.

#### 2.3.3 Bot Worker

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | Same database as the backend |
| `TELEGRAM_BOT_TOKEN` | Yes | — | Same bot token (single bot for Mini App + publishing in MVP) |
| `LOG_LEVEL` | No | `INFO` | Log level |
| `BOT_POLLING_TIMEOUT` | No | `30` | `getUpdates` long-poll timeout in seconds |
| `BOT_ALLOWED_UPDATES` | No | `message,callback_query` | Update types to process |
| `REDIS_URL` | No | — | Future: webhook/queue scaling (see [scaling path](#-7-scaling-path)) |
| `TELEGRAM_WEBHOOK_SECRET` | No | — | Future: secret token for webhook requests |
| `TELEGRAM_WEBHOOK_PATH` | No | `/webhook/bot` | Future: webhook endpoint path |

### 2.4 Local PostgreSQL Setup

If you installed PostgreSQL via the EDB Windows installer, the service is already running and you only need steps 4–5. For a portable/manual setup, run all steps once:

```powershell
# 1. Add PostgreSQL binaries to PATH (adjust version/path as installed)
$env:PATH += ";C:\Program Files\PostgreSQL\15\bin"

# 2. Initialize a data directory (one time only)
initdb -D "$env:LOCALAPPDATA\socialpilot-pgdata" -U postgres --auth=scram-sha-256

# 3. Start the server on port 5432 (one time; logs to file)
pg_ctl -D "$env:LOCALAPPDATA\socialpilot-pgdata" -l "$env:LOCALAPPDATA\socialpilot-pg.log" start

# 4. Set the postgres superuser password (one time only)
psql -U postgres -c "ALTER USER postgres PASSWORD 'postgres';"

# 5. Create the application database
createdb -U postgres socialpilot
```

**Connection string used by backend and bot:**

```
postgresql+psycopg://postgres:postgres@localhost:5432/socialpilot
```

> Use `postgresql+psycopg://` (the modern `psycopg` 3 driver). The legacy `postgresql://` scheme uses `psycopg2` and is supported only as a fallback.

### 2.5 Backend Startup

```powershell
cd backend

# Create and activate a virtual environment (one time)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies (one time, and after dependency changes)
pip install -e ".[dev]"

# Provide configuration
Copy-Item .env.example .env   # then edit .env

# Run with auto-reload on port 8000
uvicorn app.main:app --reload --port 8000
```

The API is then available at `http://localhost:8000` with interactive docs at `/docs`.

### 2.6 Frontend Startup

```powershell
cd frontend
npm install
npm run dev
```

Vite serves the Mini App at `http://localhost:5173` and proxies API and media requests to the backend so no CORS issues arise during development:

| Frontend path | Proxies to | Purpose |
|---------------|-----------|---------|
| `/api` | `http://localhost:8000` | REST API |
| `/media` | `http://localhost:8000` | Authenticated media responses |

To exercise the Mini App inside Telegram during development, expose the dev server over HTTPS with a tunnel (e.g., `ngrok http 5173`) and register the tunnel URL as the Mini App URL in BotFather. Localhost alone cannot be opened as a Mini App because Telegram requires HTTPS.

### 2.7 Bot Startup

```powershell
cd bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then edit .env
python -m bot.main
```

**Only one polling instance may run at a time.** Telegram delivers each update to exactly one `getUpdates` caller; running two instances duplicates work and can cause duplicate processing.

### 2.8 Database Migrations (Alembic)

```powershell
cd backend

# One time: initialize Alembic
alembic init alembic
# then wire alembic/env.py to read DATABASE_URL and import all ORM models

# After model changes: generate a migration (review the diff before committing!)
alembic revision --autogenerate -m "create companies and memberships"

# Apply all pending migrations
alembic upgrade head

# Roll back one revision
alembic downgrade -1

# Inspect history and current revision
alembic history
alembic current
```

**Rules:** never edit an applied migration; always review autogenerated diffs (especially drops and renames); keep migrations small and named after the feature.

### 2.9 Test Execution

```powershell
# Backend (from repo root)
python -m pytest backend/tests -q                                  # full suite
python -m pytest backend/tests -q -m "not slow"                    # skip integration tests
python -m pytest backend/tests -q -k "initdata"                    # subset by name
python -m pytest backend/tests -q --cov=app --cov-report=term-missing

# Frontend (from frontend/)
npm run test            # vitest unit/component tests
npm run typecheck       # tsc --noEmit
npm run lint            # eslint
npm run build           # production build smoke test
```

CI runs lint, typecheck, backend tests, and the frontend build on every pull request (see Phase 0 of the [roadmap](14-implementation-roadmap.md)).

### 2.10 Example Environment Files

These examples are safe to commit: they contain no real secrets, only placeholders. Copy each to `.env` adjacent to the component and replace placeholders with real values. Never commit a populated `.env`.

**`backend/.env.example`**

```ini
# --- Core ---
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
LOG_JSON=false

# --- Database ---
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/socialpilot
DATABASE_POOL_SIZE=5
DATABASE_ECHO=false

# --- Auth / JWT ---
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=replace-with-a-long-random-string
JWT_ACCESS_TTL_MINUTES=60
JWT_REFRESH_TTL_DAYS=30

# --- Telegram ---
TELEGRAM_BOT_TOKEN=123456:replace-with-botfather-token
TELEGRAM_BOT_USERNAME=your_bot_username
TELEGRAM_INITDATA_MAX_AGE_SECONDS=3600
TELEGRAM_NONCE_TTL_SECONDS=86400

# --- AI: text (Gemini) ---
GEMINI_API_KEY=replace-with-google-ai-studio-key
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_DAILY_QUOTA_PER_COMPANY=200

# --- AI: image generation (optional in MVP) ---
IMAGE_GENERATION_PROVIDER=none
IMAGE_GENERATION_API_KEY=
IMAGE_GENERATION_MODEL=
IMAGE_GENERATION_QUOTA_PER_COMPANY_MONTH=50

# --- Media ---
MEDIA_STORAGE_ROOT=./data/media
MEDIA_MAX_UPLOAD_MB=10
MEDIA_ALLOWED_EXTENSIONS=jpg,jpeg,png,webp,gif,mp4
MEDIA_SERVE_PATH=/media

# --- HTTP ---
CORS_ORIGINS=http://localhost:5173
RATE_LIMIT_PER_MINUTE=100

# --- Platform bootstrap ---
PLATFORM_OWNER_TELEGRAM_ID=replace-with-your-telegram-id
COMPANY_REGISTRATION_MODE=approval
INVITATION_TTL_HOURS=72
AUDIT_LOG_RETENTION_DAYS=365

# --- Observability (optional) ---
SENTRY_DSN=
METRICS_ENABLED=false
```

**`frontend/.env.example`**

```ini
VITE_API_BASE_URL=http://localhost:8000
VITE_TELEGRAM_BOT_USERNAME=your_bot_username
VITE_MINI_APP_VERSION=8.0
VITE_SENTRY_DSN=
VITE_ENABLE_MOCKS=false
```

**`bot/.env.example`**

```ini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/socialpilot
TELEGRAM_BOT_TOKEN=123456:replace-with-botfather-token
LOG_LEVEL=INFO
BOT_POLLING_TIMEOUT=30
BOT_ALLOWED_UPDATES=message,callback_query
# REDIS_URL=             # future
# TELEGRAM_WEBHOOK_SECRET=  # future
# TELEGRAM_WEBHOOK_PATH=/webhook/bot
```

### 2.11 Troubleshooting (Local)

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| `uvicorn` fails: "address already in use" on port 8000 | Another backend process is running | Stop the other process (`Get-NetTCPConnection -LocalPort 8000` to find it) or use another port |
| `psycopg.OperationalError: could not connect to server` | PostgreSQL not started, or wrong host/port/credentials | `pg_ctl -D "$env:LOCALAPPDATA\socialpilot-pgdata" start`; verify `DATABASE_URL` |
| `password authentication failed for user "postgres"` | Password was never set or differs | Re-run the `ALTER USER postgres PASSWORD` step from 2.4 |
| Frontend calls fail with CORS errors | Backend `CORS_ORIGINS` does not include `http://localhost:5173` | Add the dev origin; keep the proxy (2.6) as the primary path |
| Mini App opens but auth fails (`401` from `/auth/login`) | `initData` validation failing — wrong bot token, stale `initData`, or clock skew | Verify `TELEGRAM_BOT_TOKEN`; retry (initData is single-use and time-limited); check server clock |
| Bot starts but then "terminated by other getUpdates request" | Two polling instances running | Stop all but one bot process |
| Bot responds to prototype commands, not Mini App | You are running the legacy `app/bot.py` prototype, not the target bot module | Start the target worker from `bot/` (see 2.7) |
| Alembic: "Can't locate revision identified by ..." | Migration history drift between environments | Run `alembic history` on both sides; reconcile with a new merge revision |
| `alembic revision --autogenerate` produced empty/unexpected diff | Models not imported in `env.py`, or DB out of sync | Import all model modules in `env.py`; run `alembic upgrade head` first |
| Gemini calls fail with quota/429 | Free-tier quota exhausted or billing not enabled | Check Google AI Studio quotas; confirm `GEMINI_DAILY_QUOTA_PER_COMPANY` cap; verify key |
| Image upload rejected though file looks valid | Extension/MIME mismatch or size over `MEDIA_MAX_UPLOAD_MB` | Check client sends correct `Content-Type`; verify size limit |
| Media URL returns 404 in the Mini App | Media path not proxied/served in that environment | Dev: use the Vite proxy (2.6); Prod: route `/media` through the reverse proxy |
| Frontend env changes have no effect | Vite only reads env at startup | Restart `npm run dev` after changing `.env` |

---

## 3. Production Deployment

### 3.1 Docker Architecture

Two images plus a database compose the production topology. Keep the images small, non-root, and pinned by digest in CI.

**`Dockerfile.frontend` — multi-stage static build**

| Stage | Base | Purpose |
|-------|------|---------|
| Build | `node:20-alpine` | `npm ci`, `npm run build` producing `frontend/dist` |
| Serve | `nginx:alpine` | Serve static files; reverse-proxy `/api` and `/media` to the backend service; security headers; gzip |

Key properties: build-time `VITE_*` values are baked in at image build; nginx listens on port 80 (mapped to the host or internal compose network); SPA fallback (`try_files ... /index.html`) for client-side routes.

**`Dockerfile.backend` — API + worker**

| Stage | Base | Purpose |
|-------|------|---------|
| Runtime | `python:3.12-slim` | Install pinned dependencies from `pyproject.toml`; run as non-root user |

Run under **gunicorn with uvicorn workers** in production (single worker class is fine at MVP scale; tune `--workers` to 2–4 once load justifies it). The same image can run the bot poller with a different entrypoint command, or the bot can live in its own minimal image sharing the core package.

**`docker-compose.yml` services**

| Service | Image | Ports | Volumes | Notes |
|---------|-------|-------|---------|-------|
| `db` | `postgres:16-alpine` | internal 5432 | `pgdata:/var/lib/postgresql/data` | `POSTGRES_PASSWORD` from env; healthcheck on `pg_isready` |
| `backend` | local `Dockerfile.backend` | internal 8000 | `media:/data/media` | depends_on db (healthy); runs migrations on start (`alembic upgrade head`) then serves |
| `bot` | local `Dockerfile.backend` (bot entrypoint) | — | `media` (if needed) | depends_on backend; **replicas must stay 1** |
| `frontend` | local `Dockerfile.frontend` | 80 → host 8080 | — | optional locally; usually the frontend is hosted separately (3.4) |

Compose also defines a dedicated bridge network, restart policies (`unless-stopped`), and healthchecks for `db` and `backend`.

### 3.2 HTTPS Requirement for the Mini App

Telegram **requires** Mini Apps to be served over HTTPS with a valid TLS certificate; plain HTTP URLs are rejected by clients. This applies to the **frontend host only** — bot polling is outbound-only and needs no public endpoint.

| Environment | Solution |
|-------------|----------|
| Local dev with tunnel | `ngrok http 5173` (HTTPS URL provided) |
| VPS / Docker | Caddy (automatic Let's Encrypt) or nginx + certbot |
| Static host | Built-in free TLS (Vercel, Netlify, Cloudflare Pages) |
| Platform (Railway/Render/Fly) | Platform-managed TLS termination |

Register the exact HTTPS URL of the deployed frontend as the Mini App URL in BotFather. If the domain changes, update BotFather — cached clients keep the old URL until refreshed.

### 3.3 Reverse Proxy with TLS

Recommended topology when self-hosting on a VPS:

| Option | TLS | Effort | Recommendation |
|--------|-----|--------|----------------|
| **Caddy** | Automatic (Let's Encrypt), auto-renewing | Low | **Default choice** — simplest correct TLS |
| nginx + certbot | Manual certbot cron | Medium | Use when nginx is already standard |
| Cloudflare Tunnel | Free plan, no open ports | Low | Good for homelab/no-static-IP setups |

The proxy terminates TLS and routes: `/` → frontend (static or container), `/api` → backend, `/media` → backend. Add security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, restrictive `Content-Security-Policy`) and gzip/brotli for static assets.

### 3.4 Hosted Deployment Options

Managed platforms remove server patching and TLS management. All options below support environment-variable secrets and custom domains.

**Frontend (static)**

| Platform | Free tier | Notes |
|----------|-----------|-------|
| Cloudflare Pages | Yes (generous) | Fast global CDN; easy env vars; best latency story |
| Vercel | Yes (hobby) | Zero-config for Vite/React; previews per PR |
| Netlify | Yes | Similar to Vercel; forms/functions if ever needed |

**Backend**

| Platform | Free tier | Notes |
|----------|-----------|-------|
| Render | Yes (spins down after inactivity) | Easiest path: GitHub auto-deploy, managed env |
| Railway | Yes (usage-based credit) | Good Postgres pairing; simple pricing |
| Fly.io | Yes (small allowances) | Run backend + bot close to each other; good latency |
| AWS ECS (Fargate) | No | Only when already in the AWS ecosystem; highest control, highest ops burden |

**PostgreSQL**

| Provider | Free tier | Notes |
|----------|-----------|-------|
| Neon | Yes (serverless, ~0.5 GB) | Scale-to-zero; branching for staging; PITR on paid tiers |
| Supabase | Yes (~500 MB) | Adds auth/storage we don't use; solid dashboard |
| Railway | With usage credit | Convenient if backend is already there |
| AWS RDS (Postgres) | No (750 hrs free for 12 months via AWS free tier, then ~$12–18/mo smallest) | Only for AWS-centric operations |

**Bot hosting**

| Option | When to use |
|--------|-------------|
| Same service as backend (separate process/worker) | **MVP default** — one fewer host to manage |
| Separate container/worker on same host | When bot update volume or polling stability becomes a concern |
| Separate platform entirely | Post-MVP, if bot needs webhooks or independent scaling |

### 3.5 Secret Management

| Option | Cost | When to use |
|--------|------|-------------|
| Platform env vars (Render/Railway/Fly/Vercel) | Free | MVP default — sufficient with strict access control |
| Doppler | Free up to 3 users | When secrets need rotation, audit history, or multi-environment sync |
| AWS Secrets Manager | ~$0.40/secret/month | AWS-centric operations; automatic rotation |
| Docker secrets / `docker compose` env files | Free | Self-hosted compose only; never commit populated files |

Rules: never commit secrets (`.env` is git-ignored); generate `SECRET_KEY` with a CSPRNG (32+ bytes); rotate tokens immediately on suspicion of leak (BotFather revoke, Google AI key regenerate); keep a per-environment secret set (dev/staging/prod must not share keys); grant production secrets access only to the deploying identity.

### 3.6 Media Storage

**MVP — local volume.** Media lives under `MEDIA_STORAGE_ROOT` on a Docker volume (`media:/data/media`), organized by company UUID so tenant data can be exported or purged per company (data-export requirement, see [01-project-vision-and-scope.md](01-project-vision-and-scope.md)). Backups are covered by the volume backup routine (3.7). Serve files through an authenticated backend endpoint (`/media/...`) so URLs never leak to non-members; the frontend proxy routes `/media` accordingly.

**Scale — S3-compatible object storage.** Move to S3, Cloudflare R2, or Wasabi behind the storage interface (ADR-008) when media volume or instance count justifies it. R2 is the cost-first choice (no egress fees). Prefer direct browser-to-provider uploads (presigned URLs) only when media volume makes server proxying a bottleneck.

### 3.7 Backup and Recovery

| Layer | Tool | Frequency | Retention |
|-------|------|-----------|-----------|
| Database logical dump | `pg_dump` (custom format) | Daily | 30 days |
| Database continuous | WAL archiving / managed PITR (Neon, Supabase, RDS) | Continuous | 7–35 days (provider-dependent) |
| Media volume | `rclone`/`rsync` to object storage | Daily | 30 days |
| Secrets/Config | Infrastructure-as-code + secret manager | Per change | Versioned history |

**Recovery objectives (MVP):** RPO 24 hours for database dumps, near-zero if using a managed provider with PITR; RTO 4 hours for a full restore onto a fresh host.

**Runbook:** document restore steps for (1) `pg_restore` from the latest dump, (2) PITR via the managed provider, (3) media re-sync from object storage. **Drill a full restore at least monthly** — an untested backup is not a backup.

### 3.8 Monitoring and Logging

| Concern | MVP Approach | Scale Target |
|---------|--------------|--------------|
| Logs | Structured JSON to stdout; platform or Docker captures and ships | Centralized aggregation (e.g., Grafana Loki) |
| Liveness | `GET /healthz` → 200 when the process is up | Platform health checks point here |
| Readiness | `GET /readyz` → 200 only when DB ping succeeds | Used by deploy tooling to gate traffic |
| Errors | Sentry (free developer tier) for server + client | Same, with alerting rules |
| Uptime | UptimeRobot/StatusCake free tier (50 monitors) | Paid tier or self-hosted when SLA matters |
| Metrics | Platform-native dashboards; `METRICS_ENABLED=true` for Prometheus later | Prometheus + Grafana |
| Alerts | Forward critical Sentry alerts and uptime failures to a Telegram chat via the bot | Same, with escalation |

Log every mutating request with: timestamp (ISO-8601 UTC), level, request id, actor user id, company id (never the other tenants' ids), action, result. Never log secrets, full `initData`, or JWTs. Audit-sensitive actions (role changes, approvals, publishing, suspension) go to the audit log table per [03-user-roles-and-use-cases.md](03-user-roles-and-use-cases.md).

---

## 4. Cost Model

### 4.1 Free Tier Options

| Category | Free Option | Limits to Watch |
|----------|-------------|-----------------|
| Frontend hosting | Cloudflare Pages / Vercel / Netlify | Build minutes, bandwidth |
| Backend hosting | Render / Railway / Fly.io allowances | Spin-down idle, CPU/RAM caps |
| PostgreSQL | Neon / Supabase free tiers | Storage (0.5–1 GB), scale-to-zero latency |
| Domain | — | Domains are never free: budget ~$10–15/year |
| TLS | Let's Encrypt / Caddy / Cloudflare | None meaningful |
| Error tracking | Sentry developer tier | Event volume |
| Uptime monitoring | UptimeRobot free | 5-minute check interval, 50 monitors |
| Secrets | Platform env vars | No rotation/audit (Doppler free covers this) |

### 4.2 Likely Monthly Cost at Small Scale (1–20 companies)

| Scenario | Compute | Database | Domain | AI APIs* | Storage | Total/month |
|----------|----------|----------|--------|----------|---------|-------------|
| Minimum (all free tiers, spun-down compute) | $0 | $0 | ~$1 | $0–5 | $0 | **~$1–6** |
| Comfortable (always-on small VM + managed DB) | $5–10 | $0–19 | ~$1 | $5–20 | $0 | **~$11–50** |
| Growth (paid tiers, headroom) | $15–40 | $19–30 | ~$1 | $20–60 | $5–10 | **~$60–140** |

\* Driven entirely by usage; see the disclaimer below.

### 4.3 Cost-Control Measures

1. **Per-company usage quotas** for AI text (`GEMINI_DAILY_QUOTA_PER_COMPANY`), image generation, and storage — enforced server-side (usage tracking ships in Phase 10, hard limits configurable per company).
2. **Default to the cheapest viable model tier** (`gemini-2.5-flash-lite`) and let companies opt into premium models explicitly.
3. **Server-side rate limits** (`RATE_LIMIT_PER_MINUTE`) per user and per company to cap burst costs.
4. **Provider selection discipline**: compare Gemini vs. alternatives at each pricing change; the provider interface (ADR-006/007) makes switching cheap.
5. **Autoscaling-to-zero compute** where the platform allows (Render/Neon scale-to-zero) instead of always-on VMs.
6. **Billing alerts** at $10 / $25 / $50 on every paid provider; weekly cost review during MVP.
7. **Monthly cost cap policy**: define a hard monthly budget for AI APIs per company and per platform; when exceeded, features degrade gracefully (queue-style "try later" responses) rather than failing.

### 4.4 Cost Disclaimer

> **AI API calls, image generation, hosting, and storage are metered services and are NOT guaranteed free.** Free tiers exist but carry usage limits, idle spin-down, reduced support, or revocable terms. The estimates above are planning figures, not commitments by any provider. Always: enable billing alerts, set quotas before launch, and re-run the cost model at each growth milestone. The business must treat AI and image-generation cost of goods as a real, variable line item from day one.

---

## 5. Required vs Optional Services

| Service | MVP | Post-MVP | Justification |
|---------|-----|----------|---------------|
| PostgreSQL | **Required** | Required | Relational multi-tenant store; see ADR-002 |
| FastAPI backend | **Required** | Required | API + auth + business logic |
| Frontend host (HTTPS) | **Required** | Required | Telegram Mini App requirement |
| Telegram bot token | **Required** | Required | Mini App entry point + publishing |
| Gemini API key | **Required** | Required | Core AI value proposition |
| Image generation provider | Optional (interface ships disabled) | Recommended | Pluggable; see ADR-007 |
| Redis | Optional | Recommended (with workers) | Queue, rate-limit counters, cache; see ADR-013 |
| Object storage (S3/R2) | Optional | Recommended (with scale) | Replaces local volume; see ADR-008 |
| Sentry | Optional | Recommended | Free tier covers MVP |
| Uptime monitor | Optional | Recommended | Free tier covers MVP |
| Doppler / secret manager | Optional | Recommended | Rotation and audit at team scale |
| CDN | Optional | Recommended | Static asset latency at global scale |

---

## 6. Operational Runbooks

| Procedure | Frequency / Trigger | Summary |
|-----------|---------------------|---------|
| Deploy | Per release | Push to main → CI green → platform auto-deploy (or `docker compose up -d --build`); migrations run on backend start |
| Restart | On failure | Platform: restart service; self-hosted: `docker compose restart <svc>`; never run two bot pollers |
| Rotate `SECRET_KEY`/JWT secret | On suspicion of leak | Generate new value, deploy, all users re-authenticate via Mini App (zero-friction, ADR-004) |
| Rotate bot token | On suspicion of leak | Revoke in BotFather, issue new, update env, restart bot |
| Rotate API keys | Quarterly or on suspicion | Regenerate in provider console, update env, verify |
| Restore DB | After incident | Follow 3.7 runbook; verify with row counts + login test |
| Backup drill | Monthly | Full restore into a throwaway environment; time it against RTO |
| Cost review | Weekly (MVP), monthly (growth) | Compare actuals to 4.2; check quota headroom per company |

---

## 7. Scaling Path

Add complexity only when a measured trigger fires — never preemptively (ADR-001, ADR-013).

| Trigger (measured) | First Move | Follow-ups |
|--------------------|------------|------------|
| Request latency p95 > 1s or backend CPU > 70% sustained | Move to 2 gunicorn workers; add DB read replica for reports | Horizontal backend replicas behind the proxy |
| Media volume > ~1–2 GB or multi-instance media access | Adopt S3-compatible storage behind the storage interface (ADR-008) | Presigned uploads; CDN in front of media |
| Need for scheduled publishing / async jobs | Add Redis + lightweight worker (`arq` or RQ) in same compose | Job dashboard, retry policies, concurrency limits |
| Bot update volume high or global latency matters | Migrate polling → webhooks (needs HTTPS + single consumer, ADR-009) | Separate bot service; update-deduplication |
| Rate-limit or session state needed across instances | Adopt Redis for shared counters/sessions | Revisit ADR-013 if queues land first |
| DB write contention or size > 10 GB | Partitioning strategy; move analytics to a read replica | Evaluate managed Aurora/PlanetScale-class providers |
| Multi-region demand | Regional frontend + read replicas; keep single write region | Full multi-region design review |

**Guiding order of adoption:** Redis (when jobs arrive) → object storage (when media grows) → webhooks (when bot scale demands) → workers/queues (with scheduled publishing) → read replicas (when DB load justifies).

---

## 8. Related Documents

- [04-system-architecture.md](04-system-architecture.md) — target architecture and data flows
- [14-implementation-roadmap.md](14-implementation-roadmap.md) — Phase 0 scaffolding, Phase 10 launch prep
- [15-architecture-decisions.md](15-architecture-decisions.md) — ADR-002 (PostgreSQL), ADR-008 (storage), ADR-009 (polling), ADR-010 (frontend stack)
- [12-testing-strategy.md](12-testing-strategy.md) — what CI must gate before each deploy
