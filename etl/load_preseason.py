#!/usr/bin/env python3
"""
Preseason ETL script for loading MNP season metadata before matches are played.

This script loads:
- Venues (from venues.csv and venues.json)
- Teams (from teams.csv)
- Players (from rosters.csv)
- Planned matches (from matches.csv)

It does NOT require the matches/ directory with played match JSON files.

Usage:
    python etl/load_preseason.py --season 23
    python etl/load_preseason.py --season 23 --verbose
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from etl.config import config
from etl.database import db
from etl.parsers.machine_parser import MachineParser
from etl.loaders.db_loader import DatabaseLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def generate_player_key(name: str) -> str:
    """
    Generate a player key from name (lowercase, spaces replaced with underscores).

    Note: This is only used as a fallback when the player doesn't already exist
    in the database. The load_preseason_data function will first check for
    existing players by name to preserve their original keys.
    """
    return name.strip().lower().replace(' ', '_').replace('.', '').replace("'", '')


def load_preseason_data(season: int):
    """Load preseason metadata for a season"""

    logger.info("=" * 60)
    logger.info(f"Starting Preseason ETL for Season {season}")
    logger.info("=" * 60)

    # Initialize components
    machine_parser = MachineParser(config.MACHINE_VARIATIONS_FILE)
    loader = DatabaseLoader()

    # Check if season path exists
    season_path = config.get_season_path(season)

    if not season_path.exists():
        logger.error(f"Season data directory not found: {season_path}")
        return False

    logger.info(f"Data path: {season_path}")
    logger.info("")

    # Step 1: Load machine variations (needed for all seasons)
    logger.info("Step 1: Loading machine variations...")
    try:
        machine_parser.load()
        machine_parser.build_alias_map()

        machines = machine_parser.extract_machines()
        aliases = machine_parser.extract_aliases()

        loader.load_machines(machines)
        loader.load_machine_aliases(aliases)
        logger.info(f"  Loaded {len(machines)} machines and {len(aliases)} aliases")
    except Exception as e:
        logger.error(f"Failed to load machines: {e}")
        return False

    logger.info("")

    # Step 2: Load venues from venues.csv and venues.json
    logger.info("Step 2: Loading venues...")
    venues_loaded = 0
    try:
        venues_csv = season_path / "venues.csv"
        venues_json_path = config.DATA_PATH / "venues.json"

        # Load venue metadata from venues.json
        venue_metadata = {}
        if venues_json_path.exists():
            with open(venues_json_path, 'r') as f:
                venues_data = json.load(f)
                for venue_key, venue_info in venues_data.items():
                    venue_metadata[venue_key] = {
                        'venue_name': venue_info.get('name', venue_key),
                        'address': venue_info.get('address', ''),
                        'neighborhood': venue_info.get('neighborhood', '')
                    }
            logger.info(f"  Loaded metadata for {len(venue_metadata)} venues from venues.json")

        # Load venues from venues.csv
        venues = []
        if venues_csv.exists():
            with open(venues_csv, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        venue_key = row[0].strip()
                        venue_name = row[1].strip()

                        venue = {
                            'venue_key': venue_key,
                            'venue_name': venue_name,
                            'address': None,
                            'neighborhood': None,
                            'active': True
                        }

                        # Enrich with metadata from venues.json
                        if venue_key in venue_metadata:
                            venue['address'] = venue_metadata[venue_key].get('address') or None
                            venue['neighborhood'] = venue_metadata[venue_key].get('neighborhood') or None

                        venues.append(venue)

            loader.load_venues(venues)
            venues_loaded = len(venues)
            logger.info(f"  Loaded {venues_loaded} venues from venues.csv")
        else:
            logger.warning(f"  venues.csv not found at {venues_csv}")

    except Exception as e:
        logger.error(f"Failed to load venues: {e}")
        return False

    logger.info("")

    # Step 3: Load teams from teams.csv
    logger.info("Step 3: Loading teams...")
    teams_loaded = 0
    try:
        teams_csv = season_path / "teams.csv"
        teams = []

        if teams_csv.exists():
            with open(teams_csv, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 3:
                        team_key = row[0].strip()
                        home_venue_key = row[1].strip()
                        team_name = row[2].strip()

                        teams.append({
                            'team_key': team_key,
                            'season': season,
                            'team_name': team_name,
                            'home_venue_key': home_venue_key
                        })

            loader.load_teams(teams)
            teams_loaded = len(teams)
            logger.info(f"  Loaded {teams_loaded} teams from teams.csv")
        else:
            logger.warning(f"  teams.csv not found at {teams_csv}")

    except Exception as e:
        logger.error(f"Failed to load teams: {e}")
        return False

    logger.info("")

    # Step 4: Load players from rosters.csv
    logger.info("Step 4: Loading players from rosters...")
    players_loaded = 0
    players_reused = 0
    try:
        rosters_csv = season_path / "rosters.csv"
        players = {}

        if rosters_csv.exists():
            # First, get all existing player name -> key mappings to avoid duplicates
            existing_players = loader.get_all_player_keys_by_name()
            logger.info(f"  Found {len(existing_players)} existing players in database")

            with open(rosters_csv, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        player_name = row[0].strip()
                        # team_key = row[1].strip()  # Not used for player creation
                        # role = row[2].strip() if len(row) >= 3 else 'P'  # P=Player, C=Captain, A=Alternate

                        # Check if player already exists by name - reuse their key
                        if player_name in existing_players:
                            player_key = existing_players[player_name]
                            players_reused += 1
                        else:
                            # Generate new key only for truly new players
                            player_key = generate_player_key(player_name)

                        if player_key not in players:
                            players[player_key] = {
                                'player_key': player_key,
                                'name': player_name,
                                'current_ipr': None,
                                'first_seen_season': season,
                                'last_seen_season': season
                            }

            loader.load_players(list(players.values()))
            players_loaded = len(players)
            logger.info(f"  Loaded {players_loaded} players from rosters.csv ({players_reused} reused existing keys)")
        else:
            logger.warning(f"  rosters.csv not found at {rosters_csv}")

    except Exception as e:
        logger.error(f"Failed to load players: {e}")
        return False

    logger.info("")

    # Step 5: Load planned matches from matches.csv
    logger.info("Step 5: Loading planned matches...")
    matches_loaded = 0
    try:
        matches_csv = season_path / "matches.csv"
        matches = []

        if matches_csv.exists():
            with open(matches_csv, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 5:
                        week = int(row[0].strip())
                        date_str = row[1].strip()  # Format: YYYYMMDD
                        away_team_key = row[2].strip()
                        home_team_key = row[3].strip()
                        venue_key = row[4].strip()

                        # Parse date
                        try:
                            date = datetime.strptime(date_str, '%Y%m%d').date()
                        except ValueError:
                            date = None

                        # Generate match key (format must match JSON file keys: mnp-{season}-{week}-{AWAY}-{HOME})
                        match_key = f"mnp-{season}-{week}-{away_team_key}-{home_team_key}"

                        matches.append({
                            'match_key': match_key,
                            'season': season,
                            'week': week,
                            'date': date,
                            'venue_key': venue_key,
                            'home_team_key': home_team_key,
                            'away_team_key': away_team_key,
                            'state': 'scheduled'  # Preseason matches are scheduled, not completed
                        })

            loader.load_matches(matches)
            matches_loaded = len(matches)
            logger.info(f"  Loaded {matches_loaded} planned matches from matches.csv")
        else:
            logger.warning(f"  matches.csv not found at {matches_csv}")

    except Exception as e:
        logger.error(f"Failed to load matches: {e}")
        return False

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"Preseason ETL Complete for Season {season}!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Summary:")
    logger.info(f"  Machines: {len(machines)}")
    logger.info(f"  Venues: {venues_loaded}")
    logger.info(f"  Teams: {teams_loaded}")
    logger.info(f"  Players: {players_loaded}")
    logger.info(f"  Planned Matches: {matches_loaded}")
    logger.info("")

    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Load MNP preseason metadata into database'
    )
    parser.add_argument(
        '--season',
        type=int,
        required=True,
        help='Season number to load (e.g., 23)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Connect to database
    try:
        db.connect()
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    # Load preseason data
    success = load_preseason_data(args.season)

    # Close database connection
    db.close()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
