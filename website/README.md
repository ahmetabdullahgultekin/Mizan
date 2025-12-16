# Mizan Website

> Interactive website and playground for the Mizan Quranic Text Analysis Engine

## Features

- **Landing Page** - Beautiful animated introduction with live demo
- **Interactive Playground** - Analyze Quranic text in real-time
- **API Documentation** - Comprehensive docs with code examples
- **About Page** - Project mission and scholarly standards

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **UI Components**: shadcn/ui + Aceternity UI inspired
- **Deployment**: GitHub Pages (static export)

## Getting Started

### Prerequisites

- Node.js 18.17+
- npm or yarn

### Installation

```bash
# Navigate to website directory
cd website

# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the site.

### Building for Production

```bash
# Build static export
npm run build

# Output will be in ./out directory
```

### Deployment

The website is automatically deployed to GitHub Pages when changes are pushed to the `main` branch.

Manual deployment:

```bash
# Build and export
npm run build

# Deploy ./out directory to your hosting
```

## Project Structure

```
website/
├── app/                  # Next.js App Router pages
│   ├── page.tsx         # Landing page
│   ├── playground/      # Interactive playground
│   ├── docs/            # API documentation
│   └── about/           # About page
├── components/
│   ├── ui/              # Base UI components (shadcn/ui style)
│   ├── animated/        # Animated components (Aceternity inspired)
│   ├── landing/         # Landing page sections
│   ├── playground/      # Playground components
│   └── layout/          # Layout components (Navbar, Footer)
├── hooks/               # Custom React hooks
├── lib/                 # Utilities and API client
├── types/               # TypeScript types
├── config/              # Site configuration
└── public/              # Static assets
```

## Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=https://api.mizan.app
NEXT_PUBLIC_SITE_URL=https://mizan.app
```

## Arabic Fonts

Download and place in `public/fonts/`:

- [Amiri](https://fonts.google.com/specimen/Amiri) - For Quranic text
- [Cairo](https://fonts.google.com/specimen/Cairo) - For UI Arabic text

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production (static export) |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run format` | Format code with Prettier |
| `npm run type-check` | Run TypeScript checks |

## Design System

### Colors

- **Gold** (`#D4AF37`) - Primary accent
- **Emerald** (`#059669`) - Secondary accent
- **Background** - Dark theme (`#0a0a0a`)

### Typography

- **English**: Inter (system font fallback)
- **Arabic**: Amiri, Cairo

### Components

The UI is built on top of shadcn/ui principles with custom glassmorphism styling and Framer Motion animations.

## Contributing

See the main [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](../LICENSE)
