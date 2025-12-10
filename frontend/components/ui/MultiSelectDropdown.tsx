'use client';

import React, { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';

export interface MultiSelectDropdownOption<T = string | number> {
  value: T;
  label: string;
}

export interface MultiSelectDropdownProps<T = string | number> {
  label?: string;
  options: MultiSelectDropdownOption<T>[];
  value: T[];
  onChange: (value: T[]) => void;
  placeholder?: string;
  helpText?: string;
  className?: string;
  /** Maximum height of the dropdown in pixels (default: 240) */
  maxHeight?: number;
}

export function MultiSelectDropdown<T extends string | number = string | number>({
  label,
  options,
  value,
  onChange,
  placeholder = 'Select options...',
  helpText,
  className = '',
  maxHeight = 240,
}: MultiSelectDropdownProps<T>) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggle = (optionValue: T) => {
    if (value.includes(optionValue)) {
      onChange(value.filter((v) => v !== optionValue));
    } else {
      onChange([...value, optionValue]);
    }
  };

  const handleSelectAll = () => {
    if (value.length === options.length) {
      onChange([]);
    } else {
      onChange(options.map((o) => o.value));
    }
  };

  // Build display text
  const getDisplayText = () => {
    if (value.length === 0) return placeholder;
    if (value.length === options.length) return 'All selected';
    if (value.length <= 2) {
      return options
        .filter((o) => value.includes(o.value))
        .map((o) => o.label)
        .join(', ');
    }
    return `${value.length} selected`;
  };

  return (
    <div className={cn('w-full', className)} ref={containerRef}>
      {label && (
        <label
          className="block text-sm font-medium mb-1"
          style={{ color: 'var(--text-secondary)' }}
        >
          {label}
        </label>
      )}
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            'w-full h-[38px] px-3 py-2 border rounded-md transition-colors text-left',
            'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'flex items-center justify-between'
          )}
          style={{
            backgroundColor: 'var(--input-bg)',
            borderColor: 'var(--input-border)',
            color: value.length > 0 ? 'var(--text-primary)' : 'var(--text-muted)',
          }}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
        >
          <span className="truncate text-sm">{getDisplayText()}</span>
          <svg
            className={cn(
              'w-4 h-4 ml-2 flex-shrink-0 transition-transform',
              isOpen && 'transform rotate-180'
            )}
            style={{ color: 'var(--text-muted)' }}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>

        {isOpen && (
          <div
            className="absolute z-50 w-full mt-1 border rounded-md shadow-lg"
            style={{
              backgroundColor: 'var(--card-bg)',
              borderColor: 'var(--border)',
            }}
          >
            {/* Select All option */}
            <div
              className="px-3 py-2 border-b"
              style={{ borderColor: 'var(--border)' }}
            >
              <label className="flex items-center cursor-pointer group">
                <input
                  type="checkbox"
                  checked={value.length === options.length}
                  ref={(el) => {
                    if (el) {
                      el.indeterminate = value.length > 0 && value.length < options.length;
                    }
                  }}
                  onChange={handleSelectAll}
                  className="h-4 w-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
                  style={{ borderColor: 'var(--input-border)' }}
                />
                <span
                  className="ml-2 text-sm font-medium"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  {value.length === options.length ? 'Deselect All' : 'Select All'}
                </span>
              </label>
            </div>

            {/* Options list */}
            <div
              className="overflow-y-auto"
              style={{ maxHeight: `${maxHeight}px` }}
              role="listbox"
              aria-multiselectable="true"
            >
              {options.map((option) => {
                const isSelected = value.includes(option.value);
                return (
                  <label
                    key={String(option.value)}
                    className={cn(
                      'flex items-center px-3 py-2 cursor-pointer transition-colors',
                      'hover:bg-blue-50 dark:hover:bg-blue-900/20'
                    )}
                    style={{
                      backgroundColor: isSelected ? 'var(--hover-bg, rgba(59, 130, 246, 0.1))' : undefined,
                    }}
                    role="option"
                    aria-selected={isSelected}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleToggle(option.value)}
                      className="h-4 w-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
                      style={{ borderColor: 'var(--input-border)' }}
                    />
                    <span
                      className="ml-2 text-sm"
                      style={{ color: 'var(--text-secondary)' }}
                    >
                      {option.label}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>
        )}
      </div>
      {helpText && (
        <p className="mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
          {helpText}
        </p>
      )}
    </div>
  );
}
