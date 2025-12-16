'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';
import Link from 'next/link';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AnimatedCounter } from '@/components/animated/animated-counter';
import { Spotlight } from '@/components/animated/spotlight';

/**
 * Demo Preview Section
 *
 * Shows a preview of the playground with the Basmalah analysis.
 */
export function DemoPreview() {
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [showResults, setShowResults] = React.useState(false);

  const handleAnalyze = () => {
    setIsAnalyzing(true);
    setShowResults(false);

    setTimeout(() => {
      setIsAnalyzing(false);
      setShowResults(true);
    }, 1500);
  };

  return (
    <section className="relative py-24">
      <div className="container mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-12 text-center"
        >
          <Badge variant="emerald" className="mb-4">
            <Sparkles className="mr-2 h-3 w-3" />
            Live Demo
          </Badge>
          <h2 className="mb-4 text-3xl font-bold md:text-4xl">
            See It In{' '}
            <span className="text-gradient-emerald">Action</span>
          </h2>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Try the analysis engine with the Basmalah - the most analyzed phrase in Islamic tradition.
          </p>
        </motion.div>

        {/* Demo Card */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mx-auto max-w-3xl"
        >
          <Spotlight className="rounded-2xl">
            <div className="glass-card rounded-2xl p-6 md:p-8">
              {/* Input Section */}
              <div className="mb-6">
                <label className="mb-2 block text-sm font-medium text-muted-foreground">
                  Arabic Text
                </label>
                <div className="rounded-xl bg-background/50 p-4">
                  <p
                    className="text-center font-arabic text-arabic-xl text-foreground"
                    dir="rtl"
                    lang="ar"
                  >
                    بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
                  </p>
                </div>
              </div>

              {/* Analyze Button */}
              <div className="mb-6 flex justify-center">
                <Button
                  variant="glow"
                  size="lg"
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
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
                    'Analyze'
                  )}
                </Button>
              </div>

              {/* Results */}
              <motion.div
                initial={false}
                animate={{
                  height: showResults ? 'auto' : 0,
                  opacity: showResults ? 1 : 0,
                }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="grid gap-4 md:grid-cols-3">
                  <ResultCard
                    label="Letters"
                    value={19}
                    method="Traditional"
                    color="gold"
                    show={showResults}
                  />
                  <ResultCard
                    label="Words"
                    value={4}
                    method="Tanzil Standard"
                    color="emerald"
                    show={showResults}
                    delay={0.1}
                  />
                  <ResultCard
                    label="Abjad Value"
                    value={786}
                    method="Mashriqi"
                    color="gold"
                    show={showResults}
                    delay={0.2}
                  />
                </div>

                {/* Fun fact */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: showResults ? 1 : 0 }}
                  transition={{ delay: 0.5 }}
                  className="mt-4 rounded-lg bg-gold-500/10 p-4 text-center"
                >
                  <p className="text-sm text-gold-500">
                    <Sparkles className="mr-1 inline h-4 w-4" />
                    The number 19 is significant in Quranic numerology, and 786 is universally
                    recognized as the Abjad value of Basmalah.
                  </p>
                </motion.div>
              </motion.div>

              {/* CTA */}
              <div className="mt-6 text-center">
                <Button variant="outline" asChild>
                  <Link href="/playground">
                    Open Full Playground
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              </div>
            </div>
          </Spotlight>
        </motion.div>
      </div>
    </section>
  );
}

/**
 * Result Card Component
 */
function ResultCard({
  label,
  value,
  method,
  color,
  show,
  delay = 0,
}: {
  label: string;
  value: number;
  method: string;
  color: 'gold' | 'emerald';
  show: boolean;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: show ? 1 : 0, y: show ? 0 : 20 }}
      transition={{ duration: 0.3, delay: show ? delay : 0 }}
      className={cn(
        'rounded-xl border p-4 text-center',
        color === 'gold'
          ? 'border-gold-500/20 bg-gold-500/5'
          : 'border-emerald-500/20 bg-emerald-500/5'
      )}
    >
      <div className="text-sm text-muted-foreground">{label}</div>
      <div
        className={cn(
          'my-1 text-3xl font-bold',
          color === 'gold' ? 'text-gradient-gold' : 'text-gradient-emerald'
        )}
      >
        {show ? <AnimatedCounter value={value} duration={1} delay={delay} /> : '—'}
      </div>
      <Badge variant={color} className="text-xs">
        {method}
      </Badge>
    </motion.div>
  );
}
