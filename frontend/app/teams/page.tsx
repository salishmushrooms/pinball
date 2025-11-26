'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Team } from '@/lib/types';

export default function TeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seasonFilter, setSeasonFilter] = useState<number | undefined>(22);

  useEffect(() => {
    fetchTeams();
  }, [seasonFilter]);

  async function fetchTeams() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getTeams({
        season: seasonFilter,
        limit: 500,
      });
      setTeams(data.teams);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch teams');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-lg text-gray-600">Loading teams...</div>
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Teams</h1>
        <p className="mt-2 text-gray-600">
          Browse all teams and view their machine statistics
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Season
          </label>
          <select
            value={seasonFilter || ''}
            onChange={(e) => setSeasonFilter(e.target.value ? parseInt(e.target.value) : undefined)}
            className="w-full md:w-64 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Seasons</option>
            <option value="22">Season 22</option>
            <option value="21">Season 21</option>
          </select>
        </div>

        {teams.length === 0 ? (
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
            No teams found for the selected season.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {teams.map((team) => (
              <Link
                key={`${team.team_key}-${team.season}`}
                href={`/teams/${team.team_key}?season=${team.season}`}
                className="block p-6 bg-white border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-lg transition-all"
              >
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {team.team_name}
                </h3>
                <div className="space-y-1 text-sm text-gray-600">
                  <div>
                    <span className="font-medium">Team Key:</span> {team.team_key}
                  </div>
                  <div>
                    <span className="font-medium">Season:</span> {team.season}
                  </div>
                  {team.home_venue_key && (
                    <div>
                      <span className="font-medium">Home Venue:</span> {team.home_venue_key}
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}

        <div className="mt-4 text-sm text-gray-600">
          Showing {teams.length} team{teams.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  );
}
