import React from 'react';
import { MultiSelectButtons } from './ui/MultiSelect';
import { MultiSelectDropdown } from './ui/MultiSelectDropdown';

interface RoundMultiSelectProps {
  value: number[];
  onChange: (value: number[]) => void;
  label?: string;
  helpText?: string;
  className?: string;
  /** Use dropdown style instead of button grid (default: 'buttons') */
  variant?: 'buttons' | 'dropdown';
}

/**
 * Reusable round multi-select component.
 * Use this for filtering data by one or more rounds (1-4).
 *
 * MNP Rounds:
 * - Round 1: Doubles (4 players)
 * - Round 2: Singles (2 players)
 * - Round 3: Singles (2 players)
 * - Round 4: Doubles (4 players)
 *
 * @param variant - 'buttons' shows all options as toggleable buttons (default),
 *                  'dropdown' shows a compact dropdown with checkboxes
 */
export const RoundMultiSelect: React.FC<RoundMultiSelectProps> = ({
  value,
  onChange,
  label = 'Rounds',
  helpText,
  className,
  variant = 'buttons',
}) => {
  const options = [
    { value: 1, label: 'Round 1' },
    { value: 2, label: 'Round 2' },
    { value: 3, label: 'Round 3' },
    { value: 4, label: 'Round 4' },
  ];

  if (variant === 'dropdown') {
    return (
      <MultiSelectDropdown
        label={label}
        options={options}
        value={value}
        onChange={onChange}
        placeholder="All Rounds"
        helpText={helpText}
        className={className}
      />
    );
  }

  // Button variant - use shorter labels
  const buttonOptions = [
    { value: 1, label: '1' },
    { value: 2, label: '2' },
    { value: 3, label: '3' },
    { value: 4, label: '4' },
  ];

  return (
    <MultiSelectButtons
      label={label}
      options={buttonOptions}
      value={value}
      onChange={onChange}
      helpText={helpText || 'Select one or more rounds'}
      className={className}
    />
  );
};
