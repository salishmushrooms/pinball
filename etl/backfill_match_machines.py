#!/usr/bin/env python3
"""
Backfill matches.machines column from match JSON files.

This script populates the per-match machines data for historical matches,
enabling accurate opportunity calculations in team_machine_picks.

Usage:
    python etl/backfill_match_machines.py
    python etl/backfill_match_machines.py --season 22
    python etl/backfill_match_machines.py --dry-run
    python etl/backfill_match_machines.py --recalculate
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from sqlalchemy import text

from etl.database import db
from etl.parsers.match_parser import MatchParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def get_data_archive_path() -> Path:
    """Get the path to the mnp-data-archive submodule."""
    return Path(__file__).parent.parent / 'mnp-data-archive'


def get_matches_needing_machines(season: int = None) -> list:
    """
    Get matches that don't have machines data.

    Returns:
        List of match_keys that need machines data populated
    """
    season_filter = "AND season = :season" if season else ""
    params = {'season': season} if season else {}

    query = f"""
        SELECT match_key, season
        FROM matches
        WHERE machines IS NULL
        {season_filter}
        ORDER BY season, match_key
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = result.fetchall()

    return [(row[0], row[1]) for row in rows]


def load_match_json(match_key: str, season: int, data_archive: Path) -> dict | None:
    """
    Load a match JSON file by match key.

    Args:
        match_key: Match key (e.g., 'mnp-22-1-ADB-TBT')
        season: Season number
        data_archive: Path to mnp-data-archive

    Returns:
        Match data dict or None if not found
    """
    # Match files are in season-XX/matches/
    matches_dir = data_archive / f'season-{season}' / 'matches'

    if not matches_dir.exists():
        return None

    match_file = matches_dir / f'{match_key}.json'

    if not match_file.exists():
        return None

    try:
        with open(match_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error loading {match_file}: {e}")
        return None


def extract_machines_from_match(match_data: dict) -> list | None:
    """
    Extract machines array from match data.

    Args:
        match_data: Match JSON data

    Returns:
        List of machine keys or None if not present
    """
    venue = match_data.get('venue', {})
    machines = venue.get('machines', [])

    if not machines:
        return None

    return machines


def backfill_match_machines(season: int = None, dry_run: bool = False) -> int:
    """
    Backfill matches.machines from JSON files.

    Args:
        season: Optional season to limit backfill
        dry_run: If True, only report what would be done

    Returns:
        Number of matches updated
    """
    logger.info("=" * 60)
    logger.info("Backfilling matches.machines from JSON files")
    logger.info("=" * 60)

    data_archive = get_data_archive_path()
    if not data_archive.exists():
        logger.error(f"Data archive not found at {data_archive}")
        return 0

    # Get matches needing machines data
    matches_to_update = get_matches_needing_machines(season)
    logger.info(f"Found {len(matches_to_update)} matches needing machines data")

    if not matches_to_update:
        logger.info("No matches need machines data!")
        return 0

    # Process each match
    updated = 0
    not_found = 0
    no_machines = 0
    updates = []

    for match_key, match_season in matches_to_update:
        match_data = load_match_json(match_key, match_season, data_archive)

        if match_data is None:
            not_found += 1
            continue

        machines = extract_machines_from_match(match_data)

        if machines is None:
            no_machines += 1
            continue

        updates.append({
            'match_key': match_key,
            'machines': json.dumps(machines)
        })

    logger.info(f"  - {len(updates)} matches have machines data to update")
    logger.info(f"  - {not_found} match files not found in archive")
    logger.info(f"  - {no_machines} matches have no machines in JSON")

    if not updates:
        logger.info("No updates to make!")
        return 0

    # Group by season for reporting
    if len(updates) <= 20:
        for u in updates:
            machines = json.loads(u['machines'])
            logger.info(f"    {u['match_key']}: {len(machines)} machines")

    if dry_run:
        logger.info("")
        logger.info("DRY RUN - No changes made")
        return len(updates)

    # Update database
    logger.info("")
    logger.info("Updating matches.machines column...")

    update_query = """
        UPDATE matches
        SET machines = :machines,
            updated_at = CURRENT_TIMESTAMP
        WHERE match_key = :match_key
    """

    with db.engine.begin() as conn:
        for update in updates:
            conn.execute(text(update_query), update)
            updated += 1

    logger.info(f"✓ Updated {updated} matches with machines data")
    return updated


def verify_machines_data(season: int = None):
    """
    Verify machines data coverage.
    """
    logger.info("")
    logger.info("Verifying machines data coverage...")

    season_filter = "WHERE season = :season" if season else ""
    params = {'season': season} if season else {}

    query = f"""
        SELECT
            season,
            COUNT(*) as total_matches,
            COUNT(machines) as with_machines,
            COUNT(*) - COUNT(machines) as without_machines
        FROM matches
        {season_filter}
        GROUP BY season
        ORDER BY season
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = result.fetchall()

    for row in rows:
        s, total, with_m, without_m = row
        pct = (with_m / total * 100) if total > 0 else 0
        logger.info(f"  Season {s}: {with_m}/{total} matches have machines data ({pct:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description='Backfill matches.machines from JSON files')
    parser.add_argument('--season', type=int, help='Specific season to backfill (default: all)')
    parser.add_argument('--dry-run', action='store_true', help='Only show what would be done')
    parser.add_argument('--recalculate', action='store_true',
                        help='Also recalculate team_machine_picks after backfill')

    args = parser.parse_args()

    try:
        db.connect()

        # Backfill machines data
        updated = backfill_match_machines(args.season, args.dry_run)

        # Verify coverage
        if not args.dry_run:
            verify_machines_data(args.season)

        if not args.dry_run and updated > 0 and args.recalculate:
            # Re-run team_machine_picks calculation
            logger.info("")
            logger.info("=" * 60)
            logger.info("Recalculating team_machine_picks...")
            logger.info("=" * 60)

            from etl.calculate_team_machine_picks import calculate_and_store_team_picks

            if args.season:
                calculate_and_store_team_picks(args.season)
            else:
                # Recalculate all seasons with data
                for s in [18, 19, 20, 21, 22]:
                    calculate_and_store_team_picks(s)

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
