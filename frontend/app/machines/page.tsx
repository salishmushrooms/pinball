'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Machine } from '@/lib/types';
import {
  Card,
  PageHeader,
  Input,
  Alert,
  LoadingSpinner,
  EmptyState,
  Table,
} from '@/components/ui';

export default function MachinesPage() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Live search - fetch as user types (searches both name and key)
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchMachines();
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchTerm]);

  async function fetchMachines() {
    setLoading(true);
    setError(null);
    try {
      const params: any = {
        limit: 200,
      };

      if (searchTerm) params.search = searchTerm;

      const response = await api.getMachines(params);
      setMachines(response.machines);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch machines');
    } finally {
      setLoading(false);
    }
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
          {loading && (
            <div className="mt-4">
              <LoadingSpinner size="sm" text="Searching..." />
            </div>
          )}
        </Card.Content>
      </Card>

      {error && (
        <Alert variant="error" title="Error">
          {error}
        </Alert>
      )}

      {!loading && !error && machines.length === 0 && searchTerm && (
        <Card>
          <Card.Content>
            <EmptyState
              title="No machines found"
              description={`No machines found matching "${searchTerm}". Try a different search term.`}
            />
          </Card.Content>
        </Card>
      )}

      {machines.length > 0 && (
        <Card>
          <Card.Content>
            <Table>
              <Table.Header>
                <Table.Row hoverable={false}>
                  <Table.Head>Machine Name</Table.Head>
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
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>
          </Card.Content>
        </Card>
      )}

      {machines.length > 0 && (
        <div className="text-center text-sm text-gray-600">
          Showing {machines.length} machine{machines.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
