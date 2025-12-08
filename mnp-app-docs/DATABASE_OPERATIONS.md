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

Run these in order, **skipping 003_constraints.sql** (has score limit that blocks some data):

```sql
\i schema/migrations/001_initial_schema.sql
\i schema/migrations/002_indexes.sql
\i schema/migrations/002_allow_week_zero.sql
\i schema/migrations/002_remove_mn_state.sql
\i schema/migrations/004_add_substitute_field.sql
\i schema/migrations/005_performance_indexes.sql
\i schema/migrations/006_team_aliases.sql
\i schema/migrations/007_matchplay_integration.sql
```

**Note:** `003_constraints.sql` adds a check `score <= 10000000000` which blocks some AFM scores. Skip it unless you need strict constraints.

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

1. **Connect to Railway PostgreSQL:**
   ```bash
   railway connect postgres
   ```

2. **Drop and recreate schema:**
   ```sql
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   ```

3. **Run migrations (skip 003):**
   ```sql
   \i schema/migrations/001_initial_schema.sql
   \i schema/migrations/002_indexes.sql
   \i schema/migrations/002_allow_week_zero.sql
   \i schema/migrations/002_remove_mn_state.sql
   \i schema/migrations/004_add_substitute_field.sql
   \i schema/migrations/005_performance_indexes.sql
   \i schema/migrations/006_team_aliases.sql
   \i schema/migrations/007_matchplay_integration.sql
   \q
   ```

4. **Import data:**
   ```bash
   railway connect postgres < /tmp/mnp_data.sql
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

**Last Updated:** 2025-12-08
