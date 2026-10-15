/**
 * Central HTTP client with typed request/response handling,
 * JWT injection, and unified error handling matching backend contracts.
 */

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: Array<{ field?: string; code?: string; message?: string }>;
  request_id?: string;
}

export class ApiError extends Error {
  public statusCode: number;
  public code: string;
  public details?: Array<{ field?: string; code?: string; message?: string }>;
  public requestId?: string;

  constructor(statusCode: number, payload?: ApiErrorPayload | string) {
    if (typeof payload === 'string') {
      super(payload);
      this.statusCode = statusCode;
      this.code = 'API_ERROR';
    } else if (payload && payload.message) {
      super(payload.message);
      this.statusCode = statusCode;
      this.code = payload.code || 'UNKNOWN_ERROR';
      this.details = payload.details;
      this.requestId = payload.request_id;
    } else {
      super(`Request failed with status ${statusCode}`);
      this.statusCode = statusCode;
      this.code = 'HTTP_ERROR';
    }
    this.name = 'ApiError';
  }
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('socialpilot_access_token');
  
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const url = endpoint.startsWith('http')
    ? endpoint
    : `${BASE_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorPayload: ApiErrorPayload | undefined;
      try {
        const errorJson = await response.json();
        // Support both backend { error: { message, code } } and FastAPI default { detail: ... }
        if (errorJson?.error) {
          errorPayload = errorJson.error;
        } else if (errorJson?.detail) {
          if (typeof errorJson.detail === 'string') {
            errorPayload = { code: 'HTTP_ERROR', message: errorJson.detail };
          } else if (Array.isArray(errorJson.detail)) {
            errorPayload = {
              code: 'VALIDATION_ERROR',
              message: errorJson.detail.map((d: any) => d.msg || d.message).join(', '),
              details: errorJson.detail,
            };
          }
        }
      } catch {
        // Fallback if response body is not JSON
      }

      throw new ApiError(response.status, errorPayload || response.statusText);
    }

    // 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(0, {
      code: 'NETWORK_ERROR',
      message: (error as Error).message || 'Unable to connect to the server',
    });
  }
}
