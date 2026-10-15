/**
 * Company and registration types matching backend schemas
 */

export type CompanyStatus = 'pending' | 'approved' | 'rejected' | 'active' | 'suspended' | 'info_requested';

export interface CompanyRegistrationRequestCreate {
  name: string;
  industry?: string;
  website?: string;
  country?: string; // 2-letter ISO code e.g. "US", "DE"
  contact_email?: string;
}

export interface CompanyRegistrationRequestResponse {
  id: string;
  name: string;
  normalized_name: string;
  industry: string | null;
  website: string | null;
  country: string | null;
  contact_email: string | null;
  status: CompanyStatus;
  created_at: string;
  updated_at: string;
}

export interface CompanyResponse {
  id: string;
  name: string;
  normalized_name: string;
  industry: string | null;
  website: string | null;
  country: string | null;
  contact_email: string | null;
  status: CompanyStatus;
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  id: string;
  userId: string;
  displayName: string;
  username?: string;
  telegramId: number;
  role: 'company_admin' | 'content_owner';
  isActive: boolean;
  joinedAt: string;
}
