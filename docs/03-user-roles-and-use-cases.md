# User Roles and Use Cases

This document defines the user types, the role-based access control (RBAC) model, explicit permissions, and the primary use cases for SocialPilot AI.

## User Types Overview

SocialPilot AI has two conceptual planes:

1. **Platform plane** — operated by the Platform Owner. Global scope across all companies.
2. **Company plane** — operated by company members inside isolated workspaces.

A single Telegram account is one `user`. A user may belong to zero, one, or many companies via `company_memberships`, and may hold different roles in each.

## Role Definitions

SocialPilot AI defines exactly three roles:

| Role | Scope | Description |
|------|-------|-------------|
| **Platform Owner** | Platform | Global platform administration, company registration approval/rejection, and company suspension/reactivation |
| **Company Admin** | Company | Company workspace, team management, Telegram channel connections, AI settings, post review and approval, scheduling, publishing, and publishing history |
| **Content Creator** | Company | AI content generation, media uploads, draft creation/editing, and submitting posts for admin approval |

> **Note:** Platform Owner is **not** a company role. The platform owner has no implicit membership in any company and does not appear in company member lists. Platform owner authorization is checked separately from company membership.

## Permission Model

Permissions are explicit action strings of the form `resource:action`. Roles are named bundles of permissions.

### Permission Catalog

| Permission | Description | Default roles |
|------------|-------------|---------------|
| `company:view` | View company profile and workspace | Company Admin, Content Creator |
| `company:update` | Update company profile | Company Admin |
| `company:deactivate` | Deactivate the company (self-suspend) | Company Admin |
| `brand:view` | View brand profile | Company Admin, Content Creator |
| `brand:update` | Update brand profile | Company Admin |
| `member:invite` | Invite members | Company Admin |
| `member:list` | List members | Company Admin |
| `member:role:update` | Change member roles | Company Admin |
| `member:remove` | Remove members | Company Admin |
| `channel:connect` | Start/complete channel connection | Company Admin |
| `channel:verify` | Verify channel ownership | Company Admin |
| `channel:list` | List connected channels | Company Admin, Content Creator |
| `channel:disconnect` | Disconnect a channel | Company Admin |
| `post:create` | Create a draft | Company Admin, Content Creator |
| `post:list` | List posts | Company Admin, Content Creator |
| `post:view` | View a post and revisions | Company Admin, Content Creator |
| `post:update` | Edit caption/media/settings | Company Admin, Content Creator (own drafts) |
| `post:delete` | Cancel/soft-delete a draft | Company Admin, Content Creator (own drafts) |
| `ai:text:generate` | Generate text with AI | Company Admin, Content Creator |
| `ai:image:generate` | Generate images with AI | Company Admin, Content Creator |
| `media:upload` | Upload media | Company Admin, Content Creator |
| `media:list` | List media assets | Company Admin, Content Creator |
| `media:delete` | Delete a media asset | Company Admin, Content Creator (own uploads) |
| `approval:submit` | Submit a post for review | Company Admin, Content Creator |
| `approval:review` | Approve/reject/request changes | Company Admin |
| `publish:execute` | Publish an approved post | Company Admin |
| `schedule:manage` | Schedule posts (future) | Company Admin |
| `usage:view` | View usage and subscription | Company Admin |
| `audit:view` | View audit log | Company Admin |
| `notification:view` | View notifications | Company Admin, Content Creator |
| `platform:company:approve` | Approve/reject companies | Platform Owner only |
| `platform:company:suspend` | Suspend companies | Platform Owner only |
| `platform:company:reactivate` | Reactivate companies | Platform Owner only |
| `platform:provider:configure` | Configure AI providers | Platform Owner only |
| `platform:metrics:view` | View platform metrics | Platform Owner only |

### Role to Permission Bundles

| Role | Permissions |
|------|-------------|
| **Platform Owner** | `platform:company:approve`, `platform:company:suspend`, `platform:company:reactivate`, `platform:provider:configure`, `platform:metrics:view` |
| **Company Admin** | All company-scoped permissions (workspace, team, channels, AI, posts, approvals, publishing, scheduling, history) |
| **Content Creator** | `company:view`, `brand:view`, `post:create/list/view/update/delete(own)`, `ai:*:generate`, `media:upload/list/delete(own)`, `approval:submit`, `channel:list`, `notification:view` |

## Authentication vs Authorization

Every protected endpoint enforces two independent checks:

1. **Authentication** - The request carries a valid session token derived from server-validated Telegram `initData`. The token maps to a `user_id`.
2. **Authorization** - The authenticated user has a `company_membership` for the target company with the required permission. The `company_id` is **derived from the user's membership + the resource**, never trusted from the request body alone.

### Sensitive Action Matrix

| Action | Authentication | Authorization Rule |
|--------|----------------|--------------------|
| Approve a company | Valid platform-owner session | `user.telegram_id == PLATFORM_OWNER_TELEGRAM_ID` AND `platform:company:approve` |
| Invite a member | Valid session | Membership in company with `member:invite` |
| Connect a channel | Valid session | Membership with `channel:connect`; company must be `active` |
| Generate text | Valid session | Membership with `ai:text:generate`; company `active`; rate limit OK |
| Submit for approval | Valid session | Membership with `approval:submit`; post belongs to company; post is `draft`/`changes_requested` |
| Approve a post | Valid session | Membership with `approval:review`; post belongs to company; post is `in_review` |
| Publish a post | Valid session | Membership with `publish:execute`; post `approved`; channel belongs to same company |
| Suspend a company | Valid platform-owner session | `platform:company:suspend` |
| View another company's post | Valid session | Membership is checked; **404** returned if no membership (not 403) to avoid ID enumeration |

## Use Cases

### UC-01: Register a Company (Company Admin)
**Actor:** New user (becomes Company Admin)
**Preconditions:** User has authenticated via Telegram; user has no pending duplicate for the same normalized company name.
**Main flow:**
1. User opens Mini App; onboarding shows "Create a company".
2. User submits company name, industry, country, optional website/email.
3. System validates input, creates `company` (`status=pending`) and `company_membership` (Company Admin).
4. User sees pending screen with next steps.
5. Platform Owner approves, company becomes `active`, user notified.
**Alternate flows:** Duplicate name yields validation error; insufficient fields yield field errors.
**Postconditions:** Company exists with Company Admin membership.

### UC-02: Approve a Company (Platform Owner)
**Actor:** Platform Owner
**Preconditions:** At least one `pending` company.
**Main flow:**
1. Platform Owner opens Owner Admin then Pending Companies.
2. Platform Owner reviews details and clicks Approve.
3. System sets `status=active`, records `audit_log`, notifies Company Admin.
**Alternate flows:** Reject with reason transitions to `rejected`; Request more info transitions to `info_requested`.
**Postconditions:** Company state changed; audit event recorded.

### UC-03: Connect a Telegram Channel (Company Admin)
**Actor:** Company Admin
**Preconditions:** Company `active`; bot is admin in the channel.
**Main flow:**
1. User opens Channels then Connect Channel.
2. System generates a one-time verification code and instructions.
3. User forwards a message or uses the bot in the channel; backend verifies bot admin rights via `getChatAdministrators`.
4. System creates `social_channel` and a credential reference.
**Alternate flows:** Bot not admin yields error with instructions; channel already connected yields conflict.
**Postconditions:** Channel available for publishing.

### UC-04: Generate a Text Draft (Content Creator)
**Actor:** Content Creator
**Preconditions:** Company `active`; brand profile exists.
**Main flow:**
1. Content Creator opens Content, New, then AI Text.
2. Fills topic, goal, tone, language, length, CTA, hashtags.
3. Submits; system builds prompt from brand profile plus inputs, calls text provider.
4. System creates a `post` draft and `post_revision` with generated text.
5. Content Creator edits and saves.
**Alternate flows:** Provider error yields clear error with no draft created; rate limit yields 429.
**Postconditions:** Draft exists.

### UC-05: Upload Local Images (Content Creator)
**Actor:** Content Creator
**Preconditions:** Company `active`; file selection supported by client.
**Main flow:**
1. Content Creator opens Media Library or Content editor then Upload.
2. Selects 1 to N images; frontend previews and allows reorder/remove.
3. Frontend uploads each file; backend validates type, signature, size, count.
4. System stores files and creates `media_assets`.
**Alternate flows:** Unsupported client triggers Telegram forwarding fallback; invalid file triggers per-file error.
**Postconditions:** Media assets available.

### UC-06: Submit a Post for Approval (Content Creator)
**Actor:** Content Creator
**Preconditions:** Post in `draft` or `changes_requested`; caption present; media ready.
**Main flow:**
1. Content Creator opens draft then Submit for Review.
2. System transitions post to `in_review`, records `approval_event`.
3. Company Admin is notified.
**Postconditions:** Post awaiting review.

### UC-07: Review and Approve a Post (Company Admin)
**Actor:** Company Admin
**Preconditions:** Post `in_review`; Company Admin has `approval:review`.
**Main flow:**
1. Company Admin opens Approvals queue.
2. Reviews caption and media; may edit caption if permitted.
3. Clicks Approve, post transitions to `approved`; event recorded.
**Alternate flows:** Request changes with reason transitions to `changes_requested`; Reject with reason transitions to `rejected`.
**Postconditions:** Post state advanced.

### UC-08: Publish a Post (Company Admin)
**Actor:** Company Admin
**Preconditions:** Post `approved`; channel belongs to company; policy satisfied.
**Main flow:**
1. Company Admin opens post, clicks Publish, and selects channel.
2. System verifies ownership, permission, policy, media; transitions to `publishing`.
3. System sends message or media group; records `publication_result` with message IDs; post transitions to `published`.
**Alternate flows:** Telegram error returns post to `approved` or `draft`; error recorded; no auto-retry for ambiguous cases.
**Postconditions:** Content published.

### UC-09: View Publication History (Content Creator)
**Actor:** Content Creator
**Preconditions:** Membership with `post:list`.
**Main flow:**
1. Content Creator opens Analytics then History.
2. Filters by channel, date, and status; views message links.
**Postconditions:** Read-only report displayed.

### UC-10: Suspend a Company (Platform Owner)
**Actor:** Platform Owner
**Preconditions:** Company `active`.
**Main flow:**
1. Platform Owner opens Company detail then Suspend.
2. Company transitions to `suspended`; workspace becomes read-only.
3. Members see suspension notice.
**Postconditions:** Company cannot publish; data retained.

## Ownership Transfer and Deletion

- **Ownership transfer** (`FUTURE`): The current Company Admin invites a member to accept ownership. On acceptance, the recipient becomes Company Admin, the previous admin becomes Content Creator. Recorded in `audit_logs`. Until implemented, ownership is fixed to the creator.
- **Company deletion**: Only the Platform Owner may permanently delete. Flow: request deletion, export archive generated, retention window (default 24h), soft-delete, then after grace period, hard-delete cascade. Admin-initiated self-suspension is reversible and retains data.

## Unresolved Questions

Minimum approval policy granularity and self-approval edge cases will be revisited after the three-role foundation is implemented. The current default permits a Company Admin to approve their own post, which supports single-person companies.
