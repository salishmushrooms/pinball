'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Team } from '@/lib/types';
import {
  Card,
  PageHeader,
  Alert,
  LoadingSpinner,
  EmptyState,
} from '@/components/ui';

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTeams();
  }, []);

  async function fetchTeams() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getTeams({
        limit: 500, // API maximum limit
      });

      // Find the most recent season
      const maxSeason = Math.max(...data.teams.map(t => t.season));

      // Filter to only teams from the most recent season, sorted by name
      const currentSeasonTeams = data.teams
        .filter(team => team.season === maxSeason)
        .sort((a, b) => a.team_name.localeCompare(b.team_name));

      setTeams(currentSeasonTeams);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch teams');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <LoadingSpinner fullPage text="Loading teams..." />;
  }

  if (error) {
    return <Alert variant="error" title="Error">{error}</Alert>;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Teams"
        description="Browse all teams and view their machine statistics"
      />

      {teams.length === 0 ? (
        <Card>
          <Card.Content>
            <EmptyState
              title="No teams found"
              description="No teams found for the current season."
            />
          </Card.Content>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {teams.map((team) => (
              <Card
                key={`${team.team_key}-${team.season}`}
                variant="interactive"
                href={`/teams/${team.team_key}?season=${team.season}`}
              >
                <Card.Content>
                  <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                    {team.team_name}
                  </h3>
                  <div className="space-y-1">
                    {team.home_venue_name && (
                      <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                        <span className="font-medium">Venue:</span> {team.home_venue_name}
                      </p>
                    )}
                    {team.team_ipr !== null && (
                      <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                        <span className="font-medium">Team IPR:</span> {team.team_ipr}
                      </p>
                    )}
                  </div>
                </Card.Content>
              </Card>
            ))}
          </div>

          <div className="text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
            Showing {teams.length} team{teams.length !== 1 ? 's' : ''} (Season {teams[0]?.season})
          </div>
        </>
      )}
    </div>
  );
}
