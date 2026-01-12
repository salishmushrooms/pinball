'use client';

import React from 'react';
import { cn } from '@/lib/utils';

export interface FilterChipData {
  /** Unique key for the filter (e.g., 'season', 'venue', 'team') */
  key: string;
  /** Display label for the filter type */
  label: string;
  /** Display value(s) for the filter */
  value: string;
  /** Callback when the chip is dismissed */
  onRemove: () => void;
}

interface FilterChipProps {
  /** The filter data to display */
  filter: FilterChipData;
  /** Additional className for styling */
  className?: string;
}

/**
 * Individual filter chip with dismiss button.
 * Used to display active filters that can be removed with one click.
 */
export function FilterChip({ filter, className }: FilterChipProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm',
        'bg-blue-50 text-blue-800 border border-blue-200',
        'transition-colors hover:bg-blue-100',
        className
      )}
    >
      <span className="font-medium">{filter.label}:</span>
      <span>{filter.value}</span>
      <button
        onClick={filter.onRemove}
        className={cn(
          'ml-1 p-0.5 rounded-full',
          'hover:bg-blue-200 transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-1'
        )}
        aria-label={`Remove ${filter.label} filter`}
      >
        <svg
          className="w-3.5 h-3.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </span>
  );
}

interface FilterChipsProps {
  /** Array of active filters to display */
  filters: FilterChipData[];
  /** Callback to clear all filters */
  onClearAll?: () => void;
  /** Additional className for the container */
  className?: string;
}

/**
 * Container component for displaying multiple filter chips.
 * Shows active filters with individual remove buttons and optional "Clear All".
 */
export function FilterChips({ filters, onClearAll, className }: FilterChipsProps) {
  if (filters.length === 0) {
    return null;
  }

  return (
    <div className={cn('flex flex-wrap items-center gap-2', className)}>
      {filters.map((filter) => (
        <FilterChip key={filter.key} filter={filter} />
      ))}
      {onClearAll && filters.length > 1 && (
        <button
          onClick={onClearAll}
          className={cn(
            'text-sm font-medium px-2 py-1 rounded',
            'text-gray-600 hover:text-gray-800 hover:bg-gray-100',
            'transition-colors'
          )}
        >
          Clear All
        </button>
      )}
    </div>
  );
}
