import { Hero, Features, DemoPreview, Stats, CTA } from '@/components/landing';

/**
 * Landing Page
 *
 * The main entry point for the Mizan website.
 * Showcases features, demo, and encourages users to try the playground.
 */
export default function HomePage() {
  return (
    <>
      <Hero />
      <Features />
      <DemoPreview />
      <Stats />
      <CTA />
    </>
  );
}
