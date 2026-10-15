import { apiClient } from './client';
import { PendingCompanyResponse, PlatformActionResponse } from '@/types/platform';

export const platformService = {
  /**
   * List pending company registration requests.
   * Real endpoint: GET /api/v1/owner-admin/companies/pending
   * Requires: Platform Owner Telegram ID
   */
  async getPendingCompanies(): Promise<PendingCompanyResponse[]> {
    return apiClient<PendingCompanyResponse[]>('/owner-admin/companies/pending', {
      method: 'GET',
    });
  },

  /**
   * Approve a pending company registration.
   * Real endpoint: POST /api/v1/owner-admin/companies/{request_id}/approve
   */
  async approveCompany(requestId: string): Promise<PlatformActionResponse> {
    return apiClient<PlatformActionResponse>(
      `/owner-admin/companies/${requestId}/approve`,
      {
        method: 'POST',
        body: JSON.stringify({}),
      }
    );
  },

  /**
   * Reject a pending company registration.
   * Real endpoint: POST /api/v1/owner-admin/companies/{request_id}/reject
   */
  async rejectCompany(
    requestId: string,
    reason: string
  ): Promise<PlatformActionResponse> {
    return apiClient<PlatformActionResponse>(
      `/owner-admin/companies/${requestId}/reject`,
      {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }
    );
  },

  /**
   * Request more info on a pending company registration.
   * Real endpoint: POST /api/v1/owner-admin/companies/{request_id}/request-info
   */
  async requestMoreInfo(
    requestId: string,
    reason: string
  ): Promise<PlatformActionResponse> {
    return apiClient<PlatformActionResponse>(
      `/owner-admin/companies/${requestId}/request-info`,
      {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }
    );
  },
};
