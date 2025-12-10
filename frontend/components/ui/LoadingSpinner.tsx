import React from 'react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  fullPage?: boolean;
  className?: string;
}

export function LoadingSpinner({
  size = 'md',
  text,
  fullPage = false,
  className,
}: LoadingSpinnerProps) {
  const sizeStyles = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-3',
    lg: 'h-12 w-12 border-4',
  };

  const spinner = (
    <div
      className={cn(
        'animate-spin rounded-full border-blue-600 border-t-transparent',
        sizeStyles[size]
      )}
      role="status"
      aria-label="Loading"
    />
  );

  const content = (
    <div className={cn('flex flex-col items-center justify-center gap-3', className)}>
      {spinner}
      {text && <div className="text-sm" style={{ color: 'var(--text-secondary)' }}>{text}</div>}
    </div>
  );

  if (fullPage) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        {content}
      </div>
    );
  }

  return content;
}
