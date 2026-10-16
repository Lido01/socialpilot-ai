/**
 * Platform Owner review and moderation types matching backend schemas
 */

export interface PendingCompanyResponse {
  id: string;
  name: string;
  normalized_name: string;
  industry: string | null;
  website: string | null;
  country: string | null;
  contact_email: string | null;
  status: string;
  user_id: string;
  user_telegram_id: number;
  user_display_name: string;
  user_username: string | null;
  created_at: string;
  updated_at: string;
}

export interface PlatformActionResponse {
  success: boolean;
  message: string;
  company_id?: string | null;
  company_status?: string | null;
}
