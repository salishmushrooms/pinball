import React from 'react';
import { MultiSelectButtons } from './ui/MultiSelect';
import { MultiSelectDropdown } from './ui/MultiSelectDropdown';
import { Select } from './ui';
import { SUPPORTED_SEASONS } from '@/lib/utils';

interface SeasonMultiSelectProps {
  value: number[];
  onChange: (value: number[]) => void;
  availableSeasons?: number[];
  label?: string;
  helpText?: string;
  className?: string;
  /** Use dropdown style instead of button grid (default: false) */
  variant?: 'buttons' | 'dropdown';
}

interface SeasonSelectProps {
  value: number;
  onChange: (value: number) => void;
  availableSeasons?: number[];
  label?: string;
  className?: string;
}

/**
 * Reusable season multi-select component.
 * Use this for filtering data by one or more seasons.
 * Seasons are always sorted ascending (oldest first) for consistency.
 *
 * @param variant - 'buttons' shows all options as toggleable buttons (default),
 *                  'dropdown' shows a compact dropdown with checkboxes
 */
export const SeasonMultiSelect: React.FC<SeasonMultiSelectProps> = ({
  value,
  onChange,
  availableSeasons = [...SUPPORTED_SEASONS],
  label = 'Seasons',
  helpText = 'Select one or more seasons',
  className,
  variant = 'buttons',
}) => {
  // Sort seasons ascending (oldest first) for consistent display
  const sortedSeasons = [...availableSeasons].sort((a, b) => a - b);
  const options = sortedSeasons.map((season) => ({
    value: season,
    label: `Season ${season}`,
  }));

  if (variant === 'dropdown') {
    return (
      <MultiSelectDropdown
        label={label}
        options={options}
        value={value}
        onChange={onChange}
        placeholder="All Seasons"
        helpText={helpText}
        className={className}
      />
    );
  }

  // Button variant - use shorter labels
  const buttonOptions = sortedSeasons.map((season) => ({
    value: season,
    label: `${season}`,
  }));

  return (
    <MultiSelectButtons
      label={label}
      options={buttonOptions}
      value={value}
      onChange={onChange}
      helpText={helpText}
      className={className}
    />
  );
};

/**
 * Reusable season single-select component using dropdown UI.
 * Use this when only one season can be selected at a time.
 * Seasons are always sorted ascending (oldest first) for consistency.
 */
export const SeasonSelect: React.FC<SeasonSelectProps> = ({
  value,
  onChange,
  availableSeasons = [...SUPPORTED_SEASONS],
  label = 'Season',
  className,
}) => {
  // Sort seasons ascending (oldest first) for consistent display
  const sortedSeasons = [...availableSeasons].sort((a, b) => a - b);
  const options = sortedSeasons.map((season) => ({
    value: season.toString(),
    label: `Season ${season}`,
  }));

  return (
    <Select
      label={label}
      value={value.toString()}
      onChange={(e) => onChange(parseInt(e.target.value))}
      options={options}
      className={className}
    />
  );
};
