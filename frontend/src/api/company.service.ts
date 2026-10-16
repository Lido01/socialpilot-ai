import { apiClient } from './client';
import {
  CompanyRegistrationRequestCreate,
  CompanyRegistrationRequestResponse,
  CompanyResponse,
} from '@/types/company';

export const companyService = {
  /**
   * Register a new company workspace.
   * Real endpoint: POST /api/v1/companies/register
   */
  async registerCompany(
    data: CompanyRegistrationRequestCreate
  ): Promise<CompanyRegistrationRequestResponse> {
    return apiClient<CompanyRegistrationRequestResponse>('/companies/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * List the current user's registration requests.
   * Real endpoint: GET /api/v1/companies/registrations/me
   */
  async getMyRegistrations(): Promise<CompanyRegistrationRequestResponse[]> {
    return apiClient<CompanyRegistrationRequestResponse[]>('/companies/registrations/me', {
      method: 'GET',
    });
  },

  /**
   * Get company details (requires active membership).
   * Real endpoint: GET /api/v1/companies/{company_id}
   */
  async getCompany(companyId: string): Promise<CompanyResponse> {
    return apiClient<CompanyResponse>(`/companies/${companyId}`, {
      method: 'GET',
    });
  },
};
