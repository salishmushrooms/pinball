#!/usr/bin/env python3
"""
Update team home_venue_key from season CSV files.

This script reads the teams.csv file from a season directory
and updates the database with the correct home_venue_key for each team.

The teams.csv file has the format: team_key,venue_key,team_name
For example: ADB,ADM,Admiraballs

Usage:
    python etl/update_team_venues.py --season 22
    python etl/update_team_venues.py --season 22 --verbose
"""

import argparse
import csv
import logging
import sys
from pathlib import Path

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


def load_teams_csv(season: int) -> dict:
    """Load team-venue mappings from teams.csv

    Returns:
        dict: {team_key: {'venue_key': str, 'team_name': str}}
    """
    teams_file = config.get_season_path(season) / "teams.csv"

    if not teams_file.exists():
        logger.warning(f"teams.csv not found at {teams_file}")
        return {}

    teams = {}
    with open(teams_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                team_key = row[0].strip()
                venue_key = row[1].strip()
                team_name = row[2].strip()
                teams[team_key] = {
                    'venue_key': venue_key,
                    'team_name': team_name
                }

    logger.info(f"Loaded {len(teams)} team-venue mappings from teams.csv")
    return teams


def update_team_venues(season: int, team_venues: dict):
    """Update home_venue_key for teams in the database"""
    if not team_venues:
        logger.warning("No team-venue mappings to update")
        return 0

    updated = 0
    for team_key, info in team_venues.items():
        venue_key = info['venue_key']

        result = db.execute(
            """
            UPDATE teams
            SET home_venue_key = :venue_key
            WHERE team_key = :team_key AND season = :season
            """,
            {'venue_key': venue_key, 'team_key': team_key, 'season': season}
        )

        if result.rowcount > 0:
            updated += 1
            logger.debug(f"Updated {team_key} -> venue {venue_key}")

    logger.info(f"Updated home_venue_key for {updated} teams")
    return updated


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Update team home venues from season CSV files'
    )
    parser.add_argument(
        '--season',
        type=int,
        required=True,
        help='Season number to update (e.g., 22)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"=" * 60)
    logger.info(f"Updating team venues for Season {args.season}")
    logger.info(f"=" * 60)

    # Connect to database
    try:
        db.connect()
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    # Load CSV data
    team_venues = load_teams_csv(args.season)

    # Update team venues
    updated_venues = update_team_venues(args.season, team_venues)

    # Close database connection
    db.close()

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Update Complete for Season {args.season}!")
    logger.info("=" * 60)
    logger.info(f"  Team venues updated: {updated_venues}")
    logger.info("")

    sys.exit(0)


if __name__ == '__main__':
    main()
