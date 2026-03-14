'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { FileText, ArrowLeft } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GlowingOrbs } from '@/components/animated/floating-particles';

export default function TermsPage() {
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
            <FileText className="mr-2 h-3 w-3" />
            Terms of Service
          </Badge>
          <h1 className="mb-4 text-3xl font-bold md:text-4xl">
            Terms of{' '}
            <span className="text-gradient-gold">Service</span>
          </h1>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Clear, fair terms for using the Mizan platform and API.
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
            <Section title="1. Acceptance of Terms">
              <p>
                By accessing or using the Mizan Core Engine platform, API, or any
                associated services, you agree to be bound by these Terms of Service.
                If you do not agree to these terms, please do not use the service.
              </p>
            </Section>

            <Section title="2. Description of Service">
              <p>
                Mizan Core Engine provides tools for Quranic text analysis, including
                letter counting, word counting, Abjad calculations, semantic search,
                and an Islamic knowledge library. The service is provided as open-source
                software under the MIT License.
              </p>
            </Section>

            <Section title="3. Scholarly Disclaimer">
              <p>
                Mizan is a computational tool designed to assist scholarly research.
                While we strive for accuracy and verify our calculations against
                authoritative sources (Tanzil.net, Quran.com, classical scholarship),
                the results should be verified independently for scholarly work.
                Mizan is not a substitute for traditional Islamic scholarship and
                should be used as a supplementary research tool.
              </p>
            </Section>

            <Section title="4. API Usage">
              <p className="mb-3">
                When using the Mizan API, you agree to:
              </p>
              <ul className="list-disc space-y-2 pl-6">
                <li>Use the API in a respectful manner consistent with its scholarly purpose</li>
                <li>Not attempt to overload the service with excessive requests</li>
                <li>Respect rate limits (when enabled) designed to ensure fair access</li>
                <li>Not use the API for purposes that are disrespectful to the Quran or Islamic scholarship</li>
              </ul>
            </Section>

            <Section title="5. Open Source License">
              <p>
                The Mizan source code is licensed under the{' '}
                <Link href="/license" className="text-gold-500 hover:underline">
                  MIT License
                </Link>.
                You are free to use, modify, and distribute the software in accordance
                with the license terms. This includes using Mizan for both personal
                and commercial purposes.
              </p>
            </Section>

            <Section title="6. User Content">
              <p>
                Content you submit to the Library feature (text sources, annotations)
                remains your responsibility. You retain ownership of any content you
                add. You are responsible for ensuring you have the right to use and
                distribute any text you add to the library.
              </p>
            </Section>

            <Section title="7. No Warranty">
              <p>
                The service is provided &quot;as is&quot; and &quot;as available&quot; without
                warranty of any kind, express or implied. We do not guarantee that the
                service will be uninterrupted, error-free, or that the results will
                be perfectly accurate in all edge cases. See the MIT License for full
                warranty disclaimer.
              </p>
            </Section>

            <Section title="8. Limitation of Liability">
              <p>
                To the maximum extent permitted by law, the Mizan contributors shall
                not be liable for any indirect, incidental, special, consequential, or
                punitive damages resulting from your use of or inability to use the
                service.
              </p>
            </Section>

            <Section title="9. Changes to Terms">
              <p>
                We may update these terms from time to time. Changes will be reflected
                on this page with an updated date. Continued use of the service after
                changes constitutes acceptance of the updated terms.
              </p>
            </Section>

            <Section title="10. Contact">
              <p>
                For questions about these terms, please open an issue on our{' '}
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
