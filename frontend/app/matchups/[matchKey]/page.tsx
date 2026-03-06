'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import {
  MatchupAnalysis,
  TeamMachineConfidence,
  PlayerMachineConfidence,
  MachinePickFrequency,
  ScheduleMatch,
  MatchplayRatingInfo,
} from '@/lib/types';
import {
  Card,
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
import Link from 'next/link';

export default function MatchupDetailPage() {
  const params = useParams();
  const matchKey = params.matchKey as string;

  const [matchup, setMatchup] = useState<MatchupAnalysis | null>(null);
  const [match, setMatch] = useState<ScheduleMatch | null>(null);
  const [matchplayRatings, setMatchplayRatings] = useState<Record<string, MatchplayRatingInfo>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMatchup = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Get init data to find the match details
      const initData = await api.getMatchupsInit();
      const supportedSeasons = filterSupportedSeasons(initData.seasons);
      const latestSeason = supportedSeasons.length > 0
        ? Math.max(...supportedSeasons)
        : initData.current_season;
      const foundMatch = initData.matches.find((m) => m.match_key === matchKey);
      setMatch(foundMatch || null);

      if (!foundMatch) {
        setError(`Match "${matchKey}" not found in current season schedule`);
        setLoading(false);
        return;
      }

      // Try pre-computed first for scheduled matches
      let data: MatchupAnalysis;
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      // Find current week
      const upcomingWeeks = new Set<number>();
      initData.matches.forEach((m) => {
        if (m.state !== 'complete') {
          const matchDate = m.date ? new Date(m.date) : null;
          if (!matchDate || matchDate >= today) {
            upcomingWeeks.add(m.week);
          }
        }
      });
      const currentWeek = upcomingWeeks.size > 0
        ? Math.min(...Array.from(upcomingWeeks))
        : null;

      const isCurrentWeekScheduled = foundMatch.state === 'scheduled' && foundMatch.week === currentWeek;

      if (isCurrentWeekScheduled) {
        try {
          data = await api.getPrecomputedMatchup(matchKey);
        } catch {
          const seasonsToAnalyze = latestSeason
            ? [latestSeason, latestSeason - 1]
            : [23, 22];
          data = await api.getMatchupAnalysis({
            home_team: foundMatch.home_key,
            away_team: foundMatch.away_key,
            venue: foundMatch.venue.key,
            seasons: seasonsToAnalyze,
          });
        }
      } else {
        const seasonsToAnalyze = latestSeason
          ? [latestSeason, latestSeason - 1]
          : [23, 22];
        data = await api.getMatchupAnalysis({
          home_team: foundMatch.home_key,
          away_team: foundMatch.away_key,
          venue: foundMatch.venue.key,
          seasons: seasonsToAnalyze,
        });
      }

      setMatchup(data);

      // Fetch Matchplay ratings
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
  }, [matchKey]);

  useEffect(() => {
    loadMatchup();
  }, [loadMatchup]);

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

  const seasonsArray = matchup
    ? (typeof matchup.season === 'string' && matchup.season.includes('-')
      ? matchup.season.split('-').map(Number)
      : [typeof matchup.season === 'string' ? parseInt(matchup.season) : matchup.season])
    : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/matchups"
          className="text-sm font-medium hover:underline"
          style={{ color: 'var(--text-link)' }}
        >
          &larr; All Matchups
        </Link>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner size="lg" text="Analyzing matchup..." />
        </div>
      )}

      {error && (
        <Alert variant="error" title="Error">
          {error}
        </Alert>
      )}

      {matchup && (
        <div className="space-y-6">
          {/* Matchup Header */}
          <Card>
            <Card.Content>
              <h2 className="text-2xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
                {matchup.away_team_name} @ {matchup.home_team_name}
              </h2>
              <p style={{ color: 'var(--text-secondary)' }}>
                Venue: {matchup.venue_name} | Season{typeof matchup.season === 'string' && matchup.season.includes('-') ? 's' : ''}: {matchup.season}
                {match?.week ? ` | Week ${match.week}` : ''}
                {match?.date ? ` | ${match.date}` : ''}
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
                  className="flex items-center justify-between p-2 rounded text-sm"
                  style={{ backgroundColor: 'var(--card-bg-secondary)' }}
                >
                  <span className="font-medium" style={{ color: 'var(--text-primary)' }}>
                    {typeof machine === 'string' ? machine : machine.name}
                  </span>
                  <span className="text-xs ml-2" style={{ color: 'var(--text-muted)' }}>
                    {typeof machine === 'string' ? '' : machine.key}
                  </span>
                </div>
              ))}
            </div>
          </Collapsible>

          {/* Machine Pick Predictions - Doubles */}
          <div>
            <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
              Doubles Pick Predictions
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <MachinePredictionCard
                teamKey={match?.away_key || matchup.away_team_key || ''}
                teamName={matchup.away_team_name}
                roundNum={1}
                venueKey={matchup.venue_key}
                seasons={seasonsArray}
              />
              <MachinePredictionCard
                teamKey={match?.home_key || matchup.home_team_key || ''}
                teamName={matchup.home_team_name}
                roundNum={4}
                venueKey={matchup.venue_key}
                seasons={seasonsArray}
              />
            </div>
          </div>

          {/* Machine Pick Predictions - Singles */}
          <div>
            <h3 className="text-lg font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
              Singles Pick Predictions
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <MachinePredictionCard
                teamKey={match?.home_key || matchup.home_team_key || ''}
                teamName={matchup.home_team_name}
                roundNum={2}
                venueKey={matchup.venue_key}
                seasons={seasonsArray}
              />
              <MachinePredictionCard
                teamKey={match?.away_key || matchup.away_team_key || ''}
                teamName={matchup.away_team_name}
                roundNum={3}
                venueKey={matchup.venue_key}
                seasons={seasonsArray}
              />
            </div>
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
                <Card>
                  <Card.Header>
                    <Card.Title>Expected Scores (Team Average)</Card.Title>
                    <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                      Based on all team members&apos; performance at this venue
                    </p>
                  </Card.Header>
                  <Card.Content>
                    <TeamConfidenceTable
                      confidences={matchup.home_team_machine_confidence}
                      formatScore={formatScore}
                    />
                  </Card.Content>
                </Card>

                <Collapsible
                  title="Doubles Pick History"
                  badge={
                    <Badge variant="default">
                      {matchup.home_team_pick_frequency.length}
                    </Badge>
                  }
                >
                  <p className="text-sm mb-3" style={{ color: 'var(--text-muted)' }}>
                    Machines this team has historically picked in doubles rounds
                  </p>
                  <MachinePickTable picks={matchup.home_team_pick_frequency} />
                </Collapsible>

                <Collapsible
                  title="Singles Pick History"
                  badge={
                    <Badge variant="default">
                      {matchup.home_team_singles_pick_frequency?.length || 0}
                    </Badge>
                  }
                >
                  <p className="text-sm mb-3" style={{ color: 'var(--text-muted)' }}>
                    Machines this team has historically picked in singles rounds
                  </p>
                  <MachinePickTable picks={matchup.home_team_singles_pick_frequency || []} />
                </Collapsible>

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

                <Collapsible
                  title="Roster Player Expected Scores"
                  badge={
                    <Badge variant="info">Requires 5+ games</Badge>
                  }
                >
                  <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
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
                <Card>
                  <Card.Header>
                    <Card.Title>Expected Scores (Team Average)</Card.Title>
                    <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                      Based on all team members&apos; performance at this venue
                    </p>
                  </Card.Header>
                  <Card.Content>
                    <TeamConfidenceTable
                      confidences={matchup.away_team_machine_confidence}
                      formatScore={formatScore}
                    />
                  </Card.Content>
                </Card>

                <Collapsible
                  title="Doubles Pick History"
                  badge={
                    <Badge variant="default">
                      {matchup.away_team_pick_frequency.length}
                    </Badge>
                  }
                >
                  <p className="text-sm mb-3" style={{ color: 'var(--text-muted)' }}>
                    Machines this team has historically picked in doubles rounds
                  </p>
                  <MachinePickTable picks={matchup.away_team_pick_frequency} />
                </Collapsible>

                <Collapsible
                  title="Singles Pick History"
                  badge={
                    <Badge variant="default">
                      {matchup.away_team_singles_pick_frequency?.length || 0}
                    </Badge>
                  }
                >
                  <p className="text-sm mb-3" style={{ color: 'var(--text-muted)' }}>
                    Machines this team has historically picked in singles rounds
                  </p>
                  <MachinePickTable picks={matchup.away_team_singles_pick_frequency || []} />
                </Collapsible>

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

                <Collapsible
                  title="Roster Player Expected Scores"
                  badge={
                    <Badge variant="info">Requires 5+ games</Badge>
                  }
                >
                  <p className="text-sm mb-4" style={{ color: 'var(--text-secondary)' }}>
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
            <Table.Cell className="text-right text-xs">
              <span style={{ color: 'var(--text-secondary)' }}>
                {conf.confidence_interval
                  ? `${formatScore(conf.confidence_interval.lower_bound)} - ${formatScore(conf.confidence_interval.upper_bound)}`
                  : 'N/A'}
              </span>
            </Table.Cell>
            <Table.Cell className="text-right text-xs">
              <span style={{ color: 'var(--text-muted)' }}>
                n={conf.confidence_interval?.sample_size || 0}
              </span>
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
            className="border rounded-lg p-4 transition-colors"
            style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg)' }}
          >
            <div className="flex items-center justify-between mb-3">
              <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>{pref.player_name}</p>
              {mpRating && (
                <a
                  href={mpRating.profile_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs hover:underline"
                  style={{ color: 'var(--text-link)' }}
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
                  <span style={{ color: 'var(--text-secondary)' }}>
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
                    className="text-xs hover:underline"
                    style={{ color: 'var(--text-link)' }}
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
                      <Table.Cell className="text-xs text-right py-2">
                        <span style={{ color: 'var(--text-secondary)' }}>
                          {conf.confidence_interval
                            ? `${formatScore(conf.confidence_interval.lower_bound)}-${formatScore(conf.confidence_interval.upper_bound)}`
                            : 'N/A'}
                        </span>
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
