'use client';

import * as React from 'react';

/**
 * Custom hook for localStorage with SSR support
 *
 * Safely handles localStorage in Next.js with proper hydration.
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, React.Dispatch<React.SetStateAction<T>>] {
  // State to store value
  const [storedValue, setStoredValue] = React.useState<T>(initialValue);
  const [isHydrated, setIsHydrated] = React.useState(false);

  // Read from localStorage after hydration
  React.useEffect(() => {
    setIsHydrated(true);
    try {
      const item = window.localStorage.getItem(key);
      if (item) {
        setStoredValue(JSON.parse(item));
      }
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
    }
  }, [key]);

  // Update localStorage when value changes
  const setValue: React.Dispatch<React.SetStateAction<T>> = React.useCallback(
    (value) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        if (typeof window !== 'undefined') {
          window.localStorage.setItem(key, JSON.stringify(valueToStore));
        }
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  return [storedValue, setValue];
}

/**
 * Hook for analysis history
 */
interface HistoryEntry {
  id: string;
  text: string;
  letterCount: number;
  wordCount: number;
  abjadValue: number;
  letterMethod: string;
  abjadSystem: string;
  timestamp: number;
  source: 'verse' | 'custom';
  surah?: number;
  ayah?: number;
}

export function useAnalysisHistory(maxEntries = 50) {
  const [history, setHistory] = useLocalStorage<HistoryEntry[]>('mizan-analysis-history', []);

  const addEntry = React.useCallback(
    (entry: Omit<HistoryEntry, 'id' | 'timestamp'>) => {
      const newEntry: HistoryEntry = {
        ...entry,
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
      };

      setHistory((prev) => [newEntry, ...prev].slice(0, maxEntries));
      return newEntry;
    },
    [setHistory, maxEntries]
  );

  const removeEntry = React.useCallback(
    (id: string) => {
      setHistory((prev) => prev.filter((entry) => entry.id !== id));
    },
    [setHistory]
  );

  const clearHistory = React.useCallback(() => {
    setHistory([]);
  }, [setHistory]);

  return {
    history,
    addEntry,
    removeEntry,
    clearHistory,
  };
}
