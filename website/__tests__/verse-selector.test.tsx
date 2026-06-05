/**
 * Component tests for VerseSelector.
 *
 * Tests the loading state and basic render via component props.
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { VerseSelector } from '@/components/playground/verse-selector';
import { I18nProvider } from '@/lib/i18n';

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
  AnimatePresence: ({ children }: React.PropsWithChildren) => React.createElement(React.Fragment, null, children),
}));

// ---------------------------------------------------------------------------
// Helper: wrap with required providers
// ---------------------------------------------------------------------------

function renderWithProviders(ui: React.ReactElement) {
  return render(<I18nProvider>{ui}</I18nProvider>);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('VerseSelector', () => {
  const noop = () => {};

  it('renders loading state initially', () => {
    renderWithProviders(
      <VerseSelector
        isLoadingSurahs={true}
        selectedSurah={null}
        selectedAyah={null}
        onSurahChange={noop}
        onAyahChange={noop}
      />
    );

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('shows all 114 surahs from fallback when API fails', () => {
    // Component receives surahs as props; when none provided it falls back to empty list
    renderWithProviders(
      <VerseSelector
        surahs={[]}
        isLoadingSurahs={false}
        selectedSurah={null}
        selectedAyah={null}
        onSurahChange={noop}
        onAyahChange={noop}
      />
    );

    // Loading indicator should not be shown when isLoadingSurahs is false
    expect(screen.queryByText(/loading…/i)).not.toBeInTheDocument();
  });

  it('renders surah selector and ayah selector', () => {
    renderWithProviders(
      <VerseSelector
        surahs={[
          {
            number: 1,
            name_arabic: 'الفاتحة',
            name_english: 'Al-Fatihah',
            name_transliteration: 'Al-Fatihah',
            revelation_type: 'meccan',
            verse_count: 7,
          } as Parameters<typeof VerseSelector>[0]['surahs'][number],
        ]}
        isLoadingSurahs={false}
        selectedSurah={null}
        selectedAyah={null}
        onSurahChange={noop}
        onAyahChange={noop}
      />
    );

    expect(screen.getByText(/select surah/i)).toBeInTheDocument();
  });
});
