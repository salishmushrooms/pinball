# MNP Data Update Strategy

**Last Updated:** 2026-01-14
**Purpose:** Guide for updating database when new match data becomes available

---

## Overview

This document outlines the strategy for updating the MNP database across three scenarios:

1. **Preseason Setup** - Loading scheduled matches, teams, players, and venues before a season starts
2. **Weekly Match Updates** - Loading completed match data during an active season
3. **Historical Season Loading** - One-time backfill of complete seasons

### Architecture Note

The production database runs on Railway (remote). Running ETL scripts directly against Railway is **slow** due to network latency on individual INSERT statements. The recommended approach is:

1. Run all ETL locally (fast)
2. Export local database
3. Bulk import to Railway (fast)

---

## Environment Setup

### Database URLs

Your `.env` file likely points to Railway:
```
DATABASE_URL=postgresql://postgres:...@shinkansen.proxy.rlwy.net:49342/railway
```

For local ETL, override with:
```bash
DATABASE_URL=postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer
```

### Local Database Prefix

All ETL commands should use this prefix for local execution:
```bash
LOCAL_DB="DATABASE_URL=postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer"
```

---

## Data Pipeline Order

The ETL pipeline has **dependencies** - some steps must happen before others:

```
1. Load Raw Data (matches, scores, venues, etc.)
   ↓
2. Calculate Percentiles (requires scores to exist)
   ↓
3. Calculate Player Machine Stats (requires percentiles to exist)
```

**Critical:** You **cannot** calculate player stats before percentiles, because player stats include percentile rankings!

---

## Preseason Setup (Before Season Starts)

Use this workflow when a new season's schedule is posted but matches haven't been played yet.

### When to Use

- Season schedule has been published
- Teams, rosters, and venues are finalized
- No match results exist yet

### Data Requirements

Ensure these files exist in `mnp-data-archive/season-{N}/`:
- `matches.csv` - Schedule (week, date, away_team, home_team, venue)
- `teams.csv` - Team definitions (team_key, venue_key, team_name)
- `rosters.csv` - Player rosters (player_name, team_key, role)
- `venues.csv` - Venue definitions (venue_key, venue_name)

### Preseason Commands

```bash
# 1. Activate environment
conda activate mnp

# 2. Pull latest data from archive
cd mnp-data-archive && git pull origin main && cd ..

# 3. Ensure local PostgreSQL is running
pg_isready -h localhost -p 5432

# 4. Load preseason data locally (fast)
DATABASE_URL=postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer \
  python etl/load_preseason.py --season 23

# 5. Export local database
pg_dump -h localhost -U mnp_user -d mnp_analyzer \
  --data-only --no-owner --no-acl > /tmp/mnp_data.sql

# 6. Import to Railway (bulk - fast)
psql "postgresql://postgres:YOUR_PASSWORD@shinkansen.proxy.rlwy.net:49342/railway" \
  < /tmp/mnp_data.sql
```

### What Preseason Loads

| Data | Source | Notes |
|------|--------|-------|
| Machines | `machine_variations.json` | Canonical machine names + aliases |
| Venues | `venues.csv` + `venues.json` | Venue keys, names, addresses |
| Teams | `teams.csv` | Team keys, names, home venues |
| Players | `rosters.csv` | Player keys and names |
| Matches | `matches.csv` | Scheduled matches (state='scheduled') |

### Verify Preseason Load

```bash
# Check production API
curl "https://your-api.railway.app/seasons/23/status"

# Expected response:
{
  "season": 23,
  "status": "upcoming",
  "message": "Season 23 starts on February 03, 2025",
  "total_matches": 100,
  "upcoming_matches": 100
}
```

---

## Weekly Match Updates (During Season)

Use this workflow after Monday night matches complete and JSON files are added to the archive.

### When to Update

- **Frequency:** Weekly (after Monday night matches)
- **Timing:** Tuesday morning after match data is verified and committed
- **Duration:** ~1-2 minutes total

### What Gets Updated Weekly vs End-of-Season

| Data | Weekly? | Why |
|------|---------|-----|
| Raw scores/games/matches | ✅ Yes | Core match data for all lookups |
| Team machine picks | ✅ Yes | Powers matchup predictions ("Team X picks this 40%") |
| Match points | ✅ Yes | Powers standings and results |
| Score percentiles | ❌ No | Incomplete mid-season; wait for season end |
| Player machine stats | ❌ No | Depends on percentiles; wait for season end |
| Player totals | ❌ No | Cross-season aggregates; minimal mid-season value |

**Rationale:** Percentiles and player stats are most valuable with complete season data. Mid-season percentiles have limited analytical value since the distribution is incomplete. Team pick patterns and match points, however, are directly useful for matchup analysis and standings.

### Weekly Update Commands

```bash
# 1. Activate environment
conda activate mnp

# 2. Pull latest match data
cd mnp-data-archive && git pull origin main && cd ..

# 3. Ensure local PostgreSQL is running
pg_isready -h localhost -p 5432

# 4. Load new match data locally (skip most aggregations)
python etl/update_season.py --season 23 --skip-aggregations

# 5. Calculate aggregates needed for matchup analysis
python etl/calculate_team_machine_picks.py --season 23
python etl/calculate_match_points.py --season 23

# 6. Export local database
pg_dump -h localhost -U mnp_user -d mnp_analyzer \
  --data-only --no-owner --no-acl > /tmp/mnp_data.sql

# 7. Import to Railway
railway connect Postgres--OkR < /tmp/mnp_data.sql
```

### Weekly Update Script

Create `scripts/weekly_update.sh`:

```bash
#!/bin/bash
# Weekly season data update script (optimized for mid-season)

SEASON=${1:-23}

echo "=== MNP Season $SEASON Weekly Update ==="
echo ""

# Check local postgres
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "ERROR: Local PostgreSQL is not running"
    exit 1
fi

# Pull latest data
echo "1. Pulling latest data..."
cd mnp-data-archive && git pull origin main && cd ..

# Load match data (skip aggregations - we'll run specific ones)
echo "2. Loading match data..."
python etl/update_season.py --season $SEASON --skip-aggregations

# Calculate team picks (powers matchup predictions)
echo "3. Calculating team machine picks..."
python etl/calculate_team_machine_picks.py --season $SEASON

# Calculate match points (powers standings)
echo "4. Calculating match points..."
python etl/calculate_match_points.py --season $SEASON

# Export
echo "5. Exporting database..."
pg_dump -h localhost -U mnp_user -d mnp_analyzer \
  --data-only --no-owner --no-acl > /tmp/mnp_data.sql

# Import to Railway
echo "6. Importing to Railway..."
railway connect Postgres--OkR < /tmp/mnp_data.sql

echo ""
echo "=== Weekly Update Complete ==="
echo "Verify at: https://your-api.railway.app/seasons/$SEASON/status"
echo ""
echo "Note: Percentiles and player stats are NOT recalculated weekly."
echo "Run full pipeline at end of season for complete stats."
```

Usage:
```bash
chmod +x scripts/weekly_update.sh
./scripts/weekly_update.sh 23
```

### Performance Expectations

| Step | Local Time | Notes |
|------|------------|-------|
| Load matches | ~10-20s | Only loads NEW matches (skips duplicates) |
| Calculate team picks | ~5-10s | Single season |
| Calculate match points | ~5s | Single season |
| pg_dump | ~5s | Full database export |
| Railway import | ~30-60s | Bulk network transfer |
| **Total** | **~1-2 min** | Faster than full pipeline |

### Frontend Impact During Season

With this weekly approach:
- ✅ **Matchup page**: Team pick patterns current, raw scores current
- ✅ **Standings**: Match points current
- ⚠️ **Player detail**: Machine stats summary may show stale percentile rankings
- ⚠️ **Machine detail**: Percentile thresholds based on previous seasons only
- ⚠️ **Matchup page**: Player confidence intervals based on previous seasons

---

## End-of-Season Full Recalculation

When a season is complete, run the full pipeline to generate all aggregations including percentiles and player stats.

### When to Run

- After the final match of the season
- When you need complete statistical analysis for the season
- Before archiving season data

### End-of-Season Commands

```bash
# 1. Ensure all match data is loaded
cd mnp-data-archive && git pull origin main && cd ..

# 2. Run full pipeline (includes all aggregations)
python etl/update_season.py --season 23

# 3. Export and sync to production
pg_dump -h localhost -U mnp_user -d mnp_analyzer \
  --data-only --no-owner --no-acl > /tmp/mnp_data.sql
railway connect Postgres--OkR < /tmp/mnp_data.sql
```

### What Gets Calculated

| Aggregation | Purpose |
|-------------|---------|
| `calculate_percentiles.py` | Score distribution thresholds (25th, 50th, 75th, 90th, 95th) per machine/venue/season |
| `calculate_player_stats.py` | Player performance aggregates with percentile rankings |
| `calculate_team_machine_picks.py` | Team machine selection patterns |
| `calculate_match_points.py` | Match point totals for standings |
| `calculate_player_totals.py` | Cross-season player aggregates |

### Performance Expectations

| Step | Time | Notes |
|------|------|-------|
| Load season | ~10-20s | Upserts existing data |
| All aggregations | ~60-90s | Full recalculation |
| Export + import | ~60s | Bulk transfer |
| **Total** | **~3 min** | Complete refresh |

---

## Historical Season Loading (One-Time)

Use this workflow when adding a complete historical season or rebuilding the database.

### Full Season Backfill

```bash
# Load a single historical season with full aggregations
python etl/update_season.py --season 21
```

### Batch Loading Multiple Seasons

```bash
# Use the full pipeline runner for multiple seasons
python etl/run_full_pipeline.py --seasons 20 21 22 23

# Or load all available seasons
python etl/run_full_pipeline.py --all-seasons
```

Then export and import to Railway:
```bash
pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > /tmp/mnp_data.sql
railway connect Postgres--OkR < /tmp/mnp_data.sql
```

---

## Data Files Location

### Source Data (Git Submodule)
```
mnp-data-archive/
├── season-18/matches/*.json    # Historical matches
├── season-19/matches/*.json
├── season-20/matches/*.json
├── season-21/matches/*.json
├── season-22/matches/*.json
├── season-23/
│   ├── matches.csv             # Schedule
│   ├── teams.csv               # Team definitions
│   ├── rosters.csv             # Player rosters
│   ├── venues.csv              # Venue definitions
│   └── matches/*.json          # Completed match data (added weekly)
├── machine_variations.json     # Machine name mappings
├── venues.json                 # Venue metadata
└── IPR.csv                     # Player IPR ratings
```

### Database Tables
```
PostgreSQL Database: mnp_analyzer (local) / railway (production)
├── matches                     # Match metadata (state: scheduled/complete)
├── games                       # Individual games within matches
├── scores                      # Individual player scores
├── score_percentiles           # Percentile thresholds per machine/season
├── player_machine_stats        # Aggregated player stats
├── teams                       # Team definitions per season
├── players                     # Player definitions
├── venues                      # Venue definitions
└── machines                    # Machine definitions + aliases
```

---

## Current Data Status

### Loaded Seasons (Production)

| Season | Status | Matches | Scores | Notes |
|--------|--------|---------|--------|-------|
| 18 | Complete | ~190 | ~11,300 | Historical |
| 19 | Complete | ~190 | ~11,300 | Historical |
| 20 | Complete | ~190 | ~11,400 | Historical |
| 21 | Complete | ~190 | ~11,340 | Historical |
| 22 | Complete | ~191 | ~11,000 | Recently completed |
| 23 | Upcoming | ~100 | 0 | Scheduled matches only |

---

## Important Notes

### Why Local + Export/Import?

Running ETL directly against Railway is **10-100x slower** than local:
- Individual INSERTs over network: ~50-100ms each
- 1000 scores = 50-100 seconds just for inserts
- Local inserts: <1ms each
- Bulk import via psql: transfers entire dump in seconds

### Percentile Dependencies

**Player stats MUST be recalculated after percentiles!**

`player_machine_stats` includes percentile rankings calculated from `score_percentiles`. If you calculate player stats before percentiles, percentile fields will be NULL.

**Correct Order:**
```bash
# CORRECT
python etl/calculate_percentiles.py
python etl/calculate_player_stats.py

# WRONG - percentiles will be NULL in player stats
python etl/calculate_player_stats.py
python etl/calculate_percentiles.py
```

### ON CONFLICT Behavior

ETL scripts use upsert logic (INSERT ... ON CONFLICT DO UPDATE):
- Existing records get updated if changed
- New records get inserted
- No duplicates created
- Safe to run multiple times

### Match State Transitions

- `scheduled` - Match is planned but not yet played (from preseason load)
- `complete` - Match has been played (from load_season.py with JSON data)

The matchups page filters to show only `scheduled` matches for the current season.

---

## Troubleshooting

### ETL Script Hanging

**Symptom:** Script appears frozen during database operations

**Cause:** `.env` points to Railway, causing slow network inserts

**Fix:** Use DATABASE_URL override:
```bash
DATABASE_URL=postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer \
  python etl/load_preseason.py --season 23
```

### Local PostgreSQL Not Running

```bash
# Check status
pg_isready -h localhost -p 5432

# Start PostgreSQL (macOS with Homebrew)
brew services start postgresql@15
```

### Railway Import Errors

**Duplicate key errors:** Usually OK - existing data being re-imported

**Connection refused:** Check Railway database URL is correct

**Permission denied:** Ensure using correct credentials from Railway dashboard

### NULL Percentiles in Player Stats

**Cause:** Player stats calculated before percentiles

**Fix:** Recalculate in correct order:
```bash
DATABASE_URL=$LOCAL_DB python etl/calculate_percentiles.py
DATABASE_URL=$LOCAL_DB python etl/calculate_player_stats.py
# Then export and import to Railway
```

---

## Quick Reference

### Preseason (New Season Setup)
```bash
python etl/load_preseason.py --season 23
pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > /tmp/mnp_data.sql
railway connect Postgres--OkR < /tmp/mnp_data.sql
```

### Weekly Update (During Season)
```bash
cd mnp-data-archive && git pull && cd ..
python etl/update_season.py --season 23 --skip-aggregations
python etl/calculate_team_machine_picks.py --season 23
python etl/calculate_match_points.py --season 23
pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > /tmp/mnp_data.sql
railway connect Postgres--OkR < /tmp/mnp_data.sql
```

### End-of-Season (Full Recalculation)
```bash
python etl/update_season.py --season 23
pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > /tmp/mnp_data.sql
railway connect Postgres--OkR < /tmp/mnp_data.sql
```

### Verify Production
```bash
curl "https://your-api.railway.app/seasons/23/status"
curl "https://your-api.railway.app/seasons/23/matches"
```

---

**Current Season:** 23 (Upcoming - starts February 2025)
**Last Update:** 2026-01-18
