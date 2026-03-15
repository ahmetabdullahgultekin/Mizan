'use client';

import * as React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Github, BookOpen } from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { SpotlightButton } from '@/components/animated/spotlight';
import { ArabicTextGenerate } from '@/components/animated/text-generate';
import { useI18n } from '@/lib/i18n';

/**
 * CTA (Call to Action) Section
 *
 * Final section encouraging users to try the playground or contribute.
 */
export function CTA() {
  const { t } = useI18n();

  return (
    <section className="relative py-24">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent to-gold-500/5" />

      <div className="container relative z-10 mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="mx-auto max-w-3xl text-center"
        >
          {/* Arabic Quote */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="mb-8"
          >
            <p
              className="font-arabic text-arabic-lg text-gold-500/70"
              dir="rtl"
              lang="ar"
            >
              وَرَتِّلِ الْقُرْآنَ تَرْتِيلًا
            </p>
            <p className="mt-2 text-sm text-muted-foreground italic">
              {t('cta.quoteTranslation')}
            </p>
          </motion.div>

          {/* Main CTA */}
          <h2 className="mb-6 text-3xl font-bold md:text-4xl lg:text-5xl">
            {t('cta.title')}{' '}
            <span className="text-gradient-gold">{t('cta.titleHighlight')}</span>
            ?
          </h2>

          <p className="mb-8 text-lg text-muted-foreground">
            {t('cta.description')}
          </p>

          {/* Buttons */}
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <SpotlightButton className="group px-8 py-4 text-base">
              <Link href="/playground" className="flex items-center">
                {t('cta.openPlayground')}
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </SpotlightButton>

            <Button variant="outline" size="lg" className="group" asChild>
              <a
                href="https://github.com/ahmetabdullahgultekin/Mizan"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Github className="mr-2 h-4 w-4" />
                {t('cta.starGithub')}
              </a>
            </Button>

            <Button variant="ghost" size="lg" asChild>
              <Link href="/docs">
                <BookOpen className="mr-2 h-4 w-4" />
                {t('cta.readDocs')}
              </Link>
            </Button>
          </div>

          {/* Social proof */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.6 }}
            className="mt-12 flex flex-wrap items-center justify-center gap-8 text-sm text-muted-foreground"
          >
            <div className="flex items-center">
              <span className="mr-2 font-semibold text-foreground">MIT</span>
              {t('cta.mitLicensed')}
            </div>
            <div className="h-4 w-px bg-border" />
            <div className="flex items-center">
              <span className="mr-2 font-semibold text-foreground">100%</span>
              {t('cta.openSource')}
            </div>
            <div className="h-4 w-px bg-border" />
            <div className="flex items-center">
              <span className="mr-2 font-semibold text-foreground">{t('cta.scholarly')}</span>
              {t('cta.verified')}
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
