import React from 'react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn('text-center py-12', className)}>
      {icon && <div className="flex justify-center mb-4" style={{ color: 'var(--text-muted)' }}>{icon}</div>}
      <h3 className="text-lg font-medium mb-2" style={{ color: 'var(--text-primary)' }}>{title}</h3>
      {description && <div className="mb-6" style={{ color: 'var(--text-secondary)' }}>{description}</div>}
      {action && <div className="flex justify-center">{action}</div>}
    </div>
  );
}
