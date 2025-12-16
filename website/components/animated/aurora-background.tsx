'use client';

import * as React from 'react';
import { motion } from 'framer-motion';

import { cn } from '@/lib/utils';

interface AuroraBackgroundProps {
  className?: string;
  children?: React.ReactNode;
  showRadialGradient?: boolean;
}

/**
 * Aurora Background Effect - Optimized for Performance
 *
 * Performance optimizations:
 * - Simple gradient background (no blur)
 * - Respect prefers-reduced-motion
 * - Memoized component
 * - Minimal animations
 */
const AuroraBackgroundComponent = ({
  className,
  children,
  showRadialGradient = true,
}: AuroraBackgroundProps) => {
  return (
    <div
      className={cn(
        'relative flex h-full w-full flex-col items-center justify-center overflow-hidden bg-background',
        className
      )}
    >
      {/* Aurora gradient layers - Simple CSS gradient */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Simple gradient - no blur, no animation */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            background: 'linear-gradient(135deg, rgba(212,175,55,0.2) 0%, transparent 40%, rgba(5,150,105,0.15) 70%, transparent 100%)',
          }}
        />

        {/* Static overlay for depth */}
        <div className="absolute inset-0 bg-background/70" />

        {/* Radial gradient overlay */}
        {showRadialGradient && (
          <div className="absolute inset-0 bg-gradient-radial from-transparent via-background/40 to-background" />
        )}
      </div>

      {/* Content - Minimal fade-in animation */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
        className="relative z-10"
      >
        {children}
      </motion.div>
    </div>
  );
};

export const AuroraBackground = React.memo(AuroraBackgroundComponent);

/**
 * Simple Aurora Gradient - Optimized
 * A lighter version for subtle backgrounds
 */
const AuroraGradientComponent = ({ className }: { className?: string }) => {
  return (
    <div className={cn('absolute inset-0 overflow-hidden', className)}>
      <div
        className={cn(
          'absolute -inset-[100%] opacity-20',
          'bg-gradient-conic from-gold-500/20 via-emerald-500/20 to-gold-500/20',
          'animate-spin-slow',
          'motion-reduce:animate-none'
        )}
      />
      <div className="absolute inset-0 bg-background/90" />
    </div>
  );
};

export const AuroraGradient = React.memo(AuroraGradientComponent);
