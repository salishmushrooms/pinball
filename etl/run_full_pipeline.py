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

Verification:
    After running the pipeline, verify aggregations with:
    python etl/verify_team_machine_picks.py --all-seasons

Note: Steps 2-6 are aggregate calculations that depend on step 1 and post-load steps.
"""

import argparse
import subprocess
import sys
from pathlib import Path

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
    print("=" * 60)
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

    # Summary
    print("=" * 60)
    if all_success:
        print("✅ ETL Pipeline completed successfully!")
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
        etl_dir=etl_dir
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
