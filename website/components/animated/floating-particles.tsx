'use client';

import * as React from 'react';
import { motion } from 'framer-motion';

import { cn } from '@/lib/utils';

interface Particle {
  id: number;
  x: number;
  y: number;
  size: number;
  duration: number;
  delay: number;
}

interface FloatingParticlesProps {
  className?: string;
  count?: number;
  color?: string;
  minSize?: number;
  maxSize?: number;
}

/**
 * Floating Particles Effect - Optimized for Performance
 *
 * Performance optimizations:
 * - Uses CSS animations instead of Framer Motion
 * - Reduced particle count to 5
 * - Respect prefers-reduced-motion
 * - Fixed positions for consistent rendering
 */
const FloatingParticlesComponent = ({
  className,
  count = 5,
  color = 'bg-gold-500',
}: FloatingParticlesProps) => {
  // Fixed positions for deterministic rendering
  const particles = [
    { id: 0, x: 15, y: 25, size: 3 },
    { id: 1, x: 75, y: 15, size: 4 },
    { id: 2, x: 45, y: 65, size: 3 },
    { id: 3, x: 85, y: 55, size: 2 },
    { id: 4, x: 25, y: 80, size: 3 },
  ].slice(0, count);

  return (
    <div className={cn('pointer-events-none absolute inset-0 overflow-hidden', className)}>
      {particles.map((particle) => (
        <div
          key={particle.id}
          className={cn(
            'absolute rounded-full opacity-20 animate-pulse-slow motion-reduce:animate-none',
            color
          )}
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            width: particle.size,
            height: particle.size,
            animationDelay: `${particle.id * 0.5}s`,
          }}
        />
      ))}
    </div>
  );
};

export const FloatingParticles = React.memo(FloatingParticlesComponent);

/**
 * Geometric Floating Elements - Optimized for Performance
 * Static Islamic-inspired geometric shapes
 * Uses CSS animation instead of Framer Motion for better FPS
 */
const GeometricFloatingComponent = ({ className }: { className?: string }) => {
  // Fixed positions for consistent rendering
  const shapes = [
    { id: 0, x: 10, y: 20, size: 30, type: 'star' },
    { id: 1, x: 85, y: 70, size: 25, type: 'hexagon' },
    { id: 2, x: 50, y: 85, size: 20, type: 'diamond' },
  ];

  return (
    <div className={cn('pointer-events-none absolute inset-0 overflow-hidden', className)}>
      {shapes.map((shape) => (
        <div
          key={shape.id}
          className="absolute opacity-[0.03] animate-spin-slow motion-reduce:animate-none"
          style={{
            left: `${shape.x}%`,
            top: `${shape.y}%`,
            animationDuration: `${40 + shape.id * 10}s`,
          }}
        >
          {shape.type === 'star' && (
            <svg
              width={shape.size}
              height={shape.size}
              viewBox="0 0 24 24"
              fill="currentColor"
              className="text-gold-500"
            >
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
          )}
          {shape.type === 'hexagon' && (
            <svg
              width={shape.size}
              height={shape.size}
              viewBox="0 0 24 24"
              fill="currentColor"
              className="text-emerald-500"
            >
              <path d="M12 2l9 5v10l-9 5-9-5V7l9-5z" />
            </svg>
          )}
          {shape.type === 'diamond' && (
            <svg
              width={shape.size}
              height={shape.size}
              viewBox="0 0 24 24"
              fill="currentColor"
              className="text-gold-500"
            >
              <path d="M12 2L2 12l10 10 10-10L12 2z" />
            </svg>
          )}
        </div>
      ))}
    </div>
  );
};

export const GeometricFloating = React.memo(GeometricFloatingComponent);

/**
 * Glowing Orbs - Optimized for Performance
 * Static gradient orbs - no animation for better FPS
 * Uses CSS gradients instead of blur for GPU efficiency
 */
const GlowingOrbsComponent = ({ className }: { className?: string }) => {
  return (
    <div className={cn('pointer-events-none absolute inset-0 overflow-hidden', className)}>
      {/* Gold orb - static gradient, no blur */}
      <div
        className="absolute -left-20 top-1/4 h-80 w-80 rounded-full opacity-15"
        style={{
          background: 'radial-gradient(circle, rgba(212,175,55,0.4) 0%, transparent 70%)',
        }}
      />

      {/* Emerald orb - static gradient, no blur */}
      <div
        className="absolute -right-20 bottom-1/4 h-80 w-80 rounded-full opacity-15"
        style={{
          background: 'radial-gradient(circle, rgba(5,150,105,0.4) 0%, transparent 70%)',
        }}
      />

      {/* Center orb - subtle static glow */}
      <div
        className="absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full opacity-10"
        style={{
          background: 'radial-gradient(circle, rgba(212,175,55,0.3) 0%, transparent 60%)',
        }}
      />
    </div>
  );
};

export const GlowingOrbs = React.memo(GlowingOrbsComponent);
