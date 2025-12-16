'use client';

import * as React from 'react';
import { usePathname } from 'next/navigation';

/**
 * Scroll to Top Component
 *
 * Automatically scrolls to top on route changes.
 * Respects prefers-reduced-motion for smooth scrolling.
 */
export function ScrollToTop() {
  const pathname = usePathname();
  const [prefersReducedMotion, setPrefersReducedMotion] = React.useState(false);

  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const listener = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', listener);
    return () => mediaQuery.removeEventListener('change', listener);
  }, []);

  React.useEffect(() => {
    window.scrollTo({
      top: 0,
      left: 0,
      behavior: prefersReducedMotion ? 'auto' : 'smooth',
    });
  }, [pathname, prefersReducedMotion]);

  return null;
}
