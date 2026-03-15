/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use standalone for Docker, export for GitHub Pages
  output: process.env.DOCKER_BUILD === 'true' ? 'standalone' : 'export',

  // Base path for GitHub Pages (repo name as subdirectory)
  // Docker: no basePath, GitHub Pages: /Mizan
  basePath: process.env.DOCKER_BUILD === 'true' ? '' : '/Mizan',

  // Asset prefix for GitHub Pages
  assetPrefix: process.env.DOCKER_BUILD === 'true' ? '' : '/Mizan',

  // Disable image optimization for static export
  images: {
    unoptimized: process.env.DOCKER_BUILD === 'true' ? false : true,
  },

  // Trailing slashes for static hosting
  trailingSlash: true,

  // TypeScript - continue on errors for now
  typescript: {
    ignoreBuildErrors: true,
  },

  // Turbopack config (Next.js 16 default bundler)
  turbopack: {},

  // Disable server-side features for static export
  experimental: {
    // Enable if needed
  },

  // Environment variables (public)
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000',
  },

  // Headers for security
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              // Next.js requires unsafe-inline for hydration scripts; unsafe-eval only needed in dev
              `script-src 'self' 'unsafe-inline'${process.env.NODE_ENV === 'development' ? " 'unsafe-eval'" : ''}`,
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob:",
              `connect-src 'self' ${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}`,
              "frame-ancestors 'none'",
              "base-uri 'self'",
              "form-action 'self'",
              "object-src 'none'",
            ].join('; '),
          },
        ],
      },
    ];
  },

  // Redirects (if needed)
  async redirects() {
    return [];
  },
};

module.exports = nextConfig;
