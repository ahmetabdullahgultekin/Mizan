/**
 * Type Exports
 *
 * Central export file for all TypeScript types.
 */

// API Types
export * from './api';

// UI Component Types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface AnimatedComponentProps extends BaseComponentProps {
  delay?: number;
  duration?: number;
  once?: boolean;
}

// Analysis Types for UI
export interface AnalysisResult {
  letterCount: number;
  wordCount: number;
  abjadValue: number;
  letterMethod: string;
  abjadSystem: string;
  breakdown?: LetterDistribution[];
}

export interface LetterDistribution {
  letter: string;
  count: number;
  percentage: number;
  abjadValue?: number;
}

// Verse Selection Types
export interface VerseSelection {
  surah: number;
  ayah: number;
}

export interface SurahOption {
  number: number;
  nameArabic: string;
  nameEnglish: string;
  verseCount: number;
}

// History Types (for gamification)
export interface AnalysisHistoryEntry {
  id: string;
  text: string;
  result: AnalysisResult;
  timestamp: number;
  source: 'verse' | 'custom';
  verse?: VerseSelection;
}

export interface UserStats {
  totalAnalyses: number;
  versesAnalyzed: number;
  uniqueSurahs: Set<number>;
  achievements: Achievement[];
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  unlockedAt?: number;
  progress?: number;
  maxProgress?: number;
}

// Theme Types
export type Theme = 'light' | 'dark' | 'system';

// Navigation Types
export interface NavItem {
  title: string;
  href: string;
  external?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}
