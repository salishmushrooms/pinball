'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import {
  MatchplayLookupResult,
  MatchplayPlayerStats,
  MatchplayMatch,
} from '@/lib/types';
import {
  Card,
  Alert,
  LoadingSpinner,
  StatCard,
  Button,
  Table,
  Badge,
} from '@/components/ui';

interface MatchplaySectionProps {
  playerKey: string;
  playerName: string;
}

export function MatchplaySection({ playerKey, playerName }: MatchplaySectionProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lookupResult, setLookupResult] = useState<MatchplayLookupResult | null>(null);
  const [stats, setStats] = useState<MatchplayPlayerStats | null>(null);
  const [linkingUserId, setLinkingUserId] = useState<number | null>(null);
  const [unlinking, setUnlinking] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    fetchMatchplayData();
  }, [playerKey]);

  async function fetchMatchplayData() {
    setLoading(true);
    setError(null);

    try {
      // First check if player is already linked
      const lookup = await api.lookupMatchplayPlayer(playerKey);
      setLookupResult(lookup);

      // If already linked, fetch their stats
      if (lookup.status === 'already_linked') {
        const playerStats = await api.getMatchplayPlayerStats(playerKey);
        setStats(playerStats);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch Matchplay data');
    } finally {
      setLoading(false);
    }
  }

  async function handleLink(matchplayUserId: number) {
    // Prevent double-clicks
    if (linkingUserId !== null) return;

    setLinkingUserId(matchplayUserId);
    setError(null);
    try {
      await api.linkMatchplayPlayer(playerKey, matchplayUserId);
      // Refresh data after linking
      await fetchMatchplayData();
    } catch (err) {
      // Handle 409 as success - player is already linked
      if (err instanceof Error && err.message.includes('409')) {
        await fetchMatchplayData();
        return;
      }
      setError(err instanceof Error ? err.message : 'Failed to link player');
    } finally {
      setLinkingUserId(null);
    }
  }

  async function handleUnlink() {
    if (unlinking) return;

    setUnlinking(true);
    setError(null);
    try {
      await api.unlinkMatchplayPlayer(playerKey);
      setStats(null);
      // Refresh lookup data
      await fetchMatchplayData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to unlink player');
    } finally {
      setUnlinking(false);
    }
  }

  if (loading) {
    return (
      <Card>
        <Card.Header>
          <Card.Title>Matchplay.events</Card.Title>
        </Card.Header>
        <Card.Content>
          <LoadingSpinner text="Loading Matchplay data..." />
        </Card.Content>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <Card.Header>
          <Card.Title>Matchplay.events</Card.Title>
        </Card.Header>
        <Card.Content>
          <Alert variant="error" title="Error">
            {error}
          </Alert>
        </Card.Content>
      </Card>
    );
  }

  // Player is linked - show stats
  if (lookupResult?.status === 'already_linked' && stats) {
    return (
      <Card>
        <Card.Header>
          <div className="flex items-center justify-between">
            <Card.Title>Matchplay.events</Card.Title>
            <a
              href={stats.profile_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              View Profile →
            </a>
          </div>
        </Card.Header>
        <Card.Content>
          <div className="space-y-6">
            {/* Rating and IFPA Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                label="Matchplay Rating"
                value={
                  stats.rating?.rating != null && stats.rating?.rd != null
                    ? `${stats.rating.rating.toLocaleString()} ± ${(stats.rating.rd * 2)}`
                    : stats.rating?.rating?.toLocaleString() ?? 'N/A'
                }
              />
              <StatCard
                label="Lower Bound"
                value={
                  stats.rating?.rating != null && stats.rating?.rd != null
                    ? (stats.rating.rating - stats.rating.rd * 2).toLocaleString()
                    : stats.rating?.lower_bound?.toLocaleString() ?? 'N/A'
                }
              />
              <StatCard
                label="Win Rate"
                value={
                  stats.rating?.efficiency_percent != null
                    ? `${(stats.rating.efficiency_percent * 100).toFixed(1)}%`
                    : 'N/A'
                }
              />
              <StatCard
                label="IFPA Rank"
                value={stats.ifpa?.rank ? `#${stats.ifpa.rank.toLocaleString()}` : 'N/A'}
              />
            </div>

            {/* Additional Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                label="Tournaments"
                value={stats.tournament_count?.toLocaleString() ?? 'N/A'}
              />
              <StatCard
                label="Games Played"
                value={stats.rating?.game_count?.toLocaleString() ?? 'N/A'}
              />
              <StatCard
                label="Wins"
                value={stats.rating?.win_count?.toLocaleString() ?? 'N/A'}
              />
              <StatCard
                label="Losses"
                value={stats.rating?.loss_count?.toLocaleString() ?? 'N/A'}
              />
            </div>

            {/* Machine Stats */}
            {stats.machine_stats && stats.machine_stats.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-3">
                  Machine Performance (Matchplay)
                </h4>
                <Table>
                  <Table.Header>
                    <Table.Row hoverable={false}>
                      <Table.Head>Machine</Table.Head>
                      <Table.Head>Games</Table.Head>
                      <Table.Head>Wins</Table.Head>
                      <Table.Head>Win %</Table.Head>
                    </Table.Row>
                  </Table.Header>
                  <Table.Body>
                    {stats.machine_stats.slice(0, 10).map((machine, idx) => (
                      <Table.Row key={idx}>
                        <Table.Cell>{machine.matchplay_arena_name}</Table.Cell>
                        <Table.Cell>{machine.games_played}</Table.Cell>
                        <Table.Cell>{machine.wins}</Table.Cell>
                        <Table.Cell>
                          {machine.win_percentage != null
                            ? `${machine.win_percentage.toFixed(1)}%`
                            : 'N/A'}
                        </Table.Cell>
                      </Table.Row>
                    ))}
                  </Table.Body>
                </Table>
                {stats.machine_stats.length > 10 && (
                  <p className="text-sm text-gray-500 mt-2">
                    Showing top 10 of {stats.machine_stats.length} machines
                  </p>
                )}
              </div>
            )}

            {/* Unlink Option */}
            <div className="pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-500 mb-2">
                Linked to: {stats.matchplay_name}
                {stats.location && ` (${stats.location})`}
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleUnlink}
                disabled={unlinking}
              >
                {unlinking ? 'Unlinking...' : 'Unlink Account'}
              </Button>
            </div>
          </div>
        </Card.Content>
      </Card>
    );
  }

  // Player not linked - show lookup results or dismissed state
  return (
    <Card>
      <Card.Header>
        <Card.Title>Matchplay.events</Card.Title>
      </Card.Header>
      <Card.Content>
        {dismissed ? (
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              No Matchplay.events account linked.
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setDismissed(false)}
            >
              Search Again
            </Button>
          </div>
        ) : lookupResult?.status === 'not_found' ? (
          <Alert variant="warning">
            No matching Matchplay accounts found for &quot;{playerName}&quot;.
          </Alert>
        ) : lookupResult?.matches && lookupResult.matches.length > 0 ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Found {lookupResult.matches.length} potential match
                {lookupResult.matches.length !== 1 ? 'es' : ''} on Matchplay.events:
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setDismissed(true)}
              >
                Cancel
              </Button>
            </div>
            <div className="space-y-3">
              {lookupResult.matches.map((match: MatchplayMatch) => (
                <div
                  key={match.user.userId}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {match.user.avatar && (
                      <img
                        src={match.user.avatar}
                        alt=""
                        className="w-10 h-10 rounded-full"
                      />
                    )}
                    <div>
                      <p className="font-medium">{match.user.name}</p>
                      {match.user.location && (
                        <p className="text-sm text-gray-500">{match.user.location}</p>
                      )}
                    </div>
                    <Badge
                      variant={match.confidence === 1 ? 'success' : 'warning'}
                    >
                      {Math.round(match.confidence * 100)}% match
                    </Badge>
                  </div>
                  <Button
                    variant={match.auto_link_eligible ? 'primary' : 'secondary'}
                    size="sm"
                    onClick={() => handleLink(match.user.userId)}
                    disabled={linkingUserId !== null}
                  >
                    {linkingUserId === match.user.userId ? 'Linking...' : 'Link'}
                  </Button>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <Alert>
            Search for this player on Matchplay.events to link their account.
          </Alert>
        )}
      </Card.Content>
    </Card>
  );
}

export default MatchplaySection;
