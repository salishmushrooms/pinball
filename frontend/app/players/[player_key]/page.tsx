'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Player, PlayerMachineStat } from '@/lib/types';

export default function PlayerDetailPage() {
  const params = useParams();
  const playerKey = params.player_key as string;

  const [player, setPlayer] = useState<Player | null>(null);
  const [machineStats, setMachineStats] = useState<PlayerMachineStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [venueFilter, setVenueFilter] = useState('_ALL_');
  const [minGames, setMinGames] = useState('1');
  const [sortBy, setSortBy] = useState<'avg_percentile' | 'games_played' | 'avg_score'>('avg_percentile');

  useEffect(() => {
    if (playerKey) {
      fetchPlayerData();
    }
  }, [playerKey, venueFilter, minGames, sortBy]);

  async function fetchPlayerData() {
    setLoading(true);
    setError(null);
    try {
      const [playerData, statsData] = await Promise.all([
        api.getPlayer(playerKey),
        api.getPlayerMachineStats(playerKey, {
          venue_key: venueFilter,
          min_games: parseInt(minGames),
          sort_by: sortBy,
          sort_order: 'desc',
          limit: 100,
        }),
      ]);

      setPlayer(playerData);
      setMachineStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch player data');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-lg text-gray-600">Loading player data...</div>
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

  if (!player) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
        Player not found
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/players"
          className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block"
        >
          ← Back to Players
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">{player.name}</h1>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Player Information
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
          <div>
            <div className="text-sm text-gray-600">IPR</div>
            <div className="text-2xl font-bold text-blue-600">
              {player.current_ipr ? player.current_ipr.toLocaleString() : 'N/A'}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Total Matches</div>
            <div className="text-2xl font-bold text-gray-900">
              {player.total_matches}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Total Games</div>
            <div className="text-2xl font-bold text-gray-900">
              {player.total_games}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">First Season</div>
            <div className="text-2xl font-bold text-gray-900">
              {player.first_seen_season}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Last Season</div>
            <div className="text-2xl font-bold text-gray-900">
              {player.last_seen_season}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Machine Statistics
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Venue Filter
            </label>
            <select
              value={venueFilter}
              onChange={(e) => setVenueFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="_ALL_">All Venues</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Min Games
            </label>
            <input
              type="number"
              value={minGames}
              onChange={(e) => setMinGames(e.target.value)}
              min="1"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sort By
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="avg_percentile">Avg Percentile</option>
              <option value="games_played">Games Played</option>
              <option value="avg_score">Avg Score</option>
            </select>
          </div>
        </div>

        {machineStats.length === 0 ? (
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
            No machine statistics found for the selected filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Machine
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Games
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Percentile
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Max Score
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {machineStats.map((stat, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        href={`/machines/${stat.machine_key}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-800"
                      >
                        {stat.machine_name}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {stat.games_played}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-semibold text-gray-900">
                        {stat.avg_percentile.toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {stat.min_percentile.toFixed(0)} - {stat.max_percentile.toFixed(0)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {stat.avg_score.toLocaleString(undefined, {
                        maximumFractionDigits: 0,
                      })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {stat.max_score.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-4 text-sm text-gray-600">
          Showing {machineStats.length} machine{machineStats.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  );
}
