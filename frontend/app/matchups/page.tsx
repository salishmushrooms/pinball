'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import {
  Team,
  Venue,
  MatchupAnalysis,
  TeamMachineConfidence,
  PlayerMachineConfidence,
  MachinePickFrequency,
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
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';

export default function MatchupsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([21, 22]);
  const [homeTeam, setHomeTeam] = useState<string>('');
  const [awayTeam, setAwayTeam] = useState<string>('');
  const [venue, setVenue] = useState<string>('');
  const [seasons, setSeasons] = useState<number[]>([22]);
  const [matchup, setMatchup] = useState<MatchupAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load available seasons on mount
  useEffect(() => {
    async function loadSeasons() {
      try {
        const data = await api.getSeasons();
        setAvailableSeasons(data.seasons);
        // Default to most recent season
        if (data.seasons.length > 0) {
          setSeasons([Math.max(...data.seasons)]);
        }
      } catch (err) {
        console.error('Failed to load seasons:', err);
      }
    }
    loadSeasons();
  }, []);

  // Load teams and venues when seasons change
  useEffect(() => {
    async function loadData() {
      try {
        // Use the most recent selected season for fetching teams
        const latestSeason = seasons.length > 0 ? Math.max(...seasons) : 22;
        const [teamsData, venuesData] = await Promise.all([
          api.getTeams({ season: latestSeason, limit: 100 }),
          api.getVenues({ limit: 100 }),
        ]);
        setTeams(teamsData.teams);
        setVenues(venuesData.venues);
      } catch (err) {
        console.error('Failed to load teams/venues:', err);
      }
    }
    if (seasons.length > 0) {
      loadData();
    }
  }, [seasons]);

  // Load matchup analysis
  const handleAnalyzeMatchup = async () => {
    if (!homeTeam || !awayTeam || !venue) {
      setError('Please select home team, away team, and venue');
      return;
    }

    if (seasons.length === 0) {
      setError('Please select at least one season');
      return;
    }

    setLoading(true);
    setError(null);
    setMatchup(null);

    try {
      const data = await api.getMatchupAnalysis({
        home_team: homeTeam,
        away_team: awayTeam,
        venue: venue,
        seasons: seasons,
      });
      setMatchup(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze matchup');
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <div className="space-y-6">
      <PageHeader
        title="Matchup Analysis"
        description="Analyze team vs team matchups at specific venues with score predictions and machine preferences"
      />

      {/* Selection Form */}
      <Card>
        <Card.Header>
          <Card.Title>Select Matchup</Card.Title>
        </Card.Header>
        <Card.Content>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Select
              label="Home Team"
              value={homeTeam}
              onChange={(e) => setHomeTeam(e.target.value)}
              options={[
                { value: '', label: 'Select Home Team' },
                ...teams.map((team) => ({
                  value: team.team_key,
                  label: team.team_name,
                })),
              ]}
            />

            <Select
              label="Away Team"
              value={awayTeam}
              onChange={(e) => setAwayTeam(e.target.value)}
              options={[
                { value: '', label: 'Select Away Team' },
                ...teams.map((team) => ({
                  value: team.team_key,
                  label: team.team_name,
                })),
              ]}
            />

            <Select
              label="Venue"
              value={venue}
              onChange={(e) => setVenue(e.target.value)}
              options={[
                { value: '', label: 'Select Venue' },
                ...venues.map((v) => ({
                  value: v.venue_key,
                  label: v.venue_name,
                })),
              ]}
            />
          </div>

          <div className="mt-4">
            <SeasonMultiSelect
              value={seasons}
              onChange={setSeasons}
              availableSeasons={availableSeasons}
              helpText="Select one or more seasons to aggregate statistics"
            />
          </div>

          <div className="mt-6">
            <Button
              onClick={handleAnalyzeMatchup}
              disabled={loading || !homeTeam || !awayTeam || !venue || seasons.length === 0}
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

          {/* Available Machines */}
          <Card>
            <Card.Header>
              <Card.Title>
                Available Machines
                <Badge variant="info" className="ml-2">
                  {matchup.available_machines.length}
                </Badge>
              </Card.Title>
            </Card.Header>
            <Card.Content>
              <div className="flex flex-wrap gap-2">
                {matchup.available_machines.map((machine) => (
                  <Badge key={machine} variant="default">
                    {machine}
                  </Badge>
                ))}
              </div>
            </Card.Content>
          </Card>

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
                  title="Most Picked Machines"
                  badge={
                    <Badge variant="default">
                      {matchup.home_team_pick_frequency.length}
                    </Badge>
                  }
                >
                  <MachinePickTable picks={matchup.home_team_pick_frequency} />
                </Collapsible>

                {/* Player Preferences - Collapsible */}
                <Collapsible
                  title="Player Preferences"
                  badge={
                    <Badge variant="default">
                      {matchup.home_team_player_preferences.length} players
                    </Badge>
                  }
                >
                  <PlayerPreferencesGrid
                    preferences={matchup.home_team_player_preferences}
                  />
                </Collapsible>

                {/* Player-Specific Expected Scores - Collapsible */}
                <Collapsible
                  title="Player-Specific Expected Scores"
                  badge={
                    <Badge variant="info">Requires 5+ games</Badge>
                  }
                >
                  <p className="text-sm text-gray-600 mb-4">
                    Only showing players with 5 or more games on each machine for
                    statistical confidence (95% confidence interval).
                  </p>
                  <PlayerConfidenceGrid
                    confidences={matchup.home_team_player_confidence}
                    formatScore={formatScore}
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
                  title="Most Picked Machines"
                  badge={
                    <Badge variant="default">
                      {matchup.away_team_pick_frequency.length}
                    </Badge>
                  }
                >
                  <MachinePickTable picks={matchup.away_team_pick_frequency} />
                </Collapsible>

                {/* Player Preferences - Collapsible */}
                <Collapsible
                  title="Player Preferences"
                  badge={
                    <Badge variant="default">
                      {matchup.away_team_player_preferences.length} players
                    </Badge>
                  }
                >
                  <PlayerPreferencesGrid
                    preferences={matchup.away_team_player_preferences}
                  />
                </Collapsible>

                {/* Player-Specific Expected Scores - Collapsible */}
                <Collapsible
                  title="Player-Specific Expected Scores"
                  badge={
                    <Badge variant="info">Requires 5+ games</Badge>
                  }
                >
                  <p className="text-sm text-gray-600 mb-4">
                    Only showing players with 5 or more games on each machine for
                    statistical confidence (95% confidence interval).
                  </p>
                  <PlayerConfidenceGrid
                    confidences={matchup.away_team_player_confidence}
                    formatScore={formatScore}
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
}: {
  preferences: { player_key: string; player_name: string; top_machines: MachinePickFrequency[] }[];
}) {
  if (preferences.length === 0) {
    return <EmptyState title="No preference data available" />;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {preferences.map((pref) => (
        <div
          key={pref.player_key}
          className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
        >
          <p className="font-semibold text-gray-900 mb-3">{pref.player_name}</p>
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
      ))}
    </div>
  );
}

// Component for player confidence grid
function PlayerConfidenceGrid({
  confidences,
  formatScore,
}: {
  confidences: PlayerMachineConfidence[];
  formatScore: (score: number) => string;
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
      {Object.entries(byPlayer).map(([playerKey, confs]) => (
        <Card key={playerKey} className="shadow-sm">
          <Card.Header>
            <Card.Title className="text-base">
              {confs[0].player_name}
              <Badge variant="info" className="ml-2">
                {confs.length} machines
              </Badge>
            </Card.Title>
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
      ))}
    </div>
  );
}
