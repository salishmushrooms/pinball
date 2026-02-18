'use client';

import { useEffect, useState, useMemo } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Team, TeamMachineStat, TeamPlayer, Venue, MatchplayRatingInfo, TeamSeasonMatch } from '@/lib/types';
import { RoundMultiSelect } from '@/components/RoundMultiSelect';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';
import { VenueSelect } from '@/components/VenueMultiSelect';
import { useDebouncedEffect, useURLFilters, filterConfigs, DEFAULT_SEASONS, DEFAULT_ROUNDS } from '@/lib/hooks';
import { Table, Card, PageHeader, FilterPanel, Alert, LoadingSpinner, WinPercentage, Breadcrumb, TeamLogo } from '@/components/ui';
import type { FilterChipData } from '@/components/ui/FilterChip';
import { SUPPORTED_SEASONS, filterSupportedSeasons, formatScore, cn } from '@/lib/utils';

export default function TeamDetailPage() {
  const params = useParams();
  const teamKey = params.team_key as string;

  // URL-synced filters
  const { filters, getSeasonChips, clearAllFilters } = useURLFilters({
    seasons: filterConfigs.seasons(),
    venue: filterConfigs.venue(),
    rounds: filterConfigs.rounds(),
    includeSubs: filterConfigs.boolean('includeSubs', false),
    includeAllVenues: filterConfigs.boolean('includeAllVenues', false),
  });

  // Destructure for easier access
  const seasonsFilter = filters.seasons.value;
  const setSeasonsFilter = filters.seasons.setValue;
  const venueFilter = filters.venue.value;
  const setVenueFilter = filters.venue.setValue;
  const roundsFilter = filters.rounds.value;
  const setRoundsFilter = filters.rounds.setValue;
  // Note: includeSubs=true in URL means excludeSubs=false
  const excludeSubs = !filters.includeSubs.value;
  const setExcludeSubs = (exclude: boolean) => filters.includeSubs.setValue(!exclude);
  const includeAllVenues = filters.includeAllVenues.value;
  const setIncludeAllVenues = filters.includeAllVenues.setValue;

  const [team, setTeam] = useState<Team | null>(null);
  const [machineStats, setMachineStats] = useState<TeamMachineStat[]>([]);
  const [players, setPlayers] = useState<TeamPlayer[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([]);
  const [matchplayRatings, setMatchplayRatings] = useState<Record<string, MatchplayRatingInfo>>({});
  const [matchplayLastUpdated, setMatchplayLastUpdated] = useState<string | null>(null);
  const [matchplayRefreshing, setMatchplayRefreshing] = useState(false);
  const [schedule, setSchedule] = useState<TeamSeasonMatch[]>([]);
  const [currentSeason, setCurrentSeason] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters for Machine Stats
  // Note: 'machine_name' is client-side only; API supports: games_played, avg_score, best_score, win_percentage, median_score
  const [sortBy, setSortBy] = useState<'games_played' | 'avg_score' | 'best_score' | 'win_percentage' | 'median_score' | 'machine_name'>('games_played');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Sorting for Team Roster (client-side)
  const [rosterSortBy, setRosterSortBy] = useState<'player_name' | 'current_ipr' | 'games_played' | 'win_percentage'>('games_played');
  const [rosterSortDirection, setRosterSortDirection] = useState<'asc' | 'desc'>('desc');

  // Collapsible section states
  const [scheduleOpen, setScheduleOpen] = useState(true);
  const [rosterOpen, setRosterOpen] = useState(true);
  const [machinesOpen, setMachinesOpen] = useState(true);

  useEffect(() => {
    fetchVenues();
    fetchSeasons();
  }, []);

  // Fetch schedule for the current/latest season when team is loaded
  useEffect(() => {
    if (!teamKey || availableSeasons.length === 0) return;

    const latestSeason = Math.max(...availableSeasons);
    setCurrentSeason(latestSeason);

    api.getTeamSchedule(latestSeason, teamKey)
      .then((data) => {
        setSchedule(data.schedule);
      })
      .catch((err) => {
        console.warn('Failed to fetch team schedule:', err);
      });
  }, [teamKey, availableSeasons]);

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
  }, 500, [teamKey, sortBy, sortDirection, seasonsFilter, venueFilter, roundsFilter, excludeSubs, includeAllVenues]);

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
          include_all_venues: includeAllVenues,
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

      // Fetch cached Matchplay ratings for all players in roster (non-blocking)
      // This uses cached data so it's fast and doesn't hit rate limits
      if (playersData.players.length > 0) {
        const playerKeys = playersData.players.map((p) => p.player_key);
        api.getMatchplayRatings(playerKeys)
          .then((ratingsResponse) => {
            setMatchplayRatings(ratingsResponse.ratings || {});
            setMatchplayLastUpdated(ratingsResponse.last_updated);
          })
          .catch((ratingsErr) => {
            // Non-fatal - just log and continue without ratings
            console.warn('Failed to fetch Matchplay ratings:', ratingsErr);
          });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch team data');
    } finally {
      setLoading(false);
      setFetching(false);
    }
  }

  async function refreshMatchplayRatings() {
    if (players.length === 0 || matchplayRefreshing) return;

    setMatchplayRefreshing(true);
    try {
      const playerKeys = players.map((p) => p.player_key);
      const ratingsResponse = await api.getMatchplayRatings(playerKeys, true);
      setMatchplayRatings(ratingsResponse.ratings || {});
      setMatchplayLastUpdated(ratingsResponse.last_updated);
    } catch (err) {
      console.warn('Failed to refresh Matchplay ratings:', err);
    } finally {
      setMatchplayRefreshing(false);
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
          // Extract first name (first word) for sorting
          const aFirstName = a.player_name.split(' ')[0].toLowerCase();
          const bFirstName = b.player_name.split(' ')[0].toLowerCase();
          aVal = aFirstName;
          bVal = bFirstName;
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

  // Build active filters array for chips display
  const activeFilters: FilterChipData[] = [
    // Individual season chips from the hook
    ...getSeasonChips(seasonsFilter, availableSeasons.length),
  ];

  if (venueFilter) {
    const venueName = venues.find(v => v.venue_key === venueFilter)?.venue_name || venueFilter;
    activeFilters.push({
      key: 'venue',
      label: 'Venue',
      value: venueName,
      onRemove: () => setVenueFilter(''),
    });
  }

  if (roundsFilter.length > 0 && roundsFilter.length < 4) {
    activeFilters.push({
      key: 'rounds',
      label: 'Rounds',
      value: roundsFilter.map(r => `R${r}`).join(', '),
      onRemove: () => setRoundsFilter(DEFAULT_ROUNDS),
    });
  }

  if (!excludeSubs) {
    activeFilters.push({
      key: 'subs',
      label: 'Include',
      value: 'Substitutes',
      onRemove: () => setExcludeSubs(true),
    });
  }

  if (includeAllVenues && venueFilter) {
    activeFilters.push({
      key: 'allVenues',
      label: 'All Venues',
      value: 'for venue machines',
      onRemove: () => setIncludeAllVenues(false),
    });
  }

  // clearFilters is provided by the hook as clearAllFilters

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
        <Breadcrumb
          items={[
            { label: 'Teams', href: '/teams' },
            { label: team.team_name },
          ]}
        />
        <div className="flex items-center gap-4 mt-4">
          <TeamLogo
            teamKey={team.team_key}
            teamName={team.team_name}
            size="lg"
            priority={true}
          />
          <div className="flex-1">
            <PageHeader
              title={team.team_name}
              description={
                <span>
                  Season {team.season}
                  {team.home_venue_key && team.home_venue_name && (
                    <>
                      {' • Home Venue: '}
                      <Link
                        href={`/venues/${team.home_venue_key}`}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        {team.home_venue_name}
                      </Link>
                    </>
                  )}
                </span>
              }
            />
          </div>
        </div>
      </div>

      {/* Season Schedule Section */}
      {schedule.length > 0 && currentSeason && (
        <div
          className="border rounded-lg"
          style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg)' }}
        >
          <button
            onClick={() => setScheduleOpen(!scheduleOpen)}
            className="w-full flex items-center justify-between px-6 py-4 transition-colors hover:opacity-80"
          >
            <div className="flex items-center gap-3">
              <h2
                className="text-xl font-semibold"
                style={{ color: 'var(--text-primary)' }}
              >
                Season {currentSeason} Schedule
              </h2>
              <span
                className="text-sm"
                style={{ color: 'var(--text-muted)' }}
              >
                ({(() => {
                  const today = new Date();
                  today.setHours(0, 0, 0, 0);
                  return schedule.filter(m => {
                    if (m.state === 'complete') return false;
                    if (!m.date) return true;
                    const matchDate = new Date(m.date);
                    return matchDate >= today;
                  }).length;
                })()} upcoming)
              </span>
            </div>
            <svg
              className={cn(
                'w-5 h-5 transition-transform',
                scheduleOpen && 'transform rotate-180'
              )}
              style={{ color: 'var(--text-muted)' }}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          {scheduleOpen && (
            <div className="px-6 pb-6 border-t" style={{ borderColor: 'var(--border)' }}>
              <div className="pt-4 space-y-2">
                {(() => {
                  const today = new Date();
                  today.setHours(0, 0, 0, 0);

                  // Find the next match: earliest future match that's not complete
                  const upcomingMatches = schedule.filter(m => {
                    if (m.state === 'complete') return false;
                    if (!m.date) return true; // Include matches without dates
                    const matchDate = new Date(m.date);
                    return matchDate >= today;
                  });

                  const nextUnplayedMatch = upcomingMatches.length > 0
                    ? upcomingMatches.reduce((min, match) => {
                        if (!match.date) return min;
                        if (!min.date) return match;
                        return new Date(match.date) < new Date(min.date) ? match : min;
                      }, upcomingMatches[0])
                    : null;

                  return schedule.map((match) => {
                    // Match is analyzable if not complete AND (no date OR date is today/future)
                    const matchDate = match.date ? new Date(match.date) : null;
                    const isFutureOrToday = !matchDate || matchDate >= today;
                    const isAnalyzable = match.state !== 'complete' && isFutureOrToday;
                    const isNextMatch = nextUnplayedMatch?.match_key === match.match_key;

                    return (
                      <div
                        key={match.match_key}
                        className={cn(
                          'flex flex-wrap items-center gap-2 p-3 rounded-lg border',
                          isNextMatch ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                        )}
                        style={{ borderColor: 'var(--border)' }}
                      >
                        <span
                          className="text-sm font-medium"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          Wk {match.week}
                        </span>
                        <span
                          className="text-sm hidden sm:inline"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          {match.date || 'TBD'}
                        </span>
                        <span
                          className="text-sm"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          {match.is_home ? 'vs' : '@'}
                        </span>
                        <Link
                          href={`/teams/${match.opponent}`}
                          className="text-sm font-medium text-blue-600 hover:text-blue-800"
                        >
                          {match.opponent_name}
                        </Link>
                        <div className="ml-auto">
                          {isNextMatch ? (
                            <Link
                              href={`/matchups?match=${match.match_key}`}
                              className="px-2 py-1 text-xs font-medium rounded-full bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                            >
                              Analyze Matchup
                            </Link>
                          ) : isAnalyzable ? (
                            <Link
                              href={`/matchups?match=${match.match_key}`}
                              className="px-2 py-1 text-xs font-medium rounded-full transition-colors hover:bg-gray-200 dark:hover:bg-gray-700"
                              style={{
                                backgroundColor: 'var(--bg-secondary)',
                                color: 'var(--text-muted)',
                              }}
                            >
                              Analyze Matchup
                            </Link>
                          ) : (
                            <span
                              className="px-2 py-1 text-xs rounded-full"
                              style={{
                                backgroundColor: 'var(--bg-secondary)',
                                color: 'var(--text-muted)',
                              }}
                            >
                              Done
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  });
                })()}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <FilterPanel
        title="Filters"
        collapsible={true}
        activeFilters={activeFilters}
        showClearAll={activeFilters.length > 1}
        onClearAll={clearAllFilters}
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
              onChange={(value) => {
                setVenueFilter(value);
                if (!value) {
                  setIncludeAllVenues(false);
                }
              }}
              venues={venues}
              label="Venue"
            />

            <RoundMultiSelect
              value={roundsFilter}
              onChange={setRoundsFilter}
              variant="dropdown"
            />
          </div>

          <div className="flex flex-col gap-3">
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

            {venueFilter && (
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="include-all-venues"
                  checked={includeAllVenues}
                  onChange={(e) => setIncludeAllVenues(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 rounded"
                  style={{ borderColor: 'var(--input-border)' }}
                />
                <label
                  htmlFor="include-all-venues"
                  className="ml-2 text-sm"
                  style={{ color: 'var(--text-secondary)' }}
                >
                  Include scores from all venues for machines at this venue
                </label>
              </div>
            )}
          </div>
        </div>
      </FilterPanel>

      {/* Team Roster Section - Collapsible */}
      <div
        className="border rounded-lg"
        style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg)' }}
      >
        <div className="flex items-center justify-between px-6 py-4">
          <button
            onClick={() => setRosterOpen(!rosterOpen)}
            className="flex items-center gap-3 transition-colors hover:opacity-80"
          >
            <h2
              className="text-xl font-semibold"
              style={{ color: 'var(--text-primary)' }}
            >
              Team Roster
            </h2>
            <span
              className="text-sm"
              style={{ color: 'var(--text-muted)' }}
            >
              ({players.length} player{players.length !== 1 ? 's' : ''})
            </span>
            <svg
              className={cn(
                'w-5 h-5 transition-transform',
                rosterOpen && 'transform rotate-180'
              )}
              style={{ color: 'var(--text-muted)' }}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          {/* Matchplay refresh button */}
          <div className="flex items-center gap-2">
            {matchplayLastUpdated && (
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                MP data: {new Date(matchplayLastUpdated).toLocaleDateString()}
              </span>
            )}
            <button
              onClick={(e) => {
                e.stopPropagation();
                refreshMatchplayRatings();
              }}
              disabled={matchplayRefreshing || players.length === 0}
              className={cn(
                'px-3 py-1 text-xs rounded border transition-colors',
                matchplayRefreshing
                  ? 'opacity-50 cursor-not-allowed'
                  : 'hover:bg-blue-50 dark:hover:bg-blue-900/20'
              )}
              style={{
                borderColor: 'var(--border)',
                color: 'var(--text-secondary)',
              }}
              title="Refresh Matchplay ratings from API"
            >
              {matchplayRefreshing ? (
                <span className="flex items-center gap-1">
                  <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Refreshing...
                </span>
              ) : (
                'Refresh MP'
              )}
            </button>
          </div>
        </div>

        {rosterOpen && (
          <div className="px-6 pb-6 border-t" style={{ borderColor: 'var(--border)' }}>
            {players.length === 0 ? (
              <div className="pt-4">
                <Alert variant="warning">
                  No players found for the selected filters.
                </Alert>
              </div>
            ) : (
              <>
                {/* Mobile view - stacked cards */}
                <div className="sm:hidden space-y-3 pt-4">
                  {sortedPlayers.map((player) => {
                    const mpRating = matchplayRatings[player.player_key];
                    return (
                      <div
                        key={player.player_key}
                        className="border rounded-lg p-3"
                        style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg-secondary)' }}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <Link
                            href={`/players/${encodeURIComponent(player.player_key)}`}
                            className="font-medium text-blue-600 hover:text-blue-800"
                          >
                            {player.player_name}
                          </Link>
                          <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                            IPR: {player.current_ipr || 'N/A'}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span style={{ color: 'var(--text-muted)' }}>Games: </span>
                            <span style={{ color: 'var(--text-primary)' }}>{player.games_played}</span>
                          </div>
                          <div>
                            <span style={{ color: 'var(--text-muted)' }}>Win: </span>
                            <WinPercentage value={player.win_percentage} />
                          </div>
                          {mpRating && (
                            <div>
                              <span style={{ color: 'var(--text-muted)' }}>MP: </span>
                              <a
                                href={mpRating.profile_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600"
                              >
                                {mpRating.rating ?? '—'}
                              </a>
                            </div>
                          )}
                          {player.most_played_machine_name && (
                            <div className="col-span-2">
                              <span style={{ color: 'var(--text-muted)' }}>Top: </span>
                              <Link
                                href={`/machines/${player.most_played_machine_key}`}
                                className="text-blue-600"
                              >
                                {player.most_played_machine_name}
                              </Link>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Desktop view - table */}
                <div className="hidden sm:block pt-4">
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
                        <Table.Head>MP</Table.Head>
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
                        <Table.Head>Top Machine</Table.Head>
                      </Table.Row>
                    </Table.Header>
                    <Table.Body striped>
                      {sortedPlayers.map((player) => {
                        const mpRating = matchplayRatings[player.player_key];
                        return (
                          <Table.Row key={player.player_key}>
                            <Table.Cell>
                              <Link
                                href={`/players/${encodeURIComponent(player.player_key)}`}
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
                              <WinPercentage value={player.win_percentage} />
                            </Table.Cell>
                            <Table.Cell>
                              {player.most_played_machine_name ? (
                                <Link
                                  href={`/machines/${player.most_played_machine_key}`}
                                  className="text-blue-600 hover:text-blue-800"
                                >
                                  {player.most_played_machine_name}
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
                </div>
              </>
            )}
          </div>
        )}
      </div>

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
            <>
              {/* Mobile view - stacked cards */}
              <div className="sm:hidden space-y-3">
                {machineStats.map((stat, idx) => (
                  <div
                    key={idx}
                    className="border rounded-lg p-3"
                    style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg-secondary)' }}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <Link
                        href={`/machines/${stat.machine_key}`}
                        className="font-medium text-blue-600 hover:text-blue-800"
                      >
                        {stat.machine_name}
                      </Link>
                      <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                        {stat.games_played} games
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Win: </span>
                        <WinPercentage value={stat.win_percentage} />
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Med: </span>
                        <span style={{ color: 'var(--text-primary)' }}>{formatScore(stat.median_score)}</span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Best: </span>
                        <span style={{ color: 'var(--text-primary)' }}>{formatScore(stat.best_score)}</span>
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
                        Median
                      </Table.Head>
                      <Table.Head
                        sortable
                        onSort={() => handleSort('best_score')}
                        sortDirection={sortBy === 'best_score' ? sortDirection : null}
                      >
                        Best
                      </Table.Head>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body striped>
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
                          <WinPercentage value={stat.win_percentage} />
                        </Table.Cell>
                        <Table.Cell>
                          {formatScore(stat.median_score)}
                        </Table.Cell>
                        <Table.Cell>
                          {formatScore(stat.best_score)}
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table>
              </div>
            </>
          )}

          <div
            className="mt-4 text-sm"
            style={{ color: 'var(--text-muted)' }}
          >
            Showing {machineStats.length} machine{machineStats.length !== 1 ? 's' : ''}
          </div>
        </Card.Content>
      </Card>
    </div>
  );
}
