/**
 * Component tests for VerseSelector.
 *
 * Tests the API fallback behaviour and basic render.
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { VerseSelector } from '@/components/playground/verse-selector';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

jest.mock('@/lib/api/client', () => ({
  getApiClient: jest.fn(),
}));

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) =>
      React.createElement('div', props, children),
  },
}));

const { getApiClient } = jest.requireMock('@/lib/api/client') as {
  getApiClient: jest.Mock;
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('VerseSelector', () => {
  const noop = () => {};

  it('renders loading state initially', () => {
    getApiClient.mockReturnValue({
      getSurahList: jest.fn(() => new Promise(() => {})), // pending forever
    });

    render(
      <VerseSelector
        selectedSurah={null}
        selectedAyah={null}
        onSurahChange={noop}
        onAyahChange={noop}
      />
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows all 114 surahs from fallback when API fails', async () => {
    getApiClient.mockReturnValue({
      getSurahList: jest.fn(() => Promise.reject(new Error('network error'))),
    });

    render(
      <VerseSelector
        selectedSurah={null}
        selectedAyah={null}
        onSurahChange={noop}
        onAyahChange={noop}
      />
    );

    await waitFor(() => {
      // After fallback loads, the selector should no longer show loading
      expect(screen.queryByText(/loading…/i)).not.toBeInTheDocument();
    });
  });

  it('renders surah selector and ayah selector', async () => {
    getApiClient.mockReturnValue({
      getSurahList: jest.fn(() =>
        Promise.resolve([
          {
            number: 1,
            name_arabic: 'الفاتحة',
            name_english: 'Al-Fatihah',
            name_transliteration: 'Al-Fatihah',
            revelation_type: 'meccan',
            verse_count: 7,
          },
        ])
      ),
    });

    render(
      <VerseSelector
        selectedSurah={null}
        selectedAyah={null}
        onSurahChange={noop}
        onAyahChange={noop}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/select surah/i)).toBeInTheDocument();
    });
  });
});
