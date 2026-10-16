/**
 * Authentication and User Role types matching backend contracts
 */

export type UserRole = 'platform_owner' | 'company_admin' | 'content_owner';

export interface RoleInfo {
  role: UserRole;
  label: string;
  description: string;
}

export const ROLE_CONFIGS: Record<UserRole, RoleInfo> = {
  platform_owner: {
    role: 'platform_owner',
    label: 'Platform Owner',
    description: 'Global administrator: review company registrations and platform health',
  },
  company_admin: {
    role: 'company_admin',
    label: 'Company Admin',
    description: 'Company workspace owner: team management, channel setup, post approvals & publishing',
  },
  content_owner: {
    role: 'content_owner',
    label: 'Content Creator',
    description: 'Creator: drafting posts, generating AI captions, media upload, submission for approval',
  },
};

export interface TelegramAuthRequest {
  init_data: string;
}

export interface TelegramAuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface DecodedJWTPayload {
  sub: string;           // User UUID
  tid: number;           // Telegram numeric ID
  iat: number;
  exp: number;
  type: string;
  iss: string;
  aud: string;
}

export interface UserProfile {
  id: string;
  telegramId: number;
  displayName: string;
  username?: string;
  role: UserRole;
  activeCompanyId?: string;
}
