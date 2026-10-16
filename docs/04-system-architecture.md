# System Architecture

This document describes the target system architecture for SocialPilot AI: a multi-tenant SaaS delivered as a Telegram Mini App. It covers the system context, container/component structure, request lifecycle, module layout, data flows, caching, and background job strategy.

Related documents: [01-project-vision-and-scope.md](01-project-vision-and-scope.md), [02-software-requirements.md](02-software-requirements.md), [03-user-roles-and-use-cases.md](03-user-roles-and-use-cases.md), [05-database-design.md](05-database-design.md), [06-api-specification.md](06-api-specification.md).

---

## 1. System Context

SocialPilot AI is a **modular monolith**: a single FastAPI application owning all business logic, a single PostgreSQL database, and a React/TypeScript Telegram Mini App frontend. External dependencies are the Telegram Bot/Mini App platform, the Gemini text API, and a pluggable image generation provider.

```mermaid
graph TB
    subgraph Clients
        MA[Telegram Mini App<br/>React / TypeScript]
    end

    subgraph SocialPilot["SocialPilot AI (Modular Monolith)"]
        API[FastAPI Application<br/>backend/app]
        DB[(PostgreSQL 15+)]
        FS[(Local Filesystem<br/>media storage)]
    end

    subgraph External["External Services"]
        TG[Telegram Platform<br/>Bot API + Mini App initData]
        GEMINI[Google Gemini API<br/>text generation]
        IMG[Image Generation Provider<br/>pluggable interface]
    end

    subgraph Operators
        PO[Platform Owner<br/>Mini App admin interface]
    end

    MA -->|"HTTPS / JSON<br/>JWT session"| API
    PO -->|"HTTPS / JSON<br/>JWT session"| API
    API --> DB
    API --> FS
    API -->|"validate initData<br/>send messages"| TG
    API -->|"generate text"| GEMINI
    API -->|"generate images"| IMG
```

### Context Notes

- The **only client** is the Telegram Mini App (mobile and desktop). There is no standalone web frontend in MVP.
- The **platform owner** uses the same Mini App with an additional admin interface gated by `platform_*` permissions.
- All external calls (Telegram, Gemini, image provider) are made **server-side**; API keys never reach the client.
- The filesystem is a mounted volume in production; in local development it is a directory on the host.

---

## 2. Container / Component Architecture

```mermaid
graph TB
    subgraph Edge["Edge / Transport"]
        HTTPS[HTTPS Termination<br/>reverse proxy in prod]
    end

    subgraph App["FastAPI Application (single process, modular monolith)"]
        direction TB
        ROUTER[API Routers<br/>api/v1/endpoints/*]
        CORE[Core Layer<br/>core/ security, deps, config, rbac]
        SVC[Service Layer<br/>services/ business logic]
        REPO[Repository Layer<br/>repositories/ data access]
        INT[Integration Layer<br/>integrations/ telegram, ai, storage]
        WORK[Workers<br/>workers/ deferred]
        DBH[DB Session<br/>db/ engine + Alembic]
        UTIL[Utils<br/>utils/ helpers]
    end

    subgraph Data["Data Stores"]
        PG[(PostgreSQL)]
        DISK[(Filesystem Volume)]
    end

    subgraph Providers["AI Providers"]
        TXT[TextProvider interface<br/>GeminiTextProvider]
        IMGP[ImageProvider interface<br/>configurable]
    end

    subgraph Telegram["Telegram"]
        BOT[Bot Polling<br/>bot.py long-poll]
    end

    HTTPS --> ROUTER
    ROUTER --> CORE
    CORE --> SVC
    SVC --> REPO
    SVC --> INT
    REPO --> DBH
    DBH --> PG
    INT --> DISK
    INT --> TXT
    INT --> IMGP
    BOT --> CORE
```

### Component Responsibilities

| Component | Layer | Responsibility |
|-----------|-------|----------------|
| `api/v1/endpoints/*` | Transport | HTTP routing, request validation (Pydantic), response serialization, permission dependency injection |
| `core/` | Cross-cutting | Settings, DB session management, JWT auth, RBAC permission checks, exception handlers, middleware |
| `services/` | Business logic | Use-case orchestration, transaction boundaries, domain rules (approval workflow, publishing policy) |
| `repositories/` | Data access | SQLAlchemy queries, tenant-scoped filtering, no business rules |
| `integrations/telegram` | External | initData validation, Bot API client (send message, media group, getChatAdministrators), polling loop |
| `integrations/ai` | External | `TextProvider` / `ImageProvider` interfaces, Gemini implementation, prompt building, rate-limit accounting |
| `integrations/storage` | External | Local filesystem storage client (put, get, delete, URL signing); S3-compatible interface for later |
| `workers/` | Background | Placeholder module; scheduled publishing and export jobs land here post-MVP |
| `db/` | Infrastructure | Engine, session factory, Alembic migrations, base model with `company_id` mixin |
| `utils/` | Helpers | ID generation, normalization, datetime, pagination, hashing |

---

## 3. Request Lifecycle

### 3.1 Authenticated API Request

```mermaid
sequenceDiagram
    participant C as Mini App Client
    participant R as API Router
    participant A as Auth Dependency (JWT)
    participant P as RBAC Dependency
    participant S as Service
    participant Rep as Repository
    participant DB as PostgreSQL

    C->>R: HTTP /api/v1/... + Authorization: Bearer <JWT>
    R->>A: Validate JWT, load user
    A->>DB: Fetch user + memberships
    DB-->>A: user, memberships[]
    A->>P: Resolve company_id from path/body + membership
    P->>P: Check required permission
    alt Permission denied
        P-->>C: 403 Forbidden
    else No membership in company
        P-->>C: 404 Not Found (avoid enumeration)
    else Authorized
        P->>S: Call service(user, company_id, payload)
        S->>Rep: Tenant-scoped query (WHERE company_id = ...)
        Rep->>DB: SELECT ... WHERE company_id = :cid
        DB-->>Rep: rows
        Rep-->>S: ORM entities
        S-->>R: Domain result
        R-->>C: 200 OK + JSON
    end
```

### 3.2 Key Lifecycle Rules

1. **Authentication** — JWT is issued only after server-side Telegram `initData` HMAC validation. Token lifetime: 12 hours inactivity sliding window.
2. **Tenant resolution** — `company_id` is never trusted from the request body alone. It is resolved from the authenticated user's memberships and the resource being accessed.
3. **Authorization** — Every endpoint declares a required permission. The RBAC dependency loads the user's role(s) for the resolved company and checks the permission string.
4. **Tenant scoping** — All repository queries include `WHERE company_id = :company_id` as a mandatory predicate. This is the primary isolation mechanism; PostgreSQL RLS is defense-in-depth (see [05-database-design.md](05-database-design.md)).
5. **Audit** — Sensitive actions emit `audit_logs` entries within the same transaction as the action.

### 3.3 AI Generation Request

```mermaid
sequenceDiagram
    participant C as Client
    participant S as AIService
    participant RL as Rate Limiter
    participant PR as Provider (Gemini)
    participant U as UsageService
    participant DB as PostgreSQL

    C->>S: generate_text(company_id, prompt_params)
    S->>RL: check(user_id, company_id)
    alt Rate limited
        RL-->>C: 429 Too Many Requests
    else
        S->>S: Build prompt from brand profile + params
        S->>PR: generate(prompt)
        PR-->>S: generated text
        S->>U: record_usage(company_id, user_id, "text", tokens)
        U->>DB: INSERT usage_records
        S-->>C: text result
    end
```

---

## 4. Backend Module Structure

Target tree for the FastAPI application:

```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory, router registration, exception handlers
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (env-driven)
│   │   ├── security.py          # JWT encode/decode, initData HMAC validation
│   │   ├── deps.py              # FastAPI dependencies: get_db, get_current_user, get_current_membership
│   │   ├── rbac.py              # Permission enum, require_permission dependency
│   │   ├── exceptions.py        # Domain exceptions → HTTP status mapping
│   │   └── middleware.py        # Request ID, CORS, audit context
│   ├── api/
│   │   └── v1/
│   │       ├── router.py        # Aggregates all endpoint routers
│   │       └── endpoints/
│   │           ├── auth.py          # POST /auth/telegram, POST /auth/refresh
│   │           ├── companies.py     # Company CRUD, registration, suspension
│   │           ├── members.py       # Invitations, membership management
│   │           ├── channels.py      # Channel connect/verify/disconnect
│   │           ├── posts.py         # Draft CRUD, revisions, submit
│   │           ├── media.py         # Upload, list, delete media assets
│   │           ├── ai.py            # Text/image generation
│   │           ├── approvals.py     # Approve/reject/request changes
│   │           ├── publishing.py    # Publish approved post
│   │           ├── analytics.py     # History, calendar, usage
│   │           ├── notifications.py # List/mark-read notifications
│   │           └── owner_admin.py   # Platform owner: companies, providers, metrics
│   ├── models/                  # SQLAlchemy 2.0 ORM models (one file per entity)
│   ├── schemas/                 # Pydantic request/response schemas (one file per domain)
│   ├── repositories/            # Data access layer (one file per aggregate)
│   ├── services/                # Business logic (one file per domain)
│   │   ├── auth_service.py
│   │   ├── company_service.py
│   │   ├── member_service.py
│   │   ├── channel_service.py
│   │   ├── post_service.py
│   │   ├── media_service.py
│   │   ├── ai_service.py
│   │   ├── approval_service.py
│   │   ├── publishing_service.py
│   │   ├── analytics_service.py
│   │   └── notification_service.py
│   ├── integrations/
│   │   ├── telegram/
│   │   │   ├── init_data.py      # HMAC validation, parsing
│   │   │   ├── bot_client.py     # Bot API HTTP client
│   │   │   └── polling.py        # Long-polling loop (MVP)
│   │   ├── ai/
│   │   │   ├── base.py           # TextProvider / ImageProvider ABCs
│   │   │   ├── gemini_text.py    # Gemini implementation
│   │   │   └── image.py          # Image provider implementations
│   │   └── storage/
│   │       ├── base.py           # StorageProvider ABC
│   │       └── local.py          # Local filesystem implementation
│   ├── workers/
│   │   └── __init__.py           # Placeholder for future job workers
│   ├── db/
│   │   ├── base.py               # Declarative base, company_id mixin
│   │   ├── session.py            # Engine, session factory
│   │   └── migrations/           # Alembic
│   └── utils/
│       ├── ids.py                # UUID generation
│       ├── pagination.py         # Cursor/page helpers
│       ├── normalization.py      # Company name normalization
│       └── datetime.py           # Timezone-aware helpers
```

### Module Dependency Rule

```
endpoints → services → repositories → models
                     ↓
              integrations (telegram, ai, storage)
                     ↓
                   core (config, security, rbac)
```

Dependencies point **inward** only. Repositories never call services. Integrations never import endpoints. This enforces the modular monolith boundary: each module is a potential future service extraction point.

---

## 5. Frontend Module Structure

Target tree for the React/TypeScript Mini App:

```
frontend/
├── src/
│   ├── app/
│   │   ├── App.tsx               # Root component, router setup
│   │   ├── routes.tsx            # Route definitions + permission guards
│   │   └── providers.tsx         # Auth, Company, Theme providers
│   ├── components/               # Shared, reusable UI components
│   │   ├── ui/                   # Button, Input, Modal, Toast, Spinner
│   │   ├── layout/               # AppShell, Sidebar, Header
│   │   └── feedback/             # ErrorBoundary, EmptyState, Skeleton
│   ├── features/                 # Feature modules (one per domain)
│   │   ├── auth/                 # TelegramLogin, PendingApproval
│   │   ├── companies/            # CompanyList, CompanySettings, BrandProfile
│   │   ├── members/              # MemberList, InviteForm, RoleEditor
│   │   ├── channels/             # ChannelList, ConnectChannel, VerifyCode
│   │   ├── posts/                # PostEditor, PostList, PostPreview, RevisionHistory
│   │   ├── media/                # MediaLibrary, UploadZone, ImageGrid
│   │   ├── ai/                   # TextGenerator, ImageGenerator, PromptForm
│   │   ├── approvals/            # ApprovalQueue, ReviewPanel
│   │   ├── publishing/           # PublishDialog, PublishHistory
│   │   ├── analytics/            # HistoryView, CalendarView, UsageDashboard
│   │   ├── notifications/        # NotificationList, NotificationBell
│   │   └── owner-admin/          # CompanyQueue, ProviderSettings, PlatformMetrics
│   ├── hooks/                    # Shared React hooks
│   │   ├── useAuth.ts
│   │   ├── useCompany.ts
│   │   ├── usePermission.ts
│   │   └── useApi.ts             # Fetch wrapper with error handling
│   ├── lib/                      # Third-party clients and config
│   │   ├── api.ts                # Axios/fetch instance with interceptors
│   │   ├── telegram.ts           # Telegram WebApp SDK wrapper
│   │   └── constants.ts
│   ├── services/                 # API call functions (one per endpoint group)
│   │   ├── auth.service.ts
│   │   ├── company.service.ts
│   │   ├── post.service.ts
│   │   └── ...
│   ├── types/                    # TypeScript interfaces mirroring API schemas
│   │   ├── api.ts                # Generic ApiResponse, PaginatedResponse
│   │   ├── models.ts             # User, Company, Post, etc.
│   │   └── enums.ts              # PostStatus, Role, Permission
│   ├── utils/                    # Pure helper functions
│   │   ├── format.ts             # Date, number formatting
│   │   ├── validation.ts         # Client-side form validation
│   │   └── file.ts               # File type/size checks
│   └── styles/
│       ├── theme.css             # CSS custom properties, Telegram theme vars
│       └── global.css             # Reset, typography, utilities
```

### Frontend Conventions

- **Token storage**: JWT is held in React state / memory only (per FR-1.7). On Mini App relaunch, `initData` is re-sent and a new token is issued.
- **Permission gating**: `usePermission(permission)` hook drives UI visibility. Server-side RBAC remains the enforcement layer; UI gating is UX-only.
- **Telegram theming**: Use `window.Telegram.WebApp.themeParams` and `colorScheme` to match the user's Telegram client theme.
- **Optimistic UI**: Post status transitions (submit, approve, publish) use optimistic updates with rollback on error.

---

## 6. Data Flows for Key Operations

### 6.1 Company Registration and Approval

```mermaid
sequenceDiagram
    participant U as User (Mini App)
    participant API as FastAPI
    participant DB as PostgreSQL
    participant PO as Platform Owner

    U->>API: POST /auth/telegram (initData)
    API->>DB: upsert user
    API-->>U: JWT
    U->>API: POST /companies (name, industry, country)
    API->>DB: INSERT company (status=pending) + membership (owner)
    API-->>U: 201 company
    Note over PO: Owner opens admin queue
    PO->>API: GET /owner-admin/companies?status=pending
    PO->>API: POST /owner-admin/companies/{id}/approve
    API->>DB: UPDATE company SET status=active + audit_log
    API->>DB: INSERT notification (owner)
    API-->>PO: 200
```

### 6.2 AI Text Generation to Draft

```mermaid
sequenceDiagram
    participant C as Content Creator
    participant API as FastAPI
    participant S as AIService
    participant G as Gemini
    participant DB as PostgreSQL

    C->>API: POST /ai/text (topic, goal, tone, ...)
    API->>S: generate(company_id, user_id, params)
    S->>DB: SELECT brand_profile WHERE company_id
    S->>S: Build prompt (brand + params + safety instructions)
    S->>G: generateContent(prompt)
    G-->>S: text
    S->>DB: INSERT usage_records
    S-->>API: text
    API-->>C: 200 { text }
    C->>API: POST /posts (caption=text, status=draft)
    API->>DB: INSERT post + post_revision
    API-->>C: 201 post
```

### 6.3 Approval Workflow

```mermaid
stateDiagram-v2
    [*] --> draft: Content Creator saves
    draft --> in_review: Content Creator submits
    in_review --> approved: Company Admin approves
    in_review --> changes_requested: Company Admin requests changes (reason)
    in_review --> rejected: Company Admin rejects (reason)
    changes_requested --> in_review: Content Creator edits + resubmits
    approved --> publishing: Company Admin initiates
    publishing --> published: Telegram success
    publishing --> approved: Telegram failure (retryable)
    rejected --> [*]
    draft --> cancelled: Content Creator cancels
```

### 6.4 Publishing

```mermaid
sequenceDiagram
    participant P as Company Admin
    participant API as FastAPI
    participant S as PublishingService
    participant T as Telegram Bot API
    participant DB as PostgreSQL

    P->>API: POST /publishing/posts/{id}/publish (channel_id, idempotency_key)
    API->>S: publish(company_id, post_id, channel_id, key)
    S->>DB: SELECT post WHERE company_id AND status=approved
    S->>DB: SELECT channel WHERE company_id
    S->>S: Check approval policy + idempotency key
    S->>DB: UPDATE post SET status=publishing
    S->>T: sendMediaGroup / sendMessage
    alt Success
        T-->>S: message_ids
        S->>DB: INSERT publication_results + UPDATE post SET status=published
        S-->>P: 200 { message_ids }
    else Failure
        T-->>S: error
        S->>DB: INSERT publication_results (error) + UPDATE post SET status=approved
        S-->>P: 422 { error }
    end
```

---

## 7. Caching Strategy

### MVP: No Application-Level Cache

The MVP operates without a caching layer. Rationale:

- **Low concurrency**: Single-instance deployment; PostgreSQL query performance is sufficient for the expected load.
- **Multi-tenant complexity**: Cache keys must be tenant-scoped, invalidation must be tenant-aware. The complexity cost exceeds the benefit at MVP scale.
- **AI responses are not cacheable**: Each generation is unique (brand context + user params). Caching would only apply to repeated identical prompts, which is an edge case.

### What Is Cached Implicitly

| Data | Mechanism | TTL |
|------|-----------|-----|
| User session / memberships | JWT claims (stateless) | Token lifetime (12h) |
| Telegram bot token | In-memory singleton | Process lifetime |
| Brand profile | None (DB read per generation) | — |
| Static assets (frontend) | HTTP cache headers (CDN in prod) | 1 year (hashed assets) |

### Post-MVP: Redis

When justified by load, introduce Redis for:

1. **Rate limiting counters** — sliding window per user/company for AI generation.
2. **Session revocation** — denylist for compromised tokens.
3. **Provider response cache** — optional, only for identical prompt hashes (opt-in per company).
4. **Usage counters** — aggregated daily counts to reduce `usage_records` read load.

Cache invalidation strategy: **write-through with explicit invalidation** on company/brand/member changes. Tenant-scoped key pattern: `cache:{company_id}:{resource}:{id}`.

---

## 8. Background Jobs

### MVP: No Background Workers

The MVP is fully synchronous. All operations complete within the HTTP request/response cycle:

- **Publishing** — synchronous Telegram API call with a 30s timeout. The post status transitions to `publishing` and the client awaits the result.
- **Company deletion export** — synchronous generation of a JSON/CSV archive (small data volumes in MVP). The 24h retention window is enforced by a status flag, not a background job.
- **Bot polling** — a lightweight long-poll loop in a separate asyncio task within the same process. It handles channel verification callbacks only.

### Why No Workers in MVP

| Concern | MVP Approach | Risk |
|---------|--------------|------|
| Publishing latency | Synchronous call, p95 < 5s | Telegram API outage blocks the request; acceptable for MVP |
| Export generation | Synchronous, small data | Large companies may hit timeout; mitigate with pagination |
| Scheduled publishing | Not supported (FR-15 is FUTURE) | — |
| Email notifications | Not supported (Telegram notifications only) | — |

### Post-MVP: Worker Architecture

When scheduled publishing (FR-15) and other async work arrive:

```mermaid
graph LR
    API[FastAPI] -->|"enqueue job"| Q[Job Queue<br/>Redis + RQ/Celery]
    Q --> W[Worker Process]
    W --> TG[Telegram]
    W --> DB[(PostgreSQL)]
    W --> NOTIF[Notifications]
```

- **Queue**: Redis-backed (RQ or Celery). Separate queue per job type (publishing, export, notifications).
- **Worker**: Separate process, same codebase, imports `workers/` module.
- **Retry policy**: Exponential backoff, max 3 attempts for Telegram API calls. Dead-letter queue for manual inspection.
- **Idempotency**: Jobs carry idempotency keys; workers check before executing.

---

## 9. Deployment Topology (MVP)

```mermaid
graph TB
    subgraph Host["Single Host / Container"]
        NGINX[Reverse Proxy<br/>TLS termination]
        UVICORN[Uvicorn + FastAPI<br/>single process]
        BOT[Bot Polling Task<br/>asyncio]
        PG[(PostgreSQL)]
        VOL[Media Volume]
    end

    NGINX --> UVICORN
    UVICORN --> PG
    UVICORN --> VOL
    BOT --> PG
```

- **Single process** runs both the ASGI server and the bot polling loop (asyncio tasks).
- **PostgreSQL** runs as a sidecar container or managed service.
- **Media volume** is a bind mount or Docker volume.
- **Horizontal scaling** (future): stateless API replicas behind a load balancer; bot polling must be singleton (leader election or separate worker).

---

## 10. Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| **Logging** | Structured JSON logs (structlog). Request ID propagated via middleware. No PII in logs. |
| **Error handling** | Domain exceptions in `core/exceptions.py` mapped to HTTP status codes. Consistent error envelope (see [06-api-specification.md](06-api-specification.md)). |
| **Configuration** | Pydantic Settings, env vars + `.env` file. Secrets via environment or secrets manager. No secrets in code. |
| **Database migrations** | Alembic, auto-generated + reviewed. Migrations run on deploy. |
| **Testing** | pytest with testcontainers for PostgreSQL. Integration tests for tenant isolation. See [12-testing-strategy.md](12-testing-strategy.md). |
| **Observability** | Health endpoint `/health`. Metrics endpoint (Prometheus) post-MVP. |
