'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, BookOpen, Layers, Loader2, AlertCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { getApiClient } from '@/lib/api/client';
import { useI18n } from '@/lib/i18n';
import type { SemanticSearchResultResponse, SourceType } from '@/types/api';

// ---------------------------------------------------------------------------
// Source type filter options
// ---------------------------------------------------------------------------

const SOURCE_TYPES: { value: SourceType; label: string; labelAr: string }[] = [
  { value: 'QURAN',  label: 'Quran',   labelAr: 'القرآن'  },
  { value: 'TAFSIR', label: 'Tafsir',  labelAr: 'التفسير' },
  { value: 'HADITH', label: 'Hadith',  labelAr: 'الحديث'  },
  { value: 'OTHER',  label: 'Other',   labelAr: 'أخرى'    },
];

// ---------------------------------------------------------------------------
// SearchResultCard
// ---------------------------------------------------------------------------

function SearchResultCard({
  result,
  index,
  similarityLabel,
}: {
  result: SemanticSearchResultResponse;
  index: number;
  similarityLabel: string;
}) {
  const scorePercent = Math.round(result.similarity_score * 100);
  const scoreColor =
    scorePercent >= 85 ? 'text-emerald-500' :
    scorePercent >= 70 ? 'text-gold-500' :
    'text-muted-foreground';

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="rounded-xl border bg-card p-5 space-y-3"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className="text-xs capitalize">
              {result.source_type}
            </Badge>
            {result.reference && (
              <span className="text-xs text-muted-foreground font-mono">{result.reference}</span>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{result.source_title}</p>
        </div>

        {/* Similarity score */}
        <div className="text-right shrink-0">
          <span className={`text-2xl font-bold tabular-nums ${scoreColor}`}>
            {scorePercent}%
          </span>
          <p className="text-xs text-muted-foreground">{similarityLabel}</p>
        </div>
      </div>

      {/* Content */}
      <p
        dir="auto"
        className="text-base leading-relaxed font-arabic"
        style={{ fontFamily: 'var(--font-amiri), serif' }}
      >
        {result.content}
      </p>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Main Search Page
// ---------------------------------------------------------------------------

export default function SearchPage() {
  const { t } = useI18n();
  const [query, setQuery] = React.useState('');
  const [selectedTypes, setSelectedTypes] = React.useState<Set<SourceType>>(new Set());
  const [minSimilarity, setMinSimilarity] = React.useState(0.65);
  const [results, setResults] = React.useState<SemanticSearchResultResponse[]>([]);
  const [isSearching, setIsSearching] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [hasSearched, setHasSearched] = React.useState(false);
  const debounceRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setError(null);
    setHasSearched(true);

    try {
      const data = await getApiClient().semanticSearch({
        query: query.trim(),
        source_types: selectedTypes.size > 0 ? Array.from(selectedTypes) : undefined,
        limit: 20,
        min_similarity: minSimilarity,
      });
      setResults(data);
    } catch {
      setError(t('search.searchUnavailable'));
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const toggleType = (type: SourceType) => {
    setSelectedTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  return (
    <div className="relative min-h-screen pt-20">
      <div className="mx-auto max-w-4xl px-4 py-12 space-y-10">

        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-4"
        >
          <div className="inline-flex items-center gap-2 rounded-full bg-gold-500/10 px-4 py-1.5 text-sm text-gold-500">
            <Search className="h-4 w-4" />
            {t('search.badge')}
          </div>
          <h1 className="text-4xl font-bold tracking-tight">
            {t('search.title')}
          </h1>
          <p className="text-muted-foreground max-w-xl mx-auto">
            {t('search.description')}
          </p>
        </motion.div>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <input
                value={query}
                onChange={(e) => {
                  const val = e.target.value;
                  setQuery(val);
                  if (debounceRef.current) clearTimeout(debounceRef.current);
                  if (val.trim()) {
                    debounceRef.current = setTimeout(() => handleSearch(), 300);
                  }
                }}
                placeholder={t('search.placeholder')}
                dir="auto"
                aria-label="Semantic search query"
                className="w-full rounded-xl border bg-background pl-12 pr-4 py-3.5 text-base
                           placeholder:text-muted-foreground
                           focus:outline-none focus:ring-2 focus:ring-gold-500/50"
              />
            </div>
            <Button
              type="submit"
              disabled={isSearching || !query.trim()}
              className="px-6 rounded-xl"
            >
              {isSearching ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                t('common.search')
              )}
            </Button>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
              <Filter className="h-4 w-4" />
              {t('search.source')}
            </div>
            {SOURCE_TYPES.map(({ value, label, labelAr }) => (
              <button
                key={value}
                type="button"
                onClick={() => toggleType(value)}
                className={`rounded-full border px-3 py-1 text-sm transition-colors ${
                  selectedTypes.has(value)
                    ? 'border-gold-500 bg-gold-500/10 text-gold-500'
                    : 'border-border text-muted-foreground hover:border-gold-500/50'
                }`}
              >
                {label}
                <span className="ml-1.5 font-arabic text-xs opacity-70">{labelAr}</span>
              </button>
            ))}

            <div className="ml-auto flex items-center gap-2 text-sm text-muted-foreground">
              <label htmlFor="min-similarity">{t('search.minSimilarity')}</label>
              <input
                id="min-similarity"
                type="range"
                min={0.5}
                max={0.95}
                step={0.05}
                value={minSimilarity}
                onChange={(e) => setMinSimilarity(parseFloat(e.target.value))}
                className="w-24 accent-gold-500"
                aria-label="Minimum similarity threshold"
                aria-valuenow={Math.round(minSimilarity * 100)}
                aria-valuemin={50}
                aria-valuemax={95}
                aria-valuetext={`${Math.round(minSimilarity * 100)}% minimum similarity`}
              />
              <span className="tabular-nums w-10" aria-live="polite">{Math.round(minSimilarity * 100)}%</span>
            </div>
          </div>
        </form>

        {/* Results */}
        <AnimatePresence mode="wait">
          {isSearching && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center justify-center py-16 gap-3 text-muted-foreground"
            >
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>{t('search.searching')}</span>
            </motion.div>
          )}

          {error && !isSearching && (
            <motion.div
              key="error"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 flex gap-4 items-start"
            >
              <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-destructive">{t('search.searchFailed')}</p>
                <p className="text-sm text-muted-foreground mt-1">{error}</p>
              </div>
            </motion.div>
          )}

          {!isSearching && hasSearched && !error && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-medium text-muted-foreground">
                  {results.length > 0
                    ? t('search.resultsFound').replace('{count}', String(results.length))
                    : t('search.noResults')}
                </h2>
                {results.length > 0 && (
                  <p className="text-xs text-muted-foreground">
                    {t('search.sortedBy')}
                  </p>
                )}
              </div>

              {results.length === 0 ? (
                <div className="rounded-xl border bg-card p-12 text-center space-y-3">
                  <BookOpen className="h-10 w-10 mx-auto text-muted-foreground/40" />
                  <p className="text-muted-foreground">
                    {t('search.noResultsHint').replace('{percent}', String(Math.round(minSimilarity * 100)))}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {t('search.noResultsAdvice')}{' '}
                    <a href="/library" className="text-gold-500 underline">{t('search.library')}</a>.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {results.map((r, i) => (
                    <SearchResultCard key={r.chunk_id} result={r} index={i} similarityLabel={t('common.similarity')} />
                  ))}
                </div>
              )}
            </motion.div>
          )}

          {!hasSearched && !isSearching && (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="rounded-xl border-2 border-dashed border-border p-16 text-center space-y-4"
            >
              <Layers className="h-12 w-12 mx-auto text-muted-foreground/30" />
              <div className="space-y-2">
                <p className="font-medium">{t('search.enterQuery')}</p>
                <p className="text-sm text-muted-foreground">
                  {t('search.searchHint')}
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2 pt-2">
                {[
                  'الرحمة والمغفرة',
                  'patience in hardship',
                  'Tevhid ve iman',
                  'prayer and remembrance',
                ].map((ex) => (
                  <button
                    key={ex}
                    onClick={() => { setQuery(ex); }}
                    className="rounded-full border px-3 py-1 text-sm text-muted-foreground hover:border-gold-500/50 hover:text-gold-500 transition-colors"
                    dir="auto"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
