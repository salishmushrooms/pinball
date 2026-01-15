#!/usr/bin/env python3
"""
Player deduplication script.

This script finds and merges duplicate player entries that have the same name
but different player_keys. This can happen when:
- load_preseason.py generates underscore-style keys (e.g., "claire_burke")
- load_season.py uses SHA-1 hashes from match JSON files (e.g., "3534d6fb...")

The script will:
1. Find all players with duplicate names
2. For each duplicate set, pick the "canonical" key (prefer SHA-1 format)
3. Update all scores references to use the canonical key
4. Merge player stats (first/last seen season, total games)
5. Delete the duplicate player records

Usage:
    python etl/deduplicate_players.py --dry-run    # Preview changes
    python etl/deduplicate_players.py              # Execute changes
"""

import argparse
import logging
import sys
from sqlalchemy import text

from etl.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def is_sha1_key(key: str) -> bool:
    """Check if a player_key looks like a SHA-1 hash (40 hex characters)"""
    if len(key) != 40:
        return False
    try:
        int(key, 16)
        return True
    except ValueError:
        return False


def find_duplicate_players(conn) -> dict:
    """
    Find all players with the same name but different keys.

    Returns:
        Dictionary mapping player names to list of their player records
    """
    result = conn.execute(text("""
        SELECT name, COUNT(*) as count
        FROM players
        GROUP BY name
        HAVING COUNT(*) > 1
        ORDER BY count DESC
    """))

    duplicates = {}
    for row in result:
        name = row[0]
        # Get all records for this player
        player_result = conn.execute(text("""
            SELECT player_key, name, first_seen_season, last_seen_season,
                   total_games_played, current_ipr
            FROM players
            WHERE name = :name
            ORDER BY first_seen_season
        """), {'name': name})

        duplicates[name] = [dict(r._mapping) for r in player_result]

    return duplicates


def select_canonical_key(players: list) -> tuple:
    """
    Select the canonical player_key from a list of duplicate players.

    Priority:
    1. SHA-1 hash format (40 hex chars) - these come from match JSON files
    2. Most total games played
    3. Earliest first_seen_season

    Returns:
        Tuple of (canonical_key, list of keys to remove)
    """
    # Separate SHA-1 keys from other formats
    sha1_players = [p for p in players if is_sha1_key(p['player_key'])]
    other_players = [p for p in players if not is_sha1_key(p['player_key'])]

    # Prefer SHA-1 keys
    if sha1_players:
        # Among SHA-1 keys, prefer the one with most games or earliest season
        canonical = max(sha1_players,
                       key=lambda p: (p['total_games_played'] or 0,
                                     -(p['first_seen_season'] or 999)))
        keys_to_remove = [p['player_key'] for p in players if p['player_key'] != canonical['player_key']]
    else:
        # No SHA-1 keys, use the one with most games
        canonical = max(other_players,
                       key=lambda p: (p['total_games_played'] or 0,
                                     -(p['first_seen_season'] or 999)))
        keys_to_remove = [p['player_key'] for p in players if p['player_key'] != canonical['player_key']]

    return canonical, keys_to_remove


def merge_player_stats(conn, canonical: dict, duplicates: list, dry_run: bool = False):
    """
    Merge stats from duplicate players into the canonical player.

    Updates:
    - first_seen_season: MIN of all
    - last_seen_season: MAX of all
    - total_games_played: SUM of all
    - current_ipr: Keep canonical's IPR (or first non-null)
    """
    all_players = [canonical] + duplicates

    first_seen = min(p['first_seen_season'] for p in all_players if p['first_seen_season'])
    last_seen = max(p['last_seen_season'] for p in all_players if p['last_seen_season'])
    total_games = sum(p['total_games_played'] or 0 for p in all_players)

    # Find first non-null IPR
    current_ipr = canonical.get('current_ipr')
    if current_ipr is None:
        for p in all_players:
            if p.get('current_ipr') is not None:
                current_ipr = p['current_ipr']
                break

    if dry_run:
        logger.info(f"    Would update canonical player stats: first_seen={first_seen}, "
                   f"last_seen={last_seen}, total_games={total_games}")
    else:
        conn.execute(text("""
            UPDATE players
            SET first_seen_season = :first_seen,
                last_seen_season = :last_seen,
                total_games_played = :total_games,
                current_ipr = :current_ipr,
                updated_at = CURRENT_TIMESTAMP
            WHERE player_key = :player_key
        """), {
            'player_key': canonical['player_key'],
            'first_seen': first_seen,
            'last_seen': last_seen,
            'total_games': total_games,
            'current_ipr': current_ipr
        })


def update_score_references(conn, canonical_key: str, old_keys: list, dry_run: bool = False):
    """Update scores table to reference the canonical player_key"""
    for old_key in old_keys:
        # Count affected scores
        result = conn.execute(text("""
            SELECT COUNT(*) FROM scores WHERE player_key = :old_key
        """), {'old_key': old_key})
        count = result.scalar()

        if count > 0:
            if dry_run:
                logger.info(f"    Would update {count} scores from {old_key} -> {canonical_key}")
            else:
                conn.execute(text("""
                    UPDATE scores
                    SET player_key = :canonical_key
                    WHERE player_key = :old_key
                """), {'canonical_key': canonical_key, 'old_key': old_key})
                logger.info(f"    Updated {count} scores from {old_key} -> {canonical_key}")


def delete_duplicate_players(conn, keys_to_remove: list, dry_run: bool = False):
    """Delete duplicate player records after merging"""
    for key in keys_to_remove:
        if dry_run:
            logger.info(f"    Would delete player_key: {key}")
        else:
            conn.execute(text("""
                DELETE FROM players WHERE player_key = :key
            """), {'key': key})
            logger.info(f"    Deleted player_key: {key}")


def deduplicate_players(dry_run: bool = False):
    """Main deduplication logic"""
    logger.info("=" * 60)
    logger.info(f"Player Deduplication {'(DRY RUN)' if dry_run else ''}")
    logger.info("=" * 60)

    with db.engine.begin() as conn:
        # Find duplicates
        duplicates = find_duplicate_players(conn)

        if not duplicates:
            logger.info("No duplicate players found!")
            return

        logger.info(f"Found {len(duplicates)} players with duplicate entries")
        logger.info("")

        total_removed = 0
        total_scores_updated = 0

        for name, players in duplicates.items():
            logger.info(f"Processing: {name} ({len(players)} entries)")

            # Show current state
            for p in players:
                key_type = "SHA-1" if is_sha1_key(p['player_key']) else "generated"
                logger.info(f"  - {p['player_key'][:20]}... ({key_type}) "
                           f"seasons {p['first_seen_season']}-{p['last_seen_season']}, "
                           f"{p['total_games_played'] or 0} games")

            # Select canonical key
            canonical, keys_to_remove = select_canonical_key(players)
            logger.info(f"  Canonical key: {canonical['player_key'][:20]}...")

            # Get duplicate player records for stats merging
            dup_players = [p for p in players if p['player_key'] in keys_to_remove]

            # Update score references
            for old_key in keys_to_remove:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM scores WHERE player_key = :old_key
                """), {'old_key': old_key})
                count = result.scalar()
                total_scores_updated += count

            update_score_references(conn, canonical['player_key'], keys_to_remove, dry_run)

            # Merge stats
            merge_player_stats(conn, canonical, dup_players, dry_run)

            # Delete duplicates
            delete_duplicate_players(conn, keys_to_remove, dry_run)
            total_removed += len(keys_to_remove)

            logger.info("")

        logger.info("=" * 60)
        logger.info("Summary:")
        logger.info(f"  Players deduplicated: {len(duplicates)}")
        logger.info(f"  Duplicate records {'would be ' if dry_run else ''}removed: {total_removed}")
        logger.info(f"  Score references {'would be ' if dry_run else ''}updated: {total_scores_updated}")
        logger.info("=" * 60)

        if dry_run:
            logger.info("")
            logger.info("This was a DRY RUN. No changes were made.")
            logger.info("Run without --dry-run to apply changes.")


def main():
    parser = argparse.ArgumentParser(
        description='Deduplicate players with same name but different keys'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )

    args = parser.parse_args()

    # Connect to database
    try:
        db.connect()
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    try:
        deduplicate_players(dry_run=args.dry_run)
    finally:
        db.close()


if __name__ == '__main__':
    main()
