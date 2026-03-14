'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  History,
  Plus,
  Wrench,
  BookOpen,
  ExternalLink,
  Tag,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GlowingOrbs } from '@/components/animated/floating-particles';

interface ChangelogEntry {
  version: string;
  date: string;
  tag?: 'latest' | 'unreleased';
  sections: {
    title: string;
    icon: React.ReactNode;
    items: string[];
  }[];
}

const changelog: ChangelogEntry[] = [
  {
    version: '0.2.0',
    date: 'Unreleased',
    tag: 'unreleased',
    sections: [
      {
        title: 'Islamic Knowledge Library',
        icon: <Plus className="h-4 w-4" />,
        items: [
          'LibrarySpace, TextSource, TextChunk entities with pgvector support',
          'Semantic search API: POST /api/v1/search/semantic',
          'Similar verses endpoint: GET /api/v1/verses/{surah}/{verse}/similar',
          'IEmbeddingService interface with SentenceTransformer, Gemini, and Cascade implementations',
          'Cascade embedding service: primary provider with automatic fallback and dimension guard',
          'Configurable embedding settings: EMBEDDING_PROVIDER, EMBEDDING_MODEL, GEMINI_API_KEY',
        ],
      },
      {
        title: 'Data Pipeline Scripts',
        icon: <Plus className="h-4 w-4" />,
        items: [
          'ingest_tanzil.py: populate 114 surahs and 6,236 verses from Tanzil XML with juz/hizb/manzil/sajdah metadata',
          'embed_quran.py: batch-generate verse embeddings for all 6,236 verses',
        ],
      },
      {
        title: 'Frontend Pages',
        icon: <Plus className="h-4 w-4" />,
        items: [
          '/search page: semantic search UI with Arabic-aware input, source-type toggles, similarity slider (50-95%), animated result cards',
          '/library page: create spaces, add text sources, trigger indexing, retry/delete with live status badges',
          'API client extended with library and search methods',
          'TypeScript types for Library and SemanticSearch responses',
          'Navigation updated with Search and Library links',
        ],
      },
      {
        title: 'Playground Improvements',
        icon: <Plus className="h-4 w-4" />,
        items: [
          'Verse selector loads all 114 surahs dynamically from API (with graceful fallback)',
          'Removed mock delay; playground calls live API for analysis and Abjad calculations',
        ],
      },
      {
        title: 'Bug Fixes',
        icon: <Wrench className="h-4 w-4" />,
        items: [
          'getSurahList(): backend returns plain array, not {surahs, total} - mapping corrected',
          'analyzeVerse(): URL corrected from /api/v1/analyze/verse/ to /api/v1/analysis/verse/{surah}/{verse}',
        ],
      },
    ],
  },
  {
    version: '0.1.0',
    date: 'January 2025',
    tag: 'latest',
    sections: [
      {
        title: 'Core Features',
        icon: <Plus className="h-4 w-4" />,
        items: [
          'Letter Counting: Traditional, Uthmani Full, No Wasla methods (Al-Fatiha = 139 letters, Basmalah = 19 letters)',
          'Word Counting: whitespace-delimited Tanzil standard (Al-Fatiha = 29 words)',
          'Abjad Calculator: Mashriqi and Maghribi numeral systems (Allah = 66, Basmalah = 786)',
          'Verse Navigation: 114 surahs, 6,236 verses with validation and metadata',
        ],
      },
      {
        title: 'Domain Layer',
        icon: <Plus className="h-4 w-4" />,
        items: [
          'VerseLocation, AbjadValue, SurahMetadata, TextChecksum value objects',
          'Verse and Surah entities',
          'AbjadCalculator, LetterCounter, WordCounter domain services',
          'AbjadSystem, LetterCountMethod, ScriptType, RevelationType enumerations',
        ],
      },
      {
        title: 'Infrastructure',
        icon: <Plus className="h-4 w-4" />,
        items: [
          'PostgreSQL with async support (asyncpg)',
          'Redis caching layer',
          'SQLAlchemy ORM models with Alembic migrations',
          'FastAPI REST API with health, verse, and analysis endpoints',
          'OpenAPI documentation auto-generated',
          'Hexagonal Architecture with SOLID principles',
        ],
      },
      {
        title: 'Testing & Quality',
        icon: <Plus className="h-4 w-4" />,
        items: [
          '138 unit tests with property-based testing (Hypothesis)',
          'Verified against Tanzil.net, Quran.com, IslamWeb, and classical scholarship',
          'MyPy strict type checking, Ruff linting',
        ],
      },
    ],
  },
];

export default function ChangelogPage() {
  return (
    <div className="relative min-h-screen pt-20">
      <GlowingOrbs className="opacity-20" />

      <div className="container relative z-10 mx-auto px-4 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <Badge variant="emerald" className="mb-4">
            <History className="mr-2 h-3 w-3" />
            Changelog
          </Badge>
          <h1 className="mb-4 text-3xl font-bold md:text-4xl">
            Version{' '}
            <span className="text-gradient-emerald">History</span>
          </h1>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Track all changes, improvements, and bug fixes across Mizan versions.
            Format follows{' '}
            <a
              href="https://keepachangelog.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gold-500 hover:underline"
            >
              Keep a Changelog
            </a>
            {' '}and{' '}
            <a
              href="https://semver.org"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gold-500 hover:underline"
            >
              Semantic Versioning
            </a>.
          </p>
        </motion.div>

        {/* Timeline */}
        <div className="mx-auto max-w-3xl space-y-12">
          {changelog.map((entry, index) => (
            <motion.div
              key={entry.version}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + index * 0.1 }}
            >
              <div className="glass-card overflow-hidden rounded-xl">
                {/* Version header */}
                <div className="flex items-center gap-3 border-b border-border p-6">
                  <Tag className="h-5 w-5 text-gold-500" />
                  <h2 className="text-xl font-bold">v{entry.version}</h2>
                  <span className="text-sm text-muted-foreground">{entry.date}</span>
                  {entry.tag === 'unreleased' && (
                    <Badge variant="gold" className="ml-auto">In Development</Badge>
                  )}
                  {entry.tag === 'latest' && (
                    <Badge variant="emerald" className="ml-auto">Latest Release</Badge>
                  )}
                </div>

                {/* Sections */}
                <div className="divide-y divide-border">
                  {entry.sections.map((section) => (
                    <div key={section.title} className="p-6">
                      <div className="mb-3 flex items-center gap-2">
                        <div className="rounded-md bg-gold-500/10 p-1 text-gold-500">
                          {section.icon}
                        </div>
                        <h3 className="font-semibold">{section.title}</h3>
                      </div>
                      <ul className="space-y-2 pl-8">
                        {section.items.map((item, i) => (
                          <li
                            key={i}
                            className="list-disc text-sm text-muted-foreground marker:text-gold-500/50"
                          >
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-12 text-center"
        >
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button variant="glow" size="lg" asChild>
              <Link href="/playground">
                Try Latest Features
                <ExternalLink className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/docs/contributing">
                <BookOpen className="mr-2 h-4 w-4" />
                Contribute
              </Link>
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
