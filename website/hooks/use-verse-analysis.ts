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
        const result = await client.analyze(request);
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
        setSurahs(response.surahs);
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
