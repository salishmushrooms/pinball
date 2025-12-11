import React from 'react';
import { MultiSelectDropdown } from './ui/MultiSelectDropdown';

interface TeamOption {
  team_key: string;
  team_name: string;
}

interface TeamMultiSelectProps {
  value: string[];
  onChange: (value: string[]) => void;
  teams: TeamOption[];
  label?: string;
  helpText?: string;
  className?: string;
}

/**
 * Reusable team multi-select component using dropdown UI.
 * Use this for filtering data by one or more teams.
 * Teams are sorted alphabetically by name.
 */
export const TeamMultiSelect: React.FC<TeamMultiSelectProps> = ({
  value,
  onChange,
  teams,
  label = 'Teams',
  helpText,
  className,
}) => {
  // Sort teams alphabetically by name
  const sortedTeams = [...teams].sort((a, b) =>
    a.team_name.localeCompare(b.team_name)
  );
  const options = sortedTeams.map((team) => ({
    value: team.team_key,
    label: team.team_name,
  }));

  return (
    <MultiSelectDropdown
      label={label}
      options={options}
      value={value}
      onChange={onChange}
      placeholder="All Teams"
      helpText={helpText}
      className={className}
    />
  );
};
