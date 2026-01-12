'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { useTeams } from '@/lib/queries';
import {
  Card,
  PageHeader,
  Alert,
  LoadingSpinner,
  EmptyState,
  Table,
  ContentContainer,
  TeamLogo,
} from '@/components/ui';

type SortField = 'team_name' | 'team_ipr' | 'home_venue_name';
type SortDirection = 'asc' | 'desc';

export default function TeamsPage() {
  const [sortField, setSortField] = useState<SortField>('team_name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const { data, isLoading, error } = useTeams({ limit: 500 });

  // Filter to only teams from the most recent season
  const teams = useMemo(() => {
    if (!data?.teams?.length) return [];
    const maxSeason = Math.max(...data.teams.map(t => t.season));
    return data.teams.filter(team => team.season === maxSeason);
  }, [data]);

  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  }

  const sortedTeams = useMemo(() => {
    return [...teams].sort((a, b) => {
      let aValue: string | number | null;
      let bValue: string | number | null;

      switch (sortField) {
        case 'team_name':
          aValue = a.team_name;
          bValue = b.team_name;
          break;
        case 'team_ipr':
          aValue = a.team_ipr ?? -1;
          bValue = b.team_ipr ?? -1;
          break;
        case 'home_venue_name':
          aValue = a.home_venue_name ?? '';
          bValue = b.home_venue_name ?? '';
          break;
        default:
          return 0;
      }

      if (aValue === null || aValue === '') return 1;
      if (bValue === null || bValue === '') return -1;

      let comparison = 0;
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        comparison = aValue.localeCompare(bValue);
      } else {
        comparison = aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [teams, sortField, sortDirection]);

  if (isLoading) {
    return <LoadingSpinner fullPage text="Loading teams..." />;
  }

  if (error) {
    return <Alert variant="error" title="Error">{error instanceof Error ? error.message : 'Failed to fetch teams'}</Alert>;
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
        <ContentContainer>
          <Card>
            <Card.Content>
              <Table>
                <Table.Header>
                  <Table.Row hoverable={false}>
                    <Table.Head
                      sortable
                      onSort={() => handleSort('team_name')}
                      sortDirection={sortField === 'team_name' ? sortDirection : null}
                    >
                      Team
                    </Table.Head>
                    <Table.Head
                      sortable
                      onSort={() => handleSort('home_venue_name')}
                      sortDirection={sortField === 'home_venue_name' ? sortDirection : null}
                    >
                      Venue
                    </Table.Head>
                    <Table.Head
                      sortable
                      onSort={() => handleSort('team_ipr')}
                      sortDirection={sortField === 'team_ipr' ? sortDirection : null}
                    >
                      Team IPR
                    </Table.Head>
                  </Table.Row>
                </Table.Header>
                <Table.Body striped>
                  {sortedTeams.map((team) => (
                    <Table.Row key={`${team.team_key}-${team.season}`}>
                      <Table.Cell>
                        <div className="flex items-center gap-2">
                          <TeamLogo
                            teamKey={team.team_key}
                            teamName={team.team_name}
                            size="sm"
                          />
                          <Link
                            href={`/teams/${team.team_key}?season=${team.season}`}
                            className="font-medium hover:underline"
                            style={{ color: 'var(--link-color)' }}
                          >
                            {team.team_name}
                          </Link>
                        </div>
                      </Table.Cell>
                      <Table.Cell>
                        {team.home_venue_key && team.home_venue_name ? (
                          <Link
                            href={`/venues/${team.home_venue_key}`}
                            className="hover:underline"
                            style={{ color: 'var(--link-color)' }}
                          >
                            {team.home_venue_name}
                          </Link>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </Table.Cell>
                      <Table.Cell>
                        {team.team_ipr !== null ? (
                          team.team_ipr
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table>

              <div className="mt-4 text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
                Showing {teams.length} team{teams.length !== 1 ? 's' : ''} (Season {teams[0]?.season})
              </div>
            </Card.Content>
          </Card>
        </ContentContainer>
      )}
    </div>
  );
}
