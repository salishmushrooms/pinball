# Component Migration Guide

## Overview

This guide helps you migrate existing pages to use the new UI component library. The component library provides consistent styling, better accessibility, and easier maintenance.

---

## What We've Built

### 1. Design System Document
[DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) - Complete design system with:
- Color system (with dark mode support)
- Typography scale
- Spacing guidelines
- Component specifications
- Usage patterns

### 2. UI Component Library
[/components/ui/](components/ui/) - 11 reusable components:

| Component | Purpose | File |
|-----------|---------|------|
| **Card** | Container for grouped content | [Card.tsx](components/ui/Card.tsx) |
| **Button** | Interactive actions | [Button.tsx](components/ui/Button.tsx) |
| **Badge** | Status indicators, tags | [Badge.tsx](components/ui/Badge.tsx) |
| **Alert** | Error/warning/success messages | [Alert.tsx](components/ui/Alert.tsx) |
| **Input** | Text input fields with labels | [Input.tsx](components/ui/Input.tsx) |
| **Select** | Dropdown select with labels | [Select.tsx](components/ui/Select.tsx) |
| **Table** | Data tables with sorting support | [Table.tsx](components/ui/Table.tsx) |
| **PageHeader** | Page title + description | [PageHeader.tsx](components/ui/PageHeader.tsx) |
| **LoadingSpinner** | Loading states | [LoadingSpinner.tsx](components/ui/LoadingSpinner.tsx) |
| **EmptyState** | No data placeholders | [EmptyState.tsx](components/ui/EmptyState.tsx) |
| **StatCard** | Numeric stat display | [StatCard.tsx](components/ui/StatCard.tsx) |

### 3. Enhanced Global Styles
[app/globals.css](app/globals.css) - Updated with:
- CSS custom properties for all colors
- Design tokens for consistent theming
- Dark mode support
- Smooth transitions

### 4. Example Refactored Pages
- [app/players/page-refactored.tsx](app/players/page-refactored.tsx) - Shows Table component usage
- [app/teams/page-refactored.tsx](app/teams/page-refactored.tsx) - Shows Card grid pattern

---

## Migration Steps

### Step 1: Import Components

**Before:**
```tsx
// No imports, using inline Tailwind classes
```

**After:**
```tsx
import {
  Card,
  PageHeader,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  Alert,
  Input,
  LoadingSpinner,
  EmptyState,
} from '@/components/ui';
```

### Step 2: Replace Page Header

**Before:**
```tsx
<div>
  <h1 className="text-3xl font-bold text-gray-900">Players</h1>
  <p className="text-gray-600 mt-2">
    Browse and search player statistics
  </p>
</div>
```

**After:**
```tsx
<PageHeader
  title="Players"
  description="Browse and search player statistics"
/>
```

### Step 3: Replace Cards

**Before:**
```tsx
<div className="bg-white rounded-lg shadow-md p-6">
  <h3 className="text-xl font-semibold">Title</h3>
  <div>Content here</div>
</div>
```

**After:**
```tsx
<Card>
  <Card.Header>
    <Card.Title>Title</Card.Title>
  </Card.Header>
  <Card.Content>
    Content here
  </Card.Content>
</Card>
```

### Step 4: Replace Input Fields

**Before:**
```tsx
<div>
  <label className="block text-sm font-medium text-gray-700 mb-1">
    Search Name
  </label>
  <input
    type="text"
    value={searchTerm}
    onChange={(e) => setSearchTerm(e.target.value)}
    placeholder="Type to search..."
    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
  />
</div>
```

**After:**
```tsx
<Input
  label="Search Name"
  type="text"
  value={searchTerm}
  onChange={(e) => setSearchTerm(e.target.value)}
  placeholder="Type to search..."
/>
```

### Step 5: Replace Select Fields

**Before:**
```tsx
<div>
  <label className="block text-sm font-medium text-gray-700 mb-1">
    Season
  </label>
  <select
    value={seasonFilter || ''}
    onChange={(e) => setSeasonFilter(parseInt(e.target.value))}
    className="w-full md:w-64 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
  >
    <option value="">All Seasons</option>
    <option value="22">Season 22</option>
    <option value="21">Season 21</option>
  </select>
</div>
```

**After:**
```tsx
<Select
  label="Season"
  value={seasonFilter || ''}
  onChange={(e) => setSeasonFilter(parseInt(e.target.value))}
  className="md:w-64"
  options={[
    { value: '', label: 'All Seasons' },
    { value: 22, label: 'Season 22' },
    { value: 21, label: 'Season 21' },
  ]}
/>
```

### Step 6: Replace Tables

**Before:**
```tsx
<div className="bg-white rounded-lg shadow-md overflow-hidden">
  <table className="min-w-full divide-y divide-gray-200">
    <thead className="bg-gray-50">
      <tr>
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          Player Name
        </th>
        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
          IPR
        </th>
      </tr>
    </thead>
    <tbody className="bg-white divide-y divide-gray-200">
      {players.map((player) => (
        <tr key={player.player_key} className="hover:bg-gray-50">
          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            {player.name}
          </td>
          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            {player.current_ipr}
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

**After:**
```tsx
<Card>
  <Table>
    <TableHeader>
      <TableRow hoverable={false}>
        <TableHead>Player Name</TableHead>
        <TableHead>IPR</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      {players.map((player) => (
        <TableRow key={player.player_key}>
          <TableCell>{player.name}</TableCell>
          <TableCell>{player.current_ipr}</TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
</Card>
```

### Step 7: Replace Alert Messages

**Before:**
```tsx
<div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
  <strong className="font-bold">Error: </strong>
  <span>{error}</span>
</div>
```

**After:**
```tsx
<Alert variant="error" title="Error">
  {error}
</Alert>
```

### Step 8: Replace Loading States

**Before:**
```tsx
<div className="flex justify-center items-center min-h-[400px]">
  <div className="text-lg text-gray-600">Loading teams...</div>
</div>
```

**After:**
```tsx
<LoadingSpinner fullPage text="Loading teams..." />
```

### Step 9: Replace Empty States

**Before:**
```tsx
<div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
  No teams found for the selected season.
</div>
```

**After:**
```tsx
<Card>
  <Card.Content>
    <EmptyState
      title="No teams found"
      description="No teams found for the selected season."
    />
  </Card.Content>
</Card>
```

---

## Complete Example: Players Page Migration

### Before (Original)
```tsx
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Player } from '@/lib/types';

export default function PlayersPage() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // ... fetch logic ...

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Players</h1>
        <p className="text-gray-600 mt-2">
          Browse and search player statistics
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Name
            </label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Type to search players..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          <strong className="font-bold">Error: </strong>
          <span>{error}</span>
        </div>
      )}

      {players.length > 0 && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            {/* ... table markup ... */}
          </table>
        </div>
      )}
    </div>
  );
}
```

### After (Refactored)
```tsx
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Player } from '@/lib/types';
import {
  Card,
  PageHeader,
  Input,
  Alert,
  EmptyState,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui';

export default function PlayersPage() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // ... fetch logic ...

  return (
    <div className="space-y-6">
      <PageHeader
        title="Players"
        description="Browse and search player statistics"
      />

      <Card>
        <Card.Content>
          <Input
            label="Search Name"
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Type to search players..."
          />
        </Card.Content>
      </Card>

      {error && (
        <Alert variant="error" title="Error">
          {error}
        </Alert>
      )}

      {players.length > 0 && (
        <Card>
          <Table>
            <TableHeader>
              <TableRow hoverable={false}>
                <TableHead>Player Name</TableHead>
                <TableHead>IPR</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {players.map((player) => (
                <TableRow key={player.player_key}>
                  <TableCell>
                    <Link href={`/players/${player.player_key}`}>
                      {player.name}
                    </Link>
                  </TableCell>
                  <TableCell>{player.current_ipr}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
```

---

## Benefits

### Code Reduction
- **70% less styling code** - Components handle Tailwind classes internally
- **Cleaner JSX** - Less visual clutter, easier to read
- **Faster development** - Import and use, don't reinvent

### Consistency
- **Uniform appearance** - All tables, cards, inputs look the same
- **Design system adherence** - Colors, spacing, typography are standardized
- **Easier updates** - Change once, applies everywhere

### Accessibility
- **Built-in ARIA** - Components include proper ARIA attributes
- **Keyboard navigation** - Focus management handled automatically
- **Screen reader support** - Semantic HTML and labels

### Maintainability
- **Single source of truth** - Update components, not individual pages
- **Type safety** - TypeScript interfaces catch errors early
- **Documentation** - Each component has clear props and usage examples

---

## Migration Checklist

Use this checklist when migrating a page:

- [ ] Import required UI components
- [ ] Replace page header with `<PageHeader>`
- [ ] Replace all cards with `<Card>` components
- [ ] Replace form inputs with `<Input>` and `<Select>`
- [ ] Replace tables with `<Table>` component
- [ ] Replace error messages with `<Alert variant="error">`
- [ ] Replace loading states with `<LoadingSpinner>`
- [ ] Replace empty states with `<EmptyState>`
- [ ] Remove duplicate Tailwind classes
- [ ] Test keyboard navigation
- [ ] Test dark mode (if applicable)
- [ ] Compare with refactored example pages

---

## Pages to Migrate

### Priority 1 (High Traffic)
- [ ] `/app/players/page.tsx`
- [ ] `/app/teams/page.tsx`
- [ ] `/app/machines/page.tsx`
- [ ] `/app/venues/page.tsx`

### Priority 2 (Detail Pages)
- [ ] `/app/players/[player_key]/page.tsx`
- [ ] `/app/teams/[team_key]/page.tsx`
- [ ] `/app/machines/[machine_key]/page.tsx`
- [ ] `/app/venues/[venue_key]/page.tsx`

### Priority 3 (Other Pages)
- [ ] `/app/matchups/page.tsx`
- [ ] `/app/page.tsx` (Home)

---

## Testing

After migrating a page:

1. **Visual testing**
   - Does it look the same or better?
   - Are colors, spacing, typography consistent?
   - Does dark mode work?

2. **Functional testing**
   - Do all interactive elements work?
   - Are forms submitting correctly?
   - Do tables sort properly?

3. **Accessibility testing**
   - Can you navigate with keyboard only?
   - Are labels associated with inputs?
   - Do screen readers announce content correctly?

4. **Responsive testing**
   - Test on mobile (< 640px)
   - Test on tablet (640-1024px)
   - Test on desktop (> 1024px)

---

## Questions?

- Check [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) for component specifications
- Look at [page-refactored.tsx](app/players/page-refactored.tsx) examples
- Review component source code in [/components/ui/](components/ui/)

---

**Created:** 2025-11-26
**Author:** JJC
**Status:** Ready for migration
