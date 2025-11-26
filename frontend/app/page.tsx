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
            <p className="text-gray-600 mb-4">{apiInfo.data_summary.description}</p>
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

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card variant="interactive" href="/players">
          <Card.Content>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Browse Players
            </h3>
            <p className="text-gray-600">
              Search and analyze player performance across machines and venues
            </p>
          </Card.Content>
        </Card>

        <Card variant="interactive" href="/machines">
          <Card.Content>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Browse Machines
            </h3>
            <p className="text-gray-600">
              Explore machine statistics and percentile distributions
            </p>
          </Card.Content>
        </Card>

        <Card variant="interactive" href="/venues">
          <Card.Content>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Browse Venues
            </h3>
            <p className="text-gray-600">
              View venue locations and their current machine lineups
            </p>
          </Card.Content>
        </Card>

        <Card variant="interactive" href="/matchups">
          <Card.Content>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Matchup Analysis
            </h3>
            <p className="text-gray-600">
              Analyze team vs team matchups with score predictions and strategies
            </p>
          </Card.Content>
        </Card>
      </div>
    </div>
  );
}
