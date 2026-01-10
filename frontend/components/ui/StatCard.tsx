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
      {icon && (
        <div
          className="flex justify-center mb-2"
          style={{ color: 'var(--color-primary-600)' }}
        >
          {icon}
        </div>
      )}
      <div
        className="text-xs font-medium uppercase tracking-wide mb-1"
        style={{ color: 'var(--text-muted)' }}
      >
        <div className="flex items-center justify-center gap-1">
          {label}
          {tooltip && <Tooltip content={tooltip} iconSize={12} />}
        </div>
      </div>
      <div
        className="text-2xl font-bold"
        style={{ color: 'var(--color-primary-700)' }}
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
        <div className={cn('text-sm mt-2', trendColors[trendDirection])}>
          {trend}
        </div>
      )}
    </>
  );

  const baseStyles = {
    backgroundColor: 'var(--color-primary-50)',
    border: '1px solid var(--border-light)',
  };

  if (href) {
    return (
      <Link
        href={href}
        className={cn(
          'rounded-lg p-4 md:p-6 text-center block transition-all duration-200 hover:scale-105',
          className
        )}
        style={{
          ...baseStyles,
          textDecoration: 'none',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = 'var(--color-primary-100)';
          e.currentTarget.style.borderColor = 'var(--color-primary-300)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'var(--color-primary-50)';
          e.currentTarget.style.borderColor = 'var(--border-light)';
        }}
      >
        {content}
      </Link>
    );
  }

  return (
    <div
      className={cn('rounded-lg p-4 md:p-6 text-center', className)}
      style={baseStyles}
    >
      {content}
    </div>
  );
}
