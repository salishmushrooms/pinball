'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
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
  const [currentWeek, setCurrentWeek] = useState<number | null>(null);
  const [weekDate, setWeekDate] = useState<string | null>(null);
  const [seasonStatus, setSeasonStatus] = useState<SeasonStatus | null>(null);
  const [matches, setMatches] = useState<ScheduleMatch[]>([]);
  const [loadingMatches, setLoadingMatches] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>('asc');

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

        const allMatches = initData.matches;
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const upcomingWeeks = new Set<number>();
        allMatches.forEach((match) => {
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

        setCurrentWeek(nextWeek);

        const filteredMatches = nextWeek !== null
          ? allMatches.filter((match) => match.week === nextWeek)
          : allMatches;

        // Extract date from first match of the week
        if (filteredMatches.length > 0 && filteredMatches[0].date) {
          setWeekDate(filteredMatches[0].date);
        }

        setMatches(filteredMatches);
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

  const sortedMatches = [...matches].sort((a, b) => {
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

      {!loadingMatches && matches.length === 0 && (
        <Alert variant="info" title={`No Remaining Matchups in Season ${currentSeason}`}>
          <p className="mb-2">
            There are no scheduled matchups available for Season {currentSeason}.
          </p>
          <p className="text-sm">
            This typically happens between seasons or after all matches have been completed.
            Check back when the next season begins, or explore historical data from previous seasons.
          </p>
        </Alert>
      )}

      {loadingMatches && (
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner size="lg" text="Loading matchups..." />
        </div>
      )}

      {!loadingMatches && matches.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2
                className="text-lg font-semibold"
                style={{ color: 'var(--text-primary)' }}
              >
                {currentWeek !== null ? `Week ${currentWeek}` : 'All Matchups'}
              </h2>
              {weekDate && (
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                  {weekDate}
                </p>
              )}
            </div>
            <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
              {isOffSeason
                ? 'Browse completed matches'
                : `Season ${currentSeason} & ${(currentSeason || 23) - 1} data`}
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
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedMatches.map((match) => (
                <TableRow
                  key={match.match_key}
                  onClick={() => router.push(`/matchups/${match.match_key}`)}
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
                </TableRow>
              ))}
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
