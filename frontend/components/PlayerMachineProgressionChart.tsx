'use client';

import { useState, useEffect } from 'react';
import {
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from 'recharts';
import { PlayerMachineScoreHistory } from '@/lib/types';
import { formatScore } from '@/lib/utils';

interface PlayerMachineProgressionChartProps {
  data: PlayerMachineScoreHistory;
}

export default function PlayerMachineProgressionChart({
  data,
}: PlayerMachineProgressionChartProps) {
  const [isClient, setIsClient] = useState(false);

  // Fix for SSR issues with Recharts
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Calculate trend line using simple linear regression
  const calculateTrendLine = () => {
    const points = data.season_stats.map((stat) => ({
      x: stat.season,
      y: stat.mean_score,
    }));

    if (points.length < 2) return [];

    const n = points.length;
    const sumX = points.reduce((sum, p) => sum + p.x, 0);
    const sumY = points.reduce((sum, p) => sum + p.y, 0);
    const sumXY = points.reduce((sum, p) => sum + p.x * p.y, 0);
    const sumX2 = points.reduce((sum, p) => sum + p.x * p.x, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    return data.season_stats.map((stat) => ({
      season: stat.season,
      trendScore: Math.round(slope * stat.season + intercept),
    }));
  };

  const trendLine = calculateTrendLine();

  // Prepare scatter plot data (individual scores)
  const scatterData = data.scores.map((score) => ({
    season: score.season,
    score: score.score,
    venue: score.venue_name,
    date: score.date,
  }));

  // Prepare trendline data for rendering (map trendScore to score for consistency)
  const trendLineData = trendLine.map((point) => ({
    season: point.season,
    score: point.trendScore,
  }));

  if (!data || !data.scores || data.scores.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No score data available for this machine
      </div>
    );
  }

  // Don't render charts until client-side hydration is complete
  if (!isClient) {
    return (
      <div className="text-center py-8 text-gray-500">
        Loading chart...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">
            Score Progression: {data.machine_name}
          </h3>
          <p className="text-sm text-gray-600">
            {data.total_games} games across {data.season_stats.length} season(s)
          </p>
        </div>
      </div>

      <div className="bg-white p-2 sm:p-4 rounded-lg border border-gray-200">
        <ResponsiveContainer width="100%" height={250} className="sm:!h-[350px]">
          <ComposedChart
            margin={{ top: 10, right: 10, left: 0, bottom: 30 }}
            data={scatterData}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="season"
              type="number"
              domain={['dataMin - 0.5', 'dataMax + 0.5']}
              label={{ value: 'Season', position: 'insideBottom', offset: -5 }}
              allowDecimals={false}
              ticks={data.season_stats.map(s => s.season)}
              tick={{ fontSize: 12 }}
            />
            <YAxis
              dataKey="score"
              type="number"
              domain={['auto', 'auto']}
              tickFormatter={(value) => formatScore(value)}
              tick={{ fontSize: 11 }}
              width={50}
            />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <Scatter
              name="Scores"
              data={scatterData}
              fill="#60a5fa"
              opacity={0.6}
            />
            {trendLineData.length > 1 && (
              <Line
                name="Trend"
                data={trendLineData}
                dataKey="score"
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4 text-sm">
        {data.season_stats.map((stat) => (
          <div key={stat.season} className="p-2 sm:p-3 bg-gray-50 rounded border">
            <p className="font-semibold text-gray-700">S{stat.season}</p>
            <p className="text-xs text-gray-600">{stat.games_played} games</p>
            <p className="text-xs mt-1">
              Median: {formatScore(stat.median_score)}
            </p>
            <p className="text-xs">
              Best: {formatScore(stat.max_score)}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
