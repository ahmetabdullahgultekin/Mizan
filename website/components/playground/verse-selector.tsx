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
import { getApiClient } from '@/lib/api/client';
import type { SurahMetadata } from '@/types/api';

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
 * Loads surah list from the backend API and lets users pick a verse.
 */
export function VerseSelector({
  selectedSurah,
  selectedAyah,
  onSurahChange,
  onAyahChange,
  className,
}: VerseSelectorProps) {
  const [surahs, setSurahs] = React.useState<SurahMetadata[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    getApiClient()
      .getSurahList()
      .then((data) => setSurahs(data))
      .catch(() => {
        // Fallback to a minimal static list if API is unreachable
        setSurahs([
          { number: 1,   name_arabic: 'الفاتحة', name_english: 'Al-Fatihah',  name_transliteration: 'Al-Fatihah',  revelation_type: 'meccan',   verse_count: 7   },
          { number: 2,   name_arabic: 'البقرة',   name_english: 'Al-Baqarah',  name_transliteration: 'Al-Baqarah',  revelation_type: 'medinan',  verse_count: 286 },
          { number: 112, name_arabic: 'الإخلاص', name_english: 'Al-Ikhlas',   name_transliteration: 'Al-Ikhlas',   revelation_type: 'meccan',   verse_count: 4   },
          { number: 113, name_arabic: 'الفلق',   name_english: 'Al-Falaq',    name_transliteration: 'Al-Falaq',    revelation_type: 'meccan',   verse_count: 5   },
          { number: 114, name_arabic: 'الناس',   name_english: 'An-Nas',      name_transliteration: 'An-Nas',      revelation_type: 'meccan',   verse_count: 6   },
        ]);
      })
      .finally(() => setIsLoading(false));
  }, []);

  const selectedSurahData = surahs.find((s) => s.number === selectedSurah);
  const verseCount = selectedSurahData?.verse_count || 0;

  const handleSurahChange = (value: string) => {
    onSurahChange(parseInt(value, 10));
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
          <label className="text-sm text-muted-foreground">
            Surah {isLoading && <span className="text-xs opacity-60">(loading…)</span>}
          </label>
          <Select
            value={selectedSurah?.toString() || ''}
            onValueChange={handleSurahChange}
            disabled={isLoading}
          >
            <SelectTrigger>
              <SelectValue placeholder={isLoading ? 'Loading surahs…' : 'Select Surah'} />
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
              {selectedSurahData?.name_english} ({selectedSurahData?.name_arabic}) — Ayah{' '}
              {selectedAyah}
            </span>
          </p>
        </motion.div>
      )}
    </div>
  );
}
