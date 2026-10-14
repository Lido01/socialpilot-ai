# SocialPilot AI Documentation

This directory contains the complete system documentation for **SocialPilot AI**, a multi-tenant SaaS platform for AI-powered social media content management delivered as a Telegram Mini App.

## Reading Order

| Order | Document | Purpose |
|-------|----------|---------|
| 1 | [01-project-vision-and-scope.md](01-project-vision-and-scope.md) | Product vision, scope, and success criteria |
| 2 | [02-software-requirements.md](02-software-requirements.md) | Functional and non-functional requirements |
| 3 | [03-user-roles-and-use-cases.md](03-user-roles-and-use-cases.md) | User types, roles, permissions, and use cases |
| 4 | [04-system-architecture.md](04-system-architecture.md) | High-level architecture, components, and data flows |
| 5 | [05-database-design.md](05-database-design.md) | Database schema, ER diagrams, and multi-tenancy design |
| 6 | [06-api-specification.md](06-api-specification.md) | REST API endpoints, contracts, and error formats |
| 7 | [07-user-flows-and-state-machines.md](07-user-flows-and-state-machines.md) | User journeys, state transitions, and flow diagrams |
| 8 | [08-mini-app-ui-ux.md](08-mini-app-ui-ux.md) | Telegram Mini App screens, components, and UX specifications |
| 9 | [09-ai-and-media-pipeline.md](09-ai-and-media-pipeline.md) | AI text/image generation, media upload, and publishing pipeline |
| 10 | [10-telegram-integration.md](10-telegram-integration.md) | Telegram Bot API, Mini App auth, and channel management |
| 11 | [11-security-and-multi-tenancy.md](11-security-and-multi-tenancy.md) | Security model, tenant isolation, and threat mitigations |
| 12 | [12-testing-strategy.md](12-testing-strategy.md) | Test strategy, acceptance criteria, and test cases |
| 13 | [13-deployment-and-operations.md](13-deployment-and-operations.md) | Local development, production deployment, and operations |
| 14 | [14-implementation-roadmap.md](14-implementation-roadmap.md) | Phased implementation plan with milestones |
| 15 | [15-architecture-decisions.md](15-architecture-decisions.md) | Architectural decision records (ADRs) |

## Quick Reference

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, Telegram Mini Apps SDK |
| Backend | Python 3.11+, FastAPI, Pydantic, SQLAlchemy 2.0 |
| Database | PostgreSQL 15+, Alembic migrations |
| AI Providers | Google Gemini (text), Configurable image generation interface |
| Messaging | Telegram Bot API, Telegram Mini Apps |
| Infrastructure | Docker, Redis (future), Object storage (future) |

### Key Principles

- **Telegram Mini App First**: Primary interface is inside Telegram, not a standalone website
- **Multi-Tenant by Design**: Every company's data is isolated at database and API layers
- **Security by Default**: Server-side Telegram initData validation, RBAC, audit logging
- **Cost-Conscious MVP**: Start simple, add Redis/queue/object storage when justified
- **Provider-Agnostic AI**: Abstract interfaces for text and image generation providers

### MVP Scope

**Included:**
- Company registration with platform-owner approval
- Multi-company workspace with role-based access
- Telegram channel connection and verification
- AI text generation (Gemini) with brand context
- Image generation provider interface (pluggable)
- Local image upload with validation
- Draft creation, editing, preview, revision history
- Configurable approval workflow (Draft → In Review → Approved → Published)
- Multi-image album publishing (up to Telegram's 10-item limit)
- Publication history and basic analytics
- Platform-owner admin interface

**Deferred (Post-MVP):**
- Scheduled publishing with background workers
- Subscription billing and usage metering
- Advanced analytics and reporting
- Webhook-based Telegram updates
- Redis-backed job queue
- Object storage (S3-compatible) for media
- Platform administrator roles beyond owner
- Company ownership transfer
- White-label Mini App customization

## Current Prototype Status

The repository contains a **single-admin Telegram bot prototype** (`app/bot.py`, `app/ai_service.py`, `app/database.py`) using:
- SQLite for storage
- python-telegram-bot v22 for bot commands
- Google Gemini for text generation
- Single hardcoded admin user and channel

This prototype validates AI generation and basic publish flow but **does not implement** multi-tenancy, Mini App frontend, FastAPI backend, or any SaaS features. The documentation here describes the target architecture, not the current code.

## Contributing to Documentation

- Keep all documents consistent with each other
- Use Mermaid diagrams for flows and architecture
- Mark unresolved decisions with `⚠️ UNRESOLVED:` prefix
- Update `15-architecture-decisions.md` when making significant choices
- Cross-reference related sections using relative links