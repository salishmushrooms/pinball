import { TeamListResponse } from '@/lib/types';
import { TeamsClient } from './TeamsClient';

// Revalidate weekly (7 days) - can also be triggered on-demand after ETL
export const revalidate = 604800;

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getTeams(): Promise<TeamListResponse> {
  const res = await fetch(`${API_BASE_URL}/teams?limit=500`, {
    next: { revalidate: 604800 },
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch teams: ${res.status}`);
  }

  return res.json();
}

export default async function TeamsPage() {
  const data = await getTeams();

  return <TeamsClient teams={data.teams} />;
}
