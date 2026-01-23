import { VenueWithStatsListResponse } from '@/lib/types';
import { VenuesClient } from './VenuesClient';

// Revalidate weekly (7 days) - can also be triggered on-demand after ETL
export const revalidate = 604800;

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getVenuesWithStats(): Promise<VenueWithStatsListResponse> {
  // Fetch all venues (including inactive) so client can toggle
  const res = await fetch(`${API_BASE_URL}/venues/with-stats?limit=500&active_only=false`, {
    next: { revalidate: 604800 },
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch venues: ${res.status}`);
  }

  return res.json();
}

export default async function VenuesPage() {
  const data = await getVenuesWithStats();

  return <VenuesClient venues={data.venues} />;
}
