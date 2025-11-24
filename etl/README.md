# ETL Pipeline - Quick Reference

## Overview

The ETL (Extract, Transform, Load) pipeline loads MNP match data from JSON files into PostgreSQL.

## Structure

```
etl/
├── config.py              # Configuration (database, paths)
├── database.py            # Database connection manager
├── load_season.py         # Main ETL orchestrator script
├── parsers/
│   ├── machine_parser.py  # Parse machine_variations.json
│   └── match_parser.py    # Parse match JSON files
└── loaders/
    └── db_loader.py       # Insert data into database
```

## Usage

### Load Season Data

```bash
# Basic usage
python3 etl/load_season.py --season 22

# With verbose logging
python3 etl/load_season.py --season 22 --verbose
```

### What It Does

1. **Loads machine variations** from `machine_variations.json`
2. **Parses all match files** from `mnp-data-archive/season-{season}/matches/`
3. **Extracts data**: players, teams, venues, matches, games, scores
4. **Normalizes machine keys** using variations file
5. **Inserts into database** with upsert logic (handles duplicates)

## Current Issue

**Problem**: Foreign key constraint violation when loading venue machines

```
Key (machine_key)=(Scooby Doo) is not present in table "machines".
```

**Cause**: Some machines in venue lists are not in `machine_variations.json`

**Fix Needed**: Modify `loaders/db_loader.py` to auto-create missing machines before inserting venue_machines

## Expected Output

When successful, you should see:

```
==========================================================
Starting ETL for Season 22
==========================================================
Data path: /Users/test_1/Pinball/MNP/pinball/mnp-data-archive/season-22
Matches path: /Users/test_1/Pinball/MNP/pinball/mnp-data-archive/season-22/matches

Step 1: Loading machine variations...
✓ Loaded 150 machines and 450 aliases

Step 2: Loading match files...
✓ Loaded 100 match files

Step 3: Extracting venues...
✓ Loaded 10 venues

Step 4: Extracting teams...
✓ Loaded 20 teams

Step 5: Extracting players...
✓ Loaded 200 players

Step 6: Loading match metadata...
✓ Loaded 100 matches

Step 7: Loading games...
✓ Loaded 400 games

Step 8: Loading scores...
✓ Loaded 1200 scores

==========================================================
ETL Complete for Season 22!
==========================================================

Summary:
  Machines: 150
  Venues: 10
  Teams: 20
  Players: 200
  Matches: 100
  Games: 400
  Scores: 1200
```

## Verification

After loading, verify data:

```bash
# Check counts
psql mnp_analyzer -c "
SELECT
    'players' as table, COUNT(*) as count FROM players
UNION ALL SELECT 'teams', COUNT(*) FROM teams
UNION ALL SELECT 'matches', COUNT(*) FROM matches
UNION ALL SELECT 'games', COUNT(*) FROM games
UNION ALL SELECT 'scores', COUNT(*) FROM scores;
"

# Check sample data
psql mnp_analyzer -c "SELECT * FROM matches LIMIT 5;"
psql mnp_analyzer -c "SELECT * FROM scores LIMIT 10;"
```

## Configuration

Edit `etl/config.py` to change:
- Database connection details
- Data paths
- Batch size for inserts

Database connection comes from `.env` file in project root.

## Troubleshooting

### "No module named 'etl'"
**Solution**: Make sure you're in the project root directory
```bash
cd /Users/test_1/Pinball/MNP/pinball
python3 etl/load_season.py --season 22
```

### "Permission denied for table"
**Solution**: Grant privileges to mnp_user
```bash
psql mnp_analyzer -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mnp_user;"
psql mnp_analyzer -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mnp_user;"
```

### "Matches directory not found"
**Solution**: Check data path in `etl/config.py` or verify data exists
```bash
ls -la mnp-data-archive/season-22/matches/
```

### Foreign key constraint violations
**Current issue**: Need to auto-create missing machines
**Fix**: Will be implemented in next session

## Next Steps

1. **Fix machine handling** - Auto-create machines not in variations file
2. **Load Season 22 data** - Run ETL successfully
3. **Calculate percentiles** - Create script to populate score_percentiles table
4. **Data quality checks** - Verify loaded data

See [CURRENT_STATUS.md](../CURRENT_STATUS.md) for current progress.
