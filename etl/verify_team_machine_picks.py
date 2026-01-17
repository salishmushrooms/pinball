#!/usr/bin/env python3
"""
Verification script for team_machine_picks calculations.

Compares pre-calculated values in team_machine_picks table against
fresh calculations from raw games data to identify discrepancies.

Usage:
    python etl/verify_team_machine_picks.py --season 22
    python etl/verify_team_machine_picks.py --all-seasons
"""

import argparse
import logging
import sys
from sqlalchemy import text

from etl.database import db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def get_fresh_calculation(season: int) -> dict:
    """
    Calculate team machine picks fresh from raw games data.

    Returns dict of (team_key, machine_key, is_home, round_type) -> times_picked
    """
    query = """
    WITH pick_data AS (
        SELECT DISTINCT
            g.match_key,
            g.round_number,
            g.machine_key,
            CASE
                WHEN g.round_number IN (2, 4) THEN m.home_team_key
                ELSE m.away_team_key
            END as picking_team,
            CASE WHEN g.round_number IN (2, 4) THEN true ELSE false END as is_home,
            CASE WHEN g.round_number IN (1, 4) THEN 'doubles' ELSE 'singles' END as round_type
        FROM games g
        JOIN matches m ON g.match_key = m.match_key
        WHERE g.season = :season
    )
    SELECT picking_team, machine_key, is_home, round_type, COUNT(*) as times_picked
    FROM pick_data
    GROUP BY picking_team, machine_key, is_home, round_type
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        return {
            (row[0], row[1], row[2], row[3]): row[4]
            for row in result
        }


def get_precalculated(season: int) -> dict:
    """
    Get pre-calculated values from team_machine_picks table.

    Returns dict of (team_key, machine_key, is_home, round_type) -> times_picked
    """
    query = """
    SELECT team_key, machine_key, is_home, round_type, times_picked
    FROM team_machine_picks
    WHERE season = :season
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        return {
            (row[0], row[1], row[2], row[3]): row[4]
            for row in result
        }


def compare_calculations(season: int) -> dict:
    """Compare fresh vs pre-calculated and return summary."""
    fresh = get_fresh_calculation(season)
    precalc = get_precalculated(season)

    # Find discrepancies
    missing_from_precalc = []  # In fresh but not in precalc
    missing_from_fresh = []    # In precalc but not in fresh (shouldn't happen)
    mismatched = []            # Different counts

    for key, fresh_count in fresh.items():
        if key not in precalc:
            missing_from_precalc.append((key, fresh_count))
        elif precalc[key] != fresh_count:
            mismatched.append((key, fresh_count, precalc[key]))

    for key in precalc:
        if key not in fresh:
            missing_from_fresh.append((key, precalc[key]))

    return {
        'season': season,
        'fresh_total': sum(fresh.values()),
        'fresh_records': len(fresh),
        'precalc_total': sum(precalc.values()),
        'precalc_records': len(precalc),
        'missing_from_precalc': missing_from_precalc,
        'missing_from_fresh': missing_from_fresh,
        'mismatched': mismatched,
        'is_valid': len(missing_from_precalc) == 0 and len(missing_from_fresh) == 0 and len(mismatched) == 0
    }


def print_report(results: dict):
    """Print a detailed report of the comparison."""
    season = results['season']

    print(f"\n{'='*60}")
    print(f"Season {season} Verification Report")
    print(f"{'='*60}")

    print(f"\nTotals:")
    print(f"  Fresh calculation:  {results['fresh_records']:,} records, {results['fresh_total']:,} total picks")
    print(f"  Pre-calculated:     {results['precalc_records']:,} records, {results['precalc_total']:,} total picks")

    if results['is_valid']:
        print(f"\n✅ VALID: Pre-calculated data matches fresh calculation")
        return

    print(f"\n❌ INVALID: Discrepancies found!")

    if results['missing_from_precalc']:
        print(f"\n  Missing from pre-calculated ({len(results['missing_from_precalc'])} records):")
        # Show top 10
        for (team, machine, is_home, round_type), count in sorted(
            results['missing_from_precalc'],
            key=lambda x: -x[1]
        )[:10]:
            home_str = "home" if is_home else "away"
            print(f"    {team} | {machine:20} | {home_str:4} | {round_type:7} | {count} picks")
        if len(results['missing_from_precalc']) > 10:
            print(f"    ... and {len(results['missing_from_precalc']) - 10} more")

    if results['missing_from_fresh']:
        print(f"\n  In pre-calc but NOT in fresh data ({len(results['missing_from_fresh'])} records):")
        for (team, machine, is_home, round_type), count in results['missing_from_fresh'][:10]:
            home_str = "home" if is_home else "away"
            print(f"    {team} | {machine:20} | {home_str:4} | {round_type:7} | {count} picks")

    if results['mismatched']:
        print(f"\n  Mismatched counts ({len(results['mismatched'])} records):")
        for (team, machine, is_home, round_type), fresh_count, precalc_count in results['mismatched'][:10]:
            home_str = "home" if is_home else "away"
            print(f"    {team} | {machine:20} | {home_str:4} | {round_type:7} | fresh={fresh_count} vs precalc={precalc_count}")


def main():
    parser = argparse.ArgumentParser(description='Verify team_machine_picks calculations')
    parser.add_argument('--season', type=int, help='Season to verify')
    parser.add_argument('--all-seasons', action='store_true', help='Verify all seasons (18-22)')

    args = parser.parse_args()

    if not args.season and not args.all_seasons:
        parser.error("Must specify --season or --all-seasons")

    seasons = [18, 19, 20, 21, 22] if args.all_seasons else [args.season]

    try:
        db.connect()

        all_valid = True
        for season in seasons:
            results = compare_calculations(season)
            print_report(results)
            if not results['is_valid']:
                all_valid = False

        print(f"\n{'='*60}")
        if all_valid:
            print("✅ All seasons VALID")
        else:
            print("❌ Some seasons have discrepancies - re-run ETL to fix")
        print(f"{'='*60}\n")

        return 0 if all_valid else 1

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
