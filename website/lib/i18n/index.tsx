'use client';

import * as React from 'react';

import en from './translations/en.json';
import tr from './translations/tr.json';
import ar from './translations/ar.json';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type Locale = 'en' | 'tr' | 'ar';
export type TranslationKey = string;

type Translations = typeof en;

const translations: Record<Locale, Translations> = { en, tr, ar };

export const localeConfig: Record<Locale, { label: string; dir: 'ltr' | 'rtl'; flag: string }> = {
  en: { label: 'English', dir: 'ltr', flag: '🇬🇧' },
  tr: { label: 'Turkce', dir: 'ltr', flag: '🇹🇷' },
  ar: { label: 'العربية', dir: 'rtl', flag: '🇸🇦' },
};

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
  dir: 'ltr' | 'rtl';
}

const I18nContext = React.createContext<I18nContextType | null>(null);

// ---------------------------------------------------------------------------
// Helper: get nested value from translation object
// ---------------------------------------------------------------------------

function getNestedValue(obj: Record<string, unknown>, path: string): string {
  const keys = path.split('.');
  let current: unknown = obj;
  for (const key of keys) {
    if (current === null || current === undefined || typeof current !== 'object') {
      return path; // Fallback to key
    }
    current = (current as Record<string, unknown>)[key];
  }
  return typeof current === 'string' ? current : path;
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = React.useState<Locale>('en');

  // Load saved locale from localStorage on mount
  React.useEffect(() => {
    const saved = localStorage.getItem('mizan-locale') as Locale | null;
    if (saved && translations[saved]) {
      setLocaleState(saved);
    }
  }, []);

  const setLocale = React.useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem('mizan-locale', newLocale);
    // Update document direction for RTL support
    document.documentElement.dir = localeConfig[newLocale].dir;
    document.documentElement.lang = newLocale;
  }, []);

  // Set initial dir/lang
  React.useEffect(() => {
    document.documentElement.dir = localeConfig[locale].dir;
    document.documentElement.lang = locale;
  }, [locale]);

  const t = React.useCallback(
    (key: string): string => {
      // Try current locale, fallback to English
      const value = getNestedValue(translations[locale] as unknown as Record<string, unknown>, key);
      if (value !== key) return value;
      return getNestedValue(translations.en as unknown as Record<string, unknown>, key);
    },
    [locale]
  );

  const dir = localeConfig[locale].dir;

  const contextValue = React.useMemo(
    () => ({ locale, setLocale, t, dir }),
    [locale, setLocale, t, dir]
  );

  return <I18nContext.Provider value={contextValue}>{children}</I18nContext.Provider>;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useI18n() {
  const context = React.useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
}
