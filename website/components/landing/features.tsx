'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import {
  Hash,
  Calculator,
  BookOpen,
  Shield,
  Zap,
  Globe,
  Code2,
  Database,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { FeatureCard } from '@/components/animated/glass-card';
import { staggerContainer, staggerItem } from '@/lib/animations/variants';
import { useI18n } from '@/lib/i18n';

/**
 * Features Section
 *
 * Showcases the main features of Mizan with animated cards.
 */
export function Features() {
  const { t } = useI18n();

  const features = [
    {
      icon: Hash,
      title: t('features.letterCounting'),
      description: t('features.letterCountingDesc'),
    },
    {
      icon: Calculator,
      title: t('features.abjadCalculator'),
      description: t('features.abjadCalculatorDesc'),
    },
    {
      icon: BookOpen,
      title: t('features.wordAnalysis'),
      description: t('features.wordAnalysisDesc'),
    },
    {
      icon: Shield,
      title: t('features.verifiedAccuracy'),
      description: t('features.verifiedAccuracyDesc'),
    },
    {
      icon: Zap,
      title: t('features.highPerformance'),
      description: t('features.highPerformanceDesc'),
    },
    {
      icon: Globe,
      title: t('features.multiScript'),
      description: t('features.multiScriptDesc'),
    },
    {
      icon: Code2,
      title: t('features.restApi'),
      description: t('features.restApiDesc'),
    },
    {
      icon: Database,
      title: t('features.scholarlyStandards'),
      description: t('features.scholarlyStandardsDesc'),
    },
  ];

  return (
    <section id="features" className="relative py-24">
      {/* Background */}
      <div className="absolute inset-0 pattern-geometric opacity-30" />

      <div className="container relative z-10 mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-16 text-center"
        >
          <h2 className="mb-4 text-3xl font-bold md:text-4xl">
            {t('features.title')}{' '}
            <span className="text-gradient-gold">{t('features.titleHighlight')}</span>
          </h2>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            {t('features.description')}
          </p>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
        >
          {features.map((feature, index) => (
            <FeatureCard
              key={index}
              icon={<feature.icon className="h-6 w-6" />}
              title={feature.title}
              description={feature.description}
              delay={index * 0.1}
            />
          ))}
        </motion.div>

        {/* Bottom CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="mt-16 text-center"
        >
          <p className="text-sm text-muted-foreground">
            {t('features.bottomNote')}
          </p>
        </motion.div>
      </div>
    </section>
  );
}
