# MNP ETL Scripts - Actual Implementation

**Last Updated:** 2026-01-26
**Location:** `/etl` directory

> **Note:** This documents the actual ETL implementation.
> For operational guidance on running these scripts, see [DATA_UPDATE_STRATEGY.md](../../DATA_UPDATE_STRATEGY.md).

---

## Overview

The MNP ETL pipeline consists of 15 Python scripts that load match data from JSON files into PostgreSQL, calculate various aggregations, and refresh external data. Scripts are designed to be **idempotent** - safe to run multiple times.

### Key Principles

- **Local execution recommended** - Running against Railway production DB is slow (network latency)
- **Upsert logic** - All scripts use `ON CONFLICT DO UPDATE` for safe re-runs
- **Dependency order matters** - Some scripts must run before others
- **Environment override** - Use `DATABASE_URL` environment variable to target local DB
- **External data via batch** - Matchplay.events data is refreshed via ETL, not live API calls

---

## Script Overview

| Script | Purpose | Dependencies | Frequency |
|--------|---------|--------------|-----------|
| `load_season.py` | Load match data from JSON | None | Weekly |
| `load_preseason.py` | Load preseason schedule | None | Once per season |
| `calculate_percentiles.py` | Calculate score percentiles | `load_season.py` | After loading data |
| `calculate_player_stats.py` | Calculate player aggregates | `calculate_percentiles.py` | After percentiles |
| `calculate_team_machine_picks.py` | Calculate team machine selection patterns | `load_season.py` | After loading data |
| `calculate_player_totals.py` | Calculate cross-season player totals | `load_season.py` | After loading data |
| `calculate_match_points.py` | Calculate match point totals | `load_season.py` | After loading data |
| `refresh_matchplay_data.py` | Refresh Matchplay.events data for linked players | Linked accounts | Weekly (optional) |
| `run_full_pipeline.py` | Run all steps in order | None | Full season backfill |
| `update_season.py` | Orchestrate weekly update | None | Weekly (convenience wrapper) |
| `update_team_venues.py` | Update team home venues | `load_season.py` | As needed |
| `update_ipr.py` | Update player IPR from CSV | None | As needed |
| `export_machine_stats.py` | Export machine statistics to JSON | `load_season.py` | As needed |
| `config.py` | Configuration module | N/A | Imported by all |
| `database.py` | Database connection manager | N/A | Imported by all |

---

## Core Loading Scripts

### `load_season.py`

**Purpose:** Load completed match data from JSON files into database.

**Usage:**
```bash
python etl/load_season.py --season 22
python etl/load_season.py --season 22 --verbose
```

**Arguments:**
- `--season` (required): Season number to load (e.g., 22)
- `--verbose` (optional): Enable verbose logging

**What it loads:**
1. Machine variations and aliases from `machine_variations.json`
2. Venues from `venues.json` and match files
3. Teams from `teams.csv` (if exists) and match files
4. Players from match lineups
5. Player IPR ratings from `IPR.csv` (if exists)
6. Match metadata
7. Games (4 per match)
8. Scores (8-12 per match, depending on round type)

**Database tables affected:**
- `machines` - Pinball machine definitions
- `machine_aliases` - Machine name variations
- `venues` - Venue definitions
- `venue_machines` - Machines available at each venue
- `teams` - Team definitions per season
- `players` - Player definitions (upsert)
- `matches` - Match metadata (state set to 'complete')
- `games` - Individual games within matches
- `scores` - Individual player scores

**Dependencies:** None (can run independently)

**Notes:**
- Uses `ON CONFLICT DO UPDATE` for idempotency
- Safe to run multiple times - only new data is added
- Only loads matches with complete JSON data
- Normalizes machine keys using `machine_variations.json`
- Enriches venue data from `venues.json` if available

**Performance:** ~10-20 seconds for one season (local DB)

---

### `load_preseason.py`

**Purpose:** Load preseason metadata before matches are played.

**Usage:**
```bash
python etl/load_preseason.py --season 23
python etl/load_preseason.py --season 23 --verbose
```

**Arguments:**
- `--season` (required): Season number to load (e.g., 23)
- `--verbose` (optional): Enable verbose logging

**What it loads:**
1. Machine variations and aliases
2. Venues from `venues.csv` and `venues.json`
3. Teams from `teams.csv`
4. Players from `rosters.csv`
5. Planned matches from `matches.csv` (state='scheduled')

**Required files:**
- `mnp-data-archive/season-{N}/venues.csv` - Venue definitions
- `mnp-data-archive/season-{N}/teams.csv` - Team definitions
- `mnp-data-archive/season-{N}/rosters.csv` - Player rosters
- `mnp-data-archive/season-{N}/matches.csv` - Match schedule

**Database tables affected:**
- `machines`, `machine_aliases`
- `venues`
- `teams`
- `players`
- `matches` (state='scheduled')

**Dependencies:** None

**Notes:**
- Does NOT require the `matches/` directory with match JSON files
- Used before season starts to populate schedules and rosters
- Matches are marked as 'scheduled' (not 'complete')
- Safe to run before season begins

**Performance:** ~5-10 seconds

---

## Aggregation/Calculation Scripts

### `calculate_percentiles.py`

**Purpose:** Calculate score percentile thresholds for each machine and populate `score_percentiles` table.

**Usage:**
```bash
python etl/calculate_percentiles.py --season 22
python etl/calculate_percentiles.py --season 22 --verbose
python etl/calculate_percentiles.py --season 22 --venue-specific  # Not yet implemented
```

**Arguments:**
- `--season` (required): Season number (e.g., 22)
- `--venue-specific` (optional): Calculate per venue (future feature)
- `--verbose` (optional): Enable verbose logging

**What it calculates:**
For each machine in the season:
- Percentile thresholds: 10th, 25th, 50th, 75th, 90th, 95th, 99th
- Sample size (number of scores)
- Mean and standard deviation

**Database tables affected:**
- `score_percentiles` - Percentile thresholds per machine/season

**Dependencies:**
- **CRITICAL:** Must run AFTER `load_season.py` (requires scores to exist)
- **CRITICAL:** Must run BEFORE `calculate_player_stats.py` (player stats depend on percentiles)

**Notes:**
- Requires at least 10 scores per machine for meaningful percentiles
- Skips machines with insufficient data
- Clears existing percentiles for season before recalculating
- Uses `venue_key = '_ALL_'` for global (non-venue-specific) percentiles
- Safe to re-run

**Performance:** ~15 seconds for all seasons

---

### `calculate_player_stats.py`

**Purpose:** Calculate player machine statistics and populate `player_machine_stats` table.

**Usage:**
```bash
python etl/calculate_player_stats.py --season 22
python etl/calculate_player_stats.py --season 22 --verbose
python etl/calculate_player_stats.py --season 22 --venue-specific  # Not yet implemented
```

**Arguments:**
- `--season` (required): Season number (e.g., 22)
- `--venue-specific` (optional): Calculate per venue (future feature)
- `--verbose` (optional): Enable verbose logging

**What it calculates:**
For each player/machine combination:
- `games_played` - Number of games played
- `total_score` - Sum of all scores
- `median_score` - Median score
- `avg_score` - Average score
- `best_score` - Highest score
- `worst_score` - Lowest score
- `median_percentile` - Percentile ranking based on median score
- `avg_percentile` - Average percentile ranking

**Database tables affected:**
- `player_machine_stats` - Aggregated player statistics

**Dependencies:**
- **CRITICAL:** Must run AFTER `calculate_percentiles.py` (uses percentile data)
- Requires `scores` table to be populated

**Notes:**
- Clears existing stats for season before recalculating
- Uses global aggregation (venue_key='_ALL_')
- Percentile calculation interpolates between known percentile thresholds
- Logs progress every 1000 records
- Safe to re-run

**Performance:** ~30-45 seconds for all seasons

---

### `calculate_team_machine_picks.py`

**Purpose:** Calculate team machine pick statistics based on MNP selection rules.

**Usage:**
```bash
python etl/calculate_team_machine_picks.py --season 22
python etl/calculate_team_machine_picks.py --season 22 --verbose
```

**Arguments:**
- `--season` (required): Season number (e.g., 22)
- `--verbose` (optional): Enable verbose logging

**What it calculates:**
For each team/machine/context combination:
- `times_picked` - How many times team picked this machine
- `wins` - Number of round wins on this machine
- `total_points` - Points earned on this machine
- `avg_score` - Average score on this machine

**MNP Selection Rules:**
- **Home team picks:** Rounds 2 & 4
- **Away team picks:** Rounds 1 & 3
- **Doubles:** Rounds 1 & 4 (4 players)
- **Singles:** Rounds 2 & 3 (2 players)

**Database tables affected:**
- `team_machine_picks` - Team machine selection statistics

**Dependencies:**
- Requires `games` and `scores` tables to be populated
- Must run after `load_season.py`

**Notes:**
- Clears existing picks for season before recalculating
- Tracks picks separately by home/away status and round type
- Win calculation based on team total score vs opponent
- Safe to re-run

**Performance:** ~10-15 seconds per season

---

### `calculate_player_totals.py`

**Purpose:** Calculate and update player total games played across all seasons.

**Usage:**
```bash
python etl/calculate_player_totals.py
python etl/calculate_player_totals.py --verbose
```

**Arguments:**
- `--verbose` (optional): Enable verbose logging

**What it calculates:**
- `total_games_played` - Total games played across all seasons for each player

**Database tables affected:**
- `players.total_games_played` - Updates player record

**Dependencies:**
- Requires `scores` table to be populated
- Must run after `load_season.py`

**Notes:**
- No season argument - processes ALL seasons at once
- Counts distinct games by `game_id`
- Updates player records in batches of 100
- Safe to re-run

**Performance:** ~5-10 seconds

---

### `calculate_match_points.py`

**Purpose:** Calculate and update match point totals (home_team_points, away_team_points).

**Usage:**
```bash
python etl/calculate_match_points.py --season 22
python etl/calculate_match_points.py --season 22 --verbose
```

**Arguments:**
- `--season` (required): Season number (e.g., 22)
- `--verbose` (optional): Enable verbose logging

**What it calculates:**
- `home_team_points` - Total points earned by home team across all 4 rounds
- `away_team_points` - Total points earned by away team across all 4 rounds

**MNP Scoring:**
- Singles (Rounds 2 & 3): 3 points per game (winner takes all or split)
- Doubles (Rounds 1 & 4): 5 points per game (based on position finishes)
- Match total is sum of all game points

**Database tables affected:**
- `matches.home_team_points`, `matches.away_team_points`

**Dependencies:**
- Requires match JSON files (reads points from source data)
- Must run after `load_season.py`

**Notes:**
- Only processes matches with `state='complete'`
- Reads points from original JSON files (not calculated)
- Safe to re-run

**Performance:** ~5-10 seconds per season

---

## Pipeline Orchestration Scripts

### `run_full_pipeline.py`

**Purpose:** Run all ETL steps in correct order for complete data loading.

**Usage:**
```bash
# Load specific seasons
python etl/run_full_pipeline.py --seasons 22
python etl/run_full_pipeline.py --seasons 18 19 20 21 22

# Load all available seasons (18-22)
python etl/run_full_pipeline.py --all-seasons

# Skip loading step (just run aggregates)
python etl/run_full_pipeline.py --seasons 22 --skip-load

# Only run aggregate calculations
python etl/run_full_pipeline.py --only-aggregates
```

**Arguments:**
- `--seasons` (optional): Space-separated season numbers (e.g., `--seasons 21 22`)
- `--all-seasons` (optional): Load all available seasons (currently 20, 21, 22)
- `--skip-load` (optional): Skip `load_season.py` step (use when data already loaded)
- `--only-aggregates` (optional): Only run aggregate calculations (steps 2-6)

**Pipeline Steps (in order):**
1. `load_season.py` - Load raw match data
2. `calculate_percentiles.py` - Calculate score percentiles
3. `calculate_player_stats.py` - Aggregate player statistics
4. `calculate_team_machine_picks.py` - Calculate team machine picks
5. `calculate_player_totals.py` - Calculate cross-season player totals (runs once for all data)
6. `calculate_match_points.py` - Calculate match point totals

**Dependencies:** None (orchestrates all other scripts)

**Notes:**
- Single source of truth for complete ETL pipeline
- Respects dependencies between scripts
- Continues on error but reports failures
- Each script runs as subprocess with proper error handling
- Use for full season backfills or database rebuilds

**Performance:** ~3-5 minutes for one complete season

---

### `refresh_matchplay_data.py`

**Purpose:** Refresh Matchplay.events profile data for all linked players.

**Usage:**
```bash
# Refresh all linked players
python etl/refresh_matchplay_data.py

# Preview what would be refreshed (no changes)
python etl/refresh_matchplay_data.py --dry-run

# Refresh only first 10 players (for testing)
python etl/refresh_matchplay_data.py --limit 10 --verbose
```

**Arguments:**
- `--dry-run` (optional): Show what would be refreshed without making changes
- `--limit` (optional): Limit number of players to refresh (for testing)
- `--verbose` (optional): Enable verbose logging

**What it refreshes:**
For each player with a linked Matchplay account:
- Rating (value, RD, lower bound)
- Game counts (played, wins, losses, efficiency percent)
- IFPA data (ID, rank, rating, women's rank)
- Tournament count
- Profile info (location, avatar)

**Environment Requirements:**
- `MATCHPLAY_API_TOKEN` - Required API token from Matchplay.events

**Database tables affected:**
- `matchplay_ratings` - Cached profile data

**Dependencies:**
- Requires `matchplay_player_mappings` entries (players must be linked first)

**Notes:**
- Respects Matchplay API rate limits
- Adds small delay between requests to avoid hitting limits
- Stops gracefully if rate limit is nearly exhausted
- Should be run weekly as part of ETL pipeline
- Can be run standalone or via `run_full_pipeline.py --refresh-matchplay`

**Performance:** ~1-2 minutes for ~50 linked players (depends on API response time)

---

### `update_season.py`

**Purpose:** Orchestrate full update process for a season (convenience wrapper).

**Usage:**
```bash
# Update local database for a single season
python etl/update_season.py --season 22

# Update multiple seasons
python etl/update_season.py --season 20 21 22

# Update and sync to production
python etl/update_season.py --season 22 --sync-production

# Skip aggregation calculations (just load raw data)
python etl/update_season.py --season 22 --skip-aggregations

# Verbose output
python etl/update_season.py --season 22 --verbose
```

**Arguments:**
- `--season` (required): Season number(s) to update (e.g., `--season 22` or `--season 20 21 22`)
- `--sync-production` (optional): Also sync data to production database via Railway
- `--skip-aggregations` (optional): Skip aggregation calculations (just load raw data)
- `--verbose` (optional): Enable verbose logging

**What it does:**
1. Load season data (`load_season.py`)
2. Calculate aggregations (if not skipped):
   - Percentiles
   - Player stats
   - Team machine picks
   - Match points
3. Calculate cross-season player totals
4. Verify data (summary of loaded records)
5. Optionally sync to production:
   - Export local database to SQL
   - Import to Railway via `railway connect postgres`

**Aggregation Seasons:**
Currently configured to calculate aggregations for seasons 20, 21, 22 only.
Seasons 18-19 are loaded but excluded from calculations per project decision.

**Dependencies:** None (orchestrates other scripts)

**Notes:**
- Idempotent - safe to run multiple times
- Designed for weekly match updates
- Sync requires Railway CLI: `npm install -g @railway/cli`
- Sync uses bulk import for performance (much faster than direct remote loads)

**Performance:**
- Local update: ~2-3 minutes
- With production sync: ~3-4 minutes

---

## Utility Scripts

### `update_team_venues.py`

**Purpose:** Update team `home_venue_key` from season CSV files.

**Usage:**
```bash
python etl/update_team_venues.py --season 22
python etl/update_team_venues.py --season 22 --verbose
```

**Arguments:**
- `--season` (required): Season number to update (e.g., 22)
- `--verbose` (optional): Enable verbose logging

**What it does:**
- Reads `teams.csv` from season directory
- Updates `teams.home_venue_key` in database

**CSV Format:**
```csv
team_key,venue_key,team_name
ADB,ADM,Admiraballs
TRL,TRL,Trail Blazers
```

**Database tables affected:**
- `teams.home_venue_key`

**Dependencies:**
- Requires teams to exist in database
- Must run after `load_season.py` or `load_preseason.py`

**Notes:**
- Useful when team venues change mid-season
- Only updates existing team records
- Safe to re-run

**Performance:** <1 second

---

### `update_ipr.py`

**Purpose:** Standalone script to update player IPR values from IPR.csv.

**Usage:**
```bash
python etl/update_ipr.py
python etl/update_ipr.py --verbose
```

**Arguments:**
- `--verbose` (optional): Enable verbose logging

**What it does:**
- Reads `mnp-data-archive/IPR.csv`
- Updates `players.current_ipr` in database

**CSV Format:**
IPR.csv contains player ratings (IPR = International Pinball Ranking class, 1-6 scale)

**Database tables affected:**
- `players.current_ipr`

**Dependencies:**
- Requires players to exist in database
- Must run after `load_season.py` or `load_preseason.py`

**Notes:**
- Useful when IPR ratings are updated independently
- Does not require reloading all season data
- Skips players not found in database
- Safe to re-run

**Performance:** <1 second

---

### `export_machine_stats.py`

**Purpose:** Export machine score statistics for machines with >50 plays to JSON.

**Usage:**
```bash
python etl/export_machine_stats.py
python etl/export_machine_stats.py --output machine_stats.json
python etl/export_machine_stats.py --min-plays 100
```

**Arguments:**
- `--output` (optional): Output file path (default: `machine_score_stats.json`)
- `--min-plays` (optional): Minimum plays threshold (default: 50)

**What it exports:**
For each machine with sufficient plays:
- Machine metadata (name, manufacturer, year)
- Seasons played
- Comprehensive statistics:
  - Central tendency: mean, median, mode
  - Spread: std_dev, variance, range, IQR
  - Percentiles: 5th, 10th, 25th, 50th, 75th, 90th, 95th, 99th
  - Shape: skewness, kurtosis
  - Coefficient of variation (relative variability)
- Human-readable interpretation:
  - Skewness meaning (right-skewed, symmetric, etc.)
  - Kurtosis meaning (heavy-tailed, light-tailed, etc.)
  - Variability level (very high, high, moderate, low)
  - Score tiers (poor, below average, above average, good, excellent, exceptional)

**Current Configuration:**
- Includes seasons 20, 21, 22
- Default minimum: 50 plays per machine

**Output Format:** JSON with metadata and machine array

**Dependencies:**
- Requires `scores` and `machines` tables to be populated

**Notes:**
- Uses NumPy for statistical calculations
- Uses SciPy for skewness and kurtosis
- Designed for LLM consumption (includes interpretation hints)
- Scores are from competitive league play (not casual)
- Safe to re-run

**Performance:** ~5-10 seconds

---

## Configuration & Infrastructure Scripts

### `config.py`

**Purpose:** Configuration module for ETL pipeline.

**What it provides:**
- Database connection configuration
- Data path configuration
- ETL settings (batch size)
- Helper methods for season paths

**Configuration Sources:**
1. Environment variables from `.env` file
2. Fallback to sensible defaults

**Key Settings:**
```python
# Database
DATABASE_URL - Primary database URL (from LOCAL_DATABASE_URL or DATABASE_URL env var)
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD - Individual components

# Paths
PROJECT_ROOT - Project root directory
DATA_PATH - mnp-data-archive directory
MACHINE_VARIATIONS_FILE - machine_variations.json path

# ETL
BATCH_SIZE - Number of records to insert at once (default: 1000)
```

**Helper Methods:**
- `get_database_url()` - Get SQLAlchemy database URL
- `get_season_path(season)` - Get path to season data directory
- `get_matches_path(season)` - Get path to season matches directory

**Notes:**
- Singleton instance created as `config`
- Imported by all ETL scripts
- Prefers `LOCAL_DATABASE_URL` over `DATABASE_URL` for local development

---

### `database.py`

**Purpose:** Database connection and session management.

**What it provides:**
- Database engine creation
- Session management
- Connection pooling configuration
- Query execution utilities

**Key Features:**
- **Auto-detection:** Uses connection pooling for API mode, NullPool for ETL
- **Pool configuration:** 5 base connections, 10 max overflow for API mode
- **Connection verification:** Pre-ping before use, recycle after 5 minutes
- **Error handling:** Test connection on startup, report schema version

**Usage:**
```python
from etl.database import db

# Connect to database
db.connect()

# Execute query
result = db.execute("SELECT * FROM matches WHERE season = :season", {'season': 22})

# Get session
session = db.get_session()

# Close connection
db.close()
```

**Connection Modes:**
- **API Mode:** Connection pooling enabled (better for concurrent requests)
- **ETL Mode:** NullPool (better for batch jobs, prevents connection exhaustion)

**Notes:**
- Singleton instance created as `db`
- Checks `schema_version` table on connect
- Logs connection status and schema version
- Properly handles cleanup with `dispose()`

---

## Execution Order & Dependencies

### Critical Dependency Chain

```
1. load_season.py
   ↓ (requires scores to exist)
2. calculate_percentiles.py
   ↓ (requires percentiles to exist)
3. calculate_player_stats.py
```

**Why this matters:**
- `player_machine_stats` includes percentile rankings
- Percentile rankings are calculated from `score_percentiles`
- If you calculate player stats before percentiles, percentile fields will be NULL

### Weekly Update (Correct Order)

```bash
# 1. Load new match data
python etl/load_season.py --season 23

# 2. Recalculate percentiles (required before player stats)
python etl/calculate_percentiles.py --season 23

# 3. Recalculate player stats
python etl/calculate_player_stats.py --season 23

# 4. Optional: Recalculate other aggregates
python etl/calculate_team_machine_picks.py --season 23
python etl/calculate_player_totals.py
python etl/calculate_match_points.py --season 23
```

### Preseason Setup

```bash
# Load scheduled matches, teams, rosters
python etl/load_preseason.py --season 23
```

### Full Pipeline (All Seasons)

```bash
python etl/run_full_pipeline.py --seasons 18 19 20 21 22 23
```

---

## Environment Configuration

### Local Development

Override `DATABASE_URL` to use local PostgreSQL:

```bash
DATABASE_URL=postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer \
  python etl/load_season.py --season 22
```

### .env File

Scripts load configuration from `.env` file in project root:

```bash
# Local database (preferred for ETL)
LOCAL_DATABASE_URL=postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer

# Production database (Railway)
DATABASE_URL=postgresql://postgres:xxx@shinkansen.proxy.rlwy.net:49342/railway
```

**Precedence:** `LOCAL_DATABASE_URL` > `DATABASE_URL` > defaults

---

## Performance Characteristics

### Load Times (Local Database)

| Operation | Time | Records |
|-----------|------|---------|
| Load season 22 | ~15s | 190 matches, ~11,000 scores |
| Calculate percentiles (all seasons) | ~15s | ~150 machines per season |
| Calculate player stats (all seasons) | ~40s | ~50,000 player/machine combos |
| Calculate team picks | ~10s | ~500 team/machine combos |
| Calculate player totals | ~5s | ~900 players |
| Calculate match points | ~5s | ~190 matches |
| **Full pipeline (1 season)** | **~2-3 min** | Complete |

### Remote Database (Railway)

Running ETL directly against Railway is **10-100x slower** due to network latency:
- Individual INSERTs over network: ~50-100ms each
- 1000 scores = 50-100 seconds just for inserts
- **Recommendation:** Run locally, then bulk import via `psql`

---

## Common Issues & Troubleshooting

### NULL Percentiles in Player Stats

**Symptom:** `median_percentile` and `avg_percentile` are NULL in `player_machine_stats`

**Cause:** Player stats calculated before percentiles

**Fix:** Recalculate in correct order:
```bash
DATABASE_URL=$LOCAL_DB python etl/calculate_percentiles.py --season 22
DATABASE_URL=$LOCAL_DB python etl/calculate_player_stats.py --season 22
```

### ETL Script Hanging

**Symptom:** Script appears frozen during database operations

**Cause:** `.env` points to Railway, causing slow network inserts

**Fix:** Use `DATABASE_URL` override:
```bash
DATABASE_URL=postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer \
  python etl/load_season.py --season 22
```

### Local PostgreSQL Not Running

**Check status:**
```bash
pg_isready -h localhost -p 5432
```

**Start PostgreSQL (macOS with Homebrew):**
```bash
brew services start postgresql@15
```

### Machine Key Not Found

**Symptom:** Warning about unknown machine key

**Cause:** Machine name not in `machine_variations.json`

**Fix:** Add machine alias to `machine_variations.json` and re-run

---

## Data Quality Checks

### Built-in Validations

All loading scripts include validation:
- Required fields present
- Score ranges reasonable (not negative, not absurdly high)
- IPR values in valid range (1-6)
- Round/position consistency (doubles=4 players, singles=2)
- Match state transitions valid

### Post-Load Verification

Each calculation script includes verification step:
- `calculate_percentiles.py` → Shows sample sizes and percentile examples
- `calculate_player_stats.py` → Shows top performers on specific machines
- `calculate_team_machine_picks.py` → Shows most-picked machines and win rates
- `calculate_match_points.py` → Shows sample match results and win/loss distribution

---

## Related Documentation

- **[DATA_UPDATE_STRATEGY.md](../../DATA_UPDATE_STRATEGY.md)** - Operational guide for weekly updates
- **[DATABASE_OPERATIONS.md](../DATABASE_OPERATIONS.md)** - Database management guide
- **[MNP_Data_Structure_Reference.md](../../MNP_Data_Structure_Reference.md)** - Match JSON structure
- **[etl-process.md](etl-process.md)** - Conceptual ETL documentation (historical)

---

**Maintained by:** JJC
**Last Updated:** 2026-01-14
**Status:** Production - In active use
