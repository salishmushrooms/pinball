'use client';

import { useState } from 'react';
import { useVenuesWithStats } from '@/lib/queries';
import { VenueWithStats } from '@/lib/types';
import {
  Card,
  PageHeader,
  Input,
  Alert,
  LoadingSpinner,
  EmptyState,
} from '@/components/ui';

export default function VenuesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [showInactive, setShowInactive] = useState(false);

  const { data, isLoading, error } = useVenuesWithStats({
    limit: 500,
    active_only: !showInactive
  });

  const venues = data?.venues ?? [];

  const filteredVenues = venues.filter((venue) =>
    venue.venue_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return <LoadingSpinner fullPage text="Loading venues..." />;
  }

  if (error) {
    return (
      <Alert variant="error" title="Error">
        {error instanceof Error ? error.message : 'Failed to fetch venues'}
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Venues"
        description="Browse all MNP venues and view their machine lineups"
      />

      <Card>
        <Card.Content>
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <div className="flex-1 w-full sm:w-auto">
              <Input
                type="text"
                placeholder="Search venues..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <label className="flex items-center gap-2 cursor-pointer whitespace-nowrap">
              <input
                type="checkbox"
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
                className="h-4 w-4 rounded focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
                style={{ borderColor: 'var(--input-border)' }}
              />
              <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                Show inactive venues
              </span>
            </label>
          </div>
        </Card.Content>
      </Card>

      {filteredVenues.length === 0 ? (
        <Card>
          <Card.Content>
            <EmptyState
              title="No venues found"
              description={searchTerm ? `No venues match "${searchTerm}"` : 'No venues available'}
            />
          </Card.Content>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredVenues.map((venue) => (
            <VenueCard key={venue.venue_key} venue={venue} />
          ))}
        </div>
      )}

      <div className="text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
        Showing {filteredVenues.length} of {venues.length} venue{venues.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
}

interface VenueCardProps {
  venue: VenueWithStats;
}

function VenueCard({ venue }: VenueCardProps) {
  return (
    <Card variant="interactive" href={`/venues/${venue.venue_key}`}>
      <Card.Content className="p-5">
        <div className="space-y-3">
          {/* Venue Name */}
          <h3
            className="text-lg font-semibold truncate"
            style={{ color: 'var(--text-primary)' }}
          >
            {venue.venue_name}
          </h3>

          {/* Stats Row */}
          <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
            {/* Machine Count */}
            <div className="flex items-center gap-1.5">
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                style={{ color: 'var(--text-muted)' }}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                />
              </svg>
              <span>
                {venue.machine_count > 0
                  ? `${venue.machine_count} machine${venue.machine_count !== 1 ? 's' : ''}`
                  : 'No machine data'}
              </span>
            </div>
          </div>

          {/* Home Teams */}
          {venue.home_teams.length > 0 && (
            <div className="pt-2 border-t" style={{ borderColor: 'var(--border)' }}>
              <div
                className="text-xs font-medium mb-1.5 uppercase tracking-wide"
                style={{ color: 'var(--text-muted)' }}
              >
                Home Team{venue.home_teams.length > 1 ? 's' : ''}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {venue.home_teams.map((team) => (
                  <span
                    key={team.team_key}
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                    style={{
                      backgroundColor: 'var(--card-bg-secondary)',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    {team.team_name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* No home teams indicator */}
          {venue.home_teams.length === 0 && (
            <div className="pt-2 border-t" style={{ borderColor: 'var(--border)' }}>
              <span
                className="text-xs italic"
                style={{ color: 'var(--text-muted)' }}
              >
                No home teams
              </span>
            </div>
          )}
        </div>
      </Card.Content>
    </Card>
  );
}
