#!/usr/bin/env python3
"""
Calculate player machine statistics and populate player_machine_stats table.

This script:
1. Aggregates scores per player per machine (optionally per venue)
2. Calculates: games_played, total_score, median_score, avg_score, best_score, worst_score
3. Calculates median and average percentile rankings
4. Populates player_machine_stats table

Usage:
    python etl/calculate_player_stats.py --season 22
    python etl/calculate_player_stats.py --season 22 --venue-specific
    python etl/calculate_player_stats.py --season 22 --verbose
"""

import argparse
import logging
import sys
from collections import defaultdict
import numpy as np
from sqlalchemy import text

from etl.config import config
from etl.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def fetch_player_scores(season: int):
    """
    Fetch all scores with player and machine information

    Args:
        season: Season number

    Returns:
        list: [(player_key, machine_key, venue_key, score), ...]
    """
    logger.info(f"Fetching player scores for season {season}...")

    query = """
        SELECT
            s.player_key,
            s.machine_key,
            s.venue_key,
            s.score
        FROM scores s
        WHERE s.season = :season
        ORDER BY s.player_key, s.machine_key, s.score
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        rows = result.fetchall()

    logger.info(f"Fetched {len(rows)} score records")

    return rows


def fetch_percentile_map(season: int):
    """
    Fetch percentile thresholds for all machines

    Args:
        season: Season number

    Returns:
        dict: {machine_key: {percentile: threshold, ...}}
    """
    logger.info("Fetching percentile thresholds...")

    query = """
        SELECT machine_key, percentile, score_threshold
        FROM score_percentiles
        WHERE season = :season AND venue_key IS NULL
        ORDER BY machine_key, percentile
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        rows = result.fetchall()

    # Build map: {machine_key: {percentile: threshold}}
    percentile_map = defaultdict(dict)

    for machine_key, percentile, threshold in rows:
        percentile_map[machine_key][percentile] = threshold

    logger.info(f"Loaded percentiles for {len(percentile_map)} machines")

    return dict(percentile_map)


def calculate_percentile_for_score(score, percentile_thresholds):
    """
    Calculate what percentile a score falls into

    Args:
        score: The score to evaluate
        percentile_thresholds: dict of {percentile: threshold}

    Returns:
        float: Interpolated percentile (0-100)
    """
    if not percentile_thresholds:
        return None

    # Get sorted percentile list
    percentiles = sorted(percentile_thresholds.keys())

    # Below lowest percentile
    if score < percentile_thresholds[percentiles[0]]:
        # Linear interpolation between 0 and first percentile
        p0 = percentiles[0]
        threshold0 = percentile_thresholds[p0]
        if threshold0 == 0:
            return 0.0
        return (score / threshold0) * p0

    # Above highest percentile
    if score >= percentile_thresholds[percentiles[-1]]:
        return 100.0

    # Find the two percentiles that bracket this score
    for i in range(len(percentiles) - 1):
        p_low = percentiles[i]
        p_high = percentiles[i + 1]

        threshold_low = percentile_thresholds[p_low]
        threshold_high = percentile_thresholds[p_high]

        if threshold_low <= score < threshold_high:
            # Linear interpolation
            if threshold_high == threshold_low:
                return p_low

            fraction = (score - threshold_low) / (threshold_high - threshold_low)
            return p_low + fraction * (p_high - p_low)

    return 100.0


def aggregate_player_stats(scores, percentile_map):
    """
    Aggregate player statistics from score records

    Args:
        scores: List of (player_key, machine_key, venue_key, score) tuples
        percentile_map: dict of {machine_key: {percentile: threshold}}

    Returns:
        dict: {(player_key, machine_key, venue_key): stats_dict}
    """
    logger.info("Aggregating player statistics...")

    # Group scores by (player, machine, venue)
    grouped = defaultdict(list)

    for player_key, machine_key, venue_key, score in scores:
        key = (player_key, machine_key, venue_key)
        grouped[key].append(score)

    # Calculate statistics
    stats = {}
    players_processed = 0
    total_combinations = len(grouped)

    for (player_key, machine_key, venue_key), score_list in grouped.items():
        scores_array = np.array(score_list)

        # Basic statistics
        stat_dict = {
            'player_key': player_key,
            'machine_key': machine_key,
            'venue_key': venue_key,
            'games_played': len(score_list),
            'total_score': int(np.sum(scores_array)),
            'median_score': int(np.median(scores_array)),
            'avg_score': int(np.mean(scores_array)),
            'best_score': int(np.max(scores_array)),
            'worst_score': int(np.min(scores_array))
        }

        # Calculate percentiles if available
        if machine_key in percentile_map:
            percentile_thresholds = percentile_map[machine_key]

            # Calculate percentile for each score
            percentile_values = []
            for score in score_list:
                pct = calculate_percentile_for_score(score, percentile_thresholds)
                if pct is not None:
                    percentile_values.append(pct)

            if percentile_values:
                stat_dict['median_percentile'] = round(np.median(percentile_values), 2)
                stat_dict['avg_percentile'] = round(np.mean(percentile_values), 2)
            else:
                stat_dict['median_percentile'] = None
                stat_dict['avg_percentile'] = None
        else:
            stat_dict['median_percentile'] = None
            stat_dict['avg_percentile'] = None

        stats[(player_key, machine_key, venue_key)] = stat_dict
        players_processed += 1

        # Log progress every 1000 records
        if players_processed % 1000 == 0:
            logger.info(f"  Processed {players_processed}/{total_combinations} player/machine combinations...")

    logger.info(f"Calculated stats for {len(stats)} player/machine/venue combinations")

    return stats


def clear_existing_stats(season: int):
    """Clear existing player stats for the season"""

    query = """
        DELETE FROM player_machine_stats
        WHERE season = :season AND venue_key = '_ALL_'
    """
    params = {'season': season}

    logger.info(f"Clearing existing player stats for season {season}")

    with db.engine.begin() as conn:
        conn.execute(text(query), params)


def insert_player_stats(stats_dict, season: int):
    """
    Insert player statistics into database

    Args:
        stats_dict: dict of {(player_key, machine_key, venue_key): stat_values}
        season: Season number
    """
    logger.info(f"Inserting player statistics...")

    query = """
        INSERT INTO player_machine_stats (
            player_key, machine_key, venue_key, season,
            games_played, total_score, median_score, avg_score,
            best_score, worst_score, median_percentile, avg_percentile
        )
        VALUES (
            :player_key, :machine_key, :venue_key, :season,
            :games_played, :total_score, :median_score, :avg_score,
            :best_score, :worst_score, :median_percentile, :avg_percentile
        )
        ON CONFLICT (player_key, machine_key, venue_key, season)
        DO UPDATE SET
            games_played = EXCLUDED.games_played,
            total_score = EXCLUDED.total_score,
            median_score = EXCLUDED.median_score,
            avg_score = EXCLUDED.avg_score,
            best_score = EXCLUDED.best_score,
            worst_score = EXCLUDED.worst_score,
            median_percentile = EXCLUDED.median_percentile,
            avg_percentile = EXCLUDED.avg_percentile,
            last_calculated = CURRENT_TIMESTAMP
    """

    records_inserted = 0
    batch_size = 100

    with db.engine.begin() as conn:
        batch = []

        for stat in stats_dict.values():
            record = {
                'player_key': stat['player_key'],
                'machine_key': stat['machine_key'],
                'venue_key': '_ALL_',  # Global stats (special value for all venues)
                'season': season,
                'games_played': stat['games_played'],
                'total_score': stat['total_score'],
                'median_score': stat['median_score'],
                'avg_score': stat['avg_score'],
                'best_score': stat['best_score'],
                'worst_score': stat['worst_score'],
                'median_percentile': stat['median_percentile'],
                'avg_percentile': stat['avg_percentile']
            }

            batch.append(record)

            if len(batch) >= batch_size:
                for rec in batch:
                    conn.execute(text(query), rec)
                records_inserted += len(batch)
                logger.info(f"  Inserted {records_inserted} records...")
                batch = []

        # Insert remaining records
        if batch:
            for rec in batch:
                conn.execute(text(query), rec)
            records_inserted += len(batch)

    logger.info(f"✓ Inserted {records_inserted} player statistics records")


def calculate_and_store_player_stats(season: int):
    """
    Main function to calculate and store player statistics

    Args:
        season: Season number
    """

    logger.info(f"=" * 60)
    logger.info(f"Calculating Player Machine Statistics for Season {season}")
    logger.info(f"=" * 60)

    # Step 1: Clear existing stats
    clear_existing_stats(season)

    # Step 2: Fetch percentile map
    percentile_map = fetch_percentile_map(season)

    # Step 3: Fetch all player scores
    scores = fetch_player_scores(season)

    if not scores:
        logger.error("No scores found!")
        return False

    # Step 4: Aggregate by (player, machine, venue)
    # Note: For now we'll aggregate globally (venue_key=NULL in output)
    # but we track venue in grouping to later support venue-specific stats

    # Group globally: ignore venue in the key
    global_scores = defaultdict(list)
    for player_key, machine_key, venue_key, score in scores:
        key = (player_key, machine_key)
        global_scores[key].append(score)

    # Convert back to expected format for aggregate_player_stats
    # Add venue_key=None to make it global
    score_tuples = []
    for (player_key, machine_key), score_list in global_scores.items():
        for score in score_list:
            score_tuples.append((player_key, machine_key, None, score))

    stats = aggregate_player_stats(score_tuples, percentile_map)

    # Step 5: Insert into database
    insert_player_stats(stats, season)

    logger.info("")
    logger.info(f"=" * 60)
    logger.info(f"✓ Player statistics calculated successfully!")
    logger.info(f"=" * 60)

    return True


def verify_player_stats(season: int):
    """Verify that player stats were calculated correctly"""

    logger.info("")
    logger.info("Verifying player statistics...")

    query = """
        SELECT
            COUNT(*) as total_records,
            COUNT(DISTINCT player_key) as unique_players,
            COUNT(DISTINCT machine_key) as unique_machines,
            MIN(games_played) as min_games,
            MAX(games_played) as max_games,
            AVG(games_played) as avg_games,
            AVG(avg_percentile) as overall_avg_percentile
        FROM player_machine_stats
        WHERE season = :season AND venue_key = '_ALL_'
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        row = result.fetchone()

    if row:
        logger.info(f"  Total records: {row[0]}")
        logger.info(f"  Unique players: {row[1]}")
        logger.info(f"  Unique machines: {row[2]}")
        logger.info(f"  Games played: min={row[3]}, max={row[4]}, avg={row[5]:.1f}")
        logger.info(f"  Overall avg percentile: {row[6]:.1f}")

    # Show top performers on a specific machine
    logger.info("")
    logger.info("Top performers on Jaws (by median percentile):")

    query = """
        SELECT
            p.name,
            pms.games_played,
            pms.best_score,
            pms.median_score,
            pms.median_percentile,
            pms.avg_percentile
        FROM player_machine_stats pms
        JOIN players p ON pms.player_key = p.player_key
        WHERE pms.season = :season
          AND pms.venue_key = '_ALL_'
          AND pms.machine_key = 'Jaws'
          AND pms.games_played >= 5
        ORDER BY pms.median_percentile DESC
        LIMIT 10
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        rows = result.fetchall()

    for row in rows:
        name, games, best, median, med_pct, avg_pct = row
        logger.info(
            f"  {name}: "
            f"{games} games, "
            f"best={best:,}, "
            f"median={median:,}, "
            f"med_pct={med_pct:.1f}, "
            f"avg_pct={avg_pct:.1f}"
        )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Calculate player machine statistics')
    parser.add_argument('--season', type=int, required=True, help='Season number (e.g., 22)')
    parser.add_argument('--venue-specific', action='store_true',
                       help='Calculate stats per venue (future feature)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.venue_specific:
        logger.error("Venue-specific stats not yet implemented")
        return 1

    try:
        # Connect to database
        db.connect()

        # Calculate player stats
        success = calculate_and_store_player_stats(args.season)

        if not success:
            return 1

        # Verify results
        verify_player_stats(args.season)

        logger.info("")
        logger.info("Done!")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
