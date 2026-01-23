#!/usr/bin/env python3
"""
Backfill venue_machines table from actual scores data.

This script ensures venue_machines is complete by deriving it from actual match data.
If a machine was played at a venue, it was definitely available there.

This fixes the data inconsistency where times_picked > total_opportunities
because the venue_machines table was missing entries.

Usage:
    python etl/backfill_venue_machines.py
    python etl/backfill_venue_machines.py --season 22
    python etl/backfill_venue_machines.py --dry-run
"""

import argparse
import logging
import sys
from sqlalchemy import text

from etl.database import db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def get_machines_from_scores(season: int = None):
    """
    Get all venue/machine/season combinations from actual scores data.

    This is the ground truth - if a score exists for a machine at a venue,
    that machine was available there.
    """
    logger.info("Extracting venue-machine combinations from scores data...")

    season_filter = "AND s.season = :season" if season else ""
    params = {'season': season} if season else {}

    # Only include scores from complete matches for consistency
    query = f"""
        SELECT DISTINCT
            m.venue_key,
            s.machine_key,
            s.season
        FROM scores s
        JOIN matches m ON s.match_key = m.match_key
        WHERE s.machine_key IS NOT NULL
        AND m.state = 'complete'
        {season_filter}
        ORDER BY s.season, m.venue_key, s.machine_key
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = result.fetchall()

    logger.info(f"Found {len(rows)} venue-machine-season combinations in scores")
    return rows


def get_existing_venue_machines(season: int = None):
    """Get existing venue_machines entries."""
    season_filter = "WHERE season = :season" if season else ""
    params = {'season': season} if season else {}

    query = f"""
        SELECT venue_key, machine_key, season
        FROM venue_machines
        {season_filter}
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = result.fetchall()

    return set((r[0], r[1], r[2]) for r in rows)


def backfill_venue_machines(season: int = None, dry_run: bool = False):
    """
    Backfill venue_machines table from scores data.

    Args:
        season: Optional season to limit backfill to
        dry_run: If True, only report what would be done
    """
    logger.info("=" * 60)
    logger.info("Backfilling venue_machines from scores data")
    logger.info("=" * 60)

    # Get machines from scores (ground truth)
    scores_machines = get_machines_from_scores(season)

    # Get existing venue_machines
    existing = get_existing_venue_machines(season)
    logger.info(f"Found {len(existing)} existing venue_machines entries")

    # Find missing entries
    missing = []
    for row in scores_machines:
        venue_key, machine_key, s = row
        if (venue_key, machine_key, s) not in existing:
            missing.append({
                'venue_key': venue_key,
                'machine_key': machine_key,
                'season': s,
                'active': True
            })

    logger.info(f"Found {len(missing)} missing venue_machines entries")

    if not missing:
        logger.info("No missing entries to backfill!")
        return 0

    # Group by season for reporting
    by_season = {}
    for entry in missing:
        s = entry['season']
        if s not in by_season:
            by_season[s] = []
        by_season[s].append(entry)

    for s, entries in sorted(by_season.items()):
        logger.info(f"  Season {s}: {len(entries)} missing entries")
        if len(entries) <= 10:
            for e in entries:
                logger.info(f"    - {e['venue_key']}/{e['machine_key']}")

    if dry_run:
        logger.info("")
        logger.info("DRY RUN - No changes made")
        return len(missing)

    # Insert missing entries
    logger.info("")
    logger.info("Inserting missing venue_machines entries...")

    insert_query = """
        INSERT INTO venue_machines (venue_key, machine_key, season, active)
        VALUES (:venue_key, :machine_key, :season, :active)
        ON CONFLICT (venue_key, machine_key, season) DO UPDATE SET
            active = EXCLUDED.active
    """

    with db.engine.begin() as conn:
        for entry in missing:
            # First ensure machine exists
            machine_check = conn.execute(text("""
                SELECT machine_key FROM machines WHERE machine_key = :machine_key
            """), {'machine_key': entry['machine_key']})

            if machine_check.fetchone() is None:
                logger.warning(f"Auto-creating missing machine: {entry['machine_key']}")
                conn.execute(text("""
                    INSERT INTO machines (machine_key, machine_name)
                    VALUES (:machine_key, :machine_name)
                    ON CONFLICT (machine_key) DO NOTHING
                """), {
                    'machine_key': entry['machine_key'],
                    'machine_name': entry['machine_key']
                })

            conn.execute(text(insert_query), entry)

    logger.info(f"✓ Inserted {len(missing)} venue_machines entries")
    return len(missing)


def verify_data_consistency(season: int = None):
    """
    Verify that all picks have corresponding opportunities.
    """
    logger.info("")
    logger.info("Verifying data consistency...")

    season_filter = "WHERE tmp.season = :season" if season else ""
    params = {'season': season} if season else {}

    query = f"""
        SELECT COUNT(*) as count
        FROM team_machine_picks tmp
        {season_filter}
        {"AND" if season else "WHERE"} tmp.times_picked > tmp.total_opportunities
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), params)
        count = result.fetchone()[0]

    if count > 0:
        logger.warning(f"Still have {count} records where picks > opportunities")
        logger.info("You may need to re-run calculate_team_machine_picks.py")
    else:
        logger.info("✓ All records have picks <= opportunities")

    return count


def main():
    parser = argparse.ArgumentParser(description='Backfill venue_machines from scores data')
    parser.add_argument('--season', type=int, help='Specific season to backfill (default: all)')
    parser.add_argument('--dry-run', action='store_true', help='Only show what would be done')
    parser.add_argument('--recalculate', action='store_true',
                        help='Also recalculate team_machine_picks after backfill')

    args = parser.parse_args()

    try:
        db.connect()

        # Backfill venue_machines
        inserted = backfill_venue_machines(args.season, args.dry_run)

        if not args.dry_run and inserted > 0 and args.recalculate:
            # Re-run team_machine_picks calculation
            logger.info("")
            logger.info("=" * 60)
            logger.info("Recalculating team_machine_picks...")
            logger.info("=" * 60)

            from etl.calculate_team_machine_picks import calculate_and_store_team_picks

            if args.season:
                calculate_and_store_team_picks(args.season)
            else:
                # Recalculate all seasons
                for s in [18, 19, 20, 21, 22]:
                    calculate_and_store_team_picks(s)

        # Verify
        if not args.dry_run:
            verify_data_consistency(args.season)

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
