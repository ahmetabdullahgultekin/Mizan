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
