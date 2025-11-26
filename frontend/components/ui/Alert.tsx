import React from 'react';
import { cn } from '@/lib/utils';

interface AlertProps {
  children: React.ReactNode;
  variant?: 'error' | 'warning' | 'success' | 'info';
  title?: string;
  className?: string;
}

export function Alert({ children, variant = 'info', title, className }: AlertProps) {
  const baseStyles = 'px-4 py-3 rounded border';

  const variantStyles = {
    error: 'bg-red-50 border-red-200 text-red-700',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    success: 'bg-green-50 border-green-200 text-green-700',
    info: 'bg-blue-50 border-blue-200 text-blue-700',
  };

  return (
    <div className={cn(baseStyles, variantStyles[variant], className)}>
      {title && <strong className="font-bold">{title}: </strong>}
      <span>{children}</span>
    </div>
  );
}
