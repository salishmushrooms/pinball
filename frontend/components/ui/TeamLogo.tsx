import React from 'react';
import Image from 'next/image';
import { getTeamLogoUrl } from '@/lib/teamLogos';
import { cn } from '@/lib/utils';

export interface TeamLogoProps {
  teamKey: string;
  teamName?: string;
  size?: 'sm' | 'lg';
  className?: string;
  showFallback?: boolean;
  priority?: boolean;
}

/**
 * TeamLogo component displays team logos with automatic Cloudflare variant selection
 *
 * Features:
 * - Automatic variant selection (thumb for sm, full for lg)
 * - Fallback to team key initials when logo unavailable
 * - Next.js Image optimization and lazy loading
 * - Circular design for consistency
 *
 * Usage:
 * - Teams list: <TeamLogo teamKey="TRL" size="sm" />
 * - Team detail header: <TeamLogo teamKey="TRL" size="lg" priority />
 *
 * @param teamKey - Team key from database (e.g., 'TRL', 'SKP')
 * @param teamName - Team name for alt text (optional)
 * @param size - 'sm' (32px, thumb variant) or 'lg' (96px, full variant)
 * @param className - Additional CSS classes
 * @param showFallback - Show team key when logo unavailable (default: true)
 * @param priority - Load image with priority (for above-fold images)
 */
export function TeamLogo({
  teamKey,
  teamName,
  size = 'sm',
  className,
  showFallback = true,
  priority = false,
}: TeamLogoProps) {
  // Use appropriate Cloudflare variant based on size
  const variant = size === 'lg' ? 'full' : 'thumb';
  const logoUrl = getTeamLogoUrl(teamKey, variant);
  const dimension = size === 'sm' ? 32 : 96;

  // Fallback: show team initials when logo unavailable
  if (!logoUrl && showFallback) {
    return (
      <div
        className={cn(
          'inline-flex items-center justify-center flex-shrink-0 rounded-full border',
          className
        )}
        style={{
          width: dimension,
          height: dimension,
          backgroundColor: 'var(--color-gray-100)',
          borderColor: 'var(--border)',
          color: 'var(--text-muted)',
        }}
        title={teamName || teamKey}
      >
        <span
          className="font-semibold select-none"
          style={{
            fontSize: size === 'sm' ? '0.75rem' : '1rem',
          }}
        >
          {teamKey}
        </span>
      </div>
    );
  }

  // No logo and fallback disabled
  if (!logoUrl) return null;

  return (
    <div className={cn('inline-flex flex-shrink-0', className)}>
      <Image
        src={logoUrl}
        alt={teamName || teamKey}
        width={dimension}
        height={dimension}
        className="rounded-full object-cover"
        priority={priority}
      />
    </div>
  );
}
