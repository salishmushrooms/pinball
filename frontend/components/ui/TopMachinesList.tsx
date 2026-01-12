import React from 'react';
import Link from 'next/link';

interface TopMachine {
  machine_key: string;
  machine_name: string;
  total_scores: number;
}

interface TopMachinesListProps {
  machines: TopMachine[];
  title?: string;
  subtitle?: string;
  maxWidth?: string;
}

export function TopMachinesList({
  machines,
  title = 'Top Machines',
  subtitle,
  maxWidth = '320px',
}: TopMachinesListProps) {
  if (machines.length === 0) {
    return null;
  }

  return (
    <div
      className="rounded-lg p-4 md:p-6"
      style={{
        backgroundColor: 'var(--color-primary-50)',
        border: '1px solid var(--border-light)',
        maxWidth,
      }}
    >
      <div
        className="text-xs font-medium uppercase tracking-wide mb-1 text-center"
        style={{ color: 'var(--text-muted)' }}
      >
        {title}
      </div>
      {subtitle && (
        <div
          className="text-xs mb-3 text-center"
          style={{ color: 'var(--text-muted)' }}
        >
          {subtitle}
        </div>
      )}
      <div className="space-y-2">
        {machines.map((machine, index) => (
          <div
            key={machine.machine_key}
            className="flex items-center gap-3"
          >
            <span
              className="text-lg font-bold w-6 text-center"
              style={{ color: 'var(--color-primary-600)' }}
            >
              {index + 1}
            </span>
            <div className="flex-1 min-w-0">
              <Link
                href={`/machines/${machine.machine_key}`}
                className="text-sm font-medium hover:underline truncate block"
                style={{ color: 'var(--color-primary-700)' }}
              >
                {machine.machine_name}
              </Link>
            </div>
            <span
              className="text-sm tabular-nums"
              style={{ color: 'var(--text-muted)' }}
            >
              {machine.total_scores.toLocaleString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
