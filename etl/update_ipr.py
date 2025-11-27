#!/usr/bin/env python3
"""
Standalone script to update player IPR values from IPR.csv.
This is useful when you need to refresh IPR without reloading all season data.

Usage:
    python etl/update_ipr.py
    python etl/update_ipr.py --verbose
"""

import argparse
import logging
import sys
from pathlib import Path

from etl.config import config
from etl.database import db
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


def update_ipr():
    """Update player IPR values from IPR.csv"""

    logger.info("=" * 60)
    logger.info("Updating Player IPR from IPR.csv")
    logger.info("=" * 60)

    # Initialize components
    ipr_parser = IPRParser()
    loader = DatabaseLoader()

    # Load IPR data
    ipr_path = config.DATA_PATH / "IPR.csv"

    if not ipr_path.exists():
        logger.error(f"IPR.csv not found at {ipr_path}")
        return False

    logger.info(f"IPR file: {ipr_path}")
    logger.info("")

    try:
        # Parse IPR.csv
        logger.info("Parsing IPR.csv...")
        ipr_updates = ipr_parser.extract_ipr_updates(ipr_path)
        logger.info(f"✓ Found {len(ipr_updates)} players in IPR.csv")
        logger.info("")

        # Update database
        logger.info("Updating player IPR values in database...")
        updated_count = loader.load_ipr(ipr_updates)
        logger.info("")

        logger.info("=" * 60)
        logger.info("IPR Update Complete!")
        logger.info("=" * 60)
        logger.info("")
        logger.info(f"Summary:")
        logger.info(f"  Total players in IPR.csv: {len(ipr_updates)}")
        logger.info(f"  Players updated in database: {updated_count}")
        logger.info(f"  Players not found: {len(ipr_updates) - updated_count}")
        logger.info("")

        return True

    except Exception as e:
        logger.error(f"Failed to update IPR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Update player IPR values from IPR.csv'
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

    # Update IPR
    success = update_ipr()

    # Close database connection
    db.close()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
