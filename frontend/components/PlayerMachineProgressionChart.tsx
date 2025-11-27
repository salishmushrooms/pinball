'use client';

import { useState, useEffect } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Line,
  ComposedChart,
  Bar,
} from 'recharts';
import { PlayerMachineScoreHistory } from '@/lib/types';

type ChartType = 'scatter' | 'candlestick';

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

  console.log('Chart data:', data);
  console.log('Scatter data sample:', data.scores.slice(0, 3));

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

  // Prepare candlestick data (aggregated by season)
  const candlestickData = data.season_stats.map((stat) => {
    const trend = trendLine.find((t) => t.season === stat.season);
    return {
      season: stat.season,
      min: stat.min_score,
      q1: stat.q1_score,
      median: stat.median_score,
      mean: stat.mean_score,
      q3: stat.q3_score,
      max: stat.max_score,
      games: stat.games_played,
      trendScore: trend?.trendScore || stat.mean_score,
    };
  });

  // Custom tooltip for scatter plot
  const ScatterTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="font-semibold">Season {data.season}</p>
          <p className="text-sm">Score: {data.score.toLocaleString()}</p>
          <p className="text-xs text-gray-600">{data.venue}</p>
          {data.date && (
            <p className="text-xs text-gray-500">{data.date}</p>
          )}
        </div>
      );
    }
    return null;
  };

  // Custom tooltip for candlestick
  const CandlestickTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="font-semibold">Season {data.season}</p>
          <p className="text-sm">Games: {data.games}</p>
          <div className="mt-2 text-sm space-y-1">
            <p>Max: {data.max.toLocaleString()}</p>
            <p>Q3 (75%): {data.q3.toLocaleString()}</p>
            <p className="font-medium">Median: {data.median.toLocaleString()}</p>
            <p className="font-medium">Mean: {data.mean.toLocaleString()}</p>
            <p>Q1 (25%): {data.q1.toLocaleString()}</p>
            <p>Min: {data.min.toLocaleString()}</p>
          </div>
        </div>
      );
    }
    return null;
  };

  // Custom candlestick shape
  const CustomCandlestick = (props: any) => {
    const { x, y, width, height, payload } = props;

    if (!payload || !payload.max) return null;

    const centerX = x + width / 2;

    // For seasons with only 1 game, all values are the same
    // Just draw a point at that score value
    if (payload.min === payload.max) {
      // Single point - use the chart's Y scale
      // We can't calculate position from props, so draw a simple marker
      return (
        <g>
          <circle
            cx={centerX}
            cy={y + height / 2}
            r={5}
            fill="#60a5fa"
            stroke="#2563eb"
            strokeWidth={2}
          />
        </g>
      );
    }

    // Calculate positions based on score range
    const yScale = height / (payload.max - payload.min);
    const yBase = y + height;

    const yMax = yBase - (payload.max - payload.min) * yScale;
    const yQ3 = yBase - (payload.q3 - payload.min) * yScale;
    const yMedian = yBase - (payload.median - payload.min) * yScale;
    const yMean = yBase - (payload.mean - payload.min) * yScale;
    const yQ1 = yBase - (payload.q1 - payload.min) * yScale;
    const yMin = yBase;

    return (
      <g>
        {/* Whisker line (min to max) */}
        <line
          x1={centerX}
          y1={yMax}
          x2={centerX}
          y2={yMin}
          stroke="#94a3b8"
          strokeWidth={1}
        />

        {/* Box (Q1 to Q3) */}
        <rect
          x={x + width * 0.2}
          y={yQ3}
          width={width * 0.6}
          height={yQ1 - yQ3}
          fill="#60a5fa"
          stroke="#2563eb"
          strokeWidth={1}
          opacity={0.7}
        />

        {/* Median line */}
        <line
          x1={x + width * 0.2}
          y1={yMedian}
          x2={x + width * 0.8}
          y2={yMedian}
          stroke="#1e40af"
          strokeWidth={2}
        />

        {/* Mean point */}
        <circle
          cx={centerX}
          cy={yMean}
          r={3}
          fill="#f59e0b"
          stroke="#d97706"
          strokeWidth={1}
        />

        {/* Min/Max caps */}
        <line
          x1={x + width * 0.3}
          y1={yMax}
          x2={x + width * 0.7}
          y2={yMax}
          stroke="#94a3b8"
          strokeWidth={1}
        />
        <line
          x1={x + width * 0.3}
          y1={yMin}
          x2={x + width * 0.7}
          y2={yMin}
          stroke="#94a3b8"
          strokeWidth={1}
        />
      </g>
    );
  };

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

      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart
            margin={{ top: 20, right: 30, left: 80, bottom: 40 }}
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
            />
            <YAxis
              dataKey="score"
              type="number"
              domain={['auto', 'auto']}
              label={{ value: 'Score', angle: -90, position: 'insideLeft' }}
              tickFormatter={(value) => value.toLocaleString()}
            />
            <Tooltip content={<ScatterTooltip />} />
            <Legend />
            <Scatter
              name="Individual Scores"
              data={scatterData}
              fill="#60a5fa"
              opacity={0.6}
            />
            {trendLineData.length > 1 && (
              <Line
                name="Trend Line"
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

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        {data.season_stats.map((stat) => (
          <div key={stat.season} className="p-3 bg-gray-50 rounded border">
            <p className="font-semibold text-gray-700">Season {stat.season}</p>
            <p className="text-xs text-gray-600">{stat.games_played} games</p>
            <p className="text-xs mt-1">
              Avg: {stat.mean_score.toLocaleString()}
            </p>
            <p className="text-xs">
              Best: {stat.max_score.toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
