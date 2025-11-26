'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { VenueDetail, VenueMachineStats, Team } from '@/lib/types';

export default function VenueDetailPage() {
  const params = useParams();
  const venueKey = params.venue_key as string;

  const [venue, setVenue] = useState<VenueDetail | null>(null);
  const [machines, setMachines] = useState<VenueMachineStats[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [currentOnly, setCurrentOnly] = useState(true);
  const [selectedTeam, setSelectedTeam] = useState<string>('');
  const [scoresFrom, setScoresFrom] = useState<'venue' | 'all'>('venue');
  const [sortBy, setSortBy] = useState<'name' | 'games'>('games');

  // Fetch teams on mount
  useEffect(() => {
    async function fetchTeams() {
      try {
        const data = await api.getTeams({ limit: 500 });
        setTeams(data.teams);
      } catch (err) {
        console.error('Failed to fetch teams:', err);
      }
    }
    fetchTeams();
  }, []);

  // Fetch venue and machines when filters change
  useEffect(() => {
    async function fetchVenueData() {
      try {
        setLoading(true);
        const [venueData, machinesData] = await Promise.all([
          api.getVenue(venueKey),
          api.getVenueMachines(venueKey, {
            current_only: currentOnly,
            team_key: selectedTeam || undefined,
            scores_from: scoresFrom,
          }),
        ]);
        setVenue(venueData);
        setMachines(machinesData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch venue data');
      } finally {
        setLoading(false);
      }
    }

    fetchVenueData();
  }, [venueKey, currentOnly, selectedTeam, scoresFrom]);

  // Sort machines based on sortBy state
  const sortedMachines = [...machines].sort((a, b) => {
    if (sortBy === 'games') {
      return b.total_scores - a.total_scores;
    } else {
      return a.machine_name.localeCompare(b.machine_name);
    }
  });

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-lg text-gray-600">Loading venue details...</div>
      </div>
    );
  }

  if (error || !venue) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        <strong className="font-bold">Error: </strong>
        <span>{error || 'Venue not found'}</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Venue Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {venue.venue_name}
            </h1>
            {(venue.city || venue.state) && (
              <p className="text-lg text-gray-600">
                {venue.city && venue.state
                  ? `${venue.city}, ${venue.state}`
                  : venue.city || venue.state}
              </p>
            )}
            {venue.address && (
              <p className="text-sm text-gray-500 mt-1">{venue.address}</p>
            )}
          </div>
          <Link
            href="/venues"
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            ← Back to Venues
          </Link>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>

        <div className="space-y-4">
          {/* Machine Filter */}
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={currentOnly}
                onChange={(e) => setCurrentOnly(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">
                Show current machines only
              </span>
            </label>
            <div className="text-sm text-gray-500">
              ({machines.length} machine{machines.length !== 1 ? 's' : ''})
            </div>
          </div>

          {/* Team Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Team (optional)
            </label>
            <select
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Teams</option>
              {teams.map((team) => (
                <option key={team.team_key} value={team.team_key}>
                  {team.team_name}
                </option>
              ))}
            </select>
          </div>

          {/* View Mode Toggle - Only show when team is selected */}
          {selectedTeam && (
            <div className="border-t border-gray-200 pt-4">
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Statistics Source
              </label>
              <div className="space-y-2">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="radio"
                    value="venue"
                    checked={scoresFrom === 'venue'}
                    onChange={(e) => setScoresFrom(e.target.value as 'venue')}
                    className="mt-1 w-4 h-4 text-blue-600 border-gray-300 focus:ring-2 focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-900">
                      Scores at this venue only
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      Show {teams.find((t) => t.team_key === selectedTeam)?.team_name}'s
                      performance on these machines when played at {venue.venue_name}
                    </p>
                  </div>
                </label>
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="radio"
                    value="all"
                    checked={scoresFrom === 'all'}
                    onChange={(e) => setScoresFrom(e.target.value as 'all')}
                    className="mt-1 w-4 h-4 text-blue-600 border-gray-300 focus:ring-2 focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-900">
                      All scores on these machines
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      Show {teams.find((t) => t.team_key === selectedTeam)?.team_name}'s
                      total experience on these machines across all venues (useful for scouting)
                    </p>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* Sort Control */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sort By
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'name' | 'games')}
              className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="games">Total Games (Most to Least)</option>
              <option value="name">Machine Name (A-Z)</option>
            </select>
          </div>

          {/* Info messages */}
          {currentOnly && (
            <p className="text-xs text-gray-500">
              Current machines are determined from the most recent match at this venue
            </p>
          )}
        </div>
      </div>

      {/* Machines Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            {currentOnly ? 'Current Machines' : 'All Machines'}
            {selectedTeam && (
              <span className="text-base font-normal text-gray-600 ml-2">
                - {teams.find((t) => t.team_key === selectedTeam)?.team_name} Stats
              </span>
            )}
          </h2>
        </div>

        {machines.length === 0 ? (
          <div className="px-6 py-12 text-center text-gray-500">
            <p className="text-lg">No machines found</p>
            {currentOnly && (
              <p className="text-sm mt-2">
                Try unchecking "Show current machines only" to see all machines
                that have been played at this venue.
              </p>
            )}
            {selectedTeam && (
              <p className="text-sm mt-2">
                This team may not have played any games {scoresFrom === 'venue' ? 'at this venue' : 'on these machines'}.
              </p>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Machine
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {selectedTeam ? 'Games Played' : 'Total Scores'}
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Players
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Median Score
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Max Score
                  </th>
                  {!currentOnly && (
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Current
                    </th>
                  )}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedMachines.map((machine) => (
                  <tr key={machine.machine_key} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        href={`/machines/${machine.machine_key}`}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        {machine.machine_name}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      {machine.total_scores.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-600">
                      {machine.unique_players}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                      {machine.median_score.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-green-600">
                      {machine.max_score.toLocaleString()}
                    </td>
                    {!currentOnly && (
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        {machine.is_current ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Current
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            Past
                          </span>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Stats Summary */}
      {machines.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Summary Statistics
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-gray-600">Total Machines</div>
              <div className="text-2xl font-bold text-gray-900">
                {machines.length}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">
                {selectedTeam ? 'Total Games' : 'Total Scores'}
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {machines.reduce((sum, m) => sum + m.total_scores, 0).toLocaleString()}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">
                {selectedTeam ? 'Team Members' : 'Unique Players'}
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {Math.max(...machines.map((m) => m.unique_players))}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Avg {selectedTeam ? 'Games' : 'Scores'}/Machine</div>
              <div className="text-2xl font-bold text-gray-900">
                {Math.round(
                  machines.reduce((sum, m) => sum + m.total_scores, 0) /
                    machines.length
                ).toLocaleString()}
              </div>
            </div>
          </div>
          {selectedTeam && scoresFrom === 'all' && (
            <p className="text-sm text-gray-500 mt-4 p-3 bg-blue-50 rounded border border-blue-200">
              <strong>Scouting Mode:</strong> These statistics show {teams.find((t) => t.team_key === selectedTeam)?.team_name}'s
              total experience on machines currently at {venue.venue_name}, including games played at other venues.
              This helps identify which machines this team has the most practice on.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
