'use client';

import React, { useState } from 'react';
import { Card } from './Card';
import { Badge } from './Badge';
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
}: FilterPanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (!collapsible) {
    // Non-collapsible mode: standard Card layout
    return (
      <Card className={className}>
        <Card.Header>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Card.Title>{title}</Card.Title>
              {activeFilterCount > 0 && (
                <Badge variant="info">{activeFilterCount} active</Badge>
              )}
            </div>
            {showClearAll && onClearAll && activeFilterCount > 0 && (
              <button
                onClick={onClearAll}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                Clear All
              </button>
            )}
          </div>
        </Card.Header>
        <Card.Content>{children}</Card.Content>
      </Card>
    );
  }

  // Collapsible mode
  return (
    <div className={cn('border border-gray-200 rounded-lg bg-white', className)}>
      <div className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-3 flex-1"
          aria-expanded={isOpen}
          aria-label={`${isOpen ? 'Collapse' : 'Expand'} ${title}`}
        >
          <span className="text-lg font-semibold text-gray-900">{title}</span>
          {activeFilterCount > 0 && (
            <Badge variant="info">{activeFilterCount} active</Badge>
          )}
        </button>
        <div className="flex items-center gap-3">
          {showClearAll && onClearAll && activeFilterCount > 0 && (
            <button
              onClick={onClearAll}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
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
                'w-5 h-5 text-gray-500 transition-transform',
                isOpen && 'transform rotate-180'
              )}
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
        <div className="px-6 py-4 border-t border-gray-200">{children}</div>
      )}
    </div>
  );
}
