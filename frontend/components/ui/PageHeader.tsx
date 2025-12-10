import React from 'react';
import { cn } from '@/lib/utils';

interface PageHeaderProps {
  title: string;
  description?: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}

export function PageHeader({ title, description, className, action }: PageHeaderProps) {
  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>{title}</h1>
        {action && <div>{action}</div>}
      </div>
      {description && <div style={{ color: 'var(--text-secondary)' }}>{description}</div>}
    </div>
  );
}
