'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, RotateCcw, History, Keyboard, AlertCircle, GitBranch } from 'lucide-react';
import * as React from 'react';

import { GlowingOrbs } from '@/components/animated/floating-particles';
import { Spotlight } from '@/components/animated/spotlight';
import { VerseSelector, AnalysisResults, MethodSelector } from '@/components/playground';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArabicTextarea } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useSurahList } from '@/hooks/use-verse-analysis';
import { getApiClient } from '@/lib/api/client';
import type {
  LetterCountMethod,
  AbjadSystem,
  AnalysisResponse,
  VerseAnalysisResponse,
  SimilarVerseResponse,
} from '@/types/api';

/**
 * Playground Page
 *
 * Interactive page for analyzing Quranic text.
 * Supports both verse selection and custom text input.
 */
export default function PlaygroundPage() {
  // State
  const [inputMode, setInputMode] = React.useState<'verse' | 'custom'>('custom');
  const [selectedSurah, setSelectedSurah] = React.useState<number | null>(null);
  const [selectedAyah, setSelectedAyah] = React.useState<number | null>(null);
  const [customText, setCustomText] = React.useState('بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ');
  const [letterMethod, setLetterMethod] = React.useState<LetterCountMethod>('traditional');
  const [abjadSystem, setAbjadSystem] = React.useState<AbjadSystem>('mashriqi');
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [result, setResult] = React.useState<AnalysisResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [similarVerses, setSimilarVerses] = React.useState<SimilarVerseResponse[]>([]);
  const [isFindingSimilar, setIsFindingSimilar] = React.useState(false);
  const { surahs, isLoading: isLoadingSurahs } = useSurahList();

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setResult(null);
    setError(null);
    setSimilarVerses([]);

    try {
      const client = getApiClient();

      if (inputMode === 'verse' && selectedSurah && selectedAyah) {
        const raw: VerseAnalysisResponse = await client.analyzeVerse(selectedSurah, selectedAyah);

        const breakdown = raw.letter_frequency?.top_items?.map((item) => ({
          letter: item.letter,
          count: item.count,
          percentage: item.percentage,
          abjad_value: raw.abjad.breakdown?.find((b) => b.letter === item.letter)?.abjad_value,
        }));

        setResult({
          text: raw.location,
          letter_count: raw.letters.count,
          word_count: raw.words.count,
          abjad_value: raw.abjad.value,
          letter_method: letterMethod,
          abjad_system: abjadSystem,
          breakdown,
          metadata: { surah: selectedSurah, ayah: selectedAyah },
        });
      } else {
        const [letterRes, wordRes, abjadRes] = await Promise.all([
          client.countLetters({ text: customText }),
          client.countWords({ text: customText }),
          client.calculateAbjad({
            text: customText,
            system: abjadSystem,
            include_breakdown: true,
          }),
        ]);

        setResult({
          text: customText,
          letter_count: letterRes.count,
          word_count: wordRes.count,
          abjad_value: abjadRes.value,
          letter_method: letterMethod,
          abjad_system: abjadSystem,
          breakdown: abjadRes.breakdown,
        });
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Analysis failed. Make sure the backend is running.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleFindSimilar = async () => {
    if (!selectedSurah || !selectedAyah) return;
    setIsFindingSimilar(true);
    setSimilarVerses([]);
    try {
      const verses = await getApiClient().findSimilarVerses(selectedSurah, selectedAyah, 5);
      setSimilarVerses(verses);
    } catch (err) {
      setError(
        err instanceof Error && err.message.includes('404')
          ? 'No verse embeddings found. Run scripts/embed_quran.py to enable similarity search.'
          : 'Similarity search unavailable. Embeddings may not be indexed yet.'
      );
    } finally {
      setIsFindingSimilar(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setSimilarVerses([]);
    setCustomText('');
    setSelectedSurah(null);
    setSelectedAyah(null);
  };

  const canAnalyze =
    inputMode === 'custom' ? customText.trim().length > 0 : selectedSurah && selectedAyah;

  return (
    <div className="relative min-h-screen pt-20">
      <GlowingOrbs className="opacity-30" />

      <div className="container relative z-10 mx-auto px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 text-center"
        >
          <Badge variant="gold" className="mb-4">
            <Sparkles className="mr-2 h-3 w-3" />
            Interactive Playground
          </Badge>
          <h1 className="mb-4 text-3xl font-bold md:text-4xl">
            Quranic Text <span className="text-gradient-gold">Analysis</span>
          </h1>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Analyze Quranic verses or custom Arabic text with precision letter counting, word
            analysis, and Abjad calculations.
          </p>
        </motion.div>

        <div className="mx-auto max-w-4xl">
          <Spotlight className="rounded-2xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-card rounded-2xl p-6 md:p-8"
            >
              <Tabs
                value={inputMode}
                onValueChange={(value) => setInputMode(value as 'verse' | 'custom')}
                className="mb-6"
              >
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="custom" className="flex items-center gap-2">
                    <Keyboard className="h-4 w-4" />
                    Custom Text
                  </TabsTrigger>
                  <TabsTrigger value="verse" className="flex items-center gap-2">
                    <History className="h-4 w-4" />
                    Select Verse
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="custom" className="mt-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-muted-foreground">
                      Enter Arabic Text
                    </label>
                    <ArabicTextarea
                      value={customText}
                      onChange={(e) => setCustomText(e.target.value)}
                      placeholder="اكتب النص العربي هنا..."
                      className="min-h-[120px]"
                    />
                    <p className="text-xs text-muted-foreground">
                      Enter any Arabic text to analyze. Diacritics are handled automatically.
                    </p>
                  </div>
                </TabsContent>

                <TabsContent value="verse" className="mt-4">
                  <VerseSelector
                    surahs={surahs}
                    isLoadingSurahs={isLoadingSurahs}
                    selectedSurah={selectedSurah}
                    selectedAyah={selectedAyah}
                    onSurahChange={setSelectedSurah}
                    onAyahChange={setSelectedAyah}
                  />
                </TabsContent>
              </Tabs>

              <MethodSelector
                letterMethod={letterMethod}
                abjadSystem={abjadSystem}
                onLetterMethodChange={setLetterMethod}
                onAbjadSystemChange={setAbjadSystem}
                className="mb-6"
              />

              <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
                <Button
                  variant="glow"
                  size="lg"
                  onClick={handleAnalyze}
                  disabled={!canAnalyze || isAnalyzing}
                  className="min-w-[200px]"
                >
                  {isAnalyzing ? (
                    <span className="flex items-center">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        className="mr-2"
                      >
                        <Sparkles className="h-4 w-4" />
                      </motion.div>
                      Analyzing...
                    </span>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      Analyze
                    </>
                  )}
                </Button>

                <Button variant="outline" size="lg" onClick={handleReset}>
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Reset
                </Button>
              </div>

              <AnimatePresence>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="mb-6 flex items-start gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4"
                  >
                    <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
                    <div>
                      <p className="text-sm font-medium text-destructive">Analysis Failed</p>
                      <p className="mt-0.5 text-xs text-muted-foreground">{error}</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <AnalysisResults result={result} isLoading={isAnalyzing} />

              {inputMode === 'verse' && result && selectedSurah && selectedAyah && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-6 border-t pt-6"
                >
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="flex items-center gap-2 text-sm font-medium">
                      <GitBranch className="h-4 w-4 text-gold-500" />
                      Similar Verses
                    </h3>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleFindSimilar}
                      disabled={isFindingSimilar}
                    >
                      {isFindingSimilar ? 'Searching…' : 'Find Similar'}
                    </Button>
                  </div>

                  <AnimatePresence>
                    {similarVerses.length > 0 && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="space-y-2"
                      >
                        {similarVerses.map((v) => (
                          <button
                            key={`${v.surah_number}:${v.verse_number}`}
                            onClick={() => {
                              setSelectedSurah(v.surah_number);
                              setSelectedAyah(v.verse_number);
                              setSimilarVerses([]);
                              setResult(null);
                            }}
                            className="w-full rounded-lg border p-3 text-left transition-colors hover:border-gold-500/40"
                          >
                            <span className="flex items-center justify-between">
                              <span className="text-sm font-mono">
                                {v.surah_number}:{v.verse_number}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {Math.round(v.similarity_score * 100)}% similar
                              </span>
                            </span>
                          </button>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}
            </motion.div>
          </Spotlight>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-8 grid gap-4 md:grid-cols-3"
          >
            <TipCard
              title="Basmalah"
              description="Try analyzing بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ - it has 19 letters and Abjad value of 786."
              onClick={() => setCustomText('بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ')}
            />
            <TipCard
              title="Allah"
              description="The word الله has an Abjad value of 66 in the Mashriqi system."
              onClick={() => setCustomText('الله')}
            />
            <TipCard
              title="Muhammad"
              description="The name محمد has an Abjad value of 92."
              onClick={() => setCustomText('محمد')}
            />
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function TipCard({
  title,
  description,
  onClick,
}: {
  title: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="glass-card rounded-xl p-4 text-left transition-colors hover:border-gold-500/30"
    >
      <h4 className="mb-1 font-medium text-gold-500">{title}</h4>
      <p className="text-xs text-muted-foreground">{description}</p>
    </motion.button>
  );
}
