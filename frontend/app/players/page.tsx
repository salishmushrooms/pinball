'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Player } from '@/lib/types';

export default function PlayersPage() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [minIpr, setMinIpr] = useState('');

  // Live search - fetch as user types
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchPlayers();
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchTerm, minIpr]);

  async function fetchPlayers() {
    setLoading(true);
    setError(null);
    try {
      const params: any = {
        limit: 100,
      };

      if (searchTerm) params.search = searchTerm;
      if (minIpr) {
        const iprValue = parseInt(minIpr);
        if (iprValue >= 1 && iprValue <= 6) {
          params.min_ipr = iprValue;
        }
      }

      const response = await api.getPlayers(params);
      setPlayers(response.players);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch players');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Players</h1>
        <p className="text-gray-600 mt-2">
          Browse and search player statistics
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Name
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Type to search players..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Min IPR (1-6)
            </label>
            <input
              type="number"
              value={minIpr}
              onChange={(e) => setMinIpr(e.target.value)}
              placeholder="e.g., 3"
              min="1"
              max="6"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {loading && (
          <div className="mt-4 text-sm text-gray-500">
            Searching...
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <strong className="font-bold">Error: </strong>
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && players.length === 0 && (searchTerm || minIpr) && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
          No players found matching your criteria.
        </div>
      )}

      {players.length > 0 && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Player Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IPR
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Seasons
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {players.map((player) => (
                <tr key={player.player_key} className="hover:bg-gray-50 cursor-pointer">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      href={`/players/${player.player_key}`}
                      className="block text-sm font-medium text-gray-900"
                    >
                      {player.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      href={`/players/${player.player_key}`}
                      className="block text-sm text-gray-900"
                    >
                      {player.current_ipr ? player.current_ipr.toFixed(2) : 'N/A'}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <Link
                      href={`/players/${player.player_key}`}
                      className="block"
                    >
                      {player.first_seen_season} - {player.last_seen_season}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {players.length > 0 && (
        <div className="text-center text-sm text-gray-600">
          Showing {players.length} player{players.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
