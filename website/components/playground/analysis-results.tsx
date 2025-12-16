'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Hash, Type, Calculator, Info } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { AnimatedCounter } from '@/components/animated/animated-counter';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { AnalysisResponse, LetterBreakdown } from '@/types/api';

interface AnalysisResultsProps {
  result: AnalysisResponse | null;
  isLoading: boolean;
  className?: string;
}

/**
 * Analysis Results Component
 *
 * Displays the results of text analysis with animated counters.
 */
export function AnalysisResults({ result, isLoading, className }: AnalysisResultsProps) {
  return (
    <div className={cn('space-y-6', className)}>
      {/* Main Results */}
      <div className="grid gap-4 md:grid-cols-3">
        <ResultCard
          icon={<Hash className="h-5 w-5" />}
          label="Letters"
          value={result?.letter_count || 0}
          method={result?.letter_method || 'traditional'}
          methodLabel={getMethodLabel(result?.letter_method)}
          color="gold"
          isLoading={isLoading}
          show={!!result}
          tooltip="Number of Arabic letters in the text"
        />

        <ResultCard
          icon={<Type className="h-5 w-5" />}
          label="Words"
          value={result?.word_count || 0}
          method="tanzil"
          methodLabel="Tanzil Standard"
          color="emerald"
          isLoading={isLoading}
          show={!!result}
          tooltip="Number of words (whitespace-delimited)"
        />

        <ResultCard
          icon={<Calculator className="h-5 w-5" />}
          label="Abjad Value"
          value={result?.abjad_value || 0}
          method={result?.abjad_system || 'mashriqi'}
          methodLabel={getSystemLabel(result?.abjad_system)}
          color="gold"
          isLoading={isLoading}
          show={!!result}
          tooltip="Sum of numerical values of letters"
        />
      </div>

      {/* Letter Breakdown */}
      {result?.breakdown && result.breakdown.length > 0 && (
        <LetterBreakdownChart breakdown={result.breakdown} />
      )}
    </div>
  );
}

/**
 * Result Card Component
 */
interface ResultCardProps {
  icon: React.ReactNode;
  label: string;
  value: number;
  method: string;
  methodLabel: string;
  color: 'gold' | 'emerald';
  isLoading: boolean;
  show: boolean;
  tooltip: string;
}

function ResultCard({
  icon,
  label,
  value,
  method,
  methodLabel,
  color,
  isLoading,
  show,
  tooltip,
}: ResultCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        'glass-card relative overflow-hidden rounded-xl p-5',
        'border transition-colors',
        color === 'gold'
          ? 'border-gold-500/20 hover:border-gold-500/40'
          : 'border-emerald-500/20 hover:border-emerald-500/40'
      )}
    >
      {/* Loading overlay */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 flex items-center justify-center bg-background/50 backdrop-blur-sm"
          >
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-gold-500 border-t-transparent" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className={cn(
              'rounded-lg p-2',
              color === 'gold' ? 'bg-gold-500/10 text-gold-500' : 'bg-emerald-500/10 text-emerald-500'
            )}
          >
            {icon}
          </div>
          <span className="text-sm font-medium text-muted-foreground">{label}</span>
        </div>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <Info className="h-4 w-4 text-muted-foreground/50" />
            </TooltipTrigger>
            <TooltipContent>
              <p>{tooltip}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Value */}
      <div
        className={cn(
          'mb-2 text-4xl font-bold tabular-nums',
          color === 'gold' ? 'text-gradient-gold' : 'text-gradient-emerald'
        )}
      >
        {show ? <AnimatedCounter value={value} duration={1.5} /> : '—'}
      </div>

      {/* Method Badge */}
      <Badge variant={color} className="text-xs">
        {methodLabel}
      </Badge>
    </motion.div>
  );
}

/**
 * Letter Breakdown Chart
 */
function LetterBreakdownChart({ breakdown }: { breakdown: LetterBreakdown[] }) {
  // Sort by count descending and take top 10
  const topLetters = [...breakdown]
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  const maxCount = topLetters[0]?.count || 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="glass-card rounded-xl p-5"
    >
      <h4 className="mb-4 text-sm font-medium text-muted-foreground">Letter Distribution</h4>

      <div className="space-y-3">
        {topLetters.map((item, index) => (
          <motion.div
            key={item.letter}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 * index }}
            className="flex items-center gap-3"
          >
            {/* Letter */}
            <span className="w-8 text-center font-arabic text-lg">{item.letter}</span>

            {/* Bar */}
            <div className="flex-1">
              <div className="h-6 overflow-hidden rounded-md bg-muted">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(item.count / maxCount) * 100}%` }}
                  transition={{ duration: 0.5, delay: 0.1 * index }}
                  className="h-full bg-gradient-to-r from-gold-500 to-gold-600"
                />
              </div>
            </div>

            {/* Count */}
            <span className="w-12 text-right text-sm font-medium">{item.count}</span>

            {/* Percentage */}
            <span className="w-12 text-right text-xs text-muted-foreground">
              {item.percentage.toFixed(1)}%
            </span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

/**
 * Helper functions
 */
function getMethodLabel(method?: string): string {
  const labels: Record<string, string> = {
    traditional: 'Traditional',
    uthmani_full: 'Uthmani Full',
    no_wasla: 'No Wasla',
  };
  return labels[method || 'traditional'] || 'Traditional';
}

function getSystemLabel(system?: string): string {
  const labels: Record<string, string> = {
    mashriqi: 'Mashriqi',
    maghribi: 'Maghribi',
  };
  return labels[system || 'mashriqi'] || 'Mashriqi';
}
