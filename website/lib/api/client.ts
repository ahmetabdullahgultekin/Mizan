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
  SurahMetadata,
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
   * Backend returns array directly, we wrap it for frontend convenience
   */
  async getSurahList(): Promise<SurahListResponse> {
    const surahs = await this.get<SurahMetadata[]>('/api/v1/surahs');
    return { surahs, total: surahs.length };
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
   * Analyze text or verse - combines letter count, word count, and abjad
   * Uses backend GET endpoints with query params
   */
  async analyze(request: AnalysisRequest): Promise<AnalysisResponse> {
    // If surah and ayah provided, use verse analysis endpoint
    if (request.surah && request.ayah) {
      return this.analyzeVerse(request.surah, request.ayah, request.abjad_system);
    }

    // For custom text, call individual endpoints and combine results
    if (!request.text) {
      throw new ApiClientError('No text or verse reference provided', 400, {
        detail: 'Provide either text or surah+ayah',
      });
    }

    const text = request.text;
    const system = request.abjad_system || 'mashriqi';

    // Call abjad endpoint which analyzes text
    const abjadResult = await this.calculateAbjad(text, system, true);

    // Build response matching frontend expected format
    return {
      text,
      letter_count: this.countLettersLocal(text),
      word_count: this.countWordsLocal(text),
      abjad_value: abjadResult.value,
      letter_method: request.letter_method || 'traditional',
      abjad_system: system as 'mashriqi' | 'maghribi',
      breakdown: abjadResult.breakdown,
    };
  }

  /**
   * Analyze a verse by reference using backend endpoint
   */
  async analyzeVerse(
    surah: number,
    ayah: number,
    system: string = 'mashriqi'
  ): Promise<AnalysisResponse> {
    // Use the combined verse analysis endpoint
    const result = await this.get<{
      location: string;
      letters: { count: number };
      words: { count: number };
      abjad: { value: number; breakdown?: Array<{ letter: string; value: number }> };
    }>(`/api/v1/analysis/verse/${surah}/${ayah}`);

    // Get verse text
    const verse = await this.getVerse(surah, ayah);

    return {
      text: verse.text || verse.text_uthmani || '',
      letter_count: result.letters.count,
      word_count: result.words.count,
      abjad_value: result.abjad.value,
      letter_method: 'traditional',
      abjad_system: system as 'mashriqi' | 'maghribi',
      breakdown: result.abjad.breakdown?.map(b => ({
        letter: b.letter,
        count: 1,
        percentage: 0,
        abjad_value: b.value,
      })),
      metadata: {
        surah,
        ayah,
        source: 'database',
      },
    };
  }

  /**
   * Get letter count using backend endpoint
   */
  async countLetters(
    surah?: number,
    verse?: number
  ): Promise<{ count: number; scope: object; methodology: string }> {
    const params = new URLSearchParams();
    if (surah) params.append('surah', surah.toString());
    if (verse) params.append('verse', verse.toString());
    return this.get(`/api/v1/analysis/letters/count?${params}`);
  }

  /**
   * Get word count using backend endpoint
   */
  async countWords(
    surah?: number,
    verse?: number
  ): Promise<{ count: number; scope: object; methodology: string }> {
    const params = new URLSearchParams();
    if (surah) params.append('surah', surah.toString());
    if (verse) params.append('verse', verse.toString());
    return this.get(`/api/v1/analysis/words/count?${params}`);
  }

  /**
   * Calculate Abjad value using backend endpoint
   */
  async calculateAbjad(
    text: string,
    system: string = 'mashriqi',
    includeBreakdown: boolean = false
  ): Promise<{ value: number; system: string; breakdown?: Array<{ letter: string; value: number }> }> {
    const params = new URLSearchParams({
      text,
      system,
      include_breakdown: includeBreakdown.toString(),
    });
    return this.get(`/api/v1/analysis/abjad?${params}`);
  }

  // ==========================================
  // Local helpers for text analysis (when API unavailable)
  // ==========================================

  private countLettersLocal(text: string): number {
    let count = 0;
    for (const char of text) {
      // Count Arabic letters (0600-06FF range, excluding diacritics)
      if (char >= '\u0600' && char <= '\u06FF') {
        if (!(char >= '\u064B' && char <= '\u065F')) {
          count++;
        }
      }
    }
    return count;
  }

  private countWordsLocal(text: string): number {
    return text.split(/\s+/).filter(Boolean).length;
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
