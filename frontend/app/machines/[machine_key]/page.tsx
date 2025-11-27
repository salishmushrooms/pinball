'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Machine, MachineScore, MachineVenue, MachineTeam } from '@/lib/types';
import {
  Card,
  PageHeader,
  Select,
  Alert,
  LoadingSpinner,
  StatCard,
  Table,
  MultiSelect,
} from '@/components/ui';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';

export default function MachineDetailPage() {
  const params = useParams();
  const machineKey = params.machine_key as string;

  const [machine, setMachine] = useState<Machine | null>(null);
  const [scores, setScores] = useState<MachineScore[]>([]);
  const [venues, setVenues] = useState<MachineVenue[]>([]);
  const [teams, setTeams] = useState<MachineTeam[]>([]);
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([21, 22]);
  const [selectedVenue, setSelectedVenue] = useState<string>('all');
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);
  const [selectedSeasons, setSelectedSeasons] = useState<number[]>([22]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load available seasons on mount
  useEffect(() => {
    async function loadSeasons() {
      try {
        const data = await api.getSeasons();
        setAvailableSeasons(data.seasons);
        // Default to most recent season
        if (data.seasons.length > 0) {
          setSelectedSeasons([Math.max(...data.seasons)]);
        }
      } catch (err) {
        console.error('Failed to load seasons:', err);
      }
    }
    loadSeasons();
  }, []);

  useEffect(() => {
    if (machineKey) {
      fetchMachineData();
    }
  }, [machineKey]);

  useEffect(() => {
    if (machineKey) {
      fetchScores();
    }
  }, [machineKey, selectedVenue, selectedTeams, selectedSeasons]);

  async function fetchMachineData() {
    setLoading(true);
    setError(null);
    try {
      const [machineData, venuesData, teamsData] = await Promise.all([
        api.getMachine(machineKey),
        api.getMachineVenues(machineKey),
        api.getMachineTeams(machineKey),
      ]);

      setMachine(machineData);
      setVenues(venuesData);
      setTeams(teamsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch machine data');
    } finally {
      setLoading(false);
    }
  }

  async function fetchScores() {
    try {
      const params: any = { limit: 1000 };
      if (selectedVenue !== 'all') {
        params.venue_key = selectedVenue;
      }
      if (selectedTeams.length > 0) {
        params.team_keys = selectedTeams.join(',');
      }
      // If specific seasons are selected, use them; otherwise fetch all
      if (selectedSeasons.length > 0 && selectedSeasons.length < availableSeasons.length) {
        // For now, the API only supports single season filtering
        // So we'll fetch scores for each season and combine them
        const allScoresPromises = selectedSeasons.map(season =>
          api.getMachineScores(machineKey, { ...params, season })
        );
        const allScoresResults = await Promise.all(allScoresPromises);
        const combinedScores = allScoresResults.flatMap(result => result.scores);
        setScores(combinedScores);
      } else {
        // Fetch all seasons
        const scoresData = await api.getMachineScores(machineKey, params);
        setScores(scoresData.scores);
      }
    } catch (err) {
      console.error('Failed to fetch scores:', err);
    }
  }

  function formatScore(score: number): string {
    if (score >= 1_000_000_000) {
      return `${(score / 1_000_000_000).toFixed(2)}B`;
    } else if (score >= 1_000_000) {
      return `${(score / 1_000_000).toFixed(2)}M`;
    } else if (score >= 1_000) {
      return `${(score / 1_000).toFixed(2)}K`;
    }
    return score.toLocaleString();
  }

  function calculatePercentile(score: number, allScores: number[]): number {
    if (allScores.length === 0) return 0;
    const sortedScores = [...allScores].sort((a, b) => a - b);
    const index = sortedScores.findIndex((s) => s >= score);
    if (index === -1) return 100;
    return (index / sortedScores.length) * 100;
  }

  function calculateStats() {
    if (scores.length === 0) return null;
    const sortedScores = [...scores].map(s => s.score).sort((a, b) => a - b);
    const p25 = sortedScores[Math.floor(sortedScores.length * 0.25)];
    const p50 = sortedScores[Math.floor(sortedScores.length * 0.50)];
    const p75 = sortedScores[Math.floor(sortedScores.length * 0.75)];
    const p90 = sortedScores[Math.floor(sortedScores.length * 0.90)];
    return { p25, p50, p75, p90, sortedScores };
  }

  if (loading) {
    return <LoadingSpinner fullPage text="Loading machine data..." />;
  }

  if (error) {
    return (
      <Alert variant="error" title="Error">
        {error}
      </Alert>
    );
  }

  if (!machine) {
    return (
      <Alert variant="warning" title="Not Found">
        Machine not found
      </Alert>
    );
  }

  const stats = calculateStats();

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/machines"
          className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block"
        >
          ← Back to Machines
        </Link>
        <PageHeader
          title={machine.machine_name}
          description={
            machine.manufacturer
              ? `${machine.manufacturer}${machine.year ? ` (${machine.year})` : ''}`
              : undefined
          }
        />
      </div>

      <Card>
        <Card.Header>
          <Card.Title>Machine Statistics</Card.Title>
        </Card.Header>
        <Card.Content>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="Total Scores"
              value={machine.total_scores?.toLocaleString() || '0'}
            />
            <StatCard
              label="Unique Players"
              value={machine.unique_players?.toString() || '0'}
            />
            <StatCard
              label="Median Score"
              value={formatScore(machine.median_score || 0)}
            />
            <StatCard
              label="Max Score"
              value={formatScore(machine.max_score || 0)}
            />
          </div>
        </Card.Content>
      </Card>

      {/* Filters */}
      <Card>
        <Card.Header>
          <Card.Title>Filters</Card.Title>
        </Card.Header>
        <Card.Content>
          <div className="space-y-6">
            {/* Season Filter */}
            <SeasonMultiSelect
              value={selectedSeasons}
              onChange={setSelectedSeasons}
              availableSeasons={availableSeasons}
              helpText="Select one or more seasons to filter scores"
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Venue Filter */}
              <Select
                label="Venue"
                value={selectedVenue}
                onChange={(e) => setSelectedVenue(e.target.value)}
                options={[
                  { value: 'all', label: `All Venues (${machine.total_scores} scores)` },
                  ...venues.map((venue) => ({
                    value: venue.venue_key,
                    label: `${venue.venue_name} (${venue.score_count} scores)`,
                  })),
                ]}
              />

              {/* Team Filter */}
              <div>
                <MultiSelect
                  label="Teams (select multiple)"
                  options={teams.map((team) => ({
                    value: team.team_key,
                    label: `${team.team_name} (${team.score_count} scores)`,
                  }))}
                  value={selectedTeams}
                  onChange={setSelectedTeams}
                />
                {selectedTeams.length > 0 && (
                  <button
                    onClick={() => setSelectedTeams([])}
                    className="mt-2 text-sm text-blue-600 hover:text-blue-800"
                  >
                    Clear all teams
                  </button>
                )}
              </div>
            </div>
          </div>
        </Card.Content>
      </Card>

      {/* Top 5 Scores */}
      {scores.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>Top 5 Scores</Card.Title>
          </Card.Header>
          <Card.Content>
            <Table>
              <Table.Header>
                <Table.Row hoverable={false}>
                  <Table.Head>Rank</Table.Head>
                  <Table.Head>Player Name</Table.Head>
                  <Table.Head className="text-right">Score</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {[...scores]
                  .sort((a, b) => b.score - a.score)
                  .slice(0, 5)
                  .map((scoreData, index) => (
                    <Table.Row key={scoreData.score_id}>
                      <Table.Cell className="font-medium">#{index + 1}</Table.Cell>
                      <Table.Cell>
                        <Link
                          href={`/players/${scoreData.player_key}`}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          {scoreData.player_name || scoreData.player_key}
                        </Link>
                      </Table.Cell>
                      <Table.Cell className="text-right">
                        {scoreData.score.toLocaleString()}
                      </Table.Cell>
                    </Table.Row>
                  ))}
              </Table.Body>
            </Table>
          </Card.Content>
        </Card>
      )}

      {/* Top Players */}
      {scores.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>Top Players</Card.Title>
          </Card.Header>
          <Card.Content>
            <p className="text-sm text-gray-600 mb-4">
              Players with the most scores on this machine (given current filters)
            </p>
            <Table>
              <Table.Header>
                <Table.Row hoverable={false}>
                  <Table.Head>Rank</Table.Head>
                  <Table.Head>Player Name</Table.Head>
                  <Table.Head className="text-right">Total Scores</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {(() => {
                  // Group scores by player and count
                  const playerScoreCounts = scores.reduce((acc, scoreData) => {
                    const key = scoreData.player_key;
                    if (!acc[key]) {
                      acc[key] = {
                        player_key: scoreData.player_key,
                        player_name: scoreData.player_name || scoreData.player_key,
                        count: 0,
                      };
                    }
                    acc[key].count++;
                    return acc;
                  }, {} as Record<string, { player_key: string; player_name: string; count: number }>);

                  // Convert to array and sort by count descending, limit to top 10
                  return Object.values(playerScoreCounts)
                    .sort((a, b) => b.count - a.count)
                    .slice(0, 10)
                    .map((player, index) => (
                      <Table.Row key={player.player_key}>
                        <Table.Cell className="font-medium">#{index + 1}</Table.Cell>
                        <Table.Cell>
                          <Link
                            href={`/players/${player.player_key}`}
                            className="text-blue-600 hover:text-blue-800 font-medium"
                          >
                            {player.player_name}
                          </Link>
                        </Table.Cell>
                        <Table.Cell className="text-right">
                          {player.count}
                        </Table.Cell>
                      </Table.Row>
                    ));
                })()}
              </Table.Body>
            </Table>
          </Card.Content>
        </Card>
      )}

      {/* Summary Table */}
      {stats && (
        <Card>
          <Card.Header>
            <Card.Title>Score Distribution Summary</Card.Title>
          </Card.Header>
          <Card.Content>
            <Table>
              <Table.Header>
                <Table.Row hoverable={false}>
                  <Table.Head>Percentile</Table.Head>
                  <Table.Head className="text-right">Score</Table.Head>
                  <Table.Head className="text-right">Formatted</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                <Table.Row>
                  <Table.Cell className="font-medium">Median (50th)</Table.Cell>
                  <Table.Cell className="text-right">
                    {stats.p50.toLocaleString()}
                  </Table.Cell>
                  <Table.Cell className="text-right text-gray-600">
                    {formatScore(stats.p50)}
                  </Table.Cell>
                </Table.Row>
                <Table.Row>
                  <Table.Cell className="font-medium">75th</Table.Cell>
                  <Table.Cell className="text-right">
                    {stats.p75.toLocaleString()}
                  </Table.Cell>
                  <Table.Cell className="text-right text-gray-600">
                    {formatScore(stats.p75)}
                  </Table.Cell>
                </Table.Row>
                <Table.Row>
                  <Table.Cell className="font-medium">90th</Table.Cell>
                  <Table.Cell className="text-right">
                    {stats.p90.toLocaleString()}
                  </Table.Cell>
                  <Table.Cell className="text-right text-gray-600">
                    {formatScore(stats.p90)}
                  </Table.Cell>
                </Table.Row>
              </Table.Body>
            </Table>
          </Card.Content>
        </Card>
      )}

      {/* Scatter Plot */}
      {stats && scores.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>Score Distribution Chart</Card.Title>
          </Card.Header>
          <Card.Content>
          <div className="relative w-full" style={{ height: '500px' }}>
            <svg width="100%" height="100%" viewBox="0 0 800 500" className="border border-gray-200 rounded">
              {/* Calculate score range for y-axis */}
              {(() => {
                // Focus on 25th-95th percentile range (most useful data)
                const p25 = stats.sortedScores[Math.floor(stats.sortedScores.length * 0.25)];
                const p95 = stats.sortedScores[Math.floor(stats.sortedScores.length * 0.95)];

                // Ensure minimum is never negative and has some padding
                const scoreRange = p95 - p25;
                const yPadding = scoreRange * 0.1; // 10% padding
                const minScore = Math.max(0, p25 - yPadding); // Never go below 0
                const maxScore = p95 + yPadding;

                // Y-axis labels (scores) - 6 evenly spaced ticks
                const yTicks = Array.from({ length: 6 }, (_, i) => {
                  const score = minScore + ((maxScore - minScore) * i / 5);
                  return score;
                });

                return (
                  <>
                    {/* Y-axis grid lines and labels */}
                    {yTicks.map((score, i) => {
                      const y = 50 + (400 * (5 - i) / 5);
                      return (
                        <g key={`y-${i}`}>
                          <line x1="80" y1={y} x2="780" y2={y} stroke="#e5e7eb" strokeWidth="1" />
                          <text x="70" y={y + 4} textAnchor="end" fontSize="11" fill="#6b7280">
                            {formatScore(score)}
                          </text>
                        </g>
                      );
                    })}

                    {/* X-axis labels (percentiles) - focus on useful range */}
                    {[0, 25, 50, 75, 90, 100].map((percentile) => {
                      const x = 80 + (percentile / 100) * 700;
                      return (
                        <g key={`x-${percentile}`}>
                          <line x1={x} y1="50" x2={x} y2="450" stroke="#e5e7eb" strokeWidth="1" />
                          <text x={x} y="470" textAnchor="middle" fontSize="12" fill="#6b7280">
                            {percentile}%
                          </text>
                        </g>
                      );
                    })}

                    {/* Percentile reference lines */}
                    <line x1={80 + (50 / 100) * 700} y1="50" x2={80 + (50 / 100) * 700} y2="450" stroke="#3b82f6" strokeWidth="2" strokeDasharray="5,5" />
                    <line x1={80 + (75 / 100) * 700} y1="50" x2={80 + (75 / 100) * 700} y2="450" stroke="#10b981" strokeWidth="2" strokeDasharray="5,5" />
                    <line x1={80 + (90 / 100) * 700} y1="50" x2={80 + (90 / 100) * 700} y2="450" stroke="#f59e0b" strokeWidth="2" strokeDasharray="5,5" />

                    {/* Scatter points */}
                    {scores.map((scoreData) => {
                      const percentile = calculatePercentile(scoreData.score, stats.sortedScores);
                      const x = 80 + (percentile / 100) * 700;

                      // Clamp y values to visible range
                      const clampedScore = Math.max(minScore, Math.min(maxScore, scoreData.score));
                      const normalizedScore = (clampedScore - minScore) / (maxScore - minScore);
                      const y = 450 - (normalizedScore * 400);

                      // Highlight outliers that are outside the visible range
                      const isOutlier = scoreData.score < minScore || scoreData.score > maxScore;

                      return (
                        <circle
                          key={scoreData.score_id}
                          cx={x}
                          cy={y}
                          r="3"
                          fill={isOutlier ? "#ef4444" : "#6366f1"}
                          opacity={isOutlier ? "0.4" : "0.6"}
                        >
                          <title>{`${scoreData.player_name || scoreData.player_key}: ${formatScore(scoreData.score)} (${percentile.toFixed(1)}%ile)`}</title>
                        </circle>
                      );
                    })}

                    {/* Axes */}
                    <line x1="80" y1="450" x2="780" y2="450" stroke="#374151" strokeWidth="2" />
                    <line x1="80" y1="50" x2="80" y2="450" stroke="#374151" strokeWidth="2" />

                    {/* Labels */}
                    <text x="430" y="490" textAnchor="middle" fontSize="14" fill="#374151" fontWeight="bold">
                      Percentile
                    </text>
                    <text x="30" y="250" textAnchor="middle" fontSize="14" fill="#374151" fontWeight="bold" transform="rotate(-90 30 250)">
                      Score
                    </text>

                    {/* Legend */}
                    <g transform="translate(580, 20)">
                      <line x1="0" y1="0" x2="20" y2="0" stroke="#3b82f6" strokeWidth="2" strokeDasharray="5,5" />
                      <text x="25" y="4" fontSize="11" fill="#374151">50th (Median)</text>

                      <line x1="0" y1="15" x2="20" y2="15" stroke="#10b981" strokeWidth="2" strokeDasharray="5,5" />
                      <text x="25" y="19" fontSize="11" fill="#374151">75th %ile</text>

                      <line x1="0" y1="30" x2="20" y2="30" stroke="#f59e0b" strokeWidth="2" strokeDasharray="5,5" />
                      <text x="25" y="34" fontSize="11" fill="#374151">90th %ile</text>

                      <circle cx="10" cy="48" r="3" fill="#ef4444" opacity="0.4" />
                      <text x="25" y="51" fontSize="11" fill="#374151">Outliers</text>
                    </g>
                  </>
                );
              })()}
            </svg>
          </div>
            <p className="text-sm text-gray-600 mt-2">
              Showing {scores.length} score{scores.length !== 1 ? 's' : ''} focused on 25th-95th percentile range. Outliers shown in red. Hover over points for player details.
            </p>
          </Card.Content>
        </Card>
      )}

      {scores.length === 0 && (
        <Alert variant="warning" title="No Data">
          No score data available for this machine yet.
        </Alert>
      )}
    </div>
  );
}
