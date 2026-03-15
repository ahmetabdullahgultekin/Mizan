'use client';

import * as React from 'react';
import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, Play, Sparkles } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArabicTextGenerate, GradientText } from '@/components/animated/text-generate';
import { GlowingOrbs, GeometricFloating } from '@/components/animated/floating-particles';
import { SpotlightButton } from '@/components/animated/spotlight';
import { AnimatedCounter } from '@/components/animated/animated-counter';
import { fadeInUp, staggerContainer, staggerItem } from '@/lib/animations/variants';
import { useI18n } from '@/lib/i18n';

/**
 * Hero Section
 *
 * The main hero section of the landing page with animated text,
 * floating particles, and call-to-action buttons.
 */
export function Hero() {
  const { t } = useI18n();
  const prefersReducedMotion = useReducedMotion();

  // When the user prefers reduced motion, skip stagger animations and show content immediately.
  const containerVariants = prefersReducedMotion
    ? { hidden: { opacity: 1 }, visible: { opacity: 1 } }
    : staggerContainer;
  const itemVariants = prefersReducedMotion
    ? { hidden: { opacity: 1 }, visible: { opacity: 1 } }
    : staggerItem;

  return (
    <section className="relative min-h-screen overflow-hidden pt-20">
      {/* Background Effects */}
      <GlowingOrbs />
      <GeometricFloating className="opacity-30" />

      {/* Content */}
      <div className="container relative z-10 mx-auto px-4 py-20 md:py-32">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="mx-auto max-w-4xl text-center"
        >
          {/* Badge */}
          <motion.div variants={itemVariants}>
            <Badge variant="glass" className="mb-6 px-4 py-1.5">
              <Sparkles className="mr-2 h-3 w-3 text-gold-500" />
              <span>{t('hero.badge')}</span>
            </Badge>
          </motion.div>

          {/* Arabic Bismillah */}
          <motion.div variants={itemVariants} className="mb-8">
            <ArabicTextGenerate
              text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
              className="text-arabic-2xl text-gradient-gold"
              delay={0.3}
            />
          </motion.div>

          {/* Main Heading */}
          <motion.h1
            variants={itemVariants}
            className="mb-6 text-4xl font-bold tracking-tight md:text-6xl lg:text-7xl"
          >
            <span className="text-foreground">{t('hero.title')} </span>
            <GradientText text={t('hero.titleHighlight')} />
          </motion.h1>

          {/* Subheading */}
          <motion.p
            variants={itemVariants}
            className="mx-auto mb-8 max-w-2xl text-lg text-muted-foreground md:text-xl"
          >
            {t('hero.description')}
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            variants={itemVariants}
            className="mb-12 flex flex-col items-center justify-center gap-4 sm:flex-row"
          >
            <SpotlightButton className="group px-8 py-4 text-base">
              <Link href="/playground" className="flex items-center">
                {t('hero.cta')}
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </SpotlightButton>

            <Button variant="outline" size="lg" className="group" asChild>
              <Link href="/docs">
                <Play className="mr-2 h-4 w-4" />
                {t('hero.ctaSecondary')}
              </Link>
            </Button>
          </motion.div>

          {/* Stats */}
          <motion.div
            variants={itemVariants}
            className="grid grid-cols-2 gap-4 md:grid-cols-4"
          >
            <StatItem value={6236} label="Total Verses" />
            <StatItem value={114} label="Surahs" />
            <StatItem value={786} label="Basmalah Abjad" suffix="" />
            <StatItem value={99} label="Accuracy %" suffix="%" />
          </motion.div>
        </motion.div>
      </div>

      {/* Scroll indicator - centered */}
      <motion.div
        initial={{ opacity: prefersReducedMotion ? 1 : 0, y: prefersReducedMotion ? 0 : 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: prefersReducedMotion ? 0 : 1.5, duration: prefersReducedMotion ? 0 : 0.5 }}
        className="absolute bottom-8 left-0 right-0 flex justify-center"
      >
        <motion.div
          animate={prefersReducedMotion ? {} : { y: [0, 8, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="flex flex-col items-center text-muted-foreground"
        >
          <span className="mb-2 text-xs">Scroll to explore</span>
          <div className="flex h-8 w-5 items-start justify-center rounded-full border-2 border-muted-foreground/30 pt-1">
            <motion.div
              animate={prefersReducedMotion ? {} : { y: [0, 10, 0] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="h-2 w-1.5 rounded-full bg-gold-500"
            />
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}

/**
 * Stat Item Component
 */
function StatItem({
  value,
  label,
  suffix = '',
}: {
  value: number;
  label: string;
  suffix?: string;
}) {
  return (
    <div className="glass-card rounded-xl p-4 text-center">
      <div className="text-2xl font-bold text-gradient-gold md:text-3xl">
        <AnimatedCounter value={value} suffix={suffix} duration={2} />
      </div>
      <div className="mt-1 text-xs text-muted-foreground md:text-sm">{label}</div>
    </div>
  );
}
