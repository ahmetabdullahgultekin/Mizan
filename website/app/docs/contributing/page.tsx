'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  Users,
  Copy,
  Check,
  GitBranch,
  Terminal,
  BookOpen,
  Shield,
  TestTube,
  FileCode,
} from 'lucide-react';
import { Github } from '@/components/icons/github';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GlowingOrbs } from '@/components/animated/floating-particles';
import { FeatureCard } from '@/components/animated/glass-card';
import { copyToClipboard } from '@/lib/utils';
import { staggerContainer } from '@/lib/animations/variants';

export default function ContributingPage() {
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
            <Users className="mr-2 h-3 w-3" />
            Contributing
          </Badge>
          <h1 className="mb-4 text-3xl font-bold md:text-4xl">
            Contributing{' '}
            <span className="text-gradient-emerald">Guide</span>
          </h1>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Thank you for your interest in contributing to Mizan Core Engine!
            Whether you are fixing bugs, adding features, or improving documentation,
            your contributions are welcome.
          </p>
        </motion.div>

        {/* Quick Start */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-12"
        >
          <h2 className="mb-6 text-2xl font-bold">Getting Started</h2>
          <div className="glass-card rounded-xl p-6">
            <div className="space-y-4">
              <Step number={1} title="Fork and Clone">
                <CodeBlock
                  language="bash"
                  code={`git clone https://github.com/YOUR_USERNAME/mizan.git
cd mizan
git remote add upstream https://github.com/ahmetabdullahgultekin/Mizan.git`}
                />
              </Step>

              <Step number={2} title="Set Up Development Environment">
                <CodeBlock
                  language="bash"
                  code={`python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pre-commit install`}
                />
              </Step>

              <Step number={3} title="Start Services and Run Tests">
                <CodeBlock
                  language="bash"
                  code={`docker-compose up -d db redis
alembic upgrade head
pytest`}
                />
              </Step>
            </div>
          </div>
        </motion.section>

        {/* Branch Naming */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="mb-12"
        >
          <h2 className="mb-6 text-2xl font-bold">Branch Naming</h2>
          <div className="glass-card rounded-xl p-6">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <BranchExample prefix="feature/" example="add-root-extraction" description="New features" />
              <BranchExample prefix="fix/" example="abjad-calculation-error" description="Bug fixes" />
              <BranchExample prefix="docs/" example="update-api-reference" description="Documentation" />
              <BranchExample prefix="refactor/" example="simplify-letter-counter" description="Refactoring" />
              <BranchExample prefix="test/" example="add-property-tests" description="Tests" />
              <BranchExample prefix="chore/" example="update-dependencies" description="Maintenance" />
            </div>
          </div>
        </motion.section>

        {/* Coding Standards */}
        <motion.section
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="mb-12"
        >
          <h2 className="mb-6 text-2xl font-bold">Coding Standards</h2>
          <div className="grid gap-6 md:grid-cols-2">
            <FeatureCard
              icon={<FileCode className="h-6 w-6" />}
              title="Python Style"
              description="PEP 8, type hints for all signatures, max 100 char lines, Ruff for linting and formatting."
              delay={0}
            />
            <FeatureCard
              icon={<GitBranch className="h-6 w-6" />}
              title="Architecture"
              description="Hexagonal Architecture. Domain layer has no external dependencies. Use dependency injection."
              delay={0.1}
            />
            <FeatureCard
              icon={<TestTube className="h-6 w-6" />}
              title="Testing"
              description="Test one thing per function. Include positive and negative cases. Use fixtures for setup."
              delay={0.2}
            />
            <FeatureCard
              icon={<Shield className="h-6 w-6" />}
              title="Scholarly Accuracy"
              description="Accuracy is paramount. Verify against authoritative sources. Document references in code."
              delay={0.3}
            />
          </div>
        </motion.section>

        {/* Commit Messages */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <h2 className="mb-6 text-2xl font-bold">Commit Messages</h2>
          <div className="glass-card rounded-xl p-6">
            <p className="mb-4 text-sm text-muted-foreground">
              Follow the{' '}
              <a
                href="https://www.conventionalcommits.org"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gold-500 hover:underline"
              >
                Conventional Commits
              </a>{' '}
              format:
            </p>
            <CodeBlock
              language="text"
              code={`type(scope): brief description

Longer explanation if needed.

Fixes #123`}
            />
            <div className="mt-4 grid gap-2 sm:grid-cols-2">
              <CommitType type="feat" description="New feature" />
              <CommitType type="fix" description="Bug fix" />
              <CommitType type="docs" description="Documentation" />
              <CommitType type="refactor" description="Code restructuring" />
              <CommitType type="test" description="Adding tests" />
              <CommitType type="chore" description="Maintenance" />
            </div>
          </div>
        </motion.section>

        {/* PR Requirements */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <h2 className="mb-6 text-2xl font-bold">Pull Request Checklist</h2>
          <div className="glass-card rounded-xl p-6">
            <ul className="space-y-3">
              <ChecklistItem text="All tests pass (pytest)" />
              <ChecklistItem text="Code follows project style guidelines (ruff check, ruff format)" />
              <ChecklistItem text="Type checking passes (mypy src/mizan)" />
              <ChecklistItem text="Documentation is updated if needed" />
              <ChecklistItem text="Commit messages are clear and follow conventional commits" />
              <ChecklistItem text="PR description explains the changes and why" />
            </ul>
          </div>
        </motion.section>

        {/* Scholarly Accuracy */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-12"
        >
          <h2 className="mb-6 text-2xl font-bold">Scholarly Accuracy</h2>
          <div className="glass-card rounded-xl p-6">
            <p className="mb-4 text-sm text-muted-foreground">
              Mizan is a scholarly tool. <strong>Accuracy is paramount.</strong> Before
              modifying any calculation or counting logic:
            </p>
            <ol className="list-decimal space-y-2 pl-6 text-sm text-muted-foreground">
              <li>Research the standard and verify against authoritative sources</li>
              <li>Document your sources in code comments</li>
              <li>Test against known verified values</li>
              <li>Update STANDARDS.py if documenting new standards</li>
            </ol>
            <div className="mt-4 h-px w-full bg-gradient-to-r from-transparent via-gold-500/50 to-transparent" />
            <p className="mt-4 text-sm text-muted-foreground">
              <strong>Authoritative sources:</strong> Tanzil.net, Quran.com, IslamWeb,
              classical Islamic scholarship (Ibn Kathir, etc.)
            </p>
          </div>
        </motion.section>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <p
            className="mb-4 font-arabic text-lg text-gold-500/70"
            dir="rtl"
            lang="ar"
          >
            بارك الله فيكم
          </p>
          <p className="mb-6 text-sm text-muted-foreground italic">
            May Allah bless you - Thank you for contributing!
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button variant="glow" size="lg" asChild>
              <a
                href="https://github.com/ahmetabdullahgultekin/Mizan"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Github className="mr-2 h-4 w-4" />
                View on GitHub
              </a>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/docs">
                <BookOpen className="mr-2 h-4 w-4" />
                Documentation
              </Link>
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

function Step({
  number,
  title,
  children,
}: {
  number: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gold-500/10 text-xs font-bold text-gold-500">
          {number}
        </span>
        <h3 className="font-semibold">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function BranchExample({
  prefix,
  example,
  description,
}: {
  prefix: string;
  example: string;
  description: string;
}) {
  return (
    <div className="rounded-lg bg-background p-3">
      <code className="text-sm">
        <span className="text-gold-500">{prefix}</span>
        <span className="text-muted-foreground">{example}</span>
      </code>
      <p className="mt-1 text-xs text-muted-foreground">{description}</p>
    </div>
  );
}

function CommitType({ type, description }: { type: string; description: string }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <code className="rounded bg-muted px-1.5 py-0.5 text-xs text-gold-500">{type}</code>
      <span className="text-muted-foreground">{description}</span>
    </div>
  );
}

function ChecklistItem({ text }: { text: string }) {
  return (
    <li className="flex items-start gap-2 text-sm text-muted-foreground">
      <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
      {text}
    </li>
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
