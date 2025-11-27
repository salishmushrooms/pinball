# MNP Analyzer Frontend

A modern Next.js 16 frontend for the Monday Night Pinball score analysis.

## Features

- **Player Browser**: Search and filter players by name, IPR, and season
- **Team Browser**: View teams with dynamic season filtering
- **Machine Browser**: Browse pinball machines with filtering by manufacturer
- **Venue Browser**: Explore venues and their machine lineups
- **Matchup Analysis**: Compare team performance head-to-head
- **Type-Safe API**: Full TypeScript integration with type-safe API client
- **Design System**: Consistent UI components with reusable patterns
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS v4

## Tech Stack

- **Framework**: Next.js 16 (App Router with Turbopack)
- **UI Library**: React 19
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS v4 (PostCSS-based)
- **Component Library**: Custom UI components with design system
- **API Communication**: Native Fetch API
- **Fonts**: Geist Sans & Geist Mono (Google Fonts)

## Project Structure

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── layout.tsx            # Root layout with navigation
│   ├── page.tsx              # Home page with data summary
│   ├── globals.css           # Global styles with design tokens
│   ├── players/              # Player pages
│   │   ├── page.tsx          # Player list (✅ MIGRATED)
│   │   ├── page-refactored.tsx  # Example refactored version
│   │   └── [player_key]/
│   │       └── page.tsx      # Player detail
│   ├── teams/                # Team pages
│   │   ├── page.tsx          # Team list (✅ MIGRATED)
│   │   ├── page-refactored.tsx  # Example refactored version
│   │   └── [team_key]/
│   │       └── page.tsx      # Team detail
│   ├── machines/             # Machine pages
│   │   ├── page.tsx          # Machine list
│   │   └── [machine_key]/
│   │       └── page.tsx      # Machine detail
│   ├── venues/               # Venue pages
│   │   ├── page.tsx          # Venue list
│   │   └── [venue_key]/
│   │       └── page.tsx      # Venue detail
│   └── matchups/             # Matchup analysis
│       └── page.tsx          # Matchup comparison
├── components/
│   ├── Navigation.tsx        # Main navigation component
│   ├── SeasonMultiSelect.tsx # ✨ NEW: Reusable season multi-select (used across pages)
│   └── ui/                   # ✨ UI Component Library
│       ├── Card.tsx          # Card container component
│       ├── Button.tsx        # Button component (4 variants)
│       ├── Badge.tsx         # Status badges (5 variants)
│       ├── Alert.tsx         # Alert messages (4 variants)
│       ├── Input.tsx         # Form input with labels
│       ├── Select.tsx        # Dropdown select with labels
│       ├── MultiSelect.tsx   # Multi-select component (checkbox & button variants)
│       ├── Table.tsx         # Data table with sorting
│       ├── Tabs.tsx          # Tabbed content navigation
│       ├── Collapsible.tsx   # Expandable/collapsible sections
│       ├── PageHeader.tsx    # Page title component
│       ├── LoadingSpinner.tsx # Loading states
│       ├── EmptyState.tsx    # No data placeholders
│       ├── StatCard.tsx      # Statistic display cards
│       ├── index.ts          # Component exports
│       └── README.md         # Component quick reference
├── lib/
│   ├── api.ts                # API client (fully typed)
│   ├── types.ts              # TypeScript type definitions
│   └── utils.ts              # ✨ NEW: Utility functions (cn)
├── DESIGN_SYSTEM.md          # ✨ Complete design system specification
├── COMPONENT_MIGRATION_GUIDE.md  # ✨ Step-by-step migration guide
├── README.md                 # This file
└── .env.local                # Environment configuration
```

## 📚 Documentation

### Core Documentation
- **[DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)** - Complete design system with colors, typography, components, and patterns
- **[COMPONENT_MIGRATION_GUIDE.md](COMPONENT_MIGRATION_GUIDE.md)** - Step-by-step guide for migrating pages to new components
- **[components/ui/README.md](components/ui/README.md)** - Quick reference for all UI components with copy-paste examples

### When to Use Each Doc
- **Starting a new page?** → Read DESIGN_SYSTEM.md for patterns
- **Migrating an existing page?** → Follow COMPONENT_MIGRATION_GUIDE.md
- **Need component syntax?** → Check components/ui/README.md
- **Updating styles globally?** → See DESIGN_SYSTEM.md color/typography sections

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- FastAPI backend running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install
```

### Configuration

The frontend is configured via `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
# Start the development server
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## API Integration

The frontend communicates with the FastAPI backend through a type-safe API client located in `lib/api.ts`.

### API Client Usage

```typescript
import { api } from '@/lib/api';

// Get all players
const players = await api.getPlayers({ limit: 10 });

// Get player details
const player = await api.getPlayer('player_key');

// Get player machine stats
const stats = await api.getPlayerMachineStats('player_key', {
  venue_key: '_ALL_',
  min_games: 3,
});

// Get all machines
const machines = await api.getMachines({ has_percentiles: true });

// Get machine details
const machine = await api.getMachine('machine_key');

// Get machine percentiles
const percentiles = await api.getMachinePercentiles('machine_key');
```

### Testing API Integration

```bash
# Run integration tests
node test-api-integration.js
```

## Pages

### Home Page

- Displays data summary (total players, machines, matches, scores)
- Quick navigation to Players and Machines sections

### Players Page

**URL**: `/players`

Features:
- Search players by name
- Filter by minimum IPR
- Filter by season
- View player statistics (IPR, matches, games, seasons)
- Link to detailed player profiles

### Player Detail Page

**URL**: `/players/[player_key]`

Features:
- Player information (IPR, matches, games, seasons)
- Machine-by-machine performance statistics
- Filter by venue and minimum games played
- Sort by average percentile, games played, or average score
- Direct links to machine detail pages

### Machines Page

**URL**: `/machines`

Features:
- Search machines by name
- Filter by manufacturer
- Filter machines with/without percentile data
- View machine statistics (scores, players, avg/max score)
- Link to detailed machine profiles

### Machine Detail Page

**URL**: `/machines/[machine_key]`

Features:
- Machine information (manufacturer, year)
- Overall statistics (total scores, unique players, avg/max score)
- Score percentile visualizations
- Grouped by venue and season
- Visual bar charts showing percentile distributions

## TypeScript Types

All API responses are fully typed. See `lib/types.ts` for complete type definitions.

Key types:
- `Player`: Player information and statistics
- `PlayerMachineStat`: Player performance on specific machines
- `Machine`: Machine information and statistics
- `GroupedPercentiles`: Percentile data grouped by venue/season
- `Percentile`: Raw percentile records

## Design System & Styling

The application uses a **comprehensive design system** with Tailwind CSS v4. See [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) for complete details.

### Quick Reference

**Colors:**
- Primary: Blue-600 (#2563eb) - Interactive elements
- Grays: 50-900 scale - Text, borders, backgrounds
- Semantic: Success (green), Warning (yellow), Error (red), Info (blue)

**Components:**
- 11 reusable UI components in `components/ui/`
- Consistent styling with variants (primary, secondary, ghost, etc.)
- Full TypeScript support with IntelliSense
- Accessibility built-in (ARIA, keyboard nav, focus states)

**Using Components:**
```tsx
import { Card, Button, Alert, Table } from '@/components/ui';

<Card>
  <Card.Header>
    <Card.Title>Title</Card.Title>
  </Card.Header>
  <Card.Content>
    Content here
  </Card.Content>
</Card>
```

See [components/ui/README.md](components/ui/README.md) for all component examples.

## Development Notes

### Client Components

All page components use `'use client'` directive since they:
- Fetch data with `useEffect`
- Manage state with `useState`
- Handle user interactions

### Error Handling

All API calls include error handling with user-friendly error messages displayed in red alert boxes.

### Loading States

All pages show loading indicators while fetching data to improve user experience.

### Data Formatting

- Large numbers are formatted with locale-aware separators
- Scores use abbreviated format (B for billions, M for millions, K for thousands)
- Percentiles display with one decimal place

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions

## Known Issues

None currently. The integration is fully functional and tested.

## Future Enhancements

Potential improvements for future iterations:

1. **Advanced Filtering**
   - Date range selection
   - Multiple venue selection
   - Advanced search with multiple criteria

2. **Data Visualization**
   - Interactive charts (Chart.js or Recharts)
   - Score distribution histograms
   - Player performance trends over time

3. **Performance**
   - Implement pagination for large datasets
   - Add caching with SWR or React Query
   - Optimize image loading

4. **Features**
   - Compare players side-by-side
   - Export data to CSV
   - Save favorite players/machines
   - Dark mode support

5. **Mobile**
   - Mobile navigation menu
   - Touch-optimized controls
   - Progressive Web App (PWA)

## Migration Status

Component library migration progress:

### ✅ Completed
- [x] Teams page - Fully migrated with dynamic season filtering
- [x] Players page - Fully migrated with search and IPR filtering
- [x] Design system established
- [x] 11 UI components created
- [x] Documentation complete

### 🚧 Ready to Migrate
- [ ] Machines page
- [ ] Venues page
- [ ] Matchups page

### 📋 Not Started
- [ ] Detail pages (player, team, machine, venue)

**To continue migration:** See [COMPONENT_MIGRATION_GUIDE.md](COMPONENT_MIGRATION_GUIDE.md)

## Reusable Components

The project emphasizes **component reuse** to maintain consistency and reduce duplication.

### Specialized Reusable Components

Located in `components/`:

#### SeasonMultiSelect
Multi-season selector with button-style UI. Use this for filtering data by one or more seasons.

```tsx
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';

<SeasonMultiSelect
  value={seasons}
  onChange={setSeasons}
  availableSeasons={[21, 22]}
  helpText="Select one or more seasons"
/>
```

**Used on:**
- Matchups page (team vs team analysis across seasons)
- Machine details page (filter scores by season)
- Can be used on: Venue details, Player details

#### RoundMultiSelect
Round selector with button-style UI for filtering by MNP rounds (1-4).

```tsx
import { RoundMultiSelect } from '@/components/RoundMultiSelect';

<RoundMultiSelect
  value={rounds}
  onChange={setRounds}
  helpText="Doubles: 1 & 4 | Singles: 2 & 3"
/>
```

**Used on:**
- Team details page (filter machine stats by round)

### Custom Hooks

Located in `lib/hooks.ts`:

#### useDebouncedEffect
Delays execution of an effect until after a specified delay since the last dependency change. Perfect for expensive operations triggered by user input.

```tsx
import { useDebouncedEffect } from '@/lib/hooks';

const [searchTerm, setSearchTerm] = useState('');
const [filters, setFilters] = useState<number[]>([]);
const [fetching, setFetching] = useState(false);

// Wait 500ms after user stops changing filters before fetching
useDebouncedEffect(() => {
  setFetching(true);
  fetchData();
}, 500, [searchTerm, filters]);
```

**Use cases:**
- Multi-select filters that trigger expensive API calls
- Search input fields
- Any filter that causes slow database queries

**Used on:**
- Team details page (debounced filter changes)

### Base UI Components

Located in `components/ui/`:
- Card, Button, Badge, Alert, Input, Select
- MultiSelect (checkbox & button variants)
- Table, Tabs, Collapsible
- PageHeader, LoadingSpinner, EmptyState, StatCard

See [components/ui/README.md](components/ui/README.md) for full component reference.

### Before Creating New Components

**Always check:**
1. `components/` - for specialized reusable components
2. `components/ui/` - for base UI components
3. `components/ui/README.md` - for component examples

**If you need a new component:**
1. Design it to be reusable (accept flexible props)
2. Place specialized components in `components/`
3. Place generic UI components in `components/ui/`
4. Document usage with code examples
5. Export from appropriate index file

## Contributing

### Adding New Features

1. **Check for existing components**: Review `components/` and `components/ui/` before creating new ones
2. **Use the design system**: Import components from `@/components/ui`
3. **Update types**: Add TypeScript types to `lib/types.ts`
4. **Add API methods**: Extend `lib/api.ts` with new endpoints
5. **Follow patterns**: See [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) for page layout patterns
6. **Update docs**: Update this README and relevant documentation

### Migrating Existing Pages

1. **Read the guide**: Follow [COMPONENT_MIGRATION_GUIDE.md](COMPONENT_MIGRATION_GUIDE.md)
2. **Use examples**: Compare with `page-refactored.tsx` files
3. **Test thoroughly**: Check responsive behavior, loading states, errors
4. **Update status**: Mark page as migrated in this README

### Creating New Components

If you need a component that doesn't exist:

1. **Check design system**: Ensure it fits the established patterns
2. **Create in `components/ui/`**: Follow existing component structure
3. **Add TypeScript interfaces**: Define clear prop types
4. **Export from index**: Add to `components/ui/index.ts`
5. **Document**: Add examples to `components/ui/README.md`
6. **Update design system**: Add to DESIGN_SYSTEM.md if it's a new pattern

## Support

For issues or questions:
- Check the API documentation at http://localhost:8000/docs
- Review the SESSION_CONTEXT.md for project context

## License

Part of the MNP Analyzer project. See main project README for license information.
