'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import * as React from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { getApiClient } from '@/lib/api/client';
import { useI18n } from '@/lib/i18n';
import type { VerseResponse } from '@/types/api';

interface VerseSelectorProps {
  surahs?: Array<{
    number: number;
    name_arabic: string;
    name_english: string;
    verse_count: number;
  }>;
  isLoadingSurahs?: boolean;
  selectedSurah: number | null;
  selectedAyah: number | null;
  selectedToAyah?: number | null;
  rangeMode?: boolean;
  onSurahChange: (surah: number | null) => void;
  onAyahChange: (ayah: number | null) => void;
  onToAyahChange?: (ayah: number | null) => void;
  onRangeModeChange?: (rangeMode: boolean) => void;
  className?: string;
}

/**
 * Enhanced Verse Selector Component
 *
 * Allows users to select a specific verse or a range of verses from the Quran with:
 * - Surah dropdown with Arabic names
 * - Ayah dropdown with count (single or range mode)
 * - Live verse text preview
 * - Previous/Next navigation buttons (single mode only)
 */
export function VerseSelector({
  surahs = [],
  isLoadingSurahs = false,
  selectedSurah,
  selectedAyah,
  selectedToAyah = null,
  rangeMode = false,
  onSurahChange,
  onAyahChange,
  onToAyahChange,
  onRangeModeChange,
  className,
}: VerseSelectorProps) {
  const { t } = useI18n();
  const selectedSurahData = surahs.find((s) => s.number === selectedSurah);
  const verseCount = selectedSurahData?.verse_count || 0;

  // Verse text preview state
  const [versePreview, setVersePreview] = React.useState<VerseResponse | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = React.useState(false);

  // Fetch verse text when selection changes (only in single mode)
  React.useEffect(() => {
    if (rangeMode || !selectedSurah || !selectedAyah) {
      setVersePreview(null);
      return;
    }

    let cancelled = false;
    setIsLoadingPreview(true);

    getApiClient()
      .getVerse(selectedSurah, selectedAyah)
      .then((verse) => {
        if (!cancelled) setVersePreview(verse);
      })
      .catch(() => {
        if (!cancelled) setVersePreview(null);
      })
      .finally(() => {
        if (!cancelled) setIsLoadingPreview(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedSurah, selectedAyah, rangeMode]);

  const handleSurahChange = (value: string) => {
    const surahNum = parseInt(value, 10);
    onSurahChange(surahNum);
    onAyahChange(null); // Reset ayah when surah changes
    onToAyahChange?.(null);
  };

  const handleAyahChange = (value: string) => {
    const ayah = parseInt(value, 10);
    onAyahChange(ayah);
    // If range mode and toAyah is set but less than new fromAyah, reset it
    if (rangeMode && selectedToAyah !== null && selectedToAyah < ayah) {
      onToAyahChange?.(null);
    }
  };

  const handleToAyahChange = (value: string) => {
    onToAyahChange?.(parseInt(value, 10));
  };

  const handleRangeModeToggle = (isRange: boolean) => {
    onRangeModeChange?.(isRange);
    if (!isRange) {
      onToAyahChange?.(null);
    }
  };

  const goToPrevVerse = () => {
    if (!selectedSurah || !selectedAyah) return;
    if (selectedAyah > 1) {
      onAyahChange(selectedAyah - 1);
    } else if (selectedSurah > 1) {
      const prevSurah = surahs.find((s) => s.number === selectedSurah - 1);
      if (prevSurah) {
        onSurahChange(prevSurah.number);
        onAyahChange(prevSurah.verse_count);
      }
    }
  };

  const goToNextVerse = () => {
    if (!selectedSurah || !selectedAyah) return;
    if (selectedAyah < verseCount) {
      onAyahChange(selectedAyah + 1);
    } else if (selectedSurah < 114) {
      onSurahChange(selectedSurah + 1);
      onAyahChange(1);
    }
  };

  const canGoPrev = selectedSurah !== null && selectedAyah !== null && !(selectedSurah === 1 && selectedAyah === 1);
  const canGoNext = selectedSurah !== null && selectedAyah !== null && !(selectedSurah === 114 && selectedAyah === verseCount);

  const rangeVerseCount = rangeMode && selectedAyah && selectedToAyah
    ? selectedToAyah - selectedAyah + 1
    : null;

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-gold-500" />
          <h3 className="font-medium">{t('playground.selectVerse')}</h3>
        </div>

        {/* Range mode toggle */}
        <div className="flex items-center gap-1 rounded-lg border p-0.5">
          <button
            onClick={() => handleRangeModeToggle(false)}
            className={cn(
              'rounded-md px-3 py-1 text-xs font-medium transition-colors',
              !rangeMode
                ? 'bg-gold-500/15 text-gold-500'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {t('playground.singleVerse')}
          </button>
          <button
            onClick={() => handleRangeModeToggle(true)}
            className={cn(
              'rounded-md px-3 py-1 text-xs font-medium transition-colors',
              rangeMode
                ? 'bg-gold-500/15 text-gold-500'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {t('playground.verseRange')}
          </button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Surah Select */}
        <div className={cn('space-y-2', rangeMode ? 'sm:col-span-2' : '')}>
          <label className="text-sm text-muted-foreground">{t('playground.surah')}</label>
          <Select
            value={selectedSurah?.toString() || ''}
            onValueChange={handleSurahChange}
            disabled={isLoadingSurahs}
          >
            <SelectTrigger>
              <SelectValue placeholder={isLoadingSurahs ? t('playground.loadingSurahs') : t('playground.selectSurah')} />
            </SelectTrigger>
            <SelectContent>
              {surahs.map((surah) => (
                <SelectItem key={surah.number} value={surah.number.toString()}>
                  <span className="flex items-center gap-2">
                    <Badge variant="outline" className="w-8 justify-center text-xs">
                      {surah.number}
                    </Badge>
                    <span>{surah.name_english}</span>
                    <span className="font-arabic text-sm text-muted-foreground">
                      {surah.name_arabic}
                    </span>
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Ayah Select (or From Ayah in range mode) */}
        <div className="space-y-2">
          <label className="text-sm text-muted-foreground">
            {rangeMode ? t('playground.fromAyah') : t('playground.ayah')}{' '}
            {verseCount > 0 && `(1-${verseCount})`}
          </label>
          <Select
            value={selectedAyah?.toString() || ''}
            onValueChange={handleAyahChange}
            disabled={!selectedSurah}
          >
            <SelectTrigger>
              <SelectValue placeholder={rangeMode ? t('playground.fromAyah') : t('playground.selectAyah')} />
            </SelectTrigger>
            <SelectContent>
              {Array.from({ length: verseCount }, (_, i) => i + 1).map((ayah) => (
                <SelectItem key={ayah} value={ayah.toString()}>
                  {rangeMode ? `${t('playground.ayah')} ${ayah}` : `Ayah ${ayah}`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* To Ayah (range mode only) */}
        {rangeMode && (
          <div className="space-y-2">
            <label className="text-sm text-muted-foreground">
              {t('playground.toAyah')}{' '}
              {selectedAyah && verseCount > 0 && `(${selectedAyah}-${verseCount})`}
            </label>
            <Select
              value={selectedToAyah?.toString() || ''}
              onValueChange={handleToAyahChange}
              disabled={!selectedSurah || !selectedAyah}
            >
              <SelectTrigger>
                <SelectValue placeholder={t('playground.toAyah')} />
              </SelectTrigger>
              <SelectContent>
                {selectedAyah && Array.from(
                  { length: verseCount - selectedAyah + 1 },
                  (_, i) => selectedAyah + i
                ).map((ayah) => (
                  <SelectItem key={ayah} value={ayah.toString()}>
                    {t('playground.ayah')} {ayah}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {/* Range summary badge */}
      {rangeMode && rangeVerseCount && selectedSurahData && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2"
        >
          <Badge variant="gold" className="text-xs">
            {selectedSurahData.name_english} {selectedAyah}-{selectedToAyah} ({rangeVerseCount} {t('playground.verses')})
          </Badge>
        </motion.div>
      )}

      {/* Verse Navigation (single mode only) */}
      {!rangeMode && selectedSurah && selectedAyah && (
        <div className="flex items-center justify-between gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={goToPrevVerse}
            disabled={!canGoPrev}
            className="gap-1"
          >
            <ChevronLeft className="h-4 w-4" />
            {t('common.previous')}
          </Button>

          <span className="text-sm font-medium text-gold-500">
            {selectedSurahData?.name_english} {selectedSurah}:{selectedAyah}
          </span>

          <Button
            variant="outline"
            size="sm"
            onClick={goToNextVerse}
            disabled={!canGoNext}
            className="gap-1"
          >
            {t('common.next')}
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Verse Text Preview (single mode only) */}
      <AnimatePresence mode="wait">
        {!rangeMode && selectedSurah && selectedAyah && (
          <motion.div
            key={`${selectedSurah}:${selectedAyah}`}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="rounded-xl border border-gold-500/20 bg-gold-500/5 p-4"
          >
            {isLoadingPreview ? (
              <div className="flex items-center justify-center py-3 text-muted-foreground">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                <span className="text-sm">{t('playground.loadingVerse')}</span>
              </div>
            ) : versePreview ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>
                    {versePreview.surah_name_english} ({versePreview.surah_name_arabic})
                  </span>
                  <span className="font-mono">
                    {versePreview.surah_number}:{versePreview.verse_number}
                  </span>
                </div>
                <p
                  dir="rtl"
                  lang="ar"
                  className="text-lg leading-loose md:text-xl"
                  style={{ fontFamily: 'var(--font-amiri), serif' }}
                >
                  {versePreview.text_uthmani}
                </p>
                <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                  <span>{t('playground.juz')} {versePreview.juz_number}</span>
                  <span>{t('playground.page')} {versePreview.page_number}</span>
                  <span>{versePreview.word_count} {t('playground.wordsCount')}</span>
                  <span>{versePreview.letter_count} {t('playground.lettersCount')}</span>
                </div>
              </div>
            ) : (
              <p className="text-center text-sm text-muted-foreground">
                {t('playground.verseNotFound')}
              </p>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
