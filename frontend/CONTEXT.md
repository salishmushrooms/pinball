# Frontend Context for AI Assistants

**Last Updated:** 2025-11-26
**Purpose:** Quick context for AI assistants working on this frontend

---

## Current State

### What's Been Completed (2025-11-26)

1. **Design System Created** - Complete design specification in [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)
   - Color system with light/dark mode
   - Typography scale
   - Component specifications
   - Page layout patterns

2. **UI Component Library Built** - 11 reusable components in [components/ui/](components/ui/)
   - Card, Button, Badge, Alert
   - Input, Select, Table
   - PageHeader, LoadingSpinner, EmptyState, StatCard
   - All fully typed with TypeScript
   - Accessibility built-in

3. **Teams Page Migrated** - [app/teams/page.tsx](app/teams/page.tsx)
   - Uses new component library
   - Dynamic season filtering from database
   - Example refactored version available for reference

4. **Documentation Complete**
   - [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) - Full design specification
   - [COMPONENT_MIGRATION_GUIDE.md](COMPONENT_MIGRATION_GUIDE.md) - Migration how-to
   - [components/ui/README.md](components/ui/README.md) - Component quick reference
   - [README.md](README.md) - Updated main README

---

## Tech Stack

- **Framework:** Next.js 16 (App Router with Turbopack)
- **UI:** React 19
- **Language:** TypeScript 5
- **Styling:** Tailwind CSS v4 (PostCSS-based)
- **Fonts:** Geist Sans & Geist Mono

---

## Key Patterns

### 1. Component Usage

Always import from the component library:

```tsx
import {
  Card,
  PageHeader,
  Input,
  Select,
  Table,
  Alert,
  LoadingSpinner,
  EmptyState
} from '@/components/ui';
```

### 2. Page Structure

Follow this pattern for all pages:

```tsx
<div className="space-y-6">
  <PageHeader title="..." description="..." />

  <Card>
    {/* Filters/search */}
  </Card>

  {error && <Alert variant="error">{error}</Alert>}

  {data.length > 0 ? (
    <Card>
      {/* Main content - Table or Card grid */}
    </Card>
  ) : (
    <Card>
      <Card.Content>
        <EmptyState title="..." description="..." />
      </Card.Content>
    </Card>
  )}
</div>
```

### 3. Loading States

```tsx
if (loading) {
  return <LoadingSpinner fullPage text="Loading..." />;
}
```

### 4. Data Filtering

For dropdowns with dynamic data from database:

```tsx
// Fetch all data once
const [allItems, setAllItems] = useState([]);
const [availableSeasons, setAvailableSeasons] = useState([]);

// Extract unique values
const seasons = [...new Set(allItems.map(item => item.season))]
  .sort((a, b) => b - a);

// Filter client-side
const filteredItems = allItems.filter(item =>
  filter ? item.season === filter : true
);
```

---

## Migration Checklist

When migrating a page, follow these steps:

1. **Read existing page** - Understand current behavior
2. **Import UI components** - Replace inline Tailwind with components
3. **Replace page header** - Use `<PageHeader>`
4. **Replace cards** - Use `<Card>` with composition
5. **Replace forms** - Use `<Input>` and `<Select>`
6. **Replace tables** - Use `<Table>` components
7. **Replace alerts** - Use `<Alert>`
8. **Replace loading** - Use `<LoadingSpinner>`
9. **Replace empty states** - Use `<EmptyState>`
10. **Test thoroughly** - Loading, error, empty, populated states
11. **Update README** - Mark as migrated

See [COMPONENT_MIGRATION_GUIDE.md](COMPONENT_MIGRATION_GUIDE.md) for detailed examples.

---

## Pages to Migrate

### ✅ Completed
- `app/teams/page.tsx` - Fully migrated (see for reference)

### 🚧 Ready to Migrate
- `app/players/page.tsx` - Example available at `app/players/page-refactored.tsx`
- `app/teams/page-refactored.tsx` - Can use as reference

### 📋 Not Yet Started
- `app/machines/page.tsx`
- `app/venues/page.tsx`
- `app/matchups/page.tsx`
- All detail pages (`[player_key]`, `[team_key]`, etc.)

---

## Common Tasks

### Task: Migrate a List Page

1. Read [COMPONENT_MIGRATION_GUIDE.md](COMPONENT_MIGRATION_GUIDE.md)
2. Look at `app/teams/page.tsx` as reference
3. Follow the 9-step replacement process
4. Compare with `app/players/page-refactored.tsx` for table pattern

### Task: Add a New Component

1. Create in `components/ui/NewComponent.tsx`
2. Follow existing patterns (variants, TypeScript, accessibility)
3. Export from `components/ui/index.ts`
4. Add example to `components/ui/README.md`
5. Add specification to [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)

### Task: Update Global Styles

1. Edit `app/globals.css` for colors/CSS variables
2. Update [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) color section
3. Test light and dark modes

### Task: Fix a Component

1. Edit `components/ui/ComponentName.tsx`
2. Changes automatically apply to all pages using it
3. Test on all pages that use the component

---

## Important Notes

### Database-Driven Filtering

The Teams page demonstrates the pattern:
- **Fetch all data once** from API (which queries database)
- **Extract unique filter values** (e.g., seasons) from the data
- **Filter client-side** for instant response
- This means dropdowns automatically update when database changes

### API Limits

- API maximum limit: 500 items per request
- Teams endpoint: Returns teams from `teams` table in PostgreSQL
- All endpoints query the database, not local files

### File Naming

- Main pages: `page.tsx` (active)
- Refactored examples: `page-refactored.tsx` (reference only)
- Components: PascalCase (e.g., `PageHeader.tsx`)

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Main project overview |
| [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) | Complete design specification |
| [COMPONENT_MIGRATION_GUIDE.md](COMPONENT_MIGRATION_GUIDE.md) | Step-by-step migration guide |
| [components/ui/README.md](components/ui/README.md) | Component quick reference |
| [app/teams/page.tsx](app/teams/page.tsx) | Example migrated page |
| [app/players/page-refactored.tsx](app/players/page-refactored.tsx) | Table component example |

---

## Questions to Ask the User

When working on this project, you might need to clarify:

1. **Which page to work on?** - Specify page path (e.g., `app/players/page.tsx`)
2. **Migration or new feature?** - Migrating uses existing components; new features may need new components
3. **Component behavior unclear?** - Check existing components in `components/ui/` for patterns
4. **Design decision needed?** - Refer to [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) for established patterns

---

**For detailed instructions on any task, always start with the relevant documentation file listed above.**
