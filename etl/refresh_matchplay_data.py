#!/usr/bin/env python3
"""
Refresh Matchplay.events data for all linked players.

This script fetches fresh profile data (ratings, IFPA, tournament counts) from
the Matchplay.events API for all players that have linked accounts. It's designed
to run as part of the weekly ETL pipeline rather than making live API calls on
each page load.

Usage:
    python etl/refresh_matchplay_data.py                  # Refresh all linked players
    python etl/refresh_matchplay_data.py --dry-run        # Show what would be refreshed
    python etl/refresh_matchplay_data.py --limit 10       # Refresh only 10 players (for testing)
    python etl/refresh_matchplay_data.py --verbose        # Enable verbose logging

Rate Limiting:
    - Matchplay API has rate limits; this script respects them
    - Adds a small delay between requests to avoid hitting limits
    - Stops gracefully if rate limit is nearly exhausted

Data Cached:
    - Rating (value, RD, lower bound)
    - Game counts (played, wins, losses, efficiency)
    - IFPA data (ID, rank, rating, women's rank)
    - Tournament count
    - Profile info (location, avatar)
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from etl.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def check_matchplay_configured() -> bool:
    """Check if Matchplay API token is configured."""
    token = os.getenv("MATCHPLAY_API_TOKEN")
    if not token:
        logger.error("MATCHPLAY_API_TOKEN environment variable not set")
        logger.error("Get your token from: https://app.matchplay.events (Account Settings -> API tokens)")
        return False
    return True


async def get_linked_players(conn, limit: int = None) -> list:
    """Get all players with linked Matchplay accounts."""
    query = """
        SELECT
            m.mnp_player_key,
            m.matchplay_user_id,
            m.matchplay_name,
            m.last_synced,
            p.name as mnp_name
        FROM matchplay_player_mappings m
        JOIN players p ON p.player_key = m.mnp_player_key
        ORDER BY m.last_synced ASC NULLS FIRST
    """
    if limit:
        query += f" LIMIT {limit}"

    result = conn.execute(text(query))
    return [dict(row._mapping) for row in result]


async def fetch_matchplay_profile(client, user_id: int) -> dict:
    """Fetch a user's full profile from Matchplay API."""
    try:
        return await client.get_user_profile(user_id)
    except Exception as e:
        logger.warning(f"Failed to fetch profile for user {user_id}: {e}")
        return None


def update_cached_data(conn, matchplay_user_id: int, profile_data: dict) -> bool:
    """Update the cached Matchplay data in the database."""
    if not profile_data:
        return False

    # Extract user info
    user_info = profile_data.get('user', {})
    location = user_info.get('location')
    avatar = user_info.get('avatar')

    # Extract rating data
    rating_data = profile_data.get('rating', {})
    rating_value = rating_data.get('rating')
    rating_rd = rating_data.get('rd')
    game_count = rating_data.get('gameCount')
    win_count = rating_data.get('winCount')
    loss_count = rating_data.get('lossCount')
    efficiency_percent = rating_data.get('efficiencyPercent')
    lower_bound = rating_data.get('lowerBound')

    # Extract IFPA data
    ifpa_data = profile_data.get('ifpa', {})
    ifpa_id = ifpa_data.get('ifpaId') if ifpa_data else None
    ifpa_rank = ifpa_data.get('rank') if ifpa_data else None
    ifpa_rating = ifpa_data.get('rating') if ifpa_data else None
    ifpa_womens_rank = ifpa_data.get('womensRank') if ifpa_data else None

    # Extract tournament count
    counts = profile_data.get('userCounts', {})
    tournament_count = counts.get('tournamentPlayCount')

    now = datetime.utcnow()

    # Delete existing cached rating
    conn.execute(text("""
        DELETE FROM matchplay_ratings
        WHERE matchplay_user_id = :matchplay_user_id
    """), {'matchplay_user_id': matchplay_user_id})

    # Insert new cached data
    conn.execute(text("""
        INSERT INTO matchplay_ratings
            (matchplay_user_id, rating_value, rating_rd, game_count, win_count,
             loss_count, efficiency_percent, lower_bound, ifpa_id, ifpa_rank,
             ifpa_rating, ifpa_womens_rank, tournament_count, location, avatar, fetched_at)
        VALUES
            (:matchplay_user_id, :rating_value, :rating_rd, :game_count, :win_count,
             :loss_count, :efficiency_percent, :lower_bound, :ifpa_id, :ifpa_rank,
             :ifpa_rating, :ifpa_womens_rank, :tournament_count, :location, :avatar, :fetched_at)
    """), {
        'matchplay_user_id': matchplay_user_id,
        'rating_value': rating_value,
        'rating_rd': rating_rd,
        'game_count': game_count,
        'win_count': win_count,
        'loss_count': loss_count,
        'efficiency_percent': efficiency_percent,
        'lower_bound': lower_bound,
        'ifpa_id': ifpa_id,
        'ifpa_rank': ifpa_rank,
        'ifpa_rating': ifpa_rating,
        'ifpa_womens_rank': ifpa_womens_rank,
        'tournament_count': tournament_count,
        'location': location,
        'avatar': avatar,
        'fetched_at': now
    })

    # Update last_synced in mappings table
    conn.execute(text("""
        UPDATE matchplay_player_mappings
        SET last_synced = :last_synced
        WHERE matchplay_user_id = :matchplay_user_id
    """), {
        'matchplay_user_id': matchplay_user_id,
        'last_synced': now
    })

    return True


async def refresh_all_players(dry_run: bool = False, limit: int = None, verbose: bool = False):
    """Refresh Matchplay data for all linked players."""

    # Import the Matchplay client
    from api.services.matchplay_client import MatchplayClient

    client = MatchplayClient()
    if not client.is_configured():
        logger.error("Matchplay client not configured. Set MATCHPLAY_API_TOKEN environment variable.")
        return False

    # Connect to database
    db.connect()

    try:
        with db.engine.connect() as conn:
            # Get all linked players
            players = await get_linked_players(conn, limit)
            total_players = len(players)

            if total_players == 0:
                logger.info("No linked Matchplay accounts found.")
                return True

            logger.info(f"Found {total_players} linked Matchplay accounts")

            if dry_run:
                logger.info("DRY RUN - No changes will be made")
                for player in players:
                    logger.info(f"  Would refresh: {player['mnp_name']} -> Matchplay user {player['matchplay_user_id']}")
                return True

            # Process each player
            success_count = 0
            error_count = 0
            skipped_count = 0

            for i, player in enumerate(players, 1):
                mnp_name = player['mnp_name']
                matchplay_user_id = player['matchplay_user_id']

                # Check rate limit before each request
                if client.rate_limit_remaining is not None and client.rate_limit_remaining <= 5:
                    logger.warning(f"Rate limit nearly exhausted ({client.rate_limit_remaining} remaining). Stopping.")
                    skipped_count = total_players - i + 1
                    break

                if verbose:
                    logger.info(f"[{i}/{total_players}] Refreshing {mnp_name} (user {matchplay_user_id})...")

                # Fetch profile from API
                profile = await fetch_matchplay_profile(client, matchplay_user_id)

                if profile:
                    # Update database
                    if update_cached_data(conn, matchplay_user_id, profile):
                        success_count += 1
                        if verbose:
                            rating = profile.get('rating', {}).get('rating', 'N/A')
                            logger.info(f"  Rating: {rating}")
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    logger.warning(f"  Failed to fetch data for {mnp_name}")

                # Small delay between requests to avoid rate limiting
                if i < total_players:
                    await asyncio.sleep(0.2)

            # Commit all changes
            conn.commit()

            # Summary
            logger.info("=" * 50)
            logger.info("Matchplay Data Refresh Summary")
            logger.info("=" * 50)
            logger.info(f"Total linked players: {total_players}")
            logger.info(f"Successfully refreshed: {success_count}")
            logger.info(f"Errors: {error_count}")
            if skipped_count > 0:
                logger.info(f"Skipped (rate limit): {skipped_count}")
            if client.rate_limit_remaining is not None:
                logger.info(f"API rate limit remaining: {client.rate_limit_remaining}/{client.rate_limit_total}")
            logger.info("=" * 50)

            return error_count == 0

    except Exception as e:
        logger.error(f"Error during refresh: {e}")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Refresh Matchplay.events data for all linked players",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Refresh all linked players
    python etl/refresh_matchplay_data.py

    # Preview what would be refreshed (no changes)
    python etl/refresh_matchplay_data.py --dry-run

    # Refresh only first 10 players (for testing)
    python etl/refresh_matchplay_data.py --limit 10 --verbose
"""
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be refreshed without making changes"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of players to refresh (for testing)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Check configuration
    if not check_matchplay_configured():
        sys.exit(1)

    # Load .env file if present
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)

    # Run the refresh
    success = asyncio.run(refresh_all_players(
        dry_run=args.dry_run,
        limit=args.limit,
        verbose=args.verbose
    ))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
