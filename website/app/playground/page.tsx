'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, RotateCcw, History, Keyboard } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ArabicTextarea } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { VerseSelector, AnalysisResults, MethodSelector } from '@/components/playground';
import { Spotlight } from '@/components/animated/spotlight';
import { GlowingOrbs } from '@/components/animated/floating-particles';
import type { LetterCountMethod, AbjadSystem, AnalysisResponse } from '@/types/api';

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

  // Mock analysis function (in production, this would call the API)
  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setResult(null);

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Mock result based on input
    const text = inputMode === 'custom' ? customText : 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ';

    // Simple mock calculation
    const mockResult: AnalysisResponse = {
      text,
      letter_count: text === 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ' ? 19 : Math.floor(text.length * 0.6),
      word_count: text === 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ' ? 4 : text.split(' ').filter(Boolean).length,
      abjad_value: text === 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ' ? 786 : Math.floor(Math.random() * 1000) + 100,
      letter_method: letterMethod,
      abjad_system: abjadSystem,
      breakdown: text === 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ' ? [
        { letter: 'ا', count: 3, percentage: 15.79, abjad_value: 1 },
        { letter: 'ل', count: 4, percentage: 21.05, abjad_value: 30 },
        { letter: 'ر', count: 2, percentage: 10.53, abjad_value: 200 },
        { letter: 'ح', count: 2, percentage: 10.53, abjad_value: 8 },
        { letter: 'م', count: 3, percentage: 15.79, abjad_value: 40 },
        { letter: 'ن', count: 1, percentage: 5.26, abjad_value: 50 },
        { letter: 'ب', count: 1, percentage: 5.26, abjad_value: 2 },
        { letter: 'س', count: 1, percentage: 5.26, abjad_value: 60 },
        { letter: 'ه', count: 1, percentage: 5.26, abjad_value: 5 },
        { letter: 'ي', count: 1, percentage: 5.26, abjad_value: 10 },
      ] : undefined,
    };

    setResult(mockResult);
    setIsAnalyzing(false);
  };

  const handleReset = () => {
    setResult(null);
    setCustomText('');
    setSelectedSurah(null);
    setSelectedAyah(null);
  };

  const canAnalyze =
    inputMode === 'custom' ? customText.trim().length > 0 : selectedSurah && selectedAyah;

  return (
    <div className="relative min-h-screen pt-20">
      {/* Background */}
      <GlowingOrbs className="opacity-30" />

      <div className="container relative z-10 mx-auto px-4 py-12">
        {/* Header */}
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
            Quranic Text{' '}
            <span className="text-gradient-gold">Analysis</span>
          </h1>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Analyze Quranic verses or custom Arabic text with precision letter counting,
            word analysis, and Abjad calculations.
          </p>
        </motion.div>

        {/* Main Content */}
        <div className="mx-auto max-w-4xl">
          <Spotlight className="rounded-2xl">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-card rounded-2xl p-6 md:p-8"
            >
              {/* Input Mode Tabs */}
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

                {/* Custom Text Input */}
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

                {/* Verse Selection */}
                <TabsContent value="verse" className="mt-4">
                  <VerseSelector
                    selectedSurah={selectedSurah}
                    selectedAyah={selectedAyah}
                    onSurahChange={setSelectedSurah}
                    onAyahChange={setSelectedAyah}
                  />
                </TabsContent>
              </Tabs>

              {/* Method Settings */}
              <MethodSelector
                letterMethod={letterMethod}
                abjadSystem={abjadSystem}
                onLetterMethodChange={setLetterMethod}
                onAbjadSystemChange={setAbjadSystem}
                className="mb-6"
              />

              {/* Action Buttons */}
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

              {/* Results */}
              <AnalysisResults result={result} isLoading={isAnalyzing} />
            </motion.div>
          </Spotlight>

          {/* Tips Section */}
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

/**
 * Tip Card Component
 */
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
