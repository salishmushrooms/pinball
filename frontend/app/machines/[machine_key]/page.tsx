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
  FilterPanel,
  ContentContainer,
  Breadcrumb,
  type FilterChipData,
} from '@/components/ui';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';
import { VenueSelect } from '@/components/VenueMultiSelect';
import { TeamMultiSelect } from '@/components/TeamMultiSelect';
import { SUPPORTED_SEASONS, filterSupportedSeasons } from '@/lib/utils';

export default function MachineDetailPage() {
  const params = useParams();
  const machineKey = params.machine_key as string;

  const [machine, setMachine] = useState<Machine | null>(null);
  const [scores, setScores] = useState<MachineScore[]>([]);
  const [venues, setVenues] = useState<MachineVenue[]>([]);
  const [teams, setTeams] = useState<MachineTeam[]>([]);
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([...SUPPORTED_SEASONS]);
  const [selectedVenue, setSelectedVenue] = useState<string>('all');
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);
  const [selectedSeasons, setSelectedSeasons] = useState<number[]>([22, 23]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load available seasons on mount
  useEffect(() => {
    async function loadSeasons() {
      try {
        const data = await api.getSeasons();
        const supported = filterSupportedSeasons(data.seasons);
        setAvailableSeasons(supported);
        // Default to seasons 22 and 23 if available
        if (supported.includes(22) && supported.includes(23)) {
          setSelectedSeasons([22, 23]);
        } else if (supported.length > 0) {
          setSelectedSeasons([Math.max(...supported)]);
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

  // Build active filters for chips display
  const activeFilters: FilterChipData[] = [];

  // Season filter - only show if not "all seasons"
  if (selectedSeasons.length > 0 && selectedSeasons.length < availableSeasons.length) {
    activeFilters.push({
      key: 'season',
      label: 'Season',
      value: selectedSeasons.length === 1
        ? String(selectedSeasons[0])
        : selectedSeasons.sort((a, b) => b - a).join(', '),
      onRemove: () => setSelectedSeasons([...availableSeasons]),
    });
  }

  // Venue filter
  if (selectedVenue !== 'all') {
    const venueName = venues.find(v => v.venue_key === selectedVenue)?.venue_name || selectedVenue;
    activeFilters.push({
      key: 'venue',
      label: 'Venue',
      value: venueName,
      onRemove: () => setSelectedVenue('all'),
    });
  }

  // Team filter
  if (selectedTeams.length > 0) {
    const teamNames = selectedTeams.map(tk =>
      teams.find(t => t.team_key === tk)?.team_name || tk
    );
    activeFilters.push({
      key: 'team',
      label: selectedTeams.length === 1 ? 'Team' : 'Teams',
      value: teamNames.length <= 2 ? teamNames.join(', ') : `${teamNames.length} selected`,
      onRemove: () => setSelectedTeams([]),
    });
  }

  const handleClearAllFilters = () => {
    setSelectedSeasons([Math.max(...availableSeasons)]);
    setSelectedVenue('all');
    setSelectedTeams([]);
  };

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumb
          items={[
            { label: 'Machines', href: '/machines' },
            { label: machine.machine_name },
          ]}
        />
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
          <p className="text-sm text-gray-500 mt-4">* Based on data from MNP seasons 18-22</p>
        </Card.Content>
      </Card>

      {/* Filters */}
      <FilterPanel
        title="Filters"
        collapsible={true}
        defaultOpen={false}
        activeFilters={activeFilters}
        onClearAll={handleClearAllFilters}
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <SeasonMultiSelect
            value={selectedSeasons}
            onChange={setSelectedSeasons}
            availableSeasons={availableSeasons}
            variant="dropdown"
          />

          <VenueSelect
            value={selectedVenue === 'all' ? '' : selectedVenue}
            onChange={(value) => setSelectedVenue(value || 'all')}
            venues={venues}
            label="Venue"
          />

          <TeamMultiSelect
            teams={teams}
            value={selectedTeams}
            onChange={setSelectedTeams}
          />
        </div>
      </FilterPanel>

      {/* Top 5 Scores */}
      {scores.length > 0 && (
        <ContentContainer size="md">
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
                            href={`/players/${encodeURIComponent(scoreData.player_key)}`}
                            className="text-blue-600 hover:text-blue-800 font-medium"
                          >
                            {scoreData.player_name || scoreData.player_key}
                          </Link>
                        </Table.Cell>
                        <Table.Cell className="text-right">
                          {formatScore(scoreData.score)}
                        </Table.Cell>
                      </Table.Row>
                    ))}
                </Table.Body>
              </Table>
            </Card.Content>
          </Card>
        </ContentContainer>
      )}

      {/* Frequent Players */}
      {scores.length > 0 && (
        <ContentContainer size="md">
          <Card>
            <Card.Header>
              <Card.Title>Frequent Players</Card.Title>
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
                              href={`/players/${encodeURIComponent(player.player_key)}`}
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
        </ContentContainer>
      )}

      {/* Summary Table */}
      {stats && (
        <ContentContainer size="sm">
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
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  <Table.Row>
                    <Table.Cell className="font-medium">Median (50th)</Table.Cell>
                    <Table.Cell className="text-right">
                      {formatScore(stats.p50)}
                    </Table.Cell>
                  </Table.Row>
                  <Table.Row>
                    <Table.Cell className="font-medium">75th</Table.Cell>
                    <Table.Cell className="text-right">
                      {formatScore(stats.p75)}
                    </Table.Cell>
                  </Table.Row>
                  <Table.Row>
                    <Table.Cell className="font-medium">90th</Table.Cell>
                    <Table.Cell className="text-right">
                      {formatScore(stats.p90)}
                    </Table.Cell>
                  </Table.Row>
                </Table.Body>
              </Table>
            </Card.Content>
          </Card>
        </ContentContainer>
      )}

      {/* Scatter Plot */}
      {stats && scores.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>Score Distribution Chart</Card.Title>
          </Card.Header>
          <Card.Content>
          {/* Legend - positioned top right to match where outliers appear on chart */}
          <div className="flex justify-end mb-4 text-sm sm:text-base">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500 opacity-40"></div>
              <span className="text-gray-700">Outliers</span>
            </div>
          </div>
          <div className="relative w-full" style={{ minHeight: '400px' }}>
            <svg
              width="100%"
              height="100%"
              viewBox="0 0 800 520"
              className="border border-gray-200 rounded"
              preserveAspectRatio="xMidYMid meet"
              style={{ minHeight: '400px' }}
            >
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

                // Chart area - adjusted for larger labels
                const chartLeft = 100;
                const chartRight = 780;
                const chartTop = 30;
                const chartBottom = 450;
                const chartWidth = chartRight - chartLeft;
                const chartHeight = chartBottom - chartTop;

                // Y-axis labels (scores) - 6 evenly spaced ticks
                const yTicks = Array.from({ length: 6 }, (_, i) => {
                  const score = minScore + ((maxScore - minScore) * i / 5);
                  return score;
                });

                return (
                  <>
                    {/* Y-axis grid lines and labels */}
                    {yTicks.map((score, i) => {
                      const y = chartBottom - (chartHeight * i / 5);
                      return (
                        <g key={`y-${i}`}>
                          <line x1={chartLeft} y1={y} x2={chartRight} y2={y} stroke="#e5e7eb" strokeWidth="1" />
                          <text x={chartLeft - 10} y={y + 5} textAnchor="end" fontSize="16" fill="#4b5563" fontWeight="500">
                            {formatScore(score)}
                          </text>
                        </g>
                      );
                    })}

                    {/* X-axis labels (percentiles) - focus on useful range */}
                    {[0, 25, 50, 75, 90, 100].map((percentile) => {
                      const x = chartLeft + (percentile / 100) * chartWidth;
                      return (
                        <g key={`x-${percentile}`}>
                          <line x1={x} y1={chartTop} x2={x} y2={chartBottom} stroke="#e5e7eb" strokeWidth="1" />
                          <text x={x} y={chartBottom + 25} textAnchor="middle" fontSize="16" fill="#4b5563" fontWeight="500">
                            {percentile}%
                          </text>
                        </g>
                      );
                    })}

                    {/* Percentile reference lines */}
                    <line x1={chartLeft + (50 / 100) * chartWidth} y1={chartTop} x2={chartLeft + (50 / 100) * chartWidth} y2={chartBottom} stroke="#3b82f6" strokeWidth="2.5" strokeDasharray="8,6" />
                    <line x1={chartLeft + (75 / 100) * chartWidth} y1={chartTop} x2={chartLeft + (75 / 100) * chartWidth} y2={chartBottom} stroke="#10b981" strokeWidth="2.5" strokeDasharray="8,6" />
                    <line x1={chartLeft + (90 / 100) * chartWidth} y1={chartTop} x2={chartLeft + (90 / 100) * chartWidth} y2={chartBottom} stroke="#f59e0b" strokeWidth="2.5" strokeDasharray="8,6" />

                    {/* Scatter points */}
                    {scores.map((scoreData) => {
                      const percentile = calculatePercentile(scoreData.score, stats.sortedScores);
                      const x = chartLeft + (percentile / 100) * chartWidth;

                      // Clamp y values to visible range
                      const clampedScore = Math.max(minScore, Math.min(maxScore, scoreData.score));
                      const normalizedScore = (clampedScore - minScore) / (maxScore - minScore);
                      const y = chartBottom - (normalizedScore * chartHeight);

                      // Highlight outliers that are outside the visible range
                      const isOutlier = scoreData.score < minScore || scoreData.score > maxScore;

                      return (
                        <circle
                          key={scoreData.score_id}
                          cx={x}
                          cy={y}
                          r="4"
                          fill={isOutlier ? "#ef4444" : "#6366f1"}
                          opacity={isOutlier ? "0.4" : "0.6"}
                        >
                          <title>{`${scoreData.player_name || scoreData.player_key}: ${formatScore(scoreData.score)} (${percentile.toFixed(1)}%ile)`}</title>
                        </circle>
                      );
                    })}

                    {/* Axes */}
                    <line x1={chartLeft} y1={chartBottom} x2={chartRight} y2={chartBottom} stroke="#374151" strokeWidth="2" />
                    <line x1={chartLeft} y1={chartTop} x2={chartLeft} y2={chartBottom} stroke="#374151" strokeWidth="2" />

                    {/* Axis Labels */}
                    <text x={(chartLeft + chartRight) / 2} y="505" textAnchor="middle" fontSize="18" fill="#1f2937" fontWeight="600">
                      Percentile
                    </text>
                    <text x="35" y={(chartTop + chartBottom) / 2} textAnchor="middle" fontSize="18" fill="#1f2937" fontWeight="600" transform={`rotate(-90 35 ${(chartTop + chartBottom) / 2})`}>
                      Score
                    </text>
                  </>
                );
              })()}
            </svg>
          </div>
            <p className="text-sm text-gray-600 mt-3">
              Showing {scores.length} score{scores.length !== 1 ? 's' : ''} focused on 25th-95th percentile range. Outliers shown in red.
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
