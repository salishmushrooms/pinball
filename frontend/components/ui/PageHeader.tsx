import React from 'react';
import { cn } from '@/lib/utils';

interface PageHeaderProps {
  title: string;
  description?: string;
  className?: string;
  action?: React.ReactNode;
}

export function PageHeader({ title, description, className, action }: PageHeaderProps) {
  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
        {action && <div>{action}</div>}
      </div>
      {description && <p className="text-gray-600">{description}</p>}
    </div>
  );
}
