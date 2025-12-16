'use client';

import * as React from 'react';
import { motion, useInView } from 'framer-motion';

import { cn } from '@/lib/utils';

interface TextGenerateProps {
  text: string;
  className?: string;
  delay?: number;
  once?: boolean;
  as?: 'p' | 'h1' | 'h2' | 'h3' | 'h4' | 'span';
}

/**
 * Text Generate Effect
 *
 * Animates text word by word, creating a typewriter-like effect.
 */
export function TextGenerate({
  text,
  className,
  delay = 0,
  once = true,
  as: Component = 'p',
}: TextGenerateProps) {
  const ref = React.useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once, margin: '-50px' });

  const words = text.split(' ');

  const container = {
    hidden: { opacity: 0 },
    visible: (i = 1) => ({
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
        delayChildren: delay + 0.04 * i,
      },
    }),
  };

  const child = {
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring',
        damping: 12,
        stiffness: 100,
      },
    },
    hidden: {
      opacity: 0,
      y: 20,
    },
  };

  return (
    <motion.div
      ref={ref}
      variants={container}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      className={cn('flex flex-wrap', className)}
    >
      {words.map((word, index) => (
        <motion.span key={index} variants={child} className="mr-1">
          <Component className="inline">{word}</Component>
        </motion.span>
      ))}
    </motion.div>
  );
}

/**
 * Arabic Text Generate
 * RTL version for Arabic text
 */
export function ArabicTextGenerate({
  text,
  className,
  delay = 0,
  once = true,
}: TextGenerateProps) {
  const ref = React.useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once, margin: '-50px' });

  const words = text.split(' ');

  const container = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: delay,
      },
    },
  };

  const child = {
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring',
        damping: 15,
        stiffness: 80,
      },
    },
    hidden: {
      opacity: 0,
      y: 30,
    },
  };

  return (
    <motion.div
      ref={ref}
      variants={container}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      className={cn('flex flex-wrap justify-center', className)}
      dir="rtl"
      lang="ar"
    >
      {words.map((word, index) => (
        <motion.span
          key={index}
          variants={child}
          className="ml-2 font-arabic text-arabic-xl"
        >
          {word}
        </motion.span>
      ))}
    </motion.div>
  );
}

/**
 * Typing Effect
 * Classic typewriter effect for text
 */
interface TypingEffectProps {
  text: string;
  className?: string;
  speed?: number;
  delay?: number;
  cursor?: boolean;
}

export function TypingEffect({
  text,
  className,
  speed = 50,
  delay = 0,
  cursor = true,
}: TypingEffectProps) {
  const [displayText, setDisplayText] = React.useState('');
  const [isTyping, setIsTyping] = React.useState(false);
  const ref = React.useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });

  React.useEffect(() => {
    if (!isInView) return;

    const timeout = setTimeout(() => {
      setIsTyping(true);
      let currentIndex = 0;

      const interval = setInterval(() => {
        if (currentIndex <= text.length) {
          setDisplayText(text.slice(0, currentIndex));
          currentIndex++;
        } else {
          setIsTyping(false);
          clearInterval(interval);
        }
      }, speed);

      return () => clearInterval(interval);
    }, delay * 1000);

    return () => clearTimeout(timeout);
  }, [isInView, text, speed, delay]);

  return (
    <span ref={ref} className={cn('inline-block', className)}>
      {displayText}
      {cursor && (
        <motion.span
          animate={{ opacity: isTyping ? [1, 0] : 1 }}
          transition={{ duration: 0.5, repeat: isTyping ? Infinity : 0 }}
          className="ml-0.5 inline-block h-[1em] w-[2px] bg-current align-middle"
        />
      )}
    </span>
  );
}

/**
 * Gradient Text Animation
 * Text with animated gradient background
 */
interface GradientTextProps {
  text: string;
  className?: string;
  from?: string;
  via?: string;
  to?: string;
}

export function GradientText({
  text,
  className,
  from = 'from-gold-400',
  via = 'via-gold-500',
  to = 'to-emerald-500',
}: GradientTextProps) {
  return (
    <motion.span
      initial={{ backgroundPosition: '0% 50%' }}
      animate={{ backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'] }}
      transition={{ duration: 5, repeat: Infinity, ease: 'linear' }}
      className={cn(
        'inline-block bg-gradient-to-r bg-clip-text text-transparent',
        'bg-[length:200%_auto]',
        from,
        via,
        to,
        className
      )}
    >
      {text}
    </motion.span>
  );
}
