# MNP Database Operations Guide

**Guide for loading data, running migrations, and maintaining the production database.**

**Last Updated:** 2025-12-08

---

## Prerequisites

1. **Railway CLI installed:**
   ```bash
   npm install -g @railway/cli
   # or
   brew install railway
   ```

2. **Railway CLI authenticated:**
   ```bash
   railway login
   ```

3. **Project linked:**
   ```bash
   cd /Users/test_1/Pinball/MNP/pinball
   railway link
   # Select the "airy-acceptance" project
   ```

4. **Local database running** (for data export)

---

## Quick Reference Commands

| Task | Command |
|------|---------|
| Connect to Railway PostgreSQL | `railway connect postgres` |
| View Railway logs | `railway logs -s pinball` |
| Export local data | `pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > /tmp/mnp_data.sql` |
| Import to Railway | `railway connect postgres < /tmp/mnp_data.sql` |

---

## Adding a New Season (e.g., Season 23)

### Step 1: Load Data Locally First

1. **Update the mnp-data-archive submodule:**
   ```bash
   cd mnp-data-archive
   git pull origin main
   cd ..
   ```

2. **Run the ETL pipeline locally:**
   ```bash
   # Activate conda environment
   conda activate mnp

   # Load the new season
   python etl/load_season.py 23

   # Recalculate percentiles
   python etl/calculate_percentiles.py

   # Recalculate player stats
   python etl/calculate_player_stats.py

   # Recalculate team machine picks
   python etl/calculate_team_machine_picks.py
   ```

3. **Verify locally:**
   - Start local API: `cd api && uvicorn main:app --reload`
   - Check http://localhost:8000/seasons - should show season 23

### Step 2: Export and Import to Production

1. **Export local database:**
   ```bash
   pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > /tmp/mnp_data.sql
   ```

2. **Clear production tables (keep schema):**
   ```bash
   railway connect postgres
   ```

   Then run:
   ```sql
   TRUNCATE TABLE scores, games, matches, player_machine_stats,
                  score_percentiles, team_machine_picks, venue_machines
   RESTART IDENTITY CASCADE;
   -- Keep players, teams, machines, venues as they have references
   \q
   ```

3. **Import fresh data:**
   ```bash
   railway connect postgres < /tmp/mnp_data.sql
   ```

4. **Verify production:**
   ```bash
   curl "https://pinball-production.up.railway.app/seasons"
   ```

---

## Running Schema Migrations

When you add new migrations to `schema/migrations/`:

1. **Connect to Railway PostgreSQL:**
   ```bash
   railway connect postgres
   ```

2. **Run the new migration:**
   ```sql
   \i schema/migrations/008_your_new_migration.sql
   ```

3. **Exit:**
   ```sql
   \q
   ```

### Migration Order (for fresh setup)

Run the consolidated schema (includes all tables, indexes, and constraints):

```sql
\i schema/migrations/001_complete_schema.sql
```

This single file replaces all previous migrations (001-008) and includes:
- All tables (core + aggregate + matchplay integration)
- All indexes
- All foreign key constraints
- Unique constraint on scores to prevent duplicates
- Week constraint (0-15) for playoffs
- Team aliases table with seed data

**Note:** Old migrations are archived in `schema/migrations/archive/` for reference.

---

## Recalculating Aggregate Tables

After loading new data, recalculate aggregates:

### Locally (then export)
```bash
conda activate mnp

# Recalculate all aggregates
python etl/calculate_percentiles.py
python etl/calculate_player_stats.py
python etl/calculate_team_machine_picks.py
python etl/calculate_player_totals.py
python etl/calculate_match_points.py
```

### Production (if running ETL on Railway)
Currently not supported - run ETL locally and export/import.

---

## Full Database Reset

If you need to completely reset the production database:

1. **Export local data first:**
   ```bash
   pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > /tmp/mnp_data.sql
   ```

2. **Connect to Railway PostgreSQL:**
   ```bash
   railway connect postgres
   ```

3. **Drop and recreate schema:**
   ```sql
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   \q
   ```

4. **Run consolidated schema:**
   ```bash
   railway connect postgres < schema/migrations/001_complete_schema.sql
   ```

5. **Import data:**
   ```bash
   railway connect postgres < /tmp/mnp_data.sql
   ```

6. **Verify:**
   ```bash
   curl "https://pinball-production.up.railway.app/seasons"
   ```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'api'"
- Railway is deploying from wrong directory
- Fix: Clear Root Directory in Railway settings (deploy from repo root)

### 502 errors after deployment
- Check Railway logs: `railway logs -s pinball`
- Common causes:
  - DATABASE_URL not set → Link PostgreSQL to FastAPI service
  - Port mismatch → Set Target Port to 8080
  - Missing tables → Run migrations

### "relation does not exist" errors
- Schema not created → Run migrations in Railway PostgreSQL

### Data import errors
- Duplicate key errors are usually OK (existing data)
- Constraint violations → Skip 003_constraints.sql migration

### API works but frontend shows errors
- Check NEXT_PUBLIC_API_URL in Vercel
- Must point to Railway URL: `https://pinball-production.up.railway.app`
- Redeploy Vercel after changing env vars

---

## Database Statistics

Check current data counts:
```bash
railway connect postgres
```

```sql
SELECT 'players' as table_name, COUNT(*) as count FROM players
UNION ALL SELECT 'teams', COUNT(*) FROM teams
UNION ALL SELECT 'matches', COUNT(*) FROM matches
UNION ALL SELECT 'games', COUNT(*) FROM games
UNION ALL SELECT 'scores', COUNT(*) FROM scores
UNION ALL SELECT 'machines', COUNT(*) FROM machines
UNION ALL SELECT 'venues', COUNT(*) FROM venues;
```

---

## Backup and Restore

### Railway Automatic Backups
- Railway automatically backs up PostgreSQL daily
- Access via Railway Dashboard → PostgreSQL service → Backups

### Manual Backup
```bash
# Get DATABASE_URL from Railway
railway variables

# Use pg_dump with the URL
pg_dump "postgresql://..." > backup_$(date +%Y%m%d).sql
```

---

## Matchups Page and Season Transitions

The **Matchups** page (`/matchups`) provides match analysis for upcoming games. It automatically handles season transitions:

### How It Works

1. **Season Status Detection:**
   - The API endpoint `/seasons/{season}/status` determines if a season is:
     - `upcoming`: Season hasn't started yet (before first week's date)
     - `in_progress`: Season is currently active (between first and last week dates)
     - `completed`: Season has ended (after last week's date)

2. **User Experience:**
   - **During season:** Users can select matches and analyze team performance
   - **Off-season:** Users see a friendly message: "Season X has completed. Check back for Season X+1!"
   - Users can still browse completed match data even when the season is over

### When a New Season Starts

The matchups page will automatically work with the new season once the data is loaded:

1. **Update the mnp-data-archive submodule** with new season data:
   ```bash
   cd mnp-data-archive
   git pull origin main
   cd ..
   ```

2. **Run the ETL pipeline** for the new season:
   ```bash
   python etl/run_full_pipeline.py --seasons 23
   ```

3. **Export and import to production** (see "Adding a New Season" above)

4. **The matchups page will automatically:**
   - Detect the new season based on database data
   - Show the correct status (upcoming/in_progress) based on dates in `season.json`
   - Display matches for the new season

### Season Data Requirements

For the matchups page to work properly, you need:

- `mnp-data-archive/season-{N}/season.json` - Contains schedule with week dates
- `mnp-data-archive/season-{N}/matches/*.json` - Match data files (for machine lineups)
- Database tables populated via ETL:
  - `teams` - Team information for the season
  - `players` - Player data
  - `scores` - Historical score data for predictions

### Testing Season Status

You can test the season status endpoint directly:
```bash
curl "https://pinball-production.up.railway.app/seasons/22/status"
```

Expected response:
```json
{
  "season": 22,
  "status": "completed",
  "message": "Season 22 has completed. Check back for Season 23!",
  "first_week_date": "2025-09-08",
  "last_week_date": "2025-12-08",
  "total_matches": 191,
  "upcoming_matches": 0
}
```

---

**Last Updated:** 2025-12-12
