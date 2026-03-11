'use client';

import { motion } from 'framer-motion';
import { BookOpen, Home, Search } from 'lucide-react';
import Link from 'next/link';

/**
 * 404 Not Found Page
 *
 * Displayed by Next.js App Router when a route is not matched.
 */
export default function NotFound() {
  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col items-center justify-center px-4 text-center">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex flex-col items-center gap-6 max-w-md"
      >
        {/* Icon */}
        <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-gold-500/20 to-gold-600/10 border border-gold-500/20">
          <BookOpen className="h-10 w-10 text-gold-500" />
        </div>

        {/* Heading */}
        <div className="space-y-2">
          <p className="text-6xl font-bold text-muted-foreground/40 font-mono">404</p>
          <h1 className="text-2xl font-semibold tracking-tight">Page not found</h1>
          <p className="text-sm text-muted-foreground">
            The page you&apos;re looking for doesn&apos;t exist or has been moved.
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-lg bg-gold-500 px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-gold-400"
          >
            <Home className="h-4 w-4" />
            Go home
          </Link>
          <Link
            href="/search"
            className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium transition-colors hover:bg-accent"
          >
            <Search className="h-4 w-4" />
            Search Quran
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
