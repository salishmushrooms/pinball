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
 * Mobile: Shows inline text below (no icon needed)
 * Includes ARIA attributes for accessibility
 */
export function Tooltip({ content, className, iconSize = 14 }: TooltipProps) {
  return (
    <>
      {/* Desktop: Info icon with hover tooltip */}
      <span
        className={cn('tooltip-wrapper hidden sm:inline-flex', className)}
        role="tooltip"
        aria-label={content}
      >
        <Info
          size={iconSize}
          className="tooltip-icon"
          style={{ color: 'var(--text-muted)' }}
        />
        <span className="tooltip-content" role="status">
          {content}
        </span>
      </span>

      {/* Mobile: Inline text (no icon) */}
      <span
        className={cn('sm:hidden block text-xs mt-1', className)}
        style={{ color: 'var(--text-muted)' }}
      >
        {content}
      </span>
    </>
  );
}
