#!/usr/bin/env python3
"""
Machine deduplication and merge script.

Merges duplicate machine entries that have the same game but different machine_keys.
This happens when:
- machine_variations.json has duplicate entries (e.g., "Rush" AND "RUSH")
- Auto-created machines when source data doesn't match existing variations
- Trailing whitespace in machine keys from source data

The script will:
1. For each duplicate group, update all references to use the canonical key
2. Delete the orphaned machine entries (CASCADE handles aliases, stats, etc.)
3. Delete junk entries with 0 references
4. Verify data integrity after merge

Usage:
    python etl/merge_machines.py --dry-run    # Preview changes
    python etl/merge_machines.py              # Execute changes
"""

import argparse
import json
import logging
import sys

from sqlalchemy import text

from etl.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Each tuple: (canonical_key, [old_keys_to_merge])
# Canonical key is the one defined in machine_variations.json
MERGE_MAPPINGS = [
    ("Rush", ["RUSH"]),
    ("4Aces", ["4 Aces"]),
    ("Alien", ["ALIEN"]),
    ("AS", ["Alien Star"]),
    ("BanzaiRun", ["Banzai Run"]),
    ("BarryOs", ["Barry O's BBQ Challenge"]),
    ("BigGame", ["Big Game"]),
    ("BKSoR", ["Black Knight SOR"]),
    ("BOPP", ["Bobby Orr Power Player"]),
    ("BuckRogers", ["Buck Rogers", "BR"]),
    ("CF", ["Captain fantastic"]),
    ("DrDude", ["Dr Dude", "DRD"]),
    ("DRAGON", ["Dragon"]),
    ("SDND", ["Dungeons and Dragons Stern"]),
    ("EightBallBeyond", ["Eight Ball Beyond", "EBB"]),
    ("EJ", ["Elton john", "Elton John"]),
    ("FOO", ["Foo Fighters"]),
    ("FHRN", ["Funhouse Rudy's Nightmare", "Funhouse 2.0 Rudy's Nightmare"]),
    ("GF", ["Godfather", "The Godfather"]),
    ("Godzilla", ["Godzilla (Stern)"]),
    ("Guardians", ["Guardians of the Galaxy"]),
    ("HP", ["Harry potter", "Harry Potter"]),
    ("HW", ["Hot Wheels"]),
    ("007", ["James Bond '007", "James Bond 007"]),
    ("Junkyard", ["Junk Yard"]),
    (
        "LCA",
        [
            "Lights Camera Action",
            "Lights Camera Action!",
            "Lights camera action",
            "Light Camera Action",
        ],
    ),
    ("MB", ["Monster Bash"]),
    ("MotorDome", ["Motordome"]),
    ("MysteryC", ["Mystery Castle"]),
    ("PULP", ["Pulp fiction", "Pulp Fiction"]),
    ("QS", ["Quicksilver"]),
    ("Scooby-Doo", ["Scooby Doo", "SD"]),
    ("Sorcerer", ["Sorcerer - Williams"]),
    ("SpringBreak", ["Spring Break"]),
    ("SG", ["Star Gazer"]),
    ("TOM", ["Theater of magic"]),
    ("TimeMachine", ["Time Machine"]),
    ("TS", ["Toy Story"]),
    (
        "VEN",
        [
            "Venom",
            "Venom (L)",
            "Venom (R)",
            "Venom Left",
            "Venom Right",
            "Venom Pro",
        ],
    ),
    ("UXMEN", ["Uncanny X-men"]),
    ("DP", ["Deadpool"]),
    ("Galactic Tank Force", ["GTF"]),
    ("Outer Space", ["OuterSpace"]),
]

# Trailing-space entries with 0 scores — just delete
TRAILING_SPACE_DELETES = [
    "Bobby Orr Power Player ",
    "Captain fantastic ",
    "Deadpool ",
    "Dr Dude ",
    "Harry Potter ",
    "Lights Camera Action ",
    "This is not a machine ",
    "Trident ",
    "Venom ",
    "Viking ",
    "Woyal Wumble ",
]

# Junk entries to delete (0 scores, not real machines)
JUNK_DELETES = [
    "",  # empty string key
    "24",
    "Craig gary",
    "This is not a machine",
    "Twl",
    "Stern due",
    "Woyal Wumble",
]


def machine_exists(conn, key):
    """Check if a machine_key exists in the machines table."""
    result = conn.execute(
        text("SELECT 1 FROM machines WHERE machine_key = :key"),
        {"key": key},
    )
    return result.fetchone() is not None


def ensure_canonical_exists(conn, canonical_key, old_keys):
    """Create canonical machine entry if it doesn't exist, using metadata from old keys."""
    if machine_exists(conn, canonical_key):
        return

    # Get name from first old key that exists
    machine_name = canonical_key
    for old_key in old_keys:
        result = conn.execute(
            text("SELECT machine_name FROM machines WHERE machine_key = :key"),
            {"key": old_key},
        )
        row = result.fetchone()
        if row and row[0]:
            machine_name = row[0].strip()
            break

    conn.execute(
        text("INSERT INTO machines (machine_key, machine_name) VALUES (:key, :name)"),
        {"key": canonical_key, "name": machine_name},
    )
    logger.info(f"  Created canonical machine: {canonical_key} ({machine_name})")


def merge_one_key(conn, canonical, old_key, dry_run=False):
    """Merge a single old_key into canonical. Returns (scores, games, matches) counts."""
    # Count what will be affected
    scores_count = conn.execute(
        text("SELECT COUNT(*) FROM scores WHERE machine_key = :key"),
        {"key": old_key},
    ).scalar()

    games_count = conn.execute(
        text("SELECT COUNT(*) FROM games WHERE machine_key = :key"),
        {"key": old_key},
    ).scalar()

    matches_count = conn.execute(
        text("SELECT COUNT(*) FROM matches WHERE machines @> CAST(:old_jsonb AS jsonb)"),
        {"old_jsonb": json.dumps([old_key])},
    ).scalar()

    if dry_run:
        logger.info(
            f"  Would merge '{old_key}' -> '{canonical}': "
            f"{scores_count} scores, {games_count} games, {matches_count} match JSONBs"
        )
        return scores_count, games_count, matches_count

    # Step 1: Update RESTRICT FK tables (must update before deleting machine)
    conn.execute(
        text("UPDATE scores SET machine_key = :new WHERE machine_key = :old"),
        {"new": canonical, "old": old_key},
    )

    conn.execute(
        text("UPDATE games SET machine_key = :new WHERE machine_key = :old"),
        {"new": canonical, "old": old_key},
    )

    # Step 2: Update SET NULL FK tables
    conn.execute(
        text(
            "UPDATE matchplay_player_machine_stats SET machine_key = :new WHERE machine_key = :old"
        ),
        {"new": canonical, "old": old_key},
    )

    conn.execute(
        text("UPDATE matchplay_arena_mappings SET machine_key = :new WHERE machine_key = :old"),
        {"new": canonical, "old": old_key},
    )

    # Step 3: Handle venue_machines PK conflicts
    # Delete rows that would conflict (same venue+season already exists for canonical)
    conn.execute(
        text("""
            DELETE FROM venue_machines
            WHERE machine_key = :old
            AND EXISTS (
                SELECT 1 FROM venue_machines vm2
                WHERE vm2.venue_key = venue_machines.venue_key
                AND vm2.machine_key = :new
                AND vm2.season = venue_machines.season
            )
        """),
        {"new": canonical, "old": old_key},
    )

    # Update remaining rows (no conflict)
    conn.execute(
        text("UPDATE venue_machines SET machine_key = :new WHERE machine_key = :old"),
        {"new": canonical, "old": old_key},
    )

    # Step 4: Update matches.machines JSONB array (replace + deduplicate)
    if matches_count > 0:
        conn.execute(
            text("""
                UPDATE matches
                SET machines = (
                    SELECT jsonb_agg(DISTINCT replaced)
                    FROM (
                        SELECT
                            CASE
                                WHEN elem #>> '{}' = :old THEN to_jsonb(CAST(:new AS text))
                                ELSE elem
                            END AS replaced
                        FROM jsonb_array_elements(machines) AS elem
                    ) sub
                )
                WHERE machines @> CAST(:old_jsonb AS jsonb)
            """),
            {
                "new": canonical,
                "old": old_key,
                "old_jsonb": json.dumps([old_key]),
            },
        )

    # Step 5: Delete old machine (CASCADE handles aliases, percentiles, stats, picks)
    conn.execute(
        text("DELETE FROM machines WHERE machine_key = :key"),
        {"key": old_key},
    )

    logger.info(
        f"  Merged '{old_key}' -> '{canonical}': "
        f"{scores_count} scores, {games_count} games, {matches_count} match JSONBs"
    )

    return scores_count, games_count, matches_count


def safe_delete_machine(conn, key, dry_run=False):
    """Delete a machine only if it has zero references in games and scores."""
    if not machine_exists(conn, key):
        return False

    score_count = conn.execute(
        text("SELECT COUNT(*) FROM scores WHERE machine_key = :key"),
        {"key": key},
    ).scalar()

    game_count = conn.execute(
        text("SELECT COUNT(*) FROM games WHERE machine_key = :key"),
        {"key": key},
    ).scalar()

    if score_count > 0 or game_count > 0:
        logger.error(f"  REFUSING to delete '{key}' — has {score_count} scores, {game_count} games")
        return False

    if dry_run:
        logger.info(f"  Would delete: '{key}'")
    else:
        conn.execute(
            text("DELETE FROM machines WHERE machine_key = :key"),
            {"key": key},
        )
        logger.info(f"  Deleted: '{key}'")

    return True


def merge_machines(dry_run=False):
    """Main merge logic."""
    logger.info("=" * 60)
    logger.info(f"Machine Deduplication {'(DRY RUN)' if dry_run else ''}")
    logger.info("=" * 60)

    # Count totals before
    with db.engine.connect() as check_conn:
        pre_machine_count = check_conn.execute(text("SELECT COUNT(*) FROM machines")).scalar()
        pre_score_count = check_conn.execute(text("SELECT COUNT(*) FROM scores")).scalar()

    logger.info(f"Before: {pre_machine_count} machines, {pre_score_count} scores")
    logger.info("")

    with db.engine.begin() as conn:
        grand_scores = 0
        grand_games = 0
        grand_matches = 0
        merges_done = 0

        # Phase 1: Merge duplicate groups
        logger.info("Phase 1: Merging duplicate machine groups")
        logger.info("-" * 40)

        for canonical, old_keys in MERGE_MAPPINGS:
            # Filter to old_keys that actually exist
            existing_old = [k for k in old_keys if machine_exists(conn, k)]
            if not existing_old:
                continue

            logger.info(f"\n  {canonical} <- {existing_old}")

            if not dry_run:
                ensure_canonical_exists(conn, canonical, existing_old)

            for old_key in existing_old:
                s, g, m = merge_one_key(conn, canonical, old_key, dry_run)
                grand_scores += s
                grand_games += g
                grand_matches += m

            merges_done += 1

        # Phase 2: Delete trailing-space entries
        logger.info("\n")
        logger.info("Phase 2: Deleting trailing-space entries")
        logger.info("-" * 40)

        deleted_trailing = 0
        for key in TRAILING_SPACE_DELETES:
            if safe_delete_machine(conn, key, dry_run):
                deleted_trailing += 1

        # Phase 3: Delete junk entries
        logger.info("\n")
        logger.info("Phase 3: Deleting junk entries")
        logger.info("-" * 40)

        deleted_junk = 0
        for key in JUNK_DELETES:
            if safe_delete_machine(conn, key, dry_run):
                deleted_junk += 1

        # Phase 4: Verification
        logger.info("\n")
        logger.info("Phase 4: Verification")
        logger.info("-" * 40)

        post_machine_count = conn.execute(text("SELECT COUNT(*) FROM machines")).scalar()
        post_score_count = conn.execute(text("SELECT COUNT(*) FROM scores")).scalar()

        orphaned_scores = conn.execute(
            text("""
                SELECT COUNT(*) FROM scores s
                WHERE NOT EXISTS (
                    SELECT 1 FROM machines m WHERE m.machine_key = s.machine_key
                )
            """)
        ).scalar()

        orphaned_games = conn.execute(
            text("""
                SELECT COUNT(*) FROM games g
                WHERE NOT EXISTS (
                    SELECT 1 FROM machines m WHERE m.machine_key = g.machine_key
                )
            """)
        ).scalar()

        logger.info(f"  Machines: {pre_machine_count} -> {post_machine_count}")
        logger.info(f"  Scores: {pre_score_count} -> {post_score_count}")
        logger.info(f"  Orphaned scores: {orphaned_scores}")
        logger.info(f"  Orphaned games: {orphaned_games}")

        if orphaned_scores > 0 or orphaned_games > 0:
            logger.error("  ORPHANED REFERENCES DETECTED!")

        if pre_score_count != post_score_count:
            logger.error("  SCORE COUNT CHANGED — data may have been lost!")

        # Summary
        logger.info("\n")
        logger.info("=" * 60)
        logger.info("Summary:")
        logger.info(f"  Merge groups processed: {merges_done}")
        logger.info(f"  Scores re-pointed: {grand_scores}")
        logger.info(f"  Games re-pointed: {grand_games}")
        logger.info(f"  Match JSONBs updated: {grand_matches}")
        logger.info(f"  Trailing-space entries deleted: {deleted_trailing}")
        logger.info(f"  Junk entries deleted: {deleted_junk}")
        logger.info("=" * 60)

        if dry_run:
            logger.info("")
            logger.info("This was a DRY RUN. No changes were made.")
            logger.info("Run without --dry-run to apply changes.")


def main():
    parser = argparse.ArgumentParser(description="Merge duplicate machine entries in the database")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )

    args = parser.parse_args()

    try:
        db.connect()
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    try:
        merge_machines(dry_run=args.dry_run)
    finally:
        db.close()


if __name__ == "__main__":
    main()
