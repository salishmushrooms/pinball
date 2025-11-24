'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { ApiInfo } from '@/lib/types';

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
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        <strong className="font-bold">Error: </strong>
        <span>{error}</span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          MNP Analyzer
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Minnesota Pinball League Data Analysis Platform
        </p>
      </div>

      {apiInfo && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold text-gray-900 mb-4">
            Data Summary
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {apiInfo.data_summary.total_players.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600 mt-1">Players</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {apiInfo.data_summary.total_machines.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600 mt-1">Machines</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">
                {apiInfo.data_summary.total_matches.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600 mt-1">Matches</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">
                {apiInfo.data_summary.total_scores.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600 mt-1">Scores</div>
            </div>
          </div>
          <div className="mt-4 text-center text-sm text-gray-600">
            Seasons Available: {apiInfo.data_summary.seasons_available.join(', ')}
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        <Link
          href="/players"
          className="block bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Browse Players
          </h3>
          <p className="text-gray-600">
            Search and analyze player performance across machines and venues
          </p>
        </Link>

        <Link
          href="/machines"
          className="block bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Browse Machines
          </h3>
          <p className="text-gray-600">
            Explore machine statistics and percentile distributions
          </p>
        </Link>
      </div>
    </div>
  );
}
