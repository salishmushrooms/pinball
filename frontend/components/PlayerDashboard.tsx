import React, { useState } from 'react';
import Link from 'next/link';
import { PlayerDashboardStats, PlayerHighlight } from '@/lib/types';
import { Card, StatCard } from '@/components/ui';
import { formatScore } from '@/lib/utils';

interface PlayerHighlightSliderProps {
  highlights: PlayerHighlight[];
}

export function PlayerHighlightSlider({ highlights }: PlayerHighlightSliderProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (!highlights || highlights.length === 0) {
    return null;
  }

  const currentHighlight = highlights[currentIndex];

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? highlights.length - 1 : prev - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev === highlights.length - 1 ? 0 : prev + 1));
  };

  return (
    <div className="relative">
      <div
        className="rounded-lg px-3 sm:px-4 py-3 sm:py-4"
        style={{
          backgroundColor: 'var(--color-primary-100)',
          border: '1px solid var(--color-primary-200)',
        }}
      >
        {/* Navigation Buttons - Left */}
        {highlights.length > 1 && (
          <button
            onClick={handlePrevious}
            className="absolute left-1 sm:left-2 top-1/2 -translate-y-1/2 w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center transition-colors hover:opacity-90 z-10"
            style={{
              backgroundColor: 'var(--color-primary-600)',
              color: 'white',
            }}
            aria-label="Previous player"
          >
            ←
          </button>
        )}

        {/* Content - Responsive Layout */}
        <div className="px-8 sm:px-10 flex flex-col gap-1">
          {/* Header */}
          <div className="text-xs font-medium uppercase tracking-wide" style={{ color: 'var(--color-primary-700)' }}>
            Player Spotlight
          </div>

          {/* Player Name - Team */}
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href={`/players/${encodeURIComponent(currentHighlight.player_key)}`}
              className="text-lg font-bold hover:underline"
              style={{ color: 'var(--color-primary-800)' }}
            >
              {currentHighlight.player_name}
            </Link>
            {currentHighlight.team_name && (
              <>
                <span style={{ color: 'var(--color-primary-500)' }}>-</span>
                <Link
                  href={`/teams/${encodeURIComponent(currentHighlight.team_key || '')}`}
                  className="text-base hover:underline"
                  style={{ color: 'var(--color-primary-700)' }}
                >
                  {currentHighlight.team_name}
                </Link>
              </>
            )}
          </div>

          {/* S22 Highlight: [Score] [Machine] */}
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span style={{ color: 'var(--color-primary-600)' }}>
              S{currentHighlight.season} Highlight:
            </span>
            <span className="font-semibold" style={{ color: 'var(--color-primary-800)' }}>
              {formatScore(currentHighlight.best_score)}
            </span>
            <Link
              href={`/machines/${encodeURIComponent(currentHighlight.best_machine_key)}`}
              className="hover:underline"
              style={{ color: 'var(--color-primary-700)' }}
            >
              {currentHighlight.best_machine_name}
            </Link>
          </div>
        </div>

        {/* Navigation Buttons - Right */}
        {highlights.length > 1 && (
          <button
            onClick={handleNext}
            className="absolute right-1 sm:right-2 top-1/2 -translate-y-1/2 w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center transition-colors hover:opacity-90 z-10"
            style={{
              backgroundColor: 'var(--color-primary-600)',
              color: 'white',
            }}
            aria-label="Next player"
          >
            →
          </button>
        )}
      </div>

      {/* Indicator Dots */}
      {highlights.length > 1 && (
        <div className="flex justify-center gap-1.5 mt-2">
          {highlights.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentIndex(index)}
              className="w-2.5 h-2.5 rounded-full transition-all border"
              style={{
                backgroundColor: index === currentIndex ? 'var(--color-primary-600)' : 'transparent',
                borderColor: 'var(--color-primary-600)',
                borderWidth: '2px',
              }}
              aria-label={`Go to player ${index + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface PlayerDashboardProps {
  stats: PlayerDashboardStats;
}

export function PlayerDashboard({ stats }: PlayerDashboardProps) {
  const {
    total_players,
    ipr_distribution,
    new_players_count,
    latest_season,
  } = stats;

  // Filter out unrated players (level 0) and sort by IPR level
  const ratedDistribution = ipr_distribution
    .filter((d) => d.ipr_level > 0)
    .sort((a, b) => a.ipr_level - b.ipr_level);

  // Find max count for scaling the bar chart
  const maxCount = Math.max(...ratedDistribution.map((d) => d.count));

  return (
    <div className="space-y-4">
      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard
          label="Total Players"
          value={total_players.toLocaleString()}
        />
        <StatCard
          label="New Players"
          value={new_players_count.toLocaleString()}
          footnote={`Season ${latest_season}`}
        />
        <StatCard
          label="Latest Season"
          value={latest_season}
        />
      </div>

      {/* Player Distribution Chart */}
      <Card>
        <Card.Content className="py-3">
          <div
            className="text-xs font-medium uppercase tracking-wide mb-2 text-center"
            style={{ color: 'var(--text-muted)' }}
          >
            Player Distribution by IPR
          </div>
          {/* Vertical Bar Chart - Compact */}
          <div className="flex items-end justify-center gap-3 h-32">
            {ratedDistribution.map((item) => {
              const heightPercentage = maxCount > 0 ? (item.count / maxCount) * 100 : 0;

              return (
                <div key={item.ipr_level} className="flex flex-col items-center w-12">
                  {/* Bar Container */}
                  <div className="relative w-full h-24 flex items-end">
                    {/* Bar */}
                    <div
                      className="w-full rounded-t flex flex-col items-center justify-end pb-1 transition-all duration-300"
                      style={{
                        height: `${heightPercentage}%`,
                        backgroundColor: 'var(--color-primary-600)',
                        minHeight: item.count > 0 ? '20px' : '0',
                      }}
                    >
                      {/* Count Label */}
                      <span className="text-xs font-bold text-white">
                        {item.count}
                      </span>
                    </div>
                  </div>

                  {/* IPR Level Label */}
                  <div
                    className="mt-1 text-xs font-medium"
                    style={{ color: 'var(--text-secondary)' }}
                  >
                    {item.ipr_level}
                  </div>
                </div>
              );
            })}
          </div>
        </Card.Content>
      </Card>
    </div>
  );
}
