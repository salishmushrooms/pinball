import React from 'react';
import { MultiSelectButtons } from './ui/MultiSelect';

interface SeasonMultiSelectProps {
  value: number[];
  onChange: (value: number[]) => void;
  availableSeasons?: number[];
  label?: string;
  helpText?: string;
  className?: string;
}

/**
 * Reusable season multi-select component with button-style UI.
 * Use this for filtering data by one or more seasons.
 */
export const SeasonMultiSelect: React.FC<SeasonMultiSelectProps> = ({
  value,
  onChange,
  availableSeasons = [21, 22],
  label = 'Seasons',
  helpText = 'Select one or more seasons',
  className,
}) => {
  const options = availableSeasons.map((season) => ({
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
