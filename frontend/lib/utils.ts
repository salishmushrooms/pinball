/**
 * Utility functions for the MNP Analyzer app
 */

/**
 * Supported seasons for display in filters.
 * Update this array when adding support for new seasons.
 */
export const SUPPORTED_SEASONS = [20, 21, 22, 23] as const;

/**
 * Filter an array of seasons to only include supported seasons.
 */
export function filterSupportedSeasons(seasons: number[]): number[] {
  return seasons.filter(s => (SUPPORTED_SEASONS as readonly number[]).includes(s));
}

/**
 * Merges class names, filtering out undefined/null values
 * Useful for conditional styling
 */
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

/**
 * Format a score for display using compact notation with 3 significant figures
 * Examples: 22.5M, 1.23M, 456K, 12.3K, 1.23K, 456
 */
export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'N/A';

  if (score >= 1_000_000_000) {
    // Billions: show up to 3 sig figs
    const val = score / 1_000_000_000;
    return val >= 100 ? `${Math.round(val)}B` : val >= 10 ? `${val.toFixed(1)}B` : `${val.toFixed(2)}B`;
  } else if (score >= 1_000_000) {
    // Millions: show up to 3 sig figs
    const val = score / 1_000_000;
    return val >= 100 ? `${Math.round(val)}M` : val >= 10 ? `${val.toFixed(1)}M` : `${val.toFixed(2)}M`;
  } else if (score >= 1_000) {
    // Thousands: show up to 3 sig figs
    const val = score / 1_000;
    return val >= 100 ? `${Math.round(val)}K` : val >= 10 ? `${val.toFixed(1)}K` : `${val.toFixed(2)}K`;
  }
  // Below 1000: show as-is
  return score.toString();
}
