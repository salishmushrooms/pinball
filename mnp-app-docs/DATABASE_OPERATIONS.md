# MNP Database Operations Guide

**Guide for loading data, running migrations, and maintaining the production database.**

**Last Updated:** 2026-01-26

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
   # Use --browserless flag if needed: railway login --browserless
   ```

3. **Project linked:**
   ```bash
   cd /Users/JJC/Pinball/MNP
   railway link
   # Select the "airy-acceptance" project
   ```

4. **Local database running** (for data export)

5. **Conda environment activated:**
   ```bash
   conda activate mnp
   ```

---

## Quick Reference Commands

| Task | Command |
|------|---------|
| Connect to Railway PostgreSQL | `railway connect "Postgres--OkR"` |
| View Railway logs | `railway logs -s pinball` |
| Export local data | `pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > /tmp/mnp_data.sql` |
| Import to Railway | `railway connect "Postgres--OkR" < /tmp/mnp_data.sql` |
| Run migration on production | `psql "$DATABASE_PUBLIC_URL" -f schema/migrations/006_migration.sql` |
| Run ETL script on production | `DATABASE_URL="$DATABASE_PUBLIC_URL" python etl/script.py` |

> **Note:** The PostgreSQL service is named `Postgres--OkR` in Railway. Use this exact name (with quotes) for all `railway connect` commands.

---

## Environment Variables for Database Access

The `.env` file contains database connection URLs:

```bash
# Local database (default for all ETL scripts)
LOCAL_DATABASE_URL=postgresql://mnp_user:password@localhost:5432/mnp_analyzer

# Production database (Railway) - stored but NOT used by default
# This prevents accidental production writes
DATABASE_PUBLIC_URL=postgresql://postgres:PASSWORD@shinkansen.proxy.rlwy.net:49342/railway
```

**ETL scripts use this priority order** (in `etl/config.py`):
1. `LOCAL_DATABASE_URL` (if set)
2. `DATABASE_URL` (fallback)
3. Hardcoded local default

**To run ETL against production**, explicitly override `DATABASE_URL`:
```bash
DATABASE_URL="$DATABASE_PUBLIC_URL" python etl/your_script.py --args
```

This pattern makes production writes intentional, not accidental.

---

## Adding a New Season (e.g., Season 23)

### Step 1: Load Data Locally First

1. **Update the mnp-data-archive submodule:**
   ```bash
   cd mnp-data-archive
   git pull origin main
   cd ..
   ```

2. **For a season WITH match data (completed/in-progress season):**
   ```bash
   conda activate mnp

   # Load the season data
   python etl/load_season.py --season 23

   # Recalculate aggregates for this season
   python etl/calculate_percentiles.py --season 23
   python etl/calculate_player_stats.py --season 23
   python etl/calculate_team_machine_picks.py --season 23
   python etl/calculate_match_points.py --season 23

   # Recalculate cross-season totals
   python etl/calculate_player_totals.py
   ```

3. **For a PRESEASON (no matches yet, only rosters):**
   ```bash
   conda activate mnp

   # Load preseason metadata (teams, players, venues, scheduled matches)
   python etl/load_preseason.py --season 23
   ```

   > **Note:** The preseason loader will reuse existing player keys when players already exist in the database, preventing duplicate player entries.

4. **Verify locally:**
   ```bash
   # Start local API
   uvicorn api.main:app --reload --port 8000

   # In another terminal, check data
   curl http://localhost:8000/players | jq '.total'
   curl http://localhost:8000/seasons
   ```

### Step 2: Export and Import to Production

**Recommended: Full Database Reset** (cleanest approach)

1. **Export local database:**
   ```bash
   pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > /tmp/mnp_data.sql
   ```

2. **Reset production schema:**
   ```bash
   railway connect Postgres--OkR
   ```
   ```sql
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   \q
   ```

3. **Import schema then data:**
   ```bash
   railway connect Postgres--OkR < schema/migrations/001_complete_schema.sql
   railway connect Postgres--OkR < /tmp/mnp_data.sql
   ```

4. **Verify production:**
   ```bash
   railway connect Postgres--OkR
   ```
   ```sql
   SELECT COUNT(*) FROM players;
   SELECT COUNT(*) FROM scores;
   \q
   ```

> **Note:** Some duplicate key errors on `schema_version` and `team_aliases` are expected and harmless - these are seed data already inserted by the schema.

---

## Running Schema Migrations

When you add new migrations to `schema/migrations/`:

### Option 1: Using railway connect (interactive)
```bash
railway connect "Postgres--OkR"
```
Then in the psql prompt:
```sql
\i schema/migrations/006_your_new_migration.sql
\q
```

### Option 2: Using psql with DATABASE_PUBLIC_URL (non-interactive)
```bash
psql "$DATABASE_PUBLIC_URL" -f schema/migrations/006_your_new_migration.sql
```

### Option 3: Inline SQL for simple migrations
```bash
railway run psql -c "ALTER TABLE matches ADD COLUMN IF NOT EXISTS machines JSONB;"
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

# Recalculate aggregates for specific seasons (run for each loaded season)
python etl/calculate_percentiles.py --season 18
python etl/calculate_percentiles.py --season 19
# ... repeat for each season ...

python etl/calculate_player_stats.py --season 18
python etl/calculate_player_stats.py --season 19
# ... repeat for each season ...

python etl/calculate_team_machine_picks.py --season 18
# ... repeat for each season ...

python etl/calculate_match_points.py --season 18
# ... repeat for each season ...

# Cross-season totals (no season flag needed)
python etl/calculate_player_totals.py
```

### Using the Pipeline (easier)
```bash
# Load and calculate for multiple seasons at once
python etl/run_full_pipeline.py --seasons 18 19 20 21 22

# Or just recalculate aggregates (skip loading)
python etl/run_full_pipeline.py --seasons 18 19 20 21 22 --skip-load

# Include Matchplay.events data refresh (requires MATCHPLAY_API_TOKEN)
python etl/run_full_pipeline.py --seasons 22 --refresh-matchplay

# Or run Matchplay refresh standalone
python etl/refresh_matchplay_data.py
```

### Running ETL Directly Against Production

You can run ETL scripts directly against production by overriding `DATABASE_URL`:

```bash
conda activate mnp

# Run a single script against production
DATABASE_URL="$DATABASE_PUBLIC_URL" python etl/calculate_team_machine_picks.py --season 22

# Run backfill scripts against production
DATABASE_URL="$DATABASE_PUBLIC_URL" python etl/backfill_match_machines.py --recalculate

# Run multiple seasons
for season in 18 19 20 21 22; do
  DATABASE_URL="$DATABASE_PUBLIC_URL" python etl/calculate_team_machine_picks.py --season $season
done
```

**When to use direct ETL vs export/import:**
| Scenario | Approach |
|----------|----------|
| New migration + backfill script | Run migration, then `DATABASE_URL="$DATABASE_PUBLIC_URL" python etl/script.py` |
| Recalculating aggregates only | `DATABASE_URL="$DATABASE_PUBLIC_URL" python etl/calculate_*.py` |
| Loading new season data | Export/import (safer, can verify locally first) |
| Full database reset | Export/import |

---

## Full Database Reset

If you need to completely reset the production database:

> **CRITICAL:** Before any database reset, you MUST backup production-only user data.
> See [Preserving Matchplay Account Links](#preserving-matchplay-account-links) below.

### Standard Reset Procedure

1. **Backup matchplay account links FIRST:**
   ```bash
   # On production - backup user-created account links
   DATABASE_URL="$DATABASE_PUBLIC_URL" python etl/backup_matchplay_links.py --backup
   ```
   This creates a timestamped backup in `backups/matchplay_links_YYYYMMDD_HHMMSS.json`

2. **Export local data:**
   ```bash
   pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > /tmp/mnp_data.sql
   ```

3. **Connect to Railway PostgreSQL:**
   ```bash
   railway connect Postgres--OkR
   ```

4. **Drop and recreate schema:**
   ```sql
   DROP SCHEMA public CASCADE;
   CREATE SCHEMA public;
   \q
   ```

5. **Run consolidated schema:**
   ```bash
   railway connect Postgres--OkR < schema/migrations/001_complete_schema.sql
   ```

6. **Import data:**
   ```bash
   railway connect Postgres--OkR < /tmp/mnp_data.sql
   ```

7. **Restore matchplay links from backup:**
   ```bash
   DATABASE_URL="$DATABASE_PUBLIC_URL" python etl/backup_matchplay_links.py --restore --input backups/matchplay_links_YYYYMMDD_HHMMSS.json
   ```

8. **Verify matchplay links restored:**
   ```bash
   DATABASE_URL="$DATABASE_PUBLIC_URL" python etl/backup_matchplay_links.py --verify
   ```

9. **Verify production:**
   ```bash
   curl "https://your-api.railway.app/seasons"
   ```

---

## Preserving Matchplay Account Links

**Why This Matters:**
Production users can link their MNP player profiles to their Matchplay.events accounts. These links are stored in `matchplay_player_mappings` and are **user-created data that cannot be recreated from source files**. If you rebuild the database without preserving these links, users will need to re-link their accounts.

### What Gets Preserved

| Table | Contents | Critical? |
|-------|----------|-----------|
| `matchplay_player_mappings` | User account links | **YES** - Cannot be recreated |
| `matchplay_ratings` | Cached ratings | No - Can be re-fetched |
| `matchplay_player_machine_stats` | Cached stats | No - Can be re-fetched |
| `matchplay_arena_mappings` | Machine name mappings | Minor - Useful to preserve |

### Backup Commands

```bash
# Backup matchplay links (creates timestamped file)
python etl/backup_matchplay_links.py --backup

# Backup to specific file
python etl/backup_matchplay_links.py --backup --output my_backup.json

# Run against production database
DATABASE_URL="$DATABASE_PUBLIC_URL" python etl/backup_matchplay_links.py --backup
```

### Restore Commands

```bash
# Restore from backup (idempotent - safe to run multiple times)
python etl/backup_matchplay_links.py --restore --input backups/matchplay_links_20260126_120000.json

# Dry run - validate without making changes
python etl/backup_matchplay_links.py --restore --input backup.json --dry-run

# Run against production database
DATABASE_URL="$DATABASE_PUBLIC_URL" python etl/backup_matchplay_links.py --restore --input backups/matchplay_links_20260126_120000.json
```

### Verification Commands

```bash
# Verify links exist in database (run before rebuild)
python etl/backup_matchplay_links.py --verify

# Verify a backup file is valid
python etl/backup_matchplay_links.py --verify-backup --input backups/matchplay_links_20260126_120000.json

# List all available backups
python etl/backup_matchplay_links.py --list
```

### Pre-Rebuild Checklist

Before any database rebuild, ensure:

- [ ] Run `--verify` on production to check for existing links
- [ ] Run `--backup` on production to create backup file
- [ ] Run `--verify-backup` on the backup file to confirm it's valid
- [ ] Store backup file safely (it's in `backups/` directory, not committed to git)

### Post-Rebuild Checklist

After rebuilding the database:

- [ ] Run `--restore` with the backup file
- [ ] Run `--verify` to confirm links were restored
- [ ] Test a linked player in the UI to confirm functionality

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
- Must point to Railway URL: `https://your-api.railway.app`
- Redeploy Vercel after changing env vars

---

## Database Statistics

Check current data counts:
```bash
railway connect Postgres--OkR
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
curl "https://your-api.railway.app/seasons/22/status"
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

**Last Updated:** 2026-01-26
