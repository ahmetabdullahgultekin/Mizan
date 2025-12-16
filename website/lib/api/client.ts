/**
 * Mizan API Client
 *
 * Type-safe HTTP client for the Mizan backend API.
 * Follows the Repository pattern for data access.
 */

import type {
  AnalysisRequest,
  AnalysisResponse,
  VerseResponse,
  SurahListResponse,
  SurahResponse,
  HealthResponse,
  ApiError,
} from '@/types/api';

export class ApiClient {
  private baseUrl: string;
  private defaultHeaders: HeadersInit;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };
  }

  /**
   * Make an HTTP request
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: 'An unknown error occurred',
        status_code: response.status,
      }));

      throw new ApiClientError(
        error.detail || `HTTP ${response.status}`,
        response.status,
        error
      );
    }

    return response.json();
  }

  /**
   * GET request
   */
  private get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  /**
   * POST request
   */
  private post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // ==========================================
  // Health & Status
  // ==========================================

  /**
   * Check API health status
   */
  async getHealth(): Promise<HealthResponse> {
    return this.get<HealthResponse>('/api/v1/health');
  }

  // ==========================================
  // Verse Operations
  // ==========================================

  /**
   * Get a specific verse by surah and ayah number
   */
  async getVerse(surah: number, ayah: number): Promise<VerseResponse> {
    return this.get<VerseResponse>(`/api/v1/verses/${surah}/${ayah}`);
  }

  /**
   * Get all verses of a surah
   */
  async getSurahVerses(surah: number): Promise<VerseResponse[]> {
    return this.get<VerseResponse[]>(`/api/v1/verses/${surah}`);
  }

  // ==========================================
  // Surah Operations
  // ==========================================

  /**
   * Get list of all surahs with metadata
   */
  async getSurahList(): Promise<SurahListResponse> {
    return this.get<SurahListResponse>('/api/v1/surahs');
  }

  /**
   * Get detailed surah information
   */
  async getSurah(surah: number): Promise<SurahResponse> {
    return this.get<SurahResponse>(`/api/v1/surahs/${surah}`);
  }

  // ==========================================
  // Analysis Operations
  // ==========================================

  /**
   * Analyze text (letters, words, abjad)
   */
  async analyze(request: AnalysisRequest): Promise<AnalysisResponse> {
    return this.post<AnalysisResponse>('/api/v1/analyze', request);
  }

  /**
   * Analyze a verse by reference
   */
  async analyzeVerse(
    surah: number,
    ayah: number,
    options?: Partial<AnalysisRequest>
  ): Promise<AnalysisResponse> {
    return this.get<AnalysisResponse>(
      `/api/v1/analyze/verse/${surah}/${ayah}` +
        (options ? `?${new URLSearchParams(options as Record<string, string>)}` : '')
    );
  }

  /**
   * Get letter count for text
   */
  async countLetters(
    text: string,
    method: string = 'traditional'
  ): Promise<{ count: number; method: string }> {
    return this.post('/api/v1/analyze/letters', { text, method });
  }

  /**
   * Get word count for text
   */
  async countWords(text: string): Promise<{ count: number }> {
    return this.post('/api/v1/analyze/words', { text });
  }

  /**
   * Calculate Abjad value
   */
  async calculateAbjad(
    text: string,
    system: string = 'mashriqi'
  ): Promise<{ value: number; system: string }> {
    return this.post('/api/v1/analyze/abjad', { text, system });
  }
}

/**
 * Custom error class for API errors
 */
export class ApiClientError extends Error {
  status: number;
  details: ApiError;

  constructor(message: string, status: number, details: ApiError) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.details = details;
  }

  /**
   * Check if error is a network error
   */
  isNetworkError(): boolean {
    return this.status === 0;
  }

  /**
   * Check if error is a validation error
   */
  isValidationError(): boolean {
    return this.status === 422;
  }

  /**
   * Check if error is a not found error
   */
  isNotFoundError(): boolean {
    return this.status === 404;
  }

  /**
   * Check if error is a rate limit error
   */
  isRateLimitError(): boolean {
    return this.status === 429;
  }
}

// Export singleton instance for convenience
let apiClientInstance: ApiClient | null = null;

export function getApiClient(baseUrl?: string): ApiClient {
  if (!apiClientInstance) {
    apiClientInstance = new ApiClient(
      baseUrl || process.env.NEXT_PUBLIC_API_URL || 'https://api.mizan.app'
    );
  }
  return apiClientInstance;
}
