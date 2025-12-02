import React from 'react';
import { MultiSelectButtons } from './ui/MultiSelect';

interface RoundMultiSelectProps {
  value: number[];
  onChange: (value: number[]) => void;
  label?: string;
  helpText?: string;
  className?: string;
}

/**
 * Reusable round multi-select component with button-style UI.
 * Use this for filtering data by one or more rounds (1-4).
 *
 * MNP Rounds:
 * - Round 1: Doubles (4 players)
 * - Round 2: Singles (2 players)
 * - Round 3: Singles (2 players)
 * - Round 4: Doubles (4 players)
 */
export const RoundMultiSelect: React.FC<RoundMultiSelectProps> = ({
  value,
  onChange,
  label = 'Rounds',
  helpText = 'Select one or more rounds',
  className,
}) => {
  const options = [
    { value: 1, label: '1' },
    { value: 2, label: '2' },
    { value: 3, label: '3' },
    { value: 4, label: '4' },
  ];

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
