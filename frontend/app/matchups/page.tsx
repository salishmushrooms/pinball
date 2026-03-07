'use client';

import { useState, useEffect, Suspense } from 'react';
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
} from '@/components/ui';
import { filterSupportedSeasons, cn } from '@/lib/utils';

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
  const [seasonStatus, setSeasonStatus] = useState<SeasonStatus | null>(null);
  const [matches, setMatches] = useState<ScheduleMatch[]>([]);
  const [loadingMatches, setLoadingMatches] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
            <h2
              className="text-lg font-semibold"
              style={{ color: 'var(--text-primary)' }}
            >
              {currentWeek !== null ? `Week ${currentWeek} Matchups` : 'All Matchups'}
            </h2>
            <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
              {isOffSeason
                ? 'Browse completed matches'
                : `Season ${currentSeason} & ${(currentSeason || 23) - 1} data`}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {matches.map((match) => (
              <button
                key={match.match_key}
                onClick={() => router.push(`/matchups/${match.match_key}`)}
                className={cn(
                  'border rounded-lg p-4 text-left transition-all cursor-pointer hover:shadow-md',
                )}
                style={{
                  borderColor: 'var(--border)',
                  borderWidth: '1px',
                  backgroundColor: 'var(--card-bg)',
                }}
              >
                {/* Week & Date */}
                <div className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>
                  Week {match.week}{match.date ? ` \u2022 ${match.date}` : ''}
                </div>

                {/* Teams */}
                <div className="space-y-0.5">
                  <div className="font-semibold text-base" style={{ color: 'var(--text-primary)' }}>
                    {match.away_name}
                  </div>
                  <div className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>@</div>
                  <div className="font-semibold text-base" style={{ color: 'var(--text-primary)' }}>
                    {match.home_name}
                  </div>
                </div>

                {/* Venue */}
                <div className="mt-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                  {match.venue.name}
                </div>
              </button>
            ))}
          </div>

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
