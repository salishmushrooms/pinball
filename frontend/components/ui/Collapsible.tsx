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
    <div
      className={cn('border rounded-lg', className)}
      style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg)' }}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between transition-colors hover:opacity-80"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>{title}</span>
          {badge && <span>{badge}</span>}
        </div>
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
      {isOpen && (
        <div className="px-6 py-4 border-t" style={{ borderColor: 'var(--border)' }}>
          {children}
        </div>
      )}
    </div>
  );
}
