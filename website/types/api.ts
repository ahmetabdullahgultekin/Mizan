/**
 * API Response Types
 *
 * Type definitions for Mizan API responses.
 * These mirror the backend Pydantic models.
 */

// ==========================================
// Enums (matching backend)
// ==========================================

export type LetterCountMethod = 'traditional' | 'uthmani_full' | 'no_wasla';

export type AbjadSystem = 'mashriqi' | 'maghribi';

export type ScriptType = 'uthmani' | 'simple' | 'uthmani_min';

export type RevelationType = 'meccan' | 'medinan';

// ==========================================
// Request Types
// ==========================================

export interface AnalysisRequest {
  text?: string;
  surah?: number;
  ayah?: number;
  letter_method?: LetterCountMethod;
  abjad_system?: AbjadSystem;
  include_breakdown?: boolean;
}

// ==========================================
// Response Types
// ==========================================

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export interface VerseResponse {
  surah: number;
  ayah: number;
  text: string;
  text_simple?: string;
  text_uthmani?: string;
  juz?: number;
  hizb?: number;
  page?: number;
}

export interface SurahMetadata {
  number: number;
  name_arabic: string;
  name_english: string;
  name_transliteration: string;
  revelation_type: RevelationType;
  verse_count: number;
  word_count?: number;
  letter_count?: number;
}

export interface SurahListResponse {
  surahs: SurahMetadata[];
  total: number;
}

export interface SurahResponse extends SurahMetadata {
  verses: VerseResponse[];
}

export interface LetterBreakdown {
  letter: string;
  count: number;
  percentage: number;
  abjad_value?: number;
}

export interface AnalysisResponse {
  text: string;
  letter_count: number;
  word_count: number;
  abjad_value: number;
  letter_method: LetterCountMethod;
  abjad_system: AbjadSystem;
  breakdown?: LetterBreakdown[];
  metadata?: {
    surah?: number;
    ayah?: number;
    source?: string;
  };
}

// ==========================================
// Error Types
// ==========================================

export interface ApiError {
  detail: string;
  status_code?: number;
  type?: string;
  errors?: ValidationError[];
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

// ==========================================
// Verse Analysis Response (from /api/v1/analysis/verse/{surah}/{verse})
// ==========================================

export interface VerseAnalysisResponse {
  location: string;           // e.g. "1:1"
  letters: {
    count: number;
    scope: string;
    methodology: string;
  };
  words: {
    count: number;
    scope: string;
    methodology: string;
  };
  abjad: {
    value: number;
    system: string;
    text_analyzed: string;
    is_prime: boolean;
    digital_root: number;
    breakdown?: LetterBreakdown[];
  };
  letter_frequency: {
    total_items: number;
    unique_items: number;
    distribution: Record<string, number>;
    top_items: Array<{ letter: string; count: number; percentage: number }>;
  };
}

// ==========================================
// Library & Semantic Search Types
// ==========================================

export type SourceType = 'QURAN' | 'TAFSIR' | 'HADITH' | 'OTHER';
export type IndexingStatus = 'PENDING' | 'INDEXING' | 'INDEXED' | 'FAILED';

export interface LibrarySpaceResponse {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  sources?: TextSourceResponse[];
}

export interface CreateLibrarySpaceRequest {
  name: string;
  description?: string;
}

export interface TextSourceResponse {
  id: string;
  library_space_id: string;
  source_type: SourceType;
  title_arabic?: string;
  title_turkish?: string;
  title_english?: string;
  author?: string;
  status: IndexingStatus;
  total_chunks: number;
  indexed_chunks: number;
  embedding_model?: string;
  created_at: string;
  updated_at: string;
}

export interface AddTextSourceRequest {
  source_type: SourceType;
  title_arabic?: string;
  title_turkish?: string;
  title_english?: string;
  author?: string;
  content: string;          // raw text to index
}

export interface SemanticSearchRequest {
  query: string;
  library_space_id?: string;
  source_types?: SourceType[];
  limit?: number;
  min_similarity?: number;
}

export interface SemanticSearchResponse {
  chunk_content: string;
  reference: string;
  similarity_score: number;
  source: {
    id: string;
    title: string;
    source_type: SourceType;
    author?: string;
  };
  metadata?: Record<string, unknown>;
}

// ==========================================
// Utility Types
// ==========================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiState<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
}
