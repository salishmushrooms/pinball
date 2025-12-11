'use client';

import React from 'react';
import { cn } from '@/lib/utils';

type ContainerSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

interface ContentContainerProps {
  children: React.ReactNode;
  /**
   * Maximum width of the container
   * - sm: max-w-2xl (672px) - Narrow content like forms
   * - md: max-w-3xl (768px) - Medium tables (3-4 columns)
   * - lg: max-w-4xl (896px) - Standard tables (4-5 columns)
   * - xl: max-w-5xl (1024px) - Wide tables (5+ columns)
   * - full: max-w-full (100%) - Full width (default table behavior)
   */
  size?: ContainerSize;
  className?: string;
}

const sizeClasses: Record<ContainerSize, string> = {
  sm: 'max-w-2xl',
  md: 'max-w-3xl',
  lg: 'max-w-4xl',
  xl: 'max-w-5xl',
  full: 'max-w-full',
};

/**
 * ContentContainer - Constrains content width on desktop while keeping full-width on mobile
 *
 * Use this component to prevent tables and content from stretching too wide on desktop
 * screens, which can create excessive whitespace and make data harder to read.
 *
 * @example
 * // Standard table with 3-4 columns
 * <ContentContainer size="md">
 *   <Card>
 *     <Table>...</Table>
 *   </Card>
 * </ContentContainer>
 *
 * @example
 * // Wider table with more columns
 * <ContentContainer size="lg">
 *   <Card>
 *     <Table>...</Table>
 *   </Card>
 * </ContentContainer>
 */
export function ContentContainer({
  children,
  size = 'lg',
  className,
}: ContentContainerProps) {
  return (
    <div className={cn(sizeClasses[size], className)}>
      {children}
    </div>
  );
}
