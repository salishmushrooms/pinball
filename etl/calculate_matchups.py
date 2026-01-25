#!/usr/bin/env python3
"""
Pre-calculate matchup analysis for upcoming matches.

This script:
1. Identifies the next unplayed week for the current season
2. Calculates matchup analysis for each scheduled match in that week
3. Stores results in pre_calculated_matchups table

Usage:
    python etl/calculate_matchups.py --season 23           # Next week only (default)
    python etl/calculate_matchups.py --season 23 --week 1  # Specific week
    python etl/calculate_matchups.py --season 23 --all-upcoming  # All future weeks
    python etl/calculate_matchups.py --season 23 --verbose
"""

import argparse
import logging
import sys
import json
from typing import List, Dict, Optional
from sqlalchemy import text

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


def get_next_incomplete_week(season: int) -> Optional[int]:
    """
    Find the first week with scheduled (incomplete) matches.
    Returns None if all matches are complete.
    """
    query = """
        SELECT MIN(week) as next_week
        FROM matches
        WHERE season = :season
        AND state = 'scheduled'
    """
    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        row = result.fetchone()

    return row[0] if row and row[0] is not None else None


def get_all_upcoming_weeks(season: int) -> List[int]:
    """
    Get all weeks with scheduled matches.
    Returns list of week numbers.
    """
    query = """
        SELECT DISTINCT week
        FROM matches
        WHERE season = :season
        AND state = 'scheduled'
        ORDER BY week
    """
    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        rows = result.fetchall()

    return [row[0] for row in rows]


def get_scheduled_matches(season: int, week: int) -> List[Dict]:
    """
    Get all scheduled matches for a specific week.
    Returns match details needed for analysis.
    """
    query = """
        SELECT
            m.match_key,
            m.home_team_key,
            m.away_team_key,
            m.venue_key,
            v.venue_name
        FROM matches m
        JOIN venues v ON m.venue_key = v.venue_key
        WHERE m.season = :season
        AND m.week = :week
        AND m.state = 'scheduled'
        ORDER BY m.match_key
    """
    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season, 'week': week})
        return [dict(row._mapping) for row in result.fetchall()]


def calculate_matchup_analysis(match: Dict, seasons: List[int]) -> Optional[Dict]:
    """
    Calculate complete matchup analysis for a match.
    Uses the shared service module.
    """
    # Import here to avoid circular imports and ensure API module is available
    try:
        from api.services.matchup_calculator import calculate_full_matchup_analysis
    except ImportError:
        logger.error("Failed to import matchup calculator service. Ensure API module is in path.")
        return None

    return calculate_full_matchup_analysis(
        home_team=match['home_team_key'],
        away_team=match['away_team_key'],
        venue=match['venue_key'],
        seasons=seasons
    )


def store_matchup_analysis(
    match_key: str,
    season: int,
    week: int,
    match: Dict,
    analysis: Dict,
    seasons: List[int]
):
    """Store pre-calculated matchup in database."""
    query = """
        INSERT INTO pre_calculated_matchups (
            match_key, season, week,
            home_team_key, away_team_key, venue_key,
            seasons_analyzed, analysis_data,
            calculated_at, last_calculated
        )
        VALUES (
            :match_key, :season, :week,
            :home_team_key, :away_team_key, :venue_key,
            :seasons_analyzed, :analysis_data,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT (match_key)
        DO UPDATE SET
            analysis_data = EXCLUDED.analysis_data,
            seasons_analyzed = EXCLUDED.seasons_analyzed,
            last_calculated = CURRENT_TIMESTAMP
    """

    with db.engine.begin() as conn:
        conn.execute(text(query), {
            'match_key': match_key,
            'season': season,
            'week': week,
            'home_team_key': match['home_team_key'],
            'away_team_key': match['away_team_key'],
            'venue_key': match['venue_key'],
            'seasons_analyzed': seasons,
            'analysis_data': json.dumps(analysis),
        })


def clear_completed_matchups(season: int):
    """Remove pre-calculated data for completed matches."""
    query = """
        DELETE FROM pre_calculated_matchups pcm
        WHERE pcm.season = :season
        AND EXISTS (
            SELECT 1 FROM matches m
            WHERE m.match_key = pcm.match_key
            AND m.state = 'complete'
        )
    """
    with db.engine.begin() as conn:
        result = conn.execute(text(query), {'season': season})
        return result.rowcount


def calculate_and_store_matchups(
    season: int,
    week: Optional[int] = None,
    all_upcoming: bool = False
):
    """
    Main function to pre-calculate matchup data.
    """
    logger.info("=" * 60)
    logger.info(f"Pre-Calculating Matchup Data for Season {season}")
    logger.info("=" * 60)

    # Determine which week(s) to process
    if week is not None:
        weeks_to_process = [week]
        logger.info(f"Processing specific week: {week}")
    elif all_upcoming:
        weeks_to_process = get_all_upcoming_weeks(season)
        logger.info(f"Processing all upcoming weeks: {weeks_to_process}")
    else:
        next_week = get_next_incomplete_week(season)
        if next_week is None:
            logger.info("No scheduled matches found - season may be complete")
            return True
        weeks_to_process = [next_week]
        logger.info(f"Processing next incomplete week: {next_week}")

    if not weeks_to_process:
        logger.info("No weeks to process")
        return True

    # Default seasons for analysis: current + previous
    seasons_to_analyze = [season, season - 1]
    logger.info(f"Analyzing seasons: {seasons_to_analyze}")

    total_calculated = 0
    total_skipped = 0

    for process_week in weeks_to_process:
        logger.info("")
        logger.info(f"Processing Week {process_week}...")

        matches = get_scheduled_matches(season, process_week)

        if not matches:
            logger.info(f"  No scheduled matches in week {process_week}")
            continue

        logger.info(f"  Found {len(matches)} scheduled matches")

        for match in matches:
            match_key = match['match_key']
            logger.info(f"  Calculating: {match_key}")

            try:
                analysis = calculate_matchup_analysis(match, seasons_to_analyze)

                if analysis is None:
                    logger.warning(f"    Skipped - insufficient data for {match['venue_key']}")
                    total_skipped += 1
                    continue

                store_matchup_analysis(
                    match_key, season, process_week,
                    match, analysis, seasons_to_analyze
                )
                total_calculated += 1
                logger.info(f"    Stored successfully")

            except Exception as e:
                logger.error(f"    Error: {e}")
                total_skipped += 1

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Pre-calculation complete!")
    logger.info(f"  Matches calculated: {total_calculated}")
    logger.info(f"  Matches skipped: {total_skipped}")
    logger.info("=" * 60)

    return True


def verify_matchups(season: int):
    """Verify that matchups were calculated correctly."""
    logger.info("")
    logger.info("Verifying pre-calculated matchups...")

    query = """
        SELECT
            COUNT(*) as total_records,
            COUNT(DISTINCT home_team_key) as unique_home_teams,
            COUNT(DISTINCT away_team_key) as unique_away_teams,
            COUNT(DISTINCT venue_key) as unique_venues,
            MIN(week) as min_week,
            MAX(week) as max_week
        FROM pre_calculated_matchups
        WHERE season = :season
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        row = result.fetchone()

    if row:
        logger.info(f"  Total records: {row[0]}")
        logger.info(f"  Unique home teams: {row[1]}")
        logger.info(f"  Unique away teams: {row[2]}")
        logger.info(f"  Unique venues: {row[3]}")
        if row[4] is not None:
            logger.info(f"  Week range: {row[4]} - {row[5]}")

    # Show individual matches
    logger.info("")
    logger.info("Pre-calculated matches:")

    query = """
        SELECT
            match_key,
            home_team_key,
            away_team_key,
            venue_key,
            week,
            last_calculated
        FROM pre_calculated_matchups
        WHERE season = :season
        ORDER BY week, match_key
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        rows = result.fetchall()

    for row in rows:
        match_key, home, away, venue, week, calculated = row
        logger.info(f"  Week {week}: {away} @ {home} ({venue}) - calculated {calculated}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Pre-calculate matchup analysis')
    parser.add_argument('--season', type=int, required=True, help='Season number (e.g., 24)')
    parser.add_argument('--week', type=int, help='Specific week to calculate (default: next incomplete)')
    parser.add_argument('--all-upcoming', action='store_true', help='Calculate all upcoming weeks')
    parser.add_argument('--cleanup', action='store_true', help='Remove completed match data')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Connect to database
        db.connect()

        # Optional: cleanup completed matches
        if args.cleanup:
            deleted = clear_completed_matchups(args.season)
            logger.info(f"Cleaned up {deleted} completed match records")

        # Calculate matchups
        success = calculate_and_store_matchups(
            args.season,
            week=args.week,
            all_upcoming=args.all_upcoming
        )

        if not success:
            return 1

        # Verify results
        verify_matchups(args.season)

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
