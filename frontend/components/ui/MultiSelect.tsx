import React from 'react';

export interface MultiSelectOption<T = string | number> {
  value: T;
  label: string;
}

export interface MultiSelectProps<T = string | number> {
  label?: string;
  options: MultiSelectOption<T>[];
  value: T[];
  onChange: (value: T[]) => void;
  helpText?: string;
  className?: string;
}

export function MultiSelect<T extends string | number = string | number>({
  label,
  options,
  value,
  onChange,
  helpText,
  className = '',
}: MultiSelectProps<T>) {
  const handleToggle = (optionValue: T) => {
    if (value.includes(optionValue)) {
      onChange(value.filter((v) => v !== optionValue));
    } else {
      onChange([...value, optionValue]);
    }
  };

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>
          {label}
        </label>
      )}
      {helpText && (
        <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>{helpText}</p>
      )}
      <div className="space-y-2">
        {options.map((option) => {
          const isSelected = value.includes(option.value);
          return (
            <label
              key={String(option.value)}
              className="flex items-center cursor-pointer group"
            >
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => handleToggle(option.value)}
                className="h-4 w-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
                style={{ borderColor: 'var(--input-border)' }}
              />
              <span className="ml-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                {option.label}
              </span>
            </label>
          );
        })}
      </div>
    </div>
  );
}

// Compact horizontal variant (like the original button style)
export interface MultiSelectButtonsProps<T = string | number> {
  label?: string;
  options: MultiSelectOption<T>[];
  value: T[];
  onChange: (value: T[]) => void;
  helpText?: string;
  className?: string;
}

export function MultiSelectButtons<T extends string | number = string | number>({
  label,
  options,
  value,
  onChange,
  helpText,
  className = '',
}: MultiSelectButtonsProps<T>) {
  const handleToggle = (optionValue: T) => {
    if (value.includes(optionValue)) {
      onChange(value.filter((v) => v !== optionValue));
    } else {
      onChange([...value, optionValue]);
    }
  };

  return (
    <div className={className}>
      {label && (
        <label className="block text-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>
          {label}
        </label>
      )}
      {helpText && (
        <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>{helpText}</p>
      )}
      <div className="flex gap-2 flex-wrap">
        {options.map((option) => {
          const isSelected = value.includes(option.value);
          return (
            <button
              key={String(option.value)}
              type="button"
              onClick={() => handleToggle(option.value)}
              className={`px-4 py-2 border rounded-md text-sm font-medium transition-colors ${
                isSelected
                  ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700'
                  : ''
              }`}
              style={
                isSelected
                  ? undefined
                  : { backgroundColor: 'var(--card-bg)', color: 'var(--text-secondary)', borderColor: 'var(--border)' }
              }
              aria-pressed={isSelected}
            >
              {isSelected && (
                <span className="mr-1.5" aria-hidden="true">✓</span>
              )}
              {option.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
