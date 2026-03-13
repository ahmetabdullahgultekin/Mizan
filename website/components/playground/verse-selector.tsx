'use client';

import { motion } from 'framer-motion';
import { BookOpen } from 'lucide-react';
import * as React from 'react';

import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';

interface VerseSelectorProps {
  surahs: Array<{
    number: number;
    name_arabic: string;
    name_english: string;
    verse_count: number;
  }>;
  isLoadingSurahs?: boolean;
  selectedSurah: number | null;
  selectedAyah: number | null;
  onSurahChange: (surah: number | null) => void;
  onAyahChange: (ayah: number | null) => void;
  className?: string;
}

/**
 * Verse Selector Component
 *
 * Allows users to select a specific verse from the Quran.
 */
export function VerseSelector({
  surahs,
  isLoadingSurahs = false,
  selectedSurah,
  selectedAyah,
  onSurahChange,
  onAyahChange,
  className,
}: VerseSelectorProps) {
  const selectedSurahData = surahs.find((s) => s.number === selectedSurah);
  const verseCount = selectedSurahData?.verse_count || 0;

  const handleSurahChange = (value: string) => {
    const surahNum = parseInt(value, 10);
    onSurahChange(surahNum);
    onAyahChange(null); // Reset ayah when surah changes
  };

  const handleAyahChange = (value: string) => {
    onAyahChange(parseInt(value, 10));
  };

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center gap-2">
        <BookOpen className="h-5 w-5 text-gold-500" />
        <h3 className="font-medium">Select Verse</h3>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Surah Select */}
        <div className="space-y-2">
          <label className="text-sm text-muted-foreground">Surah</label>
          <Select
            value={selectedSurah?.toString() || ''}
            onValueChange={handleSurahChange}
            disabled={isLoadingSurahs}
          >
            <SelectTrigger>
              <SelectValue placeholder={isLoadingSurahs ? 'Loading surahs...' : 'Select Surah'} />
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

        {/* Ayah Select */}
        <div className="space-y-2">
          <label className="text-sm text-muted-foreground">
            Ayah {verseCount > 0 && `(1-${verseCount})`}
          </label>
          <Select
            value={selectedAyah?.toString() || ''}
            onValueChange={handleAyahChange}
            disabled={!selectedSurah}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select Ayah" />
            </SelectTrigger>
            <SelectContent>
              {Array.from({ length: verseCount }, (_, i) => i + 1).map((ayah) => (
                <SelectItem key={ayah} value={ayah.toString()}>
                  Ayah {ayah}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Selected verse info */}
      {selectedSurah && selectedAyah && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg bg-gold-500/10 p-3"
        >
          <p className="text-sm">
            <span className="text-muted-foreground">Selected: </span>
            <span className="font-medium text-gold-500">
              {selectedSurahData?.name_english} ({selectedSurahData?.name_arabic}) - Ayah{' '}
              {selectedAyah}
            </span>
          </p>
        </motion.div>
      )}
    </div>
  );
}
