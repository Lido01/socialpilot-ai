# 07 — User Flows and State Machines

SocialPilot AI · Multi-Tenant Telegram Mini App SaaS

---

## Table of Contents

1. [Registration and Onboarding Flow](#registration-and-onboarding-flow)
2. [Company State Machine](#company-state-machine)
3. [User State Machine](#user-state-machine)
4. [Invitation State Machine](#invitation-state-machine)
5. [Membership State Machine](#membership-state-machine)
6. [Post State Machine](#post-state-machine)
7. [Approval Transition Rules](#approval-transition-rules)
8. [Channel Connection Flow](#channel-connection-flow)
9. [AI Text Generation Flow](#ai-text-generation-flow)
10. [Image Generation and Upload Flow](#image-generation-and-upload-flow)
11. [Post Editing and Revision History](#post-editing-and-revision-history)
12. [Approval Workflow](#approval-workflow)
13. [Multi-Image Publishing Flow](#multi-image-publishing-flow)
14. [Failure and Retry Handling](#failure-and-retry-handling)
15. [Tenant-Isolated Request Authorization](#tenant-isolated-request-authorization)

---

## Registration and Onboarding Flow

```mermaid
flowchart TD
    A[User opens Telegram Mini App] --> B[Mini App sends initData to backend]
    B --> C{Valid initData?}
    C -- No --> C1[Display auth error screen]
    C -- Yes --> D{User exists in database?}
    D -- No --> E[Create User record — status: active]
    D -- Yes --> F[Load user profile]
    E --> F
    F --> G{User has any memberships?}
    G -- Yes --> H{Has approved/pending company?}
    G -- No --> I[Show Company Registration screen]
    H -- Yes --> J[Show Company Selection screen]
    H -- No --> I
    I --> K[User fills registration form]
    K --> L[Submit — company status: pending]
    L --> M[Admin notified for approval]
    M --> N[Show Pending Approval screen]
    N --> O{Platform owner decision}
    O -- Approve --> P[Company status: active — Onboard to Dashboard]
    O -- Request Info --> Q[Company status: info_requested — Show info form]
    Q --> K
    O -- Reject --> R[Company status: rejected — Show rejection reason]
    R --> K
    P --> S[Dashboard with default brand settings]
    S --> T[Invite team members]
    T --> U[Connect Telegram channel]
    U --> V[Create first post]
```

### Onboarding Steps

| Step | Description | Actor |
|------|-------------|-------|
| 1 | User launches Mini App via Telegram | System |
| 2 | Backend validates Telegram `initData` signature | System |
| 3 | User record created or loaded | System |
| 4 | If no active company, present registration form | User |
| 5 | Platform owner reviews and approves | Platform Owner |
| 6 | User selects or is assigned to the company | System |
| 7 | User invites team members (optional) | Company Admin |
| 8 | User connects a Telegram channel | Company Admin |
| 9 | User creates and publishes first post | Content Creator |

---

## Company State Machine

```mermaid
stateDiagram-v2
    [*] --> pending: Registration submitted
    pending --> active: Platform owner approves
    pending --> info_requested: Info needed from applicant
    pending --> rejected: Platform owner rejects
    info_requested --> pending: Applicant resubmits
    info_requested --> rejected: Platform owner rejects
    info_requested --> cancelled: Applicant abandons
    active --> suspended: Platform owner suspends
    suspended --> active: Platform owner reinstates
    suspended --> cancelled: Account closed
    rejected --> pending: User resubmits
    cancelled --> [*]
```

| State | Description | Allowed Transitions |
|-------|-------------|---------------------|
| `pending` | Awaiting platform-owner review | → `active`, `info_requested`, `rejected` |
| `active` | Fully operational tenant | → `suspended` |
| `suspended` | Temporarily blocked (billing, abuse) | → `active`, `cancelled` |
| `rejected` | Application denied | → `pending` (resubmit) |
| `cancelled` | Permanently closed | Terminal |
| `info_requested` | Additional info needed from applicant | → `pending`, `rejected`, `cancelled` |

---

## User State Machine

```mermaid
stateDiagram-v2
    [*] --> active: First Mini App launch
    active --> suspended: Platform owner / admin action
    suspended --> active: Reinstated
    suspended --> banned: Permanent ban
    active --> deactivated: User self-deactivates
    deactivated --> active: User reactivates
    banned --> [*]
```

| State | Description |
|-------|-------------|
| `active` | Can authenticate, view data, perform role actions |
| `suspended` | Read-only; cannot create/edit/publish |
| `banned` | No access; initData still valid but rejected |
| `deactivated` | Self-service account freeze |

---

## Invitation State Machine

```mermaid
stateDiagram-v2
    [*] --> pending: Invitation sent
    pending --> accepted: Invitee accepts
    pending --> expired: TTL exceeded (7 days)
    pending --> revoked: Inviter or admin revokes
    accepted --> [*]
    expired --> [*]
    revoked --> [*]
```

| State | Description | TTL / Notes |
|-------|-------------|-------------|
| `pending` | Awaiting invitee response | 7-day expiry |
| `accepted` | Invitee joined the company | Creates a Membership record |
| `expired` | Window elapsed without response | Non-recoverable |
| `revoked` | Manually cancelled by inviter/admin | Non-recoverable |

---

## Membership State Machine

```mermaid
stateDiagram-v2
    [*] --> active: Invitation accepted / direct assignment
    active --> role_updated: Admin changes role
    role_updated --> active: Role saved
    active --> removed: Admin removes member
    removed --> [*]
    active --> left: Member leaves company
    left --> [*]
```

---

## Post State Machine

```mermaid
stateDiagram-v2
    [*] --> draft: Post created
    draft --> in_review: Content Creator submits for approval
    in_review --> changes_requested: Company Admin requests changes
    in_review --> approved: Company Admin approves
    in_review --> rejected: Company Admin rejects
    changes_requested --> in_review: Content Creator resubmits
    changes_requested --> draft: Content Creator saves as draft
    rejected --> draft: Content Creator edits and saves
    approved --> publishing: Company Admin triggers publish
    publishing --> published: All media published
    publishing --> failed: Error during publishing
    failed --> publishing: Manual retry
    failed --> draft: Abandon and edit
    draft --> cancelled: Content Creator cancels
    in_review --> cancelled: Content Creator withdraws
    changes_requested --> cancelled: Content Creator withdraws
    published --> [*]
    cancelled --> [*]
```

### State Descriptions

| State | Description | Terminal? |
|-------|-------------|-----------|
| `draft` | Being authored; not yet submitted | No |
| `in_review` | Submitted; awaiting Company Admin decision | No |
| `changes_requested` | Company Admin returned post with feedback | No |
| `approved` | Approved and ready to publish | No |
| `rejected` | Company Admin declined the post | No |
| `publishing` | Actively sending to Telegram | No |
| `published` | Successfully published to channel | Yes |
| `failed` | Publishing encountered an error | No |
| `cancelled` | Abandoned by Content Creator | Yes |

---

## Approval Transition Rules

| From State | Action | Required Role | Side Effects |
|------------|--------|---------------|--------------|
| `draft` | Submit for review | Content Creator | Post → `in_review`; notify Company Admins |
| `in_review` | Approve | Company Admin | Post → `approved`; notify Content Creator |
| `in_review` | Request changes | Company Admin | Post → `changes_requested`; notify Content Creator |
| `in_review` | Reject | Company Admin | Post → `rejected`; notify Content Creator |
| `changes_requested` | Resubmit | Content Creator | Post → `in_review`; bump revision |
| `changes_requested` | Save as draft | Content Creator | Post → `draft` |
| `changes_requested` | Withdraw | Content Creator | Post → `cancelled` |
| `approved` | Publish | Company Admin | Post → `publishing` |
| `rejected` | Edit and save | Content Creator | Post → `draft`; bump revision |
| `publishing` | Auto-retry | System | Retry count incremented |
| `failed` | Manual retry | Company Admin | Post → `publishing` |
| `failed` | Abandon | Company Admin | Post → `draft` |

> **Note:** Company Admins cannot approve their own submissions. If a user is both Content Creator and Company Admin, a second Company Admin must approve.

---

## Channel Connection Flow

```mermaid
sequenceDiagram
    participant U as User (Company Admin)
    participant MA as Mini App
    participant BE as Backend
    participant TG as Telegram Bot API

    U->>MA: Tap "Connect Channel"
    MA->>BE: GET /channels/connection-token
    BE->>BE: Generate one-time token (15-min TTL)
    BE-->>MA: { token, botUsername }
    MA->>TG: Deep link to bot with token
    TG->>BE: Webhook — user starts bot
    BE->>BE: Validate token; associate user with channel
    U->>TG: Add bot as channel admin
    TG->>BE: Webhook — chat member update
    BE->>BE: Verify bot has "Post Messages" permission
    BE->>BE: Channel record → connected
    BE-->>MA: WebSocket push — channel_connected
    MA-->>U: Success — channel listed
```

### Required Bot Permissions

| Permission | Purpose |
|------------|---------|
| `can_post_messages` | Send posts to the channel |
| `can_edit_messages` | Edit published posts (optional) |
| `can_delete_messages` | Remove failed posts (optional) |

---

## AI Text Generation Flow

```mermaid
sequenceDiagram
    participant U as Content Creator
    participant MA as Mini App
    participant BE as Backend
    participant AI as Gemini API
    participant DB as PostgreSQL

    U->>MA: Open AI text generation form
    U->>MA: Enter topic, tone, length, optional context
    MA->>BE: POST /ai/generate-text
    BE->>DB: Load brand context (company profile)
    BE->>BE: Build system prompt with brand voice + anti-hallucination rules
    BE->>AI: Send request with temperature, max_tokens
    AI-->>BE: Generated text
    BE->>DB: Log usage (tokens, model, cost)
    BE->>BE: Increment company usage counter
    BE-->>MA: { text, tokens_used, model }
    MA-->>U: Display generated text in editor
    U->>MA: Accept / Regenerate / Edit manually
```

### Anti-Hallucination Rules

1. System prompt enforces: *"Use only the provided brand context. Do not invent facts about the company."*
2. If brand context is empty, generation is blocked with a clear message.
3. Response includes a `confidence` score; low-confidence outputs are flagged.
4. All generated text is treated as a suggestion, never auto-published.

---

## Image Generation and Upload Flow

```mermaid
sequenceDiagram
    participant U as Content Creator
    participant MA as Mini App
    participant BE as Backend
    participant IMG as Image Provider (Replicate / Fal / OpenAI / Self-hosted)
    participant FS as Filesystem
    participant DB as PostgreSQL

    U->>MA: Open Image Generation form
    U->>MA: Enter prompt, select aspect ratio, count
    MA->>BE: POST /images/generate
    BE->>BE: Validate company plan allows generation
    BE->>IMG: Submit generation request
    IMG-->>BE: Generated image URL(s)
    BE->>FS: Download and validate file signature
    BE->>FS: Store in tenant-isolated path
    BE->>DB: Insert media metadata record
    BE->>DB: Log usage (provider, model, cost)
    BE-->>MA: { images: [{ id, url, width, height }] }
    MA-->>U: Display generated images
    U->>MA: Select image(s) to add to post
    MA->>BE: POST /posts/{id}/media
    BE->>DB: Associate media with post
    BE-->>MA: Updated post media list
```

### Image Provider Fallback

If the primary provider returns a `5xx` or timeout:

1. Retry with exponential backoff (max 2 retries).
2. If still failing, attempt failover to secondary provider if configured.
3. If all providers fail, return structured error to UI with user-friendly message.

---

## Post Editing and Revision History

### Revision Lifecycle

| Event | Action | Stored |
|-------|--------|--------|
| Post created | Initial snapshot | `revisions[0]` |
| Content Creator saves draft | New snapshot | `revisions[n]` |
| Submitted for review | Snapshot tagged `submitted` | `revisions[n]` |
| Changes requested | Snapshot tagged `changes_requested` | `revisions[n]` |
| Resubmitted | New snapshot tagged `submitted` | `revisions[n+1]` |
| Approved | Snapshot tagged `approved` | `revisions[n+1]` |

### Revision Record Schema (Conceptual)

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Revision identifier |
| `post_id` | UUID FK | Parent post |
| `version` | integer | Monotonically increasing |
| `caption` | text | Post body |
| `hashtags` | text[] | Hashtag list |
| `cta` | jsonb | Call-to-action object |
| `media_ids` | uuid[] | Ordered media references |
| `created_by` | UUID FK | User who made the change |
| `created_at` | timestamp | Change timestamp |
| `label` | text | Snapshot tag (draft, submitted, etc.) |

> Any user with `Content Creator` role or above can view revision history and restore a prior version.

---

## Approval Workflow

```mermaid
flowchart TD
    A[Content Creator finishes post] --> B[Save as Draft]
    B --> C[Preview post]
    C --> D{Satisfied?}
    D -- No --> B
    D -- Yes --> E[Submit for Review]
    E --> F[Company Admin notified]
    F --> G[Company Admin opens post]
    G --> H[View content + media + metadata]
    H --> I{Decision}
    I -- Approve --> J[Post → Approved]
    I -- Request Changes --> K[Add feedback]
    K --> L[Post → Changes Requested]
    L --> M[Content Creator notified]
    M --> N[Content Creator edits]
    N --> E
    I -- Reject --> O[Add rejection reason]
    O --> P[Post → Rejected]
    P --> Q[Content Creator notified]
    Q --> R{Resubmit?}
    R -- Yes --> N
    R -- No --> S[Post → Cancelled]
    J --> T[Company Admin triggers publish]
```

---

## Multi-Image Publishing Flow

```mermaid
sequenceDiagram
    participant U as Company Admin
    participant MA as Mini App
    participant BE as Backend
    participant TG as Telegram Bot API

    U->>MA: Open approved post
    MA->>BE: GET /posts/{id}
    BE-->>MA: Post + ordered media list
    U->>MA: Tap "Publish"
    MA->>BE: POST /posts/{id}/publish
    BE->>BE: Validate media count ≤ 10
    BE->>BE: Validate caption length ≤ 1024 chars
    BE->>BE: Post status → publishing

    alt Text-only post
        BE->>TG: sendMessage
        TG-->>BE: OK
    else Single image
        BE->>TG: sendPhoto (caption = post caption)
        TG-->>BE: OK
    else Album (2–10 images)
        BE->>TG: sendMediaGroup (media array, first item carries caption)
        TG-->>BE: OK
    end

    BE->>BE: Store Telegram message IDs
    BE->>BE: Post status → published
    BE-->>MA: WebSocket push — published
    MA-->>U: Success confirmation with Telegram link
```

### Album Caption Placement

For multi-image albums, Telegram places the caption on the **first media item** in the array. The backend constructs the album so the first element carries the full post caption; remaining elements have empty captions.

---

## Failure and Retry Handling

### Retry Matrix

| Failure Point | Retry Strategy | Max Retries | User Notification |
|---------------|----------------|-------------|-------------------|
| Telegram API timeout | Exponential backoff (2s, 4s, 8s) | 3 | Silent retry; toast on final failure |
| Telegram rate limit | Wait `retry_after` seconds | Per Telegram response | Toast: "Rate limited — retrying" |
| Image generation provider 5xx | Exponential backoff + failover | 2 per provider | Toast on all-providers failure |
| Image generation provider timeout | Retry with same provider | 1 | Toast on failure |
| Gemini API error | Exponential backoff | 2 | Inline error in editor |
| Media upload (local file) | Immediate retry | 1 | Toast with error detail |

### Post Publishing Failure

1. Post transitions to `failed` with `failure_reason` stored.
2. Failed post is visible in Publication History with a "Retry" button.
3. Retry re-enters `publishing` state; previous Telegram message IDs are checked to avoid duplicates.
4. If 3 retries exhausted, post remains `failed`; user can abandon to `draft` or retry manually.

### Idempotency

All publish requests include an `Idempotency-Key` (UUID) generated by the backend. Telegram API deduplication is leveraged to prevent double-publishing on retry.

---

## Tenant-Isolated Request Authorization

```mermaid
sequenceDiagram
    participant MA as Mini App
    participant MW as Auth Middleware
    participant RBAC as RBAC Guard
    participant BE as Handler
    participant DB as PostgreSQL

    MA->>MW: Request + initData header
    MW->>MW: Validate Telegram signature
    MW->>DB: Load user by Telegram ID
    MW->>DB: Load user's active membership
    MW->>MW: Inject { userId, companyId, role } into context
    MW->>RBAC: Forward request
    RBAC->>RBAC: Check role permission for endpoint
    alt Permission denied
        RBAC-->>MA: 403 Forbidden
    else Permission granted
        RBAC->>BE: Forward request
        BE->>DB: Query with company_id filter (mandatory)
        DB-->>BE: Tenant-scoped results
        BE-->>MA: 200 OK with data
    end
```

### Isolation Guarantees

| Layer | Mechanism |
|-------|-----------|
| Authentication | Telegram `initData` HMAC validation on every request |
| Authorization | RBAC guard checks role against endpoint permission map |
| Data isolation | Every database query includes `company_id = $current_tenant` |
| File storage | Media stored under `/tenants/{company_id}/...` prefix |
| Cache keys | All Redis cache keys prefixed with `{companyId}:` |
| WebSocket | Connection bound to `companyId` on auth; events filtered per tenant |

---

*End of document.*
