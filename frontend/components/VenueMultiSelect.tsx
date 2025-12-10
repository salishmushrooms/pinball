import React from 'react';
import { MultiSelectDropdown } from './ui/MultiSelectDropdown';
import { Select } from './ui';
import { Venue } from '@/lib/types';

interface VenueMultiSelectProps {
  value: string[];
  onChange: (value: string[]) => void;
  venues: Venue[];
  label?: string;
  helpText?: string;
  className?: string;
}

interface VenueSelectProps {
  value: string;
  onChange: (value: string) => void;
  venues: Venue[];
  label?: string;
  helpText?: string;
  className?: string;
  /** Include "All Venues" option (default: true) */
  includeAllOption?: boolean;
}

/**
 * Reusable venue multi-select component using dropdown UI.
 * Use this for filtering data by one or more venues.
 * Venues are sorted alphabetically by name.
 */
export const VenueMultiSelect: React.FC<VenueMultiSelectProps> = ({
  value,
  onChange,
  venues,
  label = 'Venues',
  helpText,
  className,
}) => {
  // Sort venues alphabetically by name
  const sortedVenues = [...venues].sort((a, b) =>
    a.venue_name.localeCompare(b.venue_name)
  );
  const options = sortedVenues.map((venue) => ({
    value: venue.venue_key,
    label: venue.venue_name,
  }));

  return (
    <MultiSelectDropdown
      label={label}
      options={options}
      value={value}
      onChange={onChange}
      placeholder="All Venues"
      helpText={helpText}
      className={className}
    />
  );
};

/**
 * Reusable venue single-select component using dropdown UI.
 * Use this when only one venue can be selected at a time.
 * Venues are sorted alphabetically by name.
 */
export const VenueSelect: React.FC<VenueSelectProps> = ({
  value,
  onChange,
  venues,
  label = 'Venue',
  helpText,
  className,
  includeAllOption = true,
}) => {
  // Sort venues alphabetically by name
  const sortedVenues = [...venues].sort((a, b) =>
    a.venue_name.localeCompare(b.venue_name)
  );

  const options = [
    ...(includeAllOption ? [{ value: '', label: 'All Venues' }] : []),
    ...sortedVenues.map((venue) => ({
      value: venue.venue_key,
      label: venue.venue_name,
    })),
  ];

  return (
    <Select
      label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      options={options}
      helpText={helpText}
      className={className}
    />
  );
};
