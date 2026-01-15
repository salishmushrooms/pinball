# MNP Analyzer API - Actual Endpoints

**Generated:** 2026-01-14
**Source:** Live production API
**API Docs:** https://your-api.railway.app/docs

> **Note:** For interactive documentation with request/response schemas, see the live API docs above.
> This document provides a quick reference of available endpoints based on actual implementation.

---

## Overview

The MNP Analyzer API is built with FastAPI and deployed on Railway. All endpoints return JSON responses.

- **Base URL:** No `/api/v1` prefix (routers are mounted at root)
- **Authentication:** None (public data)
- **Rate Limiting:** 100 requests/minute (configurable per endpoint)
- **CORS:** Enabled for all origins (production should specify actual origins)

---

## Table of Contents

1. [Root Endpoints](#root-endpoints)
2. [Players Router](#players-router)
3. [Machines Router](#machines-router)
4. [Venues Router](#venues-router)
5. [Teams Router](#teams-router)
6. [Matchups Router](#matchups-router)
7. [Seasons Router](#seasons-router)
8. [Predictions Router](#predictions-router)
9. [Matchplay Router](#matchplay-router)
10. [Designed vs Actual Comparison](#designed-vs-actual-comparison)

---

## Root Endpoints

### GET `/`
- **Summary:** API root endpoint
- **Description:** Provides basic information and available endpoints with live database statistics
- **Query Params:** None
- **Returns:** API info, endpoint list, and data summary (player count, machine count, etc.)

### GET `/seasons`
- **Summary:** Get all available seasons
- **Description:** Returns list of season numbers from the database
- **Query Params:** None
- **Returns:** List of season numbers sorted ascending

### GET `/health`
- **Summary:** Health check endpoint
- **Description:** Check API and database health status
- **Query Params:** None
- **Returns:** Health status of API and database connection

---

## Players Router

**Prefix:** `/players`

### GET `/players/dashboard-stats`
- **Summary:** Get player dashboard statistics
- **Description:** Get statistics for the players page dashboard including total count, IPR distribution, new players, and random highlights
- **Query Params:** None
- **Returns:** Dashboard stats with IPR distribution, new player count, and player highlights

### GET `/players`
- **Summary:** List all players
- **Description:** Get a paginated list of all players with optional filtering
- **Query Params:**
  - `season` (int, optional): Filter by season (players active in this season)
  - `min_ipr` (float, optional): Minimum IPR rating
  - `max_ipr` (float, optional): Maximum IPR rating
  - `search` (string, optional): Search player names (case-insensitive)
  - `limit` (int, default: 100, max: 500): Number of results to return
  - `offset` (int, default: 0): Number of results to skip
- **Returns:** PlayerList with pagination

### GET `/players/{player_key}`
- **Summary:** Get player details
- **Description:** Get detailed information about a specific player by their player_key
- **Path Params:**
  - `player_key` (string, required): Player's unique key
- **Query Params:** None
- **Returns:** PlayerDetail with current team information
- **Example:** `/players/sean_irby`

### GET `/players/{player_key}/machines`
- **Summary:** Get player machine statistics
- **Description:** Get performance statistics for a player across all machines they've played
- **Path Params:**
  - `player_key` (string, required): Player's unique key
- **Query Params:**
  - `seasons` (list[int], optional): Filter by season(s) - can pass multiple
  - `venue_key` (string, optional): Filter by venue
  - `min_games` (int, default: 1): Minimum games played on machine
  - `sort_by` (string, default: "median_percentile"): Sort field (median_percentile, avg_percentile, games_played, avg_score, best_score, win_percentage)
  - `sort_order` (string, default: "desc"): Sort order (asc or desc)
  - `limit` (int, default: 100, max: 500): Number of results to return
  - `offset` (int, default: 0): Number of results to skip
- **Returns:** PlayerMachineStatsList with pagination
- **Example:** `/players/sean_irby/machines?seasons=22&min_games=5`

### GET `/players/{player_key}/machines/{machine_key}/scores`
- **Summary:** Get player's score history on a specific machine
- **Description:** Get all individual scores for a player on a specific machine, grouped by season for trend analysis
- **Path Params:**
  - `player_key` (string, required): Player's unique key
  - `machine_key` (string, required): Machine's unique key
- **Query Params:**
  - `venue_key` (string, optional): Filter by venue
  - `seasons` (list[int], optional): Filter by season(s) - can pass multiple
- **Returns:** PlayerMachineScoreHistoryResponse with scores and season stats
- **Example:** `/players/sean_irby/machines/MM/scores`

### GET `/players/{player_key}/machines/{machine_key}/games`
- **Summary:** Get player's games on a specific machine with opponent details
- **Description:** Get all individual games for a player on a specific machine, including all players and their scores
- **Path Params:**
  - `player_key` (string, required): Player's unique key
  - `machine_key` (string, required): Machine's unique key
- **Query Params:**
  - `venue_key` (string, optional): Filter by venue
  - `seasons` (list[int], optional): Filter by season(s) - can pass multiple
  - `limit` (int, default: 100, max: 500): Number of results to return
  - `offset` (int, default: 0): Number of results to skip
- **Returns:** PlayerMachineGamesList with pagination
- **Example:** `/players/sean_irby/machines/MM/games?seasons=21&seasons=22`

---

## Machines Router

**Prefix:** `/machines`

### GET `/machines/dashboard-stats`
- **Summary:** Get machine dashboard statistics
- **Description:** Get statistics for the machines page dashboard including total count, new machines, rare machines, and top machines by scores
- **Query Params:** None
- **Returns:** MachineDashboardStats with counts and top machines

### GET `/machines`
- **Summary:** List all machines
- **Description:** Get a paginated list of all machines with optional filtering
- **Query Params:**
  - `manufacturer` (string, optional): Filter by manufacturer
  - `year` (int, optional): Filter by year
  - `game_type` (string, optional): Filter by game type (SS, EM, etc.)
  - `search` (string, optional): Search machine names (case-insensitive)
  - `has_percentiles` (bool, optional): Filter machines with percentile data
  - `season` (int, optional): Filter by season (only show machines played in this season)
  - `venue_key` (string, optional): Filter by venue (only show machines played at this venue)
  - `limit` (int, default: 100, max: 500): Number of results to return
  - `offset` (int, default: 0): Number of results to skip
- **Returns:** MachineList with pagination
- **Example:** `/machines?manufacturer=Stern&season=22`

### GET `/machines/{machine_key}`
- **Summary:** Get machine details
- **Description:** Get detailed information about a specific machine by its machine_key
- **Path Params:**
  - `machine_key` (string, required): Machine's unique key
- **Query Params:** None
- **Returns:** MachineDetail with total scores, unique players, median and max scores
- **Example:** `/machines/MM`

### GET `/machines/{machine_key}/percentiles`
- **Summary:** Get machine score percentiles
- **Description:** Get score percentile data for a specific machine, grouped by venue and season
- **Path Params:**
  - `machine_key` (string, required): Machine's unique key
- **Query Params:**
  - `season` (int, optional): Filter by season
  - `venue_key` (string, optional): Filter by venue (use '_ALL_' for aggregate stats)
- **Returns:** List[MachinePercentiles] grouped by venue/season
- **Example:** `/machines/MM/percentiles?venue_key=_ALL_`

### GET `/machines/{machine_key}/percentiles/raw`
- **Summary:** Get raw machine score percentiles
- **Description:** Get raw score percentile records for a specific machine (one record per percentile)
- **Path Params:**
  - `machine_key` (string, required): Machine's unique key
- **Query Params:**
  - `season` (int, optional): Filter by season
  - `venue_key` (string, optional): Filter by venue
  - `percentile` (int, optional, range: 0-100): Filter by specific percentile
- **Returns:** List[ScorePercentile]
- **Example:** `/machines/MM/percentiles/raw?percentile=50`

### GET `/machines/{machine_key}/scores`
- **Summary:** Get all scores for a machine
- **Description:** Get individual score records for a specific machine with optional filtering
- **Path Params:**
  - `machine_key` (string, required): Machine's unique key
- **Query Params:**
  - `season` (int, optional): Filter by season
  - `venue_key` (string, optional): Filter by venue
  - `team_keys` (string, optional): Filter by team keys (comma-separated, e.g., 'SKP,TRL,ADB')
  - `limit` (int, default: 100, max: 1000): Number of results to return
  - `offset` (int, default: 0): Number of results to skip
- **Returns:** MachineScoreList with pagination
- **Example:** `/machines/MM/scores?season=22&venue_key=T4B`

### GET `/machines/{machine_key}/venues`
- **Summary:** Get venues where machine has been played
- **Description:** Get list of venues with score counts for a specific machine
- **Path Params:**
  - `machine_key` (string, required): Machine's unique key
- **Query Params:** None
- **Returns:** List of venues with score counts
- **Example:** `/machines/MM/venues`

### GET `/machines/{machine_key}/teams`
- **Summary:** Get teams that have played on a machine
- **Description:** Get list of teams with score counts for a specific machine
- **Path Params:**
  - `machine_key` (string, required): Machine's unique key
- **Query Params:** None
- **Returns:** List of teams with score counts
- **Example:** `/machines/MM/teams`

---

## Venues Router

**Prefix:** `/venues`

### GET `/venues`
- **Summary:** List all venues
- **Description:** Get a paginated list of all venues with optional filtering
- **Query Params:**
  - `search` (string, optional): Search venue names (case-insensitive)
  - `limit` (int, default: 100, max: 500): Number of results to return
  - `offset` (int, default: 0): Number of results to skip
- **Returns:** VenueList with pagination
- **Example:** `/venues?search=Tavern`

### GET `/venues/with-stats`
- **Summary:** List all venues with statistics
- **Description:** Get a paginated list of all venues with machine count and home teams
- **Query Params:**
  - `season` (int, optional): Filter home teams by season (defaults to most recent)
  - `active_only` (bool, default: true): Only show venues with home teams in the current season
  - `neighborhood` (string, optional): Filter by neighborhood
  - `search` (string, optional): Search venue names (case-insensitive)
  - `limit` (int, default: 100, max: 500): Number of results to return
  - `offset` (int, default: 0): Number of results to skip
- **Returns:** VenueWithStatsList with pagination
- **Example:** `/venues/with-stats?active_only=false`

### GET `/venues/{venue_key}`
- **Summary:** Get venue details
- **Description:** Get detailed information about a specific venue by its venue_key
- **Path Params:**
  - `venue_key` (string, required): Venue's unique key
- **Query Params:** None
- **Returns:** VenueDetail with home teams from most recent season
- **Example:** `/venues/T4B`

### GET `/venues/{venue_key}/machines`
- **Summary:** Get machines at a venue with score statistics
- **Description:** Get all machines that have been played at this venue with statistics
- **Path Params:**
  - `venue_key` (string, required): Venue's unique key
- **Query Params:**
  - `current_only` (bool, default: false): Filter to only show current machines at this venue
  - `seasons` (list[int], optional): Filter by one or more seasons
  - `team_key` (string, optional): Filter statistics to a specific team
  - `scores_from` (string, default: "venue"): Score source - 'venue' (only scores at this venue) or 'all' (all scores on these machines across all venues)
- **Returns:** List[VenueMachineStats]
- **Example:** `/venues/T4B/machines?current_only=true&team_key=SKP&scores_from=all`

### GET `/venues/{venue_key}/current-machines`
- **Summary:** Get current machine lineup at venue
- **Description:** Get list of machine keys currently at this venue (from most recent match)
- **Path Params:**
  - `venue_key` (string, required): Venue's unique key
- **Query Params:** None
- **Returns:** List[string] of machine keys
- **Example:** `/venues/T4B/current-machines`

---

## Teams Router

**Prefix:** `/teams`

### GET `/teams`
- **Summary:** List all teams
- **Description:** Get a list of all teams with optional filtering
- **Query Params:**
  - `season` (int, optional): Filter by season
  - `limit` (int, default: 100, max: 500): Number of results to return
  - `offset` (int, default: 0): Number of results to skip
- **Returns:** TeamList with team IPR calculated from player IPRs
- **Example:** `/teams?season=22`

### GET `/teams/{team_key}`
- **Summary:** Get team details
- **Description:** Get detailed information about a specific team
- **Path Params:**
  - `team_key` (string, required): Team's 3-letter key
- **Query Params:**
  - `season` (int, optional): Filter by season
- **Returns:** TeamDetail
- **Example:** `/teams/SKP?season=22`

### GET `/teams/{team_key}/machines`
- **Summary:** Get team machine statistics
- **Description:** Get performance statistics for a team across all machines they've played
- **Path Params:**
  - `team_key` (string, required): Team's unique key
- **Query Params:**
  - `seasons` (list[int], optional): Filter by season(s) - can pass multiple
  - `venue_key` (string, optional): Filter by venue
  - `rounds` (string, optional): Filter by rounds (comma-separated, e.g., '1,2,3,4')
  - `exclude_subs` (bool, default: true): Exclude substitute players
  - `min_games` (int, default: 1): Minimum games played on machine
  - `sort_by` (string, default: "games_played"): Sort field (games_played, avg_score, best_score, win_percentage, median_score, machine_name)
  - `sort_order` (string, default: "desc"): Sort order (asc or desc)
  - `limit` (int, default: 100, max: 500): Number of results to return
  - `offset` (int, default: 0): Number of results to skip
- **Returns:** TeamMachineStatsList with pagination
- **Note:** Includes team aliases (e.g., TRL includes CDC/Contras historical data)
- **Example:** `/teams/SKP/machines?seasons=21&seasons=22&rounds=2,4`

### GET `/teams/{team_key}/players`
- **Summary:** Get team roster with statistics
- **Description:** Get all players who have played for a team with their statistics
- **Path Params:**
  - `team_key` (string, required): Team's unique key
- **Query Params:**
  - `seasons` (string, optional): Filter by seasons (comma-separated, e.g., '21,22')
  - `venue_key` (string, optional): Filter by venue for statistics
  - `exclude_subs` (bool, default: true): Exclude substitute players
- **Returns:** TeamPlayerList with win percentages and most played machines
- **Note:** Includes team aliases (e.g., TRL includes CDC/Contras historical data)
- **Example:** `/teams/SKP/players?seasons=22`

---

## Matchups Router

**Prefix:** `/matchups`

### GET `/matchups`
- **Summary:** Analyze team matchup at a venue
- **Description:** Get comprehensive matchup analysis between two teams at a specific venue across one or more seasons
- **Query Params:**
  - `home_team` (string, required): Home team key (e.g., 'TRL')
  - `away_team` (string, required): Away team key (e.g., 'ETB')
  - `venue` (string, required): Venue key (e.g., 'T4B')
  - `seasons` (list[int], optional): Season numbers (defaults to current + previous season)
- **Returns:** MatchupAnalysis with machine picks, player preferences, and confidence intervals
- **Note:** Aggregates data across multiple seasons for better statistical confidence
- **Example:** `/matchups?home_team=TRL&away_team=ETB&venue=T4B&seasons=21&seasons=22`

**Matchup Analysis Includes:**
- Available machines at the venue
- Team machine pick frequencies (doubles rounds aggregated across home/away contexts)
- Player machine preferences (top 5 machines per player)
- Player-specific confidence intervals (95% confidence for expected scores)
- Team-level confidence intervals (aggregated team performance)

---

## Seasons Router

**Prefix:** `/seasons`

### GET `/seasons/{season}/status`
- **Summary:** Get season status
- **Description:** Get the status of a specific season (upcoming, in-progress, or completed)
- **Path Params:**
  - `season` (int, required): Season number
- **Query Params:** None
- **Returns:** Season status with dates and match counts
- **Example:** `/seasons/22/status`

### GET `/seasons/{season}/schedule`
- **Summary:** Get season schedule
- **Description:** Get the complete schedule for a specific season from the database
- **Path Params:**
  - `season` (int, required): Season number
- **Query Params:** None
- **Returns:** Season schedule with all weeks and matches, including team schedules
- **Example:** `/seasons/22/schedule`

### GET `/seasons/{season}/matches`
- **Summary:** Get season matches
- **Description:** Get all matches for a season, optionally filtered by week
- **Path Params:**
  - `season` (int, required): Season number
- **Query Params:**
  - `week` (int, optional): Filter by week number
- **Returns:** Flat list of matches with home/away teams and venue information
- **Example:** `/seasons/22/matches?week=5`

### GET `/seasons/{season}/teams/{team_key}/schedule`
- **Summary:** Get team schedule
- **Description:** Get the schedule for a specific team in a season
- **Path Params:**
  - `season` (int, required): Season number
  - `team_key` (string, required): Team's 3-letter key
- **Query Params:** None
- **Returns:** Team's complete schedule including home and away games with roster
- **Example:** `/seasons/22/teams/SKP/schedule`

### GET `/seasons/matchups-init`
- **Summary:** Combined endpoint for matchups page initialization
- **Description:** Returns seasons, current season status, and matches in a single request (eliminates 3 sequential API calls)
- **Query Params:** None
- **Returns:** Combined response with seasons list, season status, and matches for latest season
- **Example:** `/seasons/matchups-init`

---

## Predictions Router

**Prefix:** `/predictions`

### GET `/predictions/machine-picks`
- **Summary:** Predict machine picks
- **Description:** Predict which machines a team is likely to pick for a given round based on historical data
- **Query Params:**
  - `team_key` (string, required): Team making the pick (3-letter key)
  - `round_num` (int, required, range: 1-4): Round number
  - `venue_key` (string, required): Venue where match is being played
  - `seasons` (list[int], default: [22, 23]): Seasons to analyze for prediction
  - `limit` (int, default: 10, max: 20): Number of predictions to return
- **Returns:** Predictions with pick frequency and confidence, plus available machines at venue
- **Note:** Uses team_machine_picks table for efficient aggregated data
- **Note:** Doubles rounds (1 & 4) aggregate ALL doubles picks; singles rounds (2 & 3) use round-specific context
- **Example:** `/predictions/machine-picks?team_key=SKP&round_num=1&venue_key=T4B&seasons=22`

**Pick Rules:**
- Home team picks machines in rounds 2 & 4
- Away team picks machines in rounds 1 & 3

---

## Matchplay Router

**Prefix:** `/matchplay`

> **Note:** Matchplay integration requires `MATCHPLAY_API_TOKEN` environment variable. Profile data cached for 24 hours, machine stats cached until manually refreshed.

### GET `/matchplay/status`
- **Summary:** Check Matchplay integration status
- **Description:** Check if Matchplay API is configured and accessible
- **Query Params:** None
- **Returns:** Configuration status and API accessibility

### GET `/matchplay/player/{player_key}/lookup`
- **Summary:** Look up MNP player on Matchplay
- **Description:** Search Matchplay.events for profiles matching an MNP player's name
- **Path Params:**
  - `player_key` (string, required): MNP player's unique key
- **Query Params:** None
- **Returns:** MatchplayLookupResult with potential matches ranked by confidence
- **Note:** Only 100% exact name matches are eligible for automatic linking
- **Example:** `/matchplay/player/abc123def/lookup`

### POST `/matchplay/player/{player_key}/link`
- **Summary:** Link MNP player to Matchplay profile
- **Description:** Create a link between an MNP player and a Matchplay.events user
- **Path Params:**
  - `player_key` (string, required): MNP player's unique key
- **Request Body:** MatchplayLinkRequest with matchplay_user_id
- **Returns:** MatchplayLinkResponse with created mapping
- **Note:** Idempotent - returns success if link already exists with same mapping
- **Example:** `POST /matchplay/player/abc123def/link`

### DELETE `/matchplay/player/{player_key}/link`
- **Summary:** Unlink MNP player from Matchplay profile
- **Description:** Remove the link between an MNP player and Matchplay.events
- **Path Params:**
  - `player_key` (string, required): MNP player's unique key
- **Query Params:** None
- **Returns:** Unlink status
- **Note:** Idempotent - returns success even if no link exists
- **Note:** Also removes cached Matchplay data (machine stats, ratings)
- **Example:** `DELETE /matchplay/player/abc123def/link`

### GET `/matchplay/player/{player_key}/stats`
- **Summary:** Get Matchplay stats for linked player
- **Description:** Get rating, IFPA data, and machine statistics from Matchplay for a linked player
- **Path Params:**
  - `player_key` (string, required): MNP player's unique key
- **Query Params:**
  - `refresh` (bool, default: false): Force refresh all data from Matchplay API (profile and machine stats)
- **Returns:** MatchplayPlayerStats with rating, IFPA, tournament count, and machine stats
- **Note:** Profile data cached for 24 hours; machine stats from past 1 year cached until refresh
- **Example:** `/matchplay/player/abc123def/stats?refresh=true`

### POST `/matchplay/player/{player_key}/refresh-machine-stats`
- **Summary:** Refresh machine statistics for a linked player
- **Description:** Fetches game history from Matchplay (past 1 year) and updates cached machine stats
- **Path Params:**
  - `player_key` (string, required): MNP player's unique key
- **Query Params:** None
- **Returns:** Refresh status with games processed and machines updated
- **Note:** Only games from past 1 year included (configurable via MATCHPLAY_DATA_LOOKBACK_DAYS)
- **Example:** `POST /matchplay/player/abc123def/refresh-machine-stats`

### GET `/matchplay/players/ratings`
- **Summary:** Get Matchplay ratings for multiple players
- **Description:** Batch lookup of Matchplay ratings for linked players (efficient for rosters)
- **Query Params:**
  - `player_keys` (string, required): Comma-separated list of player keys
  - `refresh` (bool, default: false): Force refresh ratings from Matchplay API (rate-limited)
- **Returns:** Map of player_key to rating info for all linked players
- **Note:** Returns cached ratings by default for fast loading
- **Example:** `/matchplay/players/ratings?player_keys=abc123,def456,ghi789`

### GET `/matchplay/search/users`
- **Summary:** Search Matchplay users
- **Description:** Open search for Matchplay users by name (useful when automatic matching fails)
- **Query Params:**
  - `query` (string, required, min: 2): Search query (name)
  - `location_filter` (string, optional): Filter results by location substring (e.g., 'Washington', 'WA')
- **Returns:** List of matching Matchplay users
- **Example:** `/matchplay/search/users?query=John&location_filter=Washington`

### GET `/matchplay/search/tournaments`
- **Summary:** Search Matchplay tournaments
- **Description:** Search for tournaments on Matchplay.events by name
- **Query Params:**
  - `query` (string, required, min: 2): Search query
- **Returns:** List of matching tournaments
- **Note:** Useful for investigating whether MNP matches are uploaded to Matchplay
- **Example:** `/matchplay/search/tournaments?query=Monday+Night`

### GET `/matchplay/investigate/mnp-tournaments`
- **Summary:** Investigate MNP data in Matchplay
- **Description:** Search for Monday Night Pinball tournaments to check for data duplication
- **Query Params:** None
- **Returns:** Analysis of whether MNP data exists in Matchplay with recommendations
- **Note:** Helps identify potential data duplication between MNP database and Matchplay stats
- **Example:** `/matchplay/investigate/mnp-tournaments`

---

## Designed vs Actual Comparison

The original API design (in `endpoints.md`) differs significantly from the actual implementation. Here are the key differences:

### Major Differences

| Aspect | Original Design | Actual Implementation |
|--------|----------------|----------------------|
| **URL Prefix** | `/api/v1/` | No prefix (routers at root) |
| **Response Format** | Wrapped in `{success, data, meta}` | Direct data responses (FastAPI default) |
| **Error Format** | Custom error codes | FastAPI HTTPException with detail |
| **Player Search** | `/api/v1/players/search?q=` | `/players?search=` (query param) |
| **Pagination** | `page` and `per_page` params | `limit` and `offset` params |
| **Team Stats** | Separate `/stats` endpoint | Integrated in `/teams/{team_key}/machines` |
| **Matchups** | `/api/v1/matchups/compare` | `/matchups` (full matchup analysis) |
| **Seasons** | Limited endpoints | Comprehensive schedule/status endpoints |
| **Predictions** | Not in original design | Full `/predictions` router added |
| **Matchplay** | Not in original design | Full `/matchplay` router with integration |

### Endpoint Mapping

| Designed Endpoint | Actual Endpoint | Notes |
|------------------|-----------------|-------|
| `GET /api/v1/players/search?q=scott` | `GET /players?search=scott` | Different param name |
| `GET /api/v1/players/{key}` | `GET /players/{key}` | Similar, no prefix |
| `GET /api/v1/players/{key}/stats` | `GET /players/{key}/machines` | More comprehensive |
| `GET /api/v1/players/{key}/machine-picks` | `GET /players/{key}/machines` | Merged into machine stats |
| `GET /api/v1/players/{key}/best-machines` | `GET /players/{key}/machines?sort_by=median_percentile` | Query param sorting |
| `GET /api/v1/teams/search?q=` | `GET /teams?search=` (not implemented) | Teams don't have search |
| `GET /api/v1/teams/{key}` | `GET /teams/{key}` | Similar, no prefix |
| `GET /api/v1/teams/{key}/roster` | `GET /teams/{key}/players` | Different name |
| `GET /api/v1/machines` | `GET /machines` | Similar, no prefix |
| `GET /api/v1/machines/{key}/percentiles` | `GET /machines/{key}/percentiles` | Same (no prefix) |
| `GET /api/v1/venues` | `GET /venues` | Similar, no prefix |
| `POST /api/v1/scores/calculate-percentile` | Not implemented | Use percentiles endpoint |
| `GET /api/v1/matchups/compare` | `GET /matchups` | Different functionality |
| - | `GET /players/dashboard-stats` | New dashboard endpoint |
| - | `GET /machines/dashboard-stats` | New dashboard endpoint |
| - | `GET /venues/with-stats` | New enhanced listing |
| - | `GET /predictions/machine-picks` | New predictions router |
| - | All `/matchplay/*` endpoints | New Matchplay integration |
| - | `GET /seasons/matchups-init` | New combined endpoint |

### New Features Not in Original Design

1. **Dashboard Endpoints:** Added for players and machines pages
2. **Matchplay Integration:** Complete external API integration with linking, stats caching, and search
3. **Predictions Router:** Machine pick predictions based on historical data
4. **Enhanced Matchup Analysis:** Confidence intervals, player preferences, and multi-season aggregation
5. **Seasons Router:** Complete schedule and match management
6. **Win Percentage Calculations:** Player and team win percentages on machines
7. **Game-Level Detail:** Individual game records with opponent details
8. **Venue Machine Tracking:** Current vs historical machine lineups
9. **Team Aliases:** Support for team mergers/renames (e.g., TRL includes CDC)

### Removed/Not Implemented from Design

1. **Response Wrapper:** No `{success, data, meta}` wrapper
2. **Score Percentile Calculator:** No POST endpoint to calculate percentile for arbitrary score
3. **Head-to-Head Comparisons:** No direct player comparison endpoint
4. **Team Win/Loss Records:** Not explicitly tracked (can be derived)
5. **Caching Headers:** Different implementation (Cache-Control middleware)

---

## Notes

- **Live API Docs:** The FastAPI auto-generated docs at `/docs` are the authoritative source for request/response schemas
- **Placeholder URL:** `https://your-api.railway.app` should be replaced with actual Railway deployment URL
- **Query Parameter Arrays:** Multiple values passed by repeating parameter (e.g., `?seasons=21&seasons=22`)
- **Pagination:** Uses `limit/offset` pattern (common in FastAPI) instead of `page/per_page`
- **Response Format:** Direct JSON responses (FastAPI default) instead of wrapped format
- **Error Handling:** Standard FastAPI HTTPException format with status codes and detail messages

---

**Generated:** 2026-01-14
**Based on:** Production API routers analysis
**API Version:** 1.0.0
