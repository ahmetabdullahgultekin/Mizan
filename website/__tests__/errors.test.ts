/**
 * Unit tests for parseApiError utility.
 */

import { parseApiError } from '@/lib/api/errors';
import { ApiClientError } from '@/lib/api/client';

describe('parseApiError', () => {
  it('returns network error message for fetch TypeError', () => {
    const err = new TypeError('Failed to fetch');
    const result = parseApiError(err);
    expect(result.isNetworkError).toBe(true);
    expect(result.message).toContain('server');
  });

  it('returns 400 message for ApiClientError with status 400', () => {
    const err = new ApiClientError('Bad request', 400, { detail: 'Bad request', status_code: 400 });
    const result = parseApiError(err);
    expect(result.status).toBe(400);
    expect(result.isNetworkError).toBe(false);
  });

  it('returns 403 message for forbidden', () => {
    const err = new ApiClientError('Forbidden', 403, { detail: 'Forbidden', status_code: 403 });
    const result = parseApiError(err);
    expect(result.status).toBe(403);
    expect(result.message).toContain('API key');
  });

  it('returns 404 message for not found', () => {
    const err = new ApiClientError('Not found', 404, { detail: 'Not found', status_code: 404 });
    const result = parseApiError(err);
    expect(result.status).toBe(404);
    expect(result.message).toContain('not found');
  });

  it('returns 429 message for rate limit', () => {
    const err = new ApiClientError('Too many requests', 429, { detail: 'Too many requests', status_code: 429 });
    const result = parseApiError(err);
    expect(result.status).toBe(429);
    expect(result.message).toContain('requests');
  });

  it('returns server error message for 500', () => {
    const err = new ApiClientError('Internal error', 500, { detail: 'Internal error', status_code: 500 });
    const result = parseApiError(err);
    expect(result.status).toBe(500);
    expect(result.message).toContain('Server error');
  });

  it('surfaces field-level validation errors from 422 detail array', () => {
    const err = new ApiClientError('Validation error', 422, {
      detail: [
        { loc: ['body', 'query'], msg: 'field required', type: 'missing' },
      ],
      status_code: 422,
    } as any);
    const result = parseApiError(err);
    expect(result.status).toBe(422);
    expect(result.message).toContain('query');
    expect(result.message).toContain('field required');
  });

  it('handles generic Error', () => {
    const result = parseApiError(new Error('something went wrong'));
    expect(result.message).toBe('something went wrong');
    expect(result.isNetworkError).toBe(false);
  });

  it('handles unknown thrown value', () => {
    const result = parseApiError('unexpected string');
    expect(result.message).toBeDefined();
    expect(result.isNetworkError).toBe(false);
  });
});
