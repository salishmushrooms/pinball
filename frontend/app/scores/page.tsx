'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import {
  ScoreBrowseResponse,
  MachineScoreGroup,
  Team,
  Venue,
} from '@/lib/types';
import {
  Card,
  PageHeader,
  Button,
  Alert,
  Badge,
  Table,
  LoadingSpinner,
  EmptyState,
} from '@/components/ui';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';
import { TeamMultiSelect } from '@/components/TeamMultiSelect';
import { VenueSelect } from '@/components/VenueMultiSelect';
import { SUPPORTED_SEASONS } from '@/lib/utils';

export default function ScoresPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <ScoresPageContent />
    </Suspense>
  );
}

function ScoresPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Filter state
  const [seasons, setSeasons] = useState<number[]>([]);
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);
  const [selectedVenue, setSelectedVenue] = useState<string>('');
  const [includeAllVenues, setIncludeAllVenues] = useState(false);

  // Data state
  const [teams, setTeams] = useState<Team[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [scoreData, setScoreData] = useState<ScoreBrowseResponse | null>(null);
  const [expandedMachines, setExpandedMachines] = useState<Set<string>>(new Set());
  const [loadingMore, setLoadingMore] = useState<Set<string>>(new Set());

  // UI state
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize from URL params
  useEffect(() => {
    const seasonsParam = searchParams.get('seasons');
    const teamsParam = searchParams.get('teams');
    const venueParam = searchParams.get('venue');
    const allVenuesParam = searchParams.get('all_venues');

    if (seasonsParam) {
      setSeasons(seasonsParam.split(',').map(Number).filter(n => !isNaN(n)));
    } else {
      // Default to current and previous season
      const defaultSeasons = SUPPORTED_SEASONS.slice(-2);
      setSeasons(defaultSeasons);
    }

    if (teamsParam) {
      setSelectedTeams(teamsParam.split(','));
    }

    if (venueParam) {
      setSelectedVenue(venueParam);
    }

    if (allVenuesParam === 'true') {
      setIncludeAllVenues(true);
    }
  }, [searchParams]);

  // Load teams and venues
  useEffect(() => {
    async function loadFilterOptions() {
      try {
        const [teamsResponse, venuesResponse] = await Promise.all([
          api.getTeams({ limit: 200 }),
          api.getVenues({ limit: 200 }),
        ]);
        // Deduplicate teams by team_key, keeping the most recent season's name
        // Sort by season ascending so the newest entry (last) is kept by the Map
        const sortedTeams = [...teamsResponse.teams].sort((a, b) => a.season - b.season);
        const uniqueTeams = Array.from(
          new Map(sortedTeams.map(t => [t.team_key, t])).values()
        );
        setTeams(uniqueTeams);
        setVenues(venuesResponse.venues);
      } catch (err) {
        console.error('Failed to load filter options:', err);
      } finally {
        setInitialLoading(false);
      }
    }
    loadFilterOptions();
  }, []);

  // Update URL when filters change
  const updateUrl = useCallback((
    newSeasons: number[],
    newTeams: string[],
    newVenue: string,
    newAllVenues: boolean
  ) => {
    const params = new URLSearchParams();
    if (newSeasons.length > 0) {
      params.set('seasons', newSeasons.join(','));
    }
    if (newTeams.length > 0) {
      params.set('teams', newTeams.join(','));
    }
    if (newVenue) {
      params.set('venue', newVenue);
    }
    if (newAllVenues && newVenue) {
      params.set('all_venues', 'true');
    }
    const queryString = params.toString();
    router.replace(`/scores${queryString ? `?${queryString}` : ''}`, { scroll: false });
  }, [router]);

  // Fetch scores
  const fetchScores = useCallback(async () => {
    if (seasons.length === 0) {
      setError('Please select at least one season');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.browseScores({
        seasons,
        teams: selectedTeams.length > 0 ? selectedTeams : undefined,
        venue_key: selectedVenue || undefined,
        include_all_venues: includeAllVenues,
        scores_per_machine: 20,
      });
      setScoreData(response);

      // Auto-expand first 3 machines
      const firstThree = response.machine_groups.slice(0, 3).map(g => g.machine_key);
      setExpandedMachines(new Set(firstThree));

      // Update URL
      updateUrl(seasons, selectedTeams, selectedVenue, includeAllVenues);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scores');
    } finally {
      setLoading(false);
    }
  }, [seasons, selectedTeams, selectedVenue, includeAllVenues, updateUrl]);

  // Load more scores for a machine
  const loadMoreScores = useCallback(async (machineKey: string) => {
    if (!scoreData) return;

    const group = scoreData.machine_groups.find(g => g.machine_key === machineKey);
    if (!group) return;

    setLoadingMore(prev => new Set(prev).add(machineKey));

    try {
      const response = await api.browseMachineScores(machineKey, {
        seasons,
        teams: selectedTeams.length > 0 ? selectedTeams : undefined,
        venue_key: selectedVenue || undefined,
        include_all_venues: includeAllVenues,
        limit: 50,
        offset: group.scores.length,
      });

      // Update the machine group with new scores
      setScoreData(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          machine_groups: prev.machine_groups.map(g => {
            if (g.machine_key !== machineKey) return g;
            const newScores = [...g.scores, ...response.scores];
            return {
              ...g,
              scores: newScores,
              has_more: newScores.length < g.stats.count,
            };
          }),
        };
      });
    } catch (err) {
      console.error('Failed to load more scores:', err);
    } finally {
      setLoadingMore(prev => {
        const next = new Set(prev);
        next.delete(machineKey);
        return next;
      });
    }
  }, [scoreData, seasons, selectedTeams, selectedVenue, includeAllVenues]);

  // Toggle machine expansion
  const toggleMachine = (machineKey: string) => {
    setExpandedMachines(prev => {
      const next = new Set(prev);
      if (next.has(machineKey)) {
        next.delete(machineKey);
      } else {
        next.add(machineKey);
      }
      return next;
    });
  };

  // Format score for display
  const formatScore = (score: number): string => {
    if (score >= 1_000_000_000) {
      return `${(score / 1_000_000_000).toFixed(1)}B`;
    } else if (score >= 1_000_000) {
      return `${(score / 1_000_000).toFixed(1)}M`;
    } else if (score >= 1_000) {
      return `${(score / 1_000).toFixed(1)}K`;
    }
    return score.toLocaleString();
  };

  if (initialLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Score Browser"
        description="Browse and compare scores across teams, venues, and machines"
      />

      {/* Filters */}
      <Card>
        <Card.Header>
          <Card.Title>Filters</Card.Title>
        </Card.Header>
        <Card.Content>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <SeasonMultiSelect
              value={seasons}
              onChange={setSeasons}
              variant="dropdown"
              label="Seasons"
              helpText="Required"
            />

            <TeamMultiSelect
              value={selectedTeams}
              onChange={setSelectedTeams}
              teams={teams.map(t => ({ team_key: t.team_key, team_name: t.team_name }))}
              label="Teams"
              helpText="Compare up to 2 teams"
            />

            <VenueSelect
              value={selectedVenue}
              onChange={(value) => {
                setSelectedVenue(value);
                if (!value) setIncludeAllVenues(false);
              }}
              venues={venues.map(v => ({ venue_key: v.venue_key, venue_name: v.venue_name }))}
              label="Venue"
            />

            {selectedVenue && (
              <div className="flex items-end">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeAllVenues}
                    onChange={(e) => setIncludeAllVenues(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-600">
                    Include scores from all venues
                  </span>
                </label>
              </div>
            )}
          </div>

          <div className="mt-6 flex items-center gap-4">
            <Button
              onClick={fetchScores}
              disabled={loading || seasons.length === 0}
              variant="primary"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <LoadingSpinner size="sm" />
                  Loading...
                </span>
              ) : (
                'Load Scores'
              )}
            </Button>

            {scoreData && (
              <span className="text-sm text-gray-500">
                {scoreData.total_score_count.toLocaleString()} total scores across {scoreData.machine_groups.length} machines
              </span>
            )}
          </div>

          {error && (
            <Alert variant="error" title="Error" className="mt-4">
              {error}
            </Alert>
          )}
        </Card.Content>
      </Card>

      {/* Results */}
      {scoreData && scoreData.machine_groups.length === 0 && (
        <EmptyState
          title="No scores found"
          description="Try adjusting your filters to find scores"
        />
      )}

      {scoreData && scoreData.machine_groups.length > 0 && (
        <div className="space-y-4">
          {scoreData.machine_groups.map((group) => (
            <MachineScoreCard
              key={group.machine_key}
              group={group}
              isExpanded={expandedMachines.has(group.machine_key)}
              onToggle={() => toggleMachine(group.machine_key)}
              onLoadMore={() => loadMoreScores(group.machine_key)}
              isLoadingMore={loadingMore.has(group.machine_key)}
              formatScore={formatScore}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface MachineScoreCardProps {
  group: MachineScoreGroup;
  isExpanded: boolean;
  onToggle: () => void;
  onLoadMore: () => void;
  isLoadingMore: boolean;
  formatScore: (score: number) => string;
}

function MachineScoreCard({
  group,
  isExpanded,
  onToggle,
  onLoadMore,
  isLoadingMore,
  formatScore,
}: MachineScoreCardProps) {
  return (
    <div
      className="border rounded-lg overflow-hidden"
      style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg)' }}
    >
      {/* Header - always visible */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center gap-3">
          <svg
            className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="font-semibold text-lg">{group.machine_name}</span>
          <Badge variant="default">{group.stats.count} scores</Badge>
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span>Median: <strong className="text-blue-600">{formatScore(group.stats.median)}</strong></span>
          <span className="hidden sm:inline">Range: {formatScore(group.stats.min)} - {formatScore(group.stats.max)}</span>
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t" style={{ borderColor: 'var(--border)' }}>
          {/* Desktop table view */}
          <div className="hidden md:block">
            <Table>
              <Table.Header>
                <Table.Row>
                  <Table.Head className="w-32">Score</Table.Head>
                  <Table.Head>Player</Table.Head>
                  <Table.Head>Team</Table.Head>
                  <Table.Head>Venue</Table.Head>
                  <Table.Head className="w-24">Date</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {group.scores.map((score, idx) => (
                  <Table.Row key={`${score.player_key}-${score.date}-${idx}`}>
                    <Table.Cell className="font-semibold text-blue-600">
                      {formatScore(score.score)}
                    </Table.Cell>
                    <Table.Cell>
                      <a
                        href={`/players/${score.player_key}`}
                        className="text-blue-600 hover:underline"
                      >
                        {score.player_name}
                      </a>
                    </Table.Cell>
                    <Table.Cell>{score.team_name}</Table.Cell>
                    <Table.Cell>{score.venue_name}</Table.Cell>
                    <Table.Cell className="text-gray-500 text-sm">
                      {score.date || '-'}
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>
          </div>

          {/* Mobile card view */}
          <div className="md:hidden divide-y" style={{ borderColor: 'var(--border)' }}>
            {group.scores.map((score, idx) => (
              <div
                key={`${score.player_key}-${score.date}-${idx}`}
                className="px-4 py-3"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-blue-600 text-lg">
                    {formatScore(score.score)}
                  </span>
                  <span className="text-xs text-gray-500">{score.date || '-'}</span>
                </div>
                <div className="text-sm">
                  <a
                    href={`/players/${score.player_key}`}
                    className="text-blue-600 hover:underline font-medium"
                  >
                    {score.player_name}
                  </a>
                  <span className="text-gray-500"> · {score.team_name}</span>
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {score.venue_name}
                </div>
              </div>
            ))}
          </div>

          {/* Load more button */}
          {group.has_more && (
            <div className="px-4 py-3 border-t flex justify-center" style={{ borderColor: 'var(--border)' }}>
              <Button
                onClick={onLoadMore}
                disabled={isLoadingMore}
                variant="secondary"
                size="sm"
              >
                {isLoadingMore ? (
                  <span className="flex items-center gap-2">
                    <LoadingSpinner size="sm" />
                    Loading...
                  </span>
                ) : (
                  `Load more (${group.stats.count - group.scores.length} remaining)`
                )}
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
