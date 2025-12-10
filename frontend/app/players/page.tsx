'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Player } from '@/lib/types';
import {
  Card,
  PageHeader,
  Input,
  Alert,
  EmptyState,
  Table,
} from '@/components/ui';

export default function PlayersPage() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Live search - fetch as user types
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchPlayers();
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchTerm]);

  async function fetchPlayers() {
    setLoading(true);
    setError(null);
    try {
      const params: any = {
        limit: 100,
      };

      if (searchTerm) params.search = searchTerm;

      const response = await api.getPlayers(params);
      setPlayers(response.players);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch players');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Players"
        description="Browse and search player statistics"
      />

      {/* Search Filters */}
      <Card>
        <Card.Content>
          <div className="max-w-md">
            <Input
              label="Search Name"
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Type to search players..."
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

      {/* Empty State */}
      {!loading && !error && players.length === 0 && searchTerm && (
        <Card>
          <Card.Content>
            <EmptyState
              title="No players found"
              description="No players found matching your criteria. Try adjusting your search."
            />
          </Card.Content>
        </Card>
      )}

      {/* Players Table */}
      {players.length > 0 && (
        <Card>
          <Table>
            <Table.Header>
              <Table.Row hoverable={false}>
                <Table.Head>Player Name</Table.Head>
                <Table.Head>IPR</Table.Head>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {players.map((player) => (
                <Table.Row key={player.player_key}>
                  <Table.Cell>
                    <Link
                      href={`/players/${player.player_key}`}
                      className="font-medium"
                      style={{ color: 'var(--text-link)' }}
                    >
                      {player.name}
                    </Link>
                  </Table.Cell>
                  <Table.Cell>
                    {player.current_ipr ? Math.round(player.current_ipr) : 'N/A'}
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </Card>
      )}

      {/* Results Count */}
      {players.length > 0 && (
        <div className="text-center text-sm" style={{ color: 'var(--text-secondary)' }}>
          Showing {players.length} player{players.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
