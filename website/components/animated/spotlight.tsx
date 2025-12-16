'use client';

import * as React from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

import { cn } from '@/lib/utils';

interface SpotlightProps {
  className?: string;
  children?: React.ReactNode;
  spotlightColor?: string;
}

/**
 * Spotlight Effect
 *
 * Creates a mouse-following spotlight effect on hover.
 * Inspired by Apple's design language.
 */
export function Spotlight({
  className,
  children,
  spotlightColor = 'rgba(212, 175, 55, 0.15)', // Gold
}: SpotlightProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  // Smooth spring animation for mouse position
  const springX = useSpring(mouseX, { stiffness: 500, damping: 50 });
  const springY = useSpring(mouseY, { stiffness: 500, damping: 50 });

  const handleMouseMove = React.useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!containerRef.current) return;

      const rect = containerRef.current.getBoundingClientRect();
      mouseX.set(e.clientX - rect.left);
      mouseY.set(e.clientY - rect.top);
    },
    [mouseX, mouseY]
  );

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      className={cn('group relative overflow-hidden', className)}
    >
      {/* Spotlight gradient */}
      <motion.div
        className="pointer-events-none absolute -inset-px z-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100"
        style={{
          background: `radial-gradient(600px circle at ${springX}px ${springY}px, ${spotlightColor}, transparent 40%)`,
        }}
      />

      {/* Content */}
      <div className="relative z-10">{children}</div>
    </div>
  );
}

/**
 * Spotlight Card
 * A card component with built-in spotlight effect
 */
export function SpotlightCard({
  className,
  children,
}: {
  className?: string;
  children?: React.ReactNode;
}) {
  return (
    <Spotlight
      className={cn(
        'rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm',
        'transition-colors duration-300 hover:border-white/20',
        className
      )}
    >
      {children}
    </Spotlight>
  );
}

/**
 * Spotlight Button
 * A button with spotlight effect on hover
 */
interface SpotlightButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

export function SpotlightButton({ className, children, ...props }: SpotlightButtonProps) {
  const buttonRef = React.useRef<HTMLButtonElement>(null);
  const [position, setPosition] = React.useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    setPosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <button
      ref={buttonRef}
      onMouseMove={handleMouseMove}
      className={cn(
        'group relative overflow-hidden rounded-lg bg-gradient-to-r from-gold-500 to-gold-600 px-6 py-3 text-sm font-medium text-black',
        'transition-all duration-300 hover:shadow-gold',
        className
      )}
      {...props}
    >
      {/* Spotlight */}
      <span
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: `radial-gradient(120px circle at ${position.x}px ${position.y}px, rgba(255,255,255,0.3), transparent 40%)`,
        }}
      />

      {/* Content */}
      <span className="relative z-10">{children}</span>
    </button>
  );
}
