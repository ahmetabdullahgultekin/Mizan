'use client';

import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

/**
 * Global Loading Component
 *
 * Displayed during route transitions in Next.js App Router.
 * Uses a simple, elegant loading animation.
 */
export default function Loading() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center gap-4"
      >
        {/* Animated Logo */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br from-gold-500 to-gold-600"
        >
          <Sparkles className="h-8 w-8 text-black" />
        </motion.div>

        {/* Loading Text */}
        <motion.p
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="text-sm text-muted-foreground"
        >
          Loading...
        </motion.p>
      </motion.div>
    </div>
  );
}
