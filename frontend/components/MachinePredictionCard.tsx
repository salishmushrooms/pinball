'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { MachinePredictionResponse } from '@/lib/types';
import { Card, Badge, Alert, LoadingSpinner, EmptyState } from '@/components/ui';

interface MachinePredictionCardProps {
  teamKey: string;
  teamName: string;
  roundNum: 1 | 4;
  venueKey: string;
  seasons?: number[];
  limit?: number;
}

export function MachinePredictionCard({
  teamKey,
  teamName,
  roundNum,
  venueKey,
  seasons = [21, 22],
  limit = 5,
}: MachinePredictionCardProps) {
  const [data, setData] = useState<MachinePredictionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPredictions() {
      setLoading(true);
      setError(null);

      try {
        const response = await api.getMachinePredictions({
          team_key: teamKey,
          round_num: roundNum,
          venue_key: venueKey,
          seasons,
          limit,
        });
        setData(response);
      } catch (err) {
        console.error('Failed to load predictions:', err);
        setError(err instanceof Error ? err.message : 'Failed to load predictions');
      } finally {
        setLoading(false);
      }
    }

    if (teamKey && venueKey) {
      loadPredictions();
    }
  }, [teamKey, roundNum, venueKey, seasons, limit]);

  const title = roundNum === 1
    ? `Round 1 Prediction (${teamName} picks)`
    : `Round 4 Prediction (${teamName} picks)`;

  const description = roundNum === 1
    ? 'Away team picks machines in Round 1'
    : 'Home team picks machines in Round 4';

  return (
    <Card>
      <Card.Header>
        <div className="flex items-start justify-between">
          <div>
            <Card.Title>{title}</Card.Title>
            <p className="text-sm text-gray-500 mt-1">{description}</p>
          </div>
          {data && data.sample_size > 0 && (
            <Badge variant="info">
              {data.sample_size} opportunities
            </Badge>
          )}
        </div>
      </Card.Header>
      <Card.Content>
        {loading && (
          <div className="flex items-center justify-center py-8">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {error && (
          <Alert variant="error" title="Error loading predictions">
            {error}
          </Alert>
        )}

        {!loading && !error && data && (() => {
          // Always filter to only show machines available at the venue
          const displayPredictions = data.predictions.filter(p => p.available_at_venue);

          return (
            <>
              {displayPredictions.length === 0 ? (
                <EmptyState
                  title="No predictions available"
                  description={
                    data.predictions.length > 0
                      ? "This team's historically picked machines are not available at this venue"
                      : data.message || `No historical data available for ${teamName} in this context`
                  }
                />
              ) : (
                <div className="space-y-3">
                  {displayPredictions.map((prediction, index) => (
                  <div
                    key={prediction.machine_key}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center gap-3 flex-1">
                      <div className="text-lg font-semibold text-gray-400 w-6">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">
                            {prediction.machine_name}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-xs">
                            <div
                              className="h-2 rounded-full bg-blue-600"
                              style={{ width: `${prediction.confidence_pct}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-600 w-12 text-right">
                            {prediction.confidence_pct}%
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-xs text-gray-500">
                          {prediction.pick_count}/{prediction.opportunities || '?'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}

                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    Pick rate based on {data.context} rounds across {data.seasons_analyzed.length > 1 ? 'seasons' : 'season'} {data.seasons_analyzed.join(', ')}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Only showing machines available at this venue (min 3 opportunities)
                  </p>
                </div>
              </div>
            )}
          </>
          );
        })()}
      </Card.Content>
    </Card>
  );
}
