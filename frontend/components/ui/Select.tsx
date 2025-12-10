import React from 'react';
import { cn } from '@/lib/utils';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helpText?: string;
  options?: Array<{ value: string | number; label: string }>;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, helpText, options, className, id, children, ...props }, ref) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={selectId}
            className="block text-sm font-medium mb-1"
            style={{ color: 'var(--text-secondary)' }}
          >
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={cn(
            'w-full h-[38px] px-3 py-2 border rounded-md transition-colors text-sm',
            'focus:outline-none focus:ring-2',
            error
              ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
              : 'focus:ring-blue-500 focus:border-blue-500',
            'disabled:cursor-not-allowed',
            className
          )}
          style={{
            backgroundColor: 'var(--input-bg)',
            borderColor: error ? undefined : 'var(--input-border)',
            color: 'var(--text-primary)',
          }}
          {...props}
        >
          {options
            ? options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))
            : children}
        </select>
        {helpText && !error && (
          <p className="mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>{helpText}</p>
        )}
        {error && (
          <p className="mt-1 text-xs text-red-600">{error}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';
