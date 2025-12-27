'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { ApiInfo } from '@/lib/types';
import {
  Card,
  PageHeader,
  Alert,
  LoadingSpinner,
  StatCard,
} from '@/components/ui';

export default function Home() {
  const [apiInfo, setApiInfo] = useState<ApiInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await api.getApiInfo();
        setApiInfo(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return <LoadingSpinner fullPage text="Loading..." />;
  }

  if (error) {
    return (
      <Alert variant="error" title="Error">
        {error}
      </Alert>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="MNP Analyzer"
        description="Monday Night Pinball Data Analysis Platform"
      />

      {apiInfo && (
        <Card>
          <Card.Header>
            <Card.Title>Data Summary</Card.Title>
          </Card.Header>
          <Card.Content>
            <p className="mb-4" style={{ color: 'var(--text-secondary)' }}>{apiInfo.data_summary.description}</p>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <StatCard
                label="Players"
                value={apiInfo.data_summary.players.toLocaleString()}
              />
              <StatCard
                label="Machines"
                value={apiInfo.data_summary.machines.toLocaleString()}
              />
              <StatCard
                label="Venues"
                value={apiInfo.data_summary.venues.toLocaleString()}
              />
              <StatCard
                label="Teams"
                value={apiInfo.data_summary.teams.toLocaleString()}
              />
              <StatCard
                label="Matches"
                value={apiInfo.data_summary.matches.toLocaleString()}
              />
              <StatCard
                label="Scores"
                value={apiInfo.data_summary.total_scores}
              />
            </div>
          </Card.Content>
        </Card>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card variant="interactive" href="/players">
          <Card.Content>
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
              Players
            </h3>
            <p style={{ color: 'var(--text-secondary)' }}>
              Search and analyze player performance across machines and venues
            </p>
          </Card.Content>
        </Card>

        <Card variant="interactive" href="/teams">
          <Card.Content>
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
              Teams
            </h3>
            <p style={{ color: 'var(--text-secondary)' }}>
              View team rosters, performance, and season standings
            </p>
          </Card.Content>
        </Card>

        <Card variant="interactive" href="/machines">
          <Card.Content>
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
              Machines
            </h3>
            <p style={{ color: 'var(--text-secondary)' }}>
              Explore machine statistics and percentile distributions
            </p>
          </Card.Content>
        </Card>

        <Card variant="interactive" href="/venues">
          <Card.Content>
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
              Venues
            </h3>
            <p style={{ color: 'var(--text-secondary)' }}>
              View venue locations and their current machine lineups
            </p>
          </Card.Content>
        </Card>

        <Card variant="interactive" href="/matchups">
          <Card.Content>
            <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
              Matchups
            </h3>
            <p style={{ color: 'var(--text-secondary)' }}>
              Analyze team vs team matchups with predictions
            </p>
          </Card.Content>
        </Card>
      </div>
    </div>
  );
}
