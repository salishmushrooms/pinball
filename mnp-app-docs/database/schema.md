# Database Schema Design

## Overview

The MNP Analyzer database uses PostgreSQL with a normalized core schema and denormalized query optimization tables. The design prioritizes:

1. **Query performance** for mobile use cases (< 500ms responses)
2. **Data integrity** through proper relationships and constraints
3. **Efficient indexing** for common access patterns
4. **Pre-calculated aggregations** for expensive computations

## Entity Relationship Diagram

```
players ────────┐
                │
                ├──── scores ──── games ──── matches ──── venues
                │                                      │
teams ──────────┘                                      │
                                                       │
                                              venue_machines
                                                       │
                                                   machines
```

## Core Tables

### players

Stores player identity and current rating information.

```sql
CREATE TABLE players (
    player_key VARCHAR(64) PRIMARY KEY,  -- SHA-1 hash from MNP system
    name VARCHAR(255) NOT NULL,
    current_ipr INTEGER,                 -- Most recent IPR (1-6 scale)
    first_seen_season INTEGER,
    last_seen_season INTEGER,
    total_games_played INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_players_name ON players(name);
CREATE INDEX idx_players_ipr ON players(current_ipr);
```

**Notes:**
- `player_key` is immutable across all seasons
- `name` may change (marriage, preferred name) - track in player_aliases table if needed
- `current_ipr` is the most recent value; historical IPR stored in scores table
- `total_games_played` is a convenience counter, can be recalculated from scores

### teams

Stores team information by season (teams may change season-to-season).

```sql
CREATE TABLE teams (
    team_key VARCHAR(10) NOT NULL,       -- 3-letter code (e.g., "ADB", "TBT")
    season INTEGER NOT NULL,
    team_name VARCHAR(255) NOT NULL,
    home_venue_key VARCHAR(10),
    division VARCHAR(50),                -- Group/division if applicable
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (team_key, season)
);

CREATE INDEX idx_teams_venue ON teams(home_venue_key, season);
CREATE INDEX idx_teams_season ON teams(season);
```

**Notes:**
- Team key may be reused across seasons with different rosters
- `home_venue_key` can be NULL if team has no fixed home venue
- Same team_key + season combination is unique

### venues

Stores venue information (relatively static).

```sql
CREATE TABLE venues (
    venue_key VARCHAR(10) PRIMARY KEY,   -- 3-4 letter code (e.g., "T4B", "JUP")
    venue_name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_venues_active ON venues(active);
```

**Notes:**
- `venue_key` is stable across seasons
- `active` flag indicates if venue is currently in use
- Address information optional but useful for future features

### machines

Stores canonical machine information.

```sql
CREATE TABLE machines (
    machine_key VARCHAR(50) PRIMARY KEY,  -- Canonical key from machine_variations.json
    machine_name VARCHAR(255) NOT NULL,   -- Full display name
    manufacturer VARCHAR(100),
    year INTEGER,
    game_type VARCHAR(50),                -- SS (solid state), EM (electromechanical), etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_machines_name ON machines(machine_name);
```

**Notes:**
- `machine_key` matches canonical keys in machine_variations.json
- Additional metadata (manufacturer, year) enriches the app
- Source: Combine machine_variations.json + external data (IPDB)

### machine_aliases

Maps alternate machine names/codes to canonical machine_key.

```sql
CREATE TABLE machine_aliases (
    alias VARCHAR(100) PRIMARY KEY,
    machine_key VARCHAR(50) NOT NULL REFERENCES machines(machine_key),
    alias_type VARCHAR(20),               -- 'abbreviation', 'alternate_name', 'typo'

    FOREIGN KEY (machine_key) REFERENCES machines(machine_key)
);

CREATE INDEX idx_aliases_machine ON machine_aliases(machine_key);
```

**Notes:**
- Populated from machine_variations.json variations array
- Enables fuzzy search and handles data entry inconsistencies
- Examples: "MM" → "MedievalMadness", "T2" → "Terminator2"

### venue_machines

Junction table tracking which machines are at which venues by season.

```sql
CREATE TABLE venue_machines (
    venue_key VARCHAR(10) NOT NULL,
    machine_key VARCHAR(50) NOT NULL,
    season INTEGER NOT NULL,
    active BOOLEAN DEFAULT true,
    date_added DATE,
    date_removed DATE,

    PRIMARY KEY (venue_key, machine_key, season),
    FOREIGN KEY (venue_key) REFERENCES venues(venue_key),
    FOREIGN KEY (machine_key) REFERENCES machines(machine_key)
);

CREATE INDEX idx_venue_machines_venue ON venue_machines(venue_key, season, active);
CREATE INDEX idx_venue_machines_machine ON venue_machines(machine_key);
```

**Notes:**
- Source: Venue.machines array from match JSON files
- `active` tracks if machine is currently on the floor
- `date_added`/`date_removed` track machine rotation (future feature)
- One machine can appear at multiple venues

### matches

Stores match metadata.

```sql
CREATE TABLE matches (
    match_key VARCHAR(50) PRIMARY KEY,    -- e.g., "mnp-22-1-ADB-TBT"
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    date DATE,
    venue_key VARCHAR(10) NOT NULL,
    home_team_key VARCHAR(10) NOT NULL,
    away_team_key VARCHAR(10) NOT NULL,
    state VARCHAR(20) NOT NULL,           -- 'complete', 'playing', 'scheduled'

    home_team_points INTEGER,             -- Total match points
    away_team_points INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (venue_key) REFERENCES venues(venue_key),
    FOREIGN KEY (home_team_key, season) REFERENCES teams(team_key, season),
    FOREIGN KEY (away_team_key, season) REFERENCES teams(team_key, season)
);

CREATE INDEX idx_matches_season_week ON matches(season, week);
CREATE INDEX idx_matches_venue ON matches(venue_key, season);
CREATE INDEX idx_matches_teams ON matches(home_team_key, away_team_key, season);
CREATE INDEX idx_matches_date ON matches(date);
```

**Notes:**
- `match_key` format: `mnp-{season}-{week}-{away}-{home}`
- `state` tracks completion status
- Team points calculated from individual game results
- Date is match date, not data entry date

### games

Stores individual game instances (4 per match).

```sql
CREATE TABLE games (
    game_id SERIAL PRIMARY KEY,
    match_key VARCHAR(50) NOT NULL,
    round_number INTEGER NOT NULL,        -- 1-4
    game_number INTEGER NOT NULL,         -- 1-2 (some rounds have multiple games)
    machine_key VARCHAR(50) NOT NULL,
    done BOOLEAN DEFAULT false,

    -- Denormalized for query performance
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    venue_key VARCHAR(10) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (match_key) REFERENCES matches(match_key),
    FOREIGN KEY (machine_key) REFERENCES machines(machine_key),

    UNIQUE (match_key, round_number, game_number)
);

CREATE INDEX idx_games_match ON games(match_key);
CREATE INDEX idx_games_machine ON games(machine_key, season);
CREATE INDEX idx_games_machine_venue ON games(machine_key, venue_key, season);
```

**Notes:**
- `game_id` is surrogate key for easier referencing
- Round 1,4 = 4-player games; Round 2,3 = 2-player games
- `done` flag indicates if game was completed (some games abandoned)
- Denormalized season/week/venue for faster filtering without joins

### scores

Stores individual player scores with full context.

```sql
CREATE TABLE scores (
    score_id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL,
    player_key VARCHAR(64) NOT NULL,
    player_position INTEGER NOT NULL,     -- 1-4 (position in game)
    score BIGINT NOT NULL,
    team_key VARCHAR(10) NOT NULL,
    is_home_team BOOLEAN NOT NULL,
    player_ipr INTEGER,                   -- IPR at time of match

    -- Denormalized for query performance (avoids 4-way joins)
    match_key VARCHAR(50) NOT NULL,
    venue_key VARCHAR(10) NOT NULL,
    machine_key VARCHAR(50) NOT NULL,
    round_number INTEGER NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    date DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_key) REFERENCES players(player_key),
    FOREIGN KEY (machine_key) REFERENCES machines(machine_key)
);

-- Critical indexes for common queries
CREATE INDEX idx_scores_player_machine ON scores(player_key, machine_key, season);
CREATE INDEX idx_scores_machine_venue ON scores(machine_key, venue_key, season);
CREATE INDEX idx_scores_team ON scores(team_key, season);
CREATE INDEX idx_scores_game ON scores(game_id);
CREATE INDEX idx_scores_player_venue ON scores(player_key, venue_key, season);
CREATE INDEX idx_scores_machine_score ON scores(machine_key, score);  -- For percentile queries
```

**Notes:**
- Heavy denormalization for read performance (acceptable for write-rare data)
- `player_position` indicates reliability (position 4 in 4-player games less reliable for player final score however whether a player won or lost against their opponents  would be reliable. A player might stop playing if their score was already above their opponents)
- `player_ipr` is snapshot at time of match (players improve over time)
- This table will be the largest (tens of thousands of rows)

## Aggregate/Cache Tables

These tables store pre-calculated statistics for performance.

### score_percentiles

Pre-calculated percentile thresholds for each machine/venue/season combination.

```sql
CREATE TABLE score_percentiles (
    id SERIAL PRIMARY KEY,
    machine_key VARCHAR(50) NOT NULL,
    venue_key VARCHAR(10),                -- NULL = all venues combined
    season INTEGER NOT NULL,
    percentile INTEGER NOT NULL,          -- 0-100
    score_threshold BIGINT NOT NULL,      -- Score needed to reach this percentile
    sample_size INTEGER NOT NULL,         -- Number of games in calculation
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (machine_key, venue_key, season, percentile),
    FOREIGN KEY (machine_key) REFERENCES machines(machine_key)
);

CREATE INDEX idx_percentiles_lookup ON score_percentiles(machine_key, venue_key, season);
CREATE INDEX idx_percentiles_machine ON score_percentiles(machine_key, season);
```

**Notes:**
- Pre-calculated for percentiles: 25, 50, 75, 90, 95
- `venue_key = NULL` represents aggregate across all venues
- Recalculated weekly or on-demand when new data loaded
- Massive performance improvement vs. calculating on each request

### player_machine_stats

Aggregated player performance by machine.

```sql
CREATE TABLE player_machine_stats (
    player_key VARCHAR(64) NOT NULL,
    machine_key VARCHAR(50) NOT NULL,
    venue_key VARCHAR(10),                -- NULL = all venues
    season INTEGER NOT NULL,

    games_played INTEGER NOT NULL,
    total_score BIGINT,                   -- Sum of all scores
    median_score BIGINT,
    avg_score BIGINT,
    best_score BIGINT,
    worst_score BIGINT,

    median_percentile DECIMAL(5,2),       -- Median percentile rank (0-100)
    avg_percentile DECIMAL(5,2),

    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (player_key, machine_key, venue_key, season),
    FOREIGN KEY (player_key) REFERENCES players(player_key),
    FOREIGN KEY (machine_key) REFERENCES machines(machine_key)
);

CREATE INDEX idx_player_stats_player ON player_machine_stats(player_key, season);
CREATE INDEX idx_player_stats_best_machines ON player_machine_stats(
    player_key,
    venue_key,
    season,
    median_percentile DESC
);
CREATE INDEX idx_player_stats_machine ON player_machine_stats(machine_key, season);
```

**Notes:**
- Powers "best machines for player X" queries
- `venue_key = NULL` represents all venues combined
- Percentiles calculated against score_percentiles table
- Recalculated when new games added

### team_machine_picks

Aggregated team machine selection patterns.

```sql
CREATE TABLE team_machine_picks (
    team_key VARCHAR(10) NOT NULL,
    machine_key VARCHAR(50) NOT NULL,
    season INTEGER NOT NULL,
    is_home BOOLEAN NOT NULL,
    round_type VARCHAR(10) NOT NULL,      -- 'singles' or 'doubles'

    times_picked INTEGER NOT NULL,
    wins INTEGER,                          -- Games won on this machine
    total_points INTEGER,                  -- MNP points earned
    avg_score BIGINT,

    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (team_key, machine_key, season, is_home, round_type),
    FOREIGN KEY (team_key, season) REFERENCES teams(team_key, season),
    FOREIGN KEY (machine_key) REFERENCES machines(machine_key)
);

CREATE INDEX idx_team_picks_team ON team_machine_picks(
    team_key,
    season,
    is_home,
    round_type,
    times_picked DESC
);
```

**Notes:**
- Powers "team X's favorite picks" queries
- Separate stats for home/away and singles/doubles
- Can calculate success rate from wins/times_picked
- Useful for opponent scouting

## Data Integrity Rules

### Constraints

1. **Player Position Validation**
   - Rounds 1,4: positions 1-4 allowed
   - Rounds 2,3: positions 1-2 only
   - Enforced via application logic or check constraint

2. **Score Validity**
   - Scores must be >= 0
   - most validation done already from MNP app that is used to input data

3. **Season/Week Validation**
   - Season: 20-99 (representing 20xx)
   - Week: 1-10 for regular season, 11+ for playoffs

4. **Match Completion Logic**
   - Match state = 'complete' only if all 4 rounds have done=true games

### Referential Integrity

- All foreign keys enforced at database level
- Cascading deletes disabled (preserve data integrity)
- Updates cascade for key changes (rare)

## Data Types and Ranges

| Field | Type | Range/Format | Notes |
|-------|------|--------------|-------|
| player_key | VARCHAR(64) | SHA-1 hash | 40 hex characters |
| team_key | VARCHAR(10) | 3-letter code | Uppercase, e.g., "ADB" |
| venue_key | VARCHAR(10) | 3-4 letter code | Uppercase, e.g., "T4B" |
| machine_key | VARCHAR(50) | Canonical name | From variations.json |
| season | INTEGER | 20-99 | Represents 20xx year |
| week | INTEGER | 1-15 | 1-10 regular, 11+ playoffs |
| ipr | INTEGER | 1-6 | MNP skill rating |
| score | BIGINT | 0 - 10,000,000,000 | Pinball scores vary widely |
| percentile | DECIMAL(5,2) | 0.00 - 100.00 | Two decimal precision |

## Storage Estimates

Assuming 10 seasons of data, 20 teams per season, 10 matches per team, 4 rounds per match:

| Table | Rows | Estimated Size |
|-------|------|----------------|
| players | 500 | 50 KB |
| teams | 200 | 20 KB |
| venues | 30 | 5 KB |
| machines | 200 | 30 KB |
| machine_aliases | 1,000 | 50 KB |
| venue_machines | 3,000 | 100 KB |
| matches | 2,000 | 300 KB |
| games | 8,000 | 500 KB |
| scores | 24,000 | 4 MB |
| score_percentiles | 50,000 | 2 MB |
| player_machine_stats | 100,000 | 10 MB |
| team_machine_picks | 10,000 | 500 KB |
| **Total** | | **~18 MB** |

> **Note:** These are initial estimates from the planning phase. The actual production database is larger with 6 seasons (18-23) loaded, containing 943+ matches and 56,504+ scores. Check Railway dashboard for current storage usage.

**Additional Note:** Indexes will approximately double storage requirements.

## Maintenance Procedures

### Weekly Refresh
1. Run ETL pipeline to load new matches
2. Recalculate score_percentiles for affected machines
3. Update player_machine_stats for players with new games
4. Update team_machine_picks for teams with new matches
5. Vacuum and analyze tables

### Seasonal Refresh
1. Full recalculation of all aggregate tables
2. Database optimization (reindex, vacuum full)
3. Archive old seasons if needed
4. Update current_ipr for all players

### Data Quality Checks
- Verify all matches have 4 rounds
- Flag outlier scores (> 3 standard deviations)
- Check for duplicate game entries
- Validate venue machine lists against match data

## Migration Strategy

### Initial Schema Creation
```sql
-- Run in order:
1. schema.sql (CREATE TABLE statements)
2. indexes.sql (CREATE INDEX statements)
3. constraints.sql (ALTER TABLE foreign keys)
```

### Schema Evolution
- Use SQL migrations in `schema/migrations/` directory
- Never modify existing columns (add new, deprecate old)
- Maintain backwards compatibility for API
- Version migrations with semantic versioning

> **Note:** Originally planned to use Alembic, but implementation uses raw SQL migrations in `schema/migrations/` directory.

## Future Enhancements

### Potential Additions
- `player_aliases` table for name changes
- `match_events` table for real-time updates
- `machine_conditions` table for tracking machine state
- `player_achievements` table for badges/milestones
- `comments` table for social features
- `predictions` table for ML model outputs

### Partitioning Strategy
If data grows beyond 1M rows in scores table:
- Partition by season (most common filter)
- Partition by machine_key hash (if multi-season queries common)
- Consider TimescaleDB for time-series optimization

---

**Schema Version**: 1.0.0
**Last Updated**: 2026-01-14
**Status**: Implemented - Using PostgreSQL 15 on Railway

> **Note:** This document was created during the planning phase. The actual implementation is in use on Railway and local development, but some details may differ from the original design specifications.
