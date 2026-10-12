# Project Vision and Scope

## Product Vision

**SocialPilot AI** is a multi-tenant SaaS platform that enables companies to manage their social media content entirely within Telegram using a modern Mini App interface. Companies register, get approved by the platform owner, configure their brand and channels, invite team members, and create AI-assisted content that flows through a configurable approval workflow before publishing to their connected Telegram channels.

The platform owner operates the service, controls company admissions, manages subscription plans, and monitors platform health—all without exposing company data across tenant boundaries.

## Target Users

| User Type | Description |
|-----------|-------------|
| **Platform Owner** | Operates the SaaS; approves/rejects companies; manages plans and system settings |
| **Company Owner** | Registers the company; configures brand, channels, team; full workspace control |
| **Company Admin** | Manages workspace per assigned permissions; cannot approve companies |
| **Content Creator** | Generates content, uploads media, edits drafts, submits for approval |
| **Content Approver** | Reviews, edits, approves, or rejects submitted content |
| **Publisher** | Publishes approved content to connected channels |
| **Analyst/Viewer** | Views reports, history, and analytics without modifying content |

## Core Value Propositions

1. **Native Telegram Experience**: No separate website login; work inside Telegram on mobile and desktop
2. **AI-Assisted Creation**: Text generation with brand context; pluggable image generation
3. **Governed Workflow**: Role-based approval policies prevent unauthorized publishing
4. **Multi-Tenant Isolation**: Cryptographic tenant boundaries; zero cross-company data leakage
5. **Channel Ownership Verification**: Prove channel control before connecting
6. **Audit Trail**: Complete revision history and action logging for compliance

## Scope Boundaries

### In Scope (MVP)
- Company registration → platform owner approval → workspace activation
- Brand profile (name, tone, hashtags, CTA templates, audience, language)
- Telegram channel connection with bot-admin verification
- Team invitations with role assignment
- AI text generation (Gemini) using brand profile + user prompt
- Image generation provider interface (configurable, not hardcoded)
- Local image upload (validation, preview, reorder, multi-select)
- Draft CRUD, preview, revision history
- Approval workflow: Draft → In Review → Approved/Changes Requested/Rejected
- Immediate publishing to Telegram (media groups up to 10 items)
- Publication history with Telegram message IDs
- Platform-owner company management dashboard
- Usage tracking per company (AI calls, images, posts, storage)

### Out of Scope (Post-MVP)
- Scheduled/recurring publishing (requires job queue)
- Subscription billing, invoicing, payment integration
- Advanced analytics (engagement, reach, best-time-to-post)
- Webhook-based Telegram updates (polling is sufficient for MVP)
- Redis-backed background workers
- S3-compatible object storage (local filesystem for MVP)
- White-label Mini App theming per company
- Company ownership transfer workflow
- Platform administrator roles (beyond single owner)
- Multi-language UI localization (English only for MVP)
- Content templates and snippet library
- Competitor analysis or social listening
- Direct publishing to non-Telegram platforms (Instagram, LinkedIn, etc.)

## Success Criteria (MVP)

| Metric | Target |
|--------|--------|
| Company onboarding time (registration → first publish) | < 30 minutes |
| Mini App cold start (auth → dashboard) | < 3 seconds on 4G |
| AI text generation latency (p95) | < 8 seconds |
| Image upload validation + preview (5 MB) | < 2 seconds |
| Cross-tenant access attempts blocked | 100% in security tests |
| Approval-to-publish latency (p95) | < 5 seconds |
| Platform owner approval workflow | < 5 clicks |
| Data export on company deletion | Complete within 24 hours |

## Assumptions

1. **Telegram Mini Apps** are available to all target users (Telegram 8.0+ on iOS/Android/Desktop)
2. **Google Gemini API** remains available and cost-effective for text generation
3. **Image generation providers** (Replicate, Fal.ai, OpenAI, self-hosted) offer HTTP APIs
3. **PostgreSQL** is the standard relational database; no need for NoSQL
4. **Single platform owner** for MVP; platform admin roles added later
5. **Manual company approval** is acceptable for MVP; self-serve subscriptions later
6. **Polling-based bot** is sufficient; webhook infrastructure deferred
6. **File storage** on local disk with volume mount is acceptable for MVP
7. **English-only UI** for MVP; i18n framework prepared but not populated

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Telegram Mini App API changes | Medium | High | Pin SDK version; abstract Telegram calls behind service layer |
| Gemini API price increase | Medium | Medium | Provider interface allows switching; cache brand-context prompts |
| Image generation provider unavailable | High | Medium | Interface supports multiple providers; graceful degradation to upload-only |
| Cross-tenant data leak | Low | Critical | Row-level security + application-layer checks + integration tests |
| Channel verification spoofing | Low | High | Require bot admin rights + unique verification code per attempt |
| Media upload DoS (large files) | Medium | High | Strict size/type validation; streaming upload; quota per company |
| Platform owner credential compromise | Low | Critical | Separate admin API key; audit log; 2FA on hosting provider |

## Glossary

| Term | Definition |
|------|------------|
| **Workspace** | A company's isolated environment within SocialPilot AI |
| **Mini App** | Telegram Web App running in the Telegram client's webview |
| **initData** | Signed authentication blob from Telegram Mini App launch |
| **Brand Profile** | Company's voice, audience, hashtags, CTA templates, language settings |
| **Media Group** | Telegram's album format (up to 10 photos/videos with single caption) |
| **Approval Policy** | Rules defining which roles must approve before publish |
| **initData Validation** | Server-side HMAC-SHA256 verification of Telegram's auth data |
| **Tenant Isolation** | Enforcement that company A cannot access company B's resources |