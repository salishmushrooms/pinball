'use client';

import React from 'react';
import { Info } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TooltipProps {
  content: string;
  className?: string;
  iconSize?: number;
}

/**
 * Tooltip component with Info icon
 *
 * Desktop: Shows tooltip on hover
 * Mobile: Hidden (tooltips don't work well on touch devices)
 * Includes ARIA attributes for accessibility
 */
export function Tooltip({ content, className, iconSize = 14 }: TooltipProps) {
  return (
    <span
      className={cn('group relative hidden sm:inline-flex items-center cursor-help', className)}
      aria-label={content}
    >
      <Info
        size={iconSize}
        className="transition-colors"
        style={{ color: 'var(--text-muted)' }}
      />
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 -translate-y-2 px-3 py-2 rounded-md text-xs text-white text-center whitespace-normal max-w-60 w-max pointer-events-none opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity duration-150 z-50 shadow-lg before:content-[''] before:absolute before:top-full before:left-1/2 before:-translate-x-1/2 before:border-6 before:border-transparent before:border-t-[var(--color-gray-900)]"
        style={{ backgroundColor: 'var(--color-gray-900)' }}
      >
        {content}
      </span>
    </span>
  );
}
