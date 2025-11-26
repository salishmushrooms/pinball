'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Machine, MachineScore, MachineVenue, MachineTeam } from '@/lib/types';

export default function MachineDetailPage() {
  const params = useParams();
  const machineKey = params.machine_key as string;

  const [machine, setMachine] = useState<Machine | null>(null);
  const [scores, setScores] = useState<MachineScore[]>([]);
  const [venues, setVenues] = useState<MachineVenue[]>([]);
  const [teams, setTeams] = useState<MachineTeam[]>([]);
  const [selectedVenue, setSelectedVenue] = useState<string>('all');
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (machineKey) {
      fetchMachineData();
    }
  }, [machineKey]);

  useEffect(() => {
    if (machineKey) {
      fetchScores();
    }
  }, [machineKey, selectedVenue, selectedTeams]);

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
      const scoresData = await api.getMachineScores(machineKey, params);
      setScores(scoresData.scores);
    } catch (err) {
      console.error('Failed to fetch scores:', err);
    }
  }

  function handleTeamToggle(teamKey: string) {
    setSelectedTeams(prev => {
      if (prev.includes(teamKey)) {
        return prev.filter(t => t !== teamKey);
      } else {
        return [...prev, teamKey];
      }
    });
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
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-lg text-gray-600">Loading machine data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        <strong className="font-bold">Error: </strong>
        <span>{error}</span>
      </div>
    );
  }

  if (!machine) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
        Machine not found
      </div>
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
        <h1 className="text-3xl font-bold text-gray-900">{machine.machine_name}</h1>
        {machine.manufacturer && (
          <p className="text-gray-600 mt-1">
            {machine.manufacturer}
            {machine.year && ` (${machine.year})`}
          </p>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Machine Statistics
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <div className="text-sm text-gray-600">Total Scores</div>
            <div className="text-2xl font-bold text-blue-600">
              {machine.total_scores?.toLocaleString() || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Unique Players</div>
            <div className="text-2xl font-bold text-green-600">
              {machine.unique_players || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Median Score</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatScore(machine.median_score || 0)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Max Score</div>
            <div className="text-2xl font-bold text-purple-600">
              {formatScore(machine.max_score || 0)}
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Venue Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Venue
            </label>
            <select
              value={selectedVenue}
              onChange={(e) => setSelectedVenue(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Venues ({machine.total_scores} scores)</option>
              {venues.map((venue) => (
                <option key={venue.venue_key} value={venue.venue_key}>
                  {venue.venue_name} ({venue.score_count} scores)
                </option>
              ))}
            </select>
          </div>

          {/* Team Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Teams (select multiple)
            </label>
            <div className="border border-gray-300 rounded-md p-3 max-h-48 overflow-y-auto">
              {teams.length === 0 ? (
                <div className="text-sm text-gray-500">No teams available</div>
              ) : (
                teams.map((team) => (
                  <label
                    key={team.team_key}
                    className="flex items-center space-x-2 py-1 hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedTeams.includes(team.team_key)}
                      onChange={() => handleTeamToggle(team.team_key)}
                      className="rounded text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-900">
                      {team.team_name} ({team.score_count} scores)
                    </span>
                  </label>
                ))
              )}
            </div>
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

      {/* Top 5 Scores */}
      {scores.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Top 5 Scores
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Player Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {[...scores]
                  .sort((a, b) => b.score - a.score)
                  .slice(0, 5)
                  .map((scoreData, index) => (
                    <tr key={scoreData.score_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        #{index + 1}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <Link
                          href={`/players/${scoreData.player_key}`}
                          className="text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {scoreData.player_name || scoreData.player_key}
                        </Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {scoreData.score.toLocaleString()}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Top Players */}
      {scores.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Top Players
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Players with the most scores on this machine (given current filters)
          </p>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Player Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Scores
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
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
                      <tr key={player.player_key}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          #{index + 1}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <Link
                            href={`/players/${player.player_key}`}
                            className="text-blue-600 hover:text-blue-800 hover:underline"
                          >
                            {player.player_name}
                          </Link>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {player.count}
                        </td>
                      </tr>
                    ));
                })()}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Summary Table */}
      {stats && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Score Distribution Summary
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Percentile
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Formatted
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Median (50th)
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {stats.p50.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatScore(stats.p50)}
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    75th
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {stats.p75.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatScore(stats.p75)}
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    90th
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {stats.p90.toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatScore(stats.p90)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Scatter Plot */}
      {stats && scores.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Score Distribution Chart
          </h2>
          <div className="relative w-full" style={{ height: '500px' }}>
            <svg width="100%" height="100%" viewBox="0 0 800 500" className="border border-gray-200 rounded">
              {/* Calculate score range for y-axis */}
              {(() => {
                const minScore = Math.min(...stats.sortedScores);
                const maxScore = Math.max(...stats.sortedScores);
                const scoreRange = maxScore - minScore;
                const yPadding = scoreRange * 0.1; // 10% padding

                // Y-axis labels (scores) - 5 evenly spaced ticks
                const yTicks = Array.from({ length: 6 }, (_, i) => {
                  const score = minScore - yPadding + ((scoreRange + 2 * yPadding) * i / 5);
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

                    {/* X-axis labels (percentiles) */}
                    {[0, 25, 50, 75, 100].map((percentile) => {
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
                    <line x1={80 + (25 / 100) * 700} y1="50" x2={80 + (25 / 100) * 700} y2="450" stroke="#fbbf24" strokeWidth="2" strokeDasharray="5,5" />
                    <line x1={80 + (50 / 100) * 700} y1="50" x2={80 + (50 / 100) * 700} y2="450" stroke="#3b82f6" strokeWidth="2" strokeDasharray="5,5" />
                    <line x1={80 + (75 / 100) * 700} y1="50" x2={80 + (75 / 100) * 700} y2="450" stroke="#10b981" strokeWidth="2" strokeDasharray="5,5" />

                    {/* Scatter points */}
                    {scores.map((scoreData) => {
                      const percentile = calculatePercentile(scoreData.score, stats.sortedScores);
                      const x = 80 + (percentile / 100) * 700;
                      const normalizedScore = (scoreData.score - (minScore - yPadding)) / (scoreRange + 2 * yPadding);
                      const y = 450 - (normalizedScore * 400);

                      return (
                        <circle
                          key={scoreData.score_id}
                          cx={x}
                          cy={y}
                          r="3"
                          fill="#6366f1"
                          opacity="0.6"
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
                    <g transform="translate(600, 20)">
                      <line x1="0" y1="0" x2="20" y2="0" stroke="#fbbf24" strokeWidth="2" strokeDasharray="5,5" />
                      <text x="25" y="4" fontSize="11" fill="#374151">25th %ile</text>

                      <line x1="0" y1="15" x2="20" y2="15" stroke="#3b82f6" strokeWidth="2" strokeDasharray="5,5" />
                      <text x="25" y="19" fontSize="11" fill="#374151">50th (Median)</text>

                      <line x1="0" y1="30" x2="20" y2="30" stroke="#10b981" strokeWidth="2" strokeDasharray="5,5" />
                      <text x="25" y="34" fontSize="11" fill="#374151">75th %ile</text>
                    </g>
                  </>
                );
              })()}
            </svg>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Showing {scores.length} score{scores.length !== 1 ? 's' : ''}. Hover over points for player details.
          </p>
        </div>
      )}

      {scores.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
          No score data available for this machine yet.
        </div>
      )}
    </div>
  );
}
