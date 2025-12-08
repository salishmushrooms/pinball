import React from 'react';
import { MultiSelectButtons } from './ui/MultiSelect';
import { Select } from './ui';
import { SUPPORTED_SEASONS } from '@/lib/utils';

interface SeasonMultiSelectProps {
  value: number[];
  onChange: (value: number[]) => void;
  availableSeasons?: number[];
  label?: string;
  helpText?: string;
  className?: string;
}

interface SeasonSelectProps {
  value: number;
  onChange: (value: number) => void;
  availableSeasons?: number[];
  label?: string;
  className?: string;
}

/**
 * Reusable season multi-select component with button-style UI.
 * Use this for filtering data by one or more seasons.
 * Seasons are always sorted ascending (oldest first) for consistency.
 */
export const SeasonMultiSelect: React.FC<SeasonMultiSelectProps> = ({
  value,
  onChange,
  availableSeasons = [...SUPPORTED_SEASONS],
  label = 'Seasons',
  helpText = 'Select one or more seasons',
  className,
}) => {
  // Sort seasons ascending (oldest first) for consistent display
  const sortedSeasons = [...availableSeasons].sort((a, b) => a - b);
  const options = sortedSeasons.map((season) => ({
    value: season,
    label: `${season}`,
  }));

  return (
    <MultiSelectButtons
      label={label}
      options={options}
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
