/**
 * Custom React hooks for common functionality
 */

import { useEffect, useRef, useCallback, useState, DependencyList } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import type { FilterChipData } from '@/components/ui/FilterChip';

/**
 * Debounced effect hook
 *
 * Delays the execution of the effect callback until after the specified
 * delay has elapsed since the last time the dependencies changed.
 *
 * Perfect for:
 * - Search input fields
 * - Filter changes that trigger expensive API calls
 * - Multi-select components
 *
 * @param callback - The effect to run after debounce delay
 * @param delay - Delay in milliseconds (default: 500ms)
 * @param deps - Dependency array (like useEffect)
 *
 * @example
 * ```tsx
 * const [searchTerm, setSearchTerm] = useState('');
 * const [results, setResults] = useState([]);
 *
 * useDebouncedEffect(() => {
 *   // This will only run 500ms after user stops typing
 *   fetchSearchResults(searchTerm).then(setResults);
 * }, 500, [searchTerm]);
 * ```
 */
export function useDebouncedEffect(
  callback: () => void | (() => void),
  delay: number = 500,
  deps: DependencyList = []
) {
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const cleanupRef = useRef<(() => void) | void>(undefined);

  useEffect(() => {
    // Clear any existing timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    // Clear any previous cleanup function
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = undefined;
    }

    // Set new timer
    timerRef.current = setTimeout(() => {
      cleanupRef.current = callback();
    }, delay);

    // Cleanup function
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      if (cleanupRef.current) {
        cleanupRef.current();
      }
    };
  }, deps);
}

// Default filter values used across the app
export const DEFAULT_SEASONS = [22, 23];
export const DEFAULT_ROUNDS = [1, 2, 3, 4];

/**
 * Filter configuration for useURLFilters hook
 */
interface FilterConfig<T> {
  /** URL parameter name */
  urlKey: string;
  /** Default value when not in URL */
  defaultValue: T;
  /** Parse URL string to filter value */
  parse: (value: string | null) => T;
  /** Serialize filter value to URL string (return null to remove from URL) */
  serialize: (value: T, defaultValue: T) => string | null;
}

/**
 * Hook result for a single filter
 */
interface FilterState<T> {
  value: T;
  setValue: (value: T) => void;
  isDefault: boolean;
}

/**
 * Standard filter configurations for common filter types
 */
export const filterConfigs = {
  /**
   * Multi-select seasons filter
   */
  seasons: (defaultSeasons: number[] = DEFAULT_SEASONS): FilterConfig<number[]> => ({
    urlKey: 'seasons',
    defaultValue: defaultSeasons,
    parse: (value) => {
      if (!value) return defaultSeasons;
      // Also check for legacy 'season' single value
      const parsed = value.split(',').map(s => parseInt(s)).filter(n => !isNaN(n));
      return parsed.length > 0 ? parsed : defaultSeasons;
    },
    serialize: (value, defaultValue) => {
      const sortedValue = [...value].sort((a, b) => a - b);
      const sortedDefault = [...defaultValue].sort((a, b) => a - b);
      const isDefault = sortedValue.length === sortedDefault.length &&
        sortedValue.every((v, i) => v === sortedDefault[i]);
      return isDefault ? null : sortedValue.join(',');
    },
  }),

  /**
   * Single venue filter
   */
  venue: (): FilterConfig<string> => ({
    urlKey: 'venue',
    defaultValue: '',
    parse: (value) => value || '',
    serialize: (value) => value || null,
  }),

  /**
   * Multi-select rounds filter
   */
  rounds: (defaultRounds: number[] = DEFAULT_ROUNDS): FilterConfig<number[]> => ({
    urlKey: 'rounds',
    defaultValue: defaultRounds,
    parse: (value) => {
      if (!value) return defaultRounds;
      const parsed = value.split(',').map(r => parseInt(r)).filter(n => !isNaN(n) && n >= 1 && n <= 4);
      return parsed.length > 0 ? parsed : defaultRounds;
    },
    serialize: (value, defaultValue) => {
      const sortedValue = [...value].sort((a, b) => a - b);
      const sortedDefault = [...defaultValue].sort((a, b) => a - b);
      const isDefault = sortedValue.length === sortedDefault.length &&
        sortedValue.every((v, i) => v === sortedDefault[i]);
      return isDefault ? null : sortedValue.join(',');
    },
  }),

  /**
   * Boolean filter (stored as 'true' when non-default)
   */
  boolean: (urlKey: string, defaultValue: boolean): FilterConfig<boolean> => ({
    urlKey,
    defaultValue,
    parse: (value) => value === 'true' ? true : value === 'false' ? false : defaultValue,
    serialize: (value, def) => value === def ? null : String(value),
  }),

  /**
   * Multi-select teams filter
   */
  teams: (): FilterConfig<string[]> => ({
    urlKey: 'teams',
    defaultValue: [],
    parse: (value) => value ? value.split(',').filter(Boolean) : [],
    serialize: (value) => value.length > 0 ? value.join(',') : null,
  }),

  /**
   * Single string select (like scoresFrom: 'venue' | 'all')
   */
  string: (urlKey: string, defaultValue: string): FilterConfig<string> => ({
    urlKey,
    defaultValue,
    parse: (value) => value || defaultValue,
    serialize: (value, def) => value === def ? null : value,
  }),
};

/**
 * Hook for managing URL-synced filters
 *
 * Provides:
 * - Initial state parsed from URL
 * - Automatic URL updates when filters change
 * - Helper to build filter chips with individual remove actions
 *
 * @example
 * ```tsx
 * const { filters, getSeasonChips, clearAllFilters } = useURLFilters({
 *   seasons: filterConfigs.seasons(),
 *   venue: filterConfigs.venue(),
 *   rounds: filterConfigs.rounds(),
 * });
 *
 * // Use filter values
 * const seasonsFilter = filters.seasons.value;
 * const setSeasonsFilter = filters.seasons.setValue;
 *
 * // Get chips for display
 * const seasonChips = getSeasonChips(filters.seasons.value, availableSeasons.length);
 * ```
 */
export function useURLFilters<T extends Record<string, FilterConfig<any>>>(
  configs: T
): {
  filters: { [K in keyof T]: FilterState<ReturnType<T[K]['parse']>> };
  getSeasonChips: (seasons: number[], totalAvailable: number) => FilterChipData[];
  updateURL: (params: Record<string, string | null>) => void;
  clearAllFilters: () => void;
} {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // Initialize state from URL for each filter
  const [filterStates, setFilterStates] = useState<Record<string, any>>(() => {
    const initial: Record<string, any> = {};
    for (const [key, config] of Object.entries(configs)) {
      // Check for legacy 'season' param for seasons filter
      if (key === 'seasons' && !searchParams.get('seasons') && searchParams.get('season')) {
        const legacySeason = parseInt(searchParams.get('season') || '');
        initial[key] = !isNaN(legacySeason) ? [legacySeason] : config.defaultValue;
      } else {
        initial[key] = config.parse(searchParams.get(config.urlKey));
      }
    }
    return initial;
  });

  // Update URL when filters change
  const updateURL = useCallback((params: Record<string, string | null>) => {
    const current = new URLSearchParams(searchParams.toString());

    Object.entries(params).forEach(([key, value]) => {
      if (value === null || value === '') {
        current.delete(key);
      } else {
        current.set(key, value);
      }
    });

    // Remove legacy 'season' param if 'seasons' is set
    if (current.has('seasons')) {
      current.delete('season');
    }

    const newURL = current.toString() ? `?${current.toString()}` : '';
    const currentURL = searchParams.toString() ? `?${searchParams.toString()}` : '';

    // Only update if URL actually changed to prevent infinite loops
    if (newURL !== currentURL) {
      router.replace(`${pathname}${newURL}`, { scroll: false });
    }
  }, [searchParams, router, pathname]);

  // Sync URL when filter states change
  useEffect(() => {
    const params: Record<string, string | null> = {};
    for (const [key, config] of Object.entries(configs)) {
      params[config.urlKey] = config.serialize(filterStates[key], config.defaultValue);
    }
    updateURL(params);
  }, [filterStates, configs, updateURL]);

  // Build filter state objects with setters
  const filters = {} as { [K in keyof T]: FilterState<ReturnType<T[K]['parse']>> };
  for (const key of Object.keys(configs) as (keyof T)[]) {
    const config = configs[key];
    const value = filterStates[key as string];

    filters[key] = {
      value,
      setValue: (newValue: any) => {
        setFilterStates(prev => ({ ...prev, [key as string]: newValue }));
      },
      isDefault: config.serialize(value, config.defaultValue) === null,
    };
  }

  // Helper to generate individual season chips
  const getSeasonChips = useCallback((seasons: number[], totalAvailable: number): FilterChipData[] => {
    // Only show chips if not all seasons are selected
    if (seasons.length === 0 || seasons.length >= totalAvailable) {
      return [];
    }

    const sortedSeasons = [...seasons].sort((a, b) => a - b);
    const seasonsConfig = configs['seasons'] as FilterConfig<number[]> | undefined;
    const defaultSeasons = seasonsConfig?.defaultValue || DEFAULT_SEASONS;

    return sortedSeasons.map(season => ({
      key: `season-${season}`,
      label: 'Season',
      value: `${season}`,
      onRemove: () => {
        const remaining = seasons.filter(s => s !== season);
        // If removing would leave empty, reset to defaults
        setFilterStates(prev => ({
          ...prev,
          seasons: remaining.length > 0 ? remaining : defaultSeasons,
        }));
      },
    }));
  }, [configs]);

  // Clear all filters to defaults
  const clearAllFilters = useCallback(() => {
    const defaults: Record<string, any> = {};
    for (const [key, config] of Object.entries(configs)) {
      defaults[key] = config.defaultValue;
    }
    setFilterStates(defaults);
  }, [configs]);

  return { filters, getSeasonChips, updateURL, clearAllFilters };
}
