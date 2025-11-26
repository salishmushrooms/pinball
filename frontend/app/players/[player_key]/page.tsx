'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Player, PlayerMachineStat, Venue } from '@/lib/types';

export default function PlayerDetailPage() {
  const params = useParams();
  const playerKey = params.player_key as string;

  const [player, setPlayer] = useState<Player | null>(null);
  const [machineStats, setMachineStats] = useState<PlayerMachineStat[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'avg_percentile' | 'games_played' | 'avg_score' | 'win_percentage'>('avg_percentile');
  const [seasonFilter, setSeasonFilter] = useState<number | undefined>(undefined);
  const [venueFilter, setVenueFilter] = useState<string | undefined>(undefined);

  useEffect(() => {
    fetchVenues();
  }, []);

  useEffect(() => {
    if (playerKey) {
      fetchPlayerData();
    }
  }, [playerKey, sortBy, seasonFilter, venueFilter]);

  async function fetchVenues() {
    try {
      const venuesData = await api.getVenues({ limit: 500 });
      setVenues(venuesData.venues);
    } catch (err) {
      console.error('Failed to fetch venues:', err);
    }
  }

  async function fetchPlayerData() {
    setLoading(true);
    setError(null);
    try {
      const [playerData, statsData] = await Promise.all([
        api.getPlayer(playerKey),
        api.getPlayerMachineStats(playerKey, {
          season: seasonFilter,
          venue_key: venueFilter,
          min_games: 1,
          sort_by: sortBy,
          sort_order: 'desc',
          limit: 100,
        }),
      ]);

      setPlayer(playerData);
      setMachineStats(statsData.stats);
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
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          <div>
            <div className="text-sm text-gray-600">IPR</div>
            <div className="text-2xl font-bold text-blue-600">
              {player.current_ipr ? player.current_ipr.toLocaleString() : 'N/A'}
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

        <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Season
            </label>
            <select
              value={seasonFilter || ''}
              onChange={(e) => setSeasonFilter(e.target.value ? parseInt(e.target.value) : undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Seasons</option>
              <option value="22">Season 22</option>
              <option value="21">Season 21</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Venue
            </label>
            <select
              value={venueFilter || ''}
              onChange={(e) => setVenueFilter(e.target.value || undefined)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Venues</option>
              {venues.map((venue) => (
                <option key={venue.venue_key} value={venue.venue_key}>
                  {venue.venue_name}
                </option>
              ))}
            </select>
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
              <option value="avg_percentile">Percentile</option>
              <option value="win_percentage">Win %</option>
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
                    Win %
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Percentile
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Median Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Best Score
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {stat.win_percentage !== null ? `${stat.win_percentage.toFixed(1)}%` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {stat.avg_percentile !== null ? stat.avg_percentile.toFixed(1) : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {stat.median_score.toLocaleString(undefined, {
                        maximumFractionDigits: 0,
                      })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {stat.best_score.toLocaleString()}
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
