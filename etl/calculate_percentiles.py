#!/usr/bin/env python3
"""
Calculate score percentiles for each machine and populate score_percentiles table.

This script:
1. Fetches all scores for each machine
2. Calculates percentile thresholds (10th, 25th, 50th, 75th, 90th, 95th, 99th)
3. Calculates mean and standard deviation
4. Populates score_percentiles table

Usage:
    python etl/calculate_percentiles.py --season 22
    python etl/calculate_percentiles.py --season 22 --venue-specific
    python etl/calculate_percentiles.py --season 22 --verbose
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

# Percentiles to calculate
PERCENTILES = [10, 25, 50, 75, 90, 95, 99]


def fetch_scores_by_machine(season: int, venue_key=None):
    """
    Fetch all scores grouped by machine (and optionally venue)

    Args:
        season: Season number
        venue_key: Optional venue key to filter by

    Returns:
        dict: {machine_key: [(score, venue_key), ...]}
    """
    logger.info(f"Fetching scores for season {season}...")

    query = """
        SELECT machine_key, venue_key, score
        FROM scores
        WHERE season = :season
    """

    if venue_key:
        query += " AND venue_key = :venue_key"
        params = {'season': season, 'venue_key': venue_key}
    else:
        params = {'season': season}

    query += " ORDER BY machine_key, score"

    # Use engine connection properly
    with db.engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = result.fetchall()

    # Group scores by machine (and venue if specified)
    scores_by_machine = defaultdict(list)

    for row in rows:
        machine_key = row[0]
        venue = row[1]
        score = row[2]

        if venue_key:
            # Venue-specific grouping
            key = (machine_key, venue_key)
        else:
            # Machine-only grouping
            key = machine_key

        scores_by_machine[key].append(score)

    logger.info(f"Found scores for {len(scores_by_machine)} machine/venue combinations")

    return dict(scores_by_machine)


def calculate_percentiles_for_scores(scores):
    """
    Calculate percentile thresholds for a list of scores

    Args:
        scores: List of score values

    Returns:
        dict: {percentile: threshold_value, ...} plus 'mean' and 'stddev'
    """
    if not scores:
        return None

    scores_array = np.array(scores)

    # Calculate percentiles
    percentile_values = {}
    for p in PERCENTILES:
        threshold = np.percentile(scores_array, p)
        percentile_values[p] = int(threshold)

    # Also calculate mean and stddev for outlier detection
    percentile_values['mean'] = int(np.mean(scores_array))
    percentile_values['stddev'] = int(np.std(scores_array))
    percentile_values['sample_size'] = len(scores)

    return percentile_values


def clear_existing_percentiles(season: int, venue_key=None):
    """Clear existing percentiles for the season (and optionally venue)"""

    if venue_key:
        query = """
            DELETE FROM score_percentiles
            WHERE season = :season AND venue_key = :venue_key
        """
        params = {'season': season, 'venue_key': venue_key}
        logger.info(f"Clearing existing percentiles for season {season}, venue {venue_key}")
    else:
        query = """
            DELETE FROM score_percentiles
            WHERE season = :season AND venue_key = '_ALL_'
        """
        params = {'season': season}
        logger.info(f"Clearing existing percentiles for season {season} (all venues)")

    with db.engine.begin() as conn:
        conn.execute(text(query), params)


def insert_percentiles(machine_key, venue_key, season, percentile_data):
    """Insert percentile data for a machine/venue/season combination"""

    records = []

    for percentile in PERCENTILES:
        threshold = percentile_data[percentile]
        sample_size = percentile_data['sample_size']

        records.append({
            'machine_key': machine_key,
            'venue_key': venue_key,
            'season': season,
            'percentile': percentile,
            'score_threshold': threshold,
            'sample_size': sample_size
        })

    # Insert all percentiles for this machine
    query = """
        INSERT INTO score_percentiles (machine_key, venue_key, season, percentile, score_threshold, sample_size)
        VALUES (:machine_key, :venue_key, :season, :percentile, :score_threshold, :sample_size)
        ON CONFLICT (machine_key, venue_key, season, percentile)
        DO UPDATE SET
            score_threshold = EXCLUDED.score_threshold,
            sample_size = EXCLUDED.sample_size,
            last_calculated = CURRENT_TIMESTAMP
    """

    with db.engine.begin() as conn:
        for record in records:
            conn.execute(text(query), record)


def calculate_and_store_percentiles(season: int, venue_specific: bool = False):
    """
    Main function to calculate and store percentiles

    Args:
        season: Season number
        venue_specific: If True, calculate percentiles per venue; if False, global per machine
    """

    logger.info(f"=" * 60)
    logger.info(f"Calculating Score Percentiles for Season {season}")
    logger.info(f"Mode: {'Venue-Specific' if venue_specific else 'Global (All Venues)'}")
    logger.info(f"=" * 60)

    # Step 1: Clear existing percentiles
    clear_existing_percentiles(season)

    # Step 2: Fetch scores
    scores_by_machine = fetch_scores_by_machine(season)

    if not scores_by_machine:
        logger.error("No scores found!")
        return False

    # Step 3: Calculate percentiles
    logger.info(f"Calculating percentiles for {len(scores_by_machine)} machines...")

    machines_processed = 0
    machines_skipped = 0

    for machine_key, scores in scores_by_machine.items():
        # Need at least 10 scores for meaningful percentiles
        if len(scores) < 10:
            logger.warning(f"Skipping {machine_key}: only {len(scores)} scores (need ≥10)")
            machines_skipped += 1
            continue

        percentile_data = calculate_percentiles_for_scores(scores)

        if percentile_data:
            # Store with venue_key = '_ALL_' for global percentiles
            insert_percentiles(machine_key, '_ALL_', season, percentile_data)
            machines_processed += 1

            # Log some stats for interesting machines
            if machines_processed <= 5 or len(scores) > 100:
                logger.info(
                    f"  {machine_key}: "
                    f"n={len(scores)}, "
                    f"median={percentile_data[50]:,}, "
                    f"p90={percentile_data[90]:,}, "
                    f"p99={percentile_data[99]:,}"
                )

    logger.info("")
    logger.info(f"=" * 60)
    logger.info(f"✓ Percentiles calculated successfully!")
    logger.info(f"  Machines processed: {machines_processed}")
    logger.info(f"  Machines skipped: {machines_skipped} (insufficient data)")
    logger.info(f"  Percentile records created: {machines_processed * len(PERCENTILES)}")
    logger.info(f"=" * 60)

    return True


def verify_percentiles(season: int):
    """Verify that percentiles were calculated correctly"""

    logger.info("")
    logger.info("Verifying percentile data...")

    query = """
        SELECT
            COUNT(DISTINCT machine_key) as machines,
            COUNT(*) as total_records,
            MIN(sample_size) as min_samples,
            MAX(sample_size) as max_samples,
            AVG(sample_size) as avg_samples
        FROM score_percentiles
        WHERE season = :season AND venue_key = '_ALL_'
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        row = result.fetchone()

    if row:
        logger.info(f"  Machines with percentiles: {row[0]}")
        logger.info(f"  Total percentile records: {row[1]}")
        logger.info(f"  Sample sizes: min={row[2]}, max={row[3]}, avg={row[4]:.1f}")

    # Show a few examples
    logger.info("")
    logger.info("Sample percentiles (top 5 machines by sample size):")

    query = """
        SELECT
            machine_key,
            percentile,
            score_threshold,
            sample_size
        FROM score_percentiles
        WHERE season = :season AND venue_key = '_ALL_'
        ORDER BY sample_size DESC, machine_key, percentile
        LIMIT 35
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        rows = result.fetchall()

    current_machine = None
    for row in rows:
        machine, p, threshold, samples = row

        if machine != current_machine:
            logger.info(f"\n  {machine} (n={samples}):")
            current_machine = machine

        logger.info(f"    p{p}: {threshold:,}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Calculate score percentiles')
    parser.add_argument('--season', type=int, required=True, help='Season number (e.g., 22)')
    parser.add_argument('--venue-specific', action='store_true',
                       help='Calculate percentiles per venue (future feature)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.venue_specific:
        logger.error("Venue-specific percentiles not yet implemented")
        return 1

    try:
        # Connect to database
        db.connect()

        # Calculate percentiles
        success = calculate_and_store_percentiles(args.season, args.venue_specific)

        if not success:
            return 1

        # Verify results
        verify_percentiles(args.season)

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
