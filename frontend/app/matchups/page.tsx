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
} from '@/components/ui';

export default function MatchupsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [homeTeam, setHomeTeam] = useState<string>('');
  const [awayTeam, setAwayTeam] = useState<string>('');
  const [venue, setVenue] = useState<string>('');
  const [season, setSeason] = useState<number>(22);
  const [matchup, setMatchup] = useState<MatchupAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load teams and venues on mount
  useEffect(() => {
    async function loadData() {
      try {
        const [teamsData, venuesData] = await Promise.all([
          api.getTeams({ season, limit: 100 }),
          api.getVenues({ limit: 100 }),
        ]);
        setTeams(teamsData.teams);
        setVenues(venuesData.venues);
      } catch (err) {
        console.error('Failed to load teams/venues:', err);
      }
    }
    loadData();
  }, [season]);

  // Load matchup analysis
  const handleAnalyzeMatchup = async () => {
    if (!homeTeam || !awayTeam || !venue) {
      setError('Please select home team, away team, and venue');
      return;
    }

    console.log('Starting matchup analysis...', { homeTeam, awayTeam, venue, season });
    setLoading(true);
    setError(null);
    setMatchup(null);

    try {
      const data = await api.getMatchupAnalysis({
        home_team: homeTeam,
        away_team: awayTeam,
        venue: venue,
        season: season,
      });
      console.log('Matchup analysis received:', data);
      setMatchup(data);
    } catch (err) {
      console.error('Matchup analysis error:', err);
      setError(err instanceof Error ? err.message : 'Failed to analyze matchup');
    } finally {
      setLoading(false);
      console.log('Matchup analysis complete');
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
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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

            <Select
              label="Season"
              value={season}
              onChange={(e) => setSeason(Number(e.target.value))}
              options={[
                { value: 22, label: 'Season 22' },
                { value: 21, label: 'Season 21' },
              ]}
            />
          </div>

          <div className="mt-4">
            <Button
              onClick={handleAnalyzeMatchup}
              disabled={loading || !homeTeam || !awayTeam || !venue}
              variant="primary"
            >
              {loading ? 'Analyzing...' : 'Analyze Matchup'}
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
                Venue: {matchup.venue_name} | Season: {matchup.season}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                {matchup.available_machines.length} machines available
              </p>
            </Card.Content>
          </Card>

          {/* Available Machines */}
          <Card>
            <Card.Header>
              <Card.Title>Available Machines</Card.Title>
            </Card.Header>
            <Card.Content>
              <div className="flex flex-wrap gap-2">
                {matchup.available_machines.map((machine) => (
                  <Badge key={machine} variant="info">
                    {machine}
                  </Badge>
                ))}
              </div>
            </Card.Content>
          </Card>

          {/* Team Machine Pick Frequency */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <Card.Header>
                <Card.Title>{matchup.home_team_name} - Most Picked Machines</Card.Title>
              </Card.Header>
              <Card.Content>
                <MachinePickTable picks={matchup.home_team_pick_frequency} />
              </Card.Content>
            </Card>

            <Card>
              <Card.Header>
                <Card.Title>{matchup.away_team_name} - Most Picked Machines</Card.Title>
              </Card.Header>
              <Card.Content>
                <MachinePickTable picks={matchup.away_team_pick_frequency} />
              </Card.Content>
            </Card>
          </div>

          {/* Team Confidence Intervals */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <Card.Header>
                <Card.Title>{matchup.home_team_name} - Expected Scores (Team)</Card.Title>
              </Card.Header>
              <Card.Content>
                <TeamConfidenceTable
                  confidences={matchup.home_team_machine_confidence}
                  formatScore={formatScore}
                />
              </Card.Content>
            </Card>

            <Card>
              <Card.Header>
                <Card.Title>{matchup.away_team_name} - Expected Scores (Team)</Card.Title>
              </Card.Header>
              <Card.Content>
                <TeamConfidenceTable
                  confidences={matchup.away_team_machine_confidence}
                  formatScore={formatScore}
                />
              </Card.Content>
            </Card>
          </div>

          {/* Player Machine Preferences */}
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                {matchup.home_team_name} - Player Preferences
              </h3>
              <PlayerPreferencesTable
                preferences={matchup.home_team_player_preferences}
              />
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                {matchup.away_team_name} - Player Preferences
              </h3>
              <PlayerPreferencesTable
                preferences={matchup.away_team_player_preferences}
              />
            </div>
          </div>

          {/* Player Confidence Intervals - Expandable Section */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <details>
              <summary className="text-xl font-semibold text-gray-900 cursor-pointer">
                Player-Specific Expected Scores (Click to expand)
              </summary>
              <div className="mt-4 grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-3">
                    {matchup.home_team_name}
                  </h4>
                  <PlayerConfidenceTable
                    confidences={matchup.home_team_player_confidence}
                    formatScore={formatScore}
                  />
                </div>
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-3">
                    {matchup.away_team_name}
                  </h4>
                  <PlayerConfidenceTable
                    confidences={matchup.away_team_player_confidence}
                    formatScore={formatScore}
                  />
                </div>
              </div>
            </details>
          </div>
        </div>
      )}
    </div>
  );
}

// Component for machine pick frequency table
function MachinePickTable({ picks }: { picks: MachinePickFrequency[] }) {
  if (picks.length === 0) {
    return <p className="text-gray-500">No pick data available</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Machine
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Times Picked
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {picks.slice(0, 10).map((pick) => (
            <tr key={pick.machine_key}>
              <td className="px-4 py-3 text-sm text-gray-900">
                {pick.machine_name}
              </td>
              <td className="px-4 py-3 text-sm text-right text-gray-900 font-medium">
                {pick.times_picked}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
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
    return <p className="text-gray-500">Insufficient data for predictions</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Machine
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Expected Score
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              95% Range
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Sample
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {withData.slice(0, 10).map((conf) => (
            <tr key={conf.machine_key}>
              <td className="px-4 py-3 text-sm text-gray-900">
                {conf.machine_name}
              </td>
              <td className="px-4 py-3 text-sm text-right font-medium text-blue-600">
                {conf.confidence_interval
                  ? formatScore(conf.confidence_interval.mean)
                  : 'N/A'}
              </td>
              <td className="px-4 py-3 text-sm text-right text-gray-600">
                {conf.confidence_interval
                  ? `${formatScore(conf.confidence_interval.lower_bound)} - ${formatScore(conf.confidence_interval.upper_bound)}`
                  : 'N/A'}
              </td>
              <td className="px-4 py-3 text-sm text-right text-gray-500">
                n={conf.confidence_interval?.sample_size || 0}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Component for player preferences table
function PlayerPreferencesTable({
  preferences,
}: {
  preferences: { player_key: string; player_name: string; top_machines: MachinePickFrequency[] }[];
}) {
  if (preferences.length === 0) {
    return <p className="text-gray-500">No preference data available</p>;
  }

  return (
    <div className="space-y-4">
      {preferences.slice(0, 5).map((pref) => (
        <div key={pref.player_key} className="border-b pb-3">
          <p className="font-medium text-gray-900 mb-2">{pref.player_name}</p>
          <div className="flex flex-wrap gap-2">
            {pref.top_machines.slice(0, 3).map((machine) => (
              <span
                key={machine.machine_key}
                className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
              >
                {machine.machine_name}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// Component for player confidence interval table
function PlayerConfidenceTable({
  confidences,
  formatScore,
}: {
  confidences: PlayerMachineConfidence[];
  formatScore: (score: number) => string;
}) {
  const withData = confidences.filter((c) => !c.insufficient_data);

  if (withData.length === 0) {
    return <p className="text-gray-500">Insufficient data for player predictions</p>;
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
    <div className="space-y-4 max-h-96 overflow-y-auto">
      {Object.entries(byPlayer).map(([playerKey, confs]) => (
        <details key={playerKey} className="border rounded p-3">
          <summary className="font-medium text-gray-900 cursor-pointer">
            {confs[0].player_name} ({confs.length} machines)
          </summary>
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-2 text-left text-xs font-medium text-gray-500">
                    Machine
                  </th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">
                    Expected
                  </th>
                  <th className="px-2 py-2 text-right text-xs font-medium text-gray-500">
                    Range
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {confs.map((conf) => (
                  <tr key={conf.machine_key}>
                    <td className="px-2 py-2 text-xs text-gray-900">
                      {conf.machine_name}
                    </td>
                    <td className="px-2 py-2 text-xs text-right font-medium text-blue-600">
                      {conf.confidence_interval
                        ? formatScore(conf.confidence_interval.mean)
                        : 'N/A'}
                    </td>
                    <td className="px-2 py-2 text-xs text-right text-gray-600">
                      {conf.confidence_interval
                        ? `${formatScore(conf.confidence_interval.lower_bound)}-${formatScore(conf.confidence_interval.upper_bound)}`
                        : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      ))}
    </div>
  );
}
