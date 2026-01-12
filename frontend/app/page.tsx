'use client';

import { useApiInfo } from '@/lib/queries';
import {
  Card,
  PageHeader,
  Alert,
  LoadingSpinner,
  StatCard,
} from '@/components/ui';

// Simple SVG icons for stat cards
const icons = {
  players: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
  ),
  machines: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="6" width="20" height="12" rx="2"/>
      <circle cx="12" cy="12" r="2"/>
      <path d="M6 12h.01"/>
      <path d="M18 12h.01"/>
    </svg>
  ),
  venues: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
      <circle cx="12" cy="10" r="3"/>
    </svg>
  ),
  teams: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
      <circle cx="9" cy="7" r="4"/>
      <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
      <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  ),
  matchups: (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/>
      <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
      <path d="M4 22h16"/>
      <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/>
      <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/>
      <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>
    </svg>
  ),
};

export default function Home() {
  const { data: apiInfo, isLoading, error } = useApiInfo();

  if (isLoading) {
    return <LoadingSpinner fullPage text="Loading..." />;
  }

  if (error) {
    return (
      <Alert variant="error" title="Error">
        {error instanceof Error ? error.message : 'Failed to fetch data'}
      </Alert>
    );
  }

  return (
    <div className="space-y-8">
      <PageHeader
        title="Seattle MNP Data"
        description="Monday Night Pinball Data Analysis Platform"
      />

      {apiInfo && (
        <Card className="lg:max-w-[60%] lg:mx-auto">
          <Card.Header>
            <Card.Title>Data Summary</Card.Title>
          </Card.Header>
          <Card.Content>
            <p className="mb-4" style={{ color: 'var(--text-secondary)' }}>{apiInfo.data_summary.description}</p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              <StatCard
                label="Players"
                value={apiInfo.data_summary.players.toLocaleString()}
                icon={icons.players}
                href="/players"
              />
              <StatCard
                label="Machines"
                value={apiInfo.data_summary.machines.toLocaleString()}
                icon={icons.machines}
                href="/machines"
              />
              <StatCard
                label="Venues"
                value={apiInfo.data_summary.venues.toLocaleString()}
                icon={icons.venues}
                href="/venues"
              />
              <StatCard
                label="Teams"
                value={apiInfo.data_summary.teams.toLocaleString()}
                icon={icons.teams}
                href="/teams"
              />
              <StatCard
                label="Matchups"
                value="Season 23"
                icon={icons.matchups}
                href="/matchups"
              />
            </div>
          </Card.Content>
        </Card>
      )}
    </div>
  );
}
