'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { BookOpen, Hash, Calculator, CheckCircle } from 'lucide-react';

import { cn } from '@/lib/utils';
import { AnimatedCounterCard } from '@/components/animated/animated-counter';
import { staggerContainer } from '@/lib/animations/variants';

/**
 * Stats Section
 *
 * Displays key statistics about the Quran and Mizan's capabilities.
 */
export function Stats() {
  return (
    <section className="relative py-24">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-gold-500/5 to-transparent" />

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
            By The{' '}
            <span className="text-gradient-gold">Numbers</span>
          </h2>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Comprehensive coverage of the Holy Quran with verified accuracy.
          </p>
        </motion.div>

        {/* Stats Grid */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="grid gap-6 md:grid-cols-2 lg:grid-cols-4"
        >
          <AnimatedCounterCard
            value={114}
            label="Surahs"
            description="Complete coverage"
            icon={<BookOpen className="h-8 w-8" />}
            duration={2}
          />

          <AnimatedCounterCard
            value={6236}
            label="Verses"
            description="All verses indexed"
            icon={<Hash className="h-8 w-8" />}
            duration={2.5}
            delay={0.1}
          />

          <AnimatedCounterCard
            value={77430}
            label="Words"
            description="Tanzil standard"
            icon={<Calculator className="h-8 w-8" />}
            duration={3}
            delay={0.2}
          />

          <AnimatedCounterCard
            value={138}
            label="Tests Passing"
            description="Quality assured"
            icon={<CheckCircle className="h-8 w-8" />}
            duration={2}
            delay={0.3}
          />
        </motion.div>

        {/* Verified Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="mt-12 text-center"
        >
          <div className="inline-flex items-center rounded-full border border-emerald-500/30 bg-emerald-500/10 px-6 py-3">
            <CheckCircle className="mr-2 h-5 w-5 text-emerald-500" />
            <span className="text-sm font-medium text-emerald-500">
              Verified against Tanzil.net & scholarly standards
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
