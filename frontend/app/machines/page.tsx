'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useMachines, useMachineDashboardStats } from '@/lib/queries';
import {
  Card,
  PageHeader,
  Input,
  Alert,
  EmptyState,
  Table,
  LoadingSpinner,
} from '@/components/ui';
import { MachineDashboard } from '@/components/MachineDashboard';

export default function MachinesPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Fetch dashboard stats (cached)
  const { data: dashboardStats, isLoading: dashboardLoading } = useMachineDashboardStats();

  // Fetch machines based on search (only when search term is not empty)
  const { data: machinesData, isLoading: loading, error } = useMachines(
    debouncedSearch.trim() ? { limit: 100, search: debouncedSearch } : undefined,
    { enabled: !!debouncedSearch.trim() }
  );

  const machines = machinesData?.machines ?? [];

  // Format large scores for display (e.g., 1.2M, 500K)
  function formatScore(score: number | null | undefined): string {
    if (score === null || score === undefined) return '-';
    if (score >= 1_000_000_000) return `${(score / 1_000_000_000).toFixed(1)}B`;
    if (score >= 1_000_000) return `${(score / 1_000_000).toFixed(1)}M`;
    if (score >= 1_000) return `${(score / 1_000).toFixed(1)}K`;
    return score.toLocaleString();
  }

  return (
    <div className="space-y-4">
      {/* Page Header */}
      <PageHeader
        title="Machines"
        description="Browse and search pinball machine statistics"
      />

      {/* Search Filters */}
      <Card>
        <Card.Content>
          <div className="max-w-md">
            <Input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Type to search machines..."
            />
          </div>

          {loading && (
            <div className="mt-4 text-sm" style={{ color: 'var(--text-muted)' }}>
              Searching...
            </div>
          )}
        </Card.Content>
      </Card>

      {/* Error State */}
      {error && (
        <Alert variant="error" title="Error">
          {error instanceof Error ? error.message : 'Failed to fetch machines'}
        </Alert>
      )}

      {/* Dashboard - shown when no search term */}
      {!searchTerm.trim() && !dashboardLoading && dashboardStats && (
        <MachineDashboard stats={dashboardStats} />
      )}

      {/* Dashboard Loading State */}
      {!searchTerm.trim() && dashboardLoading && (
        <LoadingSpinner fullPage={false} text="Loading dashboard..." />
      )}

      {/* Empty State - no results found */}
      {!loading && !error && machines.length === 0 && searchTerm.trim() && (
        <Card>
          <Card.Content>
            <EmptyState
              title="No machines found"
              description="No machines found matching your criteria. Try adjusting your search."
            />
          </Card.Content>
        </Card>
      )}

      {/* Machines Table */}
      {machines.length > 0 && (
        <Card>
          <Table>
            <Table.Header>
              <Table.Row hoverable={false}>
                <Table.Head>Machine Name</Table.Head>
                <Table.Head className="text-right">Scores</Table.Head>
                <Table.Head className="text-right">Median Score</Table.Head>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {machines.map((machine) => (
                <Table.Row key={machine.machine_key}>
                  <Table.Cell>
                    <Link
                      href={`/machines/${machine.machine_key}`}
                      className="font-medium"
                      style={{ color: 'var(--text-link)' }}
                    >
                      {machine.machine_name}
                    </Link>
                  </Table.Cell>
                  <Table.Cell className="text-right">
                    {machine.game_count?.toLocaleString() ?? '-'}
                  </Table.Cell>
                  <Table.Cell className="text-right">
                    {formatScore(machine.median_score)}
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </Card>
      )}

      {/* Results Count */}
      {machines.length > 0 && (
        <div className="text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
          Showing {machines.length} machine{machines.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
