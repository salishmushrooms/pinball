'use client';

import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Tooltip } from './Tooltip';

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: string;
  trendDirection?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  className?: string;
  tooltip?: string;
  footnote?: string;
  href?: string;
}

export function StatCard({
  label,
  value,
  trend,
  trendDirection = 'neutral',
  icon,
  className,
  tooltip,
  footnote,
  href,
}: StatCardProps) {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  const content = (
    <>
      <div
        className="text-xs font-medium uppercase tracking-wide mb-1"
        style={{ color: 'var(--text-muted)' }}
      >
        <div className="flex items-center gap-1">
          {icon && (
            <span style={{ color: 'var(--color-primary-600)' }}>
              {icon}
            </span>
          )}
          {label}
          {tooltip && <Tooltip content={tooltip} iconSize={12} />}
        </div>
      </div>
      <div
        className="text-2xl font-bold"
        style={{ color: 'var(--text-primary)' }}
      >
        {value}
      </div>
      {footnote && (
        <div
          className="text-xs mt-1"
          style={{ color: 'var(--text-muted)' }}
        >
          * {footnote}
        </div>
      )}
      {trend && (
        <div className={cn('text-sm mt-1', trendColors[trendDirection])}>
          {trend}
        </div>
      )}
    </>
  );

  const baseStyles: React.CSSProperties = {
    backgroundColor: 'var(--card-bg)',
    borderLeft: '3px solid var(--color-primary-500)',
    borderTop: '1px solid var(--border-light)',
    borderRight: '1px solid var(--border-light)',
    borderBottom: '1px solid var(--border-light)',
  };

  if (href) {
    return (
      <Link
        href={href}
        className={cn(
          'rounded-md p-3 md:p-4 block transition-all duration-200 hover:scale-[1.02]',
          className
        )}
        style={{
          ...baseStyles,
          textDecoration: 'none',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = 'var(--card-bg-secondary)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'var(--card-bg)';
        }}
      >
        {content}
      </Link>
    );
  }

  return (
    <div
      className={cn('rounded-md p-3 md:p-4', className)}
      style={baseStyles}
    >
      {content}
    </div>
  );
}
