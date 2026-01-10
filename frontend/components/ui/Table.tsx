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
  sticky?: boolean;
}

export function TableHeader({ children, className, sticky = false }: TableHeaderProps) {
  return (
    <thead
      className={cn(sticky && 'sticky top-0 z-10', className)}
      style={{ backgroundColor: 'var(--table-header-bg)' }}
    >
      {children}
    </thead>
  );
}

interface TableBodyProps {
  children: React.ReactNode;
  className?: string;
  striped?: boolean;
}

export function TableBody({ children, className, striped = false }: TableBodyProps) {
  // If striped, wrap children to add alternating backgrounds
  const styledChildren = striped
    ? React.Children.map(children, (child, index) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<{ isEven?: boolean }>, {
            isEven: index % 2 === 1,
          });
        }
        return child;
      })
    : children;

  return (
    <tbody
      className={cn('divide-y', className)}
      style={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--table-border)' }}
    >
      {styledChildren}
    </tbody>
  );
}

interface TableRowProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
  isEven?: boolean;
}

export function TableRow({ children, className, onClick, hoverable = true, isEven }: TableRowProps) {
  return (
    <tr
      className={cn(
        'transition-colors duration-150',
        hoverable && 'hover:bg-[var(--table-row-hover-enhanced)]',
        onClick && 'cursor-pointer',
        className
      )}
      style={{
        backgroundColor: isEven ? 'var(--table-row-stripe)' : undefined,
      }}
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
