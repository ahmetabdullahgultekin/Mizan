'use client';

import * as React from 'react';
import { Globe } from 'lucide-react';

import { useI18n, localeConfig, type Locale } from '@/lib/i18n';
import { Button } from '@/components/ui/button';

/**
 * Language Switcher — cycles through en → tr → ar
 */
export function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();

  const locales: Locale[] = ['en', 'tr', 'ar'];

  const cycleLocale = () => {
    const currentIndex = locales.indexOf(locale);
    const nextIndex = (currentIndex + 1) % locales.length;
    setLocale(locales[nextIndex]);
  };

  const config = localeConfig[locale];

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={cycleLocale}
      className="gap-1.5 text-xs font-medium"
      title={`Language: ${config.label}`}
    >
      <Globe className="h-4 w-4" />
      <span>{config.label}</span>
    </Button>
  );
}
