'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import {
  MatchupAnalysis,
  TeamMachineConfidence,
  PlayerMachineConfidence,
  MachinePickFrequency,
  ScheduleMatch,
  MatchplayRatingInfo,
  SeasonStatus,
} from '@/lib/types';
import {
  Card,
  PageHeader,
  Select,
  Button,
  Alert,
  Badge,
  Table,
  Tabs,
  Collapsible,
  EmptyState,
  LoadingSpinner,
} from '@/components/ui';
import { MachinePredictionCard } from '@/components/MachinePredictionCard';
import { filterSupportedSeasons } from '@/lib/utils';

export default function MatchupsPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <MatchupsPageContent />
    </Suspense>
  );
}

function MatchupsPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [currentSeason, setCurrentSeason] = useState<number | null>(null);
  const [currentWeek, setCurrentWeek] = useState<number | null>(null);
  const [seasonStatus, setSeasonStatus] = useState<SeasonStatus | null>(null);
  const [matches, setMatches] = useState<ScheduleMatch[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<string>('');
  const [matchup, setMatchup] = useState<MatchupAnalysis | null>(null);
  const [matchplayRatings, setMatchplayRatings] = useState<Record<string, MatchplayRatingInfo>>({});
  const [loading, setLoading] = useState(false);
  const [loadingMatches, setLoadingMatches] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [initialMatchFromUrl, setInitialMatchFromUrl] = useState<string | null>(null);

  // Read match key from URL on initial load
  useEffect(() => {
    const matchFromUrl = searchParams.get('match');
    if (matchFromUrl) {
      setInitialMatchFromUrl(matchFromUrl);
    }
  }, [searchParams]);

  // Load current season and matches on mount using combined endpoint
  useEffect(() => {
    async function loadCurrentSeasonMatches() {
      setLoadingMatches(true);
      try {
        // Single API call for all initialization data
        const initData = await api.getMatchupsInit();

        // Filter to supported seasons
        const supportedSeasons = filterSupportedSeasons(initData.seasons);
        const latestSeason = supportedSeasons.length > 0
          ? Math.max(...supportedSeasons)
          : initData.current_season;

        setCurrentSeason(latestSeason);
        setSeasonStatus(initData.season_status);

        // Filter to only show matches from the next incomplete week
        const allMatches = initData.matches;

        // Find the first week that has incomplete matches (or week 1 if preseason)
        const incompleteWeeks = new Set<number>();
        allMatches.forEach((match) => {
          if (match.state !== 'complete') {
            incompleteWeeks.add(match.week);
          }
        });

        // Get the lowest incomplete week number (or show all if all complete)
        const nextWeek = incompleteWeeks.size > 0
          ? Math.min(...Array.from(incompleteWeeks))
          : null;

        setCurrentWeek(nextWeek);

        // Filter to only show matches from the next incomplete week
        const filteredMatches = nextWeek !== null
          ? allMatches.filter((match) => match.week === nextWeek)
          : allMatches; // Show all if season is complete (for historical analysis)

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

  // Update URL with match key
  const updateUrlWithMatch = useCallback((matchKey: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set('match', matchKey);
    router.replace(`/matchups?${params.toString()}`, { scroll: false });
  }, [searchParams, router]);

  // Load matchup analysis
  const handleAnalyzeMatchup = useCallback(async (matchKeyOverride?: string) => {
    const matchKey = matchKeyOverride || selectedMatch;

    if (!matchKey) {
      setError('Please select a match');
      return;
    }

    const match = matches.find((m) => m.match_key === matchKey);
    if (!match) {
      setError('Selected match not found');
      return;
    }

    // If using override, also update the selected match state
    if (matchKeyOverride && matchKeyOverride !== selectedMatch) {
      setSelectedMatch(matchKeyOverride);
    }

    setLoading(true);
    setError(null);
    setMatchup(null);

    try {
      let data: MatchupAnalysis;

      // For current week scheduled matches, try pre-computed endpoint first
      const isCurrentWeekScheduled = match.state === 'scheduled' && match.week === currentWeek;

      if (isCurrentWeekScheduled) {
        try {
          // Use pre-computed endpoint for faster response
          data = await api.getPrecomputedMatchup(matchKey);
        } catch {
          // Fall back to on-demand calculation if pre-computed not available
          console.log('Pre-computed matchup not available, calculating on-demand');
          const seasonsToAnalyze = currentSeason
            ? [currentSeason, currentSeason - 1]
            : [23, 22];

          data = await api.getMatchupAnalysis({
            home_team: match.home_key,
            away_team: match.away_key,
            venue: match.venue.key,
            seasons: seasonsToAnalyze,
          });
        }
      } else {
        // On-demand for completed matches or historical analysis
        const seasonsToAnalyze = currentSeason
          ? [currentSeason, currentSeason - 1]
          : [23, 22];

        data = await api.getMatchupAnalysis({
          home_team: match.home_key,
          away_team: match.away_key,
          venue: match.venue.key,
          seasons: seasonsToAnalyze,
        });
      }

      setMatchup(data);

      // Update URL with the analyzed match
      updateUrlWithMatch(matchKey);

      // Fetch Matchplay ratings for all players in both teams
      const allPlayerKeys = new Set<string>();
      data.home_team_player_preferences?.forEach((p) => allPlayerKeys.add(p.player_key));
      data.away_team_player_preferences?.forEach((p) => allPlayerKeys.add(p.player_key));
      data.home_team_player_confidence?.forEach((p) => allPlayerKeys.add(p.player_key));
      data.away_team_player_confidence?.forEach((p) => allPlayerKeys.add(p.player_key));

      if (allPlayerKeys.size > 0) {
        try {
          const ratingsResponse = await api.getMatchplayRatings(Array.from(allPlayerKeys));
          setMatchplayRatings(ratingsResponse.ratings || {});
        } catch (ratingsErr) {
          console.warn('Failed to fetch Matchplay ratings:', ratingsErr);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze matchup');
    } finally {
      setLoading(false);
    }
  }, [selectedMatch, matches, currentSeason, updateUrlWithMatch]);

  // Auto-analyze match from URL after matches are loaded
  useEffect(() => {
    if (!loadingMatches && initialMatchFromUrl && matches.length > 0 && !matchup) {
      const matchExists = matches.find((m) => m.match_key === initialMatchFromUrl);
      if (matchExists) {
        handleAnalyzeMatchup(initialMatchFromUrl);
      }
      // Clear the initial URL match so we don't re-trigger
      setInitialMatchFromUrl(null);
    }
  }, [loadingMatches, initialMatchFromUrl, matches, matchup, handleAnalyzeMatchup]);

  const formatScore = (score: number): string => {
    if (score >= 1_000_000_000) {
      return `${(score / 1_000_000_000).toFixed(1)}B`;
    } else if (score >= 1_000_000) {
      return `${(score / 1_000_000).toFixed(1)}M`;
    } else if (score >= 1_000) {
      return `${(score / 1_000).toFixed(1)}K`;
    }
    return score.toString();
  };

  // Check if season is completed (off-season)
  const isOffSeason = seasonStatus?.status === 'completed';
  const isUpcoming = seasonStatus?.status === 'upcoming';

  return (
    <div className="space-y-6">
      <PageHeader
        title="Matchup Analysis"
        description="Select a scheduled match to analyze team vs team performance at the venue"
      />

      {/* Off-Season Message */}
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

      {/* Upcoming Season Message */}
      {isUpcoming && (
        <Alert variant="info" title={`Season ${currentSeason} Coming Soon`}>
          <p className="mb-2">
            {seasonStatus?.message || `Season ${currentSeason} hasn't started yet.`}
          </p>
          <p className="text-sm">
            Matchup analysis will be available once the season begins.
            You can still browse historical data from previous seasons.
          </p>
        </Alert>
      )}

      {/* No Matches Available */}
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

      {/* Selection Form */}
      {!loadingMatches && matches.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>
              {currentWeek !== null
                ? `Week ${currentWeek} Matchups`
                : 'Select Match'}
            </Card.Title>
            <p className="text-sm text-gray-500 mt-1">
              {isOffSeason
                ? 'Browse completed matches from the season'
                : `Analysis uses data from Season ${currentSeason} and ${(currentSeason || 23) - 1}`}
            </p>
          </Card.Header>
          <Card.Content>
            <Select
              label={currentWeek !== null ? `Week ${currentWeek} Matches` : 'Match'}
              value={selectedMatch}
              onChange={(e) => setSelectedMatch(e.target.value)}
              disabled={loadingMatches}
              options={[
                { value: '', label: 'Select a match' },
                ...matches.map((match) => ({
                  value: match.match_key,
                  label: `${match.away_name} @ ${match.home_name} (${match.venue.name})`,
                })),
              ]}
            />

          <div className="mt-6">
            <Button
              onClick={() => handleAnalyzeMatchup()}
              disabled={loading || !selectedMatch}
              variant="primary"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <LoadingSpinner size="sm" />
                  Analyzing...
                </span>
              ) : (
                'Analyze Matchup'
              )}
            </Button>
          </div>

          {error && (
            <Alert variant="error" title="Error" className="mt-4">
              {error}
            </Alert>
          )}
        </Card.Content>
      </Card>
      )}

      {/* Matchup Results */}
      {matchup && (
        <div className="space-y-6">
          {/* Matchup Header */}
          <Card>
            <Card.Content>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                {matchup.home_team_name} vs {matchup.away_team_name}
              </h2>
              <p className="text-gray-600">
                Venue: {matchup.venue_name} | Season{typeof matchup.season === 'string' && matchup.season.includes('-') ? 's' : ''}: {matchup.season}
              </p>
            </Card.Content>
          </Card>

          {/* Available Machines - Collapsible */}
          <Collapsible
            title="Available Machines"
            badge={
              <Badge variant="info">
                {matchup.available_machines.length}
              </Badge>
            }
            defaultOpen={false}
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {(matchup.available_machines_info || matchup.available_machines.map(k => ({ key: k, name: k }))).map((machine) => (
                <div
                  key={typeof machine === 'string' ? machine : machine.key}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm"
                >
                  <span className="font-medium text-gray-900">
                    {typeof machine === 'string' ? machine : machine.name}
                  </span>
                  <span className="text-xs text-gray-500 ml-2">
                    {typeof machine === 'string' ? '' : machine.key}
                  </span>
                </div>
              ))}
            </div>
          </Collapsible>

          {/* Machine Pick Predictions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <MachinePredictionCard
              teamKey={matches.find((m) => m.match_key === selectedMatch)?.away_key || matchup.away_team_key || ''}
              teamName={matchup.away_team_name}
              roundNum={1}
              venueKey={matchup.venue_key}
              seasons={typeof matchup.season === 'string' && matchup.season.includes('-') ? matchup.season.split('-').map(Number) : [typeof matchup.season === 'string' ? parseInt(matchup.season) : matchup.season]}
            />
            <MachinePredictionCard
              teamKey={matches.find((m) => m.match_key === selectedMatch)?.home_key || matchup.home_team_key || ''}
              teamName={matchup.home_team_name}
              roundNum={4}
              venueKey={matchup.venue_key}
              seasons={typeof matchup.season === 'string' && matchup.season.includes('-') ? matchup.season.split('-').map(Number) : [typeof matchup.season === 'string' ? parseInt(matchup.season) : matchup.season]}
            />
          </div>

          {/* Tab Navigation for Teams */}
          <Tabs defaultValue="home">
            <Tabs.List className="w-full md:w-auto">
              <Tabs.Trigger value="home">{matchup.home_team_name}</Tabs.Trigger>
              <Tabs.Trigger value="away">{matchup.away_team_name}</Tabs.Trigger>
            </Tabs.List>

            {/* Home Team Tab */}
            <Tabs.Content value="home">
              <div className="space-y-4">
                {/* Team Expected Scores - Always visible */}
                <Card>
                  <Card.Header>
                    <Card.Title>Expected Scores (Team Average)</Card.Title>
                    <p className="text-sm text-gray-500 mt-1">
                      Based on all team members' performance at this venue
                    </p>
                  </Card.Header>
                  <Card.Content>
                    <TeamConfidenceTable
                      confidences={matchup.home_team_machine_confidence}
                      formatScore={formatScore}
                    />
                  </Card.Content>
                </Card>

                {/* Machine Pick Frequency - Collapsible */}
                <Collapsible
                  title="Team Pick History"
                  badge={
                    <Badge variant="default">
                      {matchup.home_team_pick_frequency.length}
                    </Badge>
                  }
                >
                  <p className="text-sm text-gray-500 mb-3">
                    Machines this team has historically picked in doubles rounds
                  </p>
                  <MachinePickTable picks={matchup.home_team_pick_frequency} />
                </Collapsible>

                {/* Player Preferences - Collapsible */}
                <Collapsible
                  title="Roster Player Preferences"
                  badge={
                    <Badge variant="default">
                      {matchup.home_team_player_preferences.length} players
                    </Badge>
                  }
                >
                  <PlayerPreferencesGrid
                    preferences={matchup.home_team_player_preferences}
                    matchplayRatings={matchplayRatings}
                  />
                </Collapsible>

                {/* Player-Specific Expected Scores - Collapsible */}
                <Collapsible
                  title="Roster Player Expected Scores"
                  badge={
                    <Badge variant="info">Requires 5+ games</Badge>
                  }
                >
                  <p className="text-sm text-gray-600 mb-4">
                    Only showing roster players with 5 or more games on each machine for
                    statistical confidence (95% confidence interval).
                  </p>
                  <PlayerConfidenceGrid
                    confidences={matchup.home_team_player_confidence}
                    formatScore={formatScore}
                    matchplayRatings={matchplayRatings}
                  />
                </Collapsible>
              </div>
            </Tabs.Content>

            {/* Away Team Tab */}
            <Tabs.Content value="away">
              <div className="space-y-4">
                {/* Team Expected Scores - Always visible */}
                <Card>
                  <Card.Header>
                    <Card.Title>Expected Scores (Team Average)</Card.Title>
                    <p className="text-sm text-gray-500 mt-1">
                      Based on all team members' performance at this venue
                    </p>
                  </Card.Header>
                  <Card.Content>
                    <TeamConfidenceTable
                      confidences={matchup.away_team_machine_confidence}
                      formatScore={formatScore}
                    />
                  </Card.Content>
                </Card>

                {/* Machine Pick Frequency - Collapsible */}
                <Collapsible
                  title="Team Pick History"
                  badge={
                    <Badge variant="default">
                      {matchup.away_team_pick_frequency.length}
                    </Badge>
                  }
                >
                  <p className="text-sm text-gray-500 mb-3">
                    Machines this team has historically picked in doubles rounds
                  </p>
                  <MachinePickTable picks={matchup.away_team_pick_frequency} />
                </Collapsible>

                {/* Player Preferences - Collapsible */}
                <Collapsible
                  title="Roster Player Preferences"
                  badge={
                    <Badge variant="default">
                      {matchup.away_team_player_preferences.length} players
                    </Badge>
                  }
                >
                  <PlayerPreferencesGrid
                    preferences={matchup.away_team_player_preferences}
                    matchplayRatings={matchplayRatings}
                  />
                </Collapsible>

                {/* Player-Specific Expected Scores - Collapsible */}
                <Collapsible
                  title="Roster Player Expected Scores"
                  badge={
                    <Badge variant="info">Requires 5+ games</Badge>
                  }
                >
                  <p className="text-sm text-gray-600 mb-4">
                    Only showing roster players with 5 or more games on each machine for
                    statistical confidence (95% confidence interval).
                  </p>
                  <PlayerConfidenceGrid
                    confidences={matchup.away_team_player_confidence}
                    formatScore={formatScore}
                    matchplayRatings={matchplayRatings}
                  />
                </Collapsible>
              </div>
            </Tabs.Content>
          </Tabs>
        </div>
      )}
    </div>
  );
}

// Component for machine pick frequency table
function MachinePickTable({ picks }: { picks: MachinePickFrequency[] }) {
  if (picks.length === 0) {
    return <EmptyState title="No pick data available" />;
  }

  return (
    <Table>
      <Table.Header>
        <Table.Row>
          <Table.Head>Machine</Table.Head>
          <Table.Head className="text-right">Times Picked</Table.Head>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {picks.slice(0, 10).map((pick) => (
          <Table.Row key={pick.machine_key}>
            <Table.Cell>{pick.machine_name}</Table.Cell>
            <Table.Cell className="text-right font-medium">
              {pick.times_picked}
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table>
  );
}

// Component for team confidence interval table
function TeamConfidenceTable({
  confidences,
  formatScore,
}: {
  confidences: TeamMachineConfidence[];
  formatScore: (score: number) => string;
}) {
  const withData = confidences.filter((c) => !c.insufficient_data);

  if (withData.length === 0) {
    return <EmptyState title="Insufficient data for predictions" />;
  }

  return (
    <Table>
      <Table.Header>
        <Table.Row>
          <Table.Head>Machine</Table.Head>
          <Table.Head className="text-right">Expected Score</Table.Head>
          <Table.Head className="text-right">95% Range</Table.Head>
          <Table.Head className="text-right">Sample</Table.Head>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {withData.slice(0, 10).map((conf) => (
          <Table.Row key={conf.machine_key}>
            <Table.Cell className="font-medium">{conf.machine_name}</Table.Cell>
            <Table.Cell className="text-right font-semibold text-blue-600">
              {conf.confidence_interval
                ? formatScore(conf.confidence_interval.mean)
                : 'N/A'}
            </Table.Cell>
            <Table.Cell className="text-right text-gray-600 text-xs">
              {conf.confidence_interval
                ? `${formatScore(conf.confidence_interval.lower_bound)} - ${formatScore(conf.confidence_interval.upper_bound)}`
                : 'N/A'}
            </Table.Cell>
            <Table.Cell className="text-right text-gray-500 text-xs">
              n={conf.confidence_interval?.sample_size || 0}
            </Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table>
  );
}

// Component for player preferences grid
function PlayerPreferencesGrid({
  preferences,
  matchplayRatings,
}: {
  preferences: { player_key: string; player_name: string; top_machines: MachinePickFrequency[] }[];
  matchplayRatings: Record<string, MatchplayRatingInfo>;
}) {
  if (preferences.length === 0) {
    return <EmptyState title="No preference data available" />;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {preferences.map((pref) => {
        const mpRating = matchplayRatings[pref.player_key];
        return (
          <div
            key={pref.player_key}
            className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center justify-between mb-3">
              <p className="font-semibold text-gray-900">{pref.player_name}</p>
              {mpRating && (
                <a
                  href={mpRating.profile_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:text-blue-800"
                  title={`Matchplay: ${mpRating.matchplay_name}`}
                >
                  MP: {mpRating.rating ?? '—'}
                </a>
              )}
            </div>
            <div className="space-y-2">
              {pref.top_machines.slice(0, 5).map((machine, idx) => (
                <div
                  key={machine.machine_key}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-gray-700">
                    {idx + 1}. {machine.machine_name}
                  </span>
                  <Badge variant="default" className="text-xs">
                    {machine.times_picked}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Component for player confidence grid
function PlayerConfidenceGrid({
  confidences,
  formatScore,
  matchplayRatings,
}: {
  confidences: PlayerMachineConfidence[];
  formatScore: (score: number) => string;
  matchplayRatings: Record<string, MatchplayRatingInfo>;
}) {
  const withData = confidences.filter((c) => !c.insufficient_data);

  if (withData.length === 0) {
    return (
      <EmptyState title="Insufficient data for player predictions" description="Players need 5+ games on a machine to generate confidence intervals." />
    );
  }

  // Group by player
  const byPlayer: { [key: string]: PlayerMachineConfidence[] } = {};
  withData.forEach((conf) => {
    if (!byPlayer[conf.player_key]) {
      byPlayer[conf.player_key] = [];
    }
    byPlayer[conf.player_key].push(conf);
  });

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {Object.entries(byPlayer).map(([playerKey, confs]) => {
        const mpRating = matchplayRatings[playerKey];
        return (
          <Card key={playerKey} className="shadow-sm">
            <Card.Header>
              <div className="flex items-center justify-between">
                <Card.Title className="text-base">
                  {confs[0].player_name}
                  <Badge variant="info" className="ml-2">
                    {confs.length} machines
                  </Badge>
                </Card.Title>
                {mpRating && (
                  <a
                    href={mpRating.profile_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:text-blue-800"
                    title={`Matchplay: ${mpRating.matchplay_name}`}
                  >
                    MP: {mpRating.rating ?? '—'}
                  </a>
                )}
              </div>
            </Card.Header>
            <Card.Content>
              <Table>
                <Table.Header>
                  <Table.Row>
                    <Table.Head className="text-xs">Machine</Table.Head>
                    <Table.Head className="text-xs text-right">Expected</Table.Head>
                    <Table.Head className="text-xs text-right">Range</Table.Head>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {confs.map((conf) => (
                    <Table.Row key={conf.machine_key}>
                      <Table.Cell className="text-xs py-2">
                        {conf.machine_name}
                      </Table.Cell>
                      <Table.Cell className="text-xs text-right font-semibold text-blue-600 py-2">
                        {conf.confidence_interval
                          ? formatScore(conf.confidence_interval.mean)
                          : 'N/A'}
                      </Table.Cell>
                      <Table.Cell className="text-xs text-right text-gray-600 py-2">
                        {conf.confidence_interval
                          ? `${formatScore(conf.confidence_interval.lower_bound)}-${formatScore(conf.confidence_interval.upper_bound)}`
                          : 'N/A'}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table>
            </Card.Content>
          </Card>
        );
      })}
    </div>
  );
}
