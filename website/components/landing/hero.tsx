'use client';

import * as React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Play, Sparkles } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArabicTextGenerate, GradientText } from '@/components/animated/text-generate';
import { GlowingOrbs, GeometricFloating } from '@/components/animated/floating-particles';
import { SpotlightButton } from '@/components/animated/spotlight';
import { AnimatedCounter } from '@/components/animated/animated-counter';
import { fadeInUp, staggerContainer, staggerItem } from '@/lib/animations/variants';

/**
 * Hero Section
 *
 * The main hero section of the landing page with animated text,
 * floating particles, and call-to-action buttons.
 */
export function Hero() {
  return (
    <section className="relative min-h-screen overflow-hidden pt-20">
      {/* Background Effects */}
      <GlowingOrbs />
      <GeometricFloating className="opacity-30" />

      {/* Content */}
      <div className="container relative z-10 mx-auto px-4 py-20 md:py-32">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="mx-auto max-w-4xl text-center"
        >
          {/* Badge */}
          <motion.div variants={staggerItem}>
            <Badge variant="glass" className="mb-6 px-4 py-1.5">
              <Sparkles className="mr-2 h-3 w-3 text-gold-500" />
              <span>Open Source Quranic Analysis Engine</span>
            </Badge>
          </motion.div>

          {/* Arabic Bismillah */}
          <motion.div variants={staggerItem} className="mb-8">
            <ArabicTextGenerate
              text="بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
              className="text-arabic-2xl text-gradient-gold"
              delay={0.3}
            />
          </motion.div>

          {/* Main Heading */}
          <motion.h1
            variants={staggerItem}
            className="mb-6 text-4xl font-bold tracking-tight md:text-6xl lg:text-7xl"
          >
            <span className="text-foreground">Discover the </span>
            <GradientText text="Precision" />
            <br />
            <span className="text-foreground">of Quranic Analysis</span>
          </motion.h1>

          {/* Subheading */}
          <motion.p
            variants={staggerItem}
            className="mx-auto mb-8 max-w-2xl text-lg text-muted-foreground md:text-xl"
          >
            High-precision letter counting, word analysis, and Abjad calculations.
            Verified against{' '}
            <span className="text-gold-500">Tanzil.net</span> and scholarly standards.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            variants={staggerItem}
            className="mb-12 flex flex-col items-center justify-center gap-4 sm:flex-row"
          >
            <SpotlightButton className="group px-8 py-4 text-base">
              <Link href="/playground" className="flex items-center">
                Try Playground
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </SpotlightButton>

            <Button variant="outline" size="lg" className="group" asChild>
              <Link href="/docs">
                <Play className="mr-2 h-4 w-4" />
                View Documentation
              </Link>
            </Button>
          </motion.div>

          {/* Stats */}
          <motion.div
            variants={staggerItem}
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
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.5, duration: 0.5 }}
        className="absolute bottom-8 left-0 right-0 flex justify-center"
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="flex flex-col items-center text-muted-foreground"
        >
          <span className="mb-2 text-xs">Scroll to explore</span>
          <div className="flex h-8 w-5 items-start justify-center rounded-full border-2 border-muted-foreground/30 pt-1">
            <motion.div
              animate={{ y: [0, 10, 0] }}
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
