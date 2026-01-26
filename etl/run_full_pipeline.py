#!/usr/bin/env python3
"""
MNP ETL Full Pipeline Runner

Runs all ETL steps in the correct order to fully populate the database.
This is the single source of truth for the complete ETL pipeline.

Usage:
    # Load specific seasons
    python etl/run_full_pipeline.py --seasons 22
    python etl/run_full_pipeline.py --seasons 18 19 20 21 22

    # Load all available seasons (18-22)
    python etl/run_full_pipeline.py --all-seasons

    # Skip specific steps (useful for partial updates)
    python etl/run_full_pipeline.py --seasons 22 --skip-load
    python etl/run_full_pipeline.py --seasons 22 --only-aggregates

    # Verify team machine picks after calculation
    python etl/verify_team_machine_picks.py --all-seasons

IMPORTANT - Matchplay Account Links:
    Production users may have linked their Matchplay accounts to their player profiles.
    These links are stored in matchplay_player_mappings and CANNOT be recreated.

    Before running a full database rebuild:
    1. Backup matchplay links: python etl/backup_matchplay_links.py --backup
    2. After rebuild, restore: python etl/backup_matchplay_links.py --restore --input <backup_file>

    The pipeline will warn you if matchplay links exist and offer to back them up.
    Use --skip-matchplay-check to bypass this check (not recommended for production).

IMPORTANT - Data Corrections Order:
    Before running this pipeline, ensure machine_variations.json is up to date
    (run add_missing_machines.py if needed).

    The load_season.py step normalizes machine keys using machine_variations.json.
    Post-load steps handle player deduplication and backfills automatically.

Pipeline Steps (in order):
    1. load_season.py           - Load raw match data with machine key normalization

    POST-LOAD (automatic):
    - deduplicate_players.py    - Merge duplicate players (SHA-1 vs slug key formats)
    - backfill_match_machines.py - Populate matches.machines from JSON files
    - backfill_venue_machines.py - Ensure venue_machines table is complete

    2. calculate_percentiles.py - Calculate score percentile thresholds per machine
    3. calculate_player_stats.py - Aggregate player statistics with percentiles
    4. calculate_team_machine_picks.py - Calculate team machine selection patterns
       NOTE: Each round has MULTIPLE games on different machines.
       This calculates picks per (team, machine, home/away, round_type).
    5. calculate_player_totals.py - Calculate player season totals
    6. calculate_match_points.py - Calculate match point totals

    EXTERNAL DATA (optional, requires MATCHPLAY_API_TOKEN):
    - refresh_matchplay_data.py - Refresh Matchplay.events data for linked players

    POST-PIPELINE (if --restore-matchplay specified):
    - Restore matchplay links from backup file

Verification:
    After running the pipeline, verify aggregations with:
    python etl/verify_team_machine_picks.py --all-seasons

Note: Steps 2-6 are aggregate calculations that depend on step 1 and post-load steps.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Available seasons in the data archive
# IMPORTANT: Keep this in sync with production database!
# Seasons 18-19 exist in archive but are excluded from aggregations.
# Production currently has seasons 20-23.
AVAILABLE_SEASONS = [20, 21, 22, 23]

# ETL scripts in execution order
# Format: (script_name, description, requires_season_arg)
PIPELINE_STEPS = [
    ("load_season.py", "Load raw match data", True),
    ("calculate_percentiles.py", "Calculate score percentiles", True),
    ("calculate_player_stats.py", "Calculate player statistics", True),
    ("calculate_team_machine_picks.py", "Calculate team machine picks", True),
    ("calculate_player_totals.py", "Calculate player totals", False),  # This one processes all seasons at once
    ("calculate_match_points.py", "Calculate match points", True),
]

# Post-load steps that run once after all seasons are loaded
# These fix data issues and backfill derived data before aggregates
POST_LOAD_STEPS = [
    ("deduplicate_players.py", "Deduplicate players"),
    ("backfill_match_machines.py", "Backfill match machines"),
    ("backfill_venue_machines.py", "Backfill venue machines"),
]

# External data refresh steps (optional, require API tokens)
EXTERNAL_DATA_STEPS = [
    ("refresh_matchplay_data.py", "Refresh Matchplay.events data"),
]

# Aggregate-only steps (steps 2-6)
AGGREGATE_STEPS = PIPELINE_STEPS[1:]


def check_matchplay_links(etl_dir: Path) -> tuple[bool, int, str]:
    """
    Check if matchplay links exist in the database.

    Returns:
        tuple: (has_links: bool, count: int, backup_path: str or None)
    """
    try:
        # Import the backup module
        sys.path.insert(0, str(etl_dir.parent))
        from etl.backup_matchplay_links import verify_matchplay_links, backup_matchplay_links

        has_links, message, counts = verify_matchplay_links()
        link_count = counts.get("matchplay_player_mappings", 0) or 0

        return has_links, link_count, None
    except Exception as e:
        print(f"  Warning: Could not check matchplay links: {e}")
        return False, 0, None


def backup_matchplay_data(etl_dir: Path) -> tuple[bool, str]:
    """
    Create a backup of matchplay links.

    Returns:
        tuple: (success: bool, backup_path: str or error message)
    """
    try:
        sys.path.insert(0, str(etl_dir.parent))
        from etl.backup_matchplay_links import backup_matchplay_links, BACKUP_DIR

        # Create backup with timestamp
        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"matchplay_links_{timestamp}.json"

        success, message = backup_matchplay_links(backup_path)

        if success:
            return True, str(backup_path)
        else:
            return False, message
    except Exception as e:
        return False, str(e)


def restore_matchplay_data(backup_path: Path, etl_dir: Path) -> tuple[bool, str]:
    """
    Restore matchplay links from a backup file.

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        sys.path.insert(0, str(etl_dir.parent))
        from etl.backup_matchplay_links import restore_matchplay_links

        success, message = restore_matchplay_links(backup_path)
        return success, message
    except Exception as e:
        return False, str(e)


def verify_matchplay_restored(etl_dir: Path, expected_count: int) -> tuple[bool, str]:
    """
    Verify matchplay links were restored correctly.

    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        sys.path.insert(0, str(etl_dir.parent))
        from etl.backup_matchplay_links import verify_matchplay_links

        has_links, message, counts = verify_matchplay_links()
        actual_count = counts.get("matchplay_player_mappings", 0) or 0

        if actual_count >= expected_count:
            return True, f"Verified {actual_count} matchplay links restored (expected {expected_count})"
        elif actual_count > 0:
            return True, f"Partial restore: {actual_count} links (expected {expected_count})"
        else:
            return False, f"No matchplay links found after restore (expected {expected_count})"
    except Exception as e:
        return False, str(e)


def run_script(script_name: str, season: int = None, etl_dir: Path = None) -> bool:
    """Run a single ETL script and return success status."""
    script_path = etl_dir / script_name

    if not script_path.exists():
        print(f"  ❌ Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if season is not None:
        cmd.extend(["--season", str(season)])

    try:
        result = subprocess.run(cmd, check=True, cwd=etl_dir.parent)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed with exit code {e.returncode}")
        return False


def run_pipeline(
    seasons: list[int],
    skip_load: bool = False,
    only_aggregates: bool = False,
    refresh_matchplay: bool = False,
    skip_matchplay_check: bool = False,
    restore_matchplay: Path = None,
    etl_dir: Path = None
) -> bool:
    """Run the full ETL pipeline for the specified seasons."""

    print("=" * 60)
    print("MNP ETL Full Pipeline")
    print("=" * 60)
    print(f"Seasons to process: {seasons}")
    print(f"Skip load: {skip_load}")
    print(f"Only aggregates: {only_aggregates}")
    print(f"Refresh Matchplay data: {refresh_matchplay}")
    print(f"Restore matchplay from: {restore_matchplay or 'N/A'}")
    print("=" * 60)
    print()

    matchplay_backup_path = None
    original_link_count = 0

    # PRE-PIPELINE: Check for existing matchplay links
    if not skip_matchplay_check and not only_aggregates:
        print("PRE-PIPELINE: Checking for matchplay account links")
        print("-" * 40)

        has_links, link_count, _ = check_matchplay_links(etl_dir)
        original_link_count = link_count

        if has_links:
            print(f"  Found {link_count} matchplay account links in database")
            print()
            print("  WARNING: Running a full data load may affect these user-created links.")
            print("  Creating automatic backup...")
            print()

            success, result = backup_matchplay_data(etl_dir)
            if success:
                matchplay_backup_path = result
                print(f"  Backup saved to: {matchplay_backup_path}")
                print()
            else:
                print(f"  ERROR: Failed to backup matchplay links: {result}")
                print("  Use --skip-matchplay-check to proceed anyway (not recommended)")
                return False
        else:
            print("  No existing matchplay links found (or table doesn't exist)")
        print()

    all_success = True

    # Step 1: Load season data (unless skipped)
    if not skip_load and not only_aggregates:
        print("STEP 1: Loading Season Data")
        print("-" * 40)
        for season in seasons:
            print(f"\n  Loading season {season}...")
            if not run_script("load_season.py", season=season, etl_dir=etl_dir):
                print(f"  ❌ Failed to load season {season}")
                all_success = False
                # Continue with other seasons
            else:
                print(f"  ✅ Season {season} loaded successfully")
        print()
    else:
        print("STEP 1: Loading Season Data - SKIPPED")
        print()

    # Post-load steps: deduplication and backfills (unless only running aggregates)
    if not only_aggregates:
        print("POST-LOAD: Data cleanup and backfills")
        print("-" * 40)
        for script_name, description in POST_LOAD_STEPS:
            print(f"  Running {script_name}...")
            if not run_script(script_name, etl_dir=etl_dir):
                print(f"  ❌ {description} failed")
                all_success = False
            else:
                print(f"  ✅ {description} completed")
        print()
    else:
        print("POST-LOAD: Data cleanup and backfills - SKIPPED (aggregates only)")
        print()

    # Steps 2-6: Aggregate calculations
    # Most require running once per season, some run once for all data
    steps_to_run = AGGREGATE_STEPS if only_aggregates else PIPELINE_STEPS[1:]
    step_num = 2

    for script_name, description, requires_season in steps_to_run:
        print(f"STEP {step_num}: {description}")
        print("-" * 40)

        if requires_season:
            # Run once per season
            for season in seasons:
                print(f"  Running {script_name} for season {season}...")
                if not run_script(script_name, season=season, etl_dir=etl_dir):
                    print(f"  ❌ {description} failed for season {season}")
                    all_success = False
                else:
                    print(f"  ✅ Season {season} completed")
        else:
            # Run once for all data
            print(f"  Running {script_name}...")
            if not run_script(script_name, etl_dir=etl_dir):
                print(f"  ❌ {description} failed")
                all_success = False
            else:
                print(f"  ✅ {description} completed")
        print()
        step_num += 1

    # External data refresh (optional)
    if refresh_matchplay:
        print("EXTERNAL DATA: Refreshing Matchplay.events data")
        print("-" * 40)
        for script_name, description in EXTERNAL_DATA_STEPS:
            print(f"  Running {script_name}...")
            if not run_script(script_name, etl_dir=etl_dir):
                print(f"  ⚠️  {description} failed (non-critical)")
                # Don't mark as failure - external data is optional
            else:
                print(f"  ✅ {description} completed")
        print()
    else:
        print("EXTERNAL DATA: Matchplay refresh - SKIPPED (use --refresh-matchplay to enable)")
        print()

    # POST-PIPELINE: Restore matchplay links if requested or if we backed them up
    restore_path = restore_matchplay or (Path(matchplay_backup_path) if matchplay_backup_path else None)

    if restore_path and not only_aggregates:
        print("POST-PIPELINE: Restoring matchplay account links")
        print("-" * 40)

        if not Path(restore_path).exists():
            print(f"  ERROR: Backup file not found: {restore_path}")
            all_success = False
        else:
            print(f"  Restoring from: {restore_path}")
            success, message = restore_matchplay_data(Path(restore_path), etl_dir)

            if success:
                print(f"  ✅ {message}")

                # Verify restoration
                print("  Verifying restoration...")
                verify_success, verify_message = verify_matchplay_restored(
                    etl_dir,
                    original_link_count if matchplay_backup_path else 0
                )
                if verify_success:
                    print(f"  ✅ {verify_message}")
                else:
                    print(f"  ⚠️  {verify_message}")
            else:
                print(f"  ❌ Restore failed: {message}")
                all_success = False
        print()
    elif matchplay_backup_path:
        print("POST-PIPELINE: Matchplay links backup available")
        print("-" * 40)
        print(f"  Backup location: {matchplay_backup_path}")
        print("  To restore manually, run:")
        print(f"  python etl/backup_matchplay_links.py --restore --input {matchplay_backup_path}")
        print()

    # Summary
    print("=" * 60)
    if all_success:
        print("✅ ETL Pipeline completed successfully!")
        if matchplay_backup_path or restore_path:
            print("✅ Matchplay account links preserved")
    else:
        print("⚠️  ETL Pipeline completed with errors")
    print("=" * 60)

    return all_success


def main():
    parser = argparse.ArgumentParser(
        description="Run the complete MNP ETL pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Load season 22 and run all calculations
    python etl/run_full_pipeline.py --seasons 22

    # Load multiple seasons
    python etl/run_full_pipeline.py --seasons 18 19 20 21 22

    # Load all available seasons
    python etl/run_full_pipeline.py --all-seasons

    # Only recalculate aggregates (skip loading)
    python etl/run_full_pipeline.py --only-aggregates

    # Skip loading, just run aggregates for specific seasons
    python etl/run_full_pipeline.py --seasons 22 --skip-load

    # Include Matchplay.events data refresh (requires MATCHPLAY_API_TOKEN)
    python etl/run_full_pipeline.py --seasons 22 --refresh-matchplay

    # Restore matchplay links from backup after pipeline
    python etl/run_full_pipeline.py --seasons 22 --restore-matchplay backups/matchplay_links_20260126.json

    # Skip matchplay check (not recommended for production)
    python etl/run_full_pipeline.py --seasons 22 --skip-matchplay-check
"""
    )

    parser.add_argument(
        "--seasons",
        type=int,
        nargs="+",
        help="Season numbers to load (e.g., --seasons 21 22)"
    )
    parser.add_argument(
        "--all-seasons",
        action="store_true",
        help=f"Load all available seasons ({AVAILABLE_SEASONS})"
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="Skip the load_season step (use when data already loaded)"
    )
    parser.add_argument(
        "--only-aggregates",
        action="store_true",
        help="Only run aggregate calculations (steps 2-6)"
    )
    parser.add_argument(
        "--refresh-matchplay",
        action="store_true",
        help="Refresh Matchplay.events data for linked players (requires MATCHPLAY_API_TOKEN)"
    )
    parser.add_argument(
        "--skip-matchplay-check",
        action="store_true",
        help="Skip the pre-pipeline matchplay links check (not recommended for production)"
    )
    parser.add_argument(
        "--restore-matchplay",
        type=Path,
        help="Restore matchplay links from specified backup file after pipeline completes"
    )

    args = parser.parse_args()

    # Determine which seasons to process
    if args.all_seasons:
        seasons = AVAILABLE_SEASONS
    elif args.seasons:
        seasons = args.seasons
    elif args.only_aggregates:
        seasons = []  # No seasons needed for aggregates-only
    else:
        parser.error("Must specify --seasons, --all-seasons, or --only-aggregates")

    # Validate seasons
    for season in seasons:
        if season not in AVAILABLE_SEASONS:
            print(f"Warning: Season {season} not in known seasons {AVAILABLE_SEASONS}")

    # Get the ETL directory
    etl_dir = Path(__file__).parent

    # Run the pipeline
    success = run_pipeline(
        seasons=seasons,
        skip_load=args.skip_load,
        only_aggregates=args.only_aggregates,
        refresh_matchplay=args.refresh_matchplay,
        skip_matchplay_check=args.skip_matchplay_check,
        restore_matchplay=args.restore_matchplay,
        etl_dir=etl_dir
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
