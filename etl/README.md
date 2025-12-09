# ETL Pipeline

## Quick Start

**To load the database from scratch:**

```bash
conda activate mnp
python etl/run_full_pipeline.py --all-seasons
```

This single command runs all 6 ETL steps in the correct order for seasons 20-22.

> **Important:** Local and production databases must have the same seasons loaded.
> Production currently has seasons **20, 21, 22** only.

---

## Full Pipeline Script

The `run_full_pipeline.py` script is the **single source of truth** for the complete ETL process.

### Usage

```bash
# Load specific season(s)
python etl/run_full_pipeline.py --seasons 22
python etl/run_full_pipeline.py --seasons 20 21 22

# Load all available seasons (20-22)
python etl/run_full_pipeline.py --all-seasons

# Only recalculate aggregates (data already loaded)
python etl/run_full_pipeline.py --seasons 20 21 22 --only-aggregates

# Skip loading, just run aggregates
python etl/run_full_pipeline.py --seasons 22 --skip-load
```

---

## Pipeline Steps

The pipeline runs these scripts in order:

| Step | Script | Description | Populates Tables |
|------|--------|-------------|------------------|
| 1 | `load_season.py` | Load raw match data | `players`, `teams`, `venues`, `machines`, `matches`, `games`, `scores` |
| 2 | `calculate_percentiles.py` | Score percentile thresholds | `score_percentiles` |
| 3 | `calculate_player_stats.py` | Player machine statistics | `player_machine_stats` |
| 4 | `calculate_team_machine_picks.py` | Team machine selections | `team_machine_picks` |
| 5 | `calculate_player_totals.py` | Player season totals | `player_totals` |
| 6 | `calculate_match_points.py` | Match point calculations | `match_points` |

**Important:** Steps 2-6 are aggregate calculations that depend on step 1.

---

## When to Run

### Full Database Reset
```bash
# 1. Clear and recreate schema
psql -h localhost -U mnp_user -d mnp_analyzer -f schema/migrations/001_complete_schema.sql

# 2. Run full pipeline
python etl/run_full_pipeline.py --all-seasons
```

### Adding a New Season
```bash
# Pull latest data
cd mnp-data-archive && git pull && cd ..

# Load new season and recalculate aggregates
python etl/run_full_pipeline.py --seasons 23
```

### Recalculating Aggregates Only
If raw data is already loaded but aggregates need refreshing:
```bash
python etl/run_full_pipeline.py --only-aggregates
```

---

## Individual Scripts

You can also run scripts individually (most require `--season`):

```bash
# Load raw data for a season
python etl/load_season.py --season 22

# Calculate percentiles for a season
python etl/calculate_percentiles.py --season 22

# Calculate player stats for a season
python etl/calculate_player_stats.py --season 22

# Calculate team machine picks for a season
python etl/calculate_team_machine_picks.py --season 22

# Calculate player totals (runs for all loaded seasons)
python etl/calculate_player_totals.py

# Calculate match points for a season
python etl/calculate_match_points.py --season 22

# Update IPR data
python etl/update_ipr.py
```

---

## Directory Structure

```
etl/
├── run_full_pipeline.py      # Master script - run this!
├── config.py                 # Configuration (database, paths)
├── database.py               # Database connection manager
├── load_season.py            # Load raw match data
├── calculate_percentiles.py  # Score percentile calculations
├── calculate_player_stats.py # Player machine statistics
├── calculate_team_machine_picks.py
├── calculate_player_totals.py
├── calculate_match_points.py
├── update_ipr.py             # Update IPR ratings
├── parsers/
│   ├── machine_parser.py     # Parse machine_variations.json
│   └── match_parser.py       # Parse match JSON files
└── loaders/
    └── db_loader.py          # Insert data into database
```

---

## Verification

After running the pipeline, verify data was loaded:

```bash
psql -h localhost -U mnp_user -d mnp_analyzer -c "
SELECT 'scores' as table_name, COUNT(*) as count FROM scores
UNION ALL SELECT 'score_percentiles', COUNT(*) FROM score_percentiles
UNION ALL SELECT 'player_machine_stats', COUNT(*) FROM player_machine_stats
UNION ALL SELECT 'team_machine_picks', COUNT(*) FROM team_machine_picks
ORDER BY table_name;
"
```

Expected counts for seasons 20-22:
- `scores`: ~34,000
- `score_percentiles`: ~3,000
- `player_machine_stats`: ~18,000
- `team_machine_picks`: ~2,000

---

## Troubleshooting

### "No module named 'etl'"
Run from the project root directory:
```bash
cd /Users/test_1/Pinball/MNP/pinball
python etl/run_full_pipeline.py --all-seasons
```

### "Permission denied for table"
Grant privileges:
```bash
psql -h localhost -U mnp_user -d mnp_analyzer -c "
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mnp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mnp_user;
"
```

### Percentiles showing as NULL
The `player_machine_stats` table is empty. Run:
```bash
python etl/run_full_pipeline.py --only-aggregates
```

### Foreign key constraint violations
Usually means machines are referenced that don't exist. The `load_season.py` script should auto-create them, but check the logs for specific errors.

### Foreign key error when importing to production
```
ERROR: insert or update on table "player_machine_stats" violates foreign key constraint
Key (player_key)=(xxx) is not present in table "players"
```
**Cause:** Local database has different seasons than production. Players from seasons not in production don't exist there.

**Fix:** Ensure local and production have the same seasons. Currently both should have seasons 20-22 only.

### Data appears duplicated (e.g., 30 games instead of 10)
**Cause:** Aggregate calculation scripts were run multiple times without the pipeline clearing existing data first.

**Fix:** Use `run_full_pipeline.py` which handles clearing. Or manually truncate the affected table before re-running:
```sql
TRUNCATE TABLE player_machine_stats;
```

---

## Common Issues & Lessons Learned

1. **Always use `run_full_pipeline.py`** - Don't run individual aggregate scripts manually unless you know what you're doing. The pipeline handles clearing old data and running in the correct order.

2. **Keep local and production seasons in sync** - If you load seasons 18-22 locally but production only has 20-22, exports will fail with foreign key errors.

3. **Aggregate scripts require `--season`** - Most aggregate scripts (percentiles, player_stats, team_picks, match_points) must be run once per season with `--season N`.

4. **Verify after loading** - Always run the verification query to check row counts match expectations.

---

## Configuration

Database connection is configured via environment variables in `.env`:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mnp_analyzer
DB_USER=mnp_user
DB_PASSWORD=your_password
```

Or via `DATABASE_URL`:
```
DATABASE_URL=postgresql://mnp_user:password@localhost:5432/mnp_analyzer
```
