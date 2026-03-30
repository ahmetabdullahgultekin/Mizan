'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { Scale, ArrowLeft } from 'lucide-react';
import { Github } from '@/components/icons/github';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GlowingOrbs } from '@/components/animated/floating-particles';

const licenseText = `MIT License

Copyright (c) 2025 Mizan Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.`;

export default function LicensePage() {
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
            <Scale className="mr-2 h-3 w-3" />
            License
          </Badge>
          <h1 className="mb-4 text-3xl font-bold md:text-4xl">
            MIT{' '}
            <span className="text-gradient-gold">License</span>
          </h1>
          <p className="mx-auto max-w-2xl text-muted-foreground">
            Mizan is free and open-source software. Use it, modify it, and share it
            for both personal and commercial purposes.
          </p>
        </motion.div>

        {/* License Text */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mx-auto max-w-3xl"
        >
          <div className="glass-card rounded-xl p-8">
            <pre className="whitespace-pre-wrap font-mono text-sm text-muted-foreground leading-relaxed">
              {licenseText}
            </pre>
          </div>
        </motion.div>

        {/* Summary */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mx-auto mt-8 max-w-3xl"
        >
          <div className="glass-card rounded-xl p-6">
            <h2 className="mb-4 text-lg font-semibold">What this means</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <h3 className="mb-2 text-sm font-medium text-emerald-500">You can:</h3>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li>Use commercially</li>
                  <li>Modify the source code</li>
                  <li>Distribute copies</li>
                  <li>Use privately</li>
                </ul>
              </div>
              <div>
                <h3 className="mb-2 text-sm font-medium text-amber-500">You must:</h3>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li>Include the copyright notice</li>
                  <li>Include the license text</li>
                </ul>
              </div>
            </div>
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row"
        >
          <Button variant="glow" asChild>
            <a
              href="https://github.com/ahmetabdullahgultekin/Mizan"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Github className="mr-2 h-4 w-4" />
              View Source Code
            </a>
          </Button>
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
