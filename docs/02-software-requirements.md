# Software Requirements

This document defines the functional and non-functional requirements for SocialPilot AI. Requirements are tagged with priority: **MVP** (must-have for launch), **LATER** (post-MVP), or **FUTURE** (planned but unscheduled).

## Functional Requirements

### FR-1: Telegram Mini App Authentication (MVP)

| ID | Requirement |
|----|-------------|
| FR-1.1 | The Mini App must open inside Telegram's webview on mobile and desktop. |
| FR-1.2 | The frontend must send Telegram `initData` to the backend on launch. |
| FR-1.3 | The backend must validate the `initData` HMAC-SHA256 signature using the bot token. |
| FR-1.4 | The backend must reject `initData` older than 24 hours (Telegram recommendation). |
| FR-1.5 | The backend must create or look up a `user` record from the validated Telegram identity. |
| FR-1.6 | The backend must issue a short-lived session token (JWT) after successful validation. |
| FR-1.7 | The frontend must store the session token in memory (not localStorage) for security. |
| FR-1.8 | The session must expire after 12 hours of inactivity; refresh via re-launch from Telegram. |

### FR-2: Company Registration and Approval (MVP)

| ID | Requirement |
|----|-------------|
| FR-2.1 | An authenticated user with no active company may request a new company workspace. |
| FR-2.2 | Registration must capture: company name, industry, website (optional), country, and contact email. |
| FR-2.3 | The backend must create the company in `pending` status with the requesting user as `owner`. |
| FR-2.4 | The owner must see a "Pending Approval" screen with expected next steps. |
| FR-2.5 | The platform owner must see all pending companies in an admin queue. |
| FR-2.6 | The platform owner must approve, reject (with reason), or request more info. |
| FR-2.7 | On approval, the company transitions to `active` and the owner is notified. |
| FR-2.8 | On rejection, the company transitions to `rejected`; the owner may re-register after 7 days. |
| FR-2.9 | One Telegram user may own at most 5 active companies (configurable). |
| FR-2.10 | Duplicate company names are allowed only if owned by different users; a user cannot register two companies with identical normalized names. |

### FR-3: Company Workspace Management (MVP)

| ID | Requirement |
|----|-------------|
| FR-3.1 | The company owner may update company profile (name, industry, website, country). |
| FR-3.2 | The company owner may configure the brand profile (display name, tone, audience, language, default hashtags, default CTA). |
| FR-3.3 | The company owner may suspend (deactivate) their own company; data is retained, workspace is read-only. |
| FR-3.4 | Only the platform owner may cancel (delete) a company. |
| FR-3.5 | Company deletion must export all company data to a downloadable archive before permanent deletion (async, 24h window). |

### FR-4: Team Management (MVP)

| ID | Requirement |
|----|-------------|
| FR-4.1 | The owner/admin may invite a member by Telegram username or user ID. |
| FR-4.2 | The invite must specify one or more roles (creator, approver, publisher, analyst, admin). |
| FR-4.3 | Invitations must expire after 7 days. |
| FR-4.4 | The owner/admin may revoke an unaccepted invitation. |
| FR-4.5 | The invited user must accept the invitation from within the Mini App. |
| FR-4.6 | A user may hold different roles in different companies. |
| FR-4.7 | The owner/admin may change a member's roles at any time. |
| FR-4.8 | The owner/admin may remove a member; removal takes effect immediately. |
| FR-4.9 | The last owner cannot be removed; ownership must be transferred first. |
| FR-4.10 | A user may be both creator and publisher if assigned both roles. |

### FR-5: Channel Connection (MVP)

| ID | Requirement |
|----|-------------|
| FR-5.1 | The owner/admin may start connecting a Telegram channel. |
| FR-5.2 | The user must add the platform bot as an admin of the target channel. |
| FR-5.3 | The backend must verify the bot has admin rights in the channel (via Bot API `getChat` / `getChatAdministrators`). |
| FR-5.4 | The backend must verify the channel is not already connected to another company. |
| FR-5.5 | The channel must record: channel ID, title, username (if any), type, member count, connection timestamp. |
| FR-5.6 | The owner/admin may disconnect a channel; historical publications remain. |
| FR-5.7 | A channel may belong to exactly one company. |

### FR-6: AI Text Generation (MVP)

| ID | Requirement |
|----|-------------|
| FR-6.1 | A creator may request text generation with: topic, goal, audience, tone, language, length, CTA, hashtags, campaign notes. |
| FR-6.2 | The backend must merge the company brand profile with the user's request into a provider prompt. |
| FR-6.3 | The prompt must instruct the model not to invent prices, discounts, locations, or unverified claims. |
| FR-6.4 | The generated text must be returned as an editable draft (not published). |
| FR-6.5 | Generation must be rate-limited per user and per company. |
| FR-6.6 | Each generation call must be recorded in `usage_records`. |
| FR-6.7 | Provider failures must return a clear error without exposing API keys or raw provider responses. |

### FR-7: Image Generation (LATER - provider interface in MVP)

| ID | Requirement |
|----|-------------|
| FR-7.1 | The backend must expose an `ImageGenerationProvider` interface with capabilities metadata. |
| FR-7.2 | A creator may request image generation with: prompt, aspect ratio, count (within provider limit). |
| FR-7.3 | Generated images must be returned as selectable results. |
| FR-7.4 | The user may keep, regenerate, or discard individual results. |
| FR-7.5 | Kept images become `media_assets` owned by the company. |
| FR-7.6 | Each generation must be recorded in `usage_records`. |
| FR-7.7 | If no provider is configured, image generation returns a clear "unavailable" state. |

### FR-8: Media Upload (MVP)

| ID | Requirement |
|----|-------------|
| FR-8.1 | A creator may upload images from the device via the Mini App file picker. |
| FR-8.2 | Multi-select must be supported where the client allows it. |
| FR-8.3 | The frontend must preview, remove, and reorder selected images before upload. |
| FR-8.4 | The backend must validate: MIME type (image/jpeg, image/png, image/webp, image/gif), file signature (magic bytes), size (max 10 MB per image), count (max 10 per post). |
| FR-8.5 | Validation must not trust filename extensions alone. |
| FR-8.6 | Uploaded files must be stored outside the database (filesystem in MVP; object storage later). |
| FR-8.7 | Only metadata (path, size, MIME, dimensions, hash) is stored in PostgreSQL. |
| FR-8.8 | Malformed or suspicious files must be rejected and quarantined; no execution of uploaded content. |
| FR-8.9 | Upload failures must be reported per-file with retry guidance. |

### FR-9: Content Drafts and Editing (MVP)

| ID | Requirement |
|----|-------------|
| FR-9.1 | A creator may create a draft with caption, hashtags, CTA, and media. |
| FR-9.2 | The creator may edit caption, hashtags, CTA, and media order before submission. |
| FR-9.3 | Every significant edit must create a `post_revision` with author and timestamp. |
| FR-9.4 | The creator may save a draft, preview it, or submit it for approval. |
| FR-9.5 | The creator may cancel a draft (moves to `cancelled`, retained in history). |
| FR-9.6 | Drafts must be soft-deleted on cancel; hard delete is platform-owner only. |

### FR-10: Approval Workflow (MVP)

| ID | Requirement |
|----|-------------|
| FR-10.1 | Default policy: Draft → In Review → Approved → Publishing → Published. |
| FR-10.2 | An approver may request changes (returns to Draft) with a required reason. |
| FR-10.3 | An approver may reject (terminal `rejected` state) with a required reason. |
| FR-10.4 | A rejected post must be re-created or duplicated into a new draft to be republished. |
| FR-10.5 | Publishing requires the post to be in `approved` state. |
| FR-10.6 | Company approval policy is configurable: "creator cannot publish", "creator may publish own", "any approved may publish". |
| FR-10.7 | Every approval action must be recorded in `approval_events` with actor, action, reason, timestamp. |

### FR-11: Publishing (MVP)

| ID | Requirement |
|----|-------------|
| FR-11.1 | A publisher may publish an approved post to a connected channel of the same company. |
| FR-11.2 | The backend must verify post ownership, channel ownership, publisher permission, and approval policy before sending. |
| FR-11.3 | Text-only, single-image, and multi-image album (up to 10 items) posts must be supported. |
| FR-11.4 | Albums with more than 10 items must be rejected with a clear validation message; no silent splitting. |
| FR-11.5 | The backend must record the Telegram message ID(s) on success. |
| FR-11.6 | On failure, the post must return to `draft` (or remain `approved` per policy) and the error must be recorded. |
| FR-11.7 | Concurrent publish attempts on the same post must be serialized; duplicate sends must be prevented. |
| FR-11.8 | Publishing must be idempotent: a client retry with the same idempotency key must not re-send. |

### FR-12: History, Calendar, Analytics (MVP - basic)

| ID | Requirement |
|----|-------------|
| FR-12.1 | The company may view publication history with filters (channel, date, status). |
| FR-12.2 | A basic content calendar shows planned and published posts by date. |
| FR-12.3 | Basic counts: total posts, published this month, approval rate, media count. |
| FR-12.4 | The company may view usage: AI text calls, image generations, storage used, posts created. |

### FR-13: Notifications and Activity (MVP - basic)

| ID | Requirement |
|----|-------------|
| FR-13.1 | The platform must generate notifications for: invitation received, company approved/rejected, post approved/rejected, post published, post failed. |
| FR-13.2 | Notifications must be viewable in the Mini App and marked as read. |
| FR-13.3 | An audit log must record all sensitive actions (actor, action, entity, timestamp, IP). |

### FR-14: Platform Owner Administration (MVP)

| ID | Requirement |
|----|-------------|
| FR-14.1 | The platform owner may list, approve, reject, suspend companies. |
| FR-14.2 | The platform owner may view company details, members, channels, and usage. |
| FR-14.3 | The platform owner may configure platform-wide AI provider settings. |
| FR-14.4 | The platform owner may view platform metrics (total companies, active companies, AI usage). |

### FR-15: Scheduled Publishing (FUTURE)

| ID | Requirement |
|----|-------------|
| FR-15.1 | A publisher may schedule an approved post for a future time. |
| FR-15.2 | Scheduled posts require a background worker and timezone handling. |
| FR-15.3 | Scheduled posts must support retry policy and failure notification. |

## Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1 | Tenant isolation | Zero cross-company data access in all API and DB queries |
| NFR-2 | Authentication | Server-validated Telegram initData; no client-trusted identity |
| NFR-3 | Authorization | Permission-checked on every sensitive endpoint |
| NFR-4 | Availability | 99.5% monthly uptime (MVP, single instance) |
| NFR-5 | Latency | API p95 < 500ms; AI generation p95 < 8s |
| NFR-6 | Security | HTTPS everywhere; secrets in env/secrets manager; hashed passwords |
| NFR-7 | Auditability | All sensitive actions logged with actor, timestamp, IP |
| NFR-8 | Scalability | Modular monolith; horizontal scale via replicas when needed |
| NFR-9 | Maintainability | Typed codebase (TypeScript + Python type hints); test coverage ≥ 70% on core paths |
| NFR-10 | Portability | Local dev on Windows/PowerShell; containerized production |
| NFR-11 | Cost | Development free-tier friendly; production costs documented per service |
| NFR-12 | Accessibility | WCAG 2.1 AA within Mini App constraints; keyboard navigable |
| NFR-13 | Internationalization | English for MVP; i18n framework prepared |
| NFR-14 | Data retention | Audit logs 12 months; published history retained; cancelled drafts 90 days |

## Out of Scope (Explicitly Not Required)

- Public marketing website as primary interface
- Publishing to non-Telegram social platforms
- Native mobile apps (iOS/Android)
- Real-time collaboration on a single draft
- AI agent that auto-publishes without approval
- Billing/payments integration in MVP
- Multi-language UI content in MVP

## Acceptance Criteria Summary

See [12-testing-strategy.md](12-testing-strategy.md) for the full acceptance criteria matrix. The MVP is considered complete when all MVP functional requirements pass their acceptance tests and all security acceptance criteria are met.
