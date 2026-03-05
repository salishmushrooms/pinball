'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import {
  WeeklyRecap,
  MatchResult,
  ComebackResult,
  ScoreOutlier,
  MachinePlays,
  GroupStanding,
} from '@/lib/types';
import {
  Card,
  PageHeader,
  Badge,
  Table,
  LoadingSpinner,
  EmptyState,
  StatCard,
} from '@/components/ui';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { formatScore, SUPPORTED_SEASONS } from '@/lib/utils';

export default function WeeklyAnalysisPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <WeeklyAnalysisContent />
    </Suspense>
  );
}

function WeeklyAnalysisContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [season, setSeason] = useState<number>(
    parseInt(searchParams.get('season') || '23')
  );
  const [week, setWeek] = useState<number | undefined>(
    searchParams.get('week') ? parseInt(searchParams.get('week')!) : undefined
  );
  const [recap, setRecap] = useState<WeeklyRecap | null>(null);
  const [availableWeeks, setAvailableWeeks] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch available weeks when season changes
  useEffect(() => {
    api.getWeeklyRecapWeeks(season).then(setAvailableWeeks).catch(() => setAvailableWeeks([]));
  }, [season]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);

    setError(null);
    api
      .getWeeklyRecap(season, week)
      .then((data) => {
        setRecap(data);
        // Sync resolved week into URL
        const params = new URLSearchParams();
        params.set('season', String(season));
        params.set('week', String(data.week));
        router.replace(`?${params.toString()}`, { scroll: false });
      })
      .catch((err) => setError(err.message || 'Failed to load weekly recap'))
      .finally(() => setLoading(false));
  }, [season, week]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <PageHeader
        title="Weekly Analysis"
        description="Upsets, comebacks, and standout performances"
      />

      {/* Controls */}
      <div className="flex flex-wrap gap-4 mb-8">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>
            Season
          </label>
          <select
            value={season}
            onChange={(e) => { setSeason(parseInt(e.target.value)); setWeek(undefined); }}
            className="rounded-md border px-3 py-1.5 text-sm"
            style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg)', color: 'var(--text-primary)' }}
          >
            {[...SUPPORTED_SEASONS].reverse().map((s) => (
              <option key={s} value={s}>Season {s}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium" style={{ color: 'var(--text-muted)' }}>
            Week
          </label>
          <select
            value={recap?.week ?? week ?? ''}
            onChange={(e) => setWeek(parseInt(e.target.value))}
            className="rounded-md border px-3 py-1.5 text-sm"
            style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg)', color: 'var(--text-primary)' }}
          >
            {availableWeeks.map((w) => (
              <option key={w} value={w}>Week {w}</option>
            ))}
          </select>
        </div>
      </div>

      {loading && <LoadingSpinner />}

      {error && (
        <div className="rounded-md p-4 text-sm" style={{ backgroundColor: 'var(--color-error-50)', color: 'var(--color-error-700)', border: '1px solid var(--color-error-200)' }}>
          {error}
        </div>
      )}

      {recap && !loading && (
        <div className="space-y-8">
          {/* Match Summary */}
          <section>
            <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
              Week {recap.week} Summary — {recap.match_summary.total_matches} matches
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard label="Home Wins" value={recap.match_summary.home_wins} trend={`${recap.match_summary.home_win_pct}%`} trendDirection="neutral" />
              <StatCard label="Away Wins" value={recap.match_summary.away_wins} trend={`${recap.match_summary.away_win_pct}%`} trendDirection="neutral" />
              <StatCard label="Ties" value={recap.match_summary.ties} />
              <StatCard
                label="Home Advantage"
                value={`${recap.match_summary.home_win_pct}%`}
                tooltip="Home team win percentage this week"
                trendDirection={recap.match_summary.home_win_pct > 50 ? 'up' : 'down'}
              />
            </div>
          </section>

          {/* Group Standings */}
          <section>
            <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
              Group Standings
            </h2>
            <GroupStandingsSection standings={recap.group_standings} />
          </section>

          {/* Upsets */}
          <section>
            <h2 className="text-lg font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
              Upsets
            </h2>
            <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>
              Lower avg-IPR team wins with ≥1.0 IPR gap
            </p>
            {recap.upsets.length === 0 ? (
              <EmptyState title="No upsets this week" description="All matches went to the higher-rated team." />
            ) : (
              <Card>
                <MatchResultsTable rows={recap.upsets} showUpsetTeam />
              </Card>
            )}
          </section>

          {/* Away Wins */}
          <section>
            <h2 className="text-lg font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
              Away Wins
            </h2>
            <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>
              Away team victories — underdog road wins highlighted
            </p>
            {recap.away_wins.length === 0 ? (
              <EmptyState title="No away wins this week" description="Home teams swept all matches." />
            ) : (
              <Card>
                <MatchResultsTable rows={recap.away_wins} showUnderdogBadge />
              </Card>
            )}
          </section>

          {/* Round 4 Comebacks */}
          <section>
            <h2 className="text-lg font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
              Round 4 Comebacks
            </h2>
            <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>
              Teams that trailed after Round 3 but won the match
            </p>
            {recap.comebacks.length === 0 ? (
              <EmptyState title="No comebacks this week" description="All matches went to the team leading after Round 3." />
            ) : (
              <Card>
                <ComebacksTable rows={recap.comebacks} />
              </Card>
            )}
          </section>

          {/* Score Outliers */}
          <section>
            <h2 className="text-lg font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
              Standout Scores
            </h2>
            <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>
              Scores at the 95th percentile or above for their machine
            </p>
            {recap.score_outliers.length === 0 ? (
              <EmptyState title="No standout scores this week" description="No scores reached the 95th percentile." />
            ) : (
              <Card>
                <OutliersTable rows={recap.score_outliers} />
              </Card>
            )}
          </section>

          {/* Most Played Machines */}
          <section>
            <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
              Most Played Machines
            </h2>
            <Card>
              <TopMachinesTable rows={recap.top_machines} />
            </Card>
          </section>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Group Standings
// ============================================================================

function GroupStandingsSection({ standings }: { standings: GroupStanding[] }) {
  const grouped = standings.reduce<Record<string, GroupStanding[]>>((acc, s) => {
    if (!acc[s.division]) acc[s.division] = [];
    acc[s.division].push(s);
    return acc;
  }, {});

  const divisions = Object.keys(grouped).sort();

  if (divisions.length === 0) {
    return (
      <EmptyState
        title="No group standings available"
        description="Run etl/load_groups.py to load group assignments."
      />
    );
  }

  return (
    <Tabs defaultValue={divisions[0]}>
      <TabsList>
        {divisions.map((div) => (
          <TabsTrigger key={div} value={div}>
            {div}
          </TabsTrigger>
        ))}
      </TabsList>
      {divisions.map((div) => (
        <TabsContent key={div} value={div}>
          <Card>
            <Table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Team</th>
                  <th>W</th>
                  <th>L</th>
                  <th>T</th>
                  <th>GP</th>
                  <th>POPS</th>
                </tr>
              </thead>
              <tbody>
                {grouped[div].map((s, idx) => (
                  <tr key={s.team_key}>
                    <td className="text-center font-medium" style={{ color: 'var(--text-muted)' }}>
                      {idx + 1}
                    </td>
                    <td>
                      <Link
                        href={`/teams/${s.team_key}?seasons=23`}
                        className="font-medium hover:underline"
                        style={{ color: 'var(--color-primary-700)' }}
                      >
                        {s.team_name}
                      </Link>
                    </td>
                    <td className="text-center font-semibold" style={{ color: 'var(--color-success-600)' }}>
                      {s.wins}
                    </td>
                    <td className="text-center" style={{ color: 'var(--color-error-600)' }}>
                      {s.losses}
                    </td>
                    <td className="text-center" style={{ color: 'var(--text-muted)' }}>
                      {s.ties}
                    </td>
                    <td className="text-center" style={{ color: 'var(--text-muted)' }}>
                      {s.matches_played}
                    </td>
                    <td className="text-center font-mono text-sm">
                      {s.pops.toFixed(3)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card>
        </TabsContent>
      ))}
    </Tabs>
  );
}

// ============================================================================
// Match Results Table (used for Upsets and Away Wins)
// ============================================================================

function MatchResultsTable({
  rows,
  showUpsetTeam,
  showUnderdogBadge,
}: {
  rows: MatchResult[];
  showUpsetTeam?: boolean;
  showUnderdogBadge?: boolean;
}) {
  return (
    <>
      {/* Mobile: card layout */}
      <div className="sm:hidden divide-y" style={{ borderColor: 'var(--table-border)' }}>
        {rows.map((r) => (
          <div key={r.match_key} className="px-4 py-3 space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                <span style={{ color: r.winner === 'home' ? 'var(--color-success-600)' : 'var(--text-muted)' }}>
                  {r.home_team_name}
                </span>
                <span className="mx-1.5" style={{ color: 'var(--text-muted)' }}>vs</span>
                <span style={{ color: r.winner === 'away' ? 'var(--color-success-600)' : 'var(--text-muted)' }}>
                  {r.away_team_name}
                </span>
              </div>
              <span className="font-mono text-sm font-semibold">
                {r.home_team_points} – {r.away_team_points}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--text-muted)' }}>
              <span>{r.venue_key}</span>
              {r.ipr_gap != null && (
                <Badge variant={r.ipr_gap >= 2 ? 'error' : 'warning'}>
                  Gap {r.ipr_gap.toFixed(1)}
                </Badge>
              )}
              {showUpsetTeam && r.upset_team_name && (
                <span className="font-medium" style={{ color: 'var(--color-warning-700)' }}>
                  Upset: {r.upset_team_name}
                </span>
              )}
              {showUnderdogBadge && (
                r.is_underdog ? (
                  <Badge variant="warning">Underdog</Badge>
                ) : (
                  <Badge variant="default">Road Win</Badge>
                )
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Desktop: table layout */}
      <div className="hidden sm:block">
        <Table>
          <thead>
            <tr>
              <th>Match</th>
              <th>Score</th>
              <th>Avg IPR</th>
              <th>IPR Gap</th>
              {showUpsetTeam && <th>Upset Team</th>}
              {showUnderdogBadge && <th>Type</th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.match_key}>
                <td>
                  <div className="font-medium" style={{ color: 'var(--text-primary)' }}>
                    <span style={{ color: r.winner === 'home' ? 'var(--color-success-600)' : 'var(--text-muted)' }}>
                      {r.home_team_name}
                    </span>
                    <span className="mx-2" style={{ color: 'var(--text-muted)' }}>vs</span>
                    <span style={{ color: r.winner === 'away' ? 'var(--color-success-600)' : 'var(--text-muted)' }}>
                      {r.away_team_name}
                    </span>
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                    {r.venue_key} · {r.match_key}
                  </div>
                </td>
                <td className="text-center font-mono text-sm">
                  {r.home_team_points} – {r.away_team_points}
                </td>
                <td className="text-center text-sm">
                  {r.home_avg_ipr != null && r.away_avg_ipr != null ? (
                    <span>
                      <span className={r.winner === 'home' ? 'font-semibold' : ''}>{r.home_avg_ipr.toFixed(1)}</span>
                      <span style={{ color: 'var(--text-muted)' }}> / </span>
                      <span className={r.winner === 'away' ? 'font-semibold' : ''}>{r.away_avg_ipr.toFixed(1)}</span>
                    </span>
                  ) : '—'}
                </td>
                <td className="text-center">
                  {r.ipr_gap != null ? (
                    <Badge variant={r.ipr_gap >= 2 ? 'error' : 'warning'}>
                      {r.ipr_gap.toFixed(1)}
                    </Badge>
                  ) : '—'}
                </td>
                {showUpsetTeam && (
                  <td>
                    <span className="font-medium" style={{ color: 'var(--color-warning-700)' }}>
                      {r.upset_team_name ?? '—'}
                    </span>
                  </td>
                )}
                {showUnderdogBadge && (
                  <td className="text-center">
                    {r.is_underdog ? (
                      <Badge variant="warning">Underdog</Badge>
                    ) : (
                      <Badge variant="default">Road Win</Badge>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </>
  );
}

// ============================================================================
// Comebacks Table
// ============================================================================

function ComebacksTable({ rows }: { rows: ComebackResult[] }) {
  return (
    <>
      {/* Mobile: card layout */}
      <div className="sm:hidden divide-y" style={{ borderColor: 'var(--table-border)' }}>
        {rows.map((r) => (
          <div key={r.match_key} className="px-4 py-3 space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                {r.comeback_team_name}
                <span className="font-normal" style={{ color: 'var(--text-muted)' }}> vs {r.other_team_name}</span>
              </div>
              <span className="font-mono text-sm font-semibold">
                {r.final_score_comeback} – {r.final_score_other}
              </span>
            </div>
            <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--text-muted)' }}>
              <Badge variant="error">−{r.deficit_after_r3} after R3</Badge>
              <span>
                R4: <span style={{ color: 'var(--color-success-600)', fontWeight: 600 }}>{r.comeback_r4_points}</span> / {r.other_r4_points}
              </span>
              <span>{r.venue_key}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Desktop: table layout */}
      <div className="hidden sm:block">
        <Table>
          <thead>
            <tr>
              <th>Comeback Team</th>
              <th>Deficit After R3</th>
              <th>R4 Points</th>
              <th>Final Score</th>
              <th>Venue</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.match_key}>
                <td>
                  <div className="font-medium" style={{ color: 'var(--text-primary)' }}>
                    {r.comeback_team_name}
                  </div>
                  <div className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                    vs {r.other_team_name}
                  </div>
                </td>
                <td className="text-center">
                  <Badge variant="error">−{r.deficit_after_r3}</Badge>
                </td>
                <td className="text-center font-mono text-sm">
                  <span style={{ color: 'var(--color-success-600)', fontWeight: 600 }}>
                    {r.comeback_r4_points}
                  </span>
                  <span style={{ color: 'var(--text-muted)' }}> / </span>
                  <span>{r.other_r4_points}</span>
                </td>
                <td className="text-center font-mono text-sm">
                  {r.final_score_comeback} – {r.final_score_other}
                </td>
                <td className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  {r.venue_key}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </>
  );
}

// ============================================================================
// Score Outliers Table
// ============================================================================

const ROUND_LABELS: Record<number, string> = { 1: 'R1 Dbl', 2: 'R2 Sng', 3: 'R3 Sng', 4: 'R4 Dbl' };

function OutliersTable({ rows }: { rows: ScoreOutlier[] }) {
  return (
    <>
      {/* Mobile: card layout */}
      <div className="sm:hidden divide-y" style={{ borderColor: 'var(--table-border)' }}>
        {rows.map((r, i) => (
          <div key={`${r.match_key}-${r.player_key}-${r.machine_key}-${i}`} className="px-4 py-3 space-y-1">
            <div className="flex items-center justify-between">
              <Link
                href={`/players/${r.player_key}`}
                className="font-medium text-sm hover:underline"
                style={{ color: 'var(--color-primary-700)' }}
              >
                {r.player_name}
              </Link>
              <span className="font-mono text-sm font-semibold">
                {formatScore(r.score)}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
              <Link
                href={`/machines/${r.machine_key}`}
                className="hover:underline"
                style={{ color: 'var(--text-primary)' }}
              >
                {r.machine_name}
              </Link>
              <Badge variant={r.pctile_floor >= 99 ? 'success' : 'warning'}>
                {r.pctile_floor >= 99 ? '99th+' : '95th+'}
              </Badge>
              <span>{ROUND_LABELS[r.round_number] ?? `R${r.round_number}`}</span>
              <span>{r.team_name}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Desktop: table layout */}
      <div className="hidden sm:block">
        <Table>
          <thead>
            <tr>
              <th>Player</th>
              <th>Machine</th>
              <th>Score</th>
              <th>Pctile</th>
              <th>Round</th>
              <th>Team</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={`${r.match_key}-${r.player_key}-${r.machine_key}-${i}`}>
                <td>
                  <Link
                    href={`/players/${r.player_key}`}
                    className="font-medium hover:underline"
                    style={{ color: 'var(--color-primary-700)' }}
                  >
                    {r.player_name}
                  </Link>
                </td>
                <td>
                  <Link
                    href={`/machines/${r.machine_key}`}
                    className="hover:underline"
                    style={{ color: 'var(--text-primary)' }}
                  >
                    {r.machine_name}
                  </Link>
                </td>
                <td className="font-mono text-sm font-semibold">
                  {formatScore(r.score)}
                </td>
                <td className="text-center">
                  <Badge variant={r.pctile_floor >= 99 ? 'success' : 'warning'}>
                    {r.pctile_floor >= 99 ? '99th+' : '95th+'}
                  </Badge>
                </td>
                <td className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  {ROUND_LABELS[r.round_number] ?? `R${r.round_number}`}
                </td>
                <td className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  {r.team_name}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </>
  );
}

// ============================================================================
// Top Machines Table
// ============================================================================

function TopMachinesTable({ rows }: { rows: MachinePlays[] }) {
  return (
    <Table>
      <thead>
        <tr>
          <th>#</th>
          <th>Machine</th>
          <th>Games</th>
          <th>Matches</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={r.machine_key}>
            <td className="text-center font-medium" style={{ color: 'var(--text-muted)' }}>
              {i + 1}
            </td>
            <td>
              <Link
                href={`/machines/${r.machine_key}`}
                className="font-medium hover:underline"
                style={{ color: 'var(--color-primary-700)' }}
              >
                {r.machine_name}
              </Link>
            </td>
            <td className="text-center font-semibold">{r.games_played}</td>
            <td className="text-center" style={{ color: 'var(--text-muted)' }}>
              {r.matches_played}
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
