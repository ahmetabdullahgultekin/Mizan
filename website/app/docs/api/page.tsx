'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  Code,
  Copy,
  Check,
  ExternalLink,
  BookOpen,
  Server,
  Search,
  Library,
  Activity,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { GlowingOrbs } from '@/components/animated/floating-particles';
import { copyToClipboard } from '@/lib/utils';

export default function ApiReferencePage() {
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
          <Badge variant="emerald" className="mb-4">
            <Code className="mr-2 h-3 w-3" />
            API Reference
          </Badge>
          <h1 className="mb-4 text-3xl font-bold md:text-4xl">
            Complete API{' '}
            <span className="text-gradient-emerald">Reference</span>
          </h1>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Full documentation for every endpoint in the Mizan Core Engine API.
            All endpoints return JSON and use standard HTTP methods.
          </p>
          <div className="mt-4 flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <span>Base URL:</span>
            <code className="rounded bg-muted px-2 py-0.5 font-mono text-gold-500">
              http://localhost:8000
            </code>
          </div>
        </motion.div>

        {/* Table of Contents */}
        <motion.nav
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-12"
        >
          <div className="glass-card mx-auto max-w-2xl rounded-xl p-6">
            <h2 className="mb-4 text-lg font-semibold">Sections</h2>
            <div className="grid gap-2 sm:grid-cols-2">
              <TocLink icon={<Activity className="h-4 w-4" />} href="#health" label="Health" />
              <TocLink icon={<BookOpen className="h-4 w-4" />} href="#verses" label="Verses" />
              <TocLink icon={<Server className="h-4 w-4" />} href="#analysis" label="Analysis" />
              <TocLink icon={<Library className="h-4 w-4" />} href="#library" label="Library" />
              <TocLink icon={<Search className="h-4 w-4" />} href="#search" label="Semantic Search" />
            </div>
          </div>
        </motion.nav>

        {/* Health */}
        <ApiSection id="health" title="Health" delay={0.15}>
          <EndpointCard
            method="GET"
            path="/health"
            description="Service health check. Returns embedding provider status when semantic analysis is enabled."
            responseBody={{
              status: 'healthy',
              version: '0.2.0',
              embedding: {
                provider: 'local',
                model: 'intfloat/multilingual-e5-base',
                dimension: 768,
              },
            }}
          />
        </ApiSection>

        {/* Verses */}
        <ApiSection id="verses" title="Verses" delay={0.2}>
          <EndpointCard
            method="GET"
            path="/api/v1/surahs"
            description="List all 114 surahs with metadata (name, verse count, revelation type, etc.)."
            responseBody={[
              {
                number: 1,
                name_arabic: '\u0627\u0644\u0641\u0627\u062a\u062d\u0629',
                name_english: 'Al-Fatiha',
                name_transliteration: 'Al-Fatihah',
                verse_count: 7,
                revelation_type: 'meccan',
              },
            ]}
          />

          <EndpointCard
            method="GET"
            path="/api/v1/verses/{surah}/{verse}"
            description="Get a specific verse by surah number (1-114) and verse number."
            responseBody={{
              surah_number: 1,
              verse_number: 1,
              text_uthmani: '\u0628\u0650\u0633\u0652\u0645\u0650 \u0627\u0644\u0644\u0651\u064e\u0647\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0652\u0645\u064e\u0640\u0646\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0650\u064a\u0645\u0650',
              text_simple: '\u0628\u0633\u0645 \u0627\u0644\u0644\u0647 \u0627\u0644\u0631\u062d\u0645\u0646 \u0627\u0644\u0631\u062d\u064a\u0645',
              juz: 1,
              hizb: 1,
              page: 1,
            }}
          />
        </ApiSection>

        {/* Analysis */}
        <ApiSection id="analysis" title="Analysis" delay={0.25}>
          <EndpointCard
            method="GET"
            path="/api/v1/analysis/verse/{surah}/{verse}"
            description="Full analysis of a verse: letter count, word count, and Abjad value with breakdown."
            responseBody={{
              surah_number: 1,
              verse_number: 1,
              text: '\u0628\u0650\u0633\u0652\u0645\u0650 \u0627\u0644\u0644\u0651\u064e\u0647\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0652\u0645\u064e\u0640\u0646\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0650\u064a\u0645\u0650',
              letter_count: 19,
              word_count: 4,
              abjad_value: 786,
            }}
          />

          <EndpointCard
            method="GET"
            path="/api/v1/analysis/letters/count"
            description="Count letters in arbitrary Arabic text. Pass text as a query parameter."
            params={[
              { name: 'text', type: 'string', required: true, description: 'Arabic text to count' },
              { name: 'method', type: 'string', required: false, description: 'traditional | uthmani_full | no_wasla (default: traditional)' },
            ]}
            responseBody={{
              text: '\u0628\u0633\u0645 \u0627\u0644\u0644\u0647',
              letter_count: 6,
              method: 'traditional',
            }}
          />

          <EndpointCard
            method="GET"
            path="/api/v1/analysis/abjad"
            description="Calculate Abjad numerical value of Arabic text."
            params={[
              { name: 'text', type: 'string', required: true, description: 'Arabic text to calculate' },
              { name: 'system', type: 'string', required: false, description: 'mashriqi | maghribi (default: mashriqi)' },
            ]}
            responseBody={{
              text: '\u0627\u0644\u0644\u0647',
              abjad_value: 66,
              system: 'mashriqi',
            }}
          />
        </ApiSection>

        {/* Library */}
        <ApiSection id="library" title="Library" delay={0.3}>
          <EndpointCard
            method="POST"
            path="/api/v1/library/spaces"
            description="Create a new library space for organizing text sources."
            requestBody={{ name: 'Tafsir Collection', description: 'Classical tafsir texts' }}
            responseBody={{
              id: 'uuid-here',
              name: 'Tafsir Collection',
              description: 'Classical tafsir texts',
              created_at: '2026-03-14T12:00:00Z',
            }}
          />

          <EndpointCard
            method="GET"
            path="/api/v1/library/spaces"
            description="List all library spaces."
            responseBody={[
              {
                id: 'uuid-here',
                name: 'Tafsir Collection',
                source_count: 3,
                created_at: '2026-03-14T12:00:00Z',
              },
            ]}
          />

          <EndpointCard
            method="POST"
            path="/api/v1/library/spaces/{id}/sources"
            description="Add a text source to a library space. Supports QURAN, TAFSIR, HADITH, and OTHER types."
            requestBody={{
              title: 'Tafsir Ibn Kathir - Al-Fatiha',
              source_type: 'TAFSIR',
              content: 'The tafsir text content...',
              language: 'ar',
              metadata: { author: 'Ibn Kathir' },
            }}
            responseBody={{
              id: 'uuid-here',
              title: 'Tafsir Ibn Kathir - Al-Fatiha',
              source_type: 'TAFSIR',
              indexing_status: 'PENDING',
            }}
          />

          <EndpointCard
            method="GET"
            path="/api/v1/library/sources/{id}"
            description="Get source details including indexing status and chunk count."
            responseBody={{
              id: 'uuid-here',
              title: 'Tafsir Ibn Kathir - Al-Fatiha',
              source_type: 'TAFSIR',
              indexing_status: 'INDEXED',
              chunk_count: 12,
            }}
          />

          <EndpointCard
            method="POST"
            path="/api/v1/library/sources/{id}/index"
            description="Start async indexing of a text source. Splits text into chunks and generates embeddings."
            responseBody={{
              message: 'Indexing started',
              source_id: 'uuid-here',
              status: 'INDEXING',
            }}
          />

          <EndpointCard
            method="DELETE"
            path="/api/v1/library/sources/{id}"
            description="Delete a text source and all its indexed chunks."
            responseBody={{
              message: 'Source deleted',
              source_id: 'uuid-here',
            }}
          />
        </ApiSection>

        {/* Semantic Search */}
        <ApiSection id="search" title="Semantic Search" delay={0.35}>
          <EndpointCard
            method="POST"
            path="/api/v1/search/semantic"
            description="Search across all indexed texts using natural language. Uses AI embeddings for meaning-based matching."
            requestBody={{
              query: 'mercy and compassion',
              source_types: ['QURAN', 'TAFSIR'],
              min_similarity: 0.7,
              limit: 10,
            }}
            responseBody={{
              results: [
                {
                  text: 'Matching text passage...',
                  source_type: 'QURAN',
                  similarity: 0.92,
                  metadata: {},
                },
              ],
              total: 1,
            }}
          />

          <EndpointCard
            method="GET"
            path="/api/v1/verses/{surah}/{verse}/similar"
            description="Find semantically similar verses to a given verse using vector embeddings."
            params={[
              { name: 'limit', type: 'integer', required: false, description: 'Max results (default: 10)' },
              { name: 'min_similarity', type: 'float', required: false, description: 'Minimum similarity 0-1 (default: 0.7)' },
            ]}
            responseBody={{
              source_verse: { surah: 1, verse: 1 },
              similar: [
                {
                  surah_number: 27,
                  verse_number: 30,
                  similarity: 0.89,
                  text: 'Similar verse text...',
                },
              ],
            }}
          />
        </ApiSection>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-12 text-center"
        >
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button variant="glow" size="lg" asChild>
              <Link href="/playground">
                Try in Playground
                <ExternalLink className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/docs/examples">
                <BookOpen className="mr-2 h-4 w-4" />
                Code Examples
              </Link>
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function TocLink({ icon, href, label }: { icon: React.ReactNode; href: string; label: string }) {
  return (
    <a
      href={href}
      className="flex items-center gap-2 rounded-lg p-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
    >
      {icon}
      {label}
    </a>
  );
}

function ApiSection({
  id,
  title,
  delay,
  children,
}: {
  id: string;
  title: string;
  delay: number;
  children: React.ReactNode;
}) {
  return (
    <motion.section
      id={id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="mb-12"
    >
      <h2 className="mb-6 text-2xl font-bold">{title}</h2>
      <div className="space-y-6">{children}</div>
    </motion.section>
  );
}

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

function EndpointCard({
  method,
  path,
  description,
  params,
  requestBody,
  responseBody,
}: {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  path: string;
  description: string;
  params?: { name: string; type: string; required: boolean; description: string }[];
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

      {params && (
        <div className="border-b border-border p-4">
          <h4 className="mb-2 text-xs font-semibold uppercase text-muted-foreground">Parameters</h4>
          <div className="space-y-2">
            {params.map((p) => (
              <div key={p.name} className="flex items-start gap-2 text-sm">
                <code className="rounded bg-muted px-1.5 py-0.5 text-xs text-gold-500">{p.name}</code>
                <span className="text-xs text-muted-foreground">({p.type}{p.required ? ', required' : ''})</span>
                <span className="text-xs text-muted-foreground">- {p.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}

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
