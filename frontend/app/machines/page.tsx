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
  Select,
  FilterPanel,
} from '@/components/ui';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';

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
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([21, 22]);
  const [selectedSeasons, setSelectedSeasons] = useState<number[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [selectedVenue, setSelectedVenue] = useState<string>('');

  // Load available seasons and venues on mount
  useEffect(() => {
    async function loadFilterOptions() {
      try {
        const [seasonsRes, venuesRes] = await Promise.all([
          api.getSeasons(),
          api.getVenues({ limit: 100 }),
        ]);
        setAvailableSeasons(seasonsRes.seasons);
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

  return (
    <div className="space-y-6">
      <PageHeader
        title="Machines"
        description="Browse pinball machines and view performance statistics"
      />

      <Card>
        <Card.Content>
          <Input
            label="Search by Name or Machine Key"
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Type machine name or key (e.g., 'Medieval Madness' or 'MM')..."
            helpText="Tip: Try searching by abbreviations like 'TOTAN', 'MM', 'AFM', etc."
          />
        </Card.Content>
      </Card>

      <FilterPanel
        title="Filters"
        collapsible={true}
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
          />
          <Select
            label="Venue"
            value={selectedVenue}
            onChange={(e) => setSelectedVenue(e.target.value)}
            options={[
              { value: '', label: 'All Venues' },
              ...venues.map((v) => ({
                value: v.venue_key,
                label: v.venue_name,
              })),
            ]}
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
        <Card>
          <Card.Content>
            <Table>
              <Table.Header>
                <Table.Row hoverable={false}>
                  <Table.Head>Machine Name</Table.Head>
                  <Table.Head className="text-right">Games</Table.Head>
                  <Table.Head className="text-right">Median Score</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {machines.map((machine) => (
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
      )}

      {!loading && machines.length > 0 && (
        <div className="text-center text-sm text-gray-600">
          Showing {machines.length} machine{machines.length !== 1 ? 's' : ''}
          {activeFilterCount > 0 && ' (filtered)'}
        </div>
      )}
    </div>
  );
}
