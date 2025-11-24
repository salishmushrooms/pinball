# MNP Analyzer Frontend

A modern Next.js 14 frontend for the Minnesota Pinball League Data Analysis Platform.

## Features

- **Player Browser**: Search and filter players by name, IPR, and season
- **Player Detail**: View individual player statistics across all machines
- **Machine Browser**: Browse pinball machines with filtering by manufacturer
- **Machine Detail**: View detailed machine statistics with percentile visualizations
- **Type-Safe API**: Full TypeScript integration with type-safe API client
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **API Communication**: Native Fetch API
- **Development**: Turbopack for fast development builds

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx           # Root layout with navigation
│   ├── page.tsx             # Home page with data summary
│   ├── players/
│   │   ├── page.tsx         # Player list/search page
│   │   └── [player_key]/
│   │       └── page.tsx     # Player detail page
│   └── machines/
│       ├── page.tsx         # Machine list/search page
│       └── [machine_key]/
│           └── page.tsx     # Machine detail page
├── components/
│   └── Navigation.tsx       # Main navigation component
├── lib/
│   ├── api.ts              # API client
│   └── types.ts            # TypeScript types
└── .env.local              # Environment configuration
```

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

## Styling

The application uses Tailwind CSS for styling with a consistent design system:

- **Primary Color**: Blue (#2563EB)
- **Background**: Gray-50 (#F9FAFB)
- **Cards**: White with shadow-md
- **Text**: Gray-900 for primary, Gray-600 for secondary

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

## Contributing

When adding new features:

1. Update TypeScript types in `lib/types.ts`
2. Add API methods to `lib/api.ts`
3. Create new pages in appropriate directories
4. Update this README

## Support

For issues or questions:
- Check the API documentation at http://localhost:8000/docs
- Review the SESSION_CONTEXT.md for project context

## License

Part of the MNP Analyzer project. See main project README for license information.
