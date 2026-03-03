#!/usr/bin/env python3
"""
Calculate end-of-season aggregations (percentiles and player stats).

This script is run ONCE at the end of a season to calculate final percentile
rankings and player statistics. These are skipped in the weekly workflow to
reduce runtime, but need to be computed once when the season concludes.

Usage:
    # Calculate for a single season
    python etl/calculate_end_of_season.py --season 23

    # Calculate for multiple seasons
    python etl/calculate_end_of_season.py --season 22 23

    # Verbose output
    python etl/calculate_end_of_season.py --season 23 --verbose
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from etl.config import config
from etl.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def run_etl_script(script_name: str, args: list = None) -> bool:
    """
    Run an ETL script as a subprocess.

    Args:
        script_name: Name of the script (e.g., 'calculate_percentiles.py')
        args: List of arguments to pass to the script

    Returns:
        bool: True if script succeeded, False otherwise
    """
    script_path = Path(__file__).parent / script_name

    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=config.PROJECT_ROOT,
            env={**subprocess.os.environ, "PYTHONPATH": str(config.PROJECT_ROOT)},
            capture_output=False,  # Let output flow through
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Failed to run {script_name}: {e}")
        return False


def calculate_end_of_season_aggregations(season: int) -> bool:
    """Calculate final percentiles and player statistics for a season."""
    logger.info(f"Calculating end-of-season aggregations for season {season}...")

    scripts = [
        ("calculate_percentiles.py", ["--season", str(season)]),
        ("calculate_player_stats.py", ["--season", str(season)]),
    ]

    for script_name, args in scripts:
        if not run_etl_script(script_name, args):
            logger.error(f"Failed to run {script_name}")
            return False

    return True


def verify_data(seasons: list) -> None:
    """Print summary of aggregations."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("End-of-Season Aggregations Complete")
    logger.info("=" * 60)

    from sqlalchemy import text

    try:
        db.connect()

        for season in seasons:
            with db.engine.connect() as conn:
                # Count percentile records
                result = conn.execute(
                    text("SELECT COUNT(*) FROM score_percentiles WHERE season = :season"),
                    {"season": str(season)},
                )
                percentile_count = result.scalar()

                # Count player machine stats
                result = conn.execute(
                    text("SELECT COUNT(*) FROM player_machine_stats WHERE season = :season"),
                    {"season": str(season)},
                )
                player_stats_count = result.scalar()

                logger.info(
                    f"Season {season}: {percentile_count} percentile records, {player_stats_count} player stats records"
                )

        db.close()

    except Exception as e:
        logger.error(f"Verification failed: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Calculate end-of-season aggregations (percentiles and player stats)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate for season 23 (at end of season)
  python etl/calculate_end_of_season.py --season 23

  # Calculate for multiple completed seasons
  python etl/calculate_end_of_season.py --season 22 23

  # Verbose output
  python etl/calculate_end_of_season.py --season 23 --verbose
        """,
    )
    parser.add_argument(
        "--season",
        type=int,
        nargs="+",
        required=True,
        help="Season number(s) to calculate final aggregations for",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    seasons = args.season

    logger.info("=" * 60)
    logger.info("MNP End-of-Season Aggregations")
    logger.info("=" * 60)
    logger.info(f"Seasons to calculate: {seasons}")
    logger.info("")

    # Calculate end-of-season aggregations
    for season in seasons:
        logger.info("")
        logger.info(f"{'=' * 60}")
        logger.info(f"Processing Season {season}")
        logger.info(f"{'=' * 60}")

        if not calculate_end_of_season_aggregations(season):
            logger.error(f"Failed to calculate aggregations for season {season}")
            return 1

    # Verify data
    verify_data(seasons)

    logger.info("")
    logger.info("=" * 60)
    logger.info("End-of-Season Calculation Complete!")
    logger.info("=" * 60)
    logger.info("")

    return 0


if __name__ == "__main__":
    sys.exit(main())
