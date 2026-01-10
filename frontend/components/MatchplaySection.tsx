'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import {
  MatchplayLookupResult,
  MatchplayPlayerStats,
  MatchplayMatch,
  MatchplayUser,
} from '@/lib/types';
import {
  Card,
  Alert,
  LoadingSpinner,
  StatCard,
  Button,
  Table,
  Badge,
  Tooltip,
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

  // Manual search state
  const [manualSearchMode, setManualSearchMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [waFilterEnabled, setWaFilterEnabled] = useState(true);
  const [searchResults, setSearchResults] = useState<MatchplayUser[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    fetchMatchplayData();
  }, [playerKey]);

  async function fetchMatchplayData() {
    console.log('fetchMatchplayData called');
    setLoading(true);
    setError(null);

    try {
      // First check if player is already linked
      const lookup = await api.lookupMatchplayPlayer(playerKey);
      console.log('Lookup result:', lookup);
      setLookupResult(lookup);

      // If already linked, fetch their stats
      if (lookup.status === 'already_linked') {
        console.log('Player is already linked, fetching stats...');
        try {
          const playerStats = await api.getMatchplayPlayerStats(playerKey);
          console.log('Stats fetched:', playerStats);
          setStats(playerStats);
        } catch (statsErr) {
          console.error('Failed to fetch Matchplay stats:', statsErr);
          // Still show linked state even if stats fail
        }
      } else {
        console.log('Player not linked, status:', lookup.status);
        // Clear stats if not linked
        setStats(null);
      }
    } catch (err) {
      console.error('fetchMatchplayData error:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch Matchplay data');
    } finally {
      console.log('fetchMatchplayData done, setting loading=false');
      setLoading(false);
    }
  }

  async function handleManualSearch() {
    if (!searchQuery.trim() || searchQuery.trim().length < 2) {
      setError('Please enter at least 2 characters to search');
      return;
    }

    setSearching(true);
    setError(null);
    setSearchResults([]);

    try {
      const locationFilter = waFilterEnabled ? 'Washington' : undefined;
      const result = await api.searchMatchplayUsers(searchQuery.trim(), locationFilter);
      setSearchResults(result.users);
      if (result.users.length === 0) {
        setError(
          waFilterEnabled
            ? `No Washington State players found matching "${searchQuery}". Try disabling the WA filter.`
            : `No players found matching "${searchQuery}".`
        );
      }
    } catch (err) {
      console.error('Manual search error:', err);
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setSearching(false);
    }
  }

  async function handleLink(matchplayUserId: number) {
    // Prevent double-clicks
    if (linkingUserId !== null) return;

    setLinkingUserId(matchplayUserId);
    setError(null);
    try {
      console.log('Linking player...', playerKey, matchplayUserId);
      const linkResponse = await api.linkMatchplayPlayer(playerKey, matchplayUserId);
      console.log('Link succeeded:', linkResponse);

      // Both "linked" and "already_linked" are success states
      // The latter handles race conditions where link was created by concurrent request
      if (linkResponse.status === 'already_linked') {
        console.log('Player was already linked (possibly from another tab/request)');
      }

      // Clear manual search state
      setManualSearchMode(false);
      setSearchQuery('');
      setSearchResults([]);

      // Update state directly with the response - don't re-fetch as there may be a race condition
      setLookupResult({
        mnp_player: { key: playerKey, name: playerName },
        matches: [],
        status: 'already_linked',
        mapping: linkResponse.mapping,
      });

      // Now fetch stats for the linked player
      try {
        const playerStats = await api.getMatchplayPlayerStats(playerKey);
        console.log('Stats fetched:', playerStats);
        setStats(playerStats);
      } catch (statsErr) {
        console.error('Failed to fetch stats after link:', statsErr);
      }
    } catch (err) {
      console.log('Link error:', err);
      // Handle 409 as conflict with DIFFERENT account (not the same link)
      if (err instanceof Error && err.message.includes('409')) {
        // This is a true conflict - player or matchplay account linked to someone else
        console.log('409 detected - conflict with different account');
        setError('This player or Matchplay account is already linked to a different account');
        // Refresh to show current state
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
      const result = await api.unlinkMatchplayPlayer(playerKey);
      setStats(null);
      // Both "unlinked" and "already_unlinked" are success states
      // The latter handles race conditions gracefully
      if (result.status === 'already_unlinked') {
        console.log('Player was already unlinked (possibly from another tab/request)');
      }
      // Refresh lookup data to show unlinked state
      await fetchMatchplayData();
    } catch (err) {
      // Even if we get an error, refresh state to show current reality
      console.error('Unlink error:', err);
      setError(err instanceof Error ? err.message : 'Failed to unlink player');
      // Attempt to refresh anyway to sync UI with actual state
      try {
        await fetchMatchplayData();
      } catch {
        // Ignore secondary errors
      }
    } finally {
      setUnlinking(false);
    }
  }

  function enterManualSearch() {
    setManualSearchMode(true);
    setSearchQuery('');
    setSearchResults([]);
    setError(null);
  }

  function exitManualSearch() {
    setManualSearchMode(false);
    setSearchQuery('');
    setSearchResults([]);
    setError(null);
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

  if (error && !manualSearchMode && !searchResults.length) {
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

  // Player is linked - show stats (or loading state if stats not yet fetched)
  if (lookupResult?.status === 'already_linked') {
    // If stats haven't loaded yet, show a simple linked message
    if (!stats) {
      return (
        <Card>
          <Card.Header>
            <Card.Title>Matchplay.events</Card.Title>
          </Card.Header>
          <Card.Content>
            <Alert variant="success" title="Linked">
              Player linked to Matchplay.events. Loading stats...
            </Alert>
          </Card.Content>
        </Card>
      );
    }
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
                tooltip="Glicko rating system score with Rating Deviation (RD). Higher rating = stronger player. RD shows uncertainty in rating."
              />
              <StatCard
                label="Lower Bound"
                value={
                  stats.rating?.rating != null && stats.rating?.rd != null
                    ? (stats.rating.rating - stats.rating.rd * 2).toLocaleString()
                    : stats.rating?.lower_bound?.toLocaleString() ?? 'N/A'
                }
                tooltip="95% confidence interval lower bound - your rating is very likely above this value"
              />
              <StatCard
                label="Win Rate"
                value={
                  stats.rating?.efficiency_percent != null
                    ? `${(stats.rating.efficiency_percent * 100).toFixed(1)}%`
                    : 'N/A'
                }
                tooltip="Percentage of games won on Matchplay.events"
              />
              <StatCard
                label="IFPA Rank"
                value={stats.ifpa?.rank ? `#${stats.ifpa.rank.toLocaleString()}` : 'N/A'}
                tooltip="International Flipper Pinball Association world ranking"
              />
            </div>

            {/* Additional Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                label="Tournaments"
                value={stats.tournament_count?.toLocaleString() ?? 'N/A'}
                tooltip="Total tournaments played on Matchplay.events"
              />
              <StatCard
                label="Games Played"
                value={stats.rating?.game_count?.toLocaleString() ?? 'N/A'}
                tooltip="Total games played on Matchplay.events"
              />
              <StatCard
                label="Wins"
                value={stats.rating?.win_count?.toLocaleString() ?? 'N/A'}
                tooltip="Total games won on Matchplay.events"
              />
              <StatCard
                label="Losses"
                value={stats.rating?.loss_count?.toLocaleString() ?? 'N/A'}
                tooltip="Total games lost on Matchplay.events"
              />
            </div>

            {/* Machine Stats */}
            {stats.machine_stats && stats.machine_stats.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <h4 className="text-sm font-semibold text-gray-700">
                    Machine Performance (Matchplay)
                  </h4>
                  <Tooltip content="Machine stats show data from the past 1 year (365 days) only" iconSize={12} />
                </div>
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
                            ? `${machine.win_percentage.toFixed(0)}%`
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

  // Manual search mode
  if (manualSearchMode) {
    return (
      <Card>
        <Card.Header>
          <div className="flex items-center justify-between">
            <Card.Title>Matchplay.events - Manual Search</Card.Title>
            <Button variant="ghost" size="sm" onClick={exitManualSearch}>
              Back
            </Button>
          </div>
        </Card.Header>
        <Card.Content>
          <div className="space-y-4">
            {/* Search input and filter */}
            <div className="space-y-3">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleManualSearch();
                  }}
                  placeholder="Enter player name..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleManualSearch}
                  disabled={searching || !searchQuery.trim()}
                >
                  {searching ? 'Searching...' : 'Search'}
                </Button>
              </div>
              <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={waFilterEnabled}
                  onChange={(e) => setWaFilterEnabled(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                Washington State players only
              </label>
            </div>

            {/* Error message */}
            {error && (
              <Alert variant="warning">
                {error}
              </Alert>
            )}

            {/* Search results */}
            {searchResults.length > 0 && (
              <div className="space-y-3">
                <p className="text-sm text-gray-600">
                  Found {searchResults.length} player{searchResults.length !== 1 ? 's' : ''}:
                </p>
                {searchResults.map((user) => (
                  <div
                    key={user.userId}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      {user.avatar && (
                        <img
                          src={user.avatar}
                          alt=""
                          className="w-10 h-10 rounded-full"
                        />
                      )}
                      <div>
                        <p className="font-medium">{user.name}</p>
                        {user.location && (
                          <p className="text-sm text-gray-500">{user.location}</p>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleLink(user.userId)}
                      disabled={linkingUserId !== null}
                    >
                      {linkingUserId === user.userId ? 'Linking...' : 'Link'}
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* Empty state when no search yet */}
            {!searching && searchResults.length === 0 && !error && (
              <p className="text-sm text-gray-500">
                Search for a player by name. Enable the Washington State filter to only show local players.
              </p>
            )}
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
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setDismissed(false)}
              >
                Search Again
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={enterManualSearch}
              >
                Manual Search
              </Button>
            </div>
          </div>
        ) : lookupResult?.status === 'not_found' ? (
          <div className="space-y-3">
            <Alert variant="warning">
              No matching Matchplay accounts found for &quot;{playerName}&quot;.
            </Alert>
            <Button
              variant="secondary"
              size="sm"
              onClick={enterManualSearch}
            >
              Manual Search
            </Button>
          </div>
        ) : lookupResult?.matches && lookupResult.matches.length > 0 ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">
                Found {lookupResult.matches.length} potential match
                {lookupResult.matches.length !== 1 ? 'es' : ''} on Matchplay.events:
              </p>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setDismissed(true)}
                >
                  Cancel
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={enterManualSearch}
                >
                  Manual Search
                </Button>
              </div>
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
                    onClick={() => {
                      console.log('Button clicked!', match.user.userId, 'linkingUserId:', linkingUserId);
                      handleLink(match.user.userId);
                    }}
                    disabled={linkingUserId !== null}
                  >
                    {linkingUserId === match.user.userId ? 'Linking...' : 'Link'}
                  </Button>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <Alert>
              Search for this player on Matchplay.events to link their account.
            </Alert>
            <Button
              variant="secondary"
              size="sm"
              onClick={enterManualSearch}
            >
              Manual Search
            </Button>
          </div>
        )}
      </Card.Content>
    </Card>
  );
}

export default MatchplaySection;
