'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Machine, GroupedPercentiles } from '@/lib/types';

export default function MachineDetailPage() {
  const params = useParams();
  const machineKey = params.machine_key as string;

  const [machine, setMachine] = useState<Machine | null>(null);
  const [percentiles, setPercentiles] = useState<GroupedPercentiles[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (machineKey) {
      fetchMachineData();
    }
  }, [machineKey]);

  async function fetchMachineData() {
    setLoading(true);
    setError(null);
    try {
      const [machineData, percentilesData] = await Promise.all([
        api.getMachine(machineKey),
        api.getMachinePercentiles(machineKey),
      ]);

      setMachine(machineData);
      setPercentiles(percentilesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch machine data');
    } finally {
      setLoading(false);
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
              {machine.total_scores.toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Unique Players</div>
            <div className="text-2xl font-bold text-green-600">
              {machine.unique_players}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Average Score</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatScore(machine.avg_score)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Max Score</div>
            <div className="text-2xl font-bold text-purple-600">
              {formatScore(machine.max_score)}
            </div>
          </div>
        </div>
      </div>

      {percentiles.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Score Percentiles
          </h2>
          {percentiles.map((percentileGroup, idx) => (
            <div key={idx} className="mb-6 last:mb-0">
              <h3 className="text-lg font-medium text-gray-800 mb-3">
                {percentileGroup.venue_key === '_ALL_'
                  ? 'All Venues'
                  : percentileGroup.venue_name || percentileGroup.venue_key}
                {' - '}Season {percentileGroup.season}
                <span className="text-sm text-gray-600 ml-2">
                  ({percentileGroup.sample_size} scores)
                </span>
              </h3>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Percentile
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Score
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-full">
                        Visual
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {Object.entries(percentileGroup.percentiles)
                      .sort(([a], [b]) => parseInt(a) - parseInt(b))
                      .map(([percentile, score]) => {
                        const maxScore = machine.max_score;
                        const width = (score / maxScore) * 100;
                        return (
                          <tr key={percentile}>
                            <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                              P{percentile}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                              {score.toLocaleString()}
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center">
                                <div className="w-full bg-gray-200 rounded-full h-4 mr-2">
                                  <div
                                    className="bg-blue-600 h-4 rounded-full transition-all"
                                    style={{ width: `${Math.max(width, 2)}%` }}
                                  ></div>
                                </div>
                                <span className="text-xs text-gray-600 whitespace-nowrap">
                                  {formatScore(score)}
                                </span>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}

      {percentiles.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
          No percentile data available for this machine yet.
        </div>
      )}
    </div>
  );
}
