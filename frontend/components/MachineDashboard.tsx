import React from 'react';
import Link from 'next/link';
import { MachineDashboardStats } from '@/lib/types';
import { Card, StatCard, Table } from '@/components/ui';

interface MachineDashboardProps {
  stats: MachineDashboardStats;
}

export function MachineDashboard({ stats }: MachineDashboardProps) {
  const {
    total_machines,
    total_machines_latest_season,
    new_machines_count,
    rare_machines_count,
    latest_season,
    top_machines_by_scores,
  } = stats;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Stats Cards - Left Side */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard
          label="Total Machines"
          value={total_machines.toLocaleString()}
          footnote="All seasons"
        />
        <StatCard
          label={`S${latest_season} Machines`}
          value={total_machines_latest_season.toLocaleString()}
        />
        <StatCard
          label="New Machines"
          value={new_machines_count.toLocaleString()}
          footnote={`Season ${latest_season}`}
        />
        <StatCard
          label="Rare Machines"
          value={rare_machines_count.toLocaleString()}
          footnote="1 venue only"
        />
      </div>

      {/* Top Machines Table - Right Side */}
      <Card>
        <Card.Content className="py-3">
          <div
            className="text-xs font-medium uppercase tracking-wide mb-2 text-center"
            style={{ color: 'var(--text-muted)' }}
          >
            Top 10 Machines by Total Scores (S{latest_season})
          </div>
          <Table>
            <Table.Body>
              {top_machines_by_scores.map((machine, index) => (
                <Table.Row key={machine.machine_key}>
                  <Table.Cell className="text-xs font-medium text-muted">
                    #{index + 1}
                  </Table.Cell>
                  <Table.Cell>
                    <Link
                      href={`/machines/${machine.machine_key}`}
                      className="text-sm font-medium hover:underline"
                      style={{ color: 'var(--text-link)' }}
                    >
                      {machine.machine_name}
                    </Link>
                  </Table.Cell>
                  <Table.Cell className="text-right text-sm text-secondary">
                    {machine.total_scores.toLocaleString()}
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </Card.Content>
      </Card>
    </div>
  );
}
