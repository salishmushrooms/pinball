'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';

interface CollapsibleProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  className?: string;
  badge?: React.ReactNode;
}

export function Collapsible({
  title,
  children,
  defaultOpen = false,
  className,
  badge,
}: CollapsibleProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={cn('border border-gray-200 rounded-lg bg-white', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold text-gray-900">{title}</span>
          {badge && <span>{badge}</span>}
        </div>
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
      {isOpen && (
        <div className="px-6 py-4 border-t border-gray-200">
          {children}
        </div>
      )}
    </div>
  );
}
