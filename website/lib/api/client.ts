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
  SurahVersesResponse,
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
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    let response: Response;
    try {
      response = await fetch(url, {
        ...options,
        headers: {
          ...this.defaultHeaders,
          ...options.headers,
        },
      });
    } catch (error) {
      throw new ApiClientError(
        error instanceof Error ? error.message : 'Network error',
        0,
        { detail: 'Network error', status_code: 0 }
      );
    }

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: 'An unknown error occurred',
        status_code: response.status,
      }));

      throw new ApiClientError(error.detail || `HTTP ${response.status}`, response.status, error);
    }

    return response.json();
  }

  private get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  private post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  private delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async getHealth(): Promise<HealthResponse> {
    return this.get<HealthResponse>('/health');
  }

  async getVerse(surah: number, ayah: number): Promise<VerseResponse> {
    return this.get<VerseResponse>(`/api/v1/verses/${surah}/${ayah}`);
  }

  async getSurahVerses(surah: number): Promise<SurahVersesResponse> {
    return this.get<SurahVersesResponse>(`/api/v1/surahs/${surah}/verses`);
  }

  async getSurahList(): Promise<SurahMetadata[]> {
    return this.get<SurahMetadata[]>('/api/v1/surahs');
  }

  async getSurah(surah: number): Promise<SurahResponse> {
    return this.get<SurahResponse>(`/api/v1/surahs/${surah}`);
  }

  async analyze(request: AnalysisRequest): Promise<AnalysisResponse> {
    return this.post<AnalysisResponse>('/api/v1/analyze', request);
  }

  async analyzeVerse(surah: number, ayah: number): Promise<VerseAnalysisResponse> {
    return this.get<VerseAnalysisResponse>(`/api/v1/analysis/verse/${surah}/${ayah}`);
  }

  async countLetters(params: {
    surah?: number;
    verse?: number;
    script?: string;
    count_alif_wasla?: boolean;
    count_alif_khanjariyya?: boolean;
    text?: string;
  } = {}): Promise<{ count: number; scope: Record<string, unknown>; methodology: string }> {
    const qs = new URLSearchParams(
      Object.fromEntries(
        Object.entries(params)
          .filter(([, value]) => value !== undefined)
          .map(([key, value]) => [key, String(value)])
      )
    ).toString();
    return this.get(`/api/v1/analysis/letters/count${qs ? `?${qs}` : ''}`);
  }

  async countWords(params: {
    surah?: number;
    verse?: number;
    script?: string;
    text?: string;
  } = {}): Promise<{ count: number; scope: Record<string, unknown>; methodology: string }> {
    const qs = new URLSearchParams(
      Object.fromEntries(
        Object.entries(params)
          .filter(([, value]) => value !== undefined)
          .map(([key, value]) => [key, String(value)])
      )
    ).toString();
    return this.get(`/api/v1/analysis/words/count${qs ? `?${qs}` : ''}`);
  }

  async calculateAbjad(params: {
    text?: string;
    surah?: number;
    verse?: number;
    system?: string;
    include_breakdown?: boolean;
  }): Promise<{ value: number; system: string; breakdown?: AnalysisResponse['breakdown'] }> {
    const qs = new URLSearchParams(
      Object.fromEntries(
        Object.entries(params)
          .filter(([, value]) => value !== undefined)
          .map(([key, value]) => [key, String(value)])
      )
    ).toString();
    return this.get(`/api/v1/analysis/abjad${qs ? `?${qs}` : ''}`);
  }

  async searchQuran(query: string, surah?: number, limit = 50): Promise<Record<string, unknown>> {
    const params: Record<string, string> = { q: query, limit: String(limit) };
    if (surah) params.surah = String(surah);
    return this.get(`/api/v1/search?${new URLSearchParams(params)}`);
  }

  async createLibrarySpace(data: CreateLibrarySpaceRequest): Promise<LibrarySpaceResponse> {
    return this.post<LibrarySpaceResponse>('/api/v1/library/spaces', data);
  }

  async listLibrarySpaces(): Promise<LibrarySpaceResponse[]> {
    return this.get<LibrarySpaceResponse[]>('/api/v1/library/spaces');
  }

  async addTextSource(spaceId: string, data: AddTextSourceRequest): Promise<TextSourceResponse> {
    return this.post<TextSourceResponse>(`/api/v1/library/spaces/${spaceId}/sources`, data);
  }

  async getTextSource(sourceId: string): Promise<TextSourceResponse> {
    return this.get<TextSourceResponse>(`/api/v1/library/sources/${sourceId}`);
  }

  async indexTextSource(sourceId: string): Promise<{ status: string }> {
    return this.post(`/api/v1/library/sources/${sourceId}/index`, {});
  }

  async deleteLibrarySpace(spaceId: string): Promise<void> {
    return this.delete(`/api/v1/library/spaces/${spaceId}`);
  }

  async deleteTextSource(sourceId: string): Promise<void> {
    return this.delete(`/api/v1/library/sources/${sourceId}`);
  }

  async semanticSearch(request: SemanticSearchRequest): Promise<SemanticSearchResultResponse[]> {
    const wrapper = await this.post<{ results: SemanticSearchResultResponse[] }>(
      '/api/v1/search/semantic',
      request
    );
    return wrapper.results;
  }

  async findSimilarVerses(surah: number, verse: number, limit = 5): Promise<SimilarVerseResponse[]> {
    return this.get<SimilarVerseResponse[]>(
      `/api/v1/search/verses/${surah}/${verse}/similar?limit=${limit}`
    );
  }
}

export class ApiClientError extends Error {
  status: number;
  details: ApiError;

  constructor(message: string, status: number, details: ApiError) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.details = details;
  }

  isNetworkError(): boolean {
    return this.status === 0;
  }

  isValidationError(): boolean {
    return this.status === 422;
  }

  isNotFoundError(): boolean {
    return this.status === 404;
  }

  isRateLimitError(): boolean {
    return this.status === 429;
  }
}

let apiClientInstance: ApiClient | null = null;

export function getApiClient(baseUrl?: string): ApiClient {
  if (!apiClientInstance) {
    apiClientInstance = new ApiClient(
      baseUrl || process.env.NEXT_PUBLIC_API_URL || 'https://api.mizan.app'
    );
  }
  return apiClientInstance;
}
