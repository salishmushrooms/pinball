'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Team } from '@/lib/types';
import {
  Card,
  PageHeader,
  Select,
  Alert,
  LoadingSpinner,
  EmptyState,
} from '@/components/ui';

/**
 * Refactored Teams Page using the new UI component library
 *
 * This demonstrates:
 * - Consistent component usage
 * - Clean, readable JSX
 * - Proper separation of concerns
 * - Design system adherence
 *
 * Compare this to the original page.tsx to see the improvements
 */
export default function TeamsPageRefactored() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seasonFilter, setSeasonFilter] = useState<number | undefined>(22);

  useEffect(() => {
    fetchTeams();
  }, [seasonFilter]);

  async function fetchTeams() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getTeams({
        season: seasonFilter,
        limit: 500,
      });
      setTeams(data.teams);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch teams');
    } finally {
      setLoading(false);
    }
  }

  // Loading state
  if (loading) {
    return <LoadingSpinner fullPage text="Loading teams..." />;
  }

  // Error state
  if (error) {
    return <Alert variant="error" title="Error">{error}</Alert>;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Teams"
        description="Browse all teams and view their machine statistics"
      />

      {/* Filters Card */}
      <Card>
        <Card.Content>
          <Select
            label="Season"
            value={seasonFilter || ''}
            onChange={(e) => setSeasonFilter(e.target.value ? parseInt(e.target.value) : undefined)}
            className="md:w-64"
            options={[
              { value: '', label: 'All Seasons' },
              { value: 22, label: 'Season 22' },
              { value: 21, label: 'Season 21' },
            ]}
          />
        </Card.Content>
      </Card>

      {/* Empty State */}
      {teams.length === 0 ? (
        <Card>
          <Card.Content>
            <EmptyState
              title="No teams found"
              description="No teams found for the selected season."
            />
          </Card.Content>
        </Card>
      ) : (
        <>
          {/* Teams Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {teams.map((team) => (
              <Card
                key={`${team.team_key}-${team.season}`}
                variant="interactive"
                href={`/teams/${team.team_key}?season=${team.season}`}
              >
                <Card.Content>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {team.team_name}
                  </h3>
                  <dl className="space-y-1 text-sm text-gray-600">
                    <div>
                      <dt className="inline font-medium">Team Key:</dt>{' '}
                      <dd className="inline">{team.team_key}</dd>
                    </div>
                    <div>
                      <dt className="inline font-medium">Season:</dt>{' '}
                      <dd className="inline">{team.season}</dd>
                    </div>
                    {team.home_venue_key && (
                      <div>
                        <dt className="inline font-medium">Home Venue:</dt>{' '}
                        <dd className="inline">{team.home_venue_key}</dd>
                      </div>
                    )}
                  </dl>
                </Card.Content>
              </Card>
            ))}
          </div>

          {/* Results Count */}
          <div className="text-center text-sm text-gray-600">
            Showing {teams.length} team{teams.length !== 1 ? 's' : ''}
          </div>
        </>
      )}
    </div>
  );
}
