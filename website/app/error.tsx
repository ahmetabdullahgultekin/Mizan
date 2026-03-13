'use client';

import { useEffect } from 'react';
import { AlertCircle, RotateCcw, Home } from 'lucide-react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-6 px-4 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10">
        <AlertCircle className="h-8 w-8 text-destructive" />
      </div>

      <div className="space-y-2">
        <h2 className="text-2xl font-semibold">Something went wrong</h2>
        <p className="max-w-md text-muted-foreground">
          An unexpected error occurred. Please try again or return to the home page.
        </p>
      </div>

      <div className="flex gap-3">
        <button
          onClick={reset}
          className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium hover:bg-accent transition-colors"
        >
          <RotateCcw className="h-4 w-4" />
          Try again
        </button>
        <a
          href="/"
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Home className="h-4 w-4" />
          Home
        </a>
      </div>

      {error.digest && (
        <p className="text-xs text-muted-foreground">Error ID: {error.digest}</p>
      )}
    </div>
  );
}
