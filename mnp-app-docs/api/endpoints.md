# API Endpoints Specification

> ⚠️ **Note:** This document was created during planning phase.
> See actual API docs at https://your-api.railway.app/docs for current implementation.

## Overview

The MNP Analyzer API is a RESTful API built with FastAPI. It provides access to player statistics, team intelligence, machine data, and performance analytics.

**Base URL**: `https://api.mnp-analyzer.com` (or backend deployment URL)

**API Version**: v1

**Authentication**: None required for MVP (public data)

**Rate Limiting**: 100 requests per minute per IP address

## Response Format

All responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2025-01-23T10:30:00Z",
    "api_version": "1.0",
    "response_time_ms": 145
  }
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "PLAYER_NOT_FOUND",
    "message": "Player with key 'abc123' not found",
    "details": {}
  },
  "meta": {
    "timestamp": "2025-01-23T10:30:00Z",
    "api_version": "1.0"
  }
}
```

## Core Endpoints

### 1. Player Endpoints

#### GET /api/v1/players/search

Search for players by name.

**Query Parameters:**
- `q` (required): Search query string (minimum 2 characters)
- `limit` (optional): Maximum results to return (default: 10, max: 50)
- `season` (optional): Filter by season (default: current season)

**Example Request:**
```
GET /api/v1/players/search?q=scott&limit=5
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "player_key": "f69f2cc7fc9237f2685addaa14a2ae2ec8709451",
        "name": "Scott Helgason",
        "current_ipr": 6,
        "total_games_played": 145,
        "last_seen_season": 22
      },
      {
        "player_key": "c20df9b17e2b7ec2383c7ae10a0f1293090babd7",
        "name": "Scott Lee WA",
        "current_ipr": 5,
        "total_games_played": 89,
        "last_seen_season": 22
      }
    ],
    "total_count": 2
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/players/{player_key}

Get detailed player information.

**Path Parameters:**
- `player_key` (required): Player's unique identifier

**Query Parameters:**
- `season` (optional): Season for stats (default: current)

**Example Request:**
```
GET /api/v1/players/f69f2cc7fc9237f2685addaa14a2ae2ec8709451?season=22
```

**Response:**
```json
{
  "success": true,
  "data": {
    "player_key": "f69f2cc7fc9237f2685addaa14a2ae2ec8709451",
    "name": "Scott Helgason",
    "current_ipr": 6,
    "total_games_played": 145,
    "first_seen_season": 20,
    "last_seen_season": 22,
    "season_stats": {
      "season": 22,
      "games_played": 48,
      "teams": ["ADB"],
      "venues_played": ["T4B", "JUP", "IBX"],
      "machines_played": 35,
      "median_percentile": 78.5,
      "avg_percentile": 75.2
    }
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/players/{player_key}/stats

Get player statistics summary.

**Path Parameters:**
- `player_key` (required): Player's unique identifier

**Query Parameters:**
- `season` (optional): Season filter (default: current)
- `venue` (optional): Venue filter (e.g., "T4B")

**Example Request:**
```
GET /api/v1/players/f69f2cc7fc9237f2685addaa14a2ae2ec8709451/stats?venue=T4B&season=22
```

**Response:**
```json
{
  "success": true,
  "data": {
    "player_key": "f69f2cc7fc9237f2685addaa14a2ae2ec8709451",
    "name": "Scott Helgason",
    "filters": {
      "season": 22,
      "venue": "T4B"
    },
    "overall": {
      "games_played": 24,
      "median_percentile": 82.5,
      "avg_percentile": 79.3,
      "machines_played": 18
    },
    "by_round_type": {
      "singles": {
        "games_played": 12,
        "median_percentile": 85.0
      },
      "doubles": {
        "games_played": 12,
        "median_percentile": 80.0
      }
    },
    "home_away_split": {
      "home": {
        "games_played": 12,
        "median_percentile": 84.5
      },
      "away": {
        "games_played": 12,
        "median_percentile": 80.5
      }
    }
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/players/{player_key}/machine-picks

Get machines most frequently picked by a player.

**Path Parameters:**
- `player_key` (required): Player's unique identifier

**Query Parameters:**
- `venue` (optional): Filter by venue (only show machines at this venue)
- `season` (optional): Season filter (default: current)
- `limit` (optional): Number of results (default: 10)

**Example Request:**
```
GET /api/v1/players/f69f2cc7fc9237f2685addaa14a2ae2ec8709451/machine-picks?venue=T4B&limit=5
```

**Response:**
```json
{
  "success": true,
  "data": {
    "player_key": "f69f2cc7fc9237f2685addaa14a2ae2ec8709451",
    "name": "Scott Helgason",
    "filters": {
      "venue": "T4B",
      "season": 22
    },
    "machine_picks": [
      {
        "machine_key": "MM",
        "machine_name": "Medieval Madness",
        "times_picked": 8,
        "times_available": 10,
        "pick_rate": 0.80,
        "median_percentile": 85.5,
        "games_played": 8
      },
      {
        "machine_key": "TZ",
        "machine_name": "Twilight Zone",
        "times_picked": 6,
        "times_available": 10,
        "pick_rate": 0.60,
        "median_percentile": 78.0,
        "games_played": 6
      }
    ],
    "total_machines": 18
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/players/{player_key}/best-machines

Get machines where player performs best (by percentile).

**Path Parameters:**
- `player_key` (required): Player's unique identifier

**Query Parameters:**
- `venue` (optional): Filter by venue
- `season` (optional): Season filter (default: current)
- `min_games` (optional): Minimum games played on machine (default: 3)
- `limit` (optional): Number of results (default: 10)

**Example Request:**
```
GET /api/v1/players/f69f2cc7fc9237f2685addaa14a2ae2ec8709451/best-machines?venue=T4B&min_games=3
```

**Response:**
```json
{
  "success": true,
  "data": {
    "player_key": "f69f2cc7fc9237f2685addaa14a2ae2ec8709451",
    "name": "Scott Helgason",
    "filters": {
      "venue": "T4B",
      "season": 22,
      "min_games": 3
    },
    "best_machines": [
      {
        "rank": 1,
        "machine_key": "MM",
        "machine_name": "Medieval Madness",
        "games_played": 8,
        "median_score": 28500000,
        "median_percentile": 85.5,
        "avg_percentile": 83.2,
        "best_score": 42000000,
        "best_percentile": 96.5,
        "currently_at_venue": true
      },
      {
        "rank": 2,
        "machine_key": "TZ",
        "machine_name": "Twilight Zone",
        "games_played": 6,
        "median_score": 185000000,
        "median_percentile": 78.0,
        "avg_percentile": 76.5,
        "best_score": 295000000,
        "best_percentile": 92.0,
        "currently_at_venue": true
      }
    ],
    "total_machines": 12
  },
  "meta": { ... }
}
```

---

### 2. Team Endpoints

#### GET /api/v1/teams/search

Search for teams by name or key.

**Query Parameters:**
- `q` (required): Search query
- `season` (optional): Filter by season (default: current)
- `limit` (optional): Max results (default: 10)

**Example Request:**
```
GET /api/v1/teams/search?q=admiraballs
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "team_key": "ADB",
        "team_name": "Admiraballs",
        "season": 22,
        "home_venue_key": "JUP",
        "home_venue_name": "Jupiter's Tap"
      }
    ],
    "total_count": 1
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/teams/{team_key}

Get team details.

**Path Parameters:**
- `team_key` (required): Team's 3-letter code

**Query Parameters:**
- `season` (optional): Season (default: current)

**Example Request:**
```
GET /api/v1/teams/ADB?season=22
```

**Response:**
```json
{
  "success": true,
  "data": {
    "team_key": "ADB",
    "team_name": "Admiraballs",
    "season": 22,
    "home_venue": {
      "venue_key": "JUP",
      "venue_name": "Jupiter's Tap"
    },
    "roster": [
      {
        "player_key": "f69f2cc7fc9237f2685addaa14a2ae2ec8709451",
        "name": "Scott Helgason",
        "ipr": 6,
        "games_played": 12
      }
    ],
    "record": {
      "wins": 6,
      "losses": 4,
      "win_percentage": 0.60
    }
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/teams/{team_key}/machine-picks

Get machines most frequently picked by a team.

**Path Parameters:**
- `team_key` (required): Team's 3-letter code

**Query Parameters:**
- `home` (optional): Filter by home games (true/false)
- `round_type` (optional): Filter by "singles" or "doubles"
- `season` (optional): Season filter (default: current)
- `limit` (optional): Number of results (default: 10)

**Example Request:**
```
GET /api/v1/teams/ADB/machine-picks?home=true&round_type=singles&season=22
```

**Response:**
```json
{
  "success": true,
  "data": {
    "team_key": "ADB",
    "team_name": "Admiraballs",
    "filters": {
      "home": true,
      "round_type": "singles",
      "season": 22
    },
    "machine_picks": [
      {
        "rank": 1,
        "machine_key": "MM",
        "machine_name": "Medieval Madness",
        "times_picked": 8,
        "opportunities": 10,
        "pick_rate": 0.80,
        "wins": 6,
        "win_rate": 0.75,
        "avg_score": 25000000,
        "total_points": 18
      },
      {
        "rank": 2,
        "machine_key": "007",
        "machine_name": "James Bond 007",
        "times_picked": 5,
        "opportunities": 10,
        "pick_rate": 0.50,
        "wins": 3,
        "win_rate": 0.60,
        "avg_score": 185000000,
        "total_points": 11
      }
    ],
    "total_picks": 20
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/teams/{team_key}/roster

Get team roster with player statistics.

**Path Parameters:**
- `team_key` (required): Team's 3-letter code

**Query Parameters:**
- `season` (optional): Season filter (default: current)

**Example Request:**
```
GET /api/v1/teams/ADB/roster?season=22
```

**Response:**
```json
{
  "success": true,
  "data": {
    "team_key": "ADB",
    "team_name": "Admiraballs",
    "season": 22,
    "roster": [
      {
        "player_key": "f69f2cc7fc9237f2685addaa14a2ae2ec8709451",
        "name": "Scott Helgason",
        "ipr": 6,
        "games_played": 12,
        "median_percentile": 85.5,
        "avg_percentile": 83.2,
        "best_machine": {
          "machine_key": "MM",
          "machine_name": "Medieval Madness",
          "median_percentile": 90.0
        }
      }
    ],
    "total_players": 10
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/teams/{team_key}/player-stats

Get player performance rankings on a specific machine.

**Path Parameters:**
- `team_key` (required): Team's 3-letter code

**Query Parameters:**
- `machine` (required): Machine key
- `season` (optional): Season filter (default: current)
- `venue` (optional): Venue filter

**Example Request:**
```
GET /api/v1/teams/ADB/player-stats?machine=MM&season=22
```

**Response:**
```json
{
  "success": true,
  "data": {
    "team_key": "ADB",
    "team_name": "Admiraballs",
    "machine_key": "MM",
    "machine_name": "Medieval Madness",
    "filters": {
      "season": 22,
      "venue": null
    },
    "player_rankings": [
      {
        "rank": 1,
        "player_key": "f69f2cc7fc9237f2685addaa14a2ae2ec8709451",
        "name": "Scott Helgason",
        "ipr": 6,
        "games_played": 8,
        "median_score": 28500000,
        "median_percentile": 85.5,
        "best_score": 42000000
      },
      {
        "rank": 2,
        "player_key": "a693ae0dd694c79f9af8ce9b9a3e612c8a61a4b8",
        "name": "Matthew Greene",
        "ipr": 5,
        "games_played": 6,
        "median_score": 22000000,
        "median_percentile": 72.0,
        "best_score": 35000000
      }
    ],
    "total_players": 7
  },
  "meta": { ... }
}
```

---

### 3. Machine Endpoints

#### GET /api/v1/machines

Get list of all machines with optional filtering.

**Query Parameters:**
- `venue` (optional): Filter by venue
- `season` (optional): Season filter (default: current)
- `search` (optional): Search machine names

**Example Request:**
```
GET /api/v1/machines?venue=T4B&season=22
```

**Response:**
```json
{
  "success": true,
  "data": {
    "machines": [
      {
        "machine_key": "MM",
        "machine_name": "Medieval Madness",
        "manufacturer": "Williams",
        "year": 1997,
        "total_games": 145,
        "at_venues": ["T4B", "JUP", "IBX"]
      },
      {
        "machine_key": "TZ",
        "machine_name": "Twilight Zone",
        "manufacturer": "Bally",
        "year": 1993,
        "total_games": 132,
        "at_venues": ["T4B", "NMC"]
      }
    ],
    "total_count": 18
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/machines/{machine_key}

Get detailed machine information.

**Path Parameters:**
- `machine_key` (required): Machine's canonical key

**Query Parameters:**
- `season` (optional): Season filter (default: current)

**Example Request:**
```
GET /api/v1/machines/MM?season=22
```

**Response:**
```json
{
  "success": true,
  "data": {
    "machine_key": "MM",
    "machine_name": "Medieval Madness",
    "manufacturer": "Williams",
    "year": 1997,
    "game_type": "SS",
    "aliases": ["MedievalMadness", "Medieval Madness (Remake)"],
    "stats": {
      "total_games": 145,
      "unique_players": 87,
      "venues": ["T4B", "JUP", "IBX"],
      "median_score": 18500000,
      "high_score": 78000000
    }
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/machines/{machine_key}/scores

Get score distribution for a machine.

**Path Parameters:**
- `machine_key` (required): Machine's canonical key

**Query Parameters:**
- `venue` (optional): Filter by venue
- `season` (optional): Season filter (default: current)
- `min_ipr` (optional): Filter by minimum IPR
- `max_ipr` (optional): Filter by maximum IPR

**Example Request:**
```
GET /api/v1/machines/MM/scores?venue=T4B&season=22
```

**Response:**
```json
{
  "success": true,
  "data": {
    "machine_key": "MM",
    "machine_name": "Medieval Madness",
    "filters": {
      "venue": "T4B",
      "season": 22
    },
    "distribution": {
      "total_games": 45,
      "min_score": 3200000,
      "max_score": 78000000,
      "median_score": 18500000,
      "mean_score": 21450000
    },
    "percentiles": [
      { "percentile": 10, "score": 6500000 },
      { "percentile": 25, "score": 11000000 },
      { "percentile": 50, "score": 18500000 },
      { "percentile": 75, "score": 28000000 },
      { "percentile": 90, "score": 42000000 },
      { "percentile": 95, "score": 55000000 },
      { "percentile": 99, "score": 72000000 }
    ],
    "scores": [
      {
        "score": 78000000,
        "percentile": 100.0,
        "player_name": "Scott Helgason",
        "date": "2025-01-15",
        "match_key": "mnp-22-3-ADB-TBT"
      }
      // ... more scores if requested
    ]
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/machines/{machine_key}/percentiles

Get pre-calculated percentile thresholds.

**Path Parameters:**
- `machine_key` (required): Machine's canonical key

**Query Parameters:**
- `venue` (optional): Filter by venue
- `season` (optional): Season filter (default: current)

**Example Request:**
```
GET /api/v1/machines/MM/percentiles?venue=T4B&season=22
```

**Response:**
```json
{
  "success": true,
  "data": {
    "machine_key": "MM",
    "machine_name": "Medieval Madness",
    "filters": {
      "venue": "T4B",
      "season": 22
    },
    "percentiles": [
      { "percentile": 1, "score": 2800000 },
      { "percentile": 5, "score": 4200000 },
      { "percentile": 10, "score": 6500000 },
      { "percentile": 25, "score": 11000000 },
      { "percentile": 50, "score": 18500000 },
      { "percentile": 75, "score": 28000000 },
      { "percentile": 90, "score": 42000000 },
      { "percentile": 95, "score": 55000000 },
      { "percentile": 99, "score": 72000000 }
    ],
    "sample_size": 45,
    "last_calculated": "2025-01-23T08:00:00Z"
  },
  "meta": { ... }
}
```

---

### 4. Venue Endpoints

#### GET /api/v1/venues

Get list of all venues.

**Query Parameters:**
- `active` (optional): Filter by active status (true/false)
- `season` (optional): Season filter

**Example Request:**
```
GET /api/v1/venues?active=true
```

**Response:**
```json
{
  "success": true,
  "data": {
    "venues": [
      {
        "venue_key": "T4B",
        "venue_name": "4Bs Tavern",
        "city": "St Paul",
        "active": true,
        "machine_count": 18,
        "teams": ["TBT"]
      },
      {
        "venue_key": "JUP",
        "venue_name": "Jupiter's Tap",
        "city": "Minneapolis",
        "active": true,
        "machine_count": 12,
        "teams": ["ADB"]
      }
    ],
    "total_count": 10
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/venues/{venue_key}

Get detailed venue information.

**Path Parameters:**
- `venue_key` (required): Venue's code

**Query Parameters:**
- `season` (optional): Season filter (default: current)

**Example Request:**
```
GET /api/v1/venues/T4B?season=22
```

**Response:**
```json
{
  "success": true,
  "data": {
    "venue_key": "T4B",
    "venue_name": "4Bs Tavern",
    "address": "123 Main St",
    "city": "St Paul",
    "state": null,
    "active": true,
    "machines": [
      {
        "machine_key": "MM",
        "machine_name": "Medieval Madness",
        "active": true,
        "games_played": 45
      },
      {
        "machine_key": "TZ",
        "machine_name": "Twilight Zone",
        "active": true,
        "games_played": 38
      }
    ],
    "home_teams": [
      {
        "team_key": "TBT",
        "team_name": "The B Team"
      }
    ],
    "stats": {
      "total_matches": 12,
      "total_games": 192,
      "unique_players": 45
    }
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/venues/{venue_key}/machines

Get machines at a venue.

**Path Parameters:**
- `venue_key` (required): Venue's code

**Query Parameters:**
- `season` (optional): Season filter (default: current)
- `active` (optional): Only active machines (default: true)

**Example Request:**
```
GET /api/v1/venues/T4B/machines?season=22
```

**Response:**
```json
{
  "success": true,
  "data": {
    "venue_key": "T4B",
    "venue_name": "4Bs Tavern",
    "season": 22,
    "machines": [
      {
        "machine_key": "MM",
        "machine_name": "Medieval Madness",
        "active": true,
        "games_played": 45,
        "median_score": 18500000,
        "date_added": "2024-09-01"
      }
    ],
    "total_count": 18
  },
  "meta": { ... }
}
```

---

### 5. Utility Endpoints

#### POST /api/v1/scores/calculate-percentile

Calculate what percentile a given score would be.

**Request Body:**
```json
{
  "machine": "MM",
  "score": 25000000,
  "venue": "T4B",
  "season": 22
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "machine_key": "MM",
    "machine_name": "Medieval Madness",
    "score": 25000000,
    "percentile": 68.5,
    "rank": "31 out of 45 games",
    "next_milestone": {
      "percentile": 75,
      "score": 28000000,
      "score_needed": 3000000
    }
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/seasons

Get list of available seasons.

**Response:**
```json
{
  "success": true,
  "data": {
    "seasons": [
      {
        "season": 22,
        "year": 2025,
        "current": true,
        "matches": 100,
        "teams": 20
      },
      {
        "season": 21,
        "year": 2024,
        "current": false,
        "matches": 100,
        "teams": 18
      }
    ],
    "current_season": 22
  },
  "meta": { ... }
}
```

---

#### GET /api/v1/matchups/compare

Compare two players on a machine or overall.

**Query Parameters:**
- `player1` (required): First player key
- `player2` (required): Second player key
- `machine` (optional): Machine to compare on
- `venue` (optional): Venue filter
- `season` (optional): Season filter (default: current)

**Example Request:**
```
GET /api/v1/matchups/compare?player1=f69f2cc&player2=a693ae0&machine=MM
```

**Response:**
```json
{
  "success": true,
  "data": {
    "player1": {
      "player_key": "f69f2cc7fc9237f2685addaa14a2ae2ec8709451",
      "name": "Scott Helgason",
      "ipr": 6
    },
    "player2": {
      "player_key": "a693ae0dd694c79f9af8ce9b9a3e612c8a61a4b8",
      "name": "Matthew Greene",
      "ipr": 5
    },
    "machine": {
      "machine_key": "MM",
      "machine_name": "Medieval Madness"
    },
    "comparison": {
      "player1_stats": {
        "games_played": 8,
        "median_score": 28500000,
        "median_percentile": 85.5,
        "best_score": 42000000
      },
      "player2_stats": {
        "games_played": 6,
        "median_score": 22000000,
        "median_percentile": 72.0,
        "best_score": 35000000
      },
      "advantage": {
        "player": "Scott Helgason",
        "percentile_difference": 13.5,
        "confidence": "high"
      }
    },
    "head_to_head": {
      "games_together": 3,
      "player1_wins": 2,
      "player2_wins": 1
    }
  },
  "meta": { ... }
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `PLAYER_NOT_FOUND` | 404 | Player key not found |
| `TEAM_NOT_FOUND` | 404 | Team key not found |
| `MACHINE_NOT_FOUND` | 404 | Machine key not found |
| `VENUE_NOT_FOUND` | 404 | Venue key not found |
| `INVALID_SEASON` | 400 | Invalid season number |
| `INVALID_PARAMETER` | 400 | Invalid query parameter |
| `INSUFFICIENT_DATA` | 400 | Not enough data for calculation |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## Pagination

For endpoints returning large result sets (future):

**Query Parameters:**
- `page` (default: 1)
- `per_page` (default: 20, max: 100)

**Response includes:**
```json
{
  "data": { ... },
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total_pages": 5,
    "total_items": 95,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Caching

- Percentile data cached for 1 week
- Player/team stats cached for 1 day
- Machine lists cached for 1 hour
- Search results cached for 15 minutes

**Cache Headers:**
```
Cache-Control: public, max-age=3600
ETag: "abc123def456"
```

---

## CORS Configuration

Allowed origins:
- `https://mnp-analyzer.vercel.app`
- `http://localhost:3000` (development)

---

---

### 6. Pinball Map Integration

#### GET /api/v1/venues/{venue_key}/pinballmap

Get current machine lineup from Pinball Map (community-maintained data).

**Path Parameters:**
- `venue_key` (required): Venue's code (must have `pinballmap_location_id` configured)

**Query Parameters:**
- `refresh` (optional): Force refresh from Pinball Map API, bypassing 6-hour cache (default: false)

**Example Request:**
```
GET /api/v1/venues/AAB/pinballmap
```

**Response:**
```json
{
  "venue_key": "AAB",
  "venue_name": "Add-a-Ball",
  "pinballmap_location_id": 1410,
  "pinballmap_url": "https://pinballmap.com/map?by_location_id=1410",
  "machines": [
    {
      "id": 2835,
      "name": "Attack From Mars (Remake LE)",
      "year": 2017,
      "manufacturer": "Chicago Gaming",
      "ipdb_link": "https://www.ipdb.org/machine.cgi?id=6385",
      "ipdb_id": 6385,
      "opdb_id": "G4do5-MW9z8"
    },
    {
      "id": 687,
      "name": "The Addams Family",
      "year": 1992,
      "manufacturer": "Bally",
      "ipdb_link": "https://www.ipdb.org/machine.cgi?id=20",
      "ipdb_id": 20,
      "opdb_id": "G4ODR-MDXEy"
    }
  ],
  "machine_count": 26,
  "last_updated": "2026-02-03T20:19:08.721702"
}
```

**Error Responses:**
- `404`: Venue not found or venue does not have Pinball Map location configured
- `502`: Could not connect to Pinball Map API or Pinball Map returned an error

**Notes:**
- Data is cached for 6 hours to avoid excessive API calls to Pinball Map
- Machine data is community-maintained on pinballmap.com and may differ from MNP match data
- Currently configured venues: AAB (1410), 8BT (4295), JUP (8947), KRA (22987), SHR (1126)

---

**API Version**: 1.0
**Last Updated**: 2026-02-03
**Status**: Production - Implementation may differ from this spec

> **Note:** This document was created during the planning phase. For current API implementation, see the live API documentation at https://your-api.railway.app/docs
