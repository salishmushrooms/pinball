# Matchplay.events API Integration

> **Last Updated**: 2026-01-18
> **Status**: Partial Implementation (Rating/IFPA only, machine stats removed)

## Overview

The MNP Analyzer integrates with [Matchplay.events](https://app.matchplay.events) to display player ratings and IFPA data. This document describes the API capabilities, limitations discovered during implementation, and current integration status.

## What Works

### Player Profile Data
- **Matchplay Rating**: Glicko-based rating (value + RD)
- **IFPA Data**: Rank, rating, women's rank
- **Tournament Count**: Number of tournaments played
- **Win/Loss Record**: Game counts and efficiency percentage

**Endpoint**: `GET /api/users/{user_id}?includeIfpa=1&includeCounts=1`

This data is cached in `matchplay_ratings` table with 24-hour TTL.

### Player Search & Linking
- Search for Matchplay users by name
- Link MNP players to Matchplay accounts
- Location filtering (e.g., "Washington" state filter)

## What Was Removed (Machine Stats)

### Original Goal
Display per-machine win/loss statistics from Matchplay tournaments.

### Why It Was Removed
The Matchplay API has limitations that make this feature impractical:

1. **Tournament ID Required**: The `/api/games` endpoint requires at least one `tournaments` or `series` parameter. You cannot query all games for a player globally.

2. **Multi-Step Process Required**:
   ```
   Step 1: GET /api/tournaments?playerId={id}  → Get tournament IDs
   Step 2: GET /api/tournaments/{id}?includeArenas=1  → Get arena mappings (per tournament!)
   Step 3: GET /api/games?player={id}&tournaments={ids}  → Get games
   Step 4: Join games with arena names from step 2
   ```

3. **Arena Names Not in Game Data**: Games only include `arenaId`, not the machine name. Each tournament's arena mapping must be fetched separately.

4. **API Call Explosion**: For a player with 76 tournaments, this would require:
   - 1 call to list tournaments (paginated)
   - 76+ calls to get arena mappings
   - Multiple calls to get games (paginated)
   - Total: 100+ API calls per player refresh

5. **Rate Limiting**: Matchplay API has rate limits that would be quickly exhausted.

### Database Tables (Still Present, Unused)
These tables exist but are not populated:
- `matchplay_player_machine_stats` - Per-machine statistics
- `matchplay_arena_mappings` - Arena name normalization

## Current Implementation

### Files
- `api/services/matchplay_client.py` - API client
- `api/routers/matchplay.py` - REST endpoints
- `frontend/components/MatchplaySection.tsx` - UI component

### Active Endpoints
| Endpoint | Purpose |
|----------|---------|
| `GET /matchplay/status` | Check if API is configured |
| `GET /matchplay/player/{key}/lookup` | Search for Matchplay matches |
| `POST /matchplay/player/{key}/link` | Link MNP player to Matchplay |
| `DELETE /matchplay/player/{key}/link` | Unlink player |
| `GET /matchplay/player/{key}/stats` | Get rating/IFPA (no machine stats) |
| `GET /matchplay/players/ratings` | Batch lookup ratings |
| `GET /matchplay/search/users` | Open user search |

### Removed/Non-functional Endpoints
| Endpoint | Status |
|----------|--------|
| `POST /matchplay/player/{key}/refresh-machine-stats` | Returns error (API limitation) |
| `GET /matchplay/investigate/mnp-tournaments` | Works but unused |
| `GET /matchplay/search/tournaments` | Works but unused |

## Configuration

```bash
# .env file
MATCHPLAY_API_TOKEN=your_token_here
```

Get token from: https://app.matchplay.events (Account Settings → API tokens)

## Future Considerations

If machine stats are needed in the future, options include:

1. **Incremental Collection**: Periodically fetch and cache tournament data, building up stats over time rather than on-demand.

2. **User-Triggered**: Let users manually trigger a "deep sync" that takes minutes and shows progress.

3. **Background Worker**: A scheduled job that slowly collects data for linked players without hitting rate limits.

4. **Different Data Source**: Use IFPA API or other sources for machine-level statistics.

## API Documentation

Official Matchplay API docs: https://app.matchplay.events/api-docs/

Key findings from testing (2026-01-18):
- `/api/games?player={id}` returns 400 "Must provide at least one tournament id or one series id"
- `/api/arenas/{id}` only supports PUT, not GET
- Arena names must be fetched via `/api/tournaments/{id}?includeArenas=1`
- Games only contain `arenaId`, not `arenaName`
