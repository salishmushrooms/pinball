'use client';

import { useEffect, useState, useMemo } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { GamePlayer } from '@/lib/types';
import {
  Card,
  PageHeader,
  Alert,
  LoadingSpinner,
  Table,
  Breadcrumb,
  FilterPanel,
} from '@/components/ui';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';
import { VenueSelect } from '@/components/VenueMultiSelect';
import { SUPPORTED_SEASONS, filterSupportedSeasons, formatScore } from '@/lib/utils';
import {
  usePlayer,
  useMachine,
  usePlayerMachineGames,
  useVenues,
  usePlayers,
} from '@/lib/queries';

export default function PlayerMachineGamesPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const playerKey = params.player_key as string;
  const machineKey = params.machine_key as string;

  // Get initial filter values from URL params
  const initialSeasons = searchParams.get('seasons')?.split(',').map(Number) || [22];
  const initialVenue = searchParams.get('venue_key') || '';

  // Filter state
  const [seasonsFilter, setSeasonsFilter] = useState<number[]>(initialSeasons);
  const [venueFilter, setVenueFilter] = useState<string>(initialVenue);

  // React Query hooks - data fetching with automatic caching
  const {
    data: player,
    isLoading: playerLoading,
    error: playerError,
  } = usePlayer(playerKey);

  const {
    data: machine,
    isLoading: machineLoading,
    error: machineError,
  } = useMachine(machineKey);

  const {
    data: gamesData,
    isFetching: gamesFetching,
    error: gamesError,
  } = usePlayerMachineGames(
    playerKey,
    machineKey,
    {
      seasons: seasonsFilter.length > 0 ? seasonsFilter : undefined,
      venue_key: venueFilter || undefined,
      limit: 100,
      offset: 0,
    }
  );

  const { data: venuesData } = useVenues({ limit: 500 });
  const venues = venuesData?.venues || [];

  const { data: playersData } = usePlayers({ limit: 500 });

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

  // Combine loading and error states
  const loading = playerLoading || machineLoading;
  const fetching = gamesFetching;
  const error = playerError instanceof Error ? playerError.message :
    machineError instanceof Error ? machineError.message :
    gamesError instanceof Error ? gamesError.message : null;

  // Count active filters
  const activeFilterCount =
    (seasonsFilter.length > 0 && seasonsFilter.length < availableSeasons.length ? 1 : 0) +
    (venueFilter ? 1 : 0);

  function clearFilters() {
    setSeasonsFilter([22]);
    setVenueFilter('');
  }

  // Helper function to get player position class for styling
  function getPlayerRowClass(player: GamePlayer, targetPlayerKey: string, roundNumber: number): string {
    const isTargetPlayer = player.player_key === targetPlayerKey;
    const isDoubles = roundNumber === 1 || roundNumber === 4;

    if (isTargetPlayer) {
      return 'bg-blue-50 dark:bg-blue-950/30 font-semibold';
    }

    // Determine if this is an opponent
    if (isDoubles) {
      // In doubles (rounds 1 & 4), we need to check team positions
      // This is a simplified check - in reality you'd need to know the target player's position
      return '';
    }

    return '';
  }

  // Helper function to format team display
  function formatTeamDisplay(game: typeof gamesData.games[0]): string {
    return `${game.away_team_name} @ ${game.home_team_name}`;
  }

  if (loading) {
    return <LoadingSpinner fullPage text="Loading game details..." />;
  }

  if (error) {
    return (
      <Alert variant="error" title="Error">
        {error}
      </Alert>
    );
  }

  if (!player || !machine) {
    return (
      <Alert variant="warning" title="Not Found">
        Player or machine not found
      </Alert>
    );
  }

  const games = gamesData?.games || [];

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumb
          items={[
            { label: 'Players', href: '/players' },
            { label: player.name, href: `/players/${playerKey}` },
            { label: machine.machine_name },
          ]}
        />
        <PageHeader
          title={`${player.name} - ${machine.machine_name}`}
          subtitle="Game-by-game breakdown with opponents"
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
              Games ({games.length})
            </h2>
            {fetching && (
              <LoadingSpinner size="sm" text="Updating..." />
            )}
          </div>

          {games.length === 0 ? (
            <Alert variant="warning">
              No games found for the selected filters.
            </Alert>
          ) : (
            <div className="space-y-6">
              {games.map((game, idx) => (
                <div
                  key={`${game.match_key}-${game.round_number}`}
                  className="border rounded-lg p-4"
                  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg-secondary)' }}
                >
                  {/* Game Header */}
                  <div className="mb-3 pb-3 border-b" style={{ borderColor: 'var(--border)' }}>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
                      <span className="font-medium" style={{ color: 'var(--text-primary)' }}>
                        Season {game.season}, Week {game.week}
                      </span>
                      <span style={{ color: 'var(--text-muted)' }}>•</span>
                      <span style={{ color: 'var(--text-secondary)' }}>
                        Round {game.round_number} ({game.round_number === 1 || game.round_number === 4 ? 'Doubles' : 'Singles'})
                      </span>
                      <span style={{ color: 'var(--text-muted)' }}>•</span>
                      <Link
                        href={`/venues/${game.venue_key}`}
                        className="hover:underline"
                        style={{ color: 'var(--text-link)' }}
                      >
                        {game.venue_name}
                      </Link>
                      {game.date && (
                        <>
                          <span style={{ color: 'var(--text-muted)' }}>•</span>
                          <span style={{ color: 'var(--text-muted)' }}>
                            {new Date(game.date).toLocaleDateString()}
                          </span>
                        </>
                      )}
                    </div>
                    <div className="mt-1 text-sm" style={{ color: 'var(--text-secondary)' }}>
                      <Link
                        href={`/teams/${game.away_team_key}?season=${game.season}`}
                        className="hover:underline"
                        style={{ color: 'var(--text-link)' }}
                      >
                        {game.away_team_name}
                      </Link>
                      {' @ '}
                      <Link
                        href={`/teams/${game.home_team_key}?season=${game.season}`}
                        className="hover:underline"
                        style={{ color: 'var(--text-link)' }}
                      >
                        {game.home_team_name}
                      </Link>
                    </div>
                  </div>

                  {/* Players Table */}
                  <Table>
                    <Table.Header>
                      <Table.Row hoverable={false}>
                        <Table.Head>Pos</Table.Head>
                        <Table.Head>Player</Table.Head>
                        <Table.Head>Team</Table.Head>
                        <Table.Head className="text-right">Score</Table.Head>
                      </Table.Row>
                    </Table.Header>
                    <Table.Body>
                      {game.players.sort((a, b) => a.player_position - b.player_position).map((gamePlayer) => {
                        const isTargetPlayer = gamePlayer.player_key === playerKey;
                        return (
                          <Table.Row
                            key={`${game.match_key}-${game.round_number}-${gamePlayer.player_key}`}
                            className={isTargetPlayer ? 'bg-blue-50 dark:bg-blue-950/30' : ''}
                          >
                            <Table.Cell>
                              <span className={isTargetPlayer ? 'font-semibold' : ''}>
                                {gamePlayer.player_position}
                              </span>
                            </Table.Cell>
                            <Table.Cell>
                              <Link
                                href={`/players/${gamePlayer.player_key}`}
                                className={`hover:underline ${isTargetPlayer ? 'font-semibold' : ''}`}
                                style={{ color: 'var(--text-link)' }}
                              >
                                {gamePlayer.player_name}
                              </Link>
                            </Table.Cell>
                            <Table.Cell>
                              <Link
                                href={`/teams/${gamePlayer.team_key}?season=${game.season}`}
                                className={`hover:underline ${isTargetPlayer ? 'font-semibold' : ''}`}
                                style={{ color: 'var(--text-link)' }}
                              >
                                {gamePlayer.team_name}
                              </Link>
                              <span className={`ml-1 text-xs ${isTargetPlayer ? 'font-semibold' : ''}`} style={{ color: 'var(--text-muted)' }}>
                                ({gamePlayer.is_home_team ? 'H' : 'A'})
                              </span>
                            </Table.Cell>
                            <Table.Cell className="text-right">
                              <span className={isTargetPlayer ? 'font-semibold' : ''}>
                                {formatScore(gamePlayer.score)}
                              </span>
                            </Table.Cell>
                          </Table.Row>
                        );
                      })}
                    </Table.Body>
                  </Table>
                </div>
              ))}
            </div>
          )}
        </Card.Content>
      </Card>
    </div>
  );
}
