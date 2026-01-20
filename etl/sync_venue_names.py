#!/usr/bin/env python3
"""
Sync venue names from venues.json to the database.

This script updates venue_name in the venues table to match the canonical
names defined in venues.json, fixing any inconsistencies from historical data.

Usage:
    # Update local database
    python etl/sync_venue_names.py

    # Update production database
    python etl/sync_venue_names.py --production

    # Dry run (show what would change)
    python etl/sync_venue_names.py --dry-run
    python etl/sync_venue_names.py --production --dry-run
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from sqlalchemy import text

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.config import config
from etl.database import Database

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def load_canonical_venues() -> dict:
    """Load canonical venue names from venues.json"""
    venues_path = config.DATA_PATH / "venues.json"

    if not venues_path.exists():
        logger.error(f"venues.json not found at {venues_path}")
        sys.exit(1)

    with open(venues_path) as f:
        venues_data = json.load(f)

    return {key: info.get('name', '') for key, info in venues_data.items()}


def sync_venue_names(dry_run: bool = False):
    """Sync venue names from venues.json to database"""

    # Load canonical names
    canonical = load_canonical_venues()
    logger.info(f"Loaded {len(canonical)} venues from venues.json")

    # Connect to database
    db = Database()
    db.connect()

    try:
        with db.engine.connect() as conn:
            # Get current venue names from database
            result = conn.execute(text("SELECT venue_key, venue_name FROM venues"))
            db_venues = {row[0]: row[1] for row in result}

            logger.info(f"Found {len(db_venues)} venues in database")
            logger.info("")

            # Find differences
            updates = []
            for venue_key, db_name in db_venues.items():
                canonical_name = canonical.get(venue_key)
                if canonical_name and db_name != canonical_name:
                    updates.append((venue_key, db_name, canonical_name))

            if not updates:
                logger.info("All venue names are already in sync!")
                return

            # Show what will be updated
            logger.info(f"Found {len(updates)} venue(s) to update:")
            logger.info("-" * 60)
            for venue_key, old_name, new_name in updates:
                logger.info(f"  {venue_key}: \"{old_name}\" -> \"{new_name}\"")
            logger.info("")

            if dry_run:
                logger.info("Dry run - no changes made")
                return

            # Apply updates
            for venue_key, old_name, new_name in updates:
                conn.execute(
                    text("UPDATE venues SET venue_name = :name WHERE venue_key = :key"),
                    {"name": new_name, "key": venue_key}
                )
            conn.commit()

            logger.info(f"Updated {len(updates)} venue name(s)")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Sync venue names from venues.json to database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without making updates"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run against production database (uses DATABASE_PUBLIC_URL from .env)"
    )
    args = parser.parse_args()

    # Override database URL for production
    if args.production:
        prod_url = os.getenv('DATABASE_PUBLIC_URL')
        if not prod_url:
            logger.error("DATABASE_PUBLIC_URL not found in environment/.env")
            sys.exit(1)
        config.DATABASE_URL = prod_url

    logger.info("=" * 60)
    logger.info("Venue Name Sync")
    logger.info("=" * 60)
    target = "PRODUCTION" if args.production else "local"
    logger.info(f"Target: {target}")
    logger.info(f"Database: {config.DATABASE_URL.split('@')[-1]}")  # Hide credentials
    logger.info("")

    sync_venue_names(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
