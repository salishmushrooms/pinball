'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { LiveMatchDetail, LiveGame, LiveRound, LiveScore, LiveRosterPlayer } from '@/lib/types';
import {
  Alert,
  LoadingSpinner,
  Badge,
  ContentContainer,
  Button,
  Breadcrumb,
} from '@/components/ui';
import { getPercentileStyle, fmtScore } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getStateBadgeVariant(state: string): 'default' | 'success' | 'warning' | 'error' | 'info' {
  switch (state) {
    case 'COMPLETE': return 'success';
    case 'PLAYING': return 'warning';
    case 'REVIEWING': return 'warning';
    case 'UNAVAILABLE': return 'error';
    default: return 'default';
  }
}

function getStateLabel(state: string): string {
  switch (state) {
    case 'COMPLETE': return 'Match Complete';
    case 'PLAYING': return 'Live';
    case 'REVIEWING': return 'Reviewing';
    case 'SCHEDULED': return 'Scheduled';
    case 'PREGAME': return 'Pre-game';
    case 'LINEUPS': return 'Lineups';
    case 'PICKING': return 'Picking';
    case 'RESPONDING': return 'Responding';
    default: return state;
  }
}

function getRoundTypeLabel(n: number): string {
  return (n === 1 || n === 4) ? 'Doubles' : 'Singles';
}

function getRoundStatusLabel(n: number): string {
  switch (n) {
    case 1: return 'Away picks';
    case 2: return 'Home picks';
    case 3: return 'Away picks';
    case 4: return 'Home picks';
    default: return '';
  }
}

/**
 * Split a game's scores into away and home arrays based on round number.
 * Round 1 (doubles, away picks): P1,P3 = away; P2,P4 = home
 * Round 2 (singles, home picks): P1 = home; P2 = away
 * Round 3 (singles, away picks): P1 = away; P2 = home
 * Round 4 (doubles, home picks): P1,P3 = home; P2,P4 = away
 */
function splitScores(scores: LiveScore[], roundN: number): { away: LiveScore[]; home: LiveScore[] } {
  const isDoubles = roundN === 1 || roundN === 4;
  if (isDoubles) {
    if (roundN === 1) {
      return {
        away: [scores[0], scores[2]].filter(Boolean),
        home: [scores[1], scores[3]].filter(Boolean),
      };
    } else {
      return {
        away: [scores[1], scores[3]].filter(Boolean),
        home: [scores[0], scores[2]].filter(Boolean),
      };
    }
  } else {
    if (roundN === 3) {
      return { away: [scores[0]].filter(Boolean), home: [scores[1]].filter(Boolean) };
    } else {
      return { away: [scores[1]].filter(Boolean), home: [scores[0]].filter(Boolean) };
    }
  }
}

// ---------------------------------------------------------------------------
// Scoreboard Table
// ---------------------------------------------------------------------------

function Scoreboard({ match }: { match: LiveMatchDetail }) {
  const isComplete = match.state === 'COMPLETE';
  const isLive = match.state === 'PLAYING' || match.state === 'REVIEWING';

  // Calculate round-by-round points
  const roundPoints = match.rounds.map(rd => ({
    n: rd.n,
    away: rd.games.reduce((sum, g) => sum + (g.away_points ?? 0), 0),
    home: rd.games.reduce((sum, g) => sum + (g.home_points ?? 0), 0),
  }));

  const awayWinning = match.away_final_points > match.home_final_points;
  const homeWinning = match.home_final_points > match.away_final_points;

  return (
    <div className="rounded-lg overflow-hidden" style={{ backgroundColor: '#1f2937' }}>
      {/* Match info header */}
      <div className="px-4 py-3 flex flex-wrap items-center justify-between gap-2" style={{ backgroundColor: '#111827' }}>
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold text-white">
            {match.away_team_name} @ {match.home_team_name}
          </h1>
          <Badge variant={getStateBadgeVariant(match.state)}>
            {getStateLabel(match.state)}
          </Badge>
        </div>
        <div className="text-sm text-gray-400">
          {match.venue_key} · {match.date || `Week ${match.week}`}
          {match.date && ` · Week ${match.week}`}
        </div>
      </div>

      {/* Current round indicator for live matches */}
      {isLive && match.current_round > 0 && (
        <div className="px-4 py-1.5 text-xs font-medium" style={{ backgroundColor: '#f59e0b22', color: '#f59e0b' }}>
          Round {match.current_round} in progress
        </div>
      )}

      {/* Score table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: '1px solid #374151' }}>
              <th className="py-2 px-3 text-left text-xs text-gray-500 font-medium w-20">TEAM</th>
              {[1, 2, 3, 4].map(n => (
                <th key={n} className="py-2 px-2 text-center text-xs text-gray-500 font-medium">R{n}</th>
              ))}
              <th className="py-2 px-2 text-center text-xs text-gray-500 font-medium">PMP</th>
              <th className="py-2 px-2 text-center text-xs text-gray-500 font-medium">HMP</th>
              <th className="py-2 px-3 text-center text-xs text-gray-500 font-medium">TOT</th>
            </tr>
          </thead>
          <tbody>
            {/* Away team row */}
            <tr style={{ borderBottom: '1px solid #374151' }}>
              <td className="py-2 px-3 text-sm font-semibold" style={{ color: '#60a5fa' }}>
                {match.away_team_key}
              </td>
              {[1, 2, 3, 4].map(n => {
                const rp = roundPoints.find(r => r.n === n);
                return (
                  <td key={n} className="py-2 px-2 text-center text-sm text-gray-300">
                    {rp ? rp.away : '—'}
                  </td>
                );
              })}
              <td className="py-2 px-2 text-center text-sm" style={{ color: match.away_participation > 0 ? '#a78bfa' : '#6b7280' }}>
                {match.away_participation}
              </td>
              <td className="py-2 px-2 text-center text-sm" style={{ color: match.away_handicap > 0 ? '#34d399' : '#6b7280' }}>
                {match.away_handicap}
              </td>
              <td className="py-2 px-3 text-center text-sm font-bold" style={{ color: awayWinning ? '#60a5fa' : '#e5e7eb' }}>
                {match.away_final_points}
              </td>
            </tr>
            {/* Home team row */}
            <tr>
              <td className="py-2 px-3 text-sm font-semibold" style={{ color: '#f87171' }}>
                {match.home_team_key}
              </td>
              {[1, 2, 3, 4].map(n => {
                const rp = roundPoints.find(r => r.n === n);
                return (
                  <td key={n} className="py-2 px-2 text-center text-sm text-gray-300">
                    {rp ? rp.home : '—'}
                  </td>
                );
              })}
              <td className="py-2 px-2 text-center text-sm" style={{ color: match.home_participation > 0 ? '#a78bfa' : '#6b7280' }}>
                {match.home_participation}
              </td>
              <td className="py-2 px-2 text-center text-sm" style={{ color: match.home_handicap > 0 ? '#34d399' : '#6b7280' }}>
                {match.home_handicap}
              </td>
              <td className="py-2 px-3 text-center text-sm font-bold" style={{ color: homeWinning ? '#f87171' : '#e5e7eb' }}>
                {match.home_final_points}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Team Roster Section
// ---------------------------------------------------------------------------

function PlayerRow({ player }: { player: LiveRosterPlayer }) {
  return (
    <div className="flex items-center justify-between py-1.5 px-2">
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-sm text-gray-200 truncate">{player.name}</span>
        {player.is_captain && (
          <span className="text-xs font-bold px-1.5 py-0.5 rounded" style={{ backgroundColor: '#f59e0b33', color: '#f59e0b' }}>
            C
          </span>
        )}
        {player.is_sub && (
          <span className="text-xs font-bold px-1.5 py-0.5 rounded" style={{ backgroundColor: '#34d39933', color: '#34d399' }}>
            SUB
          </span>
        )}
      </div>
      <span
        className="text-sm font-medium px-2 py-0.5 rounded-full"
        style={{
          backgroundColor: player.total_points > 0 ? '#60a5fa22' : 'transparent',
          color: player.total_points > 0 ? '#60a5fa' : '#6b7280',
        }}
      >
        {player.total_points > 0 ? `${player.total_points} Pts` : '0 Pts'}
      </span>
    </div>
  );
}

function TeamRoster({ match }: { match: LiveMatchDetail }) {
  const [open, setOpen] = useState(true);

  const awayRoster = [...match.away_lineup].sort((a, b) => a.name.localeCompare(b.name));
  const homeRoster = [...match.home_lineup].sort((a, b) => a.name.localeCompare(b.name));

  const awayTeamIpr = match.away_lineup.reduce((sum, p) => sum + (p.ipr ?? 0), 0);
  const homeTeamIpr = match.home_lineup.reduce((sum, p) => sum + (p.ipr ?? 0), 0);

  if (awayRoster.length === 0 && homeRoster.length === 0) return null;

  return (
    <div className="rounded-lg overflow-hidden" style={{ backgroundColor: '#1f2937' }}>
      <button
        className="w-full flex items-center justify-between px-4 py-3 text-left"
        onClick={() => setOpen(o => !o)}
      >
        <span className="text-sm font-medium text-white">Team Rosters</span>
        <span className="text-gray-500 text-sm">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="px-4 pb-4">
          <div className="grid grid-cols-2 gap-4">
            {/* Away team */}
            <div>
              <div className="flex items-center justify-between mb-2 pb-2" style={{ borderBottom: '2px solid #60a5fa' }}>
                <span className="text-sm font-bold" style={{ color: '#60a5fa' }}>{match.away_team_name}</span>
                <span className="text-xs font-medium px-2 py-0.5 rounded-full" style={{ backgroundColor: '#60a5fa22', color: '#60a5fa' }}>
                  IPR {Math.round(awayTeamIpr)}
                </span>
              </div>
              {awayRoster.map(p => <PlayerRow key={p.key} player={p} />)}
            </div>
            {/* Home team */}
            <div>
              <div className="flex items-center justify-between mb-2 pb-2" style={{ borderBottom: '2px solid #f87171' }}>
                <span className="text-sm font-bold" style={{ color: '#f87171' }}>{match.home_team_name}</span>
                <span className="text-xs font-medium px-2 py-0.5 rounded-full" style={{ backgroundColor: '#f8717122', color: '#f87171' }}>
                  IPR {Math.round(homeTeamIpr)}
                </span>
              </div>
              {homeRoster.map(p => <PlayerRow key={p.key} player={p} />)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Score display for a single player
// ---------------------------------------------------------------------------

function PlayerScore({ score, align }: { score: LiveScore; align: 'left' | 'right' }) {
  const pctStyle = getPercentileStyle(score.percentile);
  const isLeft = align === 'left';

  return (
    <div className={`flex flex-col ${isLeft ? 'items-start' : 'items-end'}`}>
      <div className={`flex items-center gap-1.5 ${isLeft ? '' : 'flex-row-reverse'}`}>
        <span className="text-sm text-gray-300 truncate max-w-24">
          {score.player_name || '—'}
        </span>
        {score.points !== null && score.points !== undefined && (
          <span
            className="text-xs font-medium px-1.5 py-0.5 rounded-full shrink-0"
            style={{ backgroundColor: '#374151', color: '#e5e7eb' }}
          >
            {score.points}
          </span>
        )}
      </div>
      <div className={`flex items-center gap-1.5 mt-0.5 ${isLeft ? '' : 'flex-row-reverse'}`}>
        <span
          className="text-lg font-bold font-mono"
          style={{ color: pctStyle?.color || '#e5e7eb' }}
        >
          {fmtScore(score.score)}
        </span>
        {pctStyle && (
          <span
            className="text-xs px-1 py-0.5 rounded"
            style={{ color: pctStyle.color, backgroundColor: `${pctStyle.color}22` }}
          >
            {pctStyle.label}
          </span>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Game Card
// ---------------------------------------------------------------------------

function GameCard({ game, roundN }: { game: LiveGame; roundN: number }) {
  const { away, home } = splitScores(game.scores, roundN);
  const isDoubles = roundN === 1 || roundN === 4;
  const hasScores = game.scores.some(s => s.score !== null);

  return (
    <div className="rounded-lg border overflow-hidden" style={{ borderColor: '#374151', backgroundColor: '#111827' }}>
      {/* Machine header */}
      <div className="flex items-center justify-between px-3 py-2" style={{ backgroundColor: '#1f2937' }}>
        <span className="text-sm font-semibold text-white uppercase tracking-wide">
          {game.machine_name || game.machine_key || '—'}
        </span>
        {hasScores && (
          <span className="text-xs text-gray-400">
            {game.away_points ?? 0} – {game.home_points ?? 0}
          </span>
        )}
      </div>

      {/* Player scores */}
      <div className="px-3 py-3">
        {isDoubles ? (
          /* Doubles: 2 players per side */
          <div className="space-y-2">
            {[0, 1].map(i => (
              <div key={i} className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  {away[i] && <PlayerScore score={away[i]} align="left" />}
                </div>
                <div className="flex-1">
                  {home[i] && <PlayerScore score={home[i]} align="right" />}
                </div>
              </div>
            ))}
            {/* Team totals for doubles */}
            {hasScores && (
              <div
                className="flex items-center justify-between pt-2 mt-1 text-xs text-gray-500"
                style={{ borderTop: '1px solid #374151' }}
              >
                <span>TOTAL <span className="font-medium text-gray-300 ml-1">{game.away_points ?? 0} pts</span></span>
                <span><span className="font-medium text-gray-300 mr-1">{game.home_points ?? 0} pts</span> TOTAL</span>
              </div>
            )}
          </div>
        ) : (
          /* Singles: 1 player per side */
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              {away[0] && <PlayerScore score={away[0]} align="left" />}
            </div>
            <div className="flex-1">
              {home[0] && <PlayerScore score={home[0]} align="right" />}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Round Section
// ---------------------------------------------------------------------------

function RoundSection({ round, awayKey, homeKey }: { round: LiveRound; awayKey: string; homeKey: string }) {
  const [open, setOpen] = useState(true);

  const awayRoundPts = round.games.reduce((sum, g) => sum + (g.away_points ?? 0), 0);
  const homeRoundPts = round.games.reduce((sum, g) => sum + (g.home_points ?? 0), 0);

  return (
    <div className="space-y-2">
      <button
        className="w-full flex items-center justify-between px-1 py-2 text-left"
        onClick={() => setOpen(o => !o)}
      >
        <div className="flex items-center gap-3">
          <span className="text-base font-semibold text-white">Round {round.n}</span>
          <span className="text-sm text-gray-500">{getRoundTypeLabel(round.n)}</span>
          <span className="text-xs text-gray-600">{getRoundStatusLabel(round.n)}</span>
          {round.done && <Badge variant="success">Complete</Badge>}
        </div>
        <div className="flex items-center gap-4">
          {(awayRoundPts > 0 || homeRoundPts > 0) && (
            <span className="text-sm font-medium">
              <span style={{ color: '#60a5fa' }}>{awayRoundPts}</span>
              <span className="text-gray-600 mx-1">-</span>
              <span style={{ color: '#f87171' }}>{homeRoundPts}</span>
            </span>
          )}
          <span className="text-gray-500 text-sm">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {open && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {round.games.map(game => (
            <GameCard key={game.n} game={game} roundN={round.n} />
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

const POLL_INTERVAL_MS = 30_000;

export default function LiveMatchDetailPage() {
  const params = useParams();
  const matchKey = params.match_key as string;

  const [match, setMatch] = useState<LiveMatchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(async (bypass = false) => {
    if (!matchKey) return;
    try {
      setError(null);
      if (!match) setLoading(true);
      else setRefreshing(true);

      const result = await api.getLiveMatch(matchKey, bypass || undefined);
      setMatch(result);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load match data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [matchKey, match]);

  useEffect(() => { fetchData(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (autoRefresh && match?.state !== 'COMPLETE') {
      intervalRef.current = setInterval(() => fetchData(), POLL_INTERVAL_MS);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [autoRefresh, match?.state, fetchData]);

  if (loading) {
    return <LoadingSpinner fullPage text="Loading match data..." />;
  }

  if (error && !match) {
    return (
      <ContentContainer>
        <Alert variant="error" title="Could not load match">
          {error}
        </Alert>
      </ContentContainer>
    );
  }

  if (!match) return null;

  const isComplete = match.state === 'COMPLETE';

  return (
    <ContentContainer>
      <div className="space-y-4">

        {/* Breadcrumb + refresh controls */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <Breadcrumb items={[{ label: 'Live', href: '/live' }, { label: match.match_key }]} />
          <div className="flex items-center gap-3 shrink-0">
            {refreshing && <LoadingSpinner size="sm" />}
            {lastUpdated && (
              <span className="text-xs text-gray-500">
                {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            {!isComplete && (
              <label className="flex items-center gap-1.5 text-sm text-gray-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={e => setAutoRefresh(e.target.checked)}
                  className="rounded"
                />
                Auto
              </label>
            )}
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

        {/* Scoreboard */}
        <Scoreboard match={match} />

        {/* Team Rosters */}
        <TeamRoster match={match} />

        {/* Percentile legend */}
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: '#f59e0b' }} />
          <span>90th percentile and above highlighted</span>
        </div>

        {/* Error banner */}
        {error && (
          <Alert variant="error" title="Refresh failed">
            {error}
          </Alert>
        )}

        {/* Rounds with game cards */}
        {match.rounds.length === 0 ? (
          <div className="rounded-lg p-8 text-center" style={{ backgroundColor: '#1f2937' }}>
            <p className="text-gray-400">
              {match.state === 'UNAVAILABLE'
                ? 'Match data is not yet available from the MNP site. Scores will appear here once the match is processed.'
                : 'No round data yet. Check back once the match is underway.'}
            </p>
            {match.state === 'UNAVAILABLE' && (
              <p className="text-gray-500 text-sm mt-2">
                This usually takes a day or two after match night.
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {match.rounds.map(round => (
              <RoundSection
                key={round.n}
                round={round}
                awayKey={match.away_team_key}
                homeKey={match.home_team_key}
              />
            ))}
          </div>
        )}

      </div>
    </ContentContainer>
  );
}
