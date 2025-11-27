/**
 * Utility functions for the MNP Analyzer app
 */

/**
 * Merges class names, filtering out undefined/null values
 * Useful for conditional styling
 */
export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
