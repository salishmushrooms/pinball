# Filter Patterns Guide

## Overview

This guide standardizes how filters should be implemented across the MNP Analyzer application, ensuring a consistent user experience.

---

## Component: FilterPanel

**Location:** `frontend/components/ui/FilterPanel.tsx`

The `FilterPanel` component provides a standardized, reusable way to display filters with optional collapsible behavior.

### Features

- **Collapsible Mode**: Collapse/expand to manage long filter lists
- **Active Filter Badge**: Shows count of active filters
- **Clear All Button**: Quickly reset all filters to defaults
- **Consistent Styling**: Matches design system across all pages
- **Responsive Layout**: Works on mobile and desktop

---

## When to Use FilterPanel

### Collapsible Mode (`collapsible={true}`)

**Use when:**
- Page has **3 or more filters**
- Any filter has **many options** (e.g., Teams with 20+ items)
- Filters take up **significant vertical space**
- Users may want to **hide filters after selecting** to focus on results

**Examples:**
- [Machine Details page](app/machines/[machine_key]/page.tsx) - 3 filters (Seasons, Venue, Teams)
- Venue Details page (if it has similar filters)
- Any page with MultiSelect components with 10+ options

### Non-Collapsible Mode (`collapsible={false}`)

**Use when:**
- Page has **1-2 simple filters**
- All filters are **compact** (single Select or Input)
- Filters are **frequently adjusted** during use
- **Always visible** is more important than space savings

**Examples:**
- [Players page](app/players/page.tsx) - Single search input
- [Matchups page](app/matchups/page.tsx) - Selection form (though could benefit from FilterPanel)

---

## Usage Examples

### Example 1: Collapsible Filter Panel (Recommended for Most Pages)

```tsx
import { FilterPanel, Select, MultiSelect } from '@/components/ui';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';

export default function MyPage() {
  const [selectedSeasons, setSelectedSeasons] = useState([22]);
  const [selectedVenue, setSelectedVenue] = useState('all');
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);

  const activeFilterCount =
    (selectedSeasons.length > 0 && selectedSeasons.length < availableSeasons.length ? 1 : 0) +
    (selectedVenue !== 'all' ? 1 : 0) +
    (selectedTeams.length > 0 ? 1 : 0);

  return (
    <FilterPanel
      title="Filters"
      collapsible={true}
      defaultOpen={true}
      activeFilterCount={activeFilterCount}
      showClearAll={true}
      onClearAll={() => {
        setSelectedSeasons([Math.max(...availableSeasons)]);
        setSelectedVenue('all');
        setSelectedTeams([]);
      }}
    >
      <div className="space-y-6">
        {/* Full-width filters first */}
        <SeasonMultiSelect
          value={selectedSeasons}
          onChange={setSelectedSeasons}
          availableSeasons={availableSeasons}
          helpText="Select one or more seasons to filter scores"
        />

        {/* Responsive grid for other filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Select
            label="Venue"
            value={selectedVenue}
            onChange={(e) => setSelectedVenue(e.target.value)}
            options={venueOptions}
          />

          <MultiSelect
            label="Teams"
            value={selectedTeams}
            onChange={setSelectedTeams}
            options={teamOptions}
          />
        </div>
      </div>
    </FilterPanel>
  );
}
```

### Example 2: Non-Collapsible Filter Panel

```tsx
<FilterPanel
  title="Search Players"
  collapsible={false}
  activeFilterCount={searchTerm ? 1 : 0}
  showClearAll={true}
  onClearAll={() => setSearchTerm('')}
>
  <Input
    label="Player Name"
    value={searchTerm}
    onChange={(e) => setSearchTerm(e.target.value)}
    placeholder="Type to search..."
  />
</FilterPanel>
```

### Example 3: No FilterPanel (Direct Card)

For very simple cases, you can still use a plain Card:

```tsx
<Card>
  <Card.Content>
    <Input
      label="Search"
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
    />
  </Card.Content>
</Card>
```

---

## Calculating Active Filter Count

The `activeFilterCount` prop shows users how many filters are currently active.

### Guidelines:

1. **Don't count default values** - If a filter is set to its default state, don't count it
2. **Count meaningful selections** - Season selection counts if NOT all seasons
3. **Count non-empty arrays** - MultiSelect counts if any items selected
4. **Count non-default single values** - Select counts if not 'all' or first option

### Examples:

```tsx
// Season filter: Count if specific seasons selected (not all)
const seasonActive = selectedSeasons.length > 0 &&
                     selectedSeasons.length < availableSeasons.length ? 1 : 0;

// Single select: Count if not default 'all'
const venueActive = selectedVenue !== 'all' ? 1 : 0;

// Multi-select: Count if any selected
const teamsActive = selectedTeams.length > 0 ? 1 : 0;

// Search input: Count if not empty
const searchActive = searchTerm.trim() !== '' ? 1 : 0;

// Total
const activeFilterCount = seasonActive + venueActive + teamsActive + searchActive;
```

---

## Layout Patterns Inside FilterPanel

### Pattern 1: Full-width then Grid (Recommended)

Use this when you have a mix of full-width filters (like SeasonMultiSelect) and paired filters:

```tsx
<div className="space-y-6">
  {/* Full-width filters */}
  <SeasonMultiSelect ... />

  {/* Responsive grid for paired filters */}
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
    <Select ... />
    <MultiSelect ... />
  </div>
</div>
```

### Pattern 2: All Grid

Use when all filters are the same width:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <Select ... />
  <Select ... />
  <MultiSelect ... />
</div>
```

### Pattern 3: All Vertical

Use when filters need full context or have long labels:

```tsx
<div className="space-y-6">
  <Select ... />
  <MultiSelect ... />
  <Input ... />
</div>
```

---

## Migration Guide

### Migrating Existing Filter Sections

**Before (Old Pattern):**
```tsx
<Card>
  <Card.Header>
    <Card.Title>Filters</Card.Title>
  </Card.Header>
  <Card.Content>
    {/* Filters here */}
  </Card.Content>
</Card>
```

**After (New Pattern):**
```tsx
<FilterPanel
  title="Filters"
  collapsible={true}
  defaultOpen={true}
  activeFilterCount={/* calculate */}
  showClearAll={true}
  onClearAll={() => {/* reset all filters */}}
>
  {/* Same filters */}
</FilterPanel>
```

### Steps:

1. Import `FilterPanel` from `@/components/ui`
2. Replace `Card` with `FilterPanel`
3. Calculate `activeFilterCount` based on filter states
4. Implement `onClearAll` handler to reset filters to defaults
5. Set `collapsible={true}` if page has 3+ filters or long lists
6. Test filter behavior on mobile and desktop

---

## Design Decisions

### Why Collapsible Over Sidebar?

| Feature | Collapsible | Sidebar |
|---------|-------------|---------|
| **Mobile Support** | ✅ Works perfectly | ❌ Requires drawer/modal |
| **Development Effort** | ✅ Simple component | ❌ Complex responsive logic |
| **Screen Space** | ✅ Reclaims vertical space | ❌ Takes horizontal space |
| **Consistency** | ✅ Matches existing patterns | ❌ New pattern to learn |
| **Accessibility** | ✅ Standard expand/collapse | ⚠️ Requires careful implementation |

**Conclusion:** Collapsible is mobile-first, simple, and consistent with the design system.

### Why Not Modal/Popover?

- **Modals** break the direct manipulation pattern (can't see results while filtering)
- **Popovers** are good for small option lists, but not multi-filter workflows
- **Inline collapsible** keeps everything on one page with clear visual feedback

---

## Component Props Reference

### FilterPanel Props

```tsx
interface FilterPanelProps {
  children: React.ReactNode;          // Filter components to display
  title?: string;                     // Panel title (default: "Filters")
  collapsible?: boolean;              // Enable collapse behavior (default: false)
  defaultOpen?: boolean;              // Initial state if collapsible (default: true)
  activeFilterCount?: number;         // Number of active filters (shows badge)
  className?: string;                 // Additional CSS classes
  showClearAll?: boolean;             // Show "Clear All" button (default: false)
  onClearAll?: () => void;            // Handler for clearing all filters
}
```

---

## Best Practices

1. **Always provide `onClearAll`** when `showClearAll={true}`
2. **Calculate `activeFilterCount` accurately** - don't count defaults
3. **Use `defaultOpen={true}`** for first-time users so they see filters
4. **Group related filters** in the same grid column
5. **Put most important filters first** (usually Season or Search)
6. **Provide helpful `helpText`** on individual filter components
7. **Show selection counts** in filter labels when helpful (e.g., "Teams (3 selected)")

---

## Related Components

- **[SeasonMultiSelect](components/SeasonMultiSelect.tsx)** - Specialized season selector
- **[MultiSelect](components/ui/MultiSelect.tsx)** - Checkbox-based multi-select
- **[MultiSelectButtons](components/ui/MultiSelect.tsx)** - Button-style multi-select
- **[Select](components/ui/Select.tsx)** - Single-select dropdown
- **[Input](components/ui/Input.tsx)** - Text input for search/filtering

---

## Future Enhancements

Potential improvements for FilterPanel:

- [ ] **URL state sync** - Save filter state in URL query params
- [ ] **Preset filters** - Save/load common filter combinations
- [ ] **Filter animations** - Smooth transitions when opening/closing
- [ ] **Filter chips** - Show active filters as removable chips above results
- [ ] **Keyboard shortcuts** - Quick access to expand/collapse filters

---

**Last Updated:** 2024-11-29
**Maintained by:** JJC
**See Also:** [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md), [CLAUDE.md](.claude/CLAUDE.md)
