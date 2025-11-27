'use client';

import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Team, TeamMachineStat, TeamPlayer, Venue } from '@/lib/types';
import { RoundMultiSelect } from '@/components/RoundMultiSelect';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';
import { useDebouncedEffect } from '@/lib/hooks';

export default function TeamDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const teamKey = params.team_key as string;
  const initialSeason = searchParams.get('season');

  const [team, setTeam] = useState<Team | null>(null);
  const [machineStats, setMachineStats] = useState<TeamMachineStat[]>([]);
  const [players, setPlayers] = useState<TeamPlayer[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [sortBy, setSortBy] = useState<'games_played' | 'avg_score' | 'best_score' | 'win_percentage' | 'median_score'>('games_played');
  const [seasonsFilter, setSeasonsFilter] = useState<number[]>(
    initialSeason ? [parseInt(initialSeason)] : [22]
  );
  const [venueFilter, setVenueFilter] = useState<string | undefined>(undefined);
  const [roundsFilter, setRoundsFilter] = useState<number[]>([1, 2, 3, 4]);

  useEffect(() => {
    fetchVenues();
  }, []);

  // Debounced effect for filter changes (waits 500ms after last change)
  useDebouncedEffect(() => {
    if (!teamKey) return;

    setFetching(true);
    fetchTeamData();
  }, 500, [teamKey, sortBy, seasonsFilter, venueFilter, roundsFilter]);

  async function fetchVenues() {
    try {
      const venuesData = await api.getVenues({ limit: 500 });
      setVenues(venuesData.venues);
    } catch (err) {
      console.error('Failed to fetch venues:', err);
    }
  }

  async function fetchTeamData() {
    // Only set loading true on initial load, use fetching for subsequent updates
    if (!team) {
      setLoading(true);
    }
    setError(null);
    try {
      const roundsParam = roundsFilter.length > 0 ? roundsFilter.join(',') : undefined;
      const seasonsParam = seasonsFilter.length > 0 ? seasonsFilter.join(',') : undefined;

      const [teamData, statsData, playersData] = await Promise.all([
        api.getTeam(teamKey, seasonsFilter.length === 1 ? seasonsFilter[0] : undefined),
        api.getTeamMachineStats(teamKey, {
          seasons: seasonsParam,
          venue_key: venueFilter,
          rounds: roundsParam,
          min_games: 1,
          sort_by: sortBy,
          sort_order: 'desc',
          limit: 100,
        }),
        api.getTeamPlayers(teamKey, seasonsFilter.length === 1 ? seasonsFilter[0] : undefined, venueFilter),
      ]);

      setTeam(teamData);
      setMachineStats(statsData.stats);
      setPlayers(playersData.players);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch team data');
    } finally {
      setLoading(false);
      setFetching(false);
    }
  }


  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-lg text-gray-600">Loading team data...</div>
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

  if (!team) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
        Team not found
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/teams"
          className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block"
        >
          ← Back to Teams
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">{team.team_name}</h1>
        <p className="text-gray-600 mt-1">
          Season {team.season} {team.home_venue_key && `• Home Venue: ${team.home_venue_key}`}
        </p>
      </div>

      {/* Machine Statistics Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Machine Statistics
          </h2>
          {fetching && (
            <div className="flex items-center text-sm text-gray-600">
              <svg className="animate-spin h-4 w-4 mr-2 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Updating...
            </div>
          )}
        </div>

        {/* Filters */}
        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <SeasonMultiSelect
            value={seasonsFilter}
            onChange={setSeasonsFilter}
            availableSeasons={[21, 22]}
          />

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
              <option value="games_played">Games Played</option>
              <option value="win_percentage">Win %</option>
              <option value="avg_score">Avg Score</option>
              <option value="median_score">Median Score</option>
              <option value="best_score">Best Score</option>
            </select>
          </div>

          <RoundMultiSelect
            value={roundsFilter}
            onChange={setRoundsFilter}
            helpText="Doubles: 1 & 4 | Singles: 2 & 3"
          />
        </div>

        {/* Machine Stats Table */}
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
                    Median Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Best Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rounds
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
                      {stat.median_score?.toLocaleString(undefined, {
                        maximumFractionDigits: 0,
                      }) || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {stat.best_score?.toLocaleString() || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {stat.rounds_played?.join(', ') || 'N/A'}
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

      {/* Team Roster Section */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Team Roster
        </h2>

        {players.length === 0 ? (
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
            No players found for the selected filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Player
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IPR
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Games
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Win %
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Most Played Machine
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Seasons
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {players.map((player) => (
                  <tr key={player.player_key} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        href={`/players/${player.player_key}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-800"
                      >
                        {player.player_name}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {player.current_ipr || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {player.games_played}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {player.win_percentage !== null ? `${player.win_percentage.toFixed(1)}%` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {player.most_played_machine_name ? (
                        <Link
                          href={`/machines/${player.most_played_machine_key}`}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          {player.most_played_machine_name} ({player.most_played_machine_games})
                        </Link>
                      ) : (
                        'N/A'
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {player.seasons_played.join(', ')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-4 text-sm text-gray-600">
          Showing {players.length} player{players.length !== 1 ? 's' : ''}
        </div>
      </div>
    </div>
  );
}
