'use client';

import * as React from 'react';
import { ThemeProvider as NextThemesProvider } from 'next-themes';
import { type ThemeProviderProps } from 'next-themes/dist/types';
import { Toaster } from 'sonner';

import { ApiProvider } from '@/lib/api/provider';
import { siteConfig } from '@/config/site';

interface ProvidersProps {
  children: React.ReactNode;
  themeProps?: ThemeProviderProps;
}

export function Providers({ children, themeProps }: ProvidersProps) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem
      disableTransitionOnChange
      {...themeProps}
    >
      <ApiProvider baseUrl={siteConfig.api.baseUrl}>
        {children}
        <Toaster
          position="bottom-right"
          toastOptions={{
            className: 'glass-card',
            duration: 4000,
          }}
        />
      </ApiProvider>
    </NextThemesProvider>
  );
}
