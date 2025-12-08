/**
 * Utility functions for the MNP Analyzer app
 */

/**
 * Supported seasons for display in filters.
 * Update this array when adding support for new seasons.
 */
export const SUPPORTED_SEASONS = [20, 21, 22] as const;

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
