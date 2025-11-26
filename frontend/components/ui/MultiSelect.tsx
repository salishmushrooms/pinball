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
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      {helpText && (
        <p className="text-xs text-gray-500 mb-2">{helpText}</p>
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
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
              />
              <span className="ml-2 text-sm text-gray-700 group-hover:text-gray-900">
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
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      {helpText && (
        <p className="text-xs text-gray-500 mb-2">{helpText}</p>
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
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
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
