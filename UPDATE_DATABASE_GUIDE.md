# Guide for updating database with latest data from mnp-data-archive

Steps to take to update mnp-data-archive and then use that to update database.

## Prerequisites

### Conda Environment
The ETL scripts require the `mnp` conda environment. Activate it before running any commands:
```bash
source /Users/test_1/opt/anaconda3/bin/activate mnp
```

### PYTHONPATH
All ETL scripts need PYTHONPATH set to the project root:
```bash
export PYTHONPATH=/Users/test_1/Pinball/MNP/pinball
```

Or prefix each command:
```bash
PYTHONPATH=/Users/test_1/Pinball/MNP/pinball python etl/...
```

### PostgreSQL
The database must be running. Check with:
```bash
/usr/local/Cellar/postgresql@15/15.15/bin/psql -h localhost -p 5432 -U mnp_user -d mnp_analyzer -c "SELECT 1"
```

## Update mnp-data-archive submodule with latest data

Run this combined command:
```bash
git submodule update --init --remote
```

If that fails, try:
```bash
cd mnp-data-archive && git pull origin main && cd ..
git add mnp-data-archive && git commit -m "Update data archive"
```

## Database Update Process

### Quick Reference (All Seasons 20-22)
```bash
# Activate environment
source /Users/test_1/opt/anaconda3/bin/activate mnp
export PYTHONPATH=/Users/test_1/Pinball/MNP/pinball

# Load season data
for season in 20 21 22; do
  python etl/load_season.py --season $season
done

# Calculate percentiles
for season in 20 21 22; do
  python etl/calculate_percentiles.py --season $season
done

# Calculate player stats
for season in 20 21 22; do
  python etl/calculate_player_stats.py --season $season
done

# Calculate team machine picks
for season in 20 21 22; do
  python etl/calculate_team_machine_picks.py --season $season
done

# Calculate match points
for season in 20 21 22; do
  python etl/calculate_match_points.py --season $season
done

# Calculate player totals (cross-season)
python etl/calculate_player_totals.py
```

### Step-by-Step Guide

#### 1. Load Season Data (matches, players, teams, venues, scores)
```bash
python etl/load_season.py --season 20
python etl/load_season.py --season 21
python etl/load_season.py --season 22
```
This loads:
- Machine variations and aliases
- Venues and venue-machine relationships
- Teams
- Players
- IPR ratings (from IPR.csv)
- Match metadata
- Games and scores

#### 2. Calculate Score Percentiles
```bash
python etl/calculate_percentiles.py --season 20
python etl/calculate_percentiles.py --season 21
python etl/calculate_percentiles.py --season 22
```
This generates percentile thresholds (10th, 25th, 50th, 75th, 90th, 95th, 99th) for each machine based on all scores.

#### 3. Calculate Player Statistics
```bash
python etl/calculate_player_stats.py --season 20
python etl/calculate_player_stats.py --season 21
python etl/calculate_player_stats.py --season 22
```
This aggregates player performance per machine (games played, median/avg score, percentile rankings).

#### 4. Calculate Team Machine Picks
```bash
python etl/calculate_team_machine_picks.py --season 20
python etl/calculate_team_machine_picks.py --season 21
python etl/calculate_team_machine_picks.py --season 22
```

#### 5. Calculate Match Point Totals
```bash
python etl/calculate_match_points.py --season 20
python etl/calculate_match_points.py --season 21
python etl/calculate_match_points.py --season 22
```

#### 6. Calculate Player Total Games Played (across all seasons)
```bash
python etl/calculate_player_totals.py
```

#### 7. (Optional) Update IPR Only
If you only need to refresh IPR values without reloading everything:
```bash
python etl/update_ipr.py
```

## Available Seasons

The database currently supports seasons 20, 21, and 22. Season data is located at:
- `mnp-data-archive/season-20/`
- `mnp-data-archive/season-21/`
- `mnp-data-archive/season-22/`

## Troubleshooting

### ModuleNotFoundError: No module named 'etl'
Make sure PYTHONPATH is set:
```bash
export PYTHONPATH=/Users/test_1/Pinball/MNP/pinball
```

### Cannot connect to database
Check PostgreSQL is running and the connection details in `.env` are correct.

### Submodule update fails
Try:
```bash
git submodule sync
git submodule update --init --force
```
