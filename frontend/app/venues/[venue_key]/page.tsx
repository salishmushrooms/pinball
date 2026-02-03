'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { VenueDetail, VenueMachineStats, Team, PinballMapVenueMachines } from '@/lib/types';
import {
  Card,
  PageHeader,
  Select,
  Alert,
  LoadingSpinner,
  EmptyState,
  Table,
  Badge,
  TopMachinesList,
  FilterPanel,
  ContentContainer,
  Breadcrumb,
} from '@/components/ui';
import type { FilterChipData } from '@/components/ui/FilterChip';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';
import { TeamMultiSelect } from '@/components/TeamMultiSelect';
import { SUPPORTED_SEASONS, filterSupportedSeasons, formatScore } from '@/lib/utils';
import { useURLFilters, filterConfigs } from '@/lib/hooks';

export default function VenueDetailPage() {
  const params = useParams();
  const venueKey = params.venue_key as string;

  // URL-synced filters
  // Note: seasons default is set dynamically after fetching availableSeasons
  const { filters, getSeasonChips } = useURLFilters({
    seasons: filterConfigs.seasons(SUPPORTED_SEASONS as unknown as number[]),
    teams: filterConfigs.teams(),
    currentOnly: filterConfigs.boolean('currentOnly', true),
    scoresFrom: filterConfigs.string('scoresFrom', 'venue'),
  });

  const seasons = filters.seasons.value;
  const setSeasons = filters.seasons.setValue;
  const selectedTeams = filters.teams.value;
  const setSelectedTeams = filters.teams.setValue;
  const currentOnly = filters.currentOnly.value;
  const setCurrentOnly = filters.currentOnly.setValue;
  const scoresFrom = filters.scoresFrom.value as 'venue' | 'all';
  const setScoresFrom = (v: 'venue' | 'all') => filters.scoresFrom.setValue(v);

  const [venue, setVenue] = useState<VenueDetail | null>(null);
  const [machines, setMachines] = useState<VenueMachineStats[]>([]);
  const [topMachines, setTopMachines] = useState<VenueMachineStats[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([...SUPPORTED_SEASONS]);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pinball Map integration
  const [pinballMapData, setPinballMapData] = useState<PinballMapVenueMachines | null>(null);
  const [pinballMapLoading, setPinballMapLoading] = useState(false);
  const [pinballMapError, setPinballMapError] = useState<string | null>(null);

  // Sort state (not URL-synced)
  const [sortBy, setSortBy] = useState<'name' | 'games'>('games');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Fetch available seasons, teams, and top machines on mount
  useEffect(() => {
    async function fetchInitialData() {
      try {
        const [seasonsData, teamsData, topMachinesData] = await Promise.all([
          api.getSeasons(),
          api.getTeams({ limit: 500 }),
          api.getVenueMachines(venueKey, {
            current_only: true,
            seasons: [22, 23],
          }),
        ]);
        const supported = filterSupportedSeasons(seasonsData.seasons);
        setAvailableSeasons(supported);
        setTeams(teamsData.teams);
        // If seasons haven't been set from URL, default to all supported seasons
        if (filters.seasons.isDefault) {
          setSeasons(supported);
        }
        // Top 3 machines by score count
        const sorted = [...topMachinesData].sort((a, b) => b.total_scores - a.total_scores);
        setTopMachines(sorted.slice(0, 3));
      } catch (err) {
        console.error('Failed to fetch initial data:', err);
      }
    }
    fetchInitialData();
  }, [venueKey]);

  // Fetch venue and machines when filters change
  useEffect(() => {
    async function fetchVenueData() {
      try {
        // Only set loading true on initial load (when venue is null)
        // Use fetching for subsequent filter changes to avoid unmounting FilterPanel
        if (!venue) {
          setLoading(true);
        } else {
          setFetching(true);
        }
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
        setFetching(false);
      }
    }

    fetchVenueData();
  }, [venueKey, currentOnly, selectedTeams, scoresFrom, seasons]);

  // Fetch Pinball Map data when venue is loaded and has a pinballmap_location_id
  useEffect(() => {
    async function fetchPinballMapData() {
      if (!venue?.pinballmap_location_id) {
        setPinballMapData(null);
        return;
      }

      setPinballMapLoading(true);
      setPinballMapError(null);

      try {
        const data = await api.getVenuePinballMapMachines(venueKey);
        setPinballMapData(data);
      } catch (err) {
        setPinballMapError(
          err instanceof Error ? err.message : 'Failed to load Pinball Map data'
        );
      } finally {
        setPinballMapLoading(false);
      }
    }

    fetchPinballMapData();
  }, [venue?.pinballmap_location_id, venueKey]);

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

  // Build active filters array for chips display
  const activeFilters: FilterChipData[] = [
    // Individual season chips
    ...getSeasonChips(seasons, availableSeasons.length),
  ];

  // Individual team chips
  if (selectedTeams.length > 0) {
    selectedTeams.forEach(teamKey => {
      const teamName = teams.find(t => t.team_key === teamKey)?.team_name || teamKey;
      activeFilters.push({
        key: `team-${teamKey}`,
        label: 'Team',
        value: teamName,
        onRemove: () => {
          const remaining = selectedTeams.filter(t => t !== teamKey);
          setSelectedTeams(remaining);
          if (remaining.length === 0) {
            setScoresFrom('venue');
          }
        },
      });
    });
  }

  if (!currentOnly) {
    activeFilters.push({
      key: 'status',
      label: 'Status',
      value: 'All Machines',
      onRemove: () => setCurrentOnly(true),
    });
  }

  // Helper to clear all filters
  const clearAllFilters = () => {
    setSeasons(availableSeasons);
    setCurrentOnly(true);
    setSelectedTeams([]);
    setScoresFrom('venue');
  };

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
        <Breadcrumb
          items={[
            { label: 'Venues', href: '/venues' },
            { label: venue.venue_name },
          ]}
        />
        <PageHeader
          title={venue.venue_name}
          description={
            <>
              {venue.neighborhood && (
                <div className="text-lg text-gray-600">
                  {venue.neighborhood}
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
        activeFilters={activeFilters}
        showClearAll={activeFilters.length > 1}
        onClearAll={clearAllFilters}
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

      {/* Top Machines */}
      {topMachines.length > 0 && (
        <TopMachinesList
          machines={topMachines}
          title="Most Played Machines"
          subtitle="Season 22-23 scores"
        />
      )}

      {/* Pinball Map Current Machines */}
      {venue.pinballmap_location_id && (
        <ContentContainer size="lg">
          <Card>
            <Card.Header>
              <div className="flex items-center justify-between">
                <div>
                  <Card.Title>Current Machine Lineup</Card.Title>
                  <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                    Live data from{' '}
                    <a
                      href={pinballMapData?.pinballmap_url || `https://pinballmap.com/map?by_location_id=${venue.pinballmap_location_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 hover:underline"
                    >
                      Pinball Map
                    </a>
                    {' '}(community-maintained)
                  </p>
                </div>
                {pinballMapData && (
                  <Badge variant="default">{pinballMapData.machine_count} machines</Badge>
                )}
              </div>
            </Card.Header>
            <Card.Content>
              {pinballMapLoading && (
                <div className="flex justify-center py-8">
                  <LoadingSpinner size="sm" text="Loading from Pinball Map..." />
                </div>
              )}
              {pinballMapError && (
                <Alert variant="warning" title="Could not load Pinball Map data">
                  {pinballMapError}
                </Alert>
              )}
              {pinballMapData && pinballMapData.machines.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {pinballMapData.machines.map((machine) => (
                    <div
                      key={machine.id}
                      className="flex items-center justify-between p-3 rounded-lg border"
                      style={{
                        borderColor: 'var(--border)',
                        backgroundColor: 'var(--card-bg-secondary)',
                      }}
                    >
                      <div className="min-w-0 flex-1">
                        <div
                          className="font-medium truncate"
                          style={{ color: 'var(--text-primary)' }}
                          title={machine.name}
                        >
                          {machine.name}
                        </div>
                        <div
                          className="text-xs truncate"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          {[machine.manufacturer, machine.year].filter(Boolean).join(' • ') || 'Unknown'}
                        </div>
                      </div>
                      {machine.ipdb_link && (
                        <a
                          href={machine.ipdb_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-2 text-xs text-blue-600 hover:text-blue-800 hover:underline flex-shrink-0"
                        >
                          IPDB
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {pinballMapData && pinballMapData.machines.length === 0 && (
                <EmptyState
                  title="No machines listed"
                  description="This venue doesn't have any machines listed on Pinball Map yet."
                />
              )}
            </Card.Content>
          </Card>
        </ContentContainer>
      )}

      {/* Machines Table */}
      <ContentContainer size="lg">
        <Card>
          <Card.Header>
            <div className="flex items-center justify-between">
              <Card.Title>
                {currentOnly ? 'Current Machines' : 'All Machines'}
                {selectedTeams.length > 0 && (
                  <span className="text-base font-normal ml-2" style={{ color: 'var(--text-muted)' }}>
                    - {teams.find((t) => t.team_key === selectedTeams[0])?.team_name} Stats
                  </span>
                )}
              </Card.Title>
              {fetching && <LoadingSpinner size="sm" text="Updating..." />}
            </div>
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
                          <span style={{ color: 'var(--text-primary)' }}>{formatScore(machine.max_score)}</span>
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
