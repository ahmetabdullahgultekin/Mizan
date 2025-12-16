'use client';

import * as React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowLeft, Construction, Clock, Bell } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface ComingSoonProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  expectedDate?: string;
}

/**
 * Coming Soon Page Component
 *
 * Reusable component for pages that are under development.
 */
export function ComingSoon({
  title,
  description,
  icon,
  expectedDate,
}: ComingSoonProps) {
  return (
    <div className="relative min-h-screen pt-20">
      <div className="container mx-auto px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mx-auto max-w-2xl text-center"
        >
          {/* Icon */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring' }}
            className="mb-8 inline-flex h-20 w-20 items-center justify-center rounded-2xl bg-gold-500/10"
          >
            {icon || <Construction className="h-10 w-10 text-gold-500" />}
          </motion.div>

          {/* Badge */}
          <Badge variant="gold" className="mb-6">
            <Clock className="mr-2 h-3 w-3" />
            Coming Soon
          </Badge>

          {/* Title */}
          <h1 className="mb-4 text-3xl font-bold md:text-4xl lg:text-5xl">
            {title}
          </h1>

          {/* Description */}
          <p className="mb-8 text-lg text-muted-foreground">
            {description}
          </p>

          {/* Expected Date */}
          {expectedDate && (
            <p className="mb-8 text-sm text-muted-foreground">
              Expected: <span className="text-gold-500">{expectedDate}</span>
            </p>
          )}

          {/* Decorative Element */}
          <div className="mb-8 flex justify-center">
            <div className="h-px w-32 bg-gradient-to-r from-transparent via-gold-500/50 to-transparent" />
          </div>

          {/* Arabic Text */}
          <p
            className="mb-8 font-arabic text-lg text-gold-500/70"
            dir="rtl"
            lang="ar"
          >
            صَبْرًا جَمِيلًا
          </p>
          <p className="mb-8 text-xs text-muted-foreground italic">
            "Beautiful patience" - Yusuf 12:18
          </p>

          {/* Actions */}
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button variant="glow" asChild>
              <Link href="/">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Home
              </Link>
            </Button>

            <Button variant="outline" asChild>
              <Link href="/playground">
                Try Playground
              </Link>
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
