'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface TableProps {
  children: React.ReactNode;
  className?: string;
  compact?: boolean;
  stickyHeader?: boolean;
}

export function Table({ children, className, compact = false, stickyHeader = false }: TableProps) {
  return (
    <div className={cn('overflow-x-auto -mx-4 sm:mx-0', stickyHeader && 'max-h-[600px]')}>
      <table
        className={cn(
          'w-full divide-y',
          compact && 'text-sm',
          className
        )}
        style={{ borderColor: 'var(--table-border)' }}
      >
        {children}
      </table>
    </div>
  );
}

interface TableHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export function TableHeader({ children, className }: TableHeaderProps) {
  return (
    <thead className={cn(className)} style={{ backgroundColor: 'var(--table-header-bg)' }}>
      {children}
    </thead>
  );
}

interface TableBodyProps {
  children: React.ReactNode;
  className?: string;
}

export function TableBody({ children, className }: TableBodyProps) {
  return (
    <tbody
      className={cn('divide-y', className)}
      style={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--table-border)' }}
    >
      {children}
    </tbody>
  );
}

interface TableRowProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
}

export function TableRow({ children, className, onClick, hoverable = true }: TableRowProps) {
  const hoverStyle = hoverable ? { '--tw-row-hover': 'var(--table-row-hover)' } as React.CSSProperties : {};
  return (
    <tr
      className={cn(
        hoverable && 'hover:bg-[var(--table-row-hover)]',
        onClick && 'cursor-pointer',
        className
      )}
      style={hoverStyle}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}

interface TableHeadProps {
  children: React.ReactNode;
  className?: string;
  sortable?: boolean;
  onSort?: () => void;
  sortDirection?: 'asc' | 'desc' | null;
}

export function TableHead({
  children,
  className,
  sortable,
  onSort,
  sortDirection,
}: TableHeadProps) {
  return (
    <th
      className={cn(
        'px-3 py-2 sm:px-4 sm:py-3 text-left text-xs font-medium uppercase tracking-wider',
        sortable && 'cursor-pointer select-none',
        className
      )}
      style={{ color: 'var(--text-muted)' }}
      onClick={sortable ? onSort : undefined}
    >
      <div className="flex items-center gap-1">
        {children}
        {sortable && (
          <span style={{ color: 'var(--text-muted)' }}>
            {sortDirection === 'asc' && '↑'}
            {sortDirection === 'desc' && '↓'}
            {!sortDirection && '↕'}
          </span>
        )}
      </div>
    </th>
  );
}

interface TableCellProps {
  children: React.ReactNode;
  className?: string;
}

export function TableCell({ children, className }: TableCellProps) {
  return (
    <td
      className={cn('px-3 py-2 sm:px-4 sm:py-3 whitespace-nowrap text-sm', className)}
      style={{ color: 'var(--text-primary)' }}
    >
      {children}
    </td>
  );
}

// Compose Table with sub-components
Table.Header = TableHeader;
Table.Body = TableBody;
Table.Row = TableRow;
Table.Head = TableHead;
Table.Cell = TableCell;
