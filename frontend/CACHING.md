# Frontend Caching Configuration

This document summarizes the caching strategies used across all pages in the MNP Analyzer frontend.

## Global Cache Settings

All React Query hooks use consistent cache timing defined in [lib/queries.ts](lib/queries.ts):

| Setting | Value | Description |
|---------|-------|-------------|
| `staleTime` | 5 minutes | Data considered fresh, no background refetch |
| `gcTime` | 30 minutes | Data kept in memory for instant navigation |

## Page Caching Summary

| Page | Route | Rendering | Data Fetching | Caching |
|------|-------|-----------|---------------|---------|
| Dashboard | `/` | Client | `useApiInfo` | 5 min stale / 30 min gc |
| Teams List | `/teams` | Client | `useTeams` | 5 min stale / 30 min gc |
| Team Detail | `/teams/[team_key]` | Client | `useEffect` + `useDebouncedEffect` | None (fresh each load) |
| Players List | `/players` | Client | `useEffect` + direct API | None (fresh each load) |
| Player Detail | `/players/[player_key]` | Client | React Query hooks | 5 min stale / 30 min gc |
| Player Machine | `/players/[player_key]/machines/[machine_key]` | Client | React Query hooks | 5 min stale / 30 min gc |
| Machines List | `/machines` | Client | `useMachineDashboardStats`, `useMachines` | 5 min stale / 30 min gc |
| Machine Detail | `/machines/[machine_key]` | Client | `useEffect` + direct API | None (fresh each load) |
| Venues List | `/venues` | Client | `useVenuesWithStats` | 5 min stale / 30 min gc |
| Venue Detail | `/venues/[venue_key]` | Client | `useEffect` + direct API | None (fresh each load) |
| Matchups | `/matchups` | Client | `useEffect` + direct API | None (fresh each load) |

## Caching Benefits

Pages using React Query hooks benefit from:
- **Instant navigation**: Return visits within 5 minutes show cached data immediately
- **Background refetch**: Stale data is updated in the background
- **Request deduplication**: Multiple components requesting the same data share one request
- **Memory efficiency**: Unused data is garbage collected after 30 minutes

## React Query Hooks Available

The following hooks provide automatic caching when used:

```typescript
// API Info & Seasons
useApiInfo()
useSeasons()

// Players
usePlayers(params?)
usePlayerDashboardStats()
usePlayer(playerKey)
usePlayerMachineStats(playerKey, params?)
usePlayerMachineScoreHistory(playerKey, machineKey, params?)
usePlayerMachineGames(playerKey, machineKey, params?)

// Machines
useMachines(params?)
useMachineDashboardStats()
useMachine(machineKey)
useMachinePercentiles(machineKey, params?)
useMachineScores(machineKey, params?)
useMachineVenues(machineKey)
useMachineTeams(machineKey)

// Venues
useVenues(params?)
useVenuesWithStats(params?)
useVenue(venueKey)
useVenueMachines(venueKey, params?)

// Teams
useTeams(params?)
useTeam(teamKey, season?)
useTeamMachineStats(teamKey, params?)
useTeamPlayers(teamKey, seasons?, venue_key?, exclude_subs?)

// Matchups & Schedule
useMatchup(params)
useSeasonSchedule(season)
```

## Pages Still Using Direct API Calls

These pages could benefit from React Query migration:

| Page | Current | Benefit of Migration |
|------|---------|---------------------|
| Players List (`/players`) | Direct API | Cache player list and dashboard stats |
| Machine Detail | Direct API | Cache percentiles and scores |
| Venue Detail | Direct API | Cache venue machines |
| Team Detail | Direct API + debounce | Cache team data, players, machine stats |
| Matchups | Direct API | Cache season schedule and team data |

## Browser Caching

In addition to React Query, standard browser caching applies:
- API responses may be cached by the browser based on HTTP headers
- No explicit `fetch` cache options are set in [lib/api.ts](lib/api.ts)
- Default Next.js fetch behavior applies for GET requests

## Related Files

- [lib/queries.ts](lib/queries.ts) - React Query hooks and cache configuration
- [lib/api.ts](lib/api.ts) - API client wrapper
- [app/providers.tsx](app/providers.tsx) - React Query provider setup
