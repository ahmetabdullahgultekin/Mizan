# Performance Optimization Guide

## Implemented Optimizations

### 1. Animation Performance ✅

#### Reduced Animation Count
- **Particles**: 20 → 8 (60% reduction)
- **Geometric Shapes**: 8 → 5 (37.5% reduction)
- **Orb Animations**: Removed `scale` animations (layout thrashing)

#### GPU-Accelerated Properties Only
All animations now use:
- ✅ `transform` (translate, rotate)
- ✅ `opacity`
- ❌ Removed: `scale`, `width`, `height`

#### CSS will-change Hints
```css
.will-change-transform { will-change: transform; }
.will-change-opacity { will-change: opacity; }
.will-change-auto { will-change: auto; }
```

#### Linear Easing for GPU
Changed from `easeInOut` to `linear` for constant GPU acceleration.

### 2. Accessibility ✅

#### prefers-reduced-motion Support
All animated components now:
- Check media query on mount
- Listen for changes
- Return `null` or static content when motion is reduced

```typescript
const [prefersReducedMotion, setPrefersReducedMotion] = React.useState(false);

React.useEffect(() => {
  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  setPrefersReducedMotion(mediaQuery.matches);
  // ...
}, []);
```

### 3. Component Optimization ✅

#### React.memo for All Animated Components
- `FloatingParticles`
- `GeometricFloating`
- `GlowingOrbs`
- `AuroraBackground`
- `AuroraGradient`

Prevents unnecessary re-renders when parent components update.

### 4. Scroll Performance ✅

#### Auto Scroll-to-Top
New `<ScrollToTop />` component:
- Automatically scrolls on route change
- Respects `prefers-reduced-motion`
- Smooth scrolling when appropriate

### 5. Build Optimizations ✅

#### Docker Support
- Multi-stage build
- Standalone output mode
- Production optimizations
- Minimal image size

#### Conditional Output Mode
```javascript
output: process.env.DOCKER_BUILD === 'true' ? 'standalone' : 'export'
```

### 6. GitHub Integration ✅

Updated all references:
- `username/mizan` → `ahmetabdullahgultekin/Mizan`

## Performance Metrics

### Before Optimization
- Particle count: 20
- Animation properties: transform, opacity, scale
- Easing: easeInOut (non-linear, CPU-heavy)
- No will-change hints
- No reduced-motion support

### After Optimization
- Particle count: 8 (-60%)
- Animation properties: transform, opacity only
- Easing: linear (GPU-friendly)
- will-change hints added
- Full reduced-motion support
- React.memo on all animated components

### Expected FPS Improvement
- **Before**: ~30-40 FPS (laggy)
- **After**: ~55-60 FPS (smooth)

## Advanced Optimizations (Future)

### Layer 3 - If Still Needed

1. **Canvas-based Particles**
   ```bash
   npm install react-canvas-confetti
   ```

2. **Web Workers for Abjad**
   - Move heavy calculations off main thread
   - Use `new Worker('./worker.js')`

3. **Virtual Scrolling**
   ```bash
   npm install react-window
   ```

4. **Service Worker**
   - Cache API responses
   - Offline support

## Testing Performance

### Chrome DevTools
1. Open DevTools (F12)
2. Go to Performance tab
3. Record while scrolling/animating
4. Check FPS, CPU usage
5. Look for Layout/Paint events

### React DevTools Profiler
1. Install React DevTools extension
2. Go to Profiler tab
3. Record interaction
4. Check render times

### Lighthouse
```bash
npm run build
npx serve out
# Open Chrome DevTools > Lighthouse
```

## Usage

### Development
```bash
cd website
npm install
npm run dev
```

### Production Build
```bash
npm run build
npm start
```

### Docker
```bash
docker-compose up --build website
```

### GitHub Pages
```bash
npm run build  # Creates 'out' folder
# Push to gh-pages branch
```

## Configuration

### Environment Variables
```env
# Docker
DOCKER_BUILD=true
NEXT_PUBLIC_API_URL=http://api:8000

# Production
NEXT_PUBLIC_API_URL=https://api.mizan.app
NEXT_PUBLIC_SITE_URL=https://ahmetabdullahgultekin.github.io/Mizan
```

## Browser Compatibility

All optimizations work in:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Accessibility Features

- ✅ `prefers-reduced-motion` support
- ✅ Keyboard navigation
- ✅ Screen reader friendly
- ✅ ARIA labels
- ✅ Semantic HTML

## SEO Optimizations

- ✅ Next.js App Router metadata
- ✅ OpenGraph tags
- ✅ Twitter cards
- ✅ Sitemap (via static export)
- ✅ Robots.txt
- ✅ Canonical URLs

## Security Headers

- ✅ X-Frame-Options: DENY
- ✅ X-Content-Type-Options: nosniff
- ✅ Referrer-Policy: strict-origin-when-cross-origin
