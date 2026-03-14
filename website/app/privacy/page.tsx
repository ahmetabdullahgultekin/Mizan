'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { Shield, ArrowLeft } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GlowingOrbs } from '@/components/animated/floating-particles';

export default function PrivacyPage() {
  return (
    <div className="relative min-h-screen pt-20">
      <GlowingOrbs className="opacity-20" />

      <div className="container relative z-10 mx-auto px-4 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <Badge variant="gold" className="mb-4">
            <Shield className="mr-2 h-3 w-3" />
            Privacy Policy
          </Badge>
          <h1 className="mb-4 text-3xl font-bold md:text-4xl">
            Privacy{' '}
            <span className="text-gradient-gold">Policy</span>
          </h1>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Your privacy matters. Mizan is designed with privacy-first principles.
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            Last updated: March 14, 2026
          </p>
        </motion.div>

        {/* Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mx-auto max-w-3xl"
        >
          <div className="glass-card rounded-xl p-8 space-y-8">
            <Section title="Overview">
              <p>
                Mizan Core Engine is an open-source Quranic text analysis platform.
                We are committed to protecting your privacy and being transparent
                about our data practices. This policy explains what data we collect
                (very little) and how we handle it.
              </p>
            </Section>

            <Section title="Data We Collect">
              <p className="mb-3">
                Mizan collects minimal data to operate the service:
              </p>
              <ul className="list-disc space-y-2 pl-6">
                <li>
                  <strong>API request logs:</strong> Standard server logs including
                  IP address, request path, timestamp, and response status code.
                  These logs are used for debugging and monitoring service health.
                </li>
                <li>
                  <strong>Text submitted for analysis:</strong> Arabic text you submit
                  to the API is processed in memory and not stored beyond the request
                  lifecycle, unless you explicitly add it to the Library feature.
                </li>
                <li>
                  <strong>Library content:</strong> Text sources you add to library
                  spaces are stored in the database to enable semantic search. You
                  can delete your sources at any time.
                </li>
              </ul>
            </Section>

            <Section title="Data We Do Not Collect">
              <ul className="list-disc space-y-2 pl-6">
                <li>No personal identification information (name, email, etc.)</li>
                <li>No cookies or browser tracking</li>
                <li>No analytics or third-party tracking scripts</li>
                <li>No advertising data</li>
                <li>No usage behavior profiling</li>
              </ul>
            </Section>

            <Section title="Data Storage and Security">
              <p>
                Data is stored in PostgreSQL databases. When self-hosting, all data
                remains on your own infrastructure. For the hosted version, data is
                stored on secure cloud infrastructure with encryption at rest and
                in transit.
              </p>
            </Section>

            <Section title="Open Source Transparency">
              <p>
                Mizan is fully open source under the MIT License. You can audit
                exactly what data the application collects by reviewing the source
                code on{' '}
                <a
                  href="https://github.com/ahmetabdullahgultekin/Mizan"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gold-500 hover:underline"
                >
                  GitHub
                </a>.
                Self-hosting gives you complete control over your data.
              </p>
            </Section>

            <Section title="Third-Party Services">
              <p>
                When using Gemini embeddings (optional), text is sent to Google&apos;s
                Gemini API for generating vector embeddings. This is opt-in and can
                be disabled by using the local embedding provider instead. Please
                refer to{' '}
                <a
                  href="https://policies.google.com/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gold-500 hover:underline"
                >
                  Google&apos;s Privacy Policy
                </a>{' '}
                for their data handling practices.
              </p>
            </Section>

            <Section title="Changes to This Policy">
              <p>
                We may update this privacy policy from time to time. Changes will
                be reflected on this page with an updated revision date. Since Mizan
                is open source, all changes are tracked in our version control history.
              </p>
            </Section>

            <Section title="Contact">
              <p>
                For privacy-related questions, please open an issue on our{' '}
                <a
                  href="https://github.com/ahmetabdullahgultekin/Mizan/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gold-500 hover:underline"
                >
                  GitHub repository
                </a>.
              </p>
            </Section>
          </div>
        </motion.div>

        {/* Back */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-8 text-center"
        >
          <Button variant="outline" asChild>
            <Link href="/">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Home
            </Link>
          </Button>
        </motion.div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="mb-3 text-lg font-semibold">{title}</h2>
      <div className="text-sm text-muted-foreground leading-relaxed">{children}</div>
    </div>
  );
}
