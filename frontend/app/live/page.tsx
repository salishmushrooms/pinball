'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { LiveWeekResponse, LiveMatchSummary } from '@/lib/types';
import {
  Card,
  PageHeader,
  Alert,
  LoadingSpinner,
  Badge,
  ContentContainer,
  Button,
} from '@/components/ui';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getStateBadgeVariant(state: string): 'default' | 'success' | 'warning' | 'error' | 'info' {
  switch (state) {
    case 'COMPLETE': return 'success';
    case 'PLAYING': return 'warning';
    case 'REVIEWING': return 'warning';
    case 'UNAVAILABLE': return 'error';
    default: return 'default'; // SCHEDULED, PREGAME, LINEUPS, PICKING, RESPONDING
  }
}

function getStateLabel(state: string): string {
  switch (state) {
    case 'COMPLETE': return 'Complete';
    case 'PLAYING': return 'Live';
    case 'REVIEWING': return 'Reviewing';
    case 'SCHEDULED': return 'Scheduled';
    case 'PREGAME': return 'Pre-game';
    case 'LINEUPS': return 'Lineups';
    case 'PICKING': return 'Picking';
    case 'RESPONDING': return 'Responding';
    case 'UNAVAILABLE': return 'Unavailable';
    default: return state;
  }
}

// ---------------------------------------------------------------------------
// Match card
// ---------------------------------------------------------------------------

function MatchCard({ match }: { match: LiveMatchSummary }) {
  const isActive = match.state === 'PLAYING' || match.state === 'REVIEWING';
  const isComplete = match.state === 'COMPLETE';
  const hasScores = match.away_total_points > 0 || match.home_total_points > 0;

  return (
    <Link href={`/live/${match.match_key}`} className="block group">
      <div
        className="rounded-lg border p-4 transition-colors cursor-pointer"
        style={{
          backgroundColor: '#1f2937',
          borderColor: isActive ? '#f59e0b' : isComplete ? '#374151' : '#374151',
        }}
      >
        {/* Header: teams */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white truncate">{match.away_team_name}</p>
            <p className="text-xs text-gray-400">Away</p>
          </div>
          <div className="text-center px-3">
            <p className="text-xs text-gray-500">@</p>
          </div>
          <div className="flex-1 min-w-0 text-right">
            <p className="text-sm font-semibold text-white truncate">{match.home_team_name}</p>
            <p className="text-xs text-gray-400">Home</p>
          </div>
        </div>

        {/* Score */}
        {hasScores && (
          <div className="mb-3 px-2">
            {/* Final score (game + handicap + participation) */}
            <div className="flex items-center justify-between">
              <span
                className="text-2xl font-bold"
                style={{ color: match.away_final_points > match.home_final_points ? '#60a5fa' : '#9ca3af' }}
              >
                {match.away_final_points}
              </span>
              <span className="text-xs text-gray-500">final</span>
              <span
                className="text-2xl font-bold"
                style={{ color: match.home_final_points > match.away_final_points ? '#60a5fa' : '#9ca3af' }}
              >
                {match.home_final_points}
              </span>
            </div>
            {/* Bonus breakdown — only show once match is complete */}
            {isComplete && (match.away_handicap > 0 || match.home_handicap > 0 || match.away_participation > 0) && (
              <div className="flex items-center justify-between mt-1">
                <span className="text-xs text-gray-500">
                  {match.away_total_points}
                  {match.away_handicap > 0 && <span style={{ color: '#34d399' }}> +{match.away_handicap}hcp</span>}
                  {match.away_participation > 0 && <span style={{ color: '#a78bfa' }}> +{match.away_participation}par</span>}
                </span>
                <span className="text-xs text-gray-500">
                  {match.home_total_points}
                  {match.home_handicap > 0 && <span style={{ color: '#34d399' }}> +{match.home_handicap}hcp</span>}
                  {match.home_participation > 0 && <span style={{ color: '#a78bfa' }}> +{match.home_participation}par</span>}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Footer: state + venue + round */}
        <div className="flex items-center justify-between">
          <Badge variant={getStateBadgeVariant(match.state)}>
            {getStateLabel(match.state)}
          </Badge>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>{match.venue_key}</span>
            {match.current_round > 0 && (
              <span>· Round {match.current_round}</span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const POLL_INTERVAL_MS = 60_000;

export default function LivePage() {
  const [data, setData] = useState<LiveWeekResponse | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async (bypass = false) => {
    try {
      setError(null);
      if (!data) setLoading(true);
      else setRefreshing(true);

      const result = await api.getLiveWeek(undefined, selectedWeek, bypass || undefined);
      setData(result);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load live match data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [data, selectedWeek]);

  // Fetch on mount and when selected week changes
  useEffect(() => {
    fetchData();
  }, [selectedWeek]); // eslint-disable-line react-hooks/exhaustive-deps

  // Polling
  useEffect(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (autoRefresh) {
      intervalRef.current = setInterval(() => fetchData(), POLL_INTERVAL_MS);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [autoRefresh, fetchData]);

  if (loading) {
    return <LoadingSpinner fullPage text="Loading live matches..." />;
  }

  if (error && !data) {
    return (
      <ContentContainer>
        <Alert variant="error" title="Could not load live match data">
          {error}
        </Alert>
      </ContentContainer>
    );
  }

  // Group matches by state for ordering: Live → Reviewing → Scheduled → Complete → Unavailable
  const stateOrder: Record<string, number> = {
    PLAYING: 0, REVIEWING: 1, PICKING: 2, RESPONDING: 3,
    LINEUPS: 4, PREGAME: 5, SCHEDULED: 6, COMPLETE: 7, UNAVAILABLE: 8,
  };
  const sorted = data
    ? [...data.matches].sort((a, b) => (stateOrder[a.state] ?? 9) - (stateOrder[b.state] ?? 9))
    : [];

  const liveCount = sorted.filter(m => m.state === 'PLAYING' || m.state === 'REVIEWING').length;
  const completeCount = sorted.filter(m => m.state === 'COMPLETE').length;

  return (
    <ContentContainer>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <PageHeader
              title={data ? `Season ${data.season} — Week ${data.week}` : 'Live Matches'}
              description={
                liveCount > 0
                  ? `${liveCount} match${liveCount !== 1 ? 'es' : ''} in progress`
                  : completeCount > 0
                  ? `${completeCount} of ${sorted.length} matches complete`
                  : 'Matches scheduled for this week'
              }
            />
            {data && data.available_weeks.length > 1 && (
              <select
                value={selectedWeek ?? data.week}
                onChange={e => {
                  const val = Number(e.target.value);
                  setSelectedWeek(val);
                  setData(null);
                }}
                className="rounded-md border border-gray-600 bg-gray-800 text-white text-sm px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {data.available_weeks.map(w => (
                  <option key={w} value={w}>Week {w}</option>
                ))}
              </select>
            )}
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {refreshing && <LoadingSpinner size="sm" />}
            {lastUpdated && (
              <span className="text-xs text-gray-500">
                Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            <label className="flex items-center gap-1.5 text-sm text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={e => setAutoRefresh(e.target.checked)}
                className="rounded"
              />
              Auto-refresh
            </label>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => fetchData(true)}
              disabled={refreshing}
            >
              Refresh
            </Button>
          </div>
        </div>

        {/* Error banner (keep cards visible) */}
        {error && (
          <Alert variant="error" title="Refresh failed">
            {error}
          </Alert>
        )}

        {/* Match grid */}
        {sorted.length === 0 ? (
          <Card>
            <p className="text-gray-400 text-center py-8">No matches found for this week.</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {sorted.map(match => (
              <MatchCard key={match.match_key} match={match} />
            ))}
          </div>
        )}
      </div>
    </ContentContainer>
  );
}
