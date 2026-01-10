'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Machine, MachineDashboardStats } from '@/lib/types';
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
  const [machines, setMachines] = useState<Machine[]>([]);
  const [dashboardStats, setDashboardStats] = useState<MachineDashboardStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch dashboard stats on mount
  useEffect(() => {
    async function fetchDashboardStats() {
      try {
        const stats = await api.getMachineDashboardStats();
        setDashboardStats(stats);
      } catch (err) {
        console.error('Failed to fetch dashboard stats:', err);
      } finally {
        setDashboardLoading(false);
      }
    }

    fetchDashboardStats();
  }, []);

  // Live search - fetch as user types (only when search term is not empty)
  useEffect(() => {
    if (!searchTerm.trim()) {
      setMachines([]);
      return;
    }

    const timer = setTimeout(() => {
      fetchMachines();
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchTerm]);

  async function fetchMachines() {
    if (!searchTerm.trim()) {
      setMachines([]);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await api.getMachines({
        limit: 100,
        search: searchTerm,
      });
      setMachines(response.machines);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch machines');
    } finally {
      setLoading(false);
    }
  }

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
          {error}
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
