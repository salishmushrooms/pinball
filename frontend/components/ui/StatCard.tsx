import React from 'react';
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
}

export function StatCard({
  label,
  value,
  trend,
  trendDirection = 'neutral',
  icon,
  className,
  tooltip,
}: StatCardProps) {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  return (
    <div
      className={cn('rounded-lg p-4 text-center', className)}
      style={{
        backgroundColor: 'var(--color-primary-50)',
        border: '1px solid var(--border-light)',
      }}
    >
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
      {trend && (
        <div className={cn('text-sm mt-2', trendColors[trendDirection])}>
          {trend}
        </div>
      )}
    </div>
  );
}
