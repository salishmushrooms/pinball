'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { VenueDetail, VenueMachineStats, Team } from '@/lib/types';
import {
  Card,
  PageHeader,
  Select,
  Alert,
  LoadingSpinner,
  EmptyState,
  Table,
  Badge,
  StatCard,
  FilterPanel,
  ContentContainer,
} from '@/components/ui';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';
import { TeamMultiSelect } from '@/components/TeamMultiSelect';
import { SUPPORTED_SEASONS, filterSupportedSeasons, formatScore } from '@/lib/utils';

export default function VenueDetailPage() {
  const params = useParams();
  const venueKey = params.venue_key as string;

  const [venue, setVenue] = useState<VenueDetail | null>(null);
  const [machines, setMachines] = useState<VenueMachineStats[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([...SUPPORTED_SEASONS]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [currentOnly, setCurrentOnly] = useState(true);
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);
  const [scoresFrom, setScoresFrom] = useState<'venue' | 'all'>('venue');
  const [sortBy, setSortBy] = useState<'name' | 'games'>('games');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [seasons, setSeasons] = useState<number[]>([]);

  // Fetch available seasons and teams on mount
  useEffect(() => {
    async function fetchInitialData() {
      try {
        const [seasonsData, teamsData] = await Promise.all([
          api.getSeasons(),
          api.getTeams({ limit: 500 }),
        ]);
        const supported = filterSupportedSeasons(seasonsData.seasons);
        setAvailableSeasons(supported);
        setTeams(teamsData.teams);
        // Default to all supported seasons
        setSeasons(supported);
      } catch (err) {
        console.error('Failed to fetch initial data:', err);
      }
    }
    fetchInitialData();
  }, []);

  // Fetch venue and machines when filters change
  useEffect(() => {
    async function fetchVenueData() {
      try {
        setLoading(true);
        const [venueData, machinesData] = await Promise.all([
          api.getVenue(venueKey),
          api.getVenueMachines(venueKey, {
            current_only: currentOnly,
            team_key: selectedTeams.length > 0 ? selectedTeams[0] : undefined,
            scores_from: scoresFrom,
            seasons: seasons.length > 0 ? seasons : undefined,
          }),
        ]);
        setVenue(venueData);
        setMachines(machinesData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch venue data');
      } finally {
        setLoading(false);
      }
    }

    fetchVenueData();
  }, [venueKey, currentOnly, selectedTeams, scoresFrom, seasons]);

  // Sort machines based on sortBy state and direction
  const sortedMachines = [...machines].sort((a, b) => {
    let comparison = 0;
    if (sortBy === 'games') {
      comparison = b.total_scores - a.total_scores;
    } else {
      comparison = a.machine_name.localeCompare(b.machine_name);
    }
    return sortDirection === 'asc' ? -comparison : comparison;
  });

  function handleSort(column: 'name' | 'games') {
    if (sortBy === column) {
      // Toggle direction if clicking the same column
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // New column: set appropriate default direction
      setSortBy(column);
      setSortDirection(column === 'games' ? 'desc' : 'asc');
    }
  }

  if (loading) {
    return <LoadingSpinner fullPage text="Loading venue details..." />;
  }

  if (error || !venue) {
    return (
      <Alert variant="error" title="Error">
        {error || 'Venue not found'}
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/venues"
          className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block"
        >
          ← Back to Venues
        </Link>
        <PageHeader
          title={venue.venue_name}
          description={
            <>
              {(venue.city || venue.state) && (
                <div className="text-lg text-gray-600">
                  {venue.city && venue.state
                    ? `${venue.city}, ${venue.state}`
                    : venue.city || venue.state}
                </div>
              )}
              {venue.address && (
                <div className="text-sm text-gray-500 mt-1">{venue.address}</div>
              )}
              {venue.home_teams && venue.home_teams.length > 0 && (
                <div className="mt-3 pt-3 border-t" style={{ borderColor: 'var(--border)' }}>
                  <div
                    className="text-xs font-medium mb-2 uppercase tracking-wide"
                    style={{ color: 'var(--text-muted)' }}
                  >
                    Home Team{venue.home_teams.length > 1 ? 's' : ''}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {venue.home_teams.map((team) => (
                      <Link
                        key={team.team_key}
                        href={`/teams/${team.team_key}`}
                        className="inline-flex items-center px-3 py-1 rounded text-sm font-medium transition-colors hover:bg-blue-100 hover:text-blue-700"
                        style={{
                          backgroundColor: 'var(--card-bg-secondary)',
                          color: 'var(--text-secondary)',
                        }}
                      >
                        {team.team_name}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </>
          }
        />
      </div>

      {/* Filter Controls */}
      <FilterPanel
        title="Filters"
        collapsible={true}
        defaultOpen={false}
        activeFilterCount={
          (seasons.length > 0 && seasons.length < availableSeasons.length ? 1 : 0) +
          (!currentOnly ? 1 : 0) +
          (selectedTeams.length > 0 ? 1 : 0)
        }
        showClearAll={true}
        onClearAll={() => {
          setSeasons(availableSeasons);
          setCurrentOnly(true);
          setSelectedTeams([]);
          setScoresFrom('venue');
        }}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <SeasonMultiSelect
              value={seasons}
              onChange={setSeasons}
              availableSeasons={availableSeasons}
              variant="dropdown"
            />

            <TeamMultiSelect
              teams={Array.from(new Map(teams.map((team) => [team.team_key, team])).values())}
              value={selectedTeams}
              onChange={setSelectedTeams}
              label="Team"
            />

            <div>
              <label
                className="block text-sm font-medium mb-1"
                style={{ color: 'var(--text-secondary)' }}
              >
                Machine Status
              </label>
              <Select
                value={currentOnly ? 'current' : 'all'}
                onChange={(e) => setCurrentOnly(e.target.value === 'current')}
                options={[
                  { value: 'current', label: 'Current Machines Only' },
                  { value: 'all', label: 'All Machines (Including Past)' },
                ]}
              />
            </div>
          </div>

          {/* View Mode Toggle - Only show when team is selected */}
          {selectedTeams.length > 0 && (
            <div
              className="border-t pt-4"
              style={{ borderColor: 'var(--border)' }}
            >
              <label
                className="block text-sm font-medium mb-3"
                style={{ color: 'var(--text-secondary)' }}
              >
                Statistics Source
              </label>
              <div className="flex flex-wrap gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    value="venue"
                    checked={scoresFrom === 'venue'}
                    onChange={(e) => setScoresFrom(e.target.value as 'venue')}
                    className="h-4 w-4 text-blue-600 focus:ring-2 focus:ring-blue-500"
                    style={{ borderColor: 'var(--input-border)' }}
                  />
                  <span className="text-sm" style={{ color: 'var(--text-primary)' }}>
                    Scores at this venue only
                  </span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    value="all"
                    checked={scoresFrom === 'all'}
                    onChange={(e) => setScoresFrom(e.target.value as 'all')}
                    className="h-4 w-4 text-blue-600 focus:ring-2 focus:ring-blue-500"
                    style={{ borderColor: 'var(--input-border)' }}
                  />
                  <span className="text-sm" style={{ color: 'var(--text-primary)' }}>
                    All scores on these machines (scouting mode)
                  </span>
                </label>
              </div>
            </div>
          )}
        </div>
      </FilterPanel>

      {/* Summary Statistics - moved above machines table */}
      {machines.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>Summary Statistics</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                label="Total Machines"
                value={machines.length}
              />
              <StatCard
                label={selectedTeams.length > 0 ? 'Total Games' : 'Total Scores'}
                value={machines.reduce((sum, m) => sum + m.total_scores, 0).toLocaleString()}
              />
              <StatCard
                label={selectedTeams.length > 0 ? 'Team Members' : 'Unique Players'}
                value={Math.max(...machines.map((m) => m.unique_players))}
              />
              <StatCard
                label={`Avg ${selectedTeams.length > 0 ? 'Games' : 'Scores'}/Machine`}
                value={Math.round(
                  machines.reduce((sum, m) => sum + m.total_scores, 0) /
                    machines.length
                ).toLocaleString()}
              />
            </div>
            {selectedTeams.length > 0 && scoresFrom === 'all' && (
              <Alert variant="info" title="Scouting Mode" className="mt-4">
                These statistics show {teams.find((t) => t.team_key === selectedTeams[0])?.team_name}'s
                total experience on machines currently at {venue.venue_name}, including games played at other venues.
              </Alert>
            )}
          </Card.Content>
        </Card>
      )}

      {/* Machines Table */}
      <ContentContainer size="lg">
        <Card>
          <Card.Header>
            <Card.Title>
              {currentOnly ? 'Current Machines' : 'All Machines'}
              {selectedTeams.length > 0 && (
                <span className="text-base font-normal ml-2" style={{ color: 'var(--text-muted)' }}>
                  - {teams.find((t) => t.team_key === selectedTeams[0])?.team_name} Stats
                </span>
              )}
            </Card.Title>
          </Card.Header>
          <Card.Content>
            {machines.length === 0 ? (
              <EmptyState
                title="No machines found"
                description={
                  <>
                    {currentOnly && (
                      <p className="text-sm mt-2">
                        Try selecting "All Machines" to see machines
                        that have been played at this venue in the past.
                      </p>
                    )}
                    {selectedTeams.length > 0 && (
                      <p className="text-sm mt-2">
                        This team may not have played any games {scoresFrom === 'venue' ? 'at this venue' : 'on these machines'}.
                      </p>
                    )}
                  </>
                }
              />
            ) : (
              <>
                {/* Mobile view - stacked cards */}
                <div className="sm:hidden space-y-3">
                  {sortedMachines.map((machine) => (
                    <div
                      key={machine.machine_key}
                      className="border rounded-lg p-3"
                      style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg-secondary)' }}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <Link
                          href={`/machines/${machine.machine_key}`}
                          className="font-medium text-blue-600 hover:text-blue-800"
                        >
                          {machine.machine_name}
                        </Link>
                        {!currentOnly && (
                          <Badge variant={machine.is_current ? 'success' : 'default'} className="text-xs">
                            {machine.is_current ? 'Current' : 'Past'}
                          </Badge>
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>
                            {selectedTeams.length > 0 ? 'Games: ' : 'Scores: '}
                          </span>
                          <span style={{ color: 'var(--text-primary)' }}>{machine.total_scores}</span>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Players: </span>
                          <span style={{ color: 'var(--text-primary)' }}>{machine.unique_players}</span>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Median: </span>
                          <span style={{ color: 'var(--text-primary)' }}>{formatScore(machine.median_score)}</span>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Max: </span>
                          <span className="text-green-600 font-medium">{formatScore(machine.max_score)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Desktop view - table */}
                <div className="hidden sm:block">
                  <Table>
                    <Table.Header>
                      <Table.Row hoverable={false}>
                        <Table.Head
                          sortable
                          onSort={() => handleSort('name')}
                          sortDirection={sortBy === 'name' ? sortDirection : null}
                        >
                          Machine
                        </Table.Head>
                        <Table.Head
                          className="text-right"
                          sortable
                          onSort={() => handleSort('games')}
                          sortDirection={sortBy === 'games' ? sortDirection : null}
                        >
                          {selectedTeams.length > 0 ? 'Games' : 'Scores'}
                        </Table.Head>
                        <Table.Head className="text-right">Players</Table.Head>
                        <Table.Head className="text-right">Median</Table.Head>
                        <Table.Head className="text-right">Max</Table.Head>
                        {!currentOnly && (
                          <Table.Head className="text-center">Status</Table.Head>
                        )}
                      </Table.Row>
                    </Table.Header>
                    <Table.Body>
                      {sortedMachines.map((machine) => (
                        <Table.Row key={machine.machine_key}>
                          <Table.Cell>
                            <Link
                              href={`/machines/${machine.machine_key}`}
                              className="text-blue-600 hover:text-blue-800 font-medium"
                            >
                              {machine.machine_name}
                            </Link>
                          </Table.Cell>
                          <Table.Cell className="text-right">
                            {machine.total_scores.toLocaleString()}
                          </Table.Cell>
                          <Table.Cell className="text-right text-gray-500">
                            {machine.unique_players}
                          </Table.Cell>
                          <Table.Cell className="text-right">
                            {formatScore(machine.median_score)}
                          </Table.Cell>
                          <Table.Cell className="text-right font-medium text-green-600">
                            {formatScore(machine.max_score)}
                          </Table.Cell>
                          {!currentOnly && (
                            <Table.Cell className="text-center">
                              <Badge variant={machine.is_current ? 'success' : 'default'}>
                                {machine.is_current ? 'Current' : 'Past'}
                              </Badge>
                            </Table.Cell>
                          )}
                        </Table.Row>
                      ))}
                    </Table.Body>
                  </Table>
                </div>
              </>
            )}
          </Card.Content>
        </Card>
      </ContentContainer>
    </div>
  );
}
