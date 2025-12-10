'use client';

import { useEffect, useState, useMemo } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Team, TeamMachineStat, TeamPlayer, Venue, MatchplayRatingInfo } from '@/lib/types';
import { RoundMultiSelect } from '@/components/RoundMultiSelect';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';
import { VenueSelect } from '@/components/VenueMultiSelect';
import { useDebouncedEffect } from '@/lib/hooks';
import { Table, Card, PageHeader, FilterPanel, Alert, LoadingSpinner } from '@/components/ui';
import { SUPPORTED_SEASONS, filterSupportedSeasons } from '@/lib/utils';

export default function TeamDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const teamKey = params.team_key as string;
  const initialSeason = searchParams.get('season');

  const [team, setTeam] = useState<Team | null>(null);
  const [machineStats, setMachineStats] = useState<TeamMachineStat[]>([]);
  const [players, setPlayers] = useState<TeamPlayer[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([]);
  const [matchplayRatings, setMatchplayRatings] = useState<Record<string, MatchplayRatingInfo>>({});
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters for Machine Stats
  // Note: 'machine_name' is client-side only; API supports: games_played, avg_score, best_score, win_percentage, median_score
  const [sortBy, setSortBy] = useState<'games_played' | 'avg_score' | 'best_score' | 'win_percentage' | 'median_score' | 'machine_name'>('games_played');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [seasonsFilter, setSeasonsFilter] = useState<number[]>(
    initialSeason ? [parseInt(initialSeason)] : [22]
  );
  const [venueFilter, setVenueFilter] = useState<string>('');
  const [roundsFilter, setRoundsFilter] = useState<number[]>([1, 2, 3, 4]);
  const [excludeSubs, setExcludeSubs] = useState<boolean>(true);

  // Sorting for Team Roster (client-side)
  const [rosterSortBy, setRosterSortBy] = useState<'player_name' | 'current_ipr' | 'games_played' | 'win_percentage'>('games_played');
  const [rosterSortDirection, setRosterSortDirection] = useState<'asc' | 'desc'>('desc');

  useEffect(() => {
    fetchVenues();
    fetchSeasons();
  }, []);

  async function fetchSeasons() {
    try {
      const seasonsData = await api.getSeasons();
      setAvailableSeasons(filterSupportedSeasons(seasonsData.seasons));
    } catch (err) {
      console.error('Failed to fetch seasons:', err);
      // Fallback to supported seasons if API fails (SeasonMultiSelect sorts internally)
      setAvailableSeasons([...SUPPORTED_SEASONS]);
    }
  }

  // Debounced effect for filter changes (waits 500ms after last change)
  useDebouncedEffect(() => {
    if (!teamKey) return;

    setFetching(true);
    fetchTeamData();
  }, 500, [teamKey, sortBy, sortDirection, seasonsFilter, venueFilter, roundsFilter, excludeSubs]);

  async function fetchVenues() {
    try {
      const venuesData = await api.getVenues({ limit: 500 });
      setVenues(venuesData.venues);
    } catch (err) {
      console.error('Failed to fetch venues:', err);
    }
  }

  async function fetchTeamData() {
    // Only set loading true on initial load, use fetching for subsequent updates
    if (!team) {
      setLoading(true);
    }
    setError(null);
    try {
      const roundsParam = roundsFilter.length > 0 ? roundsFilter.join(',') : undefined;

      // API doesn't support machine_name sorting - handle client-side
      const apiSortBy = sortBy === 'machine_name' ? 'games_played' : sortBy;

      const [teamData, statsData, playersData] = await Promise.all([
        api.getTeam(teamKey, seasonsFilter.length === 1 ? seasonsFilter[0] : undefined),
        api.getTeamMachineStats(teamKey, {
          seasons: seasonsFilter,
          venue_key: venueFilter || undefined,
          rounds: roundsParam,
          exclude_subs: excludeSubs,
          min_games: 1,
          sort_by: apiSortBy,
          sort_order: sortBy === 'machine_name' ? sortDirection : sortDirection,
          limit: 100,
        }),
        api.getTeamPlayers(teamKey, seasonsFilter, venueFilter || undefined, excludeSubs),
      ]);

      setTeam(teamData);

      // Client-side sorting for machine_name
      let sortedStats = statsData.stats;
      if (sortBy === 'machine_name') {
        sortedStats = [...statsData.stats].sort((a, b) => {
          const nameA = a.machine_name || '';
          const nameB = b.machine_name || '';
          const comparison = nameA.localeCompare(nameB);
          return sortDirection === 'asc' ? comparison : -comparison;
        });
      }
      setMachineStats(sortedStats);
      setPlayers(playersData.players);

      // Fetch Matchplay ratings for all players in roster
      if (playersData.players.length > 0) {
        try {
          const playerKeys = playersData.players.map((p) => p.player_key);
          const ratingsResponse = await api.getMatchplayRatings(playerKeys);
          setMatchplayRatings(ratingsResponse.ratings || {});
        } catch (ratingsErr) {
          // Non-fatal - just log and continue without ratings
          console.warn('Failed to fetch Matchplay ratings:', ratingsErr);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch team data');
    } finally {
      setLoading(false);
      setFetching(false);
    }
  }

  function handleSort(column: 'games_played' | 'avg_score' | 'best_score' | 'win_percentage' | 'median_score' | 'machine_name') {
    if (sortBy === column) {
      // Toggle direction if clicking the same column
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // New column: default to ascending for machine_name (A-Z), descending for others
      setSortBy(column);
      setSortDirection(column === 'machine_name' ? 'asc' : 'desc');
    }
  }

  function handleRosterSort(column: 'player_name' | 'current_ipr' | 'games_played' | 'win_percentage') {
    if (rosterSortBy === column) {
      setRosterSortDirection(rosterSortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Default: descending for numeric columns, ascending for name
      setRosterSortBy(column);
      setRosterSortDirection(column === 'player_name' ? 'asc' : 'desc');
    }
  }

  // Client-side sorted players
  const sortedPlayers = useMemo(() => {
    return [...players].sort((a, b) => {
      let aVal: string | number | null;
      let bVal: string | number | null;

      switch (rosterSortBy) {
        case 'player_name':
          aVal = a.player_name.toLowerCase();
          bVal = b.player_name.toLowerCase();
          break;
        case 'current_ipr':
          aVal = a.current_ipr ?? 0;
          bVal = b.current_ipr ?? 0;
          break;
        case 'games_played':
          aVal = a.games_played;
          bVal = b.games_played;
          break;
        case 'win_percentage':
          aVal = a.win_percentage ?? -1;
          bVal = b.win_percentage ?? -1;
          break;
        default:
          return 0;
      }

      if (aVal < bVal) return rosterSortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return rosterSortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [players, rosterSortBy, rosterSortDirection]);

  // Count active filters
  const activeFilterCount =
    (seasonsFilter.length > 0 && seasonsFilter.length < availableSeasons.length ? 1 : 0) +
    (venueFilter ? 1 : 0) +
    (roundsFilter.length > 0 && roundsFilter.length < 4 ? 1 : 0) +
    (excludeSubs ? 0 : 1); // excludeSubs is default on, so only count when off

  function clearFilters() {
    setSeasonsFilter([22]);
    setVenueFilter('');
    setRoundsFilter([1, 2, 3, 4]);
    setExcludeSubs(true);
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <LoadingSpinner size="lg" text="Loading team data..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="error" title="Error">
        {error}
      </Alert>
    );
  }

  if (!team) {
    return (
      <Alert variant="warning" title="Not Found">
        Team not found
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/teams"
          className="text-sm mb-2 inline-block"
          style={{ color: 'var(--text-link)' }}
        >
          ← Back to Teams
        </Link>
        <PageHeader
          title={team.team_name}
          description={`Season ${team.season}${team.home_venue_key ? ` • Home Venue: ${team.home_venue_key}` : ''}`}
        />
      </div>

      {/* Filters */}
      <FilterPanel
        title="Filters"
        collapsible={true}
        activeFilterCount={activeFilterCount}
        showClearAll={activeFilterCount > 0}
        onClearAll={clearFilters}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <SeasonMultiSelect
              value={seasonsFilter}
              onChange={setSeasonsFilter}
              availableSeasons={availableSeasons}
              variant="dropdown"
            />

            <VenueSelect
              value={venueFilter}
              onChange={setVenueFilter}
              venues={venues}
              label="Venue"
            />

            <RoundMultiSelect
              value={roundsFilter}
              onChange={setRoundsFilter}
              variant="dropdown"
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="exclude-subs"
              checked={excludeSubs}
              onChange={(e) => setExcludeSubs(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 rounded"
              style={{ borderColor: 'var(--input-border)' }}
            />
            <label
              htmlFor="exclude-subs"
              className="ml-2 text-sm"
              style={{ color: 'var(--text-secondary)' }}
            >
              Exclude substitute players (roster only)
            </label>
          </div>
        </div>
      </FilterPanel>

      {/* Machine Statistics Section */}
      <Card>
        <Card.Content>
          <div className="flex items-center justify-between mb-4">
            <h2
              className="text-xl font-semibold"
              style={{ color: 'var(--text-primary)' }}
            >
              Machine Statistics
            </h2>
            {fetching && (
              <LoadingSpinner size="sm" text="Updating..." />
            )}
          </div>

          {/* Machine Stats Table */}
          {machineStats.length === 0 ? (
            <Alert variant="warning">
              No machine statistics found for the selected filters.
            </Alert>
          ) : (
            <Table>
              <Table.Header>
                <Table.Row hoverable={false}>
                  <Table.Head
                    sortable
                    onSort={() => handleSort('machine_name')}
                    sortDirection={sortBy === 'machine_name' ? sortDirection : null}
                  >
                    Machine
                  </Table.Head>
                  <Table.Head
                    sortable
                    onSort={() => handleSort('games_played')}
                    sortDirection={sortBy === 'games_played' ? sortDirection : null}
                  >
                    Games
                  </Table.Head>
                  <Table.Head
                    sortable
                    onSort={() => handleSort('win_percentage')}
                    sortDirection={sortBy === 'win_percentage' ? sortDirection : null}
                  >
                    Win %
                  </Table.Head>
                  <Table.Head
                    sortable
                    onSort={() => handleSort('median_score')}
                    sortDirection={sortBy === 'median_score' ? sortDirection : null}
                  >
                    Median Score
                  </Table.Head>
                  <Table.Head
                    sortable
                    onSort={() => handleSort('best_score')}
                    sortDirection={sortBy === 'best_score' ? sortDirection : null}
                  >
                    Best Score
                  </Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {machineStats.map((stat, idx) => (
                  <Table.Row key={idx}>
                    <Table.Cell>
                      <Link
                        href={`/machines/${stat.machine_key}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-800"
                      >
                        {stat.machine_name}
                      </Link>
                    </Table.Cell>
                    <Table.Cell>{stat.games_played}</Table.Cell>
                    <Table.Cell>
                      {typeof stat.win_percentage === 'number' ? `${stat.win_percentage.toFixed(1)}%` : 'N/A'}
                    </Table.Cell>
                    <Table.Cell>
                      {stat.median_score?.toLocaleString(undefined, {
                        maximumFractionDigits: 0,
                      }) || 'N/A'}
                    </Table.Cell>
                    <Table.Cell>
                      {stat.best_score?.toLocaleString() || 'N/A'}
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>
          )}

          <div
            className="mt-4 text-sm"
            style={{ color: 'var(--text-muted)' }}
          >
            Showing {machineStats.length} machine{machineStats.length !== 1 ? 's' : ''}
          </div>
        </Card.Content>
      </Card>

      {/* Team Roster Section */}
      <Card>
        <Card.Content>
          <h2
            className="text-xl font-semibold mb-4"
            style={{ color: 'var(--text-primary)' }}
          >
            Team Roster
          </h2>

          {players.length === 0 ? (
            <Alert variant="warning">
              No players found for the selected filters.
            </Alert>
          ) : (
            <Table>
              <Table.Header>
                <Table.Row hoverable={false}>
                  <Table.Head
                    sortable
                    onSort={() => handleRosterSort('player_name')}
                    sortDirection={rosterSortBy === 'player_name' ? rosterSortDirection : null}
                  >
                    Player
                  </Table.Head>
                  <Table.Head
                    sortable
                    onSort={() => handleRosterSort('current_ipr')}
                    sortDirection={rosterSortBy === 'current_ipr' ? rosterSortDirection : null}
                  >
                    IPR
                  </Table.Head>
                  <Table.Head>MP Rating</Table.Head>
                  <Table.Head
                    sortable
                    onSort={() => handleRosterSort('games_played')}
                    sortDirection={rosterSortBy === 'games_played' ? rosterSortDirection : null}
                  >
                    Games
                  </Table.Head>
                  <Table.Head
                    sortable
                    onSort={() => handleRosterSort('win_percentage')}
                    sortDirection={rosterSortBy === 'win_percentage' ? rosterSortDirection : null}
                  >
                    Win %
                  </Table.Head>
                  <Table.Head>Most Played Machine</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {sortedPlayers.map((player) => {
                  const mpRating = matchplayRatings[player.player_key];
                  return (
                    <Table.Row key={player.player_key}>
                      <Table.Cell>
                        <Link
                          href={`/players/${player.player_key}`}
                          className="text-sm font-medium text-blue-600 hover:text-blue-800"
                        >
                          {player.player_name}
                        </Link>
                      </Table.Cell>
                      <Table.Cell>{player.current_ipr || 'N/A'}</Table.Cell>
                      <Table.Cell>
                        {mpRating ? (
                          <a
                            href={mpRating.profile_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800"
                            title={`Matchplay: ${mpRating.matchplay_name}`}
                          >
                            {mpRating.rating ?? '—'}
                          </a>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </Table.Cell>
                      <Table.Cell>{player.games_played}</Table.Cell>
                      <Table.Cell>
                        {player.win_percentage !== null ? `${player.win_percentage.toFixed(1)}%` : 'N/A'}
                      </Table.Cell>
                      <Table.Cell>
                        {player.most_played_machine_name ? (
                          <Link
                            href={`/machines/${player.most_played_machine_key}`}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            {player.most_played_machine_name} ({player.most_played_machine_games})
                          </Link>
                        ) : (
                          'N/A'
                        )}
                      </Table.Cell>
                    </Table.Row>
                  );
                })}
              </Table.Body>
            </Table>
          )}

          <div
            className="mt-4 text-sm"
            style={{ color: 'var(--text-muted)' }}
          >
            Showing {players.length} player{players.length !== 1 ? 's' : ''}
          </div>
        </Card.Content>
      </Card>
    </div>
  );
}
