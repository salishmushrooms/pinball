import React from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'interactive';
  href?: string;
}

export function Card({ children, className, variant = 'default', href }: CardProps) {
  const baseStyles = 'rounded-lg shadow-md border';
  const variantStyles = {
    default: '',
    interactive: 'hover:shadow-lg hover:border-blue-500 transition-all cursor-pointer',
  };

  const combinedStyles = cn(baseStyles, variantStyles[variant], className);

  const style = {
    backgroundColor: 'var(--card-bg)',
    borderColor: 'var(--border)',
  };

  if (href && variant === 'interactive') {
    return (
      <Link href={href} className={cn(combinedStyles, 'block')} style={style}>
        {children}
      </Link>
    );
  }

  return <div className={combinedStyles} style={style}>{children}</div>;
}

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export function CardHeader({ children, className }: CardHeaderProps) {
  return (
    <div className={cn('px-6 py-4 border-b', className)} style={{ borderColor: 'var(--border)' }}>
      {children}
    </div>
  );
}

interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
}

export function CardTitle({ children, className }: CardTitleProps) {
  return (
    <h3 className={cn('text-lg font-semibold', className)} style={{ color: 'var(--text-primary)' }}>
      {children}
    </h3>
  );
}

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export function CardContent({ children, className }: CardContentProps) {
  return <div className={cn('p-6', className)}>{children}</div>;
}

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
}

export function CardFooter({ children, className }: CardFooterProps) {
  return (
    <div
      className={cn('px-6 py-4 border-t', className)}
      style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg-secondary)' }}
    >
      {children}
    </div>
  );
}

// Compose Card with sub-components
Card.Header = CardHeader;
Card.Title = CardTitle;
Card.Content = CardContent;
Card.Footer = CardFooter;
