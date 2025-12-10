# MNP Database Update Guide

This guide covers how to update the database when new match data becomes available.

**Last Updated:** 2025-12-10

---

## Quick Start (Most Common Case)

When new match data is available (e.g., week 14 of season 22):

```bash
# 1. Pull latest data from mnp-data-archive
cd mnp-data-archive && git pull origin main && cd ..

# 2. Commit the submodule update
git add mnp-data-archive && git commit -m "Update mnp-data-archive submodule"

# 3. Activate environment and update database
conda activate mnp
export PYTHONPATH=/Users/JJC/Pinball/MNP

# 4. Run the update script
python etl/update_season.py --season 22
```

That's it! The script handles loading data and recalculating all aggregations.

---

## The update_season.py Script

This script orchestrates the full update process:
1. Loads/upserts season data (new records added, existing unchanged)
2. Calculates percentiles, player stats, team picks, match points
3. Recalculates cross-season player totals
4. Optionally syncs to production

### Usage Examples

```bash
# Update a single season
python etl/update_season.py --season 22

# Update multiple seasons
python etl/update_season.py --season 20 21 22

# Update and sync to production
python etl/update_season.py --season 22 --sync-production

# Just load data without recalculating aggregations
python etl/update_season.py --season 22 --skip-aggregations

# Verbose output for debugging
python etl/update_season.py --season 22 --verbose
```

### What It Does

The script runs these ETL scripts in order:
1. `load_season.py` - Load matches, teams, players, venues, games, scores
2. `calculate_percentiles.py` - Score distribution thresholds per machine
3. `calculate_player_stats.py` - Player performance aggregates
4. `calculate_team_machine_picks.py` - Team machine selection patterns
5. `calculate_match_points.py` - Match point totals
6. `calculate_player_totals.py` - Cross-season player game counts

All scripts use upsert logic (`INSERT ... ON CONFLICT DO UPDATE`), making them safe to re-run.

---

## Prerequisites

### Conda Environment
```bash
conda activate mnp
```

### PYTHONPATH
```bash
export PYTHONPATH=/Users/JJC/Pinball/MNP
```

Or prefix each command:
```bash
PYTHONPATH=/Users/JJC/Pinball/MNP python etl/...
```

### PostgreSQL Running
```bash
psql -d mnp_analyzer -c "SELECT 1"
```

---

## Updating Another Machine

If you work from multiple computers and need to sync database state:

### Option A: Run the Same Update (Recommended)

Since `update_season.py` is idempotent, just run it on each machine:

```bash
# On any machine, pull repo and data, then run:
git pull
git submodule update --init --remote
conda activate mnp
export PYTHONPATH=/Users/JJC/Pinball/MNP
python etl/update_season.py --season 22
```

Both machines will end up with identical database state.

### Option B: Export/Import Database Dump

If you need an exact copy:

```bash
# On source machine - export
pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > mnp_backup.sql

# Transfer file to other machine, then import
psql -h localhost -U mnp_user -d mnp_analyzer < mnp_backup.sql
```

---

## Syncing to Production (Railway)

### Prerequisites

1. Railway CLI installed and authenticated:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. Project linked:
   ```bash
   railway link
   # Select the pinball project
   ```

### Sync Command

```bash
python etl/update_season.py --season 22 --sync-production
```

This will:
1. Export local database to a temp SQL file
2. Truncate production tables (keeping schema)
3. Import data to production
4. Clean up temp file

### Manual Sync (If Needed)

```bash
# Export local
pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > /tmp/mnp_data.sql

# Import to Railway
railway connect postgres < /tmp/mnp_data.sql
```

---

## Full Database Rebuild

For a complete rebuild from scratch:

```bash
# 1. Drop and recreate database
psql -d postgres -c "DROP DATABASE IF EXISTS mnp_analyzer;"
psql -d postgres -c "CREATE DATABASE mnp_analyzer OWNER mnp_user;"

# 2. Create schema
psql -d mnp_analyzer -f schema/migrations/001_complete_schema.sql

# 3. Activate environment
conda activate mnp
export PYTHONPATH=/Users/JJC/Pinball/MNP

# 4. Load all seasons (18-19 loaded but excluded from aggregations)
python etl/update_season.py --season 18 19 --skip-aggregations
python etl/update_season.py --season 20 21 22
```

---

## Season Data Notes

- **Seasons 18-19**: Loaded into database but excluded from aggregation calculations (older data less useful for predictions)
- **Seasons 20-22**: Full data with all aggregations calculated
- **New seasons**: Add to the script's `AGGREGATION_SEASONS` list in `update_season.py` if you want aggregations calculated

---

## Available Seasons

Data is located at:
- `mnp-data-archive/season-18/`
- `mnp-data-archive/season-19/`
- `mnp-data-archive/season-20/`
- `mnp-data-archive/season-21/`
- `mnp-data-archive/season-22/`

---

## Troubleshooting

### ModuleNotFoundError: No module named 'etl'
```bash
export PYTHONPATH=/Users/JJC/Pinball/MNP
```

### Cannot connect to database
Check PostgreSQL is running and `.env` has correct connection details.

### Submodule update fails
```bash
git submodule sync
git submodule update --init --force
```

### Railway sync fails
```bash
# Check authentication
railway whoami

# Re-authenticate if needed
railway login
```

### Duplicate key errors during import
These are usually OK - it means the data already exists. The upsert logic handles this gracefully.

---

## Individual ETL Scripts

If you need to run scripts individually:

```bash
# Load season data only
python etl/load_season.py --season 22

# Calculate specific aggregations
python etl/calculate_percentiles.py --season 22
python etl/calculate_player_stats.py --season 22
python etl/calculate_team_machine_picks.py --season 22
python etl/calculate_match_points.py --season 22

# Cross-season totals (run after all seasons loaded)
python etl/calculate_player_totals.py

# Update IPR only (from IPR.csv)
python etl/update_ipr.py
```
