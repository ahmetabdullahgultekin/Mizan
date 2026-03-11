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

// Complete static list of all 114 surahs used as fallback when the API is unreachable.
const ALL_SURAHS_FALLBACK: SurahMetadata[] = [
  { number: 1,   name_arabic: 'الفاتحة',   name_english: 'Al-Fatihah',    name_transliteration: 'Al-Fatihah',    revelation_type: 'meccan',   verse_count: 7   },
  { number: 2,   name_arabic: 'البقرة',     name_english: 'Al-Baqarah',   name_transliteration: 'Al-Baqarah',   revelation_type: 'medinan',  verse_count: 286 },
  { number: 3,   name_arabic: 'آل عمران',   name_english: 'Ali Imran',    name_transliteration: 'Ali Imran',    revelation_type: 'medinan',  verse_count: 200 },
  { number: 4,   name_arabic: 'النساء',     name_english: 'An-Nisa',      name_transliteration: 'An-Nisa',      revelation_type: 'medinan',  verse_count: 176 },
  { number: 5,   name_arabic: 'المائدة',    name_english: 'Al-Maidah',    name_transliteration: 'Al-Maidah',    revelation_type: 'medinan',  verse_count: 120 },
  { number: 6,   name_arabic: 'الأنعام',    name_english: 'Al-Anam',      name_transliteration: 'Al-Anam',      revelation_type: 'meccan',   verse_count: 165 },
  { number: 7,   name_arabic: 'الأعراف',    name_english: 'Al-Araf',      name_transliteration: 'Al-Araf',      revelation_type: 'meccan',   verse_count: 206 },
  { number: 8,   name_arabic: 'الأنفال',    name_english: 'Al-Anfal',     name_transliteration: 'Al-Anfal',     revelation_type: 'medinan',  verse_count: 75  },
  { number: 9,   name_arabic: 'التوبة',     name_english: 'At-Tawbah',    name_transliteration: 'At-Tawbah',    revelation_type: 'medinan',  verse_count: 129 },
  { number: 10,  name_arabic: 'يونس',       name_english: 'Yunus',        name_transliteration: 'Yunus',        revelation_type: 'meccan',   verse_count: 109 },
  { number: 11,  name_arabic: 'هود',        name_english: 'Hud',          name_transliteration: 'Hud',          revelation_type: 'meccan',   verse_count: 123 },
  { number: 12,  name_arabic: 'يوسف',       name_english: 'Yusuf',        name_transliteration: 'Yusuf',        revelation_type: 'meccan',   verse_count: 111 },
  { number: 13,  name_arabic: 'الرعد',      name_english: 'Ar-Rad',       name_transliteration: 'Ar-Rad',       revelation_type: 'medinan',  verse_count: 43  },
  { number: 14,  name_arabic: 'إبراهيم',    name_english: 'Ibrahim',      name_transliteration: 'Ibrahim',      revelation_type: 'meccan',   verse_count: 52  },
  { number: 15,  name_arabic: 'الحجر',      name_english: 'Al-Hijr',      name_transliteration: 'Al-Hijr',      revelation_type: 'meccan',   verse_count: 99  },
  { number: 16,  name_arabic: 'النحل',      name_english: 'An-Nahl',      name_transliteration: 'An-Nahl',      revelation_type: 'meccan',   verse_count: 128 },
  { number: 17,  name_arabic: 'الإسراء',    name_english: 'Al-Isra',      name_transliteration: 'Al-Isra',      revelation_type: 'meccan',   verse_count: 111 },
  { number: 18,  name_arabic: 'الكهف',      name_english: 'Al-Kahf',      name_transliteration: 'Al-Kahf',      revelation_type: 'meccan',   verse_count: 110 },
  { number: 19,  name_arabic: 'مريم',       name_english: 'Maryam',       name_transliteration: 'Maryam',       revelation_type: 'meccan',   verse_count: 98  },
  { number: 20,  name_arabic: 'طه',         name_english: 'Taha',         name_transliteration: 'Taha',         revelation_type: 'meccan',   verse_count: 135 },
  { number: 21,  name_arabic: 'الأنبياء',   name_english: 'Al-Anbiya',    name_transliteration: 'Al-Anbiya',    revelation_type: 'meccan',   verse_count: 112 },
  { number: 22,  name_arabic: 'الحج',       name_english: 'Al-Hajj',      name_transliteration: 'Al-Hajj',      revelation_type: 'medinan',  verse_count: 78  },
  { number: 23,  name_arabic: 'المؤمنون',   name_english: 'Al-Muminun',   name_transliteration: 'Al-Muminun',   revelation_type: 'meccan',   verse_count: 118 },
  { number: 24,  name_arabic: 'النور',      name_english: 'An-Nur',       name_transliteration: 'An-Nur',       revelation_type: 'medinan',  verse_count: 64  },
  { number: 25,  name_arabic: 'الفرقان',    name_english: 'Al-Furqan',    name_transliteration: 'Al-Furqan',    revelation_type: 'meccan',   verse_count: 77  },
  { number: 26,  name_arabic: 'الشعراء',    name_english: 'Ash-Shuara',   name_transliteration: 'Ash-Shuara',   revelation_type: 'meccan',   verse_count: 227 },
  { number: 27,  name_arabic: 'النمل',      name_english: 'An-Naml',      name_transliteration: 'An-Naml',      revelation_type: 'meccan',   verse_count: 93  },
  { number: 28,  name_arabic: 'القصص',      name_english: 'Al-Qasas',     name_transliteration: 'Al-Qasas',     revelation_type: 'meccan',   verse_count: 88  },
  { number: 29,  name_arabic: 'العنكبوت',   name_english: 'Al-Ankabut',   name_transliteration: 'Al-Ankabut',   revelation_type: 'meccan',   verse_count: 69  },
  { number: 30,  name_arabic: 'الروم',      name_english: 'Ar-Rum',       name_transliteration: 'Ar-Rum',       revelation_type: 'meccan',   verse_count: 60  },
  { number: 31,  name_arabic: 'لقمان',      name_english: 'Luqman',       name_transliteration: 'Luqman',       revelation_type: 'meccan',   verse_count: 34  },
  { number: 32,  name_arabic: 'السجدة',     name_english: 'As-Sajdah',    name_transliteration: 'As-Sajdah',    revelation_type: 'meccan',   verse_count: 30  },
  { number: 33,  name_arabic: 'الأحزاب',    name_english: 'Al-Ahzab',     name_transliteration: 'Al-Ahzab',     revelation_type: 'medinan',  verse_count: 73  },
  { number: 34,  name_arabic: 'سبأ',        name_english: 'Saba',         name_transliteration: 'Saba',         revelation_type: 'meccan',   verse_count: 54  },
  { number: 35,  name_arabic: 'فاطر',       name_english: 'Fatir',        name_transliteration: 'Fatir',        revelation_type: 'meccan',   verse_count: 45  },
  { number: 36,  name_arabic: 'يس',         name_english: 'Ya-Sin',       name_transliteration: 'Ya-Sin',       revelation_type: 'meccan',   verse_count: 83  },
  { number: 37,  name_arabic: 'الصافات',    name_english: 'As-Saffat',    name_transliteration: 'As-Saffat',    revelation_type: 'meccan',   verse_count: 182 },
  { number: 38,  name_arabic: 'ص',          name_english: 'Sad',          name_transliteration: 'Sad',          revelation_type: 'meccan',   verse_count: 88  },
  { number: 39,  name_arabic: 'الزمر',      name_english: 'Az-Zumar',     name_transliteration: 'Az-Zumar',     revelation_type: 'meccan',   verse_count: 75  },
  { number: 40,  name_arabic: 'غافر',       name_english: 'Ghafir',       name_transliteration: 'Ghafir',       revelation_type: 'meccan',   verse_count: 85  },
  { number: 41,  name_arabic: 'فصلت',       name_english: 'Fussilat',     name_transliteration: 'Fussilat',     revelation_type: 'meccan',   verse_count: 54  },
  { number: 42,  name_arabic: 'الشورى',     name_english: 'Ash-Shura',    name_transliteration: 'Ash-Shura',    revelation_type: 'meccan',   verse_count: 53  },
  { number: 43,  name_arabic: 'الزخرف',     name_english: 'Az-Zukhruf',   name_transliteration: 'Az-Zukhruf',   revelation_type: 'meccan',   verse_count: 89  },
  { number: 44,  name_arabic: 'الدخان',     name_english: 'Ad-Dukhan',    name_transliteration: 'Ad-Dukhan',    revelation_type: 'meccan',   verse_count: 59  },
  { number: 45,  name_arabic: 'الجاثية',    name_english: 'Al-Jathiyah',  name_transliteration: 'Al-Jathiyah',  revelation_type: 'meccan',   verse_count: 37  },
  { number: 46,  name_arabic: 'الأحقاف',    name_english: 'Al-Ahqaf',     name_transliteration: 'Al-Ahqaf',     revelation_type: 'meccan',   verse_count: 35  },
  { number: 47,  name_arabic: 'محمد',       name_english: 'Muhammad',     name_transliteration: 'Muhammad',     revelation_type: 'medinan',  verse_count: 38  },
  { number: 48,  name_arabic: 'الفتح',      name_english: 'Al-Fath',      name_transliteration: 'Al-Fath',      revelation_type: 'medinan',  verse_count: 29  },
  { number: 49,  name_arabic: 'الحجرات',    name_english: 'Al-Hujurat',   name_transliteration: 'Al-Hujurat',   revelation_type: 'medinan',  verse_count: 18  },
  { number: 50,  name_arabic: 'ق',          name_english: 'Qaf',          name_transliteration: 'Qaf',          revelation_type: 'meccan',   verse_count: 45  },
  { number: 51,  name_arabic: 'الذاريات',   name_english: 'Adh-Dhariyat', name_transliteration: 'Adh-Dhariyat', revelation_type: 'meccan',   verse_count: 60  },
  { number: 52,  name_arabic: 'الطور',      name_english: 'At-Tur',       name_transliteration: 'At-Tur',       revelation_type: 'meccan',   verse_count: 49  },
  { number: 53,  name_arabic: 'النجم',      name_english: 'An-Najm',      name_transliteration: 'An-Najm',      revelation_type: 'meccan',   verse_count: 62  },
  { number: 54,  name_arabic: 'القمر',      name_english: 'Al-Qamar',     name_transliteration: 'Al-Qamar',     revelation_type: 'meccan',   verse_count: 55  },
  { number: 55,  name_arabic: 'الرحمن',     name_english: 'Ar-Rahman',    name_transliteration: 'Ar-Rahman',    revelation_type: 'medinan',  verse_count: 78  },
  { number: 56,  name_arabic: 'الواقعة',    name_english: 'Al-Waqiah',    name_transliteration: 'Al-Waqiah',    revelation_type: 'meccan',   verse_count: 96  },
  { number: 57,  name_arabic: 'الحديد',     name_english: 'Al-Hadid',     name_transliteration: 'Al-Hadid',     revelation_type: 'medinan',  verse_count: 29  },
  { number: 58,  name_arabic: 'المجادلة',   name_english: 'Al-Mujadila',  name_transliteration: 'Al-Mujadila',  revelation_type: 'medinan',  verse_count: 22  },
  { number: 59,  name_arabic: 'الحشر',      name_english: 'Al-Hashr',     name_transliteration: 'Al-Hashr',     revelation_type: 'medinan',  verse_count: 24  },
  { number: 60,  name_arabic: 'الممتحنة',   name_english: 'Al-Mumtahanah',name_transliteration: 'Al-Mumtahanah',revelation_type: 'medinan',  verse_count: 13  },
  { number: 61,  name_arabic: 'الصف',       name_english: 'As-Saf',       name_transliteration: 'As-Saf',       revelation_type: 'medinan',  verse_count: 14  },
  { number: 62,  name_arabic: 'الجمعة',     name_english: 'Al-Jumuah',    name_transliteration: 'Al-Jumuah',    revelation_type: 'medinan',  verse_count: 11  },
  { number: 63,  name_arabic: 'المنافقون',  name_english: 'Al-Munafiqun', name_transliteration: 'Al-Munafiqun', revelation_type: 'medinan',  verse_count: 11  },
  { number: 64,  name_arabic: 'التغابن',    name_english: 'At-Taghabun',  name_transliteration: 'At-Taghabun',  revelation_type: 'medinan',  verse_count: 18  },
  { number: 65,  name_arabic: 'الطلاق',     name_english: 'At-Talaq',     name_transliteration: 'At-Talaq',     revelation_type: 'medinan',  verse_count: 12  },
  { number: 66,  name_arabic: 'التحريم',    name_english: 'At-Tahrim',    name_transliteration: 'At-Tahrim',    revelation_type: 'medinan',  verse_count: 12  },
  { number: 67,  name_arabic: 'الملك',      name_english: 'Al-Mulk',      name_transliteration: 'Al-Mulk',      revelation_type: 'meccan',   verse_count: 30  },
  { number: 68,  name_arabic: 'القلم',      name_english: 'Al-Qalam',     name_transliteration: 'Al-Qalam',     revelation_type: 'meccan',   verse_count: 52  },
  { number: 69,  name_arabic: 'الحاقة',     name_english: 'Al-Haqqah',    name_transliteration: 'Al-Haqqah',    revelation_type: 'meccan',   verse_count: 52  },
  { number: 70,  name_arabic: 'المعارج',    name_english: 'Al-Maarij',    name_transliteration: 'Al-Maarij',    revelation_type: 'meccan',   verse_count: 44  },
  { number: 71,  name_arabic: 'نوح',        name_english: 'Nuh',          name_transliteration: 'Nuh',          revelation_type: 'meccan',   verse_count: 28  },
  { number: 72,  name_arabic: 'الجن',       name_english: 'Al-Jinn',      name_transliteration: 'Al-Jinn',      revelation_type: 'meccan',   verse_count: 28  },
  { number: 73,  name_arabic: 'المزمل',     name_english: 'Al-Muzzammil', name_transliteration: 'Al-Muzzammil', revelation_type: 'meccan',   verse_count: 20  },
  { number: 74,  name_arabic: 'المدثر',     name_english: 'Al-Muddathir', name_transliteration: 'Al-Muddathir', revelation_type: 'meccan',   verse_count: 56  },
  { number: 75,  name_arabic: 'القيامة',    name_english: 'Al-Qiyamah',   name_transliteration: 'Al-Qiyamah',   revelation_type: 'meccan',   verse_count: 40  },
  { number: 76,  name_arabic: 'الإنسان',    name_english: 'Al-Insan',     name_transliteration: 'Al-Insan',     revelation_type: 'medinan',  verse_count: 31  },
  { number: 77,  name_arabic: 'المرسلات',   name_english: 'Al-Mursalat',  name_transliteration: 'Al-Mursalat',  revelation_type: 'meccan',   verse_count: 50  },
  { number: 78,  name_arabic: 'النبأ',      name_english: 'An-Naba',      name_transliteration: 'An-Naba',      revelation_type: 'meccan',   verse_count: 40  },
  { number: 79,  name_arabic: 'النازعات',   name_english: 'An-Naziat',    name_transliteration: 'An-Naziat',    revelation_type: 'meccan',   verse_count: 46  },
  { number: 80,  name_arabic: 'عبس',        name_english: 'Abasa',        name_transliteration: 'Abasa',        revelation_type: 'meccan',   verse_count: 42  },
  { number: 81,  name_arabic: 'التكوير',    name_english: 'At-Takwir',    name_transliteration: 'At-Takwir',    revelation_type: 'meccan',   verse_count: 29  },
  { number: 82,  name_arabic: 'الانفطار',   name_english: 'Al-Infitar',   name_transliteration: 'Al-Infitar',   revelation_type: 'meccan',   verse_count: 19  },
  { number: 83,  name_arabic: 'المطففين',   name_english: 'Al-Mutaffifin',name_transliteration: 'Al-Mutaffifin',revelation_type: 'meccan',   verse_count: 36  },
  { number: 84,  name_arabic: 'الانشقاق',   name_english: 'Al-Inshiqaq',  name_transliteration: 'Al-Inshiqaq',  revelation_type: 'meccan',   verse_count: 25  },
  { number: 85,  name_arabic: 'البروج',     name_english: 'Al-Buruj',     name_transliteration: 'Al-Buruj',     revelation_type: 'meccan',   verse_count: 22  },
  { number: 86,  name_arabic: 'الطارق',     name_english: 'At-Tariq',     name_transliteration: 'At-Tariq',     revelation_type: 'meccan',   verse_count: 17  },
  { number: 87,  name_arabic: 'الأعلى',     name_english: 'Al-Ala',       name_transliteration: 'Al-Ala',       revelation_type: 'meccan',   verse_count: 19  },
  { number: 88,  name_arabic: 'الغاشية',    name_english: 'Al-Ghashiyah', name_transliteration: 'Al-Ghashiyah', revelation_type: 'meccan',   verse_count: 26  },
  { number: 89,  name_arabic: 'الفجر',      name_english: 'Al-Fajr',      name_transliteration: 'Al-Fajr',      revelation_type: 'meccan',   verse_count: 30  },
  { number: 90,  name_arabic: 'البلد',      name_english: 'Al-Balad',     name_transliteration: 'Al-Balad',     revelation_type: 'meccan',   verse_count: 20  },
  { number: 91,  name_arabic: 'الشمس',      name_english: 'Ash-Shams',    name_transliteration: 'Ash-Shams',    revelation_type: 'meccan',   verse_count: 15  },
  { number: 92,  name_arabic: 'الليل',      name_english: 'Al-Layl',      name_transliteration: 'Al-Layl',      revelation_type: 'meccan',   verse_count: 21  },
  { number: 93,  name_arabic: 'الضحى',      name_english: 'Ad-Duha',      name_transliteration: 'Ad-Duha',      revelation_type: 'meccan',   verse_count: 11  },
  { number: 94,  name_arabic: 'الشرح',      name_english: 'Ash-Sharh',    name_transliteration: 'Ash-Sharh',    revelation_type: 'meccan',   verse_count: 8   },
  { number: 95,  name_arabic: 'التين',      name_english: 'At-Tin',       name_transliteration: 'At-Tin',       revelation_type: 'meccan',   verse_count: 8   },
  { number: 96,  name_arabic: 'العلق',      name_english: 'Al-Alaq',      name_transliteration: 'Al-Alaq',      revelation_type: 'meccan',   verse_count: 19  },
  { number: 97,  name_arabic: 'القدر',      name_english: 'Al-Qadr',      name_transliteration: 'Al-Qadr',      revelation_type: 'meccan',   verse_count: 5   },
  { number: 98,  name_arabic: 'البينة',     name_english: 'Al-Bayyinah',  name_transliteration: 'Al-Bayyinah',  revelation_type: 'medinan',  verse_count: 8   },
  { number: 99,  name_arabic: 'الزلزلة',    name_english: 'Az-Zalzalah',  name_transliteration: 'Az-Zalzalah',  revelation_type: 'medinan',  verse_count: 8   },
  { number: 100, name_arabic: 'العاديات',   name_english: 'Al-Adiyat',    name_transliteration: 'Al-Adiyat',    revelation_type: 'meccan',   verse_count: 11  },
  { number: 101, name_arabic: 'القارعة',    name_english: 'Al-Qariah',    name_transliteration: 'Al-Qariah',    revelation_type: 'meccan',   verse_count: 11  },
  { number: 102, name_arabic: 'التكاثر',    name_english: 'At-Takathur',  name_transliteration: 'At-Takathur',  revelation_type: 'meccan',   verse_count: 8   },
  { number: 103, name_arabic: 'العصر',      name_english: 'Al-Asr',       name_transliteration: 'Al-Asr',       revelation_type: 'meccan',   verse_count: 3   },
  { number: 104, name_arabic: 'الهمزة',     name_english: 'Al-Humazah',   name_transliteration: 'Al-Humazah',   revelation_type: 'meccan',   verse_count: 9   },
  { number: 105, name_arabic: 'الفيل',      name_english: 'Al-Fil',       name_transliteration: 'Al-Fil',       revelation_type: 'meccan',   verse_count: 5   },
  { number: 106, name_arabic: 'قريش',       name_english: 'Quraysh',      name_transliteration: 'Quraysh',      revelation_type: 'meccan',   verse_count: 4   },
  { number: 107, name_arabic: 'الماعون',    name_english: 'Al-Maun',      name_transliteration: 'Al-Maun',      revelation_type: 'meccan',   verse_count: 7   },
  { number: 108, name_arabic: 'الكوثر',     name_english: 'Al-Kawthar',   name_transliteration: 'Al-Kawthar',   revelation_type: 'meccan',   verse_count: 3   },
  { number: 109, name_arabic: 'الكافرون',   name_english: 'Al-Kafirun',   name_transliteration: 'Al-Kafirun',   revelation_type: 'meccan',   verse_count: 6   },
  { number: 110, name_arabic: 'النصر',      name_english: 'An-Nasr',      name_transliteration: 'An-Nasr',      revelation_type: 'medinan',  verse_count: 3   },
  { number: 111, name_arabic: 'المسد',      name_english: 'Al-Masad',     name_transliteration: 'Al-Masad',     revelation_type: 'meccan',   verse_count: 5   },
  { number: 112, name_arabic: 'الإخلاص',    name_english: 'Al-Ikhlas',    name_transliteration: 'Al-Ikhlas',    revelation_type: 'meccan',   verse_count: 4   },
  { number: 113, name_arabic: 'الفلق',      name_english: 'Al-Falaq',     name_transliteration: 'Al-Falaq',     revelation_type: 'meccan',   verse_count: 5   },
  { number: 114, name_arabic: 'الناس',      name_english: 'An-Nas',       name_transliteration: 'An-Nas',       revelation_type: 'meccan',   verse_count: 6   },
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
        // Fallback to complete static list of all 114 surahs if API is unreachable
        setSurahs(ALL_SURAHS_FALLBACK);
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
