'use client';

import { useState, useEffect, useCallback, useMemo, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import {
  ScheduleMatch,
  SeasonStatus,
} from '@/lib/types';
import {
  PageHeader,
  Alert,
  LoadingSpinner,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui';
import { filterSupportedSeasons } from '@/lib/utils';

type SortField = 'away' | 'home' | 'venue';
type SortDir = 'asc' | 'desc';

export default function MatchupsPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <MatchupsPageContent />
    </Suspense>
  );
}

function MatchupsPageContent() {
  const router = useRouter();

  const [currentSeason, setCurrentSeason] = useState<number | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null);
  const [seasonStatus, setSeasonStatus] = useState<SeasonStatus | null>(null);
  const [allMatches, setAllMatches] = useState<ScheduleMatch[]>([]);
  const [loadingMatches, setLoadingMatches] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [defaultWeek, setDefaultWeek] = useState<number | null>(null);

  // Derive available weeks from all matches
  const weeks = useMemo(() => {
    const weekSet = new Set<number>();
    allMatches.forEach((m) => weekSet.add(m.week));
    return Array.from(weekSet).sort((a, b) => a - b);
  }, [allMatches]);

  // Derive filtered matches for selected week
  const weekMatches = useMemo(() => {
    if (selectedWeek === null) return allMatches;
    return allMatches.filter((m) => m.week === selectedWeek);
  }, [allMatches, selectedWeek]);

  // Derive week date from first match
  const weekDate = useMemo(() => {
    if (weekMatches.length > 0 && weekMatches[0].date) {
      return weekMatches[0].date;
    }
    return null;
  }, [weekMatches]);

  useEffect(() => {
    async function loadCurrentSeasonMatches() {
      setLoadingMatches(true);
      try {
        const initData = await api.getMatchupsInit();
        const supportedSeasons = filterSupportedSeasons(initData.seasons);
        const latestSeason = supportedSeasons.length > 0
          ? Math.max(...supportedSeasons)
          : initData.current_season;

        setCurrentSeason(latestSeason);
        setSeasonStatus(initData.season_status);
        setAllMatches(initData.matches);

        // Find next upcoming week
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const upcomingWeeks = new Set<number>();
        initData.matches.forEach((match) => {
          if (match.state !== 'complete') {
            const matchDate = match.date ? new Date(match.date) : null;
            if (!matchDate || matchDate >= today) {
              upcomingWeeks.add(match.week);
            }
          }
        });

        const nextWeek = upcomingWeeks.size > 0
          ? Math.min(...Array.from(upcomingWeeks))
          : null;

        // If no upcoming week, default to the last week of the season
        const allWeeks = new Set<number>();
        initData.matches.forEach((m) => allWeeks.add(m.week));
        const fallbackWeek = allWeeks.size > 0
          ? Math.max(...Array.from(allWeeks))
          : null;

        const week = nextWeek ?? fallbackWeek;
        setSelectedWeek(week);
        setDefaultWeek(nextWeek);
      } catch (err) {
        console.error('Failed to load matches:', err);
        setError('Failed to load season schedule');
      } finally {
        setLoadingMatches(false);
      }
    }
    loadCurrentSeasonMatches();
  }, []);

  const handleSort = useCallback((field: SortField) => {
    if (sortField === field) {
      setSortDir(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('asc');
    }
  }, [sortField]);

  const sortedMatches = [...weekMatches].sort((a, b) => {
    if (!sortField) return 0;
    let aVal: string, bVal: string;
    switch (sortField) {
      case 'away':
        aVal = a.away_name;
        bVal = b.away_name;
        break;
      case 'home':
        aVal = a.home_name;
        bVal = b.home_name;
        break;
      case 'venue':
        aVal = a.venue.name;
        bVal = b.venue.name;
        break;
    }
    const cmp = aVal.localeCompare(bVal);
    return sortDir === 'asc' ? cmp : -cmp;
  });

  const isOffSeason = seasonStatus?.status === 'completed';
  const allWeekMatchesComplete = weekMatches.length > 0 && weekMatches.every((m) => m.state === 'complete');

  return (
    <div className="space-y-4">
      <PageHeader
        title="Matchup Analysis"
        description="Select a scheduled match to analyze team vs team performance at the venue"
      />

      {isOffSeason && (
        <Alert variant="info" title={`Season ${currentSeason} Complete`}>
          <p className="mb-2">
            {seasonStatus?.message || `Season ${currentSeason} has ended.`}
          </p>
          <p className="text-sm">
            Check back when Season {(currentSeason || 22) + 1} begins for updated matchup analysis.
            In the meantime, you can explore player stats, team performance, and historical data
            using the other pages.
          </p>
        </Alert>
      )}

      {!loadingMatches && allMatches.length === 0 && (
        <Alert variant="info" title={`No Matchups in Season ${currentSeason}`}>
          <p className="mb-2">
            There are no matchups available for Season {currentSeason}.
          </p>
          <p className="text-sm">
            This typically happens between seasons.
            Check back when the next season begins, or explore historical data from previous seasons.
          </p>
        </Alert>
      )}

      {loadingMatches && (
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner size="lg" text="Loading matchups..." />
        </div>
      )}

      {!loadingMatches && allMatches.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <select
                value={selectedWeek ?? ''}
                onChange={(e) => {
                  setSelectedWeek(Number(e.target.value));
                  setSortField(null);
                }}
                className="text-lg font-semibold bg-transparent border rounded-md px-2 py-1 cursor-pointer"
                style={{
                  color: 'var(--text-primary)',
                  borderColor: 'var(--border)',
                  backgroundColor: 'var(--card-bg)',
                }}
              >
                {weeks.map((week) => (
                  <option key={week} value={week}>
                    {week > 10 ? `Playoffs R${week - 10}` : `Week ${week}`}
                    {week === defaultWeek ? ' (Next)' : ''}
                  </option>
                ))}
              </select>
              {weekDate && (
                <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  {weekDate}
                </span>
              )}
            </div>
            <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
              {isOffSeason
                ? 'Browse completed matches'
                : `Season ${currentSeason}`}
            </span>
          </div>

          <Table>
            <TableHeader>
              <TableRow hoverable={false}>
                <TableHead
                  sortable
                  onSort={() => handleSort('away')}
                  sortDirection={sortField === 'away' ? sortDir : null}
                >
                  Away
                </TableHead>
                <TableHead className="text-center w-8">{''}</TableHead>
                <TableHead
                  sortable
                  onSort={() => handleSort('home')}
                  sortDirection={sortField === 'home' ? sortDir : null}
                >
                  Home
                </TableHead>
                <TableHead
                  sortable
                  onSort={() => handleSort('venue')}
                  sortDirection={sortField === 'venue' ? sortDir : null}
                >
                  Venue
                </TableHead>
                {allWeekMatchesComplete && (
                  <TableHead className="text-right">Score</TableHead>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedMatches.map((match) => {
                const isComplete = match.state === 'complete';
                const hasScore = isComplete && match.away_team_points != null && match.home_team_points != null;

                return (
                  <TableRow
                    key={match.match_key}
                    onClick={() => {
                      if (isComplete) {
                        router.push(`/live/${match.match_key}`);
                      } else {
                        router.push(`/matchups/${match.match_key}`);
                      }
                    }}
                  >
                    <TableCell>
                      <span className="font-medium">{match.away_name}</span>
                      {match.away_record && (
                        <span className="ml-1.5 text-xs" style={{ color: 'var(--text-muted)' }}>
                          ({match.away_record})
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-center text-xs" style={{ color: 'var(--text-muted)' }}>
                      @
                    </TableCell>
                    <TableCell>
                      <span className="font-medium">{match.home_name}</span>
                      {match.home_record && (
                        <span className="ml-1.5 text-xs" style={{ color: 'var(--text-muted)' }}>
                          ({match.home_record})
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      <span style={{ color: 'var(--text-secondary)' }}>{match.venue.name}</span>
                    </TableCell>
                    {allWeekMatchesComplete && (
                      <TableCell className="text-right">
                        {hasScore && (
                          <span className="text-sm font-semibold font-mono">
                            {match.away_team_points}-{match.home_team_points}
                          </span>
                        )}
                      </TableCell>
                    )}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>

          {error && (
            <Alert variant="error" title="Error" className="mt-4">
              {error}
            </Alert>
          )}
        </div>
      )}
    </div>
  );
}
