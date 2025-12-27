'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface TruncatedTextProps {
  children: React.ReactNode;
  /** Maximum width in pixels or CSS value (default: 120px on mobile, none on desktop) */
  maxWidth?: string | number;
  /** Whether to show tooltip with full text on hover */
  showTooltip?: boolean;
  /** Additional className */
  className?: string;
  /** Title attribute for tooltip (defaults to children if string) */
  title?: string;
}

/**
 * Truncates text with ellipsis and optional tooltip.
 * By default, only truncates on mobile (< sm breakpoint).
 */
export function TruncatedText({
  children,
  maxWidth,
  showTooltip = true,
  className,
  title,
}: TruncatedTextProps) {
  const tooltipText = title || (typeof children === 'string' ? children : undefined);

  const maxWidthStyle = typeof maxWidth === 'number' ? `${maxWidth}px` : maxWidth;

  return (
    <span
      className={cn(
        'truncate inline-block align-bottom',
        // Default: truncate on mobile only, full width on desktop
        !maxWidth && 'max-w-[120px] sm:max-w-none',
        className
      )}
      style={maxWidth ? { maxWidth: maxWidthStyle } : undefined}
      title={showTooltip ? tooltipText : undefined}
    >
      {children}
    </span>
  );
}
