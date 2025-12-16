export const siteConfig = {
  name: 'Mizan - Quranic Text Analysis',
  description:
    'High-precision Quranic text analysis engine with letter counting, word counting, and Abjad calculations. Verified against scholarly standards.',
  url: process.env.NEXT_PUBLIC_SITE_URL || 'https://mizan.app',
  ogImage: '/og-image.png',
  keywords: [
    'Quran',
    'Quranic analysis',
    'Arabic text analysis',
    'Abjad',
    'Gematria',
    'Islamic',
    'Letter counting',
    'Word counting',
    'Tanzil',
    'Scholarly',
    'API',
  ] as string[],
  links: {
    github: 'https://github.com/ahmetabdullahgultekin/Mizan',
    docs: '/docs',
    playground: '/playground',
  },
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'https://api.mizan.app',
  },
};

export type SiteConfig = typeof siteConfig;
