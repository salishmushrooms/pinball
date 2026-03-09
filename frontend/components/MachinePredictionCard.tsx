'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { MachinePredictionResponse, MachinePickFrequency } from '@/lib/types';
import { Card, Badge, Alert, LoadingSpinner, EmptyState, Table } from '@/components/ui';

interface MachinePredictionCardProps {
  teamKey: string;
  teamName: string;
  roundNum: 1 | 2 | 3 | 4;
  venueKey: string;
  seasons?: number[];
  limit?: number;
  pickHistory?: MachinePickFrequency[];
}

function LikelihoodDot({ percentage }: { percentage: number }) {
  let color: string;
  if (percentage >= 60) {
    color = '#16a34a'; // green
  } else if (percentage >= 30) {
    color = '#ca8a04'; // yellow
  } else {
    color = '#dc2626'; // red
  }

  return (
    <span
      style={{
        display: 'inline-block',
        width: 12,
        height: 12,
        borderRadius: '50%',
        backgroundColor: color,
        flexShrink: 0,
      }}
      title={`${percentage}% pick rate`}
    />
  );
}

export function MachinePredictionCard({
  teamKey,
  teamName,
  roundNum,
  venueKey,
  seasons = [21, 22],
  limit = 5,
  pickHistory,
}: MachinePredictionCardProps) {
  const [data, setData] = useState<MachinePredictionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

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
          limit: 10,
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

  const roundType = roundNum === 1 || roundNum === 4 ? 'Doubles' : 'Singles';
  const title = `Round ${roundNum} — ${teamName} picks (${roundType})`;

  return (
    <Card>
      <Card.Header>
        <div className="flex items-start justify-between">
          <Card.Title className="text-base">{title}</Card.Title>
          {data && data.sample_size > 0 && (
            <Badge variant="info" className="text-xs">
              {data.sample_size} opps
            </Badge>
          )}
        </div>
      </Card.Header>
      <Card.Content>
        {loading && (
          <div className="flex items-center justify-center py-6">
            <LoadingSpinner size="lg" />
          </div>
        )}

        {error && (
          <Alert variant="error" title="Error loading predictions">
            {error}
          </Alert>
        )}

        {!loading && !error && data && (() => {
          const displayPredictions = data.predictions.filter(p => p.available_at_venue);
          const topPredictions = displayPredictions.slice(0, limit);
          const remainingPredictions = displayPredictions.slice(limit);

          // Merge remaining predictions with pick history for expanded view
          const expandedRows = expanded ? remainingPredictions : [];

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
                <>
                  <Table>
                    <Table.Header>
                      <Table.Row>
                        <Table.Head className="w-6">{' '}</Table.Head>
                        <Table.Head>Machine</Table.Head>
                        <Table.Head className="text-right">Pick%</Table.Head>
                        <Table.Head className="text-right">Win%</Table.Head>
                        <Table.Head className="text-right">Picks</Table.Head>
                      </Table.Row>
                    </Table.Header>
                    <Table.Body>
                      {topPredictions.map((prediction) => (
                        <Table.Row key={prediction.machine_key}>
                          <Table.Cell className="pr-0">
                            <LikelihoodDot percentage={prediction.confidence_pct} />
                          </Table.Cell>
                          <Table.Cell className="font-medium">
                            {prediction.machine_name}
                          </Table.Cell>
                          <Table.Cell className="text-right text-sm">
                            {prediction.confidence_pct}%
                          </Table.Cell>
                          <Table.Cell className="text-right text-sm">
                            {prediction.win_percentage != null ? (
                              <span style={{ color: prediction.win_percentage >= 50 ? '#16a34a' : 'var(--text-muted)' }}>
                                {prediction.win_percentage.toFixed(0)}%
                              </span>
                            ) : (
                              <span style={{ color: 'var(--text-muted)' }}>—</span>
                            )}
                          </Table.Cell>
                          <Table.Cell className="text-right text-xs" style={{ color: 'var(--text-muted)' }}>
                            {prediction.pick_count}/{prediction.opportunities || '?'}
                          </Table.Cell>
                        </Table.Row>
                      ))}
                      {expandedRows.map((prediction) => (
                        <Table.Row key={prediction.machine_key}>
                          <Table.Cell className="pr-0">
                            <LikelihoodDot percentage={prediction.confidence_pct} />
                          </Table.Cell>
                          <Table.Cell className="font-medium text-sm" style={{ color: 'var(--text-secondary)' }}>
                            {prediction.machine_name}
                          </Table.Cell>
                          <Table.Cell className="text-right text-sm">
                            {prediction.confidence_pct}%
                          </Table.Cell>
                          <Table.Cell className="text-right text-sm">
                            {prediction.win_percentage != null ? (
                              <span style={{ color: prediction.win_percentage >= 50 ? '#16a34a' : 'var(--text-muted)' }}>
                                {prediction.win_percentage.toFixed(0)}%
                              </span>
                            ) : (
                              <span style={{ color: 'var(--text-muted)' }}>—</span>
                            )}
                          </Table.Cell>
                          <Table.Cell className="text-right text-xs" style={{ color: 'var(--text-muted)' }}>
                            {prediction.pick_count}/{prediction.opportunities || '?'}
                          </Table.Cell>
                        </Table.Row>
                      ))}
                    </Table.Body>
                  </Table>

                  {remainingPredictions.length > 0 && (
                    <button
                      onClick={() => setExpanded(!expanded)}
                      className="mt-2 text-xs font-medium hover:underline"
                      style={{ color: 'var(--text-link)' }}
                    >
                      {expanded
                        ? 'Show less'
                        : `Show ${remainingPredictions.length} more`}
                    </button>
                  )}

                  <p className="text-xs mt-3" style={{ color: 'var(--text-muted)' }}>
                    Seasons {data.seasons_analyzed.join(', ')} | Min 3 opportunities
                  </p>
                </>
              )}
            </>
          );
        })()}
      </Card.Content>
    </Card>
  );
}
