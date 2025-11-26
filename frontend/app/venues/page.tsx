'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Venue } from '@/lib/types';
import {
  Card,
  PageHeader,
  Input,
  Alert,
  LoadingSpinner,
  EmptyState,
  Table,
} from '@/components/ui';

export default function VenuesPage() {
  const [venues, setVenues] = useState<Venue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    async function fetchVenues() {
      try {
        const data = await api.getVenues({ limit: 500 });
        setVenues(data.venues);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch venues');
      } finally {
        setLoading(false);
      }
    }

    fetchVenues();
  }, []);

  const filteredVenues = venues.filter((venue) =>
    venue.venue_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <LoadingSpinner fullPage text="Loading venues..." />;
  }

  if (error) {
    return (
      <Alert variant="error" title="Error">
        {error}
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Venues"
        description="Browse all MNP venues and view their machine lineups"
      />

      <Card>
        <Card.Content>
          <Input
            type="text"
            placeholder="Search venues..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </Card.Content>
      </Card>

      {filteredVenues.length === 0 ? (
        <Card>
          <Card.Content>
            <EmptyState
              title="No venues found"
              description={searchTerm ? `No venues match "${searchTerm}"` : 'No venues available'}
            />
          </Card.Content>
        </Card>
      ) : (
        <Card>
          <Card.Content>
            <Table>
              <Table.Header>
                <Table.Row hoverable={false}>
                  <Table.Head>Venue Name</Table.Head>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {filteredVenues.map((venue) => (
                  <Table.Row key={venue.venue_key}>
                    <Table.Cell>
                      <Link
                        href={`/venues/${venue.venue_key}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-800"
                      >
                        {venue.venue_name}
                      </Link>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>
          </Card.Content>
        </Card>
      )}

      <div className="text-center text-sm text-gray-600">
        Showing {filteredVenues.length} of {venues.length} venue{venues.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
}
