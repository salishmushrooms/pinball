'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { VenueDetail, VenueMachineStats, Team } from '@/lib/types';
import {
  Card,
  PageHeader,
  Select,
  Alert,
  LoadingSpinner,
  EmptyState,
  Table,
  Badge,
  StatCard,
} from '@/components/ui';

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
    return <LoadingSpinner fullPage text="Loading venue details..." />;
  }

  if (error || !venue) {
    return (
      <Alert variant="error" title="Error">
        {error || 'Venue not found'}
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/venues"
          className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block"
        >
          ← Back to Venues
        </Link>
        <PageHeader
          title={venue.venue_name}
          description={
            <>
              {(venue.city || venue.state) && (
                <div className="text-lg text-gray-600">
                  {venue.city && venue.state
                    ? `${venue.city}, ${venue.state}`
                    : venue.city || venue.state}
                </div>
              )}
              {venue.address && (
                <div className="text-sm text-gray-500 mt-1">{venue.address}</div>
              )}
            </>
          }
        />
      </div>

      {/* Filter Controls */}
      <Card>
        <Card.Header>
          <Card.Title>Filters</Card.Title>
        </Card.Header>
        <Card.Content>
          <div className="space-y-4">
            {/* Machine Filter */}
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={currentOnly}
                  onChange={(e) => setCurrentOnly(e.target.checked)}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
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
            <Select
              label="Filter by Team (optional)"
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              className="max-w-md"
              options={[
                { value: '', label: 'All Teams' },
                ...teams.map((team) => ({
                  value: team.team_key,
                  label: team.team_name,
                })),
              ]}
            />

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
                      className="mt-1 h-4 w-4 text-blue-600 border-gray-300 focus:ring-2 focus:ring-blue-500"
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
                      className="mt-1 h-4 w-4 text-blue-600 border-gray-300 focus:ring-2 focus:ring-blue-500"
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
            <Select
              label="Sort By"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'name' | 'games')}
              className="max-w-md"
              options={[
                { value: 'games', label: 'Total Games (Most to Least)' },
                { value: 'name', label: 'Machine Name (A-Z)' },
              ]}
            />

            {/* Info messages */}
            {currentOnly && (
              <p className="text-xs text-gray-500">
                Current machines are determined from the most recent match at this venue
              </p>
            )}
          </div>
        </Card.Content>
      </Card>

      {/* Machines Table */}
      <Card>
        <Card.Header>
          <Card.Title>
            {currentOnly ? 'Current Machines' : 'All Machines'}
            {selectedTeam && (
              <span className="text-base font-normal text-gray-600 ml-2">
                - {teams.find((t) => t.team_key === selectedTeam)?.team_name} Stats
              </span>
            )}
          </Card.Title>
        </Card.Header>
        <Card.Content>
          {machines.length === 0 ? (
            <EmptyState
              title="No machines found"
              description={
                <>
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
                </>
              }
            />
          ) : (
            <Table>
              <Table.Header>
                <Table.Row hoverable={false}>
                  <Table.Head>Machine</Table.Head>
                  <Table.Head align="right">
                    {selectedTeam ? 'Games Played' : 'Total Scores'}
                  </Table.Head>
                  <Table.Head align="right">Players</Table.Head>
                  <Table.Head align="right">Median Score</Table.Head>
                  <Table.Head align="right">Max Score</Table.Head>
                  {!currentOnly && (
                    <Table.Head align="center">Current</Table.Head>
                  )}
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {sortedMachines.map((machine) => (
                  <Table.Row key={machine.machine_key}>
                    <Table.Cell>
                      <Link
                        href={`/machines/${machine.machine_key}`}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        {machine.machine_name}
                      </Link>
                    </Table.Cell>
                    <Table.Cell align="right">
                      {machine.total_scores.toLocaleString()}
                    </Table.Cell>
                    <Table.Cell align="right" className="text-gray-600">
                      {machine.unique_players}
                    </Table.Cell>
                    <Table.Cell align="right">
                      {machine.median_score.toLocaleString()}
                    </Table.Cell>
                    <Table.Cell align="right" className="font-medium text-green-600">
                      {machine.max_score.toLocaleString()}
                    </Table.Cell>
                    {!currentOnly && (
                      <Table.Cell align="center">
                        <Badge variant={machine.is_current ? 'success' : 'default'}>
                          {machine.is_current ? 'Current' : 'Past'}
                        </Badge>
                      </Table.Cell>
                    )}
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>
          )}
        </Card.Content>
      </Card>

      {/* Stats Summary */}
      {machines.length > 0 && (
        <Card>
          <Card.Header>
            <Card.Title>Summary Statistics</Card.Title>
          </Card.Header>
          <Card.Content>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                label="Total Machines"
                value={machines.length}
              />
              <StatCard
                label={selectedTeam ? 'Total Games' : 'Total Scores'}
                value={machines.reduce((sum, m) => sum + m.total_scores, 0).toLocaleString()}
              />
              <StatCard
                label={selectedTeam ? 'Team Members' : 'Unique Players'}
                value={Math.max(...machines.map((m) => m.unique_players))}
              />
              <StatCard
                label={`Avg ${selectedTeam ? 'Games' : 'Scores'}/Machine`}
                value={Math.round(
                  machines.reduce((sum, m) => sum + m.total_scores, 0) /
                    machines.length
                ).toLocaleString()}
              />
            </div>
            {selectedTeam && scoresFrom === 'all' && (
              <Alert variant="info" title="Scouting Mode" className="mt-4">
                These statistics show {teams.find((t) => t.team_key === selectedTeam)?.team_name}'s
                total experience on machines currently at {venue.venue_name}, including games played at other venues.
                This helps identify which machines this team has the most practice on.
              </Alert>
            )}
          </Card.Content>
        </Card>
      )}
    </div>
  );
}
