#!/usr/bin/env python3
"""
Main ETL script for loading MNP season data into the database.

Usage:
    python etl/load_season.py --season 22
    python etl/load_season.py --season 22 --verbose
"""

import argparse
import logging
import sys
from pathlib import Path

from etl.config import config
from etl.database import db
from etl.parsers.machine_parser import MachineParser
from etl.parsers.match_parser import MatchParser
from etl.parsers.ipr_parser import IPRParser
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


def load_season_data(season: int):
    """Load all data for a season"""

    logger.info(f"=" * 60)
    logger.info(f"Starting ETL for Season {season}")
    logger.info(f"=" * 60)

    # Initialize components
    machine_parser = MachineParser(config.MACHINE_VARIATIONS_FILE)
    match_parser = MatchParser()
    loader = DatabaseLoader()

    # Check if data paths exist
    season_path = config.get_season_path(season)
    matches_path = config.get_matches_path(season)

    if not season_path.exists():
        logger.error(f"Season data directory not found: {season_path}")
        return False

    if not matches_path.exists():
        logger.error(f"Matches directory not found: {matches_path}")
        return False

    logger.info(f"Data path: {season_path}")
    logger.info(f"Matches path: {matches_path}")
    logger.info("")

    # Step 1: Load machine variations
    logger.info("Step 1: Loading machine variations...")
    try:
        machine_parser.load()
        machine_parser.build_alias_map()

        machines = machine_parser.extract_machines()
        aliases = machine_parser.extract_aliases()

        loader.load_machines(machines)
        loader.load_machine_aliases(aliases)
        logger.info(f"✓ Loaded {len(machines)} machines and {len(aliases)} aliases")
    except Exception as e:
        logger.error(f"Failed to load machines: {e}")
        return False

    logger.info("")

    # Step 2: Load all matches
    logger.info("Step 2: Loading match files...")
    try:
        matches = match_parser.load_all_matches(matches_path)

        if not matches:
            logger.error("No matches found!")
            return False

        logger.info(f"✓ Loaded {len(matches)} match files")
    except Exception as e:
        logger.error(f"Failed to load matches: {e}")
        return False

    logger.info("")

    # Step 3: Extract and load venues
    logger.info("Step 3: Extracting venues...")
    try:
        all_venues = {}
        all_venue_machines = []

        for match in matches:
            venue = match_parser.extract_venue_from_match(match)
            all_venues[venue['venue_key']] = venue

            venue_machines = match_parser.extract_venue_machines(match)
            all_venue_machines.extend(venue_machines)

        loader.load_venues(list(all_venues.values()))

        # Deduplicate venue machines
        unique_vm = {}
        for vm in all_venue_machines:
            key = (vm['venue_key'], vm['machine_key'], vm['season'])
            unique_vm[key] = vm

        loader.load_venue_machines(list(unique_vm.values()))

        logger.info(f"✓ Loaded {len(all_venues)} venues")
    except Exception as e:
        logger.error(f"Failed to load venues: {e}")
        return False

    logger.info("")

    # Step 4: Extract and load teams
    logger.info("Step 4: Extracting teams...")
    try:
        all_teams = {}

        for match in matches:
            teams = match_parser.extract_teams_from_match(match)
            for team in teams:
                key = (team['team_key'], team['season'])
                all_teams[key] = team

        loader.load_teams(list(all_teams.values()))
        logger.info(f"✓ Loaded {len(all_teams)} teams")
    except Exception as e:
        logger.error(f"Failed to load teams: {e}")
        return False

    logger.info("")

    # Step 5: Extract and load players
    logger.info("Step 5: Extracting players...")
    try:
        all_players = {}

        for match in matches:
            players = match_parser.extract_players_from_match(match)
            for player in players:
                if player['player_key'] in all_players:
                    # Update last_seen_season
                    existing = all_players[player['player_key']]
                    existing['last_seen_season'] = max(
                        existing['last_seen_season'],
                        player['last_seen_season']
                    )
                else:
                    all_players[player['player_key']] = player

        loader.load_players(list(all_players.values()))
        logger.info(f"✓ Loaded {len(all_players)} players")
    except Exception as e:
        logger.error(f"Failed to load players: {e}")
        return False

    logger.info("")

    # Step 5b: Load IPR from IPR.csv (source of truth)
    logger.info("Step 5b: Loading IPR from IPR.csv...")
    try:
        ipr_parser = IPRParser()
        ipr_path = config.DATA_PATH / "IPR.csv"

        if not ipr_path.exists():
            logger.warning(f"IPR.csv not found at {ipr_path}, skipping IPR update")
        else:
            ipr_updates = ipr_parser.extract_ipr_updates(ipr_path)
            updated_count = loader.load_ipr(ipr_updates)
            logger.info(f"✓ Updated IPR for {updated_count} players from IPR.csv")
    except Exception as e:
        logger.error(f"Failed to load IPR: {e}")
        # Don't return False - IPR is optional
        logger.warning("Continuing without IPR updates...")

    logger.info("")

    # Step 6: Load matches
    logger.info("Step 6: Loading match metadata...")
    try:
        match_metadata = []
        for match in matches:
            metadata = match_parser.extract_match_metadata(match)
            match_metadata.append(metadata)

        loader.load_matches(match_metadata)
        logger.info(f"✓ Loaded {len(match_metadata)} matches")
    except Exception as e:
        logger.error(f"Failed to load match metadata: {e}")
        return False

    logger.info("")

    # Step 7: Load games
    logger.info("Step 7: Loading games...")
    try:
        all_games = []
        for match in matches:
            games = match_parser.extract_games_from_match(match)

            # Normalize machine keys
            for game in games:
                game['machine_key'] = machine_parser.normalize_machine_key(
                    game['machine_key']
                )

            all_games.extend(games)

        loader.load_games(all_games)
        logger.info(f"✓ Loaded {len(all_games)} games")
    except Exception as e:
        logger.error(f"Failed to load games: {e}")
        return False

    logger.info("")

    # Step 8: Load scores
    logger.info("Step 8: Loading scores...")
    try:
        all_scores = []
        for match in matches:
            scores = match_parser.extract_scores_from_match(match, machine_parser)
            all_scores.extend(scores)

        loader.load_scores_batch(all_scores)
        logger.info(f"✓ Loaded {len(all_scores)} scores")
    except Exception as e:
        logger.error(f"Failed to load scores: {e}")
        return False

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"ETL Complete for Season {season}!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Summary:")
    logger.info(f"  Machines: {len(machines)}")
    logger.info(f"  Venues: {len(all_venues)}")
    logger.info(f"  Teams: {len(all_teams)}")
    logger.info(f"  Players: {len(all_players)}")
    logger.info(f"  Matches: {len(match_metadata)}")
    logger.info(f"  Games: {len(all_games)}")
    logger.info(f"  Scores: {len(all_scores)}")
    logger.info("")

    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Load MNP season data into database'
    )
    parser.add_argument(
        '--season',
        type=int,
        required=True,
        help='Season number to load (e.g., 22)'
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

    # Load season data
    success = load_season_data(args.season)

    # Close database connection
    db.close()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
