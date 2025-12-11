'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Machine, Venue } from '@/lib/types';
import {
  Card,
  PageHeader,
  Input,
  Alert,
  LoadingSpinner,
  EmptyState,
  Table,
  FilterPanel,
  ContentContainer,
} from '@/components/ui';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';
import { VenueSelect } from '@/components/VenueMultiSelect';
import { SUPPORTED_SEASONS, filterSupportedSeasons } from '@/lib/utils';

// Format large scores for display (e.g., 1.2M, 500K)
function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return '-';
  if (score >= 1_000_000_000) return `${(score / 1_000_000_000).toFixed(1)}B`;
  if (score >= 1_000_000) return `${(score / 1_000_000).toFixed(1)}M`;
  if (score >= 1_000) return `${(score / 1_000).toFixed(1)}K`;
  return score.toLocaleString();
}

export default function MachinesPage() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Filter state
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([...SUPPORTED_SEASONS]);
  const [selectedSeasons, setSelectedSeasons] = useState<number[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [selectedVenue, setSelectedVenue] = useState<string>('');

  // Sort state
  type SortField = 'machine_name' | 'game_count';
  type SortDirection = 'asc' | 'desc';
  const [sortField, setSortField] = useState<SortField>('machine_name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  // Load available seasons and venues on mount
  useEffect(() => {
    async function loadFilterOptions() {
      try {
        const [seasonsRes, venuesRes] = await Promise.all([
          api.getSeasons(),
          api.getVenues({ limit: 100 }),
        ]);
        setAvailableSeasons(filterSupportedSeasons(seasonsRes.seasons));
        setVenues(venuesRes.venues);
      } catch (err) {
        console.error('Failed to load filter options:', err);
      }
    }
    loadFilterOptions();
  }, []);

  // Live search - fetch as user types (searches both name and key)
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchMachines();
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchTerm, selectedSeasons, selectedVenue]);

  async function fetchMachines() {
    setLoading(true);
    setError(null);
    try {
      const params: any = {
        limit: 200,
      };

      if (searchTerm) params.search = searchTerm;
      // Only include season filter if a single season is selected
      if (selectedSeasons.length === 1) {
        params.season = selectedSeasons[0];
      }
      if (selectedVenue) params.venue_key = selectedVenue;

      const response = await api.getMachines(params);
      setMachines(response.machines);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch machines');
    } finally {
      setLoading(false);
    }
  }

  // Count active filters for FilterPanel badge
  const activeFilterCount =
    (selectedSeasons.length > 0 ? 1 : 0) + (selectedVenue ? 1 : 0);

  function clearFilters() {
    setSelectedSeasons([]);
    setSelectedVenue('');
  }

  // Sort handler
  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection(field === 'game_count' ? 'desc' : 'asc');
    }
  }

  // Filter out machines with zero scores, then sort
  const filteredMachines = machines.filter((m) => (m.game_count ?? 0) > 0);
  const sortedMachines = [...filteredMachines].sort((a, b) => {
    let comparison = 0;
    if (sortField === 'machine_name') {
      comparison = a.machine_name.localeCompare(b.machine_name);
    } else if (sortField === 'game_count') {
      comparison = (a.game_count ?? 0) - (b.game_count ?? 0);
    }
    return sortDirection === 'asc' ? comparison : -comparison;
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Machines"
        description="Browse pinball machines and view performance statistics"
      />

      {/* Sticky search bar on mobile for better UX while typing */}
      <div className="sticky top-0 z-10 -mx-4 px-4 py-2 md:static md:mx-0 md:px-0 md:py-0" style={{ backgroundColor: 'var(--bg-primary)' }}>
        <Card>
          <Card.Content>
            <div className="space-y-2">
              <Input
                label="Search by Name or Machine Key"
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Type machine name or key (e.g., 'Medieval Madness' or 'MM')..."
                helpText="Tip: Try searching by abbreviations like 'TOTAN', 'MM', 'AFM', etc."
              />
              {/* Inline results count - shows immediately as user types */}
              <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                {loading ? (
                  <span className="flex items-center gap-1">
                    <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Searching...
                  </span>
                ) : (
                  <span>
                    {filteredMachines.length} machine{filteredMachines.length !== 1 ? 's' : ''} found
                    {activeFilterCount > 0 && ' (filtered)'}
                  </span>
                )}
              </div>
            </div>
          </Card.Content>
        </Card>
      </div>

      <FilterPanel
        title="Filters"
        collapsible={true}
        defaultOpen={false}
        activeFilterCount={activeFilterCount}
        showClearAll={activeFilterCount > 0}
        onClearAll={clearFilters}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <SeasonMultiSelect
            value={selectedSeasons}
            onChange={setSelectedSeasons}
            availableSeasons={availableSeasons}
            label="Season"
            helpText="Filter machines played in selected season"
            variant="dropdown"
          />
          <VenueSelect
            value={selectedVenue}
            onChange={setSelectedVenue}
            venues={venues}
            label="Venue"
          />
        </div>
      </FilterPanel>

      {loading && (
        <div className="flex justify-center py-8">
          <LoadingSpinner size="md" text="Loading machines..." />
        </div>
      )}

      {error && (
        <Alert variant="error" title="Error">
          {error}
        </Alert>
      )}

      {!loading && !error && machines.length === 0 && (searchTerm || activeFilterCount > 0) && (
        <Card>
          <Card.Content>
            <EmptyState
              title="No machines found"
              description={
                searchTerm
                  ? `No machines found matching "${searchTerm}". Try a different search term.`
                  : 'No machines found with the selected filters. Try adjusting your filters.'
              }
            />
          </Card.Content>
        </Card>
      )}

      {!loading && machines.length > 0 && (
        <ContentContainer size="md">
          <Card>
            <Card.Content>
              <Table>
                <Table.Header>
                  <Table.Row hoverable={false}>
                    <Table.Head
                      sortable
                      onSort={() => handleSort('machine_name')}
                      sortDirection={sortField === 'machine_name' ? sortDirection : null}
                    >
                      Machine Name
                    </Table.Head>
                    <Table.Head
                      className="text-right"
                      sortable
                      onSort={() => handleSort('game_count')}
                      sortDirection={sortField === 'game_count' ? sortDirection : null}
                    >
                      Scores
                    </Table.Head>
                    <Table.Head className="text-right">Median Score</Table.Head>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  {sortedMachines.map((machine) => (
                    <Table.Row key={machine.machine_key}>
                      <Table.Cell>
                        <Link
                          href={`/machines/${machine.machine_key}`}
                          className="text-sm font-medium text-blue-600 hover:text-blue-800"
                        >
                          {machine.machine_name}
                        </Link>
                      </Table.Cell>
                      <Table.Cell className="text-right text-sm text-gray-600">
                        {machine.game_count?.toLocaleString() ?? '-'}
                      </Table.Cell>
                      <Table.Cell className="text-right text-sm text-gray-600">
                        {formatScore(machine.median_score)}
                      </Table.Cell>
                    </Table.Row>
                  ))}
                </Table.Body>
              </Table>
            </Card.Content>
          </Card>
        </ContentContainer>
      )}

    </div>
  );
}
