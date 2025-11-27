/**
 * Custom React hooks for common functionality
 */

import { useEffect, useRef, DependencyList } from 'react';

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
  const cleanupRef = useRef<(() => void) | void>();

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
