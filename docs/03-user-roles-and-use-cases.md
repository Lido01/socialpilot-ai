# User Roles and Use Cases

This document defines the user types, the role-based access control (RBAC) model, explicit permissions, and the primary use cases for SocialPilot AI.

## User Types Overview

SocialPilot AI has two conceptual planes:

1. **Platform plane** — operated by the Platform Owner. Global scope across all companies.
2. **Company plane** — operated by company members inside isolated workspaces.

A single Telegram account is one `user`. A user may belong to zero, one, or many companies via `company_memberships`, and may hold different roles in each.

## Role Definitions

| Role | Scope | Description |
|------|-------|-------------|
| `platform_owner` | Platform | Operates the SaaS; approves/suspends companies; configures providers |
| `company_owner` | Company | Original creator of the company; full control; exactly one per company |
| `company_admin` | Company | Manages workspace per assigned permissions; cannot approve companies |
| `creator` | Company | Generates/uploads content, edits drafts, submits for approval |
| `approver` | Company | Reviews content, approves/rejects/requests changes |
| `publisher` | Company | Publishes approved content to connected channels |
| `analyst` | Company | Read-only access to reports, history, and analytics |

> **Note:** `platform_owner` is **not** a company role. The platform owner has no implicit membership in any company and does not appear in company member lists. Platform owner authorization is checked separately from company membership.

## Permission Model

Permissions are explicit action strings of the form `resource:action`. Roles are named bundles of permissions. This lets the platform grant finer-grained access than role labels alone.

### Permission Catalog

| Permission | Description | Default roles |
|------------|-------------|---------------|
| `company:view` | View company profile and workspace | owner, admin, creator, approver, publisher, analyst |
| `company:update` | Update company profile | owner, admin |
| `company:deactivate` | Deactivate the company (self-suspend) | owner |
| `brand:view` | View brand profile | all members |
| `brand:update` | Update brand profile | owner, admin |
| `member:invite` | Invite members | owner, admin |
| `member:list` | List members | owner, admin, analyst |
| `member:role:update` | Change member roles | owner, admin (limited) |
| `member:remove` | Remove members | owner, admin (limited) |
| `channel:connect` | Start/complete channel connection | owner, admin |
| `channel:verify` | Verify channel ownership | owner, admin |
| `channel:list` | List connected channels | all members |
| `channel:disconnect` | Disconnect a channel | owner, admin |
| `post:create` | Create a draft | owner, admin, creator |
| `post:list` | List posts | all members |
| `post:view` | View a post and revisions | all members |
| `post:update` | Edit caption/media/settings | owner, admin, creator (own drafts), approver (if allowed) |
| `post:delete` | Cancel/soft-delete a draft | owner, admin, creator (own drafts) |
| `ai:text:generate` | Generate text with AI | owner, admin, creator |
| `ai:image:generate` | Generate images with AI | owner, admin, creator |
| `media:upload` | Upload media | owner, admin, creator |
| `media:list` | List media assets | all members |
| `media:delete` | Delete a media asset | owner, admin, creator (own uploads) |
| `approval:submit` | Submit a post for review | owner, admin, creator |
| `approval:review` | Approve/reject/request changes | owner, admin, approver |
| `publish:execute` | Publish an approved post | owner, admin, publisher |
| `schedule:manage` | Schedule posts (future) | owner, admin, publisher |
| `usage:view` | View usage and subscription | owner, admin, analyst |
| `audit:view` | View audit log | owner, admin |
| `notification:view` | View notifications | all members |
| `platform:company:approve` | Approve/reject companies | platform_owner only |
| `platform:company:suspend` | Suspend companies | platform_owner only |
| `platform:provider:configure` | Configure AI providers | platform_owner only |
| `platform:metrics:view` | View platform metrics | platform_owner only |

### Role → Permission Bundles

| Role | Permissions |
|------|-------------|
| `company_owner` | All company-scoped permissions |
| `company_admin` | All company-scoped except `company:deactivate`, and with restricted `member:role:update`/`member:remove` (cannot remove or demote the owner) |
| `creator` | `company:view`, `brand:view`, `post:create/list/view/update/delete(own)`, `ai:*:generate`, `media:upload/list/delete(own)`, `approval:submit`, `notification:view`, `channel:list` |
| `approver` | `company:view`, `brand:view`, `post:list/view`, `post:update` (if company config allows), `approval:review`, `notification:view`, `channel:list` |
| `publisher` | `company:view`, `brand:view`, `post:list/view`, `publish:execute`, `schedule:manage`, `notification:view`, `channel:list` |
| `analyst` | `company:view`, `brand:view`, `post:list/view`, `media:list`, `usage:view`, `member:list`, `notification:view`, `channel:list` |

### Multi-Role Membership

A `company_membership` has one or more **role assignments**. A user may hold `creator` and `publisher` simultaneously, enabling them to create and publish (subject to the company approval policy). Roles are stored per membership, so a user can be `creator` in Company A and `analyst` in Company B.

## Authentication vs Authorization

Every protected endpoint enforces two independent checks:

1. **Authentication** — The request carries a valid session token derived from server-validated Telegram `initData`. The token maps to a `user_id`.
2. **Authorization** — The authenticated user has a `company_membership` for the target company with the required permission. The `company_id` is **derived from the user's membership + the resource**, never trusted from the request body alone.

### Sensitive Action Matrix

| Action | Authentication | Authorization Rule |
|--------|----------------|--------------------|
| Approve a company | Valid platform-owner session | `user.telegram_id == PLATFORM_OWNER_TELEGRAM_ID` AND `platform:company:approve` |
| Invite a member | Valid session | Membership in company with `member:invite`; cannot invite above own privilege |
| Connect a channel | Valid session | Membership with `channel:connect`; company must be `active` |
| Generate text | Valid session | Membership with `ai:text:generate`; company `active`; rate limit OK |
| Submit for approval | Valid session | Membership with `approval:submit`; post belongs to company; post is `draft`/`changes_requested` |
| Approve a post | Valid session | Membership with `approval:review`; post belongs to company; post is `in_review`; approver not the sole author if policy requires separation |
| Publish a post | Valid session | Membership with `publish:execute`; post `approved`; channel belongs to same company; approval policy satisfied |
| Suspend a company | Valid platform-owner session | `platform:company:suspend` |
| View another company's post | Valid session | Membership is checked; **404** returned if no membership (not 403) to avoid ID enumeration |

## Use Cases

### UC-01: Register a Company (Company Owner)
**Actor:** New user (becomes `company_owner`)
**Preconditions:** User has authenticated via Telegram; user has no pending duplicate for the same normalized company name.
**Main flow:**
1. User opens Mini App; onboarding shows "Create a company".
2. User submits company name, industry, country, optional website/email.
3. System validates input, creates `company` (`status=pending`) and `company_membership` (`company_owner`).
4. User sees pending screen with next steps.
5. Platform owner approves → company becomes `active` → user notified.
**Alternate flows:** Duplicate name → validation error; insufficient fields → field errors.
**Postconditions:** Company exists with owner membership.

### UC-02: Approve a Company (Platform Owner)
**Actor:** `platform_owner`
**Preconditions:** At least one `pending` company.
**Main flow:**
1. Owner opens Owner Admin → Pending Companies.
2. Owner reviews details and clicks Approve.
3. System sets `status=active`, records `audit_log`, notifies owner.
**Alternate flows:** Reject with reason → `status=rejected`; Request more info → `status=info_requested`.
**Postconditions:** Company state changed; audit event recorded.

### UC-03: Connect a Telegram Channel (Company Owner/Admin)
**Actor:** `company_owner` or `company_admin`
**Preconditions:** Company `active`; bot is admin in the channel.
**Main flow:**
1. User opens Channels → Connect Channel.
2. System generates a one-time verification code and instructions.
3. User forwards a message/uses the bot in the channel; backend verifies bot admin rights via `getChatAdministrators`.
4. System creates `social_channel` and (separately) a credential reference.
**Alternate flows:** Bot not admin → error with instructions; channel already connected → conflict.
**Postconditions:** Channel available for publishing.

### UC-04: Generate a Text Draft (Creator)
**Actor:** `creator`
**Preconditions:** Company `active`; brand profile exists.
**Main flow:**
1. Creator opens Content → New → AI Text.
2. Fills topic, goal, tone, language, length, CTA, hashtags.
3. Submits; system builds prompt from brand profile + inputs, calls text provider.
4. System creates a `post` (draft) + `post_revision` with generated text.
5. Creator edits and saves.
**Alternate flows:** Provider error → clear error, no draft created; rate limited → 429.
**Postconditions:** Draft exists.

### UC-05: Upload Local Images (Creator)
**Actor:** `creator`
**Preconditions:** Company `active`; file selection supported by client.
**Main flow:**
1. Creator opens Media Library or Content editor → Upload.
2. Selects 1..N images; frontend previews and allows reorder/remove.
3. Frontend uploads each file; backend validates type/signature/size/count.
4. System stores files and creates `media_assets`.
**Alternate flows:** Unsupported client → Telegram forwarding fallback; invalid file → per-file error.
**Postconditions:** Media assets available.

### UC-06: Submit a Post for Approval (Creator)
**Actor:** `creator`
**Preconditions:** Post in `draft`/`changes_requested`; caption present; media ready.
**Main flow:**
1. Creator opens draft → Submit for Review.
2. System transitions post to `in_review`, records `approval_event`.
3. Approvers notified.
**Postconditions:** Post awaiting review.

### UC-07: Review and Approve a Post (Approver)
**Actor:** `approver`
**Preconditions:** Post `in_review`; approver has `approval:review`.
**Main flow:**
1. Approver opens Approvals queue.
2. Reviews caption/media; may edit caption if permitted.
3. Clicks Approve → post `approved`; event recorded.
**Alternate flows:** Request changes (reason required) → `changes_requested`; Reject (reason required) → `rejected`.
**Postconditions:** Post state advanced.

### UC-08: Publish a Post (Publisher)
**Actor:** `publisher`
**Preconditions:** Post `approved`; channel belongs to company; policy satisfied.
**Main flow:**
1. Publisher opens post → Publish → selects channel.
2. System verifies ownership, permission, policy, media; transitions to `publishing`.
3. System sends message/media group; records `publication_result` with message IDs; post `published`.
**Alternate flows:** Telegram error → post returns to `approved`/`draft`; error recorded; no auto-retry for ambiguous cases.
**Postconditions:** Content published.

### UC-09: View Publication History (Analyst)
**Actor:** `analyst`
**Preconditions:** Membership with `post:list`.
**Main flow:**
1. Analyst opens Analytics → History.
2. Filters by channel/date/status; views message links.
**Postconditions:** Read-only report displayed.

### UC-10: Suspend a Company (Platform Owner)
**Actor:** `platform_owner`
**Preconditions:** Company `active`.
**Main flow:**
1. Owner opens Company detail → Suspend.
2. Company `status=suspended`; workspace becomes read-only.
3. Members see suspension notice.
**Postconditions:** Company cannot publish; data retained.

## Ownership Transfer and Deletion

- **Ownership transfer** (`FUTURE`): The current owner invites a member to accept ownership. On acceptance, the recipient becomes `company_owner`, the previous owner becomes `company_admin`. Recorded in `audit_logs`. Until implemented, ownership is fixed to the creator.
- **Company deletion**: Only the `platform_owner` may permanently delete. Flow: request deletion → export archive generated → retention window (default 24h) → soft-delete → after grace period, hard-delete cascade. Owner-initiated self-suspension is reversible and retains data.

## Unresolved Questions

⚠️ **UNRESOLVED:** Should a `company_admin` be able to remove another `company_admin`? **Recommended default:** No — only the owner may remove/demote admins. Admins may remove creators/approvers/publishers/analysts.
⚠️ **UNRESOLVED:** Minimum approval policy granularity. **Recommended default:** three presets (see FR-10.6) plus per-post override by owner/admin only.
⚠️ **UNRESOLVED:** Should the approver be blocked from approving their own authored post? **Recommended default:** Configurable; default off for MVP (single-person companies must be able to operate).