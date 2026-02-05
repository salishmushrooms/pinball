'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import {
  ScoreBrowseResponse,
  MachineScoreGroup,
  Team,
  Venue,
  Machine,
  ScoreItem,
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
import { MachineMultiSelect } from '@/components/MachineMultiSelect';
import { SUPPORTED_SEASONS } from '@/lib/utils';

type SortField = 'score' | 'player_name' | 'team_name' | 'date';
type SortOrder = 'asc' | 'desc';

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
  const [selectedMachines, setSelectedMachines] = useState<string[]>([]);
  const [includeAllVenues, setIncludeAllVenues] = useState(false);

  // Sorting state
  const [sortField, setSortField] = useState<SortField>('score');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  // Data state
  const [teams, setTeams] = useState<Team[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [allMachines, setAllMachines] = useState<Machine[]>([]);
  const [venueMachineKeys, setVenueMachineKeys] = useState<string[]>([]);
  const [scoreData, setScoreData] = useState<ScoreBrowseResponse | null>(null);
  const [expandedMachines, setExpandedMachines] = useState<Set<string>>(new Set());
  const [loadingMore, setLoadingMore] = useState<Set<string>>(new Set());

  // UI state
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [machineWarningDismissed, setMachineWarningDismissed] = useState(false);

  // Compute machine-venue mismatch
  const machineVenueMismatch = (() => {
    if (!selectedVenue || venueMachineKeys.length === 0 || selectedMachines.length === 0) {
      return null;
    }
    const venueSet = new Set(venueMachineKeys);
    const machinesAtVenue = selectedMachines.filter(m => venueSet.has(m));
    const machinesNotAtVenue = selectedMachines.filter(m => !venueSet.has(m));

    if (machinesNotAtVenue.length === 0) {
      return null; // All selected machines are at the venue
    }

    return {
      atVenue: machinesAtVenue.length,
      notAtVenue: machinesNotAtVenue.length,
      total: selectedMachines.length,
    };
  })();

  // Reset warning dismissal when venue changes
  useEffect(() => {
    setMachineWarningDismissed(false);
  }, [selectedVenue]);

  // Initialize from URL params
  useEffect(() => {
    const seasonsParam = searchParams.get('seasons');
    const teamsParam = searchParams.get('teams');
    const venueParam = searchParams.get('venue');
    const machinesParam = searchParams.get('machines');
    const allVenuesParam = searchParams.get('all_venues');
    const sortParam = searchParams.get('sort');
    const orderParam = searchParams.get('order');

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

    if (machinesParam) {
      setSelectedMachines(machinesParam.split(','));
    }

    if (allVenuesParam === 'true') {
      setIncludeAllVenues(true);
    }

    if (sortParam && ['score', 'player_name', 'team_name', 'date'].includes(sortParam)) {
      setSortField(sortParam as SortField);
    }

    if (orderParam && ['asc', 'desc'].includes(orderParam)) {
      setSortOrder(orderParam as SortOrder);
    }
  }, [searchParams]);

  // Load teams, venues, and machines
  useEffect(() => {
    async function loadFilterOptions() {
      try {
        const [teamsResponse, venuesResponse, machinesResponse] = await Promise.all([
          api.getTeams({ limit: 500 }),
          api.getVenues({ limit: 200 }),
          api.getMachines({ limit: 500 }),
        ]);
        // Deduplicate teams by team_key, keeping the most recent season's name
        // Sort by season ascending so the newest entry (last) is kept by the Map
        const sortedTeams = [...teamsResponse.teams].sort((a, b) => a.season - b.season);
        const uniqueTeams = Array.from(
          new Map(sortedTeams.map(t => [t.team_key, t])).values()
        );
        setTeams(uniqueTeams);
        setVenues(venuesResponse.venues);
        setAllMachines(machinesResponse.machines);
      } catch (err) {
        console.error('Failed to load filter options:', err);
      } finally {
        setInitialLoading(false);
      }
    }
    loadFilterOptions();
  }, []);

  // Load venue machines when venue changes
  useEffect(() => {
    async function loadVenueMachines() {
      if (!selectedVenue) {
        setVenueMachineKeys([]);
        return;
      }

      try {
        const machineKeys = await api.getVenueCurrentMachines(selectedVenue);
        setVenueMachineKeys(machineKeys);
        // Auto-select venue machines if no machines were previously selected
        if (selectedMachines.length === 0) {
          setSelectedMachines(machineKeys);
        }
      } catch (err) {
        console.error('Failed to load venue machines:', err);
        setVenueMachineKeys([]);
      }
    }
    loadVenueMachines();
  }, [selectedVenue]); // eslint-disable-line react-hooks/exhaustive-deps

  // Update URL when filters change
  const updateUrl = useCallback((
    newSeasons: number[],
    newTeams: string[],
    newVenue: string,
    newMachines: string[],
    newAllVenues: boolean,
    newSortField: SortField,
    newSortOrder: SortOrder
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
    if (newMachines.length > 0) {
      params.set('machines', newMachines.join(','));
    }
    if (newAllVenues && newVenue) {
      params.set('all_venues', 'true');
    }
    if (newSortField !== 'score') {
      params.set('sort', newSortField);
    }
    if (newSortOrder !== 'desc') {
      params.set('order', newSortOrder);
    }
    const queryString = params.toString();
    router.replace(`/scores${queryString ? `?${queryString}` : ''}`, { scroll: false });
  }, [router]);

  // Sort scores within a machine group
  const sortScores = useCallback((scores: ScoreItem[]): ScoreItem[] => {
    return [...scores].sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'score':
          comparison = a.score - b.score;
          break;
        case 'player_name':
          comparison = (a.player_name || '').localeCompare(b.player_name || '');
          break;
        case 'team_name':
          comparison = (a.team_name || '').localeCompare(b.team_name || '');
          break;
        case 'date':
          comparison = (a.date || '').localeCompare(b.date || '');
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  }, [sortField, sortOrder]);

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
        machine_keys: selectedMachines.length > 0 ? selectedMachines : undefined,
        include_all_venues: includeAllVenues,
        scores_per_machine: 20,
      });
      setScoreData(response);

      // Auto-expand first 3 machines
      const firstThree = response.machine_groups.slice(0, 3).map(g => g.machine_key);
      setExpandedMachines(new Set(firstThree));

      // Update URL
      updateUrl(seasons, selectedTeams, selectedVenue, selectedMachines, includeAllVenues, sortField, sortOrder);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scores');
    } finally {
      setLoading(false);
    }
  }, [seasons, selectedTeams, selectedVenue, selectedMachines, includeAllVenues, sortField, sortOrder, updateUrl]);

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
                if (!value) {
                  setIncludeAllVenues(false);
                  setSelectedMachines([]);
                }
              }}
              venues={venues.map(v => ({ venue_key: v.venue_key, venue_name: v.venue_name }))}
              label="Venue"
            />

            <MachineMultiSelect
              value={selectedMachines}
              onChange={setSelectedMachines}
              machines={allMachines.map(m => ({ machine_key: m.machine_key, machine_name: m.machine_name }))}
              label="Machines"
              placeholder={selectedVenue && venueMachineKeys.length > 0 ? `${venueMachineKeys.length} at venue` : 'All Machines'}
              helpText={selectedVenue && venueMachineKeys.length > 0 ? 'Auto-filled from venue' : undefined}
            />
          </div>

          {/* Advanced options */}
          {selectedVenue && (
            <div className="mt-4 flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeAllVenues}
                  onChange={(e) => setIncludeAllVenues(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-600">
                  Include scores from all venues for selected machines
                </span>
              </label>
            </div>
          )}

          {/* Machine-venue mismatch warning */}
          {machineVenueMismatch && !machineWarningDismissed && (
            <Alert variant="warning" className="mt-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <strong>{machineVenueMismatch.notAtVenue} of {machineVenueMismatch.total}</strong> selected machines aren&apos;t at this venue.
                  {machineVenueMismatch.atVenue > 0 && (
                    <span className="text-gray-600"> ({machineVenueMismatch.atVenue} match)</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      setSelectedMachines(venueMachineKeys);
                      setMachineWarningDismissed(true);
                    }}
                  >
                    Use venue machines
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setMachineWarningDismissed(true)}
                  >
                    Keep selection
                  </Button>
                </div>
              </div>
            </Alert>
          )}

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
          {/* Sorting controls */}
          <div className="flex items-center justify-end gap-4">
            <span className="text-sm text-gray-500">Sort by:</span>
            <select
              value={sortField}
              onChange={(e) => setSortField(e.target.value as SortField)}
              className="text-sm border rounded px-2 py-1"
              style={{ backgroundColor: 'var(--input-bg)', borderColor: 'var(--input-border)' }}
            >
              <option value="score">Score</option>
              <option value="player_name">Player</option>
              <option value="team_name">Team</option>
              <option value="date">Date</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="text-sm px-2 py-1 border rounded hover:bg-gray-100 dark:hover:bg-gray-800"
              style={{ borderColor: 'var(--input-border)' }}
              title={sortOrder === 'asc' ? 'Ascending' : 'Descending'}
            >
              {sortOrder === 'asc' ? '↑ Asc' : '↓ Desc'}
            </button>
          </div>

          {scoreData.machine_groups.map((group) => (
            <MachineScoreCard
              key={group.machine_key}
              group={group}
              sortedScores={sortScores(group.scores)}
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
  sortedScores: ScoreItem[];
  isExpanded: boolean;
  onToggle: () => void;
  onLoadMore: () => void;
  isLoadingMore: boolean;
  formatScore: (score: number) => string;
}

function MachineScoreCard({
  group,
  sortedScores,
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
                {sortedScores.map((score, idx) => (
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
            {sortedScores.map((score, idx) => (
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
