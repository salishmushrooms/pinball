'use client';

import React, { useState, useEffect, useCallback } from 'react';
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
    <div className="space-y-4">
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
        <div className="space-y-4">
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
                <MachineScoreRanges
                  teamConfidences={matchup.home_team_machine_confidence}
                  playerConfidences={matchup.home_team_player_confidence}
                  formatScore={formatScore}
                  matchplayRatings={matchplayRatings}
                />

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
              </div>
            </Tabs.Content>

            {/* Away Team Tab */}
            <Tabs.Content value="away">
              <div className="space-y-4">
                <MachineScoreRanges
                  teamConfidences={matchup.away_team_machine_confidence}
                  playerConfidences={matchup.away_team_player_confidence}
                  formatScore={formatScore}
                  matchplayRatings={matchplayRatings}
                />

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
        {[...picks].sort((a, b) => b.times_picked - a.times_picked).slice(0, 10).map((pick) => (
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

// Integrated component: team score ranges with per-player breakdowns
function MachineScoreRanges({
  teamConfidences,
  playerConfidences,
  formatScore,
  matchplayRatings,
}: {
  teamConfidences: TeamMachineConfidence[];
  playerConfidences: PlayerMachineConfidence[];
  formatScore: (score: number) => string;
  matchplayRatings: Record<string, MatchplayRatingInfo>;
}) {
  const [expandedMachines, setExpandedMachines] = useState<Set<string>>(new Set());

  const teamWithData = teamConfidences.filter((c) => !c.insufficient_data);

  // Group player data by machine
  const playersByMachine: Record<string, PlayerMachineConfidence[]> = {};
  playerConfidences
    .filter((c) => !c.insufficient_data)
    .forEach((conf) => {
      if (!playersByMachine[conf.machine_key]) {
        playersByMachine[conf.machine_key] = [];
      }
      playersByMachine[conf.machine_key].push(conf);
    });

  if (teamWithData.length === 0) {
    return (
      <Card>
        <Card.Header>
          <Card.Title>Score Ranges</Card.Title>
        </Card.Header>
        <Card.Content>
          <EmptyState title="Insufficient data for score ranges" />
        </Card.Content>
      </Card>
    );
  }

  const toggleMachine = (machineKey: string) => {
    setExpandedMachines((prev) => {
      const next = new Set(prev);
      if (next.has(machineKey)) {
        next.delete(machineKey);
      } else {
        next.add(machineKey);
      }
      return next;
    });
  };

  return (
    <Card>
      <Card.Header>
        <Card.Title>Score Ranges</Card.Title>
        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
          25th-75th percentile range. Click a machine to see player breakdowns.
        </p>
      </Card.Header>
      <Card.Content>
        <Table>
          <Table.Header>
            <Table.Row>
              <Table.Head>Machine</Table.Head>
              <Table.Head className="text-right">25th</Table.Head>
              <Table.Head className="text-right">Median</Table.Head>
              <Table.Head className="text-right">75th</Table.Head>
              <Table.Head className="text-right">Win%</Table.Head>
              <Table.Head className="text-right">n</Table.Head>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {teamWithData.slice(0, 10).map((conf) => {
              const players = playersByMachine[conf.machine_key] || [];
              const isExpanded = expandedMachines.has(conf.machine_key);

              return (
                <React.Fragment key={conf.machine_key}>
                  <Table.Row
                    className={players.length > 0 ? 'cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800' : ''}
                    onClick={() => players.length > 0 && toggleMachine(conf.machine_key)}
                  >
                    <Table.Cell className="font-medium">
                      <span className="flex items-center gap-1">
                        {players.length > 0 && (
                          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            {isExpanded ? '▼' : '▶'}
                          </span>
                        )}
                        {conf.machine_name}
                      </span>
                    </Table.Cell>
                    <Table.Cell className="text-right text-xs">
                      <span style={{ color: 'var(--text-secondary)' }}>
                        {conf.confidence_interval
                          ? formatScore(conf.confidence_interval.p25)
                          : 'N/A'}
                      </span>
                    </Table.Cell>
                    <Table.Cell className="text-right font-semibold text-blue-600">
                      {conf.confidence_interval
                        ? formatScore(conf.confidence_interval.median)
                        : 'N/A'}
                    </Table.Cell>
                    <Table.Cell className="text-right text-xs">
                      <span style={{ color: 'var(--text-secondary)' }}>
                        {conf.confidence_interval
                          ? formatScore(conf.confidence_interval.p75)
                          : 'N/A'}
                      </span>
                    </Table.Cell>
                    <Table.Cell className="text-right text-xs">
                      <span style={{ color: 'var(--text-muted)' }}>—</span>
                    </Table.Cell>
                    <Table.Cell className="text-right text-xs">
                      <span style={{ color: 'var(--text-muted)' }}>
                        {conf.confidence_interval?.sample_size || 0}
                      </span>
                    </Table.Cell>
                  </Table.Row>
                  {isExpanded && players.map((player) => {
                    const mpRating = matchplayRatings[player.player_key];
                    return (
                      <Table.Row
                        key={`${conf.machine_key}-${player.player_key}`}
                        style={{ backgroundColor: 'var(--card-bg-secondary)' }}
                      >
                        <Table.Cell className="text-xs pl-8">
                          <span className="flex items-center gap-1">
                            {mpRating ? (
                              <a
                                href={mpRating.profile_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="hover:underline"
                                style={{ color: 'var(--text-link)' }}
                                onClick={(e) => e.stopPropagation()}
                              >
                                {player.player_name}
                              </a>
                            ) : (
                              <span style={{ color: 'var(--text-secondary)' }}>
                                {player.player_name}
                              </span>
                            )}
                          </span>
                        </Table.Cell>
                        <Table.Cell className="text-right text-xs">
                          <span style={{ color: 'var(--text-secondary)' }}>
                            {player.confidence_interval
                              ? formatScore(player.confidence_interval.p25)
                              : '—'}
                          </span>
                        </Table.Cell>
                        <Table.Cell className="text-right text-xs font-medium" style={{ color: 'var(--text-primary)' }}>
                          {player.confidence_interval
                            ? formatScore(player.confidence_interval.median)
                            : '—'}
                        </Table.Cell>
                        <Table.Cell className="text-right text-xs">
                          <span style={{ color: 'var(--text-secondary)' }}>
                            {player.confidence_interval
                              ? formatScore(player.confidence_interval.p75)
                              : '—'}
                          </span>
                        </Table.Cell>
                        <Table.Cell className="text-right text-xs">
                          {player.win_percentage != null ? (
                            <span style={{ color: player.win_percentage >= 50 ? '#16a34a' : 'var(--text-muted)' }}>
                              {player.win_percentage.toFixed(0)}%
                            </span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>—</span>
                          )}
                        </Table.Cell>
                        <Table.Cell className="text-right text-xs">
                          <span style={{ color: 'var(--text-muted)' }}>
                            {player.confidence_interval?.sample_size || 0}
                          </span>
                        </Table.Cell>
                      </Table.Row>
                    );
                  })}
                </React.Fragment>
              );
            })}
          </Table.Body>
        </Table>
      </Card.Content>
    </Card>
  );
}

// Component for player preferences grid
function PlayerPreferencesGrid({
  preferences,
  matchplayRatings,
}: {
  preferences: { player_key: string; player_name: string; current_ipr?: number | null; top_machines: MachinePickFrequency[] }[];
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
              <div className="flex items-center gap-2">
                <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>{pref.player_name}</p>
                {pref.current_ipr != null && (
                  <Badge variant="info" className="text-xs">
                    IPR {pref.current_ipr}
                  </Badge>
                )}
              </div>
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
                  <div className="flex items-center gap-2">
                    {machine.win_percentage != null && (
                      <span className="text-xs" style={{ color: machine.win_percentage >= 50 ? '#16a34a' : 'var(--text-muted)' }}>
                        {machine.win_percentage.toFixed(0)}% W
                      </span>
                    )}
                    <Badge variant="default" className="text-xs">
                      {machine.times_picked}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
