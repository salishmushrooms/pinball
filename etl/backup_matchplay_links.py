#!/usr/bin/env python3
"""
Matchplay Account Links Backup and Restore Script

This script handles backup and restore of production user data that cannot be
recreated from source files - specifically the matchplay account links that
users have manually created.

IMPORTANT: Run this script BEFORE any database rebuild to preserve user data.

Usage:
    # Backup matchplay links (creates timestamped backup file)
    python etl/backup_matchplay_links.py --backup

    # Backup to specific file
    python etl/backup_matchplay_links.py --backup --output /path/to/backup.json

    # Restore matchplay links from backup
    python etl/backup_matchplay_links.py --restore --input backups/matchplay_links_20260126_120000.json

    # Verify current matchplay links exist (pre-rebuild check)
    python etl/backup_matchplay_links.py --verify

    # Verify backup file is valid
    python etl/backup_matchplay_links.py --verify-backup --input backups/matchplay_links_20260126_120000.json

Backup Contents:
    - matchplay_player_mappings: User-created account links (CRITICAL)
    - matchplay_ratings: Cached ratings (can be re-fetched, but included for convenience)
    - matchplay_player_machine_stats: Cached stats (can be re-fetched, but included for convenience)
    - matchplay_arena_mappings: Machine name mappings (useful to preserve)

The backup is stored as JSON for readability and portability.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from etl.config import get_db_connection


# Tables to backup in order (respecting foreign key dependencies)
MATCHPLAY_TABLES = [
    "matchplay_player_mappings",  # Core user links - CRITICAL
    "matchplay_ratings",           # Cached data - can be re-fetched
    "matchplay_player_machine_stats",  # Cached data - can be re-fetched
    "matchplay_arena_mappings",    # Machine name mappings
]

# Default backup directory
BACKUP_DIR = Path(__file__).parent.parent / "backups"


def decimal_serializer(obj):
    """JSON serializer for Decimal types."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def get_table_data(cursor, table_name: str) -> list[dict]:
    """Fetch all rows from a table as list of dicts."""
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    result = []
    for row in rows:
        row_dict = {}
        for i, col in enumerate(columns):
            value = row[i]
            # Convert datetime to ISO string for JSON serialization
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            row_dict[col] = value
        result.append(row_dict)

    return result


def backup_matchplay_links(output_path: Path = None) -> tuple[bool, str]:
    """
    Backup all matchplay-related tables to a JSON file.

    Returns:
        tuple: (success: bool, message: str)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        backup_data = {
            "backup_version": "1.0",
            "created_at": datetime.now().isoformat(),
            "description": "MNP Matchplay account links backup",
            "tables": {}
        }

        total_records = 0
        critical_records = 0

        for table_name in MATCHPLAY_TABLES:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
            """, (table_name,))

            if not cursor.fetchone()[0]:
                print(f"  Warning: Table {table_name} does not exist, skipping")
                backup_data["tables"][table_name] = []
                continue

            data = get_table_data(cursor, table_name)
            backup_data["tables"][table_name] = data

            record_count = len(data)
            total_records += record_count

            if table_name == "matchplay_player_mappings":
                critical_records = record_count

            print(f"  {table_name}: {record_count} records")

        # Determine output path
        if output_path is None:
            BACKUP_DIR.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = BACKUP_DIR / f"matchplay_links_{timestamp}.json"

        # Write backup file
        with open(output_path, 'w') as f:
            json.dump(backup_data, f, indent=2, default=decimal_serializer)

        return True, f"Backup saved to {output_path} ({critical_records} account links, {total_records} total records)"

    except Exception as e:
        return False, f"Backup failed: {e}"
    finally:
        cursor.close()
        conn.close()


def restore_matchplay_links(input_path: Path, dry_run: bool = False) -> tuple[bool, str]:
    """
    Restore matchplay links from a backup file.

    Args:
        input_path: Path to backup JSON file
        dry_run: If True, only validate without actually restoring

    Returns:
        tuple: (success: bool, message: str)
    """
    if not input_path.exists():
        return False, f"Backup file not found: {input_path}"

    # Load backup data
    with open(input_path, 'r') as f:
        backup_data = json.load(f)

    # Validate backup format
    if "backup_version" not in backup_data or "tables" not in backup_data:
        return False, "Invalid backup file format"

    print(f"Backup created: {backup_data.get('created_at', 'unknown')}")
    print(f"Backup version: {backup_data.get('backup_version', 'unknown')}")

    if dry_run:
        print("\n[DRY RUN] Would restore the following data:")
        for table_name, records in backup_data["tables"].items():
            print(f"  {table_name}: {len(records)} records")
        return True, "Dry run completed successfully"

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        restored_counts = {}

        # Restore in order (respecting foreign key dependencies)
        # First, restore matchplay_player_mappings
        # Then restore dependent tables

        for table_name in MATCHPLAY_TABLES:
            records = backup_data["tables"].get(table_name, [])

            if not records:
                print(f"  {table_name}: No records to restore")
                restored_counts[table_name] = 0
                continue

            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
            """, (table_name,))

            if not cursor.fetchone()[0]:
                print(f"  Warning: Table {table_name} does not exist, skipping")
                continue

            # Get column names from first record
            columns = list(records[0].keys())

            # Build INSERT statement with ON CONFLICT DO NOTHING
            # This makes restore idempotent - won't fail if data already exists
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join(columns)

            insert_sql = f"""
                INSERT INTO {table_name} ({column_names})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
            """

            inserted = 0
            for record in records:
                values = [record.get(col) for col in columns]
                cursor.execute(insert_sql, values)
                inserted += cursor.rowcount

            restored_counts[table_name] = inserted
            print(f"  {table_name}: {inserted} records restored ({len(records)} in backup)")

        conn.commit()

        critical_restored = restored_counts.get("matchplay_player_mappings", 0)
        total_restored = sum(restored_counts.values())

        return True, f"Restore complete: {critical_restored} account links, {total_restored} total records"

    except Exception as e:
        conn.rollback()
        return False, f"Restore failed: {e}"
    finally:
        cursor.close()
        conn.close()


def verify_matchplay_links() -> tuple[bool, str, dict]:
    """
    Verify that matchplay links exist in the database.

    Returns:
        tuple: (has_links: bool, message: str, counts: dict)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        counts = {}

        for table_name in MATCHPLAY_TABLES:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
            """, (table_name,))

            if not cursor.fetchone()[0]:
                counts[table_name] = None  # Table doesn't exist
                continue

            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            counts[table_name] = cursor.fetchone()[0]

        # Check critical table
        critical_count = counts.get("matchplay_player_mappings")

        if critical_count is None:
            return False, "matchplay_player_mappings table does not exist", counts
        elif critical_count == 0:
            return False, "No matchplay account links found in database", counts
        else:
            return True, f"Found {critical_count} matchplay account links", counts

    except Exception as e:
        return False, f"Verification failed: {e}", {}
    finally:
        cursor.close()
        conn.close()


def verify_backup_file(input_path: Path) -> tuple[bool, str, dict]:
    """
    Verify that a backup file is valid and contains expected data.

    Returns:
        tuple: (is_valid: bool, message: str, info: dict)
    """
    if not input_path.exists():
        return False, f"Backup file not found: {input_path}", {}

    try:
        with open(input_path, 'r') as f:
            backup_data = json.load(f)

        # Check required fields
        if "backup_version" not in backup_data:
            return False, "Missing backup_version field", {}
        if "tables" not in backup_data:
            return False, "Missing tables field", {}

        info = {
            "backup_version": backup_data.get("backup_version"),
            "created_at": backup_data.get("created_at"),
            "tables": {}
        }

        for table_name in MATCHPLAY_TABLES:
            records = backup_data["tables"].get(table_name, [])
            info["tables"][table_name] = len(records)

        critical_count = info["tables"].get("matchplay_player_mappings", 0)

        if critical_count == 0:
            return False, "Backup contains no matchplay account links", info

        return True, f"Valid backup with {critical_count} account links", info

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in backup file: {e}", {}
    except Exception as e:
        return False, f"Error reading backup file: {e}", {}


def list_backups() -> list[dict]:
    """List all available backup files with metadata."""
    if not BACKUP_DIR.exists():
        return []

    backups = []
    for backup_file in sorted(BACKUP_DIR.glob("matchplay_links_*.json"), reverse=True):
        is_valid, message, info = verify_backup_file(backup_file)
        backups.append({
            "path": backup_file,
            "filename": backup_file.name,
            "is_valid": is_valid,
            "created_at": info.get("created_at") if is_valid else None,
            "account_links": info.get("tables", {}).get("matchplay_player_mappings", 0) if is_valid else 0
        })

    return backups


def main():
    parser = argparse.ArgumentParser(
        description="Backup and restore matchplay account links",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Backup matchplay links
    python etl/backup_matchplay_links.py --backup

    # Backup to specific file
    python etl/backup_matchplay_links.py --backup --output my_backup.json

    # Verify links exist before rebuild
    python etl/backup_matchplay_links.py --verify

    # List available backups
    python etl/backup_matchplay_links.py --list

    # Restore from backup
    python etl/backup_matchplay_links.py --restore --input backups/matchplay_links_20260126_120000.json

    # Dry run restore (validate without changes)
    python etl/backup_matchplay_links.py --restore --input backup.json --dry-run
"""
    )

    # Action arguments (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--backup",
        action="store_true",
        help="Backup matchplay links to a JSON file"
    )
    action_group.add_argument(
        "--restore",
        action="store_true",
        help="Restore matchplay links from a backup file"
    )
    action_group.add_argument(
        "--verify",
        action="store_true",
        help="Verify matchplay links exist in the database"
    )
    action_group.add_argument(
        "--verify-backup",
        action="store_true",
        help="Verify a backup file is valid"
    )
    action_group.add_argument(
        "--list",
        action="store_true",
        help="List available backup files"
    )

    # Additional arguments
    parser.add_argument(
        "--input",
        type=Path,
        help="Input backup file for restore or verify-backup"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for backup (default: backups/matchplay_links_TIMESTAMP.json)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="For restore: validate without making changes"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("MNP Matchplay Links Backup/Restore")
    print("=" * 60)
    print()

    if args.backup:
        print("Creating backup of matchplay account links...")
        print()
        success, message = backup_matchplay_links(args.output)
        print()
        if success:
            print(f"SUCCESS: {message}")
        else:
            print(f"ERROR: {message}")
            sys.exit(1)

    elif args.restore:
        if not args.input:
            parser.error("--restore requires --input to specify backup file")

        print(f"Restoring matchplay links from: {args.input}")
        if args.dry_run:
            print("[DRY RUN MODE - No changes will be made]")
        print()

        success, message = restore_matchplay_links(args.input, dry_run=args.dry_run)
        print()
        if success:
            print(f"SUCCESS: {message}")
        else:
            print(f"ERROR: {message}")
            sys.exit(1)

    elif args.verify:
        print("Verifying matchplay links in database...")
        print()
        has_links, message, counts = verify_matchplay_links()

        print("Table record counts:")
        for table_name, count in counts.items():
            if count is None:
                print(f"  {table_name}: TABLE MISSING")
            else:
                print(f"  {table_name}: {count}")
        print()

        if has_links:
            print(f"SUCCESS: {message}")
        else:
            print(f"WARNING: {message}")
            print()
            print("If you have production matchplay links, ensure you restore them")
            print("from a backup before proceeding with database operations.")
            sys.exit(1)

    elif args.verify_backup:
        if not args.input:
            parser.error("--verify-backup requires --input to specify backup file")

        print(f"Verifying backup file: {args.input}")
        print()
        is_valid, message, info = verify_backup_file(args.input)

        if is_valid:
            print(f"Backup version: {info.get('backup_version')}")
            print(f"Created at: {info.get('created_at')}")
            print()
            print("Table record counts:")
            for table_name, count in info.get("tables", {}).items():
                print(f"  {table_name}: {count}")
            print()
            print(f"SUCCESS: {message}")
        else:
            print(f"ERROR: {message}")
            sys.exit(1)

    elif args.list:
        print("Available backup files:")
        print()
        backups = list_backups()

        if not backups:
            print("  No backup files found in backups/ directory")
        else:
            for backup in backups:
                status = "VALID" if backup["is_valid"] else "INVALID"
                links = backup["account_links"]
                created = backup.get("created_at", "unknown")[:19] if backup.get("created_at") else "unknown"
                print(f"  {backup['filename']}")
                print(f"    Status: {status}, Links: {links}, Created: {created}")
                print()


if __name__ == "__main__":
    main()
