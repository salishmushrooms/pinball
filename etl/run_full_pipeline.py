#!/usr/bin/env python3
"""
MNP ETL Full Pipeline Runner

Runs all ETL steps in the correct order to fully populate the database.
This is the single source of truth for the complete ETL pipeline.

Usage:
    # Load specific seasons
    python etl/run_full_pipeline.py --seasons 22
    python etl/run_full_pipeline.py --seasons 20 21 22 23

    # Load all available seasons (20-23)
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

Logging:
    All pipeline output (including subprocess output) is written to both the
    console and a timestamped log file in etl/logs/. Old log files are
    automatically cleaned up (keeps the most recent 10 by default).
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Available seasons in the data archive
# IMPORTANT: Keep this in sync with production database!
# Seasons 18-19 exist in archive but are excluded from aggregations.
# Production currently has seasons 20-23.
AVAILABLE_SEASONS = [20, 21, 22, 23]

# ETL scripts in execution order
# Format: (script_name, description, requires_season_arg, latest_season_only)
# latest_season_only: if True, only runs for the most recent season (not all)
PIPELINE_STEPS = [
    ("load_season.py", "Load raw match data", True, False),
    ("calculate_percentiles.py", "Calculate score percentiles", True, True),
    ("calculate_player_stats.py", "Calculate player statistics", True, False),
    ("calculate_team_machine_picks.py", "Calculate team machine picks", True, False),
    (
        "calculate_player_totals.py",
        "Calculate player totals",
        False,
        False,
    ),  # This one processes all seasons at once
    ("calculate_match_points.py", "Calculate match points", True, False),
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

# Log rotation: keep this many recent log files
MAX_LOG_FILES = 10


class PipelineLogger:
    """Writes output to both console and a log file."""

    def __init__(self, log_dir: Path):
        log_dir.mkdir(exist_ok=True)
        self._rotate_logs(log_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path = log_dir / f"pipeline_{timestamp}.log"
        self._file = open(self.log_path, "w")  # noqa: SIM115

    def _rotate_logs(self, log_dir: Path):
        """Delete old log files, keeping only the most recent MAX_LOG_FILES."""
        log_files = sorted(log_dir.glob("pipeline_*.log"), key=lambda p: p.stat().st_mtime)
        files_to_remove = log_files[: max(0, len(log_files) - MAX_LOG_FILES + 1)]
        for f in files_to_remove:
            f.unlink()

    def log(self, message: str = ""):
        """Print to console and write to log file."""
        print(message)
        self._file.write(message + "\n")
        self._file.flush()

    def log_subprocess_line(self, line: str):
        """Write a subprocess output line to both console and log file."""
        sys.stdout.write(line)
        sys.stdout.flush()
        self._file.write(line)
        self._file.flush()

    def close(self):
        self._file.close()


def check_matchplay_links(etl_dir: Path) -> tuple[bool, int, str]:
    """
    Check if matchplay links exist in the database.

    Returns:
        tuple: (has_links: bool, count: int, backup_path: str or None)
    """
    try:
        # Import the backup module
        sys.path.insert(0, str(etl_dir.parent))
        from etl.backup_matchplay_links import verify_matchplay_links

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
        from etl.backup_matchplay_links import BACKUP_DIR, backup_matchplay_links

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
            return (
                True,
                f"Verified {actual_count} matchplay links restored (expected {expected_count})",
            )
        elif actual_count > 0:
            return True, f"Partial restore: {actual_count} links (expected {expected_count})"
        else:
            return False, f"No matchplay links found after restore (expected {expected_count})"
    except Exception as e:
        return False, str(e)


def run_script(
    script_name: str,
    season: int = None,
    etl_dir: Path = None,
    logger: PipelineLogger = None,
) -> bool:
    """Run a single ETL script, streaming output to console and log file."""
    log = logger.log if logger else print

    script_path = etl_dir / script_name

    if not script_path.exists():
        log(f"  ❌ Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if season is not None:
        cmd.extend(["--season", str(season)])

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=etl_dir.parent,
            text=True,
        )
        for line in proc.stdout:
            if logger:
                logger.log_subprocess_line(line)
            else:
                sys.stdout.write(line)
        proc.wait()
        if proc.returncode != 0:
            log(f"  ❌ Failed with exit code {proc.returncode}")
            return False
        return True
    except Exception as e:
        log(f"  ❌ Failed: {e}")
        return False


def run_pipeline(  # noqa: C901
    seasons: list[int],
    skip_load: bool = False,
    only_aggregates: bool = False,
    refresh_matchplay: bool = False,
    skip_matchplay_check: bool = False,
    restore_matchplay: Path = None,
    etl_dir: Path = None,
    logger: PipelineLogger = None,
) -> bool:
    """Run the full ETL pipeline for the specified seasons."""
    log = logger.log if logger else print

    log("=" * 60)
    log("MNP ETL Full Pipeline")
    log("=" * 60)
    log(f"Seasons to process: {seasons}")
    log(f"Skip load: {skip_load}")
    log(f"Only aggregates: {only_aggregates}")
    log(f"Refresh Matchplay data: {refresh_matchplay}")
    log(f"Restore matchplay from: {restore_matchplay or 'N/A'}")
    if logger:
        log(f"Log file: {logger.log_path}")
    log("=" * 60)
    log()

    matchplay_backup_path = None
    original_link_count = 0

    # PRE-PIPELINE: Check for existing matchplay links
    if not skip_matchplay_check and not only_aggregates:
        log("PRE-PIPELINE: Checking for matchplay account links")
        log("-" * 40)

        has_links, link_count, _ = check_matchplay_links(etl_dir)
        original_link_count = link_count

        if has_links:
            log(f"  Found {link_count} matchplay account links in database")
            log()
            log("  WARNING: Running a full data load may affect these user-created links.")
            log("  Creating automatic backup...")
            log()

            success, result = backup_matchplay_data(etl_dir)
            if success:
                matchplay_backup_path = result
                log(f"  Backup saved to: {matchplay_backup_path}")
                log()
            else:
                log(f"  ERROR: Failed to backup matchplay links: {result}")
                log("  Use --skip-matchplay-check to proceed anyway (not recommended)")
                return False
        else:
            log("  No existing matchplay links found (or table doesn't exist)")
        log()

    all_success = True

    # Step 1: Load season data (unless skipped)
    if not skip_load and not only_aggregates:
        log("STEP 1: Loading Season Data")
        log("-" * 40)
        for season in seasons:
            log(f"\n  Loading season {season}...")
            if not run_script("load_season.py", season=season, etl_dir=etl_dir, logger=logger):
                log(f"  ❌ Failed to load season {season}")
                all_success = False
                # Continue with other seasons
            else:
                log(f"  ✅ Season {season} loaded successfully")
        log()
    else:
        log("STEP 1: Loading Season Data - SKIPPED")
        log()

    # Post-load steps: deduplication and backfills (unless only running aggregates)
    if not only_aggregates:
        log("POST-LOAD: Data cleanup and backfills")
        log("-" * 40)
        for script_name, description in POST_LOAD_STEPS:
            log(f"  Running {script_name}...")
            if not run_script(script_name, etl_dir=etl_dir, logger=logger):
                log(f"  ❌ {description} failed")
                all_success = False
            else:
                log(f"  ✅ {description} completed")
        log()
    else:
        log("POST-LOAD: Data cleanup and backfills - SKIPPED (aggregates only)")
        log()

    # Steps 2-6: Aggregate calculations
    # Most require running once per season, some run once for all data
    steps_to_run = AGGREGATE_STEPS if only_aggregates else PIPELINE_STEPS[1:]
    step_num = 2

    for script_name, description, requires_season, latest_only in steps_to_run:
        log(f"STEP {step_num}: {description}")
        log("-" * 40)

        if requires_season:
            # Run for latest season only or all seasons
            target_seasons = [max(seasons)] if latest_only and seasons else seasons
            if latest_only and len(seasons) > 1:
                log(f"  (latest season only: {max(seasons)})")
            for season in target_seasons:
                log(f"  Running {script_name} for season {season}...")
                if not run_script(script_name, season=season, etl_dir=etl_dir, logger=logger):
                    log(f"  ❌ {description} failed for season {season}")
                    all_success = False
                else:
                    log(f"  ✅ Season {season} completed")
        else:
            # Run once for all data
            log(f"  Running {script_name}...")
            if not run_script(script_name, etl_dir=etl_dir, logger=logger):
                log(f"  ❌ {description} failed")
                all_success = False
            else:
                log(f"  ✅ {description} completed")
        log()
        step_num += 1

    # External data refresh (optional)
    if refresh_matchplay:
        log("EXTERNAL DATA: Refreshing Matchplay.events data")
        log("-" * 40)
        for script_name, description in EXTERNAL_DATA_STEPS:
            log(f"  Running {script_name}...")
            if not run_script(script_name, etl_dir=etl_dir, logger=logger):
                log(f"  ⚠️  {description} failed (non-critical)")
                # Don't mark as failure - external data is optional
            else:
                log(f"  ✅ {description} completed")
        log()
    else:
        log("EXTERNAL DATA: Matchplay refresh - SKIPPED (use --refresh-matchplay to enable)")
        log()

    # POST-PIPELINE: Restore matchplay links if requested or if we backed them up
    restore_path = restore_matchplay or (
        Path(matchplay_backup_path) if matchplay_backup_path else None
    )

    if restore_path and not only_aggregates:
        log("POST-PIPELINE: Restoring matchplay account links")
        log("-" * 40)

        if not Path(restore_path).exists():
            log(f"  ERROR: Backup file not found: {restore_path}")
            all_success = False
        else:
            log(f"  Restoring from: {restore_path}")
            success, message = restore_matchplay_data(Path(restore_path), etl_dir)

            if success:
                log(f"  ✅ {message}")

                # Verify restoration
                log("  Verifying restoration...")
                verify_success, verify_message = verify_matchplay_restored(
                    etl_dir, original_link_count if matchplay_backup_path else 0
                )
                if verify_success:
                    log(f"  ✅ {verify_message}")
                else:
                    log(f"  ⚠️  {verify_message}")
            else:
                log(f"  ❌ Restore failed: {message}")
                all_success = False
        log()
    elif matchplay_backup_path:
        log("POST-PIPELINE: Matchplay links backup available")
        log("-" * 40)
        log(f"  Backup location: {matchplay_backup_path}")
        log("  To restore manually, run:")
        log(f"  python etl/backup_matchplay_links.py --restore --input {matchplay_backup_path}")
        log()

    # Summary
    log("=" * 60)
    if all_success:
        log("✅ ETL Pipeline completed successfully!")
        if matchplay_backup_path or restore_path:
            log("✅ Matchplay account links preserved")
    else:
        log("⚠️  ETL Pipeline completed with errors")
    if logger:
        log(f"Full log: {logger.log_path}")
    log("=" * 60)

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
""",
    )

    parser.add_argument(
        "--seasons", type=int, nargs="+", help="Season numbers to load (e.g., --seasons 21 22)"
    )
    parser.add_argument(
        "--all-seasons",
        action="store_true",
        help=f"Load all available seasons ({AVAILABLE_SEASONS})",
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="Skip the load_season step (use when data already loaded)",
    )
    parser.add_argument(
        "--only-aggregates", action="store_true", help="Only run aggregate calculations (steps 2-6)"
    )
    parser.add_argument(
        "--refresh-matchplay",
        action="store_true",
        help="Refresh Matchplay.events data for linked players (requires MATCHPLAY_API_TOKEN)",
    )
    parser.add_argument(
        "--skip-matchplay-check",
        action="store_true",
        help="Skip the pre-pipeline matchplay links check (not recommended for production)",
    )
    parser.add_argument(
        "--restore-matchplay",
        type=Path,
        help="Restore matchplay links from specified backup file after pipeline completes",
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

    # Set up logging to file
    logger = PipelineLogger(etl_dir / "logs")
    print(f"Logging to: {logger.log_path}")

    try:
        # Run the pipeline
        success = run_pipeline(
            seasons=seasons,
            skip_load=args.skip_load,
            only_aggregates=args.only_aggregates,
            refresh_matchplay=args.refresh_matchplay,
            skip_matchplay_check=args.skip_matchplay_check,
            restore_matchplay=args.restore_matchplay,
            etl_dir=etl_dir,
            logger=logger,
        )
    finally:
        logger.close()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
