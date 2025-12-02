#!/usr/bin/env python3
"""
Calculate and update player total games played.

This script updates the players.total_games_played field by counting
all games each player has participated in across all seasons.

Usage:
    python etl/calculate_player_totals.py
    python etl/calculate_player_totals.py --verbose
"""

import argparse
import logging
import sys
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


def calculate_player_game_counts():
    """
    Calculate total games played for each player.

    Returns:
        list: [(player_key, total_games), ...]
    """
    logger.info("Calculating player game counts...")

    # Count distinct games (by game_id) for each player
    query = """
        SELECT
            player_key,
            COUNT(DISTINCT game_id) as total_games
        FROM scores
        GROUP BY player_key
        ORDER BY total_games DESC
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()

    logger.info(f"Calculated game counts for {len(rows)} players")
    return rows


def update_player_totals(game_counts):
    """
    Update players.total_games_played for all players.

    Args:
        game_counts: List of (player_key, total_games) tuples
    """
    logger.info("Updating player total_games_played...")

    query = """
        UPDATE players
        SET total_games_played = :total_games,
            updated_at = CURRENT_TIMESTAMP
        WHERE player_key = :player_key
    """

    updated = 0
    batch_size = 100

    with db.engine.begin() as conn:
        for i, (player_key, total_games) in enumerate(game_counts):
            conn.execute(text(query), {
                'player_key': player_key,
                'total_games': total_games
            })
            updated += 1

            if (i + 1) % batch_size == 0:
                logger.info(f"  Updated {i + 1}/{len(game_counts)} players...")

    logger.info(f"✓ Updated total_games_played for {updated} players")
    return updated


def calculate_and_store_player_totals():
    """
    Main function to calculate and store player total games.
    """
    logger.info("=" * 60)
    logger.info("Calculating Player Total Games Played")
    logger.info("=" * 60)

    # Step 1: Calculate game counts
    game_counts = calculate_player_game_counts()

    if not game_counts:
        logger.warning("No player scores found!")
        return False

    # Step 2: Update player records
    update_player_totals(game_counts)

    logger.info("")
    logger.info("=" * 60)
    logger.info("✓ Player totals calculated successfully!")
    logger.info("=" * 60)

    return True


def verify_player_totals():
    """Verify that player totals were calculated correctly"""

    logger.info("")
    logger.info("Verifying player total games...")

    query = """
        SELECT
            COUNT(*) as total_players,
            COUNT(*) FILTER (WHERE total_games_played > 0) as players_with_games,
            MIN(total_games_played) as min_games,
            MAX(total_games_played) as max_games,
            AVG(total_games_played)::int as avg_games,
            SUM(total_games_played) as total_game_participations
        FROM players
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query))
        row = result.fetchone()

    if row:
        logger.info(f"  Total players: {row[0]}")
        logger.info(f"  Players with games: {row[1]}")
        logger.info(f"  Games played: min={row[2]}, max={row[3]}, avg={row[4]}")
        logger.info(f"  Total game participations: {row[5]}")

    # Show top players by games played
    logger.info("")
    logger.info("Top 10 players by games played:")

    query = """
        SELECT
            name,
            total_games_played,
            current_ipr,
            first_seen_season,
            last_seen_season
        FROM players
        WHERE total_games_played > 0
        ORDER BY total_games_played DESC
        LIMIT 10
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()

    for row in rows:
        name, games, ipr, first_season, last_season = row
        ipr_str = f"IPR {ipr}" if ipr else "No IPR"
        logger.info(f"  {name}: {games} games ({ipr_str}, S{first_season}-S{last_season})")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Calculate player total games played')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Connect to database
        db.connect()

        # Calculate player totals
        success = calculate_and_store_player_totals()

        if not success:
            return 1

        # Verify results
        verify_player_totals()

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
