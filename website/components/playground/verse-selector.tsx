'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { BookOpen } from 'lucide-react';

import { cn } from '@/lib/utils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';

// Static surah data (simplified for client-side usage)
const SURAHS = [
  { number: 1, name_arabic: 'الفاتحة', name_english: 'Al-Fatiha', verse_count: 7 },
  { number: 2, name_arabic: 'البقرة', name_english: 'Al-Baqara', verse_count: 286 },
  { number: 3, name_arabic: 'آل عمران', name_english: 'Ali Imran', verse_count: 200 },
  { number: 4, name_arabic: 'النساء', name_english: 'An-Nisa', verse_count: 176 },
  { number: 5, name_arabic: 'المائدة', name_english: 'Al-Maida', verse_count: 120 },
  { number: 6, name_arabic: 'الأنعام', name_english: 'Al-Anam', verse_count: 165 },
  { number: 7, name_arabic: 'الأعراف', name_english: 'Al-Araf', verse_count: 206 },
  { number: 8, name_arabic: 'الأنفال', name_english: 'Al-Anfal', verse_count: 75 },
  { number: 9, name_arabic: 'التوبة', name_english: 'At-Tawba', verse_count: 129 },
  { number: 10, name_arabic: 'يونس', name_english: 'Yunus', verse_count: 109 },
  // Add more surahs as needed - this is a simplified list
  { number: 112, name_arabic: 'الإخلاص', name_english: 'Al-Ikhlas', verse_count: 4 },
  { number: 113, name_arabic: 'الفلق', name_english: 'Al-Falaq', verse_count: 5 },
  { number: 114, name_arabic: 'الناس', name_english: 'An-Nas', verse_count: 6 },
];

interface VerseSelectorProps {
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
  selectedSurah,
  selectedAyah,
  onSurahChange,
  onAyahChange,
  className,
}: VerseSelectorProps) {
  const selectedSurahData = SURAHS.find((s) => s.number === selectedSurah);
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
          >
            <SelectTrigger>
              <SelectValue placeholder="Select Surah" />
            </SelectTrigger>
            <SelectContent>
              {SURAHS.map((surah) => (
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
