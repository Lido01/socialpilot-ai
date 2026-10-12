# API Specification

This document defines the versioned REST API for SocialPilot AI. All endpoints are under `/api/v1`. The API is consumed exclusively by the Telegram Mini App frontend.

Related documents: [04-system-architecture.md](04-system-architecture.md), [05-database-design.md](05-database-design.md), [03-user-roles-and-use-cases.md](03-user-roles-and-use-cases.md).

---

## 1. Conventions

### 1.1 Base URL

```
https://api.socialpilot.ai/api/v1
```

### 1.2 Authentication

All endpoints except `POST /auth/telegram` require a Bearer token:

```
Authorization: Bearer <JWT>
```

The JWT is obtained by validating Telegram `initData` (see [Auth](#2-auth)). Token lifetime: 12 hours sliding inactivity window.

### 1.3 Tenant Scoping

Company-scoped endpoints resolve `company_id` from the URL path parameter `{company_id}`. The server verifies the authenticated user has an active membership in that company. If no membership exists, the response is **404** (not 403) to prevent company ID enumeration.

### 1.4 Content Type

All requests and responses use `application/json; charset=utf-8`. File uploads use `multipart/form-data`.

### 1.5 Pagination

List endpoints accept query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 20 | Max items per page (1–100) |
| `offset` | integer | 0 | Items to skip |

Response envelope:

```json
{
  "data": [ ... ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 137
  }
}
```

### 1.6 Idempotency

Publishing endpoints accept an optional `Idempotency-Key` header. If the same key is reused within 24 hours, the original result is returned without re-executing the publish.

---

## 2. Error Format

All errors return a consistent envelope:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [
      {
        "field": "caption",
        "message": "Caption must not exceed 1024 characters"
      }
    ],
    "request_id": "req_abc123"
  }
}
```

### 2.1 Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `VALIDATION_ERROR` | Request body/params fail schema validation |
| 401 | `UNAUTHENTICATED` | Missing, expired, or invalid JWT |
| 403 | `FORBIDDEN` | Authenticated but lacks required permission |
| 404 | `NOT_FOUND` | Resource does not exist or user has no access |
| 409 | `CONFLICT` | Resource state conflict (e.g., duplicate, already connected) |
| 422 | `UNPROCESSABLE` | Semantic validation failed (e.g., post not in approved state) |
| 429 | `RATE_LIMITED` | Rate limit exceeded |
| 500 | `INTERNAL_ERROR` | Unexpected server error |
| 502 | `PROVIDER_ERROR` | External provider (Telegram, Gemini) failure |
| 503 | `SERVICE_UNAVAILABLE` | Feature not configured (e.g., no image provider) |

### 2.2 Error Handling Rules

- **404 for cross-tenant access**: If a user has no membership in the target company, return 404 regardless of whether the resource exists.
- **No stack traces in production**: Internal errors return a generic message; details are logged server-side.
- **Provider errors are sanitized**: Gemini/Telegram errors never expose API keys or raw provider responses.
- **Request ID**: Every request generates a UUID returned in the `X-Request-ID` response header and in error bodies.

---

## 3. Auth

### 3.1 `POST /auth/telegram` — Authenticate with Telegram initData

**Purpose:** Validate Telegram `initData`, create or update user, issue JWT.

**Permission:** Public (no authentication required).

**Tenant scoping:** None (platform-level).

**Request body:**

```json
{
  "initData": "query_id=...&user=...&auth_date=...&hash=...",
  "startParam": "company_abc123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `initData` | string | Yes | Raw `initData` string from `window.Telegram.WebApp.initData` |
| `startParam` | string | No | Deep-link parameter from Mini App launch |

**Validation:**

- `initData` must be a non-empty string.
- HMAC-SHA256 signature must validate against the bot token.
- `auth_date` must be within 24 hours of current time.
- `user` object must contain `id` (integer).

**Success response (200):**

```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "expiresAt": "2026-10-11T14:30:00Z",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "telegramId": 123456789,
    "username": "johndoe",
    "displayName": "John Doe"
  },
  "companies": [
    {
      "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "name": "Acme Corp",
      "status": "active",
      "roles": ["company_owner"]
    }
  ]
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 400 | `VALIDATION_ERROR` | Missing or malformed `initData` |
| 401 | `UNAUTHENTICATED` | Invalid HMAC signature |
| 401 | `UNAUTHENTICATED` | `initData` expired (> 24h) |

**Idempotency:** Safe to retry. Re-authentication returns a new token; old tokens remain valid until expiry.

---

### 3.2 `GET /auth/me` — Get Current User

**Purpose:** Return the authenticated user's profile and memberships.

**Permission:** Authenticated.

**Tenant scoping:** None (returns all memberships across companies).

**Success response (200):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "telegramId": 123456789,
  "username": "johndoe",
  "displayName": "John Doe",
  "languageCode": "en",
  "companies": [
    {
      "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "name": "Acme Corp",
      "status": "active",
      "roles": ["company_owner"],
      "permissions": ["company:view", "company:update", "..."]
    }
  ]
}
```

---

### 3.3 `POST /auth/switch-company` — Switch Active Company

**Purpose:** Set the active company context for subsequent requests (stored in JWT claims or session).

**Permission:** Authenticated.

**Request body:**

```json
{
  "companyId": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
}
```

**Success response (200):**

```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "activeCompany": {
    "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "name": "Acme Corp"
  }
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 403 | `FORBIDDEN` | User has no membership in the specified company |
| 404 | `NOT_FOUND` | Company does not exist |

---

## 4. Companies

### 4.1 `POST /companies` — Register a New Company

**Purpose:** Create a new company workspace in `pending` status. The requesting user becomes `company_owner`.

**Permission:** Authenticated (any user with no active company).

**Tenant scoping:** None (creates a new tenant).

**Request body:**

```json
{
  "name": "Acme Corp",
  "industry": "E-commerce",
  "website": "https://acme.example.com",
  "country": "US",
  "contactEmail": "owner@acme.example.com"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `name` | string | Yes | 3–255 chars |
| `industry` | string | No | Max 128 chars |
| `website` | string | No | Valid URL, max 512 chars |
| `country` | string | No | ISO 3166-1 alpha-2 |
| `contactEmail` | string | No | Valid email, max 255 chars |

**Success response (201):**

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "name": "Acme Corp",
  "status": "pending",
  "ownerUserId": "550e8400-e29b-41d4-a716-446655440000",
  "createdAt": "2026-10-11T12:00:00Z"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 400 | `VALIDATION_ERROR` | Missing required fields or invalid format |
| 409 | `CONFLICT` | User already has a company with the same normalized name |
| 409 | `CONFLICT` | User already has 5 active companies (FR-2.9) |
| 422 | `UNPROCESSABLE` | User has a pending registration for the same normalized name |

**Idempotency:** Not idempotent. Retries create duplicate attempts; client should handle 409.

---

### 4.2 `GET /companies/{company_id}` — Get Company Details

**Purpose:** Return company profile and brand profile.

**Permission:** `company:view`

**Tenant scoping:** `company_id` from path; membership required.

**Success response (200):**

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "name": "Acme Corp",
  "industry": "E-commerce",
  "website": "https://acme.example.com",
  "country": "US",
  "contactEmail": "owner@acme.example.com",
  "status": "active",
  "brandProfile": {
    "displayName": "Acme",
    "tone": "professional",
    "audience": "Tech-savvy consumers aged 25-45",
    "language": "en",
    "defaultHashtags": ["#acme", "#tech"],
    "defaultCta": "Shop now at acme.example.com"
  },
  "subscription": {
    "planName": "Starter",
    "status": "active",
    "expiresAt": "2026-11-11T00:00:00Z"
  }
}
```

---

### 4.3 `PATCH /companies/{company_id}` — Update Company Profile

**Purpose:** Update company name, industry, website, country, or contact email.

**Permission:** `company:update`

**Tenant scoping:** `company_id` from path.

**Request body:** Same fields as registration, all optional.

**Success response (200):** Updated company object.

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 400 | `VALIDATION_ERROR` | Invalid field values |
| 403 | `FORBIDDEN` | User lacks `company:update` |
| 404 | `NOT_FOUND` | No membership in company |
| 409 | `CONFLICT` | Normalized name already used by another company owned by same user |

---

### 4.4 `PUT /companies/{company_id}/brand` — Update Brand Profile

**Purpose:** Create or update the company's brand profile.

**Permission:** `brand:update`

**Tenant scoping:** `company_id` from path.

**Request body:**

```json
{
  "displayName": "Acme",
  "tone": "professional",
  "audience": "Tech-savvy consumers aged 25-45",
  "language": "en",
  "defaultHashtags": ["#acme", "#tech"],
  "defaultCta": "Shop now at acme.example.com"
}
```

**Success response (200):** Updated brand profile.

---

### 4.5 `POST /companies/{company_id}/suspend` — Self-Suspend Company

**Purpose:** Owner suspends their own company. Data retained, workspace read-only.

**Permission:** `company:deactivate`

**Tenant scoping:** `company_id` from path.

**Success response (200):**

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "status": "suspended"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 403 | `FORBIDDEN` | Only the owner may self-suspend |
| 409 | `CONFLICT` | Company already suspended |

---

### 4.6 `GET /companies/{company_id}/usage` — Get Company Usage

**Purpose:** Return usage metrics for the company.

**Permission:** `usage:view`

**Tenant scoping:** `company_id` from path.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from` | date | 30 days ago | Start date (ISO 8601) |
| `to` | date | today | End date (ISO 8601) |

**Success response (200):**

```json
{
  "period": { "from": "2026-09-11", "to": "2026-10-11" },
  "textGenerations": 142,
  "imageGenerations": 38,
  "postsCreated": 56,
  "postsPublished": 48,
  "storageUsedBytes": 52428800,
  "breakdown": [
    { "date": "2026-10-10", "textGenerations": 12, "imageGenerations": 3, "postsCreated": 5 }
  ]
}
```

---

## 5. Members

### 5.1 `GET /companies/{company_id}/members` — List Members

**Purpose:** Return all active members with their roles.

**Permission:** `member:list`

**Tenant scoping:** `company_id` from path.

**Success response (200):**

```json
{
  "data": [
    {
      "userId": "550e8400-e29b-41d4-a716-446655440000",
      "displayName": "John Doe",
      "username": "johndoe",
      "roles": ["company_owner"],
      "joinedAt": "2026-10-01T10:00:00Z"
    },
    {
      "userId": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "displayName": "Jane Smith",
      "username": "janesmith",
      "roles": ["creator", "publisher"],
      "joinedAt": "2026-10-05T14:30:00Z"
    }
  ],
  "pagination": { "limit": 20, "offset": 0, "total": 2 }
}
```

---

### 5.2 `POST /companies/{company_id}/invitations` — Invite a Member

**Purpose:** Invite a user by Telegram username or user ID.

**Permission:** `member:invite`

**Tenant scoping:** `company_id` from path.

**Request body:**

```json
{
  "telegramUsername": "janesmith",
  "roleIds": ["role-creator-uuid", "role-publisher-uuid"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `telegramUsername` | string | Yes* | Telegram username (without @) |
| `telegramUserId` | integer | Yes* | Telegram user ID (alternative to username) |
| `roleIds` | string[] | Yes | At least one role ID |

*Either `telegramUsername` or `telegramUserId` is required.

**Success response (201):**

```json
{
  "id": "inv-uuid",
  "companyId": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "telegramUsername": "janesmith",
  "status": "pending",
  "expiresAt": "2026-10-18T12:00:00Z"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 400 | `VALIDATION_ERROR` | Neither username nor userId provided |
| 403 | `FORBIDDEN` | Inviter's roles are a subset of invitee's roles (cannot invite above own privilege) |
| 409 | `CONFLICT` | User is already a member |
| 409 | `CONFLICT` | Pending invitation already exists for this user |
| 404 | `NOT_FOUND` | Telegram username not found in platform |

---

### 5.3 `POST /invitations/{invitation_id}/accept` — Accept Invitation

**Purpose:** Accept a pending invitation. Creates membership with assigned roles.

**Permission:** Authenticated (invited user only).

**Tenant scoping:** Invitation must belong to the authenticated user.

**Success response (200):**

```json
{
  "membershipId": "mem-uuid",
  "company": {
    "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    "name": "Acme Corp"
  },
  "roles": ["creator", "publisher"]
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 403 | `FORBIDDEN` | Authenticated user is not the invitee |
| 404 | `NOT_FOUND` | Invitation not found or not pending |
| 410 | `EXPIRED` | Invitation expired (> 7 days) |

---

### 5.4 `DELETE /invitations/{invitation_id}` — Revoke Invitation

**Purpose:** Revoke a pending invitation.

**Permission:** `member:invite`

**Tenant scoping:** Invitation's company must match user's membership.

**Success response (204):** No content.

---

### 5.5 `PATCH /companies/{company_id}/members/{user_id}/roles` — Update Member Roles

**Purpose:** Change a member's role assignments.

**Permission:** `member:role:update`

**Tenant scoping:** `company_id` from path.

**Request body:**

```json
{
  "roleIds": ["role-creator-uuid", "role-approver-uuid"]
}
```

**Success response (200):**

```json
{
  "userId": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "roles": ["creator", "approver"]
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 403 | `FORBIDDEN` | Attempting to remove or demote the owner |
| 403 | `FORBIDDEN` | Admin attempting to modify another admin |
| 404 | `NOT_FOUND` | User is not a member of the company |

---

### 5.6 `DELETE /companies/{company_id}/members/{user_id}` — Remove Member

**Purpose:** Remove a member from the company. Takes effect immediately.

**Permission:** `member:remove`

**Tenant scoping:** `company_id` from path.

**Success response (204):** No content.

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 403 | `FORBIDDEN` | Attempting to remove the owner (FR-4.9) |
| 403 | `FORBIDDEN` | Admin attempting to remove another admin |
| 404 | `NOT_FOUND` | User is not a member |

---

## 6. Channels

### 6.1 `GET /companies/{company_id}/channels` — List Channels

**Purpose:** Return all connected channels for the company.

**Permission:** `channel:list`

**Tenant scoping:** `company_id` from path.

**Success response (200):**

```json
{
  "data": [
    {
      "id": "chan-uuid",
      "telegramChannelId": -1001234567890,
      "title": "Acme Official",
      "username": "acme_official",
      "type": "channel",
      "memberCount": 1523,
      "status": "active",
      "connectedAt": "2026-10-02T09:00:00Z"
    }
  ],
  "pagination": { "limit": 20, "offset": 0, "total": 1 }
}
```

---

### 6.2 `POST /companies/{company_id}/channels/connect` — Start Channel Connection

**Purpose:** Initiate channel connection. Returns a verification code and instructions.

**Permission:** `channel:connect`

**Tenant scoping:** `company_id` from path. Company must be `active`.

**Request body:**

```json
{
  "telegramChannelId": -1001234567890
}
```

**Success response (200):**

```json
{
  "verificationCode": "ACM-7X4K",
  "instructions": "1. Add @SocialPilotBot as admin of your channel.\n2. Forward any message from the channel to the bot.\n3. The bot will verify and complete the connection.",
  "expiresAt": "2026-10-11T13:00:00Z"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 400 | `VALIDATION_ERROR` | Invalid channel ID format |
| 403 | `FORBIDDEN` | Company not active |
| 409 | `CONFLICT` | Channel already connected to another company |
| 409 | `CONFLICT` | Channel already connected to this company |

---

### 6.3 `POST /channels/{channel_id}/verify` — Verify Channel Connection

**Purpose:** Complete channel connection after bot admin verification.

**Permission:** `channel:verify`

**Tenant scoping:** Channel's company must match user's membership.

**Success response (200):**

```json
{
  "id": "chan-uuid",
  "title": "Acme Official",
  "username": "acme_official",
  "type": "channel",
  "memberCount": 1523,
  "status": "active",
  "connectedAt": "2026-10-11T12:05:00Z"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 404 | `NOT_FOUND` | Verification code not found or expired |
| 409 | `CONFLICT` | Bot is not admin in the channel |
| 409 | `CONFLICT` | Channel already connected |

---

### 6.4 `DELETE /channels/{channel_id}` — Disconnect Channel

**Purpose:** Disconnect a channel. Historical publications remain.

**Permission:** `channel:disconnect`

**Tenant scoping:** Channel's company must match user's membership.

**Success response (204):** No content.

---

## 7. Posts

### 7.1 `GET /companies/{company_id}/posts` — List Posts

**Purpose:** Return posts with optional filtering.

**Permission:** `post:list`

**Tenant scoping:** `company_id` from path.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | — | Filter by status |
| `authorId` | UUID | — | Filter by author |
| `channelId` | UUID | — | Filter by published channel |
| `from` | date | — | Created after date |
| `to` | date | — | Created before date |
| `search` | string | — | Full-text search on caption |

**Success response (200):**

```json
{
  "data": [
    {
      "id": "post-uuid",
      "status": "published",
      "caption": "Check out our new product line!...",
      "hashtags": ["#acme", "#new"],
      "cta": "Shop now",
      "author": { "id": "user-uuid", "displayName": "John Doe" },
      "mediaCount": 3,
      "createdAt": "2026-10-10T15:00:00Z",
      "updatedAt": "2026-10-10T15:30:00Z"
    }
  ],
  "pagination": { "limit": 20, "offset": 0, "total": 56 }
}
```

---

### 7.2 `POST /companies/{company_id}/posts` — Create Draft

**Purpose:** Create a new post draft.

**Permission:** `post:create`

**Tenant scoping:** `company_id` from path.

**Request body:**

```json
{
  "caption": "Check out our new product line!",
  "hashtags": ["#acme", "#new"],
  "cta": "Shop now",
  "mediaIds": ["media-uuid-1", "media-uuid-2"]
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `caption` | string | No* | Max 1024 chars (Telegram limit) |
| `hashtags` | string[] | No | Max 10 items |
| `cta` | string | No | Max 255 chars |
| `mediaIds` | UUID[] | No | Max 10 items (FR-11.4) |

*At least one of `caption` or `mediaIds` must be present.

**Success response (201):**

```json
{
  "id": "post-uuid",
  "companyId": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "status": "draft",
  "caption": "Check out our new product line!",
  "hashtags": ["#acme", "#new"],
  "cta": "Shop now",
  "authorUserId": "550e8400-e29b-41d4-a716-446655440000",
  "media": [
    { "mediaId": "media-uuid-1", "position": 0 },
    { "mediaId": "media-uuid-2", "position": 1 }
  ],
  "createdAt": "2026-10-11T12:00:00Z"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 400 | `VALIDATION_ERROR` | Caption too long, too many media items, etc. |
| 403 | `FORBIDDEN` | User lacks `post:create` |
| 404 | `NOT_FOUND` | One or more media IDs do not exist in this company |

---

### 7.3 `GET /posts/{post_id}` — Get Post Details

**Purpose:** Return full post details including media and revision history.

**Permission:** `post:view`

**Tenant scoping:** Post's company must match user's membership.

**Success response (200):**

```json
{
  "id": "post-uuid",
  "status": "in_review",
  "caption": "Check out our new product line!",
  "hashtags": ["#acme", "#new"],
  "cta": "Shop now",
  "author": { "id": "user-uuid", "displayName": "John Doe" },
  "media": [
    {
      "mediaId": "media-uuid-1",
      "position": 0,
      "previewUrl": "/api/v1/media/media-uuid-1/preview",
      "mimeType": "image/jpeg",
      "width": 1080,
      "height": 1080
    }
  ],
  "revisions": [
    {
      "version": 2,
      "caption": "Check out our new product line!",
      "author": { "id": "user-uuid", "displayName": "John Doe" },
      "createdAt": "2026-10-11T12:05:00Z"
    },
    {
      "version": 1,
      "caption": "New product line!",
      "author": { "id": "user-uuid", "displayName": "John Doe" },
      "createdAt": "2026-10-11T12:00:00Z"
    }
  ],
  "approvalHistory": [
    {
      "action": "submit",
      "actor": { "id": "user-uuid", "displayName": "John Doe" },
      "createdAt": "2026-10-11T12:10:00Z"
    }
  ],
  "createdAt": "2026-10-11T12:00:00Z",
  "updatedAt": "2026-10-11T12:10:00Z"
}
```

---

### 7.4 `PATCH /posts/{post_id}` — Update Post

**Purpose:** Edit caption, hashtags, CTA, or media. Creates a new revision.

**Permission:** `post:update` (own drafts for creator; any post for owner/admin/approver)

**Tenant scoping:** Post's company must match user's membership.

**Request body:** Same fields as create, all optional.

**Success response (200):** Updated post object with new revision.

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 400 | `VALIDATION_ERROR` | Invalid field values |
| 403 | `FORBIDDEN` | User lacks permission or post is not in editable state |
| 404 | `NOT_FOUND` | Post not found or no membership |
| 409 | `CONFLICT` | Post is in `publishing` or `published` state |

---

### 7.5 `DELETE /posts/{post_id}` — Cancel/Delete Post

**Purpose:** Soft-delete a draft (sets status to `cancelled`).

**Permission:** `post:delete`

**Tenant scoping:** Post's company must match user's membership.

**Success response (204):** No content.

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 403 | `FORBIDDEN` | Post is published or in publishing |
| 404 | `NOT_FOUND` | Post not found or already cancelled |

---

### 7.6 `GET /posts/{post_id}/revisions` — Get Revision History

**Purpose:** Return all revisions for a post.

**Permission:** `post:view`

**Tenant scoping:** Post's company must match user's membership.

**Success response (200):**

```json
{
  "data": [
    {
      "version": 3,
      "caption": "Final version",
      "hashtags": ["#acme"],
      "cta": "Shop now",
      "author": { "id": "user-uuid", "displayName": "John Doe" },
      "createdAt": "2026-10-11T12:15:00Z"
    }
  ],
  "pagination": { "limit": 20, "offset": 0, "total": 3 }
}
```

---

## 8. Media

### 8.1 `POST /companies/{company_id}/media/upload` — Upload Media

**Purpose:** Upload one or more image files.

**Permission:** `media:upload`

**Tenant scoping:** `company_id` from path.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files` | File[] | Yes | 1–10 image files |

**Validation (per file):**

- MIME type: `image/jpeg`, `image/png`, `image/webp`, `image/gif`
- Magic bytes must match declared MIME type
- Max size: 10 MB per file
- Max count: 10 files per request

**Success response (201):**

```json
{
  "uploaded": [
    {
      "id": "media-uuid-1",
      "previewUrl": "/api/v1/media/media-uuid-1/preview",
      "mimeType": "image/jpeg",
      "fileSizeBytes": 2048576,
      "width": 1080,
      "height": 1080
    }
  ],
  "failed": [
    {
      "filename": "malware.jpg",
      "error": "File signature does not match declared MIME type"
    }
  ]
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 400 | `VALIDATION_ERROR` | No files provided |
| 413 | `FILE_TOO_LARGE` | File exceeds 10 MB |
| 415 | `UNSUPPORTED_MEDIA_TYPE` | MIME type not allowed |
| 422 | `UNPROCESSABLE` | Magic bytes mismatch |

**Idempotency:** Not idempotent. Each upload creates new media assets.

---

### 8.2 `GET /companies/{company_id}/media` — List Media Assets

**Purpose:** Return media library for the company.

**Permission:** `media:list`

**Tenant scoping:** `company_id` from path.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | string | — | Filter by `upload` or `ai_generated` |
| `from` | date | — | Uploaded after date |
| `to` | date | — | Uploaded before date |

**Success response (200):**

```json
{
  "data": [
    {
      "id": "media-uuid-1",
      "previewUrl": "/api/v1/media/media-uuid-1/preview",
      "mimeType": "image/jpeg",
      "fileSizeBytes": 2048576,
      "width": 1080,
      "height": 1080,
      "source": "upload",
      "uploadedBy": { "id": "user-uuid", "displayName": "John Doe" },
      "createdAt": "2026-10-10T10:00:00Z"
    }
  ],
  "pagination": { "limit": 20, "offset": 0, "total": 42 }
}
```

---

### 8.3 `GET /media/{media_id}/preview` — Get Media Preview

**Purpose:** Redirect to or stream the media file.

**Permission:** `media:list`

**Tenant scoping:** Media's company must match user's membership.

**Success response (200):** Binary image data with appropriate `Content-Type`.

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 404 | `NOT_FOUND` | Media not found or no membership |

---

### 8.4 `DELETE /media/{media_id}` — Delete Media Asset

**Purpose:** Soft-delete a media asset. Hard delete after 30 days.

**Permission:** `media:delete` (own uploads for creator; any for owner/admin)

**Tenant scoping:** Media's company must match user's membership.

**Success response (204):** No content.

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 403 | `FORBIDDEN` | Media is attached to a non-cancelled post |
| 404 | `NOT_FOUND` | Media not found or no membership |

---

## 9. AI

### 9.1 `POST /companies/{company_id}/ai/text` — Generate Text

**Purpose:** Generate post text using Gemini with brand context.

**Permission:** `ai:text:generate`

**Tenant scoping:** `company_id` from path. Company must be `active`.

**Request body:**

```json
{
  "topic": "New product launch",
  "goal": "Drive traffic to the product page",
  "audience": "Tech-savvy consumers aged 25-45",
  "tone": "professional",
  "language": "en",
  "length": "medium",
  "cta": "Shop now",
  "hashtags": ["#acme", "#new"],
  "campaignNotes": "Emphasize the 30-day money-back guarantee"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | Yes | Subject of the post |
| `goal` | string | No | Desired outcome |
| `audience` | string | No | Target audience (overrides brand default) |
| `tone` | string | No | Tone override |
| `language` | string | No | Language override |
| `length` | string | No | `short`, `medium`, `long` |
| `cta` | string | No | Call-to-action override |
| `hashtags` | string[] | No | Hashtag override |
| `campaignNotes` | string | No | Additional context |

**Success response (200):**

```json
{
  "text": "Excited to announce our latest innovation!...",
  "usage": {
    "promptTokens": 156,
    "completionTokens": 89,
    "totalTokens": 245
  }
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 403 | `FORBIDDEN` | User lacks `ai:text:generate` |
| 429 | `RATE_LIMITED` | Per-user or per-company rate limit exceeded |
| 502 | `PROVIDER_ERROR` | Gemini API failure |
| 503 | `SERVICE_UNAVAILABLE` | No text provider configured |

**Idempotency:** Not idempotent. Each call generates new text and records usage.

---

### 9.2 `POST /companies/{company_id}/ai/image` — Generate Image

**Purpose:** Generate images using the configured image provider.

**Permission:** `ai:image:generate`

**Tenant scoping:** `company_id` from path. Company must be `active`.

**Request body:**

```json
{
  "prompt": "A modern minimalist product photo of a wireless headphone",
  "aspectRatio": "1:1",
  "count": 2
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `prompt` | string | Yes | Max 1000 chars |
| `aspectRatio` | string | No | `1:1`, `16:9`, `9:16`, `4:3` |
| `count` | integer | No | 1–4 (provider limit) |

**Success response (200):**

```json
{
  "images": [
    {
      "id": "img-result-1",
      "url": "/api/v1/ai/image-results/img-result-1",
      "width": 1024,
      "height": 1024
    },
    {
      "id": "img-result-2",
      "url": "/api/v1/ai/image-results/img-result-2",
      "width": 1024,
      "height": 1024
    }
  ],
  "usage": {
    "imagesGenerated": 2
  }
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 403 | `FORBIDDEN` | User lacks `ai:image:generate` |
| 429 | `RATE_LIMITED` | Rate limit exceeded |
| 502 | `PROVIDER_ERROR` | Image provider failure |
| 503 | `SERVICE_UNAVAILABLE` | No image provider configured (FR-7.7) |

---

### 9.3 `POST /ai/image-results/{result_id}/keep` — Keep Generated Image

**Purpose:** Save a generated image as a company media asset.

**Permission:** `media:upload`

**Tenant scoping:** Image result must belong to the user's generation request.

**Success response (201):**

```json
{
  "id": "media-uuid",
  "previewUrl": "/api/v1/media/media-uuid/preview",
  "mimeType": "image/png",
  "source": "ai_generated"
}
```

---

## 10. Approvals

### 10.1 `POST /posts/{post_id}/submit` — Submit for Review

**Purpose:** Transition post from `draft` or `changes_requested` to `in_review`.

**Permission:** `approval:submit`

**Tenant scoping:** Post's company must match user's membership.

**Success response (200):**

```json
{
  "id": "post-uuid",
  "status": "in_review"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 403 | `FORBIDDEN` | User lacks `approval:submit` |
| 409 | `CONFLICT` | Post is not in `draft` or `changes_requested` state |
| 422 | `UNPROCESSABLE` | Post has no caption and no media |

---

### 10.2 `POST /posts/{post_id}/approve` — Approve Post

**Purpose:** Transition post from `in_review` to `approved`.

**Permission:** `approval:review`

**Tenant scoping:** Post's company must match user's membership.

**Success response (200):**

```json
{
  "id": "post-uuid",
  "status": "approved"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 403 | `FORBIDDEN` | User lacks `approval:review` |
| 409 | `CONFLICT` | Post is not `in_review` |
| 409 | `CONFLICT` | Approver is the sole author and policy requires separation |

---

### 10.3 `POST /posts/{post_id}/reject` — Reject Post

**Purpose:** Transition post to `rejected` (terminal state).

**Permission:** `approval:review`

**Tenant scoping:** Post's company must match user's membership.

**Request body:**

```json
{
  "reason": "Caption contains unverified pricing claims"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `reason` | string | Yes | Max 1000 chars |

**Success response (200):**

```json
{
  "id": "post-uuid",
  "status": "rejected"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 400 | `VALIDATION_ERROR` | Missing reason |
| 403 | `FORBIDDEN` | User lacks `approval:review` |
| 409 | `CONFLICT` | Post is not `in_review` |

---

### 10.4 `POST /posts/{post_id}/request-changes` — Request Changes

**Purpose:** Return post to `changes_requested` with a reason.

**Permission:** `approval:review`

**Tenant scoping:** Post's company must match user's membership.

**Request body:**

```json
{
  "reason": "Please make the tone more casual and add a question to drive engagement"
}
```

**Success response (200):**

```json
{
  "id": "post-uuid",
  "status": "changes_requested"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 400 | `VALIDATION_ERROR` | Missing reason |
| 403 | `FORBIDDEN` | User lacks `approval:review` |
| 409 | `CONFLICT` | Post is not `in_review` |

---

### 10.5 `GET /companies/{company_id}/approvals/queue` — Get Approval Queue

**Purpose:** Return posts in `in_review` status.

**Permission:** `approval:review`

**Tenant scoping:** `company_id` from path.

**Success response (200):**

```json
{
  "data": [
    {
      "id": "post-uuid",
      "caption": "Check out our new product line!",
      "author": { "id": "user-uuid", "displayName": "John Doe" },
      "mediaCount": 3,
      "submittedAt": "2026-10-11T12:10:00Z"
    }
  ],
  "pagination": { "limit": 20, "offset": 0, "total": 5 }
}
```

---

## 11. Publishing

### 11.1 `POST /posts/{post_id}/publish` — Publish Post

**Purpose:** Publish an approved post to a connected channel.

**Permission:** `publish:execute`

**Tenant scoping:** Post and channel must belong to the same company; user must have membership.

**Headers:**

| Header | Required | Description |
|--------|----------|-------------|
| `Idempotency-Key` | Recommended | Client-generated UUID for deduplication |

**Request body:**

```json
{
  "channelId": "chan-uuid"
}
```

**Success response (200):**

```json
{
  "postId": "post-uuid",
  "status": "published",
  "channel": {
    "id": "chan-uuid",
    "title": "Acme Official"
  },
  "telegramMessageIds": [12345, 12346, 12347],
  "publishedAt": "2026-10-11T12:30:00Z"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 403 | `FORBIDDEN` | User lacks `publish:execute` |
| 404 | `NOT_FOUND` | Post or channel not found, or no membership |
| 409 | `CONFLICT` | Post is not `approved` |
| 409 | `CONFLICT` | Channel is disconnected |
| 422 | `UNPROCESSABLE` | Approval policy not satisfied |
| 422 | `UNPROCESSABLE` | Media validation failed (corrupted file, etc.) |
| 502 | `PROVIDER_ERROR` | Telegram API failure |

**Idempotency:** Idempotent with `Idempotency-Key`. Retries with the same key return the original result without re-sending to Telegram (FR-11.8).

---

### 11.2 `GET /companies/{company_id}/publishing/history` — Get Publication History

**Purpose:** Return publication results with filtering.

**Permission:** `post:list`

**Tenant scoping:** `company_id` from path.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `channelId` | UUID | — | Filter by channel |
| `status` | string | — | `success`, `partial`, `failed` |
| `from` | date | — | Published after date |
| `to` | date | — | Published before date |

**Success response (200):**

```json
{
  "data": [
    {
      "postId": "post-uuid",
      "postCaption": "Check out our new product line!...",
      "channel": { "id": "chan-uuid", "title": "Acme Official" },
      "status": "success",
      "telegramMessageIds": [12345, 12346],
      "publishedAt": "2026-10-10T15:30:00Z"
    }
  ],
  "pagination": { "limit": 20, "offset": 0, "total": 48 }
}
```

---

### 11.3 `GET /companies/{company_id}/calendar` — Get Content Calendar

**Purpose:** Return posts organized by date for calendar view.

**Permission:** `post:list`

**Tenant scoping:** `company_id` from path.

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `month` | string | Yes | Format: `YYYY-MM` |

**Success response (200):**

```json
{
  "month": "2026-10",
  "days": [
    {
      "date": "2026-10-10",
      "posts": [
        {
          "id": "post-uuid",
          "status": "published",
          "caption": "Check out our new product line!...",
          "channel": { "id": "chan-uuid", "title": "Acme Official" },
          "publishedAt": "2026-10-10T15:30:00Z"
        }
      ]
    },
    {
      "date": "2026-10-15",
      "posts": [
        {
          "id": "post-uuid-2",
          "status": "approved",
          "caption": "Upcoming webinar announcement",
          "channel": null
        }
      ]
    }
  ]
}
```

---

## 12. Notifications

### 12.1 `GET /companies/{company_id}/notifications` — List Notifications

**Purpose:** Return notifications for the authenticated user in this company.

**Permission:** `notification:view`

**Tenant scoping:** `company_id` from path.

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `unreadOnly` | boolean | false | Filter to unread only |

**Success response (200):**

```json
{
  "data": [
    {
      "id": "notif-uuid",
      "type": "post_approved",
      "title": "Post Approved",
      "body": "Your post 'Check out our new...' has been approved.",
      "entityType": "post",
      "entityId": "post-uuid",
      "isRead": false,
      "createdAt": "2026-10-11T12:20:00Z"
    }
  ],
  "pagination": { "limit": 20, "offset": 0, "total": 12 }
}
```

---

### 12.3 `POST /notifications/{notification_id}/read` — Mark as Read

**Purpose:** Mark a notification as read.

**Permission:** `notification:view`

**Tenant scoping:** Notification must belong to the authenticated user.

**Success response (204):** No content.

---

### 12.4 `POST /notifications/read-all` — Mark All as Read

**Purpose:** Mark all notifications as read for the authenticated user in a company.

**Permission:** `notification:view`

**Tenant scoping:** `company_id` from query parameter.

**Query parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `companyId` | UUID | Yes | Company context |

**Success response (204):** No content.

---

### 12.5 `PUT /companies/{company_id}/notification-preferences` — Update Notification Preferences

**Purpose:** Configure notification settings for the authenticated user.

**Permission:** `notification:view`

**Tenant scoping:** `company_id` from path.

**Request body:**

```json
{
  "inApp": true,
  "telegram": false
}
```

**Success response (200):**

```json
{
  "inApp": true,
  "telegram": false
}
```

---

## 13. Owner Admin

All endpoints in this group require `platform_owner` role. The platform owner has no company membership; authorization is checked via the `platform_*` permission set.

### 13.1 `GET /owner-admin/companies` — List All Companies

**Purpose:** Platform-wide company listing with filtering.

**Permission:** `platform:metrics:view`

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | — | Filter by status |
| `search` | string | — | Search by name |
| `from` | date | — | Created after date |
| `to` | date | — | Created before date |

**Success response (200):**

```json
{
  "data": [
    {
      "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "name": "Acme Corp",
      "status": "active",
      "industry": "E-commerce",
      "owner": { "id": "user-uuid", "displayName": "John Doe" },
      "memberCount": 5,
      "channelCount": 2,
      "postCount": 48,
      "createdAt": "2026-10-01T10:00:00Z"
    }
  ],
  "pagination": { "limit": 20, "offset": 0, "total": 137 }
}
```

---

### 13.2 `GET /owner-admin/companies/pending` — Get Pending Companies

**Purpose:** Return companies awaiting approval.

**Permission:** `platform:company:approve`

**Success response (200):** Same format as list, filtered to `status=pending`.

---

### 13.3 `GET /owner-admin/companies/{company_id}` — Get Company Details (Admin)

**Purpose:** Full company details including members, channels, and usage.

**Permission:** `platform:metrics:view`

**Success response (200):**

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "name": "Acme Corp",
  "status": "active",
  "industry": "E-commerce",
  "website": "https://acme.example.com",
  "country": "US",
  "contactEmail": "owner@acme.example.com",
  "owner": { "id": "user-uuid", "displayName": "John Doe", "username": "johndoe" },
  "members": [
    { "id": "user-uuid", "displayName": "John Doe", "roles": ["company_owner"] }
  ],
  "channels": [
    { "id": "chan-uuid", "title": "Acme Official", "status": "active" }
  ],
  "usage": {
    "textGenerations": 142,
    "imageGenerations": 38,
    "postsCreated": 56,
    "postsPublished": 48
  },
  "createdAt": "2026-10-01T10:00:00Z"
}
```

---

### 13.4 `POST /owner-admin/companies/{company_id}/approve` — Approve Company

**Purpose:** Transition company from `pending` to `active`.

**Permission:** `platform:company:approve`

**Success response (200):**

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "status": "active"
  "approvedAt": "2026-10-11T12:00:00Z"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 409 | `CONFLICT` | Company is not in `pending` or `info_requested` state |

---

### 13.5 `POST /owner-admin/companies/{company_id}/reject` — Reject Company

**Purpose:** Transition company to `rejected`.

**Permission:** `platform:company:approve`

**Request body:**

```json
{
  "reason": "Company name violates trademark policy"
}
```

**Success response (200):**

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "status": "rejected"
}
```

---

### 13.6 `POST /owner-admin/companies/{company_id}/request-info` — Request More Info

**Purpose:** Transition company to `info_requested`.

**Permission:** `platform:company:approve`

**Request body:**

```json
{
  "reason": "Please provide a valid business registration number"
}
```

**Success response (200):**

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "status": "info_requested"
}
```

---

### 13.7 `POST /owner-admin/companies/{company_id}/suspend` — Suspend Company

**Purpose:** Suspend an active company.

**Permission:** `platform:company:suspend`

**Request body:**

```json
{
  "reason": "Violation of content policy"
}
```

**Success response (200):**

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "status": "suspended"
}
```

---

### 13.8 `POST /owner-admin/companies/{company_id}/delete` — Delete Company

**Purpose:** Permanently delete a company after export.

**Permission:** `platform:company:suspend`

**Success response (202):**

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "status": "cancelled",
  "deletionScheduledAt": "2026-10-12T12:00:00Z",
  "exportUrl": "/api/v1/owner-admin/exports/export-uuid"
}
```

---

### 13.9 `GET /owner-admin/metrics` — Platform Metrics

**Purpose:** Platform-wide health and usage metrics.

**Permission:** `platform:metrics:view`

**Success response (200):**

```json
{
  "totalCompanies": 137,
  "activeCompanies": 112,
  "pendingCompanies": 8,
  "suspendedCompanies": 3,
  "totalUsers": 456,
  "totalPosts": 5234,
  "totalPublished": 4102,
  "aiUsage": {
    "textGenerations24h": 892,
    "imageGenerations24h": 156
  },
  "topIndustries": [
    { "industry": "E-commerce", "count": 34 },
    { "industry": "SaaS", "count": 28 }
  ]
}
```

---

### 13.10 `GET /owner-admin/audit-logs` — View Audit Logs

**Purpose:** Platform-wide audit log access.

**Permission:** `platform:metrics:view`

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `companyId` | UUID | — | Filter by company |
| `actorId` | UUID | — | Filter by actor |
| `action` | string | — | Filter by action |
| `from` | date | — | After date |
| `to` | date | — | Before date |

**Success response (200):**

```json
{
  "data": [
    {
      "id": "audit-uuid",
      "companyId": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "actor": { "id": "user-uuid", "displayName": "John Doe" },
      "action": "company.approved",
      "entityType": "company",
      "entityId": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "createdAt": "2026-10-11T12:00:00Z"
    }
  ],
  "pagination": { "limit": 20, "offset": 0, "total": 1234 }
}
```

---

## 14. Endpoint Summary

### 14.1 MVP Endpoints

| Group | Endpoint | Method | Permission |
|-------|----------|--------|------------|
| Auth | `/auth/telegram` | POST | Public |
| Auth | `/auth/me` | GET | Authenticated |
| Auth | `/auth/switch-company` | POST | Authenticated |
| Companies | `/companies` | POST | Authenticated |
| Companies | `/companies/{company_id}` | GET | `company:view` |
| Companies | `/companies/{company_id}` | PATCH | `company:update` |
| Companies | `/companies/{company_id}/brand` | PUT | `brand:update` |
| Companies | `/companies/{company_id}/suspend` | POST | `company:deactivate` |
| Companies | `/companies/{company_id}/usage` | GET | `usage:view` |
| Members | `/companies/{company_id}/members` | GET | `member:list` |
| Members | `/companies/{company_id}/invitations` | POST | `member:invite` |
| Members | `/invitations/{id}/accept` | POST | Authenticated |
| Members | `/invitations/{id}` | DELETE | `member:invite` |
| Members | `/companies/{company_id}/members/{user_id}/roles` | PATCH | `member:role:update` |
| Members | `/companies/{company_id}/members/{user_id}` | DELETE | `member:remove` |
| Channels | `/companies/{company_id}/channels` | GET | `channel:list` |
| Channels | `/companies/{company_id}/channels/connect` | POST | `channel:connect` |
| Channels | `/channels/{channel_id}/verify` | POST | `channel:verify` |
| Channels | `/channels/{channel_id}` | DELETE | `channel:disconnect` |
| Posts | `/companies/{company_id}/posts` | GET | `post:list` |
| Posts | `/companies/{company_id}/posts` | POST | `post:create` |
| Posts | `/posts/{post_id}` | GET | `post:view` |
| Posts | `/posts/{post_id}` | PATCH | `post:update` |
| Posts | `/posts/{post_id}` | DELETE | `post:delete` |
| Posts | `/posts/{post_id}/revisions` | GET | `post:view` |
| Media | `/companies/{company_id}/media/upload` | POST | `media:upload` |
| Media | `/companies/{company_id}/media` | GET | `media:list` |
| Media | `/media/{media_id}/preview` | GET | `media:list` |
| Media | `/media/{media_id}` | DELETE | `media:delete` |
| AI | `/companies/{company_id}/ai/text` | POST | `ai:text:generate` |
| AI | `/companies/{company_id}/ai/image` | POST | `ai:image:generate` |
| AI | `/ai/image-results/{result_id}/keep` | POST | `media:upload` |
| Approvals | `/posts/{post_id}/submit` | POST | `approval:submit` |
| Approvals | `/posts/{post_id}/approve` | POST | `approval:review` |
| Approvals | `/posts/{post_id}/reject` | POST | `approval:review` |
| Approvals | `/posts/{post_id}/request-changes` | POST | `approval:review` |
| Approvals | `/companies/{company_id}/approvals/queue` | GET | `approval:review` |
| Publishing | `/posts/{post_id}/publish` | POST | `publish:execute` |
| Publishing | `/companies/{company_id}/publishing/history` | GET | `post:list` |
| Publishing | `/companies/{company_id}/calendar` | GET | `post:list` |
| Notifications | `/companies/{company_id}/notifications` | GET | `notification:view` |
| Notifications | `/notifications/{id}/read` | POST | `notification:view` |
| Notifications | `/notifications/read-all` | POST | `notification:view` |
| Notifications | `/companies/{company_id}/notification-preferences` | PUT | `notification:view` |
| Owner Admin | `/owner-admin/companies` | GET | `platform:metrics:view` |
| Owner Admin | `/owner-admin/companies/pending` | GET | `platform:company:approve` |
| Owner Admin | `/owner-admin/companies/{company_id}` | GET | `platform:metrics:view` |
| Owner Admin | `/owner-admin/companies/{company_id}/approve` | POST | `platform:company:approve` |
| Owner Admin | `/owner-admin/companies/{company_id}/reject` | POST | `platform:company:approve` |
| Owner Admin | `/owner-admin/companies/{company_id}/request-info` | POST | `platform:company:approve` |
| Owner Admin | `/owner-admin/companies/{company_id}/suspend` | POST | `platform:company:suspend` |
| Owner Admin | `/owner-admin/companies/{company_id}/delete` | POST | `platform:company:suspend` |
| Owner Admin | `/owner-admin/metrics` | GET | `platform:metrics:view` |
| Owner Admin | `/owner-admin/audit-logs` | GET | `platform:metrics:view` |

### 14.2 Future Extension Endpoints (Post-MVP)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/posts/{post_id}/schedule` | POST | Schedule a post for future publishing |
| `/posts/{post_id}/unschedule` | POST | Cancel a scheduled post |
| `/companies/{company_id}/subscription` | GET | Get subscription details |
| `/companies/{company_id}/subscription/upgrade` | POST | Change subscription plan |
| `/owner-admin/plans` | CRUD | Manage subscription plans |
| `/owner-admin/providers` | PUT | Configure AI provider settings |
| `/companies/{company_id}/analytics/engagement` | GET | Advanced engagement analytics |
| `/companies/{company_id}/export` | POST | On-demand data export |
| `/posts/{post_id}/duplicate` | POST | Duplicate a post as new draft |
| `/companies/{company_id}/members/{user_id}/transfer-ownership` | POST | Transfer company ownership |

---

## 15. Rate Limits

| Scope | Limit | Window | Applies To |
|-------|-------|--------|------------|
| AI text generation | 20 requests | 1 minute | Per user |
| AI text generation | 200 requests | 1 hour | Per company |
| AI image generation | 10 requests | 1 minute | Per user |
| Media upload | 50 files | 1 hour | Per company |
| Auth | 10 requests | 1 minute | Per IP |
| General API | 300 requests | 1 minute | Per user |

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1697020800
```

---

## 16. Versioning

- The API version is in the URL path: `/api/v1/...`
- Breaking changes require a new version (`/api/v2/...`)
- Deprecations are announced via `Deprecation` and `Sunset` response headers
- Minimum supported version: `v1`
