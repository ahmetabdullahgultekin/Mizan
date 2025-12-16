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

/**
 * Features Section
 *
 * Showcases the main features of Mizan with animated cards.
 */
export function Features() {
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
            Powerful{' '}
            <span className="text-gradient-gold">Features</span>
          </h2>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Everything you need for precise Quranic text analysis,
            built with scholarly accuracy and modern technology.
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
              key={feature.title}
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
            All features are{' '}
            <span className="text-gold-500">open source</span> and{' '}
            <span className="text-emerald-500">free to use</span>
          </p>
        </motion.div>
      </div>
    </section>
  );
}

/**
 * Feature definitions
 */
const features = [
  {
    icon: Hash,
    title: 'Letter Counting',
    description:
      'Multiple counting methods (Traditional, Uthmani Full, No Wasla) verified against Tanzil.net. Al-Fatiha = 139 letters.',
  },
  {
    icon: Calculator,
    title: 'Abjad Calculator',
    description:
      'Mashriqi and Maghribi numeral systems. All 28 letter values verified against scholarly standards. Basmalah = 786.',
  },
  {
    icon: BookOpen,
    title: 'Word Analysis',
    description:
      'Whitespace-delimited word counting following Tanzil standard. Full verse navigation with 6,236 verses across 114 surahs.',
  },
  {
    icon: Shield,
    title: 'Verified Accuracy',
    description:
      'Cross-referenced with Tanzil.net, Quran.com, IslamWeb, and classical scholarship. SHA-256 text integrity verification.',
  },
  {
    icon: Zap,
    title: 'High Performance',
    description:
      'FastAPI backend with Redis caching. Sub-millisecond response times for analysis operations. Async PostgreSQL.',
  },
  {
    icon: Globe,
    title: 'Multi-Script Support',
    description:
      'Uthmani, Simple, and Uthmani Minimal script variants. Full Arabic text normalization and diacritics handling.',
  },
  {
    icon: Code2,
    title: 'REST API',
    description:
      'Clean, well-documented REST API. OpenAPI specification with interactive documentation. Easy integration.',
  },
  {
    icon: Database,
    title: 'Scholarly Standards',
    description:
      'Following Modern Computational standards (Tanzil/Quran.com). Comprehensive documentation of methodologies.',
  },
];
