'use client';

import * as React from 'react';

import { useApiClient } from '@/lib/api/provider';
import type { AnalysisResponse, AnalysisRequest, LetterCountMethod, AbjadSystem } from '@/types/api';

interface UseVerseAnalysisOptions {
  onSuccess?: (result: AnalysisResponse) => void;
  onError?: (error: Error) => void;
}

interface AnalysisState {
  result: AnalysisResponse | null;
  isLoading: boolean;
  error: Error | null;
}

/**
 * Custom hook for verse analysis
 *
 * Provides a clean interface for analyzing Quranic text
 * with loading and error states.
 */
export function useVerseAnalysis(options?: UseVerseAnalysisOptions) {
  const client = useApiClient();

  const [state, setState] = React.useState<AnalysisState>({
    result: null,
    isLoading: false,
    error: null,
  });

  const analyze = React.useCallback(
    async (request: AnalysisRequest) => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        let result: AnalysisResponse;

        if (request.surah != null && request.ayah != null) {
          // Verse mode — use analyzeVerse and map to AnalysisResponse shape
          const verseResult = await client.analyzeVerse(request.surah, request.ayah);
          result = {
            text: '',
            letter_count: verseResult.letters.count,
            word_count: verseResult.words.count,
            abjad_value: verseResult.abjad.value,
            letter_method: (request.letter_method ?? 'traditional') as AnalysisResponse['letter_method'],
            abjad_system: (request.abjad_system ?? 'mashriqi') as AnalysisResponse['abjad_system'],
            metadata: { surah: request.surah, ayah: request.ayah },
          };
        } else if (request.text) {
          // Text mode — use individual analysis endpoints
          const [letters, words, abjad] = await Promise.all([
            client.countLetters({ text: request.text }),
            client.countWords({ text: request.text }),
            client.calculateAbjad({
              text: request.text,
              system: request.abjad_system,
              include_breakdown: request.include_breakdown,
            }),
          ]);
          result = {
            text: request.text,
            letter_count: letters.count,
            word_count: words.count,
            abjad_value: abjad.value,
            letter_method: request.letter_method ?? 'traditional',
            abjad_system: request.abjad_system ?? 'mashriqi',
          };
        } else {
          throw new Error('AnalysisRequest must include either text or surah+ayah');
        }

        setState({ result, isLoading: false, error: null });
        options?.onSuccess?.(result);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Analysis failed');
        setState((prev) => ({ ...prev, isLoading: false, error }));
        options?.onError?.(error);
        throw error;
      }
    },
    [client, options]
  );

  const analyzeText = React.useCallback(
    async (
      text: string,
      letterMethod: LetterCountMethod = 'traditional',
      abjadSystem: AbjadSystem = 'mashriqi'
    ) => {
      return analyze({
        text,
        letter_method: letterMethod,
        abjad_system: abjadSystem,
        include_breakdown: true,
      });
    },
    [analyze]
  );

  const analyzeVerse = React.useCallback(
    async (
      surah: number,
      ayah: number,
      letterMethod: LetterCountMethod = 'traditional',
      abjadSystem: AbjadSystem = 'mashriqi'
    ) => {
      return analyze({
        surah,
        ayah,
        letter_method: letterMethod,
        abjad_system: abjadSystem,
        include_breakdown: true,
      });
    },
    [analyze]
  );

  const reset = React.useCallback(() => {
    setState({ result: null, isLoading: false, error: null });
  }, []);

  return {
    ...state,
    analyze,
    analyzeText,
    analyzeVerse,
    reset,
  };
}

/**
 * Hook for fetching surah list
 */
export function useSurahList() {
  const client = useApiClient();
  const [surahs, setSurahs] = React.useState<{ number: number; name_arabic: string; name_english: string; verse_count: number }[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const fetchSurahs = async () => {
      setIsLoading(true);
      try {
        const response = await client.getSurahList();
        setSurahs(response);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch surahs'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchSurahs();
  }, [client]);

  return { surahs, isLoading, error };
}

/**
 * Hook for fetching a single verse
 */
export function useVerse(surah: number | null, ayah: number | null) {
  const client = useApiClient();
  const [verse, setVerse] = React.useState<{ text: string } | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    if (surah === null || ayah === null) {
      setVerse(null);
      return;
    }

    const fetchVerse = async () => {
      setIsLoading(true);
      try {
        const response = await client.getVerse(surah, ayah);
        setVerse(response);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch verse'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchVerse();
  }, [client, surah, ayah]);

  return { verse, isLoading, error };
}
