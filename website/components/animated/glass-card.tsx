'use client';

import * as React from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';

import { cn } from '@/lib/utils';
import { cardHover, hoverScale } from '@/lib/animations/variants';

interface GlassCardProps extends Omit<HTMLMotionProps<'div'>, 'children'> {
  children: React.ReactNode;
  glowColor?: 'gold' | 'emerald' | 'none';
  hoverEffect?: 'lift' | 'scale' | 'glow' | 'none';
}

/**
 * Animated Glass Card
 *
 * A glassmorphism card with smooth hover animations.
 */
export function AnimatedGlassCard({
  children,
  className,
  glowColor = 'none',
  hoverEffect = 'lift',
  ...props
}: GlassCardProps) {
  const glowClasses = {
    gold: 'hover:shadow-gold',
    emerald: 'hover:shadow-emerald',
    none: '',
  };

  const hoverVariants = {
    lift: cardHover,
    scale: hoverScale,
    glow: {
      initial: { boxShadow: '0 0 0 rgba(212, 175, 55, 0)' },
      hover: { boxShadow: '0 0 30px rgba(212, 175, 55, 0.3)' },
    },
    none: {},
  };

  return (
    <motion.div
      initial="initial"
      whileHover="hover"
      whileTap={hoverEffect === 'scale' ? 'tap' : undefined}
      variants={hoverVariants[hoverEffect]}
      className={cn(
        'glass-card rounded-xl p-6',
        'transition-colors duration-300',
        glowClasses[glowColor],
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
}

/**
 * Feature Card
 * A glass card optimized for feature sections
 */
interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  className?: string;
  delay?: number;
}

export function FeatureCard({ icon, title, description, className, delay = 0 }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ y: -5, transition: { duration: 0.2 } }}
      className={cn(
        'glass-card group relative overflow-hidden rounded-xl p-6',
        'border border-white/10 hover:border-white/20',
        'transition-colors duration-300',
        className
      )}
    >
      {/* Gradient overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-gold-500/5 to-emerald-500/5 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

      {/* Icon */}
      <div className="relative mb-4 inline-flex rounded-lg bg-gold-500/10 p-3 text-gold-500">
        {icon}
      </div>

      {/* Title */}
      <h3 className="relative mb-2 text-lg font-semibold text-foreground">{title}</h3>

      {/* Description */}
      <p className="relative text-sm text-muted-foreground">{description}</p>

      {/* Bottom highlight */}
      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-gold-500/50 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
    </motion.div>
  );
}

/**
 * Stat Card
 * A glass card for displaying statistics
 */
interface StatCardProps {
  value: string | number;
  label: string;
  icon?: React.ReactNode;
  trend?: { value: number; isPositive: boolean };
  className?: string;
  delay?: number;
}

export function StatCard({ value, label, icon, trend, className, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.5, delay }}
      className={cn('glass-card rounded-xl p-6 text-center', className)}
    >
      {icon && <div className="mb-3 inline-flex text-gold-500">{icon}</div>}

      <div className="text-3xl font-bold text-gradient-gold">{value}</div>

      <div className="mt-1 text-sm text-muted-foreground">{label}</div>

      {trend && (
        <div
          className={cn(
            'mt-2 inline-flex items-center text-xs font-medium',
            trend.isPositive ? 'text-emerald-500' : 'text-red-500'
          )}
        >
          <span className="mr-1">{trend.isPositive ? '↑' : '↓'}</span>
          {Math.abs(trend.value)}%
        </div>
      )}
    </motion.div>
  );
}

/**
 * Interactive Card
 * A card with click interaction
 */
interface InteractiveCardProps extends GlassCardProps {
  onClick?: () => void;
  selected?: boolean;
}

export function InteractiveCard({
  children,
  className,
  onClick,
  selected,
  ...props
}: InteractiveCardProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        'glass-card cursor-pointer rounded-xl p-4',
        'border-2 transition-colors duration-200',
        selected ? 'border-gold-500 bg-gold-500/5' : 'border-transparent hover:border-white/20',
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
}
