'use client';

import * as React from 'react';
import { ApiClient } from './client';

// Context for API client
const ApiContext = React.createContext<ApiClient | null>(null);

interface ApiProviderProps {
  children: React.ReactNode;
  baseUrl: string;
}

/**
 * Provider component that makes the API client available throughout the app
 * Follows the Provider pattern for dependency injection
 */
export function ApiProvider({ children, baseUrl }: ApiProviderProps) {
  // Memoize the client to prevent unnecessary re-creation
  const client = React.useMemo(() => new ApiClient(baseUrl), [baseUrl]);

  return <ApiContext.Provider value={client}>{children}</ApiContext.Provider>;
}

/**
 * Hook to access the API client
 * @throws Error if used outside of ApiProvider
 */
export function useApiClient(): ApiClient {
  const client = React.useContext(ApiContext);

  if (!client) {
    throw new Error('useApiClient must be used within an ApiProvider');
  }

  return client;
}

/**
 * Hook for API client with loading and error states
 * Provides a convenient wrapper for API calls
 */
export function useApi() {
  const client = useApiClient();

  return {
    client,
    // Expose commonly used methods for convenience
    getHealth: client.getHealth.bind(client),
    getVerse: client.getVerse.bind(client),
    getSurahList: client.getSurahList.bind(client),
    getSurah: client.getSurah.bind(client),
    analyze: client.analyze.bind(client),
    analyzeVerse: client.analyzeVerse.bind(client),
    countLetters: client.countLetters.bind(client),
    countWords: client.countWords.bind(client),
    calculateAbjad: client.calculateAbjad.bind(client),
  };
}
