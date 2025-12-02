#!/usr/bin/env python3
"""
Calculate and update match point totals (home_team_points, away_team_points).

This script calculates the total points for each team in a match by summing
the away_points and home_points from each game in all rounds.

MNP Scoring:
- Each game awards points based on head-to-head position finishes
- Singles (Rounds 2 & 3): 3 points per game (winner takes all or split)
- Doubles (Rounds 1 & 4): 5 points per game (based on position finishes)
- Match total is sum of all game points across all 4 rounds

Usage:
    python etl/calculate_match_points.py --season 22
    python etl/calculate_match_points.py --season 22 --verbose
"""

import argparse
import json
import logging
import sys
from pathlib import Path
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


def load_match_files(season: int):
    """
    Load all match JSON files for a season.

    Args:
        season: Season number

    Returns:
        list: List of match data dictionaries
    """
    matches_path = config.get_matches_path(season)

    if not matches_path.exists():
        logger.error(f"Matches path does not exist: {matches_path}")
        return []

    matches = []
    for match_file in matches_path.glob("*.json"):
        try:
            with open(match_file, 'r') as f:
                match_data = json.load(f)
                matches.append(match_data)
        except Exception as e:
            logger.warning(f"Failed to load {match_file}: {e}")

    logger.info(f"Loaded {len(matches)} match files from {matches_path}")
    return matches


def calculate_match_points(match_data: dict):
    """
    Calculate total points for home and away teams from match data.

    Args:
        match_data: Match dictionary from JSON file

    Returns:
        tuple: (match_key, home_points, away_points) or None if incomplete
    """
    match_key = match_data.get('key')
    state = match_data.get('state', '')

    # Only process complete matches
    if state != 'complete':
        return None

    home_points = 0.0
    away_points = 0.0

    rounds = match_data.get('rounds', [])

    for round_data in rounds:
        games = round_data.get('games', [])

        for game in games:
            # Sum up points from each game
            game_home = game.get('home_points', 0) or 0
            game_away = game.get('away_points', 0) or 0

            home_points += float(game_home)
            away_points += float(game_away)

    return (match_key, home_points, away_points)


def update_match_points(match_points: list):
    """
    Update matches table with calculated point totals.

    Args:
        match_points: List of (match_key, home_points, away_points) tuples
    """
    logger.info(f"Updating {len(match_points)} matches with point totals...")

    query = """
        UPDATE matches
        SET home_team_points = :home_points,
            away_team_points = :away_points,
            updated_at = CURRENT_TIMESTAMP
        WHERE match_key = :match_key
    """

    updated = 0

    with db.engine.begin() as conn:
        for match_key, home_points, away_points in match_points:
            result = conn.execute(text(query), {
                'match_key': match_key,
                'home_points': home_points,
                'away_points': away_points
            })
            if result.rowcount > 0:
                updated += 1

    logger.info(f"✓ Updated point totals for {updated} matches")
    return updated


def calculate_and_store_match_points(season: int):
    """
    Main function to calculate and store match point totals.

    Args:
        season: Season number
    """
    logger.info("=" * 60)
    logger.info(f"Calculating Match Point Totals for Season {season}")
    logger.info("=" * 60)

    # Step 1: Load match files
    matches = load_match_files(season)

    if not matches:
        logger.error("No match files found!")
        return False

    # Step 2: Calculate points for each match
    match_points = []
    incomplete = 0

    for match_data in matches:
        result = calculate_match_points(match_data)
        if result:
            match_points.append(result)
        else:
            incomplete += 1

    logger.info(f"Calculated points for {len(match_points)} complete matches")
    if incomplete > 0:
        logger.info(f"Skipped {incomplete} incomplete matches")

    # Step 3: Update database
    if match_points:
        update_match_points(match_points)

    logger.info("")
    logger.info("=" * 60)
    logger.info("✓ Match points calculated successfully!")
    logger.info("=" * 60)

    return True


def verify_match_points(season: int):
    """Verify that match points were calculated correctly"""

    logger.info("")
    logger.info("Verifying match point totals...")

    query = """
        SELECT
            COUNT(*) as total_matches,
            COUNT(*) FILTER (WHERE home_team_points IS NOT NULL) as matches_with_points,
            AVG(home_team_points) as avg_home_points,
            AVG(away_team_points) as avg_away_points,
            COUNT(*) FILTER (WHERE home_team_points > away_team_points) as home_wins,
            COUNT(*) FILTER (WHERE away_team_points > home_team_points) as away_wins,
            COUNT(*) FILTER (WHERE home_team_points = away_team_points) as ties
        FROM matches
        WHERE season = :season
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        row = result.fetchone()

    if row:
        logger.info(f"  Total matches: {row[0]}")
        logger.info(f"  Matches with points: {row[1]}")
        if row[2]:
            logger.info(f"  Avg home points: {row[2]:.1f}")
            logger.info(f"  Avg away points: {row[3]:.1f}")
        logger.info(f"  Home wins: {row[4]}, Away wins: {row[5]}, Ties: {row[6]}")

    # Show sample matches
    logger.info("")
    logger.info("Sample match results:")

    query = """
        SELECT
            match_key,
            home_team_key,
            away_team_key,
            home_team_points,
            away_team_points,
            CASE
                WHEN home_team_points > away_team_points THEN home_team_key
                WHEN away_team_points > home_team_points THEN away_team_key
                ELSE 'TIE'
            END as winner
        FROM matches
        WHERE season = :season AND home_team_points IS NOT NULL
        ORDER BY week, match_key
        LIMIT 10
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        rows = result.fetchall()

    for row in rows:
        match_key, home, away, home_pts, away_pts, winner = row
        logger.info(f"  {match_key}: {home} {home_pts:.0f} - {away_pts:.0f} {away} (W: {winner})")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Calculate match point totals')
    parser.add_argument('--season', type=int, required=True, help='Season number (e.g., 22)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Connect to database
        db.connect()

        # Calculate match points
        success = calculate_and_store_match_points(args.season)

        if not success:
            return 1

        # Verify results
        verify_match_points(args.season)

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
