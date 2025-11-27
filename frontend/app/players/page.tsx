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
  const [minIpr, setMinIpr] = useState('');

  // Live search - fetch as user types
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchPlayers();
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchTerm, minIpr]);

  async function fetchPlayers() {
    setLoading(true);
    setError(null);
    try {
      const params: any = {
        limit: 100,
      };

      if (searchTerm) params.search = searchTerm;
      if (minIpr) {
        const iprValue = parseInt(minIpr);
        if (iprValue >= 1 && iprValue <= 6) {
          params.min_ipr = iprValue;
        }
      }

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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Search Name"
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Type to search players..."
            />

            <Input
              label="Min IPR (1-6)"
              type="number"
              value={minIpr}
              onChange={(e) => setMinIpr(e.target.value)}
              placeholder="e.g., 3"
              min={1}
              max={6}
            />
          </div>

          {loading && (
            <div className="mt-4 text-sm text-gray-500">
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
      {!loading && !error && players.length === 0 && (searchTerm || minIpr) && (
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
                <Table.Head>Seasons</Table.Head>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {players.map((player) => (
                <Table.Row key={player.player_key}>
                  <Table.Cell>
                    <Link
                      href={`/players/${player.player_key}`}
                      className="font-medium text-blue-600 hover:text-blue-700"
                    >
                      {player.name}
                    </Link>
                  </Table.Cell>
                  <Table.Cell>
                    {player.current_ipr ? player.current_ipr.toFixed(2) : 'N/A'}
                  </Table.Cell>
                  <Table.Cell className="text-gray-500">
                    {player.first_seen_season} - {player.last_seen_season}
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </Card>
      )}

      {/* Results Count */}
      {players.length > 0 && (
        <div className="text-center text-sm text-gray-600">
          Showing {players.length} player{players.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
