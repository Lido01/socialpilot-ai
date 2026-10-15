import { apiClient } from './client';
import { TelegramAuthRequest, TelegramAuthResponse, DecodedJWTPayload } from '@/types/auth';

export const authService = {
  /**
   * Authenticate with raw Telegram initData string.
   * Real endpoint: POST /api/v1/auth/telegram
   */
  async authenticateTelegram(initData: string): Promise<TelegramAuthResponse> {
    const payload: TelegramAuthRequest = { init_data: initData };
    const response = await apiClient<TelegramAuthResponse>('/auth/telegram', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (response?.access_token) {
      localStorage.setItem('socialpilot_access_token', response.access_token);
    }
    return response;
  },

  /**
   * Decode JWT token locally to extract user ID and Telegram ID.
   */
  decodeToken(token: string): DecodedJWTPayload | null {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return null;
      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload);
    } catch {
      return null;
    }
  },

  getToken(): string | null {
    return localStorage.getItem('socialpilot_access_token');
  },

  /**
   * Check if the JWT token is missing, corrupted, or expired.
   */
  isTokenExpired(token: string | null): boolean {
    if (!token) return true;
    const decoded = this.decodeToken(token);
    if (!decoded || !decoded.exp) return true;
    // Buffer of 30 seconds
    return decoded.exp * 1000 <= Date.now() + 30000;
  },

  clearToken(): void {
    localStorage.removeItem('socialpilot_access_token');
  },
};
