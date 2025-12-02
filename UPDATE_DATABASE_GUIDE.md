# Guide for updating database with latest data from mnp-data-archive

Steps to take to update mnp-data archive and then use that to update database

## Update mnp-data-archive submodule with latest data

Run this combined command
git submodule update --remote mnp-data-archive && git add mnp-data-archive && git commit -m "Update data archive"

## Database Update Process

1. Activate mnp conda environment
conda activate mnp

2. Load Season Data (matches, players, teams, venues, scores)
python etl/load_season.py --season 22
This loads:
Machine variations and aliases
Venues and venue-machine relationships
Teams
Players
IPR ratings (from IPR.csv)
Match metadata
Games and scores

3. Calculate Score Percentiles
python etl/calculate_percentiles.py --season 23
This generates percentile thresholds (10th, 25th, 50th, 75th, 90th, 95th, 99th) for each machine based on all scores.

4. Calculate Player Statistics
python etl/calculate_player_stats.py --season 23
This aggregates player performance per machine (games played, median/avg score, percentile rankings).

5. Calculate team machine picks
python etl/calculate_team_machine_picks.py --season 22

6. Calculate match point totals
python etl/calculate_match_points.py --season 22

7. Calculate player total games played (across all seasons)
python etl/calculate_player_totals.py

7. (Optional) Update IPR Only
If you only need to refresh IPR values without reloading everything:
python etl/update_ipr.py