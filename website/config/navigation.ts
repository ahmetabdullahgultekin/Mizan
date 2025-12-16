export const navigationConfig = {
  mainNav: [
    {
      title: 'Home',
      href: '/',
    },
    {
      title: 'Playground',
      href: '/playground',
    },
    {
      title: 'Documentation',
      href: '/docs',
    },
    {
      title: 'About',
      href: '/about',
    },
  ],
  footerNav: {
    product: [
      { title: 'Features', href: '/#features' },
      { title: 'Playground', href: '/playground' },
      { title: 'API', href: '/docs' },
      { title: 'Pricing', href: '/#pricing' },
    ],
    resources: [
      { title: 'Documentation', href: '/docs' },
      { title: 'API Reference', href: '/docs/api' },
      { title: 'Examples', href: '/docs/examples' },
      { title: 'Changelog', href: '/docs/changelog' },
    ],
    company: [
      { title: 'About', href: '/about' },
      { title: 'Standards', href: '/about#standards' },
      { title: 'Contributing', href: '/docs/contributing' },
      { title: 'GitHub', href: 'https://github.com/ahmetabdullahgultekin/Mizan', external: true },
    ],
    legal: [
      { title: 'Privacy', href: '/privacy' },
      { title: 'Terms', href: '/terms' },
      { title: 'License', href: '/license' },
    ],
  },
} as const;

export type NavigationConfig = typeof navigationConfig;
