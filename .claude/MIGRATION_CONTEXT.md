# Database Migration Context - Resume Guide

**Created**: 2026-01-14
**Status**: In Progress - ETL loading data to Railway

---

## Problem Summary

1. Original Railway Postgres service crashed (`failed to exec pid1` error)
2. Created new Postgres service, but ETL times out when loading scores over public network
3. Solution: Load data locally, then pg_dump/pg_restore to Railway

---

## Completed Steps

### Code Fixes (All Done)
- [x] `api/models/schemas.py` line 243: Changed `state` → `neighborhood` in VenueBase
- [x] `api/routers/venues.py` line 81: Removed `as state` SQL alias
- [x] `api/routers/machines.py` line 47: Fixed null `latest_season` bug
- [x] `frontend/lib/types.ts` lines 298-314, 351-357: Updated Venue interfaces
- [x] `frontend/app/venues/[venue_key]/page.tsx` lines 146-152: Updated display logic

### Railway Setup (Done)
- [x] Created new Postgres service
- [x] Schema deployed (schema version 2.0.0 confirmed)
- [x] Pinball service variables updated to reference new Postgres

---

## Current State

**Railway Production Database** (partial data loaded):
- URL: `postgresql://postgres:sAeOqwxMBCSPUgHtHMECqPCXSijewFQB@shinkansen.proxy.rlwy.net:49342/railway`
- Internal: `postgresql://postgres:sAeOqwxMBCSPUgHtHMECqPCXSijewFQB@postgres--okr.railway.internal:5432/railway`
- Has: 565 players, 190 matches, 0 scores (ETL timed out during score insertion)

**Local Database**:
- URL: `postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer`
- Has full data from previous loads

---

## Remaining Steps

### Step 1: Clear Railway DB and Load Fresh via pg_dump

```bash
# First, drop and recreate Railway schema (clear partial data)
psql "postgresql://postgres:sAeOqwxMBCSPUgHtHMECqPCXSijewFQB@shinkansen.proxy.rlwy.net:49342/railway" << 'EOF'
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
EOF

# Run schema migration on Railway
psql "postgresql://postgres:sAeOqwxMBCSPUgHtHMECqPCXSijewFQB@shinkansen.proxy.rlwy.net:49342/railway" -f schema/migrations/001_complete_schema.sql
```

### Step 2: Load Data Locally (if not already done)

```bash
# Set local database
export DATABASE_URL="postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer"

# Load all seasons
conda activate mnp
python etl/load_season.py --season 18
python etl/load_season.py --season 19
python etl/load_season.py --season 20
python etl/load_season.py --season 21
python etl/load_season.py --season 22
python etl/calculate_percentiles.py
```

### Step 3: Dump Local → Restore to Railway

```bash
# Dump local database (data only, no schema since Railway already has it)
pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only > mnp_data_backup.sql

# Restore to Railway
psql "postgresql://postgres:sAeOqwxMBCSPUgHtHMECqPCXSijewFQB@shinkansen.proxy.rlwy.net:49342/railway" -f mnp_data_backup.sql
```

### Step 4: Verify Data

```bash
psql "postgresql://postgres:sAeOqwxMBCSPUgHtHMECqPCXSijewFQB@shinkansen.proxy.rlwy.net:49342/railway" -c "SELECT 'players' as t, COUNT(*) FROM players UNION ALL SELECT 'scores', COUNT(*) FROM scores UNION ALL SELECT 'matches', COUNT(*) FROM matches;"
```

Expected: ~939 players, ~56,000 scores, ~948 matches

### Step 5: Deploy Code Changes

```bash
cd /Users/JJC/Pinball/MNP
git add -A
git commit -m "Fix venue schema alignment and null latest_season bug"
git push
```

Railway should auto-deploy, or run `railway up`.

---

## Key Files Changed

1. `api/models/schemas.py` - VenueBase.neighborhood
2. `api/routers/venues.py` - SQL query fix
3. `api/routers/machines.py` - null latest_season fix
4. `frontend/lib/types.ts` - Venue interface changes
5. `frontend/app/venues/[venue_key]/page.tsx` - Display logic

---

## Data Loss Note

Matchplay player linkings were lost with the old database. These need to be re-linked manually through the UI after deployment.

---

## Troubleshooting

**If pg_dump fails with schema mismatch**:
Use `--data-only --disable-triggers` flags

**If restore fails with FK violations**:
Restore with `--disable-triggers` or load tables in order: machines, venues, players, teams, matches, games, scores

**If Railway connection times out**:
The public URL may be slow. Try smaller chunks or use `railway run` for internal network.
