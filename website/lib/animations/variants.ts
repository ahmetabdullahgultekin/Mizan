/**
 * Framer Motion Animation Variants
 *
 * Centralized animation configurations for consistent motion design.
 * Following the DRY principle for reusable animations.
 */

import { type Variants, type Transition } from 'framer-motion';

// ==========================================
// Transition Presets
// ==========================================

export const transitions = {
  spring: {
    type: 'spring',
    stiffness: 400,
    damping: 30,
  } as Transition,

  springBouncy: {
    type: 'spring',
    stiffness: 300,
    damping: 20,
  } as Transition,

  smooth: {
    duration: 0.5,
    ease: [0.25, 0.1, 0.25, 1],
  } as Transition,

  smoothSlow: {
    duration: 0.8,
    ease: [0.25, 0.1, 0.25, 1],
  } as Transition,

  bounce: {
    type: 'spring',
    stiffness: 500,
    damping: 25,
  } as Transition,

  gentle: {
    duration: 0.6,
    ease: [0.4, 0, 0.2, 1],
  } as Transition,
};

// ==========================================
// Fade Variants
// ==========================================

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: transitions.smooth,
  },
  exit: { opacity: 0 },
};

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: transitions.smooth,
  },
  exit: { opacity: 0, y: -10 },
};

export const fadeInDown: Variants = {
  hidden: { opacity: 0, y: -20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: transitions.smooth,
  },
  exit: { opacity: 0, y: 10 },
};

export const fadeInLeft: Variants = {
  hidden: { opacity: 0, x: -20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: transitions.smooth,
  },
  exit: { opacity: 0, x: -10 },
};

export const fadeInRight: Variants = {
  hidden: { opacity: 0, x: 20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: transitions.smooth,
  },
  exit: { opacity: 0, x: 10 },
};

// ==========================================
// Scale Variants
// ==========================================

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: transitions.spring,
  },
  exit: { opacity: 0, scale: 0.95 },
};

export const scaleInBounce: Variants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: transitions.springBouncy,
  },
  exit: { opacity: 0, scale: 0.8 },
};

export const popIn: Variants = {
  hidden: { opacity: 0, scale: 0.5 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: transitions.bounce,
  },
  exit: { opacity: 0, scale: 0.5 },
};

// ==========================================
// Stagger Variants
// ==========================================

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

export const staggerContainerFast: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.05,
    },
  },
};

export const staggerContainerSlow: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
      delayChildren: 0.2,
    },
  },
};

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: transitions.smooth,
  },
};

// ==========================================
// Slide Variants
// ==========================================

export const slideInFromBottom: Variants = {
  hidden: { opacity: 0, y: 50 },
  visible: {
    opacity: 1,
    y: 0,
    transition: transitions.smoothSlow,
  },
  exit: { opacity: 0, y: 50 },
};

export const slideInFromTop: Variants = {
  hidden: { opacity: 0, y: -50 },
  visible: {
    opacity: 1,
    y: 0,
    transition: transitions.smoothSlow,
  },
  exit: { opacity: 0, y: -50 },
};

export const slideInFromLeft: Variants = {
  hidden: { opacity: 0, x: -50 },
  visible: {
    opacity: 1,
    x: 0,
    transition: transitions.smoothSlow,
  },
  exit: { opacity: 0, x: -50 },
};

export const slideInFromRight: Variants = {
  hidden: { opacity: 0, x: 50 },
  visible: {
    opacity: 1,
    x: 0,
    transition: transitions.smoothSlow,
  },
  exit: { opacity: 0, x: 50 },
};

// ==========================================
// Interactive Variants
// ==========================================

export const hoverScale: Variants = {
  initial: { scale: 1 },
  hover: { scale: 1.02 },
  tap: { scale: 0.98 },
};

export const hoverScaleLarge: Variants = {
  initial: { scale: 1 },
  hover: { scale: 1.05 },
  tap: { scale: 0.95 },
};

export const hoverLift: Variants = {
  initial: { y: 0 },
  hover: { y: -4 },
};

export const hoverGlow: Variants = {
  initial: { boxShadow: '0 0 0 rgba(212, 175, 55, 0)' },
  hover: { boxShadow: '0 0 20px rgba(212, 175, 55, 0.3)' },
};

// ==========================================
// Text Animation Variants
// ==========================================

export const textReveal: Variants = {
  hidden: { opacity: 0 },
  visible: (i: number = 0) => ({
    opacity: 1,
    transition: {
      delay: i * 0.05,
      duration: 0.5,
    },
  }),
};

export const letterStagger: Variants = {
  hidden: { opacity: 0, y: 50 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      staggerChildren: 0.03,
    },
  },
};

export const letter: Variants = {
  hidden: { opacity: 0, y: 50 },
  visible: {
    opacity: 1,
    y: 0,
  },
};

// ==========================================
// Card Variants
// ==========================================

export const cardHover: Variants = {
  initial: {
    y: 0,
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
  },
  hover: {
    y: -8,
    boxShadow: '0 20px 40px rgba(0, 0, 0, 0.4)',
    transition: transitions.spring,
  },
};

export const glassCardHover: Variants = {
  initial: {
    background: 'rgba(255, 255, 255, 0.03)',
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  hover: {
    background: 'rgba(255, 255, 255, 0.05)',
    borderColor: 'rgba(255, 255, 255, 0.12)',
    transition: { duration: 0.3 },
  },
};

// ==========================================
// Number Counter Variants
// ==========================================

export const counterSpring = {
  type: 'spring',
  stiffness: 100,
  damping: 30,
  mass: 1,
};

// ==========================================
// Page Transition Variants
// ==========================================

export const pageTransition: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.25, 0.1, 0.25, 1],
    },
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: {
      duration: 0.3,
    },
  },
};

// ==========================================
// Floating Animation
// ==========================================

export const float: Variants = {
  initial: { y: 0 },
  animate: {
    y: [-10, 10, -10],
    transition: {
      duration: 4,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};

export const floatSlow: Variants = {
  initial: { y: 0 },
  animate: {
    y: [-5, 5, -5],
    transition: {
      duration: 6,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};

// ==========================================
// Pulse Animation
// ==========================================

export const pulse: Variants = {
  initial: { scale: 1, opacity: 1 },
  animate: {
    scale: [1, 1.05, 1],
    opacity: [1, 0.8, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};

// ==========================================
// Shimmer Effect
// ==========================================

export const shimmer: Variants = {
  initial: { backgroundPosition: '-200% 0' },
  animate: {
    backgroundPosition: ['200% 0', '-200% 0'],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'linear',
    },
  },
};
