'use client';

import * as React from 'react';
import { motion } from 'framer-motion';
import { Settings2, Info } from 'lucide-react';

import { cn } from '@/lib/utils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { LetterCountMethod, AbjadSystem } from '@/types/api';

interface MethodSelectorProps {
  letterMethod: LetterCountMethod;
  abjadSystem: AbjadSystem;
  onLetterMethodChange: (method: LetterCountMethod) => void;
  onAbjadSystemChange: (system: AbjadSystem) => void;
  className?: string;
}

/**
 * Method Selector Component
 *
 * Allows users to choose counting methods and Abjad systems.
 */
export function MethodSelector({
  letterMethod,
  abjadSystem,
  onLetterMethodChange,
  onAbjadSystemChange,
  className,
}: MethodSelectorProps) {
  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center gap-2">
        <Settings2 className="h-5 w-5 text-emerald-500" />
        <h3 className="font-medium">Analysis Settings</h3>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Letter Counting Method */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground">Letter Counting Method</label>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-3.5 w-3.5 text-muted-foreground/50" />
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p className="text-xs">
                    <strong>Traditional:</strong> Includes Alif Wasla, excludes Khanjariyya
                    <br />
                    <strong>Uthmani Full:</strong> Includes both special characters
                    <br />
                    <strong>No Wasla:</strong> Base letters only
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <Select
            value={letterMethod}
            onValueChange={(value) => onLetterMethodChange(value as LetterCountMethod)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="traditional">
                <span className="flex items-center gap-2">
                  <span>Traditional</span>
                  <span className="text-xs text-muted-foreground">(Recommended)</span>
                </span>
              </SelectItem>
              <SelectItem value="uthmani_full">Uthmani Full</SelectItem>
              <SelectItem value="no_wasla">No Wasla</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Abjad System */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground">Abjad System</label>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Info className="h-3.5 w-3.5 text-muted-foreground/50" />
                </TooltipTrigger>
                <TooltipContent className="max-w-xs">
                  <p className="text-xs">
                    <strong>Mashriqi:</strong> Eastern system (most common)
                    <br />
                    <strong>Maghribi:</strong> Western/North African system
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <Select
            value={abjadSystem}
            onValueChange={(value) => onAbjadSystemChange(value as AbjadSystem)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="mashriqi">
                <span className="flex items-center gap-2">
                  <span>Mashriqi (Eastern)</span>
                  <span className="text-xs text-muted-foreground">(Default)</span>
                </span>
              </SelectItem>
              <SelectItem value="maghribi">Maghribi (Western)</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Method explanation */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="rounded-lg bg-muted/50 p-3 text-xs text-muted-foreground"
      >
        <p>
          <strong className="text-foreground">Current settings:</strong> Using{' '}
          <span className="text-gold-500">{getMethodLabel(letterMethod)}</span> letter counting
          with <span className="text-emerald-500">{getSystemLabel(abjadSystem)}</span> Abjad
          values.
        </p>
      </motion.div>
    </div>
  );
}

function getMethodLabel(method: LetterCountMethod): string {
  const labels: Record<LetterCountMethod, string> = {
    traditional: 'Traditional',
    uthmani_full: 'Uthmani Full',
    no_wasla: 'No Wasla',
  };
  return labels[method];
}

function getSystemLabel(system: AbjadSystem): string {
  const labels: Record<AbjadSystem, string> = {
    mashriqi: 'Mashriqi (Eastern)',
    maghribi: 'Maghribi (Western)',
  };
  return labels[system];
}
