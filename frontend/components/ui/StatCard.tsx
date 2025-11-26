import React from 'react';
import { Card } from './Card';
import { cn } from '@/lib/utils';

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: string;
  trendDirection?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  className?: string;
}

export function StatCard({
  label,
  value,
  trend,
  trendDirection = 'neutral',
  icon,
  className,
}: StatCardProps) {
  const trendColors = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  return (
    <Card className={className}>
      <Card.Content className="text-center">
        {icon && <div className="flex justify-center mb-2 text-gray-400">{icon}</div>}
        <div className="text-sm font-medium text-gray-600 mb-1">{label}</div>
        <div className="text-3xl font-bold text-gray-900">{value}</div>
        {trend && (
          <div className={cn('text-sm mt-2', trendColors[trendDirection])}>
            {trend}
          </div>
        )}
      </Card.Content>
    </Card>
  );
}
