import React from 'react';
import { MultiSelectDropdown } from './ui/MultiSelectDropdown';

interface MachineOption {
  machine_key: string;
  machine_name: string;
}

interface MachineMultiSelectProps {
  value: string[];
  onChange: (value: string[]) => void;
  machines: MachineOption[];
  label?: string;
  helpText?: string;
  className?: string;
  placeholder?: string;
  disabled?: boolean;
}

/**
 * Reusable machine multi-select component using dropdown UI.
 * Use this for filtering data by one or more machines.
 * Machines are sorted alphabetically by name.
 */
export const MachineMultiSelect: React.FC<MachineMultiSelectProps> = ({
  value,
  onChange,
  machines,
  label = 'Machines',
  helpText,
  className,
  placeholder = 'All Machines',
  disabled = false,
}) => {
  // Sort machines alphabetically by name
  const sortedMachines = [...machines].sort((a, b) =>
    a.machine_name.localeCompare(b.machine_name)
  );
  const options = sortedMachines.map((machine) => ({
    value: machine.machine_key,
    label: machine.machine_name,
  }));

  return (
    <MultiSelectDropdown
      label={label}
      options={options}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      helpText={helpText}
      className={className}
      disabled={disabled}
    />
  );
};
