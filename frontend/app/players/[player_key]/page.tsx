'use client';

import { useEffect, useState, useMemo } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { PlayerMachineStat, PlayerMachineScoreHistory } from '@/lib/types';
import {
  Card,
  PageHeader,
  Alert,
  LoadingSpinner,
  Table,
  FilterPanel,
  Modal,
  WinPercentage,
  Breadcrumb,
  Tooltip,
} from '@/components/ui';
import PlayerMachineProgressionChart from '@/components/PlayerMachineProgressionChart';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';
import { VenueSelect } from '@/components/VenueMultiSelect';
import { MatchplaySection } from '@/components/MatchplaySection';
import { SUPPORTED_SEASONS, filterSupportedSeasons, formatScore } from '@/lib/utils';
import {
  usePlayer,
  usePlayerMachineStats,
  usePlayerMachineScoreHistory,
  useVenues,
  usePlayers,
} from '@/lib/queries';

export default function PlayerDetailPage() {
  const params = useParams();
  const playerKey = params.player_key as string;

  // Filter state
  const [sortBy, setSortBy] = useState<'avg_percentile' | 'games_played' | 'avg_score' | 'win_percentage'>('games_played');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [seasonsFilter, setSeasonsFilter] = useState<number[]>([22]);
  const [venueFilter, setVenueFilter] = useState<string>('');

  // Chart-related state
  const [selectedMachine, setSelectedMachine] = useState<string | null>(null);
  const [selectedMachineName, setSelectedMachineName] = useState<string>('');
  const [chartModalOpen, setChartModalOpen] = useState(false);

  // React Query hooks - data fetching with automatic caching
  const {
    data: player,
    isLoading: playerLoading,
    error: playerError,
  } = usePlayer(playerKey);

  const {
    data: statsData,
    isFetching: statsFetching,
    error: statsError,
  } = usePlayerMachineStats(playerKey, {
    seasons: seasonsFilter.length > 0 ? seasonsFilter : undefined,
    venue_key: venueFilter || undefined,
    min_games: 1,
    sort_by: sortBy,
    sort_order: sortDirection,
    limit: 100,
  });

  const { data: venuesData } = useVenues({ limit: 500 });
  const venues = venuesData?.venues || [];

  const { data: playersData } = usePlayers({ limit: 500 });

  // Score history for chart modal
  const {
    data: scoreHistory,
    isLoading: chartLoading,
    error: chartErrorData,
  } = usePlayerMachineScoreHistory(
    playerKey,
    selectedMachine || '',
    {
      venue_key: venueFilter || undefined,
      seasons: seasonsFilter.length > 0 ? seasonsFilter : undefined,
    },
    { enabled: !!selectedMachine && chartModalOpen }
  );

  const chartError = chartErrorData instanceof Error ? chartErrorData.message : null;

  // Derive available seasons from players data
  const availableSeasons = useMemo(() => {
    if (!playersData?.players) return [...SUPPORTED_SEASONS];

    const seasons = new Set<number>();
    playersData.players.forEach(p => {
      if (p.first_seen_season) seasons.add(p.first_seen_season);
      if (p.last_seen_season) seasons.add(p.last_seen_season);
    });

    return filterSupportedSeasons(Array.from(seasons));
  }, [playersData]);

  // Process machine stats with aggregation if multiple seasons
  const machineStats = useMemo(() => {
    if (!statsData?.stats) return [];

    if (seasonsFilter.length !== 1) {
      return aggregateStatsByMachine(statsData.stats);
    } else {
      return sortAggregatedStats(statsData.stats, sortBy, sortDirection);
    }
  }, [statsData, seasonsFilter, sortBy, sortDirection]);

  // Combine loading and error states
  const loading = playerLoading;
  const fetching = statsFetching;
  const error = playerError instanceof Error ? playerError.message :
    statsError instanceof Error ? statsError.message : null;

  function handleMachineSelect(machineKey: string, machineName: string) {
    setSelectedMachine(machineKey);
    setSelectedMachineName(machineName);
    setChartModalOpen(true);
    // React Query will automatically fetch score history when modal opens
    // due to the enabled condition on usePlayerMachineScoreHistory
  }

  function aggregateStatsByMachine(stats: PlayerMachineStat[]): PlayerMachineStat[] {
    // Group stats by machine_key
    const grouped = new Map<string, PlayerMachineStat[]>();

    stats.forEach(stat => {
      const existing = grouped.get(stat.machine_key) || [];
      existing.push(stat);
      grouped.set(stat.machine_key, existing);
    });

    // Aggregate each group
    const aggregated: PlayerMachineStat[] = [];

    grouped.forEach((machineStats) => {
      // Sum games played
      const totalGames = machineStats.reduce((sum, s) => sum + s.games_played, 0);

      // Collect all scores for median calculation (approximate from aggregated data)
      const allScores: number[] = [];
      machineStats.forEach(s => {
        // Add best and worst scores
        allScores.push(s.best_score, s.worst_score);
        // Approximate median by adding median_score
        allScores.push(s.median_score);
      });

      // Calculate aggregated values
      const bestScore = Math.max(...machineStats.map(s => s.best_score));
      const worstScore = Math.min(...machineStats.map(s => s.worst_score));
      const medianScore = allScores.sort((a, b) => a - b)[Math.floor(allScores.length / 2)];
      const avgScore = machineStats.reduce((sum, s) => sum + s.avg_score * s.games_played, 0) / totalGames;

      // Average percentiles (weighted by games played)
      const totalPercentileWeight = machineStats.reduce((sum, s) =>
        (s.avg_percentile !== null ? sum + s.games_played : sum), 0
      );
      const avgPercentile = totalPercentileWeight > 0
        ? machineStats.reduce((sum, s) =>
            s.avg_percentile !== null ? sum + s.avg_percentile * s.games_played : sum, 0
          ) / totalPercentileWeight
        : null;

      const medianPercentile = totalPercentileWeight > 0
        ? machineStats.reduce((sum, s) =>
            s.median_percentile !== null ? sum + s.median_percentile * s.games_played : sum, 0
          ) / totalPercentileWeight
        : null;

      // Calculate win percentage across all seasons
      const totalWins = machineStats.reduce((sum, s) =>
        sum + ((s.win_percentage || 0) / 100 * s.games_played), 0
      );
      const winPercentage = (totalWins / totalGames) * 100;

      // Use first entry as template, update aggregated values
      aggregated.push({
        ...machineStats[0],
        games_played: totalGames,
        best_score: bestScore,
        worst_score: worstScore,
        median_score: Math.round(medianScore),
        avg_score: Math.round(avgScore),
        avg_percentile: avgPercentile,
        median_percentile: medianPercentile,
        win_percentage: winPercentage,
        season: 0, // Indicate this is aggregated across all seasons
      });
    });

    // Sort aggregated results based on sortBy and sortDirection
    return sortAggregatedStats(aggregated, sortBy, sortDirection);
  }

  function sortAggregatedStats(stats: PlayerMachineStat[], sortBy: string, direction: 'asc' | 'desc' = 'desc'): PlayerMachineStat[] {
    const sorted = [...stats].sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'avg_percentile':
          comparison = (b.avg_percentile || 0) - (a.avg_percentile || 0);
          break;
        case 'games_played':
          comparison = b.games_played - a.games_played;
          break;
        case 'avg_score':
          comparison = b.avg_score - a.avg_score;
          break;
        case 'win_percentage':
          comparison = (b.win_percentage || 0) - (a.win_percentage || 0);
          break;
        default:
          return 0;
      }
      return direction === 'asc' ? -comparison : comparison;
    });
    return sorted;
  }

  function handleSort(column: 'avg_percentile' | 'games_played' | 'avg_score' | 'win_percentage') {
    if (sortBy === column) {
      // Toggle direction if clicking the same column
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // New column: default to descending (highest first)
      setSortBy(column);
      setSortDirection('desc');
    }
  }

  // Count active filters
  const activeFilterCount =
    (seasonsFilter.length > 0 && seasonsFilter.length < availableSeasons.length ? 1 : 0) +
    (venueFilter ? 1 : 0);

  function clearFilters() {
    setSeasonsFilter([22]);
    setVenueFilter('');
  }

  if (loading) {
    return <LoadingSpinner fullPage text="Loading player data..." />;
  }

  if (error) {
    return (
      <Alert variant="error" title="Error">
        {error}
      </Alert>
    );
  }

  if (!player) {
    return (
      <Alert variant="warning" title="Not Found">
        Player not found
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumb
          items={[
            { label: 'Players', href: '/players' },
            { label: player.name },
          ]}
        />
        <PageHeader title={player.name} />
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
          <span className="flex items-center gap-1">
            IPR: {player.current_ipr ? Math.round(player.current_ipr) : 'N/A'}
            <Tooltip content="IFPA Player Rating tier (1-6), calculated from Matchplay.events percentile ranking" iconSize={12} />
          </span>
          {player.current_team_key && player.current_team_name && (
            <>
              <span>•</span>
              <span className="flex items-center gap-1">
                Team:{' '}
                <Link
                  href={`/teams/${player.current_team_key}`}
                  className="hover:underline"
                  style={{ color: 'var(--text-link)' }}
                >
                  {player.current_team_name}
                </Link>
                <Tooltip content="Current team based on most recent season (non-substitute appearances)" iconSize={12} />
              </span>
            </>
          )}
        </div>
      </div>

      {/* Matchplay.events Integration */}
      <MatchplaySection playerKey={playerKey} playerName={player.name} />

      {/* Filters */}
      <FilterPanel
        title="Filters"
        collapsible={true}
        activeFilterCount={activeFilterCount}
        showClearAll={activeFilterCount > 0}
        onClearAll={clearFilters}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
        </div>
      </FilterPanel>

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
                      <button
                        onClick={() => handleMachineSelect(stat.machine_key, stat.machine_name)}
                        className="px-4 py-2.5 rounded-lg text-base font-medium transition-colors hover:opacity-80 active:scale-95"
                        style={{ backgroundColor: 'var(--card-bg)', color: 'var(--text-secondary)' }}
                        aria-label={`View chart for ${stat.machine_name}`}
                      >
                        📊
                      </button>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Games: </span>
                        <span style={{ color: 'var(--text-primary)' }}>{stat.games_played}</span>
                      </div>
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
                      <Table.Head>Machine</Table.Head>
                      <Table.Head
                        sortable
                        onSort={() => handleSort('games_played')}
                        sortDirection={sortBy === 'games_played' ? sortDirection : null}
                        tooltip="Total games played on this machine, filtered by selected seasons and venue"
                      >
                        Games
                      </Table.Head>
                      <Table.Head
                        sortable
                        onSort={() => handleSort('win_percentage')}
                        sortDirection={sortBy === 'win_percentage' ? sortDirection : null}
                        tooltip="Win rate in head-to-head matchups. Note: Player 4 scores in doubles may be unreliable due to early game completion"
                      >
                        Win %
                      </Table.Head>
                      <Table.Head
                        sortable
                        onSort={() => handleSort('avg_percentile')}
                        sortDirection={sortBy === 'avg_percentile' ? sortDirection : null}
                        tooltip="Average percentile rank for this machine. Percentiles are machine-specific and not comparable across different machines"
                      >
                        %ile
                      </Table.Head>
                      <Table.Head tooltip="Median score - the middle value when all scores are sorted, representing typical performance">Median</Table.Head>
                      <Table.Head tooltip="Best score achieved on this machine - your peak performance">Best</Table.Head>
                      <Table.Head className="text-center">Chart</Table.Head>
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
                        <Table.Cell>
                          {stat.games_played}
                        </Table.Cell>
                        <Table.Cell>
                          <WinPercentage value={stat.win_percentage} />
                        </Table.Cell>
                        <Table.Cell>
                          {stat.avg_percentile !== null ? stat.avg_percentile.toFixed(1) : 'N/A'}
                        </Table.Cell>
                        <Table.Cell>
                          {formatScore(stat.median_score)}
                        </Table.Cell>
                        <Table.Cell>
                          {formatScore(stat.best_score)}
                        </Table.Cell>
                        <Table.Cell className="text-center">
                          <button
                            onClick={() => handleMachineSelect(stat.machine_key, stat.machine_name)}
                            className="px-3 py-1 rounded text-xs font-medium transition-colors hover:opacity-80"
                            style={{ backgroundColor: 'var(--card-bg-secondary)', color: 'var(--text-secondary)' }}
                            title="View score progression chart"
                          >
                            📊
                          </button>
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
            {machineStats.length > 0 && (
              <span className="ml-2" style={{ color: 'var(--text-muted)' }}>
                (Click 📊 to view score progression)
              </span>
            )}
          </div>
        </Card.Content>
      </Card>

      {/* Score Progression Chart Modal */}
      <Modal
        isOpen={chartModalOpen}
        onClose={() => setChartModalOpen(false)}
        title={`Score Progression: ${selectedMachineName}`}
        size="xl"
      >
        {chartLoading ? (
          <div className="py-8">
            <LoadingSpinner text="Loading score history..." />
          </div>
        ) : chartError ? (
          <Alert variant="error" title="Error">
            {chartError}
          </Alert>
        ) : scoreHistory ? (
          <div>
            <p
              className="text-sm mb-4"
              style={{ color: 'var(--text-muted)' }}
            >
              {scoreHistory.total_games} games recorded
            </p>
            <PlayerMachineProgressionChart data={scoreHistory} />
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>No data loaded</p>
        )}
      </Modal>
    </div>
  );
}
