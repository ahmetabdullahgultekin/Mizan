'use client';

import * as React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Github, Twitter, Heart, Sparkles, ExternalLink } from 'lucide-react';

import { cn } from '@/lib/utils';
import { navigationConfig } from '@/config/navigation';
import { Separator } from '@/components/ui/separator';
import { staggerContainer, staggerItem } from '@/lib/animations/variants';

/**
 * Footer Component
 *
 * Site footer with navigation links, social links, and copyright.
 */
export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="relative border-t border-white/10 bg-background/50 backdrop-blur-sm">
      {/* Gradient line at top */}
      <div className="absolute left-0 right-0 top-0 h-px bg-gradient-to-r from-transparent via-gold-500/50 to-transparent" />

      <div className="container mx-auto px-4 py-12">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid gap-8 md:grid-cols-2 lg:grid-cols-5"
        >
          {/* Brand Section */}
          <motion.div variants={staggerItem} className="lg:col-span-2">
            <Link href="/" className="inline-flex items-center space-x-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-gold-500 to-gold-600">
                <Sparkles className="h-5 w-5 text-black" />
              </div>
              <span className="text-xl font-bold text-gradient-gold">Mizan</span>
            </Link>

            <p className="mt-4 max-w-xs text-sm text-muted-foreground">
              High-precision Quranic text analysis engine. Verified against scholarly standards.
            </p>

            {/* Arabic tagline */}
            <p className="mt-2 font-arabic text-sm text-gold-500/70" dir="rtl" lang="ar">
              الميزان - لتحليل النص القرآني
            </p>

            {/* Social Links */}
            <div className="mt-6 flex space-x-4">
              <a
                href="https://github.com/ahmetabdullahgultekin/Mizan"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground transition-colors hover:text-gold-500"
              >
                <Github className="h-5 w-5" />
                <span className="sr-only">GitHub</span>
              </a>
              <a
                href="https://twitter.com/mizan"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground transition-colors hover:text-gold-500"
              >
                <Twitter className="h-5 w-5" />
                <span className="sr-only">Twitter</span>
              </a>
            </div>
          </motion.div>

          {/* Product Links */}
          <motion.div variants={staggerItem}>
            <h3 className="mb-4 text-sm font-semibold text-foreground">Product</h3>
            <ul className="space-y-3">
              {navigationConfig.footerNav.product.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {item.title}
                  </Link>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* Resources Links */}
          <motion.div variants={staggerItem}>
            <h3 className="mb-4 text-sm font-semibold text-foreground">Resources</h3>
            <ul className="space-y-3">
              {navigationConfig.footerNav.resources.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {item.title}
                  </Link>
                </li>
              ))}
            </ul>
          </motion.div>

          {/* Company Links */}
          <motion.div variants={staggerItem}>
            <h3 className="mb-4 text-sm font-semibold text-foreground">Company</h3>
            <ul className="space-y-3">
              {navigationConfig.footerNav.company.map((item) => (
                <li key={item.href}>
                  {'external' in item && item.external ? (
                    <a
                      href={item.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-sm text-muted-foreground transition-colors hover:text-foreground"
                    >
                      {item.title}
                      <ExternalLink className="ml-1 h-3 w-3" />
                    </a>
                  ) : (
                    <Link
                      href={item.href}
                      className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                    >
                      {item.title}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </motion.div>
        </motion.div>

        <Separator className="my-8 bg-white/10" />

        {/* Bottom Bar */}
        <div className="flex flex-col items-center justify-between space-y-4 text-sm text-muted-foreground md:flex-row md:space-y-0">
          <div className="flex items-center space-x-1">
            <span>&copy; {currentYear} Mizan.</span>
            <span className="hidden sm:inline">All rights reserved.</span>
          </div>

          <div className="flex items-center space-x-1">
            <span>Made with</span>
            <Heart className="h-4 w-4 text-red-500" fill="currentColor" />
            <span>for the</span>
            <span className="font-arabic text-gold-500" dir="rtl" lang="ar">
              أمة
            </span>
          </div>

          <div className="flex space-x-4">
            {navigationConfig.footerNav.legal.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="transition-colors hover:text-foreground"
              >
                {item.title}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
