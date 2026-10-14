# 15 — Architecture Decisions

This document contains the Architecture Decision Records (ADRs) for SocialPilot AI. Each ADR captures one significant decision in standard format — **Status, Context, Decision, Alternatives Considered, Consequences, When to Revisit** — so future contributors understand not just *what* was decided but *why*, and under what conditions the decision should be revisited.

**Process:** decisions are proposed when a significant architectural choice first arises, reviewed against the cost-conscious MVP principles in [01-project-vision-and-scope.md](01-project-vision-and-scope.md), and marked **Accepted** once implemented or explicitly deferred. Superseded decisions are never deleted — they are marked `Superseded by ADR-XXX` with the rationale preserved.

## ADR Summary

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-001](#adr-001-modular-monolith-over-microservices) | Modular monolith over microservices | Accepted | 2026-10 |
| [ADR-002](#adr-002-postgresql-over-sqlitemysql) | PostgreSQL over SQLite/MySQL | Accepted | 2026-10 |
| [ADR-003](#adr-003-sqlalchemy-20-with-alembic) | SQLAlchemy 2.0 with Alembic | Accepted | 2026-10 |
| [ADR-004](#adr-004-jwt-sessions-from-telegram-initdata-not-telegram-login-widget) | JWT sessions from Telegram initData (not Telegram Login Widget) | Accepted | 2026-10 |
| [ADR-005](#adr-005-application-layer-tenant-isolation-optional-rls) | Application-layer tenant isolation (+ optional RLS) | Accepted | 2026-10 |
| [ADR-006](#adr-006-provider-interface-for-ai-gemini-default-pluggable) | Provider interface for AI (Gemini default, pluggable) | Accepted | 2026-10 |
| [ADR-007](#adr-007-provider-interface-for-image-generation-no-hardcoded-provider) | Provider interface for image generation (no hardcoded provider) | Accepted | 2026-10 |
| [ADR-008](#adr-008-local-filesystem-storage-for-mvp-object-storage-later) | Local filesystem storage for MVP (object storage later) | Accepted | 2026-10 |
| [ADR-009](#adr-009-bot-polling-for-mvp-webhooks-later) | Bot polling for MVP (webhooks later) | Accepted | 2026-10 |
| [ADR-010](#adr-010-react-with-vite-over-nextjs-mini-app-constraint) | React with Vite over Next.js (Mini App constraint) | Accepted | 2026-10 |
| [ADR-011](#adr-011-uuid-for-all-public-facing-ids) | UUIDs for all public-facing IDs | Accepted | 2026-10 |
| [ADR-012](#adr-012-pydantic-v2-for-requestresponse-validation) | Pydantic v2 for request/response validation | Accepted | 2026-10 |
| [ADR-013](#adr-013-immediate-publishing-only-no-job-queue-for-mvp) | Immediate publishing only (no job queue for MVP) | Accepted | 2026-10 |
| [ADR-014](#adr-014-manual-platform-owner-approval-no-self-serve-subscriptions) | Manual platform-owner approval (no self-serve subscriptions) | Accepted | 2026-10 |
| [ADR-015](#adr-015-role-based-access-control-with-explicit-permissions) | Role-based access control with explicit permissions | Accepted | 2026-10 |

---

## ADR-001: Modular Monolith over Microservices

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

SocialPilot AI is a multi-tenant SaaS built by one developer with a hard cost budget. The domain (companies, memberships, posts, media, approvals, publishing) is richly interconnected — nearly every feature touches auth, tenant context, and the posts table. Microservices would give independent deployability and scaling, but impose distributed-systems costs: inter-service networking, distributed tracing, per-service hosting and secret management, and eventual-consistency reasoning in exactly the workflows (approval → publish) that must be transactional.

### Decision

Build a **single deployable FastAPI application** organized as modules per domain (`auth`, `companies`, `posts`, `media`, `approvals`, `publishing`, `admin`). The bot poller is a separate *process* (not a service) launched from the same codebase or a thin package sharing the core module. Service boundaries follow domain lines so a future split is a refactor, not a rewrite.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Microservices (one per domain) | Ops burden (N deploys, N log pipelines, service mesh) exceeds the value at MVP scale; cross-service transactions in the approval→publish path add real risk |
| Serverless functions per endpoint | Cold starts hurt the <3 s Mini App cold-start target; vendor lock-in; hard to run the transactional workflows locally |
| Multi-repo application suite | Synchronization overhead for one developer; shared types and migrations become a coordination problem |

### Consequences

- **Positive:** one deploy unit; simple local development; ACID transactions within one database; trivial structured logging; cheapest hosting story (fits [13-deployment-and-operations.md](13-deployment-and-operations.md)).
- **Negative:** no independent scaling per domain; a backend defect can take down all domains (mitigated by healthchecks and fast restarts); shared database is a single failure domain.
- **Neutral:** module boundaries must be enforced by code review; nothing structural prevents accidental cross-module coupling.

### When to Revisit

When a specific domain needs independent scale or independent team ownership (e.g., bot/webhook ingestion outgrowing the API), or when a second developer makes parallel deploys contended. The split point will be a module boundary, so this is a mechanical extraction if it happens.

---

## ADR-002: PostgreSQL over SQLite/MySQL

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

The data is relational and tenant-heavy: users, companies, memberships, posts, revisions, media assets, publications, audit logs. The current prototype uses SQLite, which is fine for one admin but wrong for concurrent multi-tenant workloads: weak concurrent-write support, no row-level security option, and a different feature surface than any production database the team would adopt later. MySQL is a viable alternative but offers no compelling advantage for this workload and weaker JSON/JSONB support for flexible per-company settings.

### Decision

Use **PostgreSQL 15+** as the single database system, locally (Phase 1) and in production, hosted on Neon/Supabase/Railway or containerized per the deployment doc. The `postgresql+psycopg` driver URL scheme is the default; `psycopg2` URLs are accepted only as a migration fallback.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| SQLite | Single-writer concurrency model breaks under concurrent Mini App users + bot polling + background work; no RLS option for ADR-005; prototype-only |
| MySQL/MariaDB | Works, but weaker JSONB for flexible company settings, weaker full-text and range types, and no advantage the project needs |
| CockroachDB/YugabyteDB (distributed SQL) | Meaningless at MVP scale; operational and cost overhead with zero present benefit |
| DynamoDB/NoSQL | Relational integrity across tenants (memberships, revisions, approvals) is the core of the product; a document model would invite integrity bugs |

### Consequences

- **Positive:** production-grade concurrency; JSONB for evolving per-company settings; optional Postgres RLS as defense-in-depth for tenant isolation (ADR-005); mature tooling (`pg_dump`, PITR, hosted serverless options).
- **Negative:** requires a running database service (the one mandatory infrastructure component, per deployment doc §5); slightly heavier than SQLite for local dev.
- **Neutral:** the hosted Postgres decision (Neon vs. Supabase vs. RDS) is orthogonal and revisited at deployment time based on price.

### When to Revisit

Only under extreme write-scale or multi-region write requirements, which are post-scale concerns. If self-hosting Postgres in Docker, revisit when operational burden exceeds the team's capacity — that is a hosting change, not an engine change.

---

## ADR-003: SQLAlchemy 2.0 with Alembic

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

The backend needs an ORM with typed mappings and a migration tool that enforces discipline from day one (Phase 0–1). The team's Python ecosystem knowledge centers on SQLAlchemy, and the schema will evolve constantly across eleven roadmap phases. Raw SQL would maximize control but forfeit typing, model-level constraint declaration, and migration autogeneration; lighter ORMs lack the depth this schema needs.

### Decision

Use **SQLAlchemy 2.0** with the 2.0-style typed mapping API (`Mapped[]`, `mapped_column()`) as the single ORM, with **Alembic** for migrations. Pydantic v2 models (ADR-012) handle API schemas; SQLAlchemy models never leak directly to the API layer. Every schema change ships as an Alembic revision; autogenerated diffs are reviewed before commit.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Raw SQL + hand-written migrations | No typing, no constraint reuse, migration drift risk for a solo developer across 11 phases |
| Django ORM | Pulls in Django's framework opinions; async story and ecosystem mismatch with a FastAPI-centered stack |
| Peewee / PonyORM | Smaller ecosystem, weaker typing, migration tooling less mature |
| Prisma / Node-side ORM | Wrong language for a Python backend |
| NoSQL + manual schema | Rejected in ADR-002 |

### Consequences

- **Positive:** typed models reviewed by the type checker; migrations give rollback and multi-environment parity; 2.0 style is the supported future of the library; large talent pool for future hires.
- **Negative:** SQLAlchemy 2.0 style has a learning curve if the team only knows 1.x; Alembic autogenerate needs a disciplined review habit (a bad generated migration is worse than none).
- **Neutral:** migration files are a permanent audit trail of schema evolution — treat them as history, never edit applied revisions.

### When to Revisit

If migration tooling friction appears at scale (e.g., needing online schema changes with zero downtime), evaluate migration tooling (e.g., `pgroll`) while keeping Alembic as the source of truth. The decision would not change unless the 2.0 API itself becomes a demonstrated burden.

---

## ADR-004: JWT Sessions from Telegram initData (not Telegram Login Widget)

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

The Mini App runs inside Telegram's webview, which injects a signed `initData` query string on every launch — instant, frictionless proof of the user's Telegram identity. The Telegram Login Widget is designed for external websites: it redirects the user to `oauth.telegram.org` and back, which is a jarring flow inside a Mini App and adds an external surface. The product requirement is "work inside Telegram with no separate login."

### Decision

Validate `initData` **server-side on every first authentication** (and never trust client-sent user data): recompute `HMAC_SHA256("WebAppData", bot_token)` over the sorted key-value fields, compare in constant time, and enforce an `auth_date` freshness window plus a single-use nonce cache for replay protection. On success, issue an application JWT pair (short-lived access token + longer-lived refresh token, ADR-001 in [13-deployment-and-operations.md](13-deployment-and-operations.md) env tables). Subsequent requests authenticate with the JWT.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Telegram Login Widget | Designed for external web; redirect flow breaks the "native Telegram" UX goal; no advantage inside a Mini App |
| Trust client-sent user ID | Trivially forgeable; cross-tenant impersonation |
| Cookie sessions | Mini App webview cookie behavior is inconsistent; JWT keeps auth stateless and API-first |
| Telegram Stars/payment-auth | Irrelevant to identity; a monetization concern (post-MVP) |

### Consequences

- **Positive:** zero-friction login exactly where the user already is; stateless API auth; token lifetimes configurable per environment; rotation is cheap.
- **Negative:** auth only works inside Telegram (a web admin console would need the Login Widget later — the platform-owner admin UI is inside the Mini App by design); `initData` is replayable within the freshness window, mitigated by the nonce cache; clock skew between client and server can cause spurious failures.
- **Neutral:** validation logic is security-critical and carries 100% tamper-case test coverage (Phase 1 test requirements).

### When to Revisit

If a non-Telegram client is ever required (web console, desktop app), add the Telegram Login Widget as a second auth path behind the same JWT issuance — no change to the session model.

---

## ADR-005: Application-Layer Tenant Isolation (+ optional RLS)

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

Multi-tenant isolation is the product's core security promise: one company's data must never be readable or writable through another company's session. Two enforcement depths exist: application-layer filtering (every query scoped by `company_id` resolved from the authenticated session) and database-layer enforcement (PostgreSQL Row-Level Security policies on each tenant table). RLS is the strongest guarantee but is subtle to author correctly (policy roles, session variables, per-connection setup) and its failure modes are silent; with a solo developer, a single missed policy is a breach.

### Decision

Enforce isolation in the **application layer as the primary control**: a tenant-context dependency resolves the authenticated user's company membership, and the repository layer *structurally* appends the `company_id` filter to every tenant-scoped query — no endpoint can query tenant data without going through it. Every tenant-scoped table carries `company_id`. PostgreSQL RLS is adopted later as defense-in-depth (a policy per table, exercised by the same endpoint test matrix). CI runs a table-driven isolation test over every tenant endpoint (Phase 2 requirements) that proves cross-tenant reads and writes are impossible.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| RLS only (no app-layer scoping) | Silent failure risk per missed policy; hard to test from the API; solo-op cannot audit every policy path |
| Database-per-tenant | Strong isolation but N databases to migrate, back up, and connect; connection pooling explodes; unaffordable at MVP |
| Schema-per-tenant | Same operational multiplication as database-per-tenant, weaker isolation guarantee |
| Shared tables, app-layer only | Accepted as the primary layer, but the risk of a forgotten filter is real — hence the mandatory CI isolation suite and planned RLS hardening |

### Consequences

- **Positive:** isolation is testable at the API layer (the attack surface users actually touch); one database to operate and back up; clear failure modes (missing filter → CI fails).
- **Negative:** no database-enforced guarantee — isolation depends on developer discipline backed by tests; a raw-SQL path that bypasses repositories could leak data (mitigated by code review rules and, later, RLS).
- **Neutral:** RLS, when added, must be validated by re-running the same endpoint matrix as a second, independent check.

### When to Revisit

When a compliance requirement mandates database-enforced isolation, when tenant count or data sensitivity grows, or immediately if any isolation regression is found. The trigger is not time-based but risk-based.

---

## ADR-006: Provider Interface for AI (Gemini default, pluggable)

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

AI text generation is the product's core value, but the provider landscape shifts: model names change, pricing moves, free tiers appear and disappear, and a better or cheaper model may dominate by launch. Hardcoding the Gemini SDK into business logic would make every such change a code change, and would lock the product to one vendor's availability and pricing.

### Decision

Define a **`TextProvider` interface** — `generate(prompt, brand_context, options) -> generation result` — with the Gemini implementation as the default provider. Provider selection is configuration, not code: environment variables for the platform, per-company overrides possible later. The interface standardizes timeouts, empty-response handling, content-safety failures, and cost metering (every call is counted for usage quotas). Tests run against a fake provider; Gemini is exercised by one marked integration smoke test per release.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Hardcode the `google-genai` SDK everywhere | Vendor lock-in; every pricing/model change is a code change; untestable without spending quota |
| LangChain / LlamaIndex abstraction | Heavy dependency for a single-call pattern; abstraction漂移 risk without adding value |
| Multi-provider gateway (Portkey, LiteLLM) | Useful at scale, but another service to pay for and operate; premature at MVP |
| Self-hosted model only | Cost and quality unacceptable for a cost-conscious MVP; local generation stays an interface implementation option |

### Consequences

- **Positive:** provider swap is a configuration change; per-company provider routing becomes possible post-MVP; tests never depend on paid APIs; quota and metering live in one place.
- **Negative:** the interface must accommodate provider quirks (some return stream, some batch, some rate-limit differently); small adapter-maintenance burden; two providers in production means two integrations to keep healthy.
- **Neutral:** Gemini remains the default and only provider for MVP; the interface is proven by at least two implementations (Gemini + the test fake) before any second real provider is added.

### When to Revisit

When a second provider is genuinely needed (price, quality, or availability) — that is the moment to extend the interface with real multi-provider semantics (fallback chains, model routing). If prompt engineering grows into few-shot pipelines or tool use, evaluate a lightweight orchestration layer then.

---

## ADR-007: Provider Interface for Image Generation (no hardcoded provider)

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

Image generation providers differ radically in cost, output style, latency, and terms (Replicate, Fal.ai, OpenAI images, self-hosted Stable Diffusion). Unlike text generation, image generation is *not* required for the MVP value loop — users can upload their own images — so the system must tolerate the feature being entirely disabled without code changes.

### Decision

Define an **`ImageProvider` interface** — `generate(prompt, size, style) -> image result` — with a configurable provider keyed by environment variable. The default configuration ships **`none`** (feature disabled); each provider (Replicate, Fal, OpenAI, local) is an implementation that can be added without touching business logic. Generated images enter the same storage and library as uploads (Phase 6), and every generation consumes the per-company monthly quota. The UI hides generation controls when the provider is `none`.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Hardcode one provider (e.g., Replicate) | Locks cost/quality/terms to one vendor at commit time; a pricing change becomes an emergency |
| No image capability in MVP | Under-sells the product vision; the interface costs little and keeps the door open |
| Self-hosted GPU | Unaffordable for a cost-conscious MVP; remains a future `local` implementation of the interface |

### Consequences

- **Positive:** image generation can be enabled, disabled, or swapped by configuration; the disabled state is a first-class supported mode; quota accounting is uniform with text AI.
- **Negative:** each provider integration is its own small project (auth, polling vs. streaming output, refund/cancel semantics); the interface is exercised by fakes in CI and by a real provider only when enabled.
- **Neutral:** providers have wildly different latency (seconds to minutes); the interface must tolerate synchronous results only — async generation is a post-MVP concern tied to the job queue.

### When to Revisit

When a provider is enabled for the first time (validate the interface against reality), or when generation volume justifies async generation — which arrives together with the job queue (ADR-013).

---

## ADR-008: Local Filesystem Storage for MVP (object storage later)

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

Uploaded and generated media must be stored somewhere the backend can serve it from. S3-compatible object storage is the end state for scale, but for an MVP with a handful of companies it is an unnecessary bill and an unnecessary dependency (bucket policies, egress costs, signed URLs). A Docker volume under `MEDIA_STORAGE_ROOT` is free, trivial, and backed up by the same volume-backup routine as the database.

### Decision

Store media on the **local filesystem** behind a `StorageInterface` (put/get/delete/serve-url). The MVP deployment uses a Docker volume organized by company UUID (`media/<company_id>/<uuid>.<ext>`), served through an authenticated backend endpoint so URLs never leak across tenants. Migrating to S3/Cloudflare R2 means implementing the same interface and changing configuration — no business-logic change.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| S3-compatible from day one | Another paid service with egress costs before any revenue; bucket misconfiguration is a classic data-leak vector; premature |
| Store files in the database (BYTEA) | Bloats the database, complicates backups, and makes serving expensive |
| Third-party image CDN/API | Another account, another bill, another terms-of-service dependency for no MVP need |

### Consequences

- **Positive:** zero storage cost at MVP; no cloud permissions surface; backups ride the existing volume strategy; the interface makes the later swap mechanical.
- **Negative:** media availability is tied to one host (no horizontal scaling of media serving); no built-in CDN; disk capacity must be monitored and alerted (deployment doc §3.8).
- **Neutral:** the storage interface must be exercised with a filesystem-backed fake in tests so the S3 swap is test-verified.

### When to Revisit

When media volume exceeds roughly 1–2 GB, when the backend runs multiple instances, or when a global CDN meaningfully improves load times — see the scaling path in [13-deployment-and-operations.md](13-deployment-and-operations.md) §7. R2 is the designated target (zero egress fees).

---

## ADR-009: Bot Polling for MVP (webhooks later)

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

Telegram bots receive updates either by polling (`getUpdates`, outbound HTTPS only) or webhooks (Telegram calls a public HTTPS URL). Webhooks are more efficient and scalable but require a public HTTPS endpoint, a webhook secret, and exactly-one-consumer discipline. At MVP scale — one bot, modest update volume — polling is sufficient and removes an entire class of infrastructure. Note the Mini App *frontend* still requires HTTPS (a frontend hosting concern); polling does not.

### Decision

Run the bot with **long polling** (`python-telegram-bot` `run_polling`) as a single worker process, deployed alongside the backend (same host or container). Exactly one polling instance is enforced operationally (deployment doc §2.7) since Telegram fans updates out to one consumer. Migration to webhooks is a configuration and endpoint change, not a code rewrite.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Webhooks from day one | Requires public HTTPS + webhook secret + redeploy discipline before the product even has users; premature |
| aiogram instead of python-telegram-bot | Both are excellent; python-telegram-bot v22 is what the prototype validated, reducing unknowns |
| Third-party bot hosting | Unmanaged vendor dependency for a core product surface at MVP |

### Consequences

- **Positive:** no public endpoint for the bot; simplest possible production topology; updates arrive with low latency at MVP scale; zero cost difference.
- **Negative:** polling latency grows with update volume; a single instance caps throughput (fine for MVP); if two instances ever run, updates split nondeterministically — hence the hard one-instance rule.
- **Neural:** polling is outbound-only, so bot uptime does not depend on the frontend host's TLS.

### When to Revisit

When update volume is consistently high (many companies, frequent interactions), when bot work is moved to a dedicated service, or when global latency matters — the scaling path in the deployment doc §7. The trigger is measured latency/instability, not a calendar date.

---

## ADR-010: React with Vite over Next.js (Mini App constraint)

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

The frontend is a Telegram Mini App: a client-rendered SPA inside a webview, with no SEO requirement, no server-side data fetching at runtime (all data comes from the API via initData auth), and a hard cold-start target (<3 s on 4G). Next.js's SSR/SSG strengths are irrelevant inside a webview — the server round trip happens before the user sees anything — and its runtime, hosting, and bundle-weight overheads are pure cost here. Vite + React produces a static bundle served from any CDN with near-instant startup.

### Decision

Build the Mini App with **Vite + React 18 + TypeScript**, client-side routing, and static hosting (Cloudflare Pages/Vercel/Netlify or nginx in the container stack). The backend is API-only; there is no SSR, no server components, no Node runtime in production. This matches the Telegram Mini Apps SDK assumptions (static files + webview).

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Next.js (SSR/SSG) | SSR adds a server round trip before first paint in a webview; heavier runtime and hosting model; features unusable in a Mini App context |
| Svelte/SvelteKit | Excellent cold-start story, but the hiring pool, ecosystem (Telegram SDK examples, component libraries), and team familiarity favor React |
| Create React App | Deprecated; no longer supported |
| htmx / server-rendered HTML | Wrong tool for an app with this much interactive state (editor, queues, drag-reorder) |

### Consequences

- **Positive:** fastest possible cold start (static assets only); cheapest hosting (static files); the entire frontend is one CI build artifact; the Telegram SDK ecosystem is React-first.
- **Negative:** no SSR benefits (irrelevant here — but means a future public marketing site is a separate static project, not this app); client-side routing must handle deep links manually; bundle size must be kept disciplined (code-split routes).
- **Neutral:** Vite's dev server and proxy model make local development trivial (deployment doc §2.6).

### When to Revisit

Essentially never for the Mini App. The only adjacent future decision is a public marketing/docs site, which should be a separate static Astro/Vite project rather than a reason to change the Mini App stack.

---

## ADR-011: UUIDs for all public-facing IDs

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

Public-facing identifiers (in API responses, URLs, logs, media object names, invitation tokens) must not leak information about the system: sequential integer IDs expose record counts, enable enumeration attacks (guess `/posts/101` after `/posts/100`), and make cross-environment joins fragile. The prototype's integer IDs are fine for SQLite but wrong for a multi-tenant SaaS where ID predictability is itself a vulnerability class.

### Decision

Use **UUIDs for every public-facing identifier**: primary keys of tenant-scoped entities (companies, posts, media, invitations, publications) are UUIDs — time-ordered UUIDv7 preferred for index locality, UUIDv4 acceptable — and they appear in API responses, URLs, log lines, and storage object names. Non-public surrogate keys may remain bigint only where they never leave the system (rare; default is UUID everywhere for consistency).

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Sequential integer IDs | Enumeration attacks, exposes scale, leaks growth data to competitors via screenshots |
| NanoID/ULID strings | Fine, but Postgres-native UUID type gives index efficiency and type safety for free; no reason to reinvent |
| Snowflake IDs | Coordinated generation infrastructure is unnecessary complexity at this scale |
| Hashids of integer keys | Obscurity, not security; still leaks sequence and count information |

### Consequences

- **Positive:** non-enumerable by construction; safe to paste into logs and tickets; media object names in storage are collision-resistant and tenant-organized; no coordination needed to generate IDs anywhere in the system.
- **Negative:** 16-byte keys consume more index/storage space than 8-byte bigints (negligible at this scale); UUIDv7 requires a generator that mixes time and randomness correctly (use a vetted library or database default); slightly less human-friendly in support chats (mitigated by short codes for user-facing references where needed).
- **Neutral:** UUIDs in URLs are opaque to users — which is intended.

### When to Revisit

Only if index or storage pressure becomes measurable at large scale (terabytes, billions of rows) — not an MVP or near-term concern. If it ever matters, the change is confined to primary-key types, and the public contract stays UUID-shaped regardless.

---

## ADR-012: Pydantic v2 for request/response validation

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

Every API boundary in a multi-tenant system is a trust boundary: request bodies must be validated for type, shape, and business rules (tenant scoping fields, ID formats, enum values) before touching the database. The FastAPI ecosystem is built on Pydantic, and v2 is a strict improvement in performance and typing over v1.

### Decision

Use **Pydantic v2** as the single validation and serialization layer for all request/response schemas, with strict types (real `UUID` types, not strings; real enums; constrained lengths). SQLAlchemy models (ADR-003) and API schemas never mix. Custom validators encode business rules (e.g., post status values, media limits) at the schema layer, and the OpenAPI contract is generated from these schemas — so the API documentation cannot drift from enforcement.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Pydantic v1 | Deprecated line; slower; weaker typing; the ecosystem has moved to v2 |
| Marshmallow / Django validators | Second validation paradigm to learn; not the FastAPI native path |
| Manual `if` checks in handlers | Validation logic would scatter across endpoints; OpenAPI would lie; untestable as a layer |
| msgspec | Fast, but a second mental model and weaker ecosystem integration with FastAPI |

### Consequences

- **Positive:** validation is centralized, typed, and documented (OpenAPI generated from the same models that enforce); v2's Rust core is meaningfully faster; schemas are the contract for frontend type generation.
- **Negative:** strict types can reject edge inputs that v1 would have coerced (behavior to handle deliberately, not accidentally); v1→v2 migration patterns must be learned once; custom validators add code that must itself be tested.
- **Neutral:** the schema layer becomes the API's source of truth — schema review is code review.

### When to Revisit

Rarely. Only a fundamental ecosystem shift (e.g., FastAPI moving off Pydantic) would reopen this. Adopt new Pydantic minor versions promptly for performance and security fixes.

---

## ADR-013: Immediate Publishing Only (no job queue for MVP)

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

Publishing a post to Telegram is a network call that can take seconds and can fail transiently. The robust pattern is a job queue with workers, retries, and a dashboard — but that means Redis, a worker process, a retry policy, and failure triage: real complexity. At MVP scale (a handful of posts per day), synchronous publishing inside the request is operationally simpler, gives the user immediate feedback, and the failure surface is small enough to handle with a transactional state transition.

### Decision

Publish **synchronously within the request**: the endpoint performs a transactional status transition (`Approved → Publishing`), calls the Telegram API with bounded retries and timeouts, and records the outcome (`Published` with message IDs, or `Failed` with a reason). Idempotency keys prevent double publication on client retries. No job queue, no scheduler, no background workers ship in MVP. Deferred work (scheduled publishing, bulk image generation) is the explicit post-MVP trigger for introducing Redis + a lightweight worker.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Celery/RQ/Arq from day one | Redis + worker + retry policies + monitoring before the product has any posts; the most common source of "it worked yesterday" bugs |
| Serverless scheduled functions | Vendor-specific scheduling; another paid service; no user-visible benefit at MVP volume |
| Database-only polling scheduler | Hides the job mechanism in SQL; harder to observe and operate than a real queue when one is eventually needed |

### Consequences

- **Positive:** one process fewer to deploy and debug; the user sees the publish result in the same screen; failure states are simple and observable; zero queue infrastructure cost.
- **Negative:** request latency includes the Telegram API call (mitigated by bounded retries and a clear "publishing..." UI state); no scheduled publishing; no bulk/async work; a slow Telegram API makes the request slow (acceptable at MVP volume with a loading state and an idempotency guarantee).
- **Neutral:** the `Publishing → Published/Failed` state transition is designed so a future job queue can drive it without schema change — the queue calls the same service the endpoint does.

### When to Revisit

When scheduled publishing is prioritized (first post-MVP feature), when async image generation is enabled at volume, or when publish request latency becomes a measured problem. The migration path is additive: add Redis, wrap the same publisher service in a worker, and move the endpoint to enqueue — no rewrite.

---

## ADR-014: Manual Platform-Owner Approval (no self-serve subscriptions)

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

Any public signup form attracts spam, abuse, and low-quality tenants — for a product whose value is trusted AI content in real companies' channels, that risk is disproportionate. Self-serve signup also implies subscriptions, metering enforcement, and payments — a large surface with no MVP revenue to justify it. The tradeoff is growth friction: every company requires a human decision.

### Decision

Company registration creates a **pending** company; only the platform owner can approve (activate) or reject it, via the admin UI or bot notification — no self-serve subscriptions, no payment integration, no billing in MVP. The platform owner is bootstrapped from `PLATFORM_OWNER_TELEGRAM_ID`. Open signup and monetization are explicit post-MVP decisions.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Open self-serve signup | Spam and abuse exposure; implies billing/quota enforcement before any revenue; off-brand for a curated B2B tool |
| Stripe self-serve subscriptions | Payments, proration, dunning, and tax surface with zero MVP revenue to justify it |
| Invite-only (no registration flow) | Blocks the natural "hear about it → try it" path; approval already provides curation without invisibility |

### Consequences

- **Positive:** complete control over tenant quality; no payment/tax/billing complexity; the approval step doubles as a trust signal for users; abuse surface stays near zero.
- **Negative:** manual operational bottleneck as signups grow (mitigated by the <5-click approval flow, Phase 9); growth is gated by the owner's availability; the product cannot "go viral" on its own.
- **Neutral:** approval state is a first-class company status in the data model, so adding self-serve tiers later is an extension, not a redesign.

### When to Revisit

When sustained signup demand makes the owner the bottleneck, or when monetization becomes a business priority — at which point the decision splits into "open signup?" and "subscriptions?", each evaluated on its own merits.

---

## ADR-015: Role-Based Access Control with Explicit Permissions

- **Status:** Accepted
- **Date:** 2026-10
- **Deciders:** Platform owner (solo developer)

### Context

The product defines exactly three roles — Platform Owner, Company Admin, and Content Creator — and role needs evolve per company and over time (e.g., "admins may also edit captions" is a configuration question, not a role question). Pure role-name checks (`if user.role == "content_creator"`) freeze that flexibility into code and make every new rule a deploy. Pure attribute-based access control is over-engineered for a known, small role set.

### Decision

Implement **RBAC with explicit permissions**: permissions are `resource:action` strings (e.g., `post:update`, `approval:review`, `platform:company:approve`); roles are named bundles of permissions; authorization is enforced by a FastAPI dependency that resolves the authenticated user's company role and checks the required permission. The permission catalog in [03-user-roles-and-use-cases.md](03-user-roles-and-use-cases.md) is the source of truth and the test oracle. Platform-plane permissions (`platform:*`) are checked separately from company membership — the platform owner has no implicit company access. Sensitive actions are audit-logged.

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| Role-name checks in handlers | Every new rule is a code change; no auditable catalog; permission drift between docs and code |
| ABAC (attribute-based) | Power the product doesn't need; policy engine complexity without a driver |
| Third-party auth platform (Clerk/Auth0) | Vendor dependency for a well-understood, in-product concern; multi-tenant company modeling still custom |
| Telegram-native roles | Telegram has no notion of company roles; identity (ADR-004) is not authorization |

### Consequences

- **Positive:** authorization rules are data (the catalog), reviewable in one table, testable as a matrix, and changeable by configuration; audit logging attaches to explicit actions; new roles are new bundles, not new code.
- **Negative:** permission sprawl risk — the catalog must stay deliberately curated; developers must look up permissions instead of reading role names (mitigated by the catalog as a first-class doc); two-layer (company + platform) checks add a small amount of boilerplate.
- **Neutral:** the three-role model keeps the permission surface small and auditable from day one.

### When to Revisit

When the permission catalog grows large enough to need grouping/tooling (admin UI for bundles), or when companies demand custom role definitions — at which point the bundle table becomes per-company configuration. The dependency-based enforcement architecture supports both without change.

---

## Related Documents

- [04-system-architecture.md](04-system-architecture.md) — architecture these decisions implement
- [03-user-roles-and-use-cases.md](03-user-roles-and-use-cases.md) — role and permission catalog (ADR-015)
- [11-security-and-multi-tenancy.md](11-security-and-multi-tenancy.md) — security model (ADR-004, ADR-005)
- [13-deployment-and-operations.md](13-deployment-and-operations.md) — operational implications (ADR-001, ADR-008, ADR-009, ADR-013)
- [14-implementation-roadmap.md](14-implementation-roadmap.md) — phases that implement each decision
