# Mizan Website Architecture Document

> **Version:** 1.0.0
> **Date:** 2025-12-16
> **Status:** Approved for Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Software Engineering Principles Compliance](#software-engineering-principles-compliance)
3. [Architecture Overview](#architecture-overview)
4. [Component Architecture](#component-architecture)
5. [Design Patterns Applied](#design-patterns-applied)
6. [Data Flow Architecture](#data-flow-architecture)
7. [Performance Architecture](#performance-architecture)
8. [Security Considerations](#security-considerations)
9. [Accessibility Standards](#accessibility-standards)
10. [Technology Stack Rationale](#technology-stack-rationale)

---

## Executive Summary

The Mizan Website is a high-performance, interactive web application that showcases the Mizan Quranic Text Analysis Engine. It consists of:

- **Landing Page**: Introducing Mizan with stunning animations
- **Interactive Playground**: Real-time Quranic text analysis
- **API Documentation**: Comprehensive developer resources
- **About Page**: Project mission and scholarly standards

---

## Software Engineering Principles Compliance

### SOLID Principles

| Principle | Implementation |
|-----------|----------------|
| **S**ingle Responsibility | Each component has ONE purpose. `VerseSelector` only handles verse selection, `AnalysisResults` only displays results. |
| **O**pen/Closed | Components are open for extension via props/composition, closed for modification. Base components accept `className` for styling extensions. |
| **L**iskov Substitution | All UI components follow consistent interfaces. Any `Button` variant can replace another without breaking behavior. |
| **I**nterface Segregation | Props interfaces are granular. `AnalysisResultsProps` doesn't include unrelated properties. |
| **D**ependency Inversion | Components depend on abstractions (hooks, contexts) not concrete implementations. API client is injected via context. |

### DRY (Don't Repeat Yourself)

```
✓ Shared animation variants in lib/animations.ts
✓ Reusable UI primitives in components/ui/
✓ Common API logic abstracted into hooks
✓ Consistent styling via Tailwind design tokens
✓ Shared types in types/ directory
```

### KISS (Keep It Simple, Stupid)

```
✓ Flat component structure (max 3 levels deep)
✓ Prefer composition over inheritance
✓ Simple state management (React hooks, no Redux overhead)
✓ Clear naming conventions
✓ Minimal abstraction layers
```

### YAGNI (You Aren't Gonna Need It)

```
✓ No premature optimization
✓ No unused feature scaffolding
✓ No speculative generality
✓ Build only what's needed for MVP
✓ Add complexity only when required
```

### Separation of Concerns

```
├── Presentation Layer    → components/
├── Business Logic        → hooks/
├── Data Access Layer     → lib/api/
├── Styling Layer         → styles/ + Tailwind
└── Configuration Layer   → config/
```

### Clean Code Practices

| Practice | Implementation |
|----------|----------------|
| Meaningful Names | `useVerseAnalysis`, `LetterCountDisplay`, `AbjadCalculator` |
| Small Functions | Each function does ONE thing, <20 lines |
| No Side Effects | Pure components where possible |
| Comments | Self-documenting code, JSDoc for public APIs |
| Error Handling | Graceful degradation, user-friendly messages |
| Consistent Formatting | ESLint + Prettier enforced |

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   Landing   │ │  Playground │ │    Docs     │ │   About   │ │
│  │    Page     │ │    Page     │ │    Page     │ │   Page    │ │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └─────┬─────┘ │
│         │               │               │               │       │
│  ┌──────┴───────────────┴───────────────┴───────────────┴─────┐ │
│  │                    COMPONENT LAYER                          │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │ │
│  │  │   UI    │ │ Landing │ │Playground│ │  Docs   │          │ │
│  │  │ (base)  │ │ (hero)  │ │(analysis)│ │ (api)   │          │ │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        LOGIC LAYER                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │    Hooks     │ │   Contexts   │ │   Utilities  │            │
│  │ useAnalysis  │ │  ApiContext  │ │  formatters  │            │
│  │ useVerse     │ │ ThemeContext │ │  validators  │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      API Client                           │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐           │  │
│  │  │  analyze   │ │   verse    │ │   surah    │           │  │
│  │  │  service   │ │  service   │ │  service   │           │  │
│  │  └────────────┘ └────────────┘ └────────────┘           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Mizan Backend API (FastAPI)                  │  │
│  │              https://api.mizan.app                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
website/
├── app/                          # Next.js 14 App Router
│   ├── layout.tsx               # Root layout (providers, fonts)
│   ├── page.tsx                 # Landing page
│   ├── playground/
│   │   └── page.tsx             # Interactive playground
│   ├── docs/
│   │   └── page.tsx             # API documentation
│   ├── about/
│   │   └── page.tsx             # About page
│   └── globals.css              # Global styles
│
├── components/                   # React components
│   ├── ui/                      # Base UI primitives (shadcn/ui)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── tabs.tsx
│   │   └── tooltip.tsx
│   │
│   ├── animated/                # Aceternity/Magic UI components
│   │   ├── aurora-background.tsx
│   │   ├── spotlight.tsx
│   │   ├── animated-counter.tsx
│   │   ├── floating-particles.tsx
│   │   ├── glass-card.tsx
│   │   └── text-generate.tsx
│   │
│   ├── landing/                 # Landing page sections
│   │   ├── hero.tsx
│   │   ├── features.tsx
│   │   ├── demo-preview.tsx
│   │   ├── stats.tsx
│   │   ├── testimonials.tsx
│   │   └── cta.tsx
│   │
│   ├── playground/              # Playground components
│   │   ├── verse-selector.tsx
│   │   ├── text-input.tsx
│   │   ├── analysis-results.tsx
│   │   ├── letter-breakdown.tsx
│   │   ├── abjad-display.tsx
│   │   ├── method-selector.tsx
│   │   └── history-panel.tsx
│   │
│   ├── docs/                    # Documentation components
│   │   ├── api-explorer.tsx
│   │   ├── code-block.tsx
│   │   ├── endpoint-card.tsx
│   │   └── response-preview.tsx
│   │
│   ├── layout/                  # Layout components
│   │   ├── navbar.tsx
│   │   ├── footer.tsx
│   │   ├── sidebar.tsx
│   │   └── mobile-menu.tsx
│   │
│   └── shared/                  # Shared components
│       ├── arabic-text.tsx
│       ├── loading-spinner.tsx
│       ├── error-boundary.tsx
│       └── seo-head.tsx
│
├── hooks/                       # Custom React hooks
│   ├── use-verse-analysis.ts
│   ├── use-verse.ts
│   ├── use-surah-list.ts
│   ├── use-local-storage.ts
│   ├── use-debounce.ts
│   └── use-media-query.ts
│
├── lib/                         # Utilities and services
│   ├── api/                     # API client
│   │   ├── client.ts           # Base HTTP client
│   │   ├── endpoints.ts        # API endpoints
│   │   ├── types.ts            # API types
│   │   └── errors.ts           # Error handling
│   │
│   ├── animations/              # Animation configurations
│   │   ├── variants.ts         # Framer Motion variants
│   │   └── transitions.ts      # Transition presets
│   │
│   └── utils/                   # Utility functions
│       ├── formatters.ts       # Number/text formatters
│       ├── validators.ts       # Input validation
│       └── cn.ts               # className utility
│
├── types/                       # TypeScript types
│   ├── api.ts                  # API response types
│   ├── analysis.ts             # Analysis types
│   ├── verse.ts                # Verse/Surah types
│   └── ui.ts                   # UI component types
│
├── config/                      # Configuration
│   ├── site.ts                 # Site metadata
│   ├── navigation.ts           # Navigation config
│   └── api.ts                  # API configuration
│
├── public/                      # Static assets
│   ├── fonts/                  # Arabic fonts
│   │   ├── Amiri-Regular.woff2
│   │   ├── Amiri-Bold.woff2
│   │   ├── Cairo-Variable.woff2
│   │   └── IBMPlexSansArabic.woff2
│   │
│   ├── images/                 # Images
│   │   ├── logo.svg
│   │   ├── og-image.png
│   │   └── favicon.ico
│   │
│   └── patterns/               # Islamic geometric patterns
│       ├── geometric-1.svg
│       ├── geometric-2.svg
│       └── arabesque.svg
│
├── styles/                      # Additional styles
│   └── arabic.css              # Arabic typography styles
│
├── next.config.js              # Next.js configuration
├── tailwind.config.ts          # Tailwind configuration
├── tsconfig.json               # TypeScript configuration
├── package.json                # Dependencies
└── README.md                   # Project documentation
```

---

## Component Architecture

### Component Hierarchy

```
App (layout.tsx)
├── Providers
│   ├── ThemeProvider
│   ├── ApiProvider
│   └── ToastProvider
│
├── Navbar
│   ├── Logo
│   ├── NavLinks
│   ├── ThemeToggle
│   └── MobileMenu
│
├── Main Content (page.tsx)
│   │
│   ├── [Landing Page]
│   │   ├── Hero
│   │   │   ├── AuroraBackground
│   │   │   ├── AnimatedText
│   │   │   ├── CTAButtons
│   │   │   └── FloatingParticles
│   │   │
│   │   ├── Features
│   │   │   └── FeatureCard[] (mapped)
│   │   │       ├── GlassCard
│   │   │       ├── AnimatedIcon
│   │   │       └── Description
│   │   │
│   │   ├── DemoPreview
│   │   │   ├── MiniPlayground
│   │   │   └── ResultsPreview
│   │   │
│   │   ├── Stats
│   │   │   └── AnimatedCounter[] (mapped)
│   │   │
│   │   └── CTA
│   │       ├── Spotlight
│   │       └── ActionButtons
│   │
│   ├── [Playground Page]
│   │   ├── PlaygroundHeader
│   │   │
│   │   ├── InputSection
│   │   │   ├── VerseSelector
│   │   │   │   ├── SurahSelect
│   │   │   │   └── AyahSelect
│   │   │   │
│   │   │   ├── TextInput
│   │   │   │   └── ArabicTextarea
│   │   │   │
│   │   │   └── MethodSelector
│   │   │       ├── LetterMethodSelect
│   │   │       └── AbjadSystemSelect
│   │   │
│   │   ├── AnalysisResults
│   │   │   ├── ResultCard (Letters)
│   │   │   │   ├── AnimatedCounter
│   │   │   │   └── MethodBadge
│   │   │   │
│   │   │   ├── ResultCard (Words)
│   │   │   │   └── AnimatedCounter
│   │   │   │
│   │   │   └── ResultCard (Abjad)
│   │   │       ├── AnimatedCounter
│   │   │       └── SystemBadge
│   │   │
│   │   ├── DetailedBreakdown
│   │   │   ├── LetterDistribution
│   │   │   │   └── AnimatedBarChart
│   │   │   │
│   │   │   └── LetterTable
│   │   │
│   │   └── HistoryPanel
│   │       └── HistoryItem[] (mapped)
│   │
│   ├── [Docs Page]
│   │   ├── DocsSidebar
│   │   │   └── NavSection[] (mapped)
│   │   │
│   │   ├── DocsContent
│   │   │   ├── EndpointCard[] (mapped)
│   │   │   │   ├── MethodBadge
│   │   │   │   ├── PathDisplay
│   │   │   │   ├── ParameterTable
│   │   │   │   └── ResponsePreview
│   │   │   │
│   │   │   └── CodeBlock
│   │   │
│   │   └── ApiExplorer
│   │       ├── RequestBuilder
│   │       └── ResponseViewer
│   │
│   └── [About Page]
│       ├── Mission
│       ├── Standards
│       ├── Team
│       └── Contact
│
└── Footer
    ├── FooterLinks
    ├── SocialLinks
    └── Copyright
```

### Component Design Principles

#### 1. Atomic Design Pattern

```
Atoms      → Button, Input, Badge, Icon
Molecules  → Card, Select, Tooltip, AnimatedCounter
Organisms  → VerseSelector, AnalysisResults, Navbar
Templates  → PageLayout, PlaygroundLayout
Pages      → Landing, Playground, Docs, About
```

#### 2. Composition Over Inheritance

```tsx
// ✓ Good: Composition
const FeatureCard = ({ icon, title, description, children }) => (
  <GlassCard>
    <AnimatedIcon icon={icon} />
    <h3>{title}</h3>
    <p>{description}</p>
    {children}
  </GlassCard>
);

// ✗ Bad: Inheritance
class FeatureCard extends GlassCard { ... }
```

#### 3. Props Interface Design

```tsx
// Granular, specific interfaces
interface AnalysisResultsProps {
  letterCount: number;
  wordCount: number;
  abjadValue: number;
  method: LetterCountMethod;
  system: AbjadSystem;
  isLoading?: boolean;
  onMethodChange?: (method: LetterCountMethod) => void;
}

// Not monolithic
interface BadProps {
  data: any;
  options: any;
  callbacks: any;
}
```

---

## Design Patterns Applied

### 1. Provider Pattern (Dependency Injection)

```tsx
// contexts/api-context.tsx
const ApiContext = createContext<ApiClient | null>(null);

export const ApiProvider = ({ children, baseUrl }) => {
  const client = useMemo(() => new ApiClient(baseUrl), [baseUrl]);
  return (
    <ApiContext.Provider value={client}>
      {children}
    </ApiContext.Provider>
  );
};

// Usage in components
const { analyze } = useApi();
```

### 2. Custom Hook Pattern (Logic Extraction)

```tsx
// hooks/use-verse-analysis.ts
export function useVerseAnalysis() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const api = useApi();

  const analyze = useCallback(async (text: string, options: AnalysisOptions) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.analyze(text, options);
      setResult(data);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [api]);

  return { result, isLoading, error, analyze };
}
```

### 3. Compound Component Pattern

```tsx
// components/playground/analysis-panel.tsx
const AnalysisPanel = ({ children }) => (
  <div className="analysis-panel">{children}</div>
);

AnalysisPanel.Header = ({ title }) => (
  <h2 className="panel-header">{title}</h2>
);

AnalysisPanel.Results = ({ data }) => (
  <div className="panel-results">{/* ... */}</div>
);

AnalysisPanel.Actions = ({ children }) => (
  <div className="panel-actions">{children}</div>
);

// Usage
<AnalysisPanel>
  <AnalysisPanel.Header title="Analysis Results" />
  <AnalysisPanel.Results data={results} />
  <AnalysisPanel.Actions>
    <Button>Export</Button>
  </AnalysisPanel.Actions>
</AnalysisPanel>
```

### 4. Strategy Pattern (Method Selection)

```tsx
// lib/utils/counting-strategies.ts
interface CountingStrategy {
  name: string;
  count: (text: string) => number;
}

const strategies: Record<LetterCountMethod, CountingStrategy> = {
  traditional: {
    name: 'Traditional',
    count: (text) => countTraditional(text),
  },
  uthmani_full: {
    name: 'Uthmani Full',
    count: (text) => countUthmani(text),
  },
  no_wasla: {
    name: 'No Wasla',
    count: (text) => countNoWasla(text),
  },
};
```

### 5. Observer Pattern (State Subscription)

```tsx
// Real-time updates via React hooks
const useAnalysisHistory = () => {
  const [history, setHistory] = useLocalStorage<AnalysisEntry[]>('analysis-history', []);

  const addEntry = useCallback((entry: AnalysisEntry) => {
    setHistory(prev => [entry, ...prev].slice(0, 50));
  }, []);

  return { history, addEntry };
};
```

### 6. Factory Pattern (Component Generation)

```tsx
// components/animated/create-animated-component.tsx
function createAnimatedComponent<T extends HTMLElement>(
  Component: keyof JSX.IntrinsicElements,
  defaultVariants: Variants
) {
  return motion(Component, {
    initial: "hidden",
    animate: "visible",
    variants: defaultVariants,
  });
}

// Usage
const AnimatedDiv = createAnimatedComponent('div', fadeInVariants);
const AnimatedSection = createAnimatedComponent('section', slideUpVariants);
```

---

## Data Flow Architecture

### Unidirectional Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      USER ACTION                             │
│              (Click Analyze, Select Verse)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    EVENT HANDLER                             │
│              (onClick, onChange callbacks)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    CUSTOM HOOK                               │
│              (useVerseAnalysis.analyze())                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API CLIENT                                │
│              (POST /api/analyze)                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND API                               │
│              (Mizan FastAPI Server)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    STATE UPDATE                              │
│              (setResult, setLoading)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    UI RE-RENDER                              │
│              (Components update with new data)               │
└─────────────────────────────────────────────────────────────┘
```

### State Management Strategy

| State Type | Solution | Scope |
|------------|----------|-------|
| UI State | `useState` | Component-local |
| Form State | `useState` + controlled inputs | Component-local |
| Server State | Custom hooks + `useState` | Feature-scoped |
| Persistent State | `useLocalStorage` | Cross-session |
| Theme State | Context + `useState` | Global |
| API Client | Context | Global |

---

## Performance Architecture

### Optimization Strategies

#### 1. Code Splitting

```tsx
// Dynamic imports for heavy components
const Playground = dynamic(() => import('@/components/playground'), {
  loading: () => <PlaygroundSkeleton />,
  ssr: false,
});

const ApiExplorer = dynamic(() => import('@/components/docs/api-explorer'), {
  loading: () => <ExplorerSkeleton />,
});
```

#### 2. Image Optimization

```tsx
// next/image with proper sizing
<Image
  src="/images/hero.webp"
  alt="Mizan Hero"
  width={1200}
  height={600}
  priority // For above-the-fold
  placeholder="blur"
  blurDataURL={blurDataUrl}
/>
```

#### 3. Animation Performance

```tsx
// Use transform and opacity only (GPU-accelerated)
const variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.25, 0.1, 0.25, 1], // Custom easing
    }
  },
};

// Reduce motion for accessibility
const prefersReducedMotion = useReducedMotion();
```

#### 4. Memoization

```tsx
// Memoize expensive computations
const letterDistribution = useMemo(() =>
  calculateDistribution(analysisResult),
  [analysisResult]
);

// Memoize callbacks
const handleAnalyze = useCallback(() => {
  analyze(text, options);
}, [text, options, analyze]);

// Memoize components
const MemoizedChart = memo(LetterDistributionChart);
```

#### 5. Lazy Loading

```tsx
// Intersection Observer for sections
const { ref, inView } = useInView({
  threshold: 0.1,
  triggerOnce: true,
});

<section ref={ref}>
  {inView && <HeavyComponent />}
</section>
```

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| FCP (First Contentful Paint) | <1.5s | Lighthouse |
| LCP (Largest Contentful Paint) | <2.5s | Lighthouse |
| CLS (Cumulative Layout Shift) | <0.1 | Lighthouse |
| TTI (Time to Interactive) | <3.0s | Lighthouse |
| Bundle Size (initial) | <100KB gzipped | webpack-bundle-analyzer |

---

## Security Considerations

### Input Validation

```tsx
// Validate all user inputs
const validateArabicText = (text: string): ValidationResult => {
  if (!text.trim()) {
    return { valid: false, error: 'Text is required' };
  }
  if (text.length > MAX_TEXT_LENGTH) {
    return { valid: false, error: `Max ${MAX_TEXT_LENGTH} characters` };
  }
  // Allow Arabic, spaces, and common punctuation
  const arabicPattern = /^[\u0600-\u06FF\u0750-\u077F\s.,!?]+$/;
  if (!arabicPattern.test(text)) {
    return { valid: false, error: 'Please enter Arabic text only' };
  }
  return { valid: true };
};
```

### XSS Prevention

```tsx
// React automatically escapes content
// For dangerouslySetInnerHTML (avoid when possible):
import DOMPurify from 'dompurify';

const sanitizedHtml = DOMPurify.sanitize(rawHtml);
```

### API Security

```tsx
// Rate limiting on client
const { analyze, isRateLimited } = useRateLimitedApi({
  maxRequests: 10,
  windowMs: 60000,
});

// CORS configured on backend
// API key for production (future)
```

### Content Security Policy

```tsx
// next.config.js
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
  },
  {
    key: 'X-Frame-Options',
    value: 'DENY',
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
];
```

---

## Accessibility Standards

### WCAG 2.1 AA Compliance

| Requirement | Implementation |
|-------------|----------------|
| Color Contrast | Minimum 4.5:1 ratio, tested with axe |
| Keyboard Navigation | All interactive elements focusable |
| Screen Reader | Semantic HTML, ARIA labels |
| Focus Indicators | Visible focus rings |
| Motion | `prefers-reduced-motion` support |
| Text Scaling | Responsive to 200% zoom |

### Arabic Text Accessibility

```tsx
// Proper language attributes
<html lang="en" dir="ltr">
  <span lang="ar" dir="rtl">بسم الله الرحمن الرحيم</span>
</html>

// Screen reader hints
<span
  lang="ar"
  dir="rtl"
  aria-label="Bismillah ir-Rahman ir-Rahim"
>
  بسم الله الرحمن الرحيم
</span>
```

### Component Accessibility

```tsx
// Using Radix UI primitives (via shadcn/ui)
// Automatically handles:
// - Focus management
// - Keyboard interactions
// - ARIA attributes
// - Screen reader announcements

<Select.Root>
  <Select.Trigger aria-label="Select Surah">
    <Select.Value placeholder="Choose a Surah" />
  </Select.Trigger>
  <Select.Content>
    {surahs.map(surah => (
      <Select.Item key={surah.number} value={surah.number.toString()}>
        {surah.name}
      </Select.Item>
    ))}
  </Select.Content>
</Select.Root>
```

---

## Technology Stack Rationale

### Framework: Next.js 14

| Requirement | Next.js Capability |
|-------------|-------------------|
| Static Export | `output: 'export'` for GitHub Pages |
| Performance | Automatic code splitting, image optimization |
| SEO | Static generation, metadata API |
| DX | Fast Refresh, TypeScript support |
| Ecosystem | Largest React ecosystem |

### UI: shadcn/ui + Aceternity + Magic UI

| Layer | Library | Rationale |
|-------|---------|-----------|
| Base | shadcn/ui | Accessible, customizable, no lock-in |
| Animation | Aceternity UI | Premium visual effects |
| Effects | Magic UI | Interactive wow-factor |
| Motion | Framer Motion | Declarative, performant, MIT license |

### Styling: Tailwind CSS

| Requirement | Tailwind Capability |
|-------------|---------------------|
| Customization | Full design token control |
| RTL Support | Logical properties (`ms-`, `me-`) |
| Dark Mode | Built-in dark mode variants |
| Performance | PurgeCSS removes unused styles |
| DX | Utility-first, no context switching |

### TypeScript

- Type safety across the codebase
- Better IDE support and autocomplete
- Self-documenting code
- Catch errors at compile time

---

## Conclusion

This architecture document ensures the Mizan Website follows industry best practices and software engineering principles. The modular, component-based design allows for:

1. **Maintainability** - Clear separation of concerns
2. **Scalability** - Easy to add new features
3. **Testability** - Isolated, pure components
4. **Performance** - Optimized loading and rendering
5. **Accessibility** - WCAG 2.1 AA compliance
6. **Security** - Input validation, XSS prevention

The implementation will strictly follow this architecture to deliver a professional, impressive, and high-performance website.

---

**Document Approved By:** Mizan Development Team
**Implementation Start Date:** 2025-12-16
**Target Completion:** MVP Ready

