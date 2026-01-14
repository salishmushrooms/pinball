'use client';

import React, { useState } from 'react';
import { Badge } from './Badge';
import { FilterChips, type FilterChipData } from './FilterChip';
import { cn } from '@/lib/utils';

interface FilterPanelProps {
  children: React.ReactNode;
  title?: string;
  collapsible?: boolean;
  defaultOpen?: boolean;
  activeFilterCount?: number;
  className?: string;
  showClearAll?: boolean;
  onClearAll?: () => void;
  /** Active filters to display as chips above the panel (always visible) */
  activeFilters?: FilterChipData[];
}

/**
 * Reusable FilterPanel component for standardized filter UI across pages.
 *
 * Features:
 * - Collapsible mode for pages with many filters
 * - Badge showing active filter count
 * - Optional "Clear All" button
 * - Consistent styling and spacing
 *
 * Usage:
 * ```tsx
 * <FilterPanel
 *   title="Filters"
 *   collapsible={true}
 *   activeFilterCount={2}
 *   onClearAll={() => resetFilters()}
 * >
 *   <div className="space-y-6">
 *     <SeasonMultiSelect ... />
 *     <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
 *       <Select ... />
 *       <MultiSelect ... />
 *     </div>
 *   </div>
 * </FilterPanel>
 * ```
 */
export function FilterPanel({
  children,
  title = 'Filters',
  collapsible = false,
  defaultOpen = true,
  activeFilterCount = 0,
  className,
  showClearAll = false,
  onClearAll,
  activeFilters = [],
}: FilterPanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  // Calculate filter count from activeFilters if provided, otherwise use activeFilterCount
  const effectiveFilterCount = activeFilters.length > 0 ? activeFilters.length : activeFilterCount;

  // Filter icon SVG component
  const FilterIcon = () => (
    <svg
      className="w-5 h-5"
      style={{ color: 'var(--filter-icon, #3b82f6)' }}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
      />
    </svg>
  );

  if (!collapsible) {
    // Non-collapsible mode: styled container
    return (
      <div className="space-y-3">
        {/* Filter chips always visible */}
        {activeFilters.length > 0 && (
          <FilterChips filters={activeFilters} onClearAll={onClearAll} />
        )}
        <div
          className={cn('border-2 rounded-lg', className)}
          style={{
            borderColor: 'var(--filter-border, #bfdbfe)',
            backgroundColor: 'var(--filter-bg, #eff6ff)',
          }}
        >
          <div className="px-6 py-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <FilterIcon />
                <span className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>{title}</span>
                {effectiveFilterCount > 0 && activeFilters.length === 0 && (
                  <Badge variant="info">{effectiveFilterCount} active</Badge>
                )}
              </div>
              {showClearAll && onClearAll && effectiveFilterCount > 0 && activeFilters.length === 0 && (
                <button
                  onClick={onClearAll}
                  className="text-sm font-medium"
                  style={{ color: 'var(--text-link)' }}
                >
                  Clear All
                </button>
              )}
            </div>
            {children}
          </div>
        </div>
      </div>
    );
  }

  // Collapsible mode
  return (
    <div className="space-y-3">
      {/* Filter chips always visible above the collapsible panel */}
      {activeFilters.length > 0 && (
        <FilterChips filters={activeFilters} onClearAll={onClearAll} />
      )}
      <div
        className={cn('border-2 rounded-lg', className)}
        style={{
          borderColor: 'var(--filter-border, #bfdbfe)',
          backgroundColor: 'var(--filter-bg, #eff6ff)',
        }}
      >
        <div className="px-6 py-4 flex items-center justify-between transition-colors hover:opacity-90">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-3 flex-1"
            aria-expanded={isOpen}
            aria-label={`${isOpen ? 'Collapse' : 'Expand'} ${title}`}
          >
            <FilterIcon />
            <span className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>{title}</span>
            {effectiveFilterCount > 0 && activeFilters.length === 0 && (
              <Badge variant="info">{effectiveFilterCount} active</Badge>
            )}
          </button>
          <div className="flex items-center gap-3">
            {showClearAll && onClearAll && effectiveFilterCount > 0 && activeFilters.length === 0 && (
              <button
                onClick={onClearAll}
                className="text-sm font-medium"
                style={{ color: 'var(--text-link)' }}
              >
                Clear All
              </button>
            )}
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-1"
              aria-label={`${isOpen ? 'Collapse' : 'Expand'} ${title}`}
            >
              <svg
                className={cn(
                  'w-5 h-5 transition-transform',
                  isOpen && 'transform rotate-180'
                )}
                style={{ color: 'var(--text-muted)' }}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
          </div>
        </div>
        {isOpen && (
          <div className="px-6 py-4 border-t" style={{ borderColor: 'var(--filter-border, #bfdbfe)' }}>{children}</div>
        )}
      </div>
    </div>
  );
}
