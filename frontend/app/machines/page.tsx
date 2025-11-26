'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Machine } from '@/lib/types';

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
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Machines</h1>
        <p className="text-gray-600 mt-2">
          Browse pinball machines and view performance statistics
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search by Name or Machine Key
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Type machine name or key (e.g., 'Medieval Madness' or 'MM')..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Tip: Try searching by abbreviations like "TOTAN", "MM", "AFM", etc.
            </p>
          </div>
        </div>

        {loading && (
          <div className="mt-4 text-sm text-gray-500">
            Searching...
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <strong className="font-bold">Error: </strong>
          <span>{error}</span>
        </div>
      )}

      {!loading && !error && machines.length === 0 && searchTerm && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
          No machines found matching "{searchTerm}". Try a different search term.
        </div>
      )}

      {machines.length > 0 && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Machine Name
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {machines.map((machine) => (
                <tr
                  key={machine.machine_key}
                  className="hover:bg-gray-50 cursor-pointer"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      href={`/machines/${machine.machine_key}`}
                      className="block text-sm font-medium text-gray-900"
                    >
                      {machine.machine_name}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {machines.length > 0 && (
        <div className="text-center text-sm text-gray-600">
          Showing {machines.length} machine{machines.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
}
