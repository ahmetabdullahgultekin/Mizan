'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  BookOpen,
  Copy,
  Check,
  ExternalLink,
  Code2,
  Terminal,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { GlowingOrbs } from '@/components/animated/floating-particles';
import { copyToClipboard } from '@/lib/utils';

const examples = [
  {
    title: 'Get a Verse and Analyze It',
    description: 'Fetch a verse by surah and verse number, then run full analysis.',
    python: `import requests

BASE_URL = "http://localhost:8000"

# Get verse text
verse = requests.get(f"{BASE_URL}/api/v1/verses/1/1").json()
print(f"Text: {verse['text_uthmani']}")

# Full analysis (letter count, word count, Abjad)
analysis = requests.get(f"{BASE_URL}/api/v1/analysis/verse/1/1").json()
print(f"Letters: {analysis['letter_count']}")
print(f"Words:   {analysis['word_count']}")
print(f"Abjad:   {analysis['abjad_value']}")`,
    javascript: `const BASE_URL = "http://localhost:8000";

// Get verse text
const verse = await fetch(\`\${BASE_URL}/api/v1/verses/1/1\`)
  .then(res => res.json());
console.log("Text:", verse.text_uthmani);

// Full analysis (letter count, word count, Abjad)
const analysis = await fetch(\`\${BASE_URL}/api/v1/analysis/verse/1/1\`)
  .then(res => res.json());
console.log("Letters:", analysis.letter_count);
console.log("Words:", analysis.word_count);
console.log("Abjad:", analysis.abjad_value);`,
    curl: `# Get verse text
curl http://localhost:8000/api/v1/verses/1/1

# Full analysis
curl http://localhost:8000/api/v1/analysis/verse/1/1`,
  },
  {
    title: 'Calculate Abjad Value',
    description: 'Calculate the Abjad numerical value of any Arabic text using Mashriqi or Maghribi system.',
    python: `import requests

BASE_URL = "http://localhost:8000"

# Abjad value of "Allah" (expected: 66)
result = requests.get(
    f"{BASE_URL}/api/v1/analysis/abjad",
    params={"text": "الله", "system": "mashriqi"}
).json()
print(f"Abjad value of 'Allah': {result['abjad_value']}")

# Abjad value of Basmalah (expected: 786)
result = requests.get(
    f"{BASE_URL}/api/v1/analysis/abjad",
    params={"text": "بسم الله الرحمن الرحيم"}
).json()
print(f"Abjad value of Basmalah: {result['abjad_value']}")`,
    javascript: `const BASE_URL = "http://localhost:8000";

// Abjad value of "Allah" (expected: 66)
const params1 = new URLSearchParams({
  text: "الله",
  system: "mashriqi",
});
const result1 = await fetch(\`\${BASE_URL}/api/v1/analysis/abjad?\${params1}\`)
  .then(res => res.json());
console.log("Abjad value of 'Allah':", result1.abjad_value);

// Abjad value of Basmalah (expected: 786)
const params2 = new URLSearchParams({
  text: "بسم الله الرحمن الرحيم",
});
const result2 = await fetch(\`\${BASE_URL}/api/v1/analysis/abjad?\${params2}\`)
  .then(res => res.json());
console.log("Abjad value of Basmalah:", result2.abjad_value);`,
    curl: `# Abjad of "Allah" (expected: 66)
curl "http://localhost:8000/api/v1/analysis/abjad?text=%D8%A7%D9%84%D9%84%D9%87&system=mashriqi"

# Abjad of Basmalah (expected: 786)
curl "http://localhost:8000/api/v1/analysis/abjad?text=%D8%A8%D8%B3%D9%85+%D8%A7%D9%84%D9%84%D9%87+%D8%A7%D9%84%D8%B1%D8%AD%D9%85%D9%86+%D8%A7%D9%84%D8%B1%D8%AD%D9%8A%D9%85"`,
  },
  {
    title: 'Semantic Search',
    description: 'Search across Quran, Tafsir, and Hadith using natural language queries with AI embeddings.',
    python: `import requests

BASE_URL = "http://localhost:8000"

# Semantic search for "mercy and compassion"
results = requests.post(
    f"{BASE_URL}/api/v1/search/semantic",
    json={
        "query": "mercy and compassion",
        "source_types": ["QURAN"],
        "min_similarity": 0.7,
        "limit": 5,
    }
).json()

for r in results["results"]:
    print(f"[{r['similarity']:.0%}] {r['text'][:80]}...")

# Find verses similar to Al-Fatiha verse 1
similar = requests.get(
    f"{BASE_URL}/api/v1/verses/1/1/similar",
    params={"limit": 5, "min_similarity": 0.7}
).json()

for v in similar["similar"]:
    print(f"[{v['similarity']:.0%}] Surah {v['surah_number']}:{v['verse_number']}")`,
    javascript: `const BASE_URL = "http://localhost:8000";

// Semantic search for "mercy and compassion"
const results = await fetch(\`\${BASE_URL}/api/v1/search/semantic\`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "mercy and compassion",
    source_types: ["QURAN"],
    min_similarity: 0.7,
    limit: 5,
  }),
}).then(res => res.json());

results.results.forEach(r => {
  console.log(\`[\${(r.similarity * 100).toFixed(0)}%] \${r.text.slice(0, 80)}...\`);
});

// Find similar verses
const similar = await fetch(
  \`\${BASE_URL}/api/v1/verses/1/1/similar?limit=5&min_similarity=0.7\`
).then(res => res.json());

similar.similar.forEach(v => {
  console.log(\`[\${(v.similarity * 100).toFixed(0)}%] Surah \${v.surah_number}:\${v.verse_number}\`);
});`,
    curl: `# Semantic search
curl -X POST http://localhost:8000/api/v1/search/semantic \\
  -H "Content-Type: application/json" \\
  -d '{"query": "mercy and compassion", "source_types": ["QURAN"], "min_similarity": 0.7, "limit": 5}'

# Find similar verses to Al-Fatiha:1
curl "http://localhost:8000/api/v1/verses/1/1/similar?limit=5&min_similarity=0.7"`,
  },
  {
    title: 'Library Management',
    description: 'Create a library space, add text sources, and trigger indexing for semantic search.',
    python: `import requests

BASE_URL = "http://localhost:8000"

# 1. Create a library space
space = requests.post(
    f"{BASE_URL}/api/v1/library/spaces",
    json={"name": "My Research", "description": "Research texts"}
).json()
space_id = space["id"]
print(f"Created space: {space['name']} ({space_id})")

# 2. Add a text source
source = requests.post(
    f"{BASE_URL}/api/v1/library/spaces/{space_id}/sources",
    json={
        "title": "Ibn Kathir - Al-Fatiha",
        "source_type": "TAFSIR",
        "content": "The tafsir text content goes here...",
        "language": "ar",
    }
).json()
source_id = source["id"]
print(f"Added source: {source['title']}")

# 3. Start indexing (generates embeddings)
requests.post(f"{BASE_URL}/api/v1/library/sources/{source_id}/index")
print("Indexing started!")

# 4. Check indexing status
status = requests.get(f"{BASE_URL}/api/v1/library/sources/{source_id}").json()
print(f"Status: {status['indexing_status']}")`,
    javascript: `const BASE_URL = "http://localhost:8000";
const headers = { "Content-Type": "application/json" };

// 1. Create a library space
const space = await fetch(\`\${BASE_URL}/api/v1/library/spaces\`, {
  method: "POST",
  headers,
  body: JSON.stringify({
    name: "My Research",
    description: "Research texts",
  }),
}).then(res => res.json());
console.log("Created space:", space.name);

// 2. Add a text source
const source = await fetch(
  \`\${BASE_URL}/api/v1/library/spaces/\${space.id}/sources\`,
  {
    method: "POST",
    headers,
    body: JSON.stringify({
      title: "Ibn Kathir - Al-Fatiha",
      source_type: "TAFSIR",
      content: "The tafsir text content goes here...",
      language: "ar",
    }),
  }
).then(res => res.json());
console.log("Added source:", source.title);

// 3. Start indexing
await fetch(\`\${BASE_URL}/api/v1/library/sources/\${source.id}/index\`, {
  method: "POST",
});
console.log("Indexing started!");`,
    curl: `# 1. Create a library space
curl -X POST http://localhost:8000/api/v1/library/spaces \\
  -H "Content-Type: application/json" \\
  -d '{"name": "My Research", "description": "Research texts"}'

# 2. Add a text source (replace SPACE_ID)
curl -X POST http://localhost:8000/api/v1/library/spaces/SPACE_ID/sources \\
  -H "Content-Type: application/json" \\
  -d '{"title": "Ibn Kathir", "source_type": "TAFSIR", "content": "...", "language": "ar"}'

# 3. Start indexing (replace SOURCE_ID)
curl -X POST http://localhost:8000/api/v1/library/sources/SOURCE_ID/index

# 4. Check status
curl http://localhost:8000/api/v1/library/sources/SOURCE_ID`,
  },
];

export default function ExamplesPage() {
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
            <Code2 className="mr-2 h-3 w-3" />
            Code Examples
          </Badge>
          <h1 className="mb-4 text-3xl font-bold md:text-4xl">
            Practical{' '}
            <span className="text-gradient-emerald">Examples</span>
          </h1>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Ready-to-use code examples in Python, JavaScript, and cURL.
            Copy, paste, and start building with the Mizan API.
          </p>
        </motion.div>

        {/* Prerequisites */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-12"
        >
          <div className="glass-card mx-auto max-w-3xl rounded-xl p-6">
            <div className="flex items-center gap-2 mb-3">
              <Terminal className="h-5 w-5 text-gold-500" />
              <h3 className="font-semibold">Prerequisites</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-3">
              Make sure the Mizan API is running locally before trying these examples:
            </p>
            <CodeBlock
              language="bash"
              code={`# Start infrastructure and API
docker-compose up -d
alembic upgrade head
python scripts/ingest_tanzil.py
uvicorn mizan.api.main:app --reload --port 8000`}
            />
          </div>
        </motion.div>

        {/* Examples */}
        <div className="space-y-12">
          {examples.map((example, index) => (
            <motion.section
              key={example.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + index * 0.05 }}
            >
              <div className="glass-card overflow-hidden rounded-xl">
                <div className="border-b border-border p-6">
                  <h2 className="text-xl font-bold">{example.title}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">{example.description}</p>
                </div>

                <Tabs defaultValue="python" className="p-6">
                  <TabsList>
                    <TabsTrigger value="python">Python</TabsTrigger>
                    <TabsTrigger value="javascript">JavaScript</TabsTrigger>
                    <TabsTrigger value="curl">cURL</TabsTrigger>
                  </TabsList>

                  <TabsContent value="python" className="mt-4">
                    <CodeBlock language="python" code={example.python} />
                  </TabsContent>
                  <TabsContent value="javascript" className="mt-4">
                    <CodeBlock language="javascript" code={example.javascript} />
                  </TabsContent>
                  <TabsContent value="curl" className="mt-4">
                    <CodeBlock language="bash" code={example.curl} />
                  </TabsContent>
                </Tabs>
              </div>
            </motion.section>
          ))}
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
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
              <Link href="/docs/api">
                <BookOpen className="mr-2 h-4 w-4" />
                API Reference
              </Link>
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
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
