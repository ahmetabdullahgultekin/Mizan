'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  BookOpen,
  Code2,
  Hash,
  Calculator,
  Type,
  ExternalLink,
  Copy,
  Check,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { GlowingOrbs } from '@/components/animated/floating-particles';
import { copyToClipboard } from '@/lib/utils';

/**
 * Documentation Page
 *
 * API documentation and usage examples.
 */
export default function DocsPage() {
  return (
    <div className="relative min-h-screen pt-20">
      {/* Background */}
      <GlowingOrbs className="opacity-20" />

      <div className="container relative z-10 mx-auto px-4 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12 text-center"
        >
          <Badge variant="emerald" className="mb-4">
            <BookOpen className="mr-2 h-3 w-3" />
            Documentation
          </Badge>
          <h1 className="mb-4 text-3xl font-bold md:text-4xl">
            API{' '}
            <span className="text-gradient-emerald">Reference</span>
          </h1>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Complete documentation for the Mizan API. Analyze Quranic text with
            letter counting, word analysis, and Abjad calculations.
          </p>
        </motion.div>

        {/* Quick Start */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-12"
        >
          <h2 className="mb-6 text-2xl font-bold">Quick Start</h2>
          <div className="glass-card rounded-xl p-6">
            <p className="mb-4 text-muted-foreground">
              Make your first API request to analyze the Basmalah:
            </p>
            <CodeBlock
              language="bash"
              code={`curl -X POST https://api.mizan.app/api/v1/analyze \\
  -H "Content-Type: application/json" \\
  -d '{"text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"}'`}
            />
          </div>
        </motion.section>

        {/* Endpoints */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="mb-6 text-2xl font-bold">API Endpoints</h2>

          <div className="space-y-6">
            {/* Analyze Endpoint */}
            <EndpointCard
              method="POST"
              path="/api/v1/analyze"
              description="Analyze Arabic text for letters, words, and Abjad value"
              requestBody={{
                text: 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
                letter_method: 'traditional',
                abjad_system: 'mashriqi',
                include_breakdown: true,
              }}
              responseBody={{
                text: 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
                letter_count: 19,
                word_count: 4,
                abjad_value: 786,
                letter_method: 'traditional',
                abjad_system: 'mashriqi',
              }}
            />

            {/* Get Verse Endpoint */}
            <EndpointCard
              method="GET"
              path="/api/v1/verses/{surah}/{ayah}"
              description="Get a specific verse by surah and ayah number"
              responseBody={{
                surah: 1,
                ayah: 1,
                text: 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
              }}
            />

            {/* Get Surah List Endpoint */}
            <EndpointCard
              method="GET"
              path="/api/v1/surahs"
              description="Get list of all surahs with metadata"
              responseBody={{
                surahs: [
                  {
                    number: 1,
                    name_arabic: 'الفاتحة',
                    name_english: 'Al-Fatiha',
                    verse_count: 7,
                  },
                ],
                total: 114,
              }}
            />

            {/* Health Check */}
            <EndpointCard
              method="GET"
              path="/api/v1/health"
              description="Check API health status"
              responseBody={{
                status: 'healthy',
                version: '0.1.0',
              }}
            />
          </div>
        </motion.section>

        {/* Parameters */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-12"
        >
          <h2 className="mb-6 text-2xl font-bold">Parameters</h2>

          <div className="grid gap-6 md:grid-cols-2">
            <ParameterCard
              title="Letter Counting Methods"
              icon={<Hash className="h-5 w-5" />}
              parameters={[
                {
                  name: 'traditional',
                  description: 'Include Alif Wasla, exclude Khanjariyya (Default)',
                },
                {
                  name: 'uthmani_full',
                  description: 'Include both Alif Wasla and Khanjariyya',
                },
                {
                  name: 'no_wasla',
                  description: 'Base letters only, exclude special characters',
                },
              ]}
            />

            <ParameterCard
              title="Abjad Systems"
              icon={<Calculator className="h-5 w-5" />}
              parameters={[
                {
                  name: 'mashriqi',
                  description: 'Eastern system - most common (Default)',
                },
                {
                  name: 'maghribi',
                  description: 'Western/North African system',
                },
              ]}
            />
          </div>
        </motion.section>

        {/* Verified Values */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-12"
        >
          <h2 className="mb-6 text-2xl font-bold">Verified Values</h2>

          <div className="glass-card overflow-hidden rounded-xl">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium">Metric</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Value</th>
                  <th className="px-4 py-3 text-left text-sm font-medium">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                <tr>
                  <td className="px-4 py-3 text-sm">Al-Fatiha letters</td>
                  <td className="px-4 py-3 text-sm font-mono text-gold-500">139</td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">Tanzil.net</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm">Basmalah letters</td>
                  <td className="px-4 py-3 text-sm font-mono text-gold-500">19</td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">Traditional</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm">Allah Abjad</td>
                  <td className="px-4 py-3 text-sm font-mono text-gold-500">66</td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">Universal</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm">Basmalah Abjad</td>
                  <td className="px-4 py-3 text-sm font-mono text-gold-500">786</td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">Universal</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm">Total verses</td>
                  <td className="px-4 py-3 text-sm font-mono text-gold-500">6,236</td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">Consensus</td>
                </tr>
                <tr>
                  <td className="px-4 py-3 text-sm">Total surahs</td>
                  <td className="px-4 py-3 text-sm font-mono text-gold-500">114</td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">Consensus</td>
                </tr>
              </tbody>
            </table>
          </div>
        </motion.section>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-12 text-center"
        >
          <Button variant="glow" size="lg" asChild>
            <Link href="/playground">
              Try in Playground
              <ExternalLink className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </motion.div>
      </div>
    </div>
  );
}

/**
 * Code Block Component
 */
function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    await copyToClipboard(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="group relative overflow-hidden rounded-lg bg-background">
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <span className="text-xs text-muted-foreground">{language}</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-7 px-2 opacity-0 transition-opacity group-hover:opacity-100"
        >
          {copied ? (
            <Check className="h-3 w-3 text-emerald-500" />
          ) : (
            <Copy className="h-3 w-3" />
          )}
        </Button>
      </div>
      <pre className="overflow-x-auto p-4 text-sm">
        <code>{code}</code>
      </pre>
    </div>
  );
}

/**
 * Endpoint Card Component
 */
function EndpointCard({
  method,
  path,
  description,
  requestBody,
  responseBody,
}: {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  path: string;
  description: string;
  requestBody?: object;
  responseBody: object;
}) {
  const methodColors = {
    GET: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30',
    POST: 'bg-blue-500/10 text-blue-500 border-blue-500/30',
    PUT: 'bg-amber-500/10 text-amber-500 border-amber-500/30',
    DELETE: 'bg-red-500/10 text-red-500 border-red-500/30',
  };

  return (
    <div className="glass-card overflow-hidden rounded-xl">
      <div className="border-b border-border p-4">
        <div className="flex items-center gap-3">
          <Badge className={cn('font-mono', methodColors[method])}>{method}</Badge>
          <code className="font-mono text-sm">{path}</code>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">{description}</p>
      </div>

      <Tabs defaultValue="response" className="p-4">
        <TabsList>
          {requestBody && <TabsTrigger value="request">Request</TabsTrigger>}
          <TabsTrigger value="response">Response</TabsTrigger>
        </TabsList>

        {requestBody && (
          <TabsContent value="request" className="mt-4">
            <CodeBlock language="json" code={JSON.stringify(requestBody, null, 2)} />
          </TabsContent>
        )}

        <TabsContent value="response" className="mt-4">
          <CodeBlock language="json" code={JSON.stringify(responseBody, null, 2)} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

/**
 * Parameter Card Component
 */
function ParameterCard({
  title,
  icon,
  parameters,
}: {
  title: string;
  icon: React.ReactNode;
  parameters: { name: string; description: string }[];
}) {
  return (
    <div className="glass-card rounded-xl p-5">
      <div className="mb-4 flex items-center gap-2">
        <div className="rounded-lg bg-gold-500/10 p-2 text-gold-500">{icon}</div>
        <h3 className="font-medium">{title}</h3>
      </div>

      <div className="space-y-3">
        {parameters.map((param) => (
          <div key={param.name}>
            <code className="rounded bg-muted px-1.5 py-0.5 text-sm text-gold-500">
              {param.name}
            </code>
            <p className="mt-1 text-xs text-muted-foreground">{param.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
