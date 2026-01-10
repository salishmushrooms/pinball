import React from 'react';
import { cn } from '@/lib/utils';

interface WinPercentageProps {
  value: number | null;
  className?: string;
  showBadge?: boolean;
}

/**
 * Displays a win percentage with visual emphasis for high values (>70%).
 *
 * @param value - Win percentage (0-100) or null
 * @param showBadge - If true, wraps in a badge-style container for high values
 */
export function WinPercentage({ value, className, showBadge = false }: WinPercentageProps) {
  if (value === null || value === undefined) {
    return <span className={className} style={{ color: 'var(--text-muted)' }}>N/A</span>;
  }

  const isHighWin = value >= 70;
  const formattedValue = `${value.toFixed(0)}%`;

  if (showBadge && isHighWin) {
    return (
      <span
        className={cn(
          'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold',
          className
        )}
        style={{
          backgroundColor: 'var(--color-success-50)',
          color: 'var(--color-success-700)',
        }}
      >
        {formattedValue}
      </span>
    );
  }

  return (
    <span
      className={cn(isHighWin && 'font-semibold', className)}
      style={{
        color: isHighWin ? 'var(--color-success-600)' : 'var(--text-primary)',
      }}
    >
      {formattedValue}
    </span>
  );
}
