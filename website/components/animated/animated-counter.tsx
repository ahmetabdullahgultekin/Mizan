'use client';

import * as React from 'react';
import { motion, useSpring, useTransform, useInView } from 'framer-motion';

import { cn } from '@/lib/utils';
import { formatNumber, formatArabicNumber } from '@/lib/utils';

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  delay?: number;
  className?: string;
  locale?: 'en' | 'ar';
  prefix?: string;
  suffix?: string;
  once?: boolean;
}

/**
 * Animated Counter Component
 *
 * Smoothly animates a number from 0 to the target value.
 * Uses Framer Motion springs for natural motion.
 */
export function AnimatedCounter({
  value,
  duration = 2,
  delay = 0,
  className,
  locale = 'en',
  prefix = '',
  suffix = '',
  once = true,
}: AnimatedCounterProps) {
  const ref = React.useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once, margin: '-50px' });

  // Spring animation for smooth counting
  const spring = useSpring(0, {
    stiffness: 50,
    damping: 30,
    duration: duration * 1000,
  });

  // Transform spring value to display value
  const display = useTransform(spring, (latest) =>
    locale === 'ar' ? formatArabicNumber(Math.round(latest)) : formatNumber(Math.round(latest))
  );

  React.useEffect(() => {
    if (isInView) {
      const timeout = setTimeout(() => {
        spring.set(value);
      }, delay * 1000);

      return () => clearTimeout(timeout);
    }
  }, [isInView, spring, value, delay]);

  return (
    <span ref={ref} className={cn('tabular-nums', className)}>
      {prefix}
      <motion.span>{display}</motion.span>
      {suffix}
    </span>
  );
}

/**
 * Animated Counter Card
 * A styled card with an animated counter
 */
interface AnimatedCounterCardProps extends AnimatedCounterProps {
  label: string;
  icon?: React.ReactNode;
  description?: string;
}

export function AnimatedCounterCard({
  value,
  label,
  icon,
  description,
  className,
  ...props
}: AnimatedCounterCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.5 }}
      className={cn(
        'glass-card-hover flex flex-col items-center justify-center p-6 text-center',
        className
      )}
    >
      {icon && <div className="mb-4 text-gold-500">{icon}</div>}

      <AnimatedCounter
        value={value}
        className="text-4xl font-bold text-gradient-gold"
        {...props}
      />

      <p className="mt-2 text-sm font-medium text-foreground">{label}</p>

      {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
    </motion.div>
  );
}

/**
 * Inline Animated Number
 * For use within text content
 */
export function AnimatedNumber({
  value,
  className,
  ...props
}: Omit<AnimatedCounterProps, 'prefix' | 'suffix'>) {
  return (
    <AnimatedCounter
      value={value}
      className={cn('inline-block font-semibold text-primary', className)}
      {...props}
    />
  );
}

/**
 * Animated Percentage
 * Displays an animated percentage value
 */
interface AnimatedPercentageProps extends Omit<AnimatedCounterProps, 'suffix'> {
  showProgressBar?: boolean;
  barColor?: string;
}

export function AnimatedPercentage({
  value,
  showProgressBar = false,
  barColor = 'bg-gold-500',
  className,
  ...props
}: AnimatedPercentageProps) {
  const ref = React.useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <div ref={ref} className={cn('w-full', className)}>
      <div className="flex items-center justify-between">
        <AnimatedCounter value={value} suffix="%" {...props} />
      </div>

      {showProgressBar && (
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-muted">
          <motion.div
            initial={{ width: 0 }}
            animate={isInView ? { width: `${value}%` } : { width: 0 }}
            transition={{ duration: 1, delay: 0.5, ease: 'easeOut' }}
            className={cn('h-full rounded-full', barColor)}
          />
        </div>
      )}
    </div>
  );
}
