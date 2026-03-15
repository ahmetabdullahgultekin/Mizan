/**
 * API Error Parsing Utility
 *
 * Converts raw HTTP/network errors into user-friendly messages.
 * Centralises all error string logic so pages stay clean.
 */

import { ApiClientError } from './client';

export interface ParsedApiError {
  /** Short message suitable for a toast or inline alert */
  message: string;
  /** True if the error is a network/connectivity failure (backend unreachable) */
  isNetworkError: boolean;
  /** HTTP status code, or undefined for network errors */
  status?: number;
}

/**
 * Convert any thrown value into a structured, user-friendly error object.
 *
 * Usage:
 *   } catch (err) {
 *     const { message } = parseApiError(err);
 *     setError(message);
 *   }
 */
export function parseApiError(err: unknown): ParsedApiError {
  // Network / fetch failure (no response at all)
  if (err instanceof TypeError && err.message.toLowerCase().includes('fetch')) {
    return {
      message: 'Cannot reach the server. Check that the backend is running.',
      isNetworkError: true,
    };
  }

  if (err instanceof ApiClientError) {
    const status = err.status;

    if (status === 400) {
      return {
        message: err.message || 'Invalid request. Please check your input.',
        isNetworkError: false,
        status,
      };
    }
    if (status === 401 || status === 403) {
      return {
        message: 'Access denied. A valid API key is required.',
        isNetworkError: false,
        status,
      };
    }
    if (status === 404) {
      return {
        message: err.message || 'The requested resource was not found.',
        isNetworkError: false,
        status,
      };
    }
    if (status === 422) {
      // Pydantic validation error — try to surface field detail
      const detail = (err.details as unknown as { detail?: Array<{ msg: string; loc: string[] }> })?.detail;
      if (Array.isArray(detail) && detail.length > 0) {
        const fieldErrors = detail
          .map((d) => `${d.loc?.slice(1).join('.')} — ${d.msg}`)
          .join('; ');
        return {
          message: `Validation error: ${fieldErrors}`,
          isNetworkError: false,
          status,
        };
      }
      return {
        message: 'Validation failed. Please check your input.',
        isNetworkError: false,
        status,
      };
    }
    if (status === 429) {
      return {
        message: 'Too many requests. Please wait a moment before trying again.',
        isNetworkError: false,
        status,
      };
    }
    if (status !== undefined && status >= 500) {
      return {
        message: 'Server error. Please try again later.',
        isNetworkError: false,
        status,
      };
    }

    return {
      message: err.message || 'An unexpected error occurred.',
      isNetworkError: false,
      status,
    };
  }

  // Generic JS error
  if (err instanceof Error) {
    return {
      message: err.message || 'An unexpected error occurred.',
      isNetworkError: false,
    };
  }

  return {
    message: 'An unknown error occurred.',
    isNetworkError: false,
  };
}
