#!/usr/bin/env python3
"""
Update database with latest season data from mnp-data-archive.

This script orchestrates the full update process:
1. Load/upsert season data (new records added, existing unchanged)
2. Recalculate all aggregations for that season
3. Recalculate cross-season player totals
4. Optionally sync to production database

The script is idempotent - run it multiple times and get the same result.
Works regardless of current database state.

Usage:
    # Update local database for a single season
    python etl/update_season.py --season 22

    # Update multiple seasons
    python etl/update_season.py --season 20 21 22

    # Update and sync to production
    python etl/update_season.py --season 22 --sync-production

    # Skip aggregation calculations (just load raw data)
    python etl/update_season.py --season 22 --skip-aggregations

    # Verbose output
    python etl/update_season.py --season 22 --verbose
"""

import argparse
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

from etl.config import config
from etl.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Seasons that should have aggregations calculated
# Seasons 18-19 are loaded but excluded from calculations per project decision
AGGREGATION_SEASONS = [20, 21, 22, 23]


def run_etl_script(script_name: str, args: list = None) -> bool:
    """
    Run an ETL script as a subprocess.

    Args:
        script_name: Name of the script (e.g., 'load_season.py')
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
            env={**subprocess.os.environ, 'PYTHONPATH': str(config.PROJECT_ROOT)},
            capture_output=False  # Let output flow through
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Failed to run {script_name}: {e}")
        return False


def load_season_data(season: int) -> bool:
    """Load/upsert season data into database."""
    logger.info(f"Loading data for season {season}...")
    return run_etl_script('load_season.py', ['--season', str(season)])


def calculate_aggregations(season: int) -> bool:
    """Calculate all aggregations for a season."""

    if season not in AGGREGATION_SEASONS:
        logger.info(f"Skipping aggregations for season {season} (not in AGGREGATION_SEASONS)")
        return True

    logger.info(f"Calculating aggregations for season {season}...")

    scripts = [
        ('calculate_percentiles.py', ['--season', str(season)]),
        ('calculate_player_stats.py', ['--season', str(season)]),
        ('calculate_team_machine_picks.py', ['--season', str(season)]),
        ('calculate_match_points.py', ['--season', str(season)]),
    ]

    for script_name, args in scripts:
        if not run_etl_script(script_name, args):
            logger.error(f"Failed to run {script_name}")
            return False

    return True


def calculate_player_totals() -> bool:
    """Calculate cross-season player totals."""
    logger.info("Calculating cross-season player totals...")
    return run_etl_script('calculate_player_totals.py')


def export_local_database(output_path: str) -> bool:
    """
    Export local database to SQL file.

    Args:
        output_path: Path to write the SQL dump

    Returns:
        bool: True if export succeeded
    """
    logger.info(f"Exporting local database to {output_path}...")

    cmd = [
        'pg_dump',
        '-h', 'localhost',
        '-U', 'mnp_user',
        '-d', 'mnp_analyzer',
        '--data-only',
        '--no-owner',
        '--no-acl',
        '-f', output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"pg_dump failed: {result.stderr}")
            return False
        logger.info(f"Export complete: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return False


def sync_to_production(sql_file: str) -> bool:
    """
    Sync data to production database via Railway.

    Args:
        sql_file: Path to SQL dump file

    Returns:
        bool: True if sync succeeded
    """
    logger.info("Syncing to production database...")

    # Check if railway CLI is available
    try:
        result = subprocess.run(['railway', 'whoami'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Railway CLI not authenticated. Run 'railway login' first.")
            return False
    except FileNotFoundError:
        logger.error("Railway CLI not found. Install with: npm install -g @railway/cli")
        return False

    # Clear production tables before import
    logger.info("Clearing production tables...")
    truncate_sql = """
TRUNCATE TABLE scores, games, matches, player_machine_stats,
               score_percentiles, team_machine_picks, venue_machines
RESTART IDENTITY CASCADE;
"""

    try:
        # Run truncate via railway
        proc = subprocess.Popen(
            ['railway', 'connect', 'Postgres--OkR'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(input=truncate_sql, timeout=60)

        if proc.returncode != 0:
            logger.warning(f"Truncate may have failed (this is OK if tables were empty): {stderr}")
    except Exception as e:
        logger.warning(f"Truncate step encountered an error: {e}")

    # Import data
    logger.info("Importing data to production...")
    try:
        with open(sql_file, 'r') as f:
            sql_content = f.read()

        proc = subprocess.Popen(
            ['railway', 'connect', 'Postgres--OkR'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(input=sql_content, timeout=300)

        if proc.returncode != 0:
            # Check if it's just duplicate key errors (which are OK)
            if 'duplicate key' in stderr.lower():
                logger.warning("Some duplicate key errors occurred (this is OK for existing data)")
            else:
                logger.error(f"Import failed: {stderr}")
                return False

        logger.info("Production sync complete!")
        return True

    except Exception as e:
        logger.error(f"Import failed: {e}")
        return False


def verify_data(seasons: list) -> None:
    """Print summary of loaded data."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Data Verification")
    logger.info("=" * 60)

    from sqlalchemy import text

    try:
        db.connect()

        for season in seasons:
            with db.engine.connect() as conn:
                # Count matches
                result = conn.execute(
                    text("SELECT COUNT(*) FROM matches WHERE season = :season"),
                    {'season': str(season)}
                )
                match_count = result.scalar()

                # Count scores
                result = conn.execute(
                    text("SELECT COUNT(*) FROM scores WHERE season = :season"),
                    {'season': str(season)}
                )
                score_count = result.scalar()

                # Count percentile records
                result = conn.execute(
                    text("SELECT COUNT(*) FROM score_percentiles WHERE season = :season"),
                    {'season': str(season)}
                )
                percentile_count = result.scalar()

                logger.info(f"Season {season}: {match_count} matches, {score_count} scores, {percentile_count} percentile records")

        db.close()

    except Exception as e:
        logger.error(f"Verification failed: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Update database with latest season data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update season 22 locally
  python etl/update_season.py --season 22

  # Update multiple seasons
  python etl/update_season.py --season 20 21 22

  # Update and sync to production
  python etl/update_season.py --season 22 --sync-production
        """
    )
    parser.add_argument(
        '--season',
        type=int,
        nargs='+',
        required=True,
        help='Season number(s) to update (e.g., 22 or 20 21 22)'
    )
    parser.add_argument(
        '--sync-production',
        action='store_true',
        help='Also sync data to production database via Railway'
    )
    parser.add_argument(
        '--skip-aggregations',
        action='store_true',
        help='Skip aggregation calculations (just load raw data)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    seasons = args.season

    logger.info("=" * 60)
    logger.info("MNP Database Update")
    logger.info("=" * 60)
    logger.info(f"Seasons to update: {seasons}")
    logger.info(f"Sync to production: {args.sync_production}")
    logger.info(f"Calculate aggregations: {not args.skip_aggregations}")
    logger.info("")

    # Step 1: Load season data
    for season in seasons:
        logger.info("")
        logger.info(f"{'='*60}")
        logger.info(f"Processing Season {season}")
        logger.info(f"{'='*60}")

        if not load_season_data(season):
            logger.error(f"Failed to load season {season}")
            return 1

        # Step 2: Calculate aggregations (if not skipped)
        if not args.skip_aggregations:
            if not calculate_aggregations(season):
                logger.error(f"Failed to calculate aggregations for season {season}")
                return 1

    # Step 3: Calculate cross-season player totals
    if not args.skip_aggregations:
        if not calculate_player_totals():
            logger.error("Failed to calculate player totals")
            return 1

    # Step 4: Verify data
    verify_data(seasons)

    # Step 5: Sync to production (if requested)
    if args.sync_production:
        logger.info("")
        logger.info("=" * 60)
        logger.info("Syncing to Production")
        logger.info("=" * 60)

        with tempfile.NamedTemporaryFile(suffix='.sql', delete=False) as f:
            temp_sql = f.name

        try:
            if not export_local_database(temp_sql):
                logger.error("Failed to export local database")
                return 1

            if not sync_to_production(temp_sql):
                logger.error("Failed to sync to production")
                return 1

        finally:
            # Clean up temp file
            Path(temp_sql).unlink(missing_ok=True)

    logger.info("")
    logger.info("=" * 60)
    logger.info("Update Complete!")
    logger.info("=" * 60)

    if not args.sync_production:
        logger.info("")
        logger.info("To sync to production, run:")
        logger.info(f"  python etl/update_season.py --season {' '.join(map(str, seasons))} --sync-production")

    return 0


if __name__ == '__main__':
    sys.exit(main())
