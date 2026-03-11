/**
 * Mizan API Client
 *
 * Type-safe HTTP client for the Mizan backend API.
 * Follows the Repository pattern for data access.
 */

import type {
  AnalysisRequest,
  AnalysisResponse,
  VerseAnalysisResponse,
  VerseResponse,
  SurahMetadata,
  SurahResponse,
  HealthResponse,
  ApiError,
  LibrarySpaceResponse,
  CreateLibrarySpaceRequest,
  TextSourceResponse,
  AddTextSourceRequest,
  SemanticSearchRequest,
  SemanticSearchResultResponse,
  SimilarVerseResponse,
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

  /**
   * DELETE request
   */
  private delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // ==========================================
  // Health & Status
  // ==========================================

  /**
   * Check API health status
   */
  async getHealth(): Promise<HealthResponse> {
    return this.get<HealthResponse>('/health');
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
    return this.get<VerseResponse[]>(`/api/v1/surahs/${surah}/verses`);
  }

  // ==========================================
  // Surah Operations
  // ==========================================

  /**
   * Get list of all surahs with metadata.
   * Backend returns an array directly (not wrapped).
   */
  async getSurahList(): Promise<SurahMetadata[]> {
    return this.get<SurahMetadata[]>('/api/v1/surahs');
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
   * Get full analysis for a verse (letters, words, abjad, frequency).
   * Endpoint: GET /api/v1/analysis/verse/{surah}/{verse}
   */
  async analyzeVerse(surah: number, ayah: number): Promise<VerseAnalysisResponse> {
    return this.get<VerseAnalysisResponse>(`/api/v1/analysis/verse/${surah}/${ayah}`);
  }

  /**
   * Count letters in scope (surah/verse or whole Quran).
   * Endpoint: GET /api/v1/analysis/letters/count
   */
  async countLetters(params: {
    surah?: number;
    verse?: number;
    script?: string;
    count_alif_wasla?: boolean;
    text?: string;
  } = {}): Promise<{ count: number; scope: Record<string, unknown>; methodology: string }> {
    const qs = new URLSearchParams(
      Object.fromEntries(
        Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])
      )
    ).toString();
    return this.get(`/api/v1/analysis/letters/count${qs ? `?${qs}` : ''}`);
  }

  /**
   * Count words in scope.
   * Endpoint: GET /api/v1/analysis/words/count
   */
  async countWords(params: { surah?: number; verse?: number; text?: string } = {}): Promise<{
    count: number;
    scope: Record<string, unknown>;
  }> {
    const qs = new URLSearchParams(
      Object.fromEntries(
        Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])
      )
    ).toString();
    return this.get(`/api/v1/analysis/words/count${qs ? `?${qs}` : ''}`);
  }

  /**
   * Calculate Abjad value.
   * Endpoint: GET /api/v1/analysis/abjad
   */
  async calculateAbjad(params: {
    text?: string;
    surah?: number;
    verse?: number;
    system?: string;
    include_breakdown?: boolean;
  }): Promise<{ value: number; system: string; breakdown?: AnalysisResponse['breakdown'] }> {
    const qs = new URLSearchParams(params as Record<string, string>).toString();
    return this.get(`/api/v1/analysis/abjad${qs ? `?${qs}` : ''}`);
  }

  /**
   * Search Quran text (trigram-based).
   * Endpoint: GET /api/v1/search?q=...
   */
  async searchQuran(query: string, surah?: number, limit = 50): Promise<AnalysisResponse> {
    const params: Record<string, string> = { q: query, limit: String(limit) };
    if (surah) params.surah = String(surah);
    return this.get(`/api/v1/search?${new URLSearchParams(params)}`);
  }

  // ==========================================
  // Library Management (Semantic Search)
  // ==========================================

  /**
   * Create a new library space.
   */
  async createLibrarySpace(data: CreateLibrarySpaceRequest): Promise<LibrarySpaceResponse> {
    return this.post<LibrarySpaceResponse>('/api/v1/library/spaces', data);
  }

  /**
   * List all library spaces.
   */
  async listLibrarySpaces(): Promise<LibrarySpaceResponse[]> {
    return this.get<LibrarySpaceResponse[]>('/api/v1/library/spaces');
  }

  /**
   * Add a text source to a library space.
   */
  async addTextSource(spaceId: string, data: AddTextSourceRequest): Promise<TextSourceResponse> {
    return this.post<TextSourceResponse>(`/api/v1/library/spaces/${spaceId}/sources`, data);
  }

  /**
   * Get text source details (including indexing status).
   */
  async getTextSource(sourceId: string): Promise<TextSourceResponse> {
    return this.get<TextSourceResponse>(`/api/v1/library/sources/${sourceId}`);
  }

  /**
   * Trigger indexing for a text source.
   */
  async indexTextSource(sourceId: string): Promise<{ status: string }> {
    return this.post(`/api/v1/library/sources/${sourceId}/index`, {});
  }

  /**
   * Delete a library space and all its sources.
   */
  async deleteLibrarySpace(spaceId: string): Promise<void> {
    return this.delete(`/api/v1/library/spaces/${spaceId}`);
  }

  /**
   * Delete a text source and all its chunks.
   */
  async deleteTextSource(sourceId: string): Promise<void> {
    return this.delete(`/api/v1/library/sources/${sourceId}`);
  }

  // ==========================================
  // Semantic Search
  // ==========================================

  /**
   * Perform semantic search across indexed text sources.
   * Returns the results array extracted from the backend wrapper response.
   */
  async semanticSearch(request: SemanticSearchRequest): Promise<SemanticSearchResultResponse[]> {
    const wrapper = await this.post<{ results: SemanticSearchResultResponse[] }>(
      '/api/v1/search/semantic',
      request
    );
    return wrapper.results;
  }

  /**
   * Find semantically similar verses.
   */
  async findSimilarVerses(surah: number, verse: number, limit = 5): Promise<SimilarVerseResponse[]> {
    return this.get<SimilarVerseResponse[]>(
      `/api/v1/search/verses/${surah}/${verse}/similar?limit=${limit}`
    );
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
