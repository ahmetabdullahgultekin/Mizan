'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  Heart,
  BookOpen,
  Shield,
  Globe,
  Github,
  ExternalLink,
  CheckCircle,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { GlowingOrbs } from '@/components/animated/floating-particles';
import { FeatureCard } from '@/components/animated/glass-card';
import { staggerContainer, staggerItem } from '@/lib/animations/variants';

/**
 * About Page
 *
 * Information about the Mizan project, its mission, and standards.
 */
export default function AboutPage() {
  return (
    <div className="relative min-h-screen pt-20">
      {/* Background */}
      <GlowingOrbs className="opacity-20" />

      <div className="container relative z-10 mx-auto px-4 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-16 text-center"
        >
          <Badge variant="gold" className="mb-4">
            <Heart className="mr-2 h-3 w-3" />
            About Mizan
          </Badge>
          <h1 className="mb-4 text-3xl font-bold md:text-4xl lg:text-5xl">
            Built with{' '}
            <span className="text-gradient-gold">Love</span>{' '}
            for the Ummah
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
            Mizan is an open-source Quranic text analysis engine, providing
            high-precision tools for scholars, researchers, and developers.
          </p>
        </motion.div>

        {/* Mission */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-16"
        >
          <div className="glass-card mx-auto max-w-3xl rounded-2xl p-8 text-center">
            <p
              className="mb-4 font-arabic text-arabic-xl text-gold-500"
              dir="rtl"
              lang="ar"
            >
              وَنَزَّلْنَا عَلَيْكَ الْكِتَابَ تِبْيَانًا لِّكُلِّ شَيْءٍ
            </p>
            <p className="text-sm text-muted-foreground italic">
              "And We have sent down to you the Book as clarification for all things"
              <br />
              — An-Nahl 16:89
            </p>

            <div className="mt-6 h-px w-full bg-gradient-to-r from-transparent via-gold-500/50 to-transparent" />

            <p className="mt-6 text-muted-foreground">
              Our mission is to provide accurate, verifiable tools for Quranic text
              analysis. We believe that technology should serve scholarship, not
              replace it. Every calculation is documented, every method is
              transparent, and every result is verifiable against authoritative
              sources.
            </p>
          </div>
        </motion.section>

        {/* Values */}
        <motion.section
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mb-16"
        >
          <h2 className="mb-8 text-center text-2xl font-bold">Our Values</h2>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <FeatureCard
              icon={<Shield className="h-6 w-6" />}
              title="Scholarly Accuracy"
              description="Every feature is verified against authoritative Islamic sources and scholarly standards."
              delay={0}
            />
            <FeatureCard
              icon={<Globe className="h-6 w-6" />}
              title="Open Source"
              description="Free and open for the entire Ummah. MIT licensed for maximum accessibility."
              delay={0.1}
            />
            <FeatureCard
              icon={<BookOpen className="h-6 w-6" />}
              title="Transparency"
              description="All methodologies are documented. Every calculation can be verified independently."
              delay={0.2}
            />
            <FeatureCard
              icon={<Heart className="h-6 w-6" />}
              title="Community Driven"
              description="Built by the community, for the community. Contributions are welcome."
              delay={0.3}
            />
          </div>
        </motion.section>

        {/* Standards */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          id="standards"
          className="mb-16"
        >
          <h2 className="mb-8 text-center text-2xl font-bold">
            Standards We Follow
          </h2>

          <div className="mx-auto max-w-3xl space-y-4">
            <StandardItem
              title="Tanzil.net"
              description="Primary source for Quranic text and letter counting verification"
              verified
            />
            <StandardItem
              title="Quran.com"
              description="Cross-reference for verse data and word counts"
              verified
            />
            <StandardItem
              title="IslamWeb"
              description="Classical scholarship reference for counting methodologies"
              verified
            />
            <StandardItem
              title="Wikipedia - Abjad Numerals"
              description="Verification of standard Abjad letter values"
              verified
            />
            <StandardItem
              title="Ibn Kathir's Methodology"
              description="Classical phonetic counting tradition (documented as alternative)"
              verified
            />
          </div>
        </motion.section>

        {/* Technical */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <h2 className="mb-8 text-center text-2xl font-bold">
            Technical Excellence
          </h2>

          <div className="glass-card mx-auto max-w-3xl rounded-xl p-6">
            <div className="grid gap-4 md:grid-cols-2">
              <TechItem label="Architecture" value="Hexagonal (Ports & Adapters)" />
              <TechItem label="Backend" value="FastAPI + Python 3.11+" />
              <TechItem label="Database" value="PostgreSQL + Redis" />
              <TechItem label="Frontend" value="Next.js 14 + React" />
              <TechItem label="Styling" value="Tailwind CSS + Framer Motion" />
              <TechItem label="Testing" value="138 tests, Property-based" />
              <TechItem label="License" value="MIT" />
              <TechItem label="Code Quality" value="MyPy strict, Ruff" />
            </div>
          </div>
        </motion.section>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <p className="mb-6 text-muted-foreground">
            Ready to contribute or have questions?
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button variant="glow" size="lg" asChild>
              <a
                href="https://github.com/ahmetabdullahgultekin/Mizan"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Github className="mr-2 h-4 w-4" />
                View on GitHub
              </a>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/docs">
                <BookOpen className="mr-2 h-4 w-4" />
                Read Documentation
              </Link>
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

/**
 * Standard Item Component
 */
function StandardItem({
  title,
  description,
  verified,
}: {
  title: string;
  description: string;
  verified?: boolean;
}) {
  return (
    <div className="glass-card flex items-start gap-4 rounded-xl p-4">
      <div className="mt-0.5 rounded-full bg-emerald-500/10 p-1">
        <CheckCircle className="h-4 w-4 text-emerald-500" />
      </div>
      <div>
        <h4 className="font-medium">{title}</h4>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      {verified && (
        <Badge variant="emerald" className="ml-auto">
          Verified
        </Badge>
      )}
    </div>
  );
}

/**
 * Tech Item Component
 */
function TechItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border py-2 last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
    </div>
  );
}
