'use client';

import { useEffect, useState, useMemo } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Team, TeamMachineStat, TeamPlayer, Venue, MatchplayRatingInfo } from '@/lib/types';
import { RoundMultiSelect } from '@/components/RoundMultiSelect';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';
import { useDebouncedEffect } from '@/lib/hooks';
import { Table } from '@/components/ui';
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
  const [sortBy, setSortBy] = useState<'games_played' | 'avg_score' | 'best_score' | 'win_percentage' | 'median_score' | 'machine_name'>('games_played');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [seasonsFilter, setSeasonsFilter] = useState<number[]>(
    initialSeason ? [parseInt(initialSeason)] : [22]
  );
  const [venueFilter, setVenueFilter] = useState<string | undefined>(undefined);
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

      const [teamData, statsData, playersData] = await Promise.all([
        api.getTeam(teamKey, seasonsFilter.length === 1 ? seasonsFilter[0] : undefined),
        api.getTeamMachineStats(teamKey, {
          seasons: seasonsFilter,
          venue_key: venueFilter,
          rounds: roundsParam,
          exclude_subs: excludeSubs,
          min_games: 1,
          sort_by: sortBy,
          sort_order: sortDirection,
          limit: 100,
        }),
        api.getTeamPlayers(teamKey, seasonsFilter, venueFilter, excludeSubs),
      ]);

      setTeam(teamData);
      setMachineStats(statsData.stats);
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

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-lg text-gray-600">Loading team data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        <strong className="font-bold">Error: </strong>
        <span>{error}</span>
      </div>
    );
  }

  if (!team) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
        Team not found
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/teams"
          className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block"
        >
          ← Back to Teams
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">{team.team_name}</h1>
        <p className="text-gray-600 mt-1">
          Season {team.season} {team.home_venue_key && `• Home Venue: ${team.home_venue_key}`}
        </p>
      </div>

      {/* Machine Statistics Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Machine Statistics
          </h2>
          {fetching && (
            <div className="flex items-center text-sm text-gray-600">
              <svg className="animate-spin h-4 w-4 mr-2 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Updating...
            </div>
          )}
        </div>

        {/* Filters */}
        <div className="mb-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <SeasonMultiSelect
              value={seasonsFilter}
              onChange={setSeasonsFilter}
              availableSeasons={availableSeasons}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Venue
              </label>
              <select
                value={venueFilter || ''}
                onChange={(e) => setVenueFilter(e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Venues</option>
                {venues.map((venue) => (
                  <option key={venue.venue_key} value={venue.venue_key}>
                    {venue.venue_name}
                  </option>
                ))}
              </select>
            </div>

            <RoundMultiSelect
              value={roundsFilter}
              onChange={setRoundsFilter}
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="exclude-subs"
              checked={excludeSubs}
              onChange={(e) => setExcludeSubs(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="exclude-subs" className="ml-2 text-sm text-gray-700">
              Exclude substitute players (roster only)
            </label>
          </div>
        </div>

        {/* Machine Stats Table */}
        {machineStats.length === 0 ? (
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
            No machine statistics found for the selected filters.
          </div>
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

        <div className="mt-4 text-sm text-gray-600">
          Showing {machineStats.length} machine{machineStats.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Team Roster Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Team Roster
        </h2>

        {players.length === 0 ? (
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
            No players found for the selected filters.
          </div>
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
                        <span className="text-gray-400">—</span>
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

        <div className="mt-4 text-sm text-gray-600">
          Showing {players.length} player{players.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  );
}
