#!/usr/bin/env python3
"""
Script to add missing machine entries and variations to machine_variations.json.

This script:
1. Adds new machine entries for machines not in the variations file
2. Adds variations to existing entries where the machine name is a variant

Run this script once to update machine_variations.json, then re-run the ETL
to get the machines properly normalized.

Usage:
    python etl/add_missing_machines.py --dry-run    # Preview changes
    python etl/add_missing_machines.py              # Apply changes
"""

import argparse
import json
import sys
from pathlib import Path

VARIATIONS_FILE = Path(__file__).parent.parent / "machine_variations.json"

# New machines to add (machine_key -> full entry)
NEW_MACHINES = {
    "4Aces": {
        "name": "4 Aces",
        "variations": ["4 aces", "4aces", "four aces"]
    },
    "Alien": {
        "name": "Alien",
        "manufacturer": "Data East",
        "year": 1980,
        "variations": ["alien"]
    },
    "BarryOs": {
        "name": "Barry O's BBQ Challenge",
        "variations": ["barry o's bbq challenge", "barry os bbq challenge", "barryos", "barry o's"]
    },
    "BigGame": {
        "name": "Big Game",
        "manufacturer": "Stern",
        "year": 1980,
        "variations": ["big game", "biggame"]
    },
    "BuckRogers": {
        "name": "Buck Rogers",
        "manufacturer": "Gottlieb",
        "year": 1980,
        "variations": ["buck rogers", "buckrogers", "BR"]
    },
    "DrDude": {
        "name": "Dr. Dude",
        "manufacturer": "Bally",
        "year": 1990,
        "variations": ["dr dude", "drdude", "dr. dude", "DRD", "drd", "Dr Dude"]
    },
    "EightBallBeyond": {
        "name": "Eight Ball Beyond",
        "manufacturer": "Multimorphic",
        "year": 2024,
        "variations": ["eight ball beyond", "eightballbeyond", "8 ball beyond", "EBB"]
    },
    "MysteryC": {
        "name": "Mystery Castle",
        "variations": ["mystery castle", "mysterycastle", "Mystery Castle"]
    },
    "Sorcerer": {
        "name": "Sorcerer",
        "manufacturer": "Williams",
        "year": 1985,
        "variations": ["sorcerer", "Sorcerer - Williams", "sorcerer - williams"]
    },
    "SpringBreak": {
        "name": "Spring Break",
        "manufacturer": "Gottlieb",
        "year": 1987,
        "variations": ["spring break", "springbreak"]
    },
    "TimeMachine": {
        "name": "Time Machine",
        "manufacturer": "Data East",
        "year": 1988,
        "variations": ["time machine", "timemachine"]
    },
    "TCM": {
        "name": "Texas Chainsaw Massacre",
        "manufacturer": "Spooky",
        "year": 2022,
        "variations": ["tcm", "texas chainsaw massacre", "texaschainsawmassacre"]
    }
}

# Variations to add to existing entries (existing_key -> list of new variations)
ADD_VARIATIONS = {
    "BKSoR": ["Black Knight SOR", "black knight sor"],
    "Scooby-Doo": ["Scooby Doo", "scooby doo", "SD", "sd"],
    "007": [
        "James Bond '007",  # Smart quote version
        "James Bond 007",   # No quote version
        "james bond '007",
        "james bond 007"
    ]
}


def load_variations():
    """Load the current machine_variations.json"""
    with open(VARIATIONS_FILE, 'r') as f:
        return json.load(f)


def save_variations(data):
    """Save the updated machine_variations.json"""
    with open(VARIATIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')  # Add trailing newline


def add_missing_machines(dry_run=False):
    """Add missing machines and variations to the file"""

    print("=" * 60)
    print(f"Machine Variations Update {'(DRY RUN)' if dry_run else ''}")
    print("=" * 60)
    print()

    data = load_variations()
    changes_made = 0

    # Add new machine entries
    print("Adding NEW machine entries:")
    print("-" * 40)
    for key, entry in NEW_MACHINES.items():
        if key in data:
            print(f"  SKIP: {key} already exists")
        else:
            print(f"  ADD:  {key} -> {entry['name']}")
            if not dry_run:
                data[key] = entry
            changes_made += 1
    print()

    # Add variations to existing entries
    print("Adding variations to EXISTING entries:")
    print("-" * 40)
    for existing_key, new_variations in ADD_VARIATIONS.items():
        if existing_key not in data:
            print(f"  WARN: {existing_key} not found in file!")
            continue

        current_variations = set(data[existing_key].get('variations', []))
        added = []

        for var in new_variations:
            if var.lower() not in [v.lower() for v in current_variations]:
                added.append(var)
                if not dry_run:
                    data[existing_key]['variations'].append(var)

        if added:
            print(f"  {existing_key}: +{len(added)} variations")
            for var in added:
                print(f"    - {var}")
            changes_made += len(added)
        else:
            print(f"  {existing_key}: all variations already present")

    print()
    print("=" * 60)
    print(f"Summary: {changes_made} changes {'would be ' if dry_run else ''}made")
    print("=" * 60)

    if not dry_run and changes_made > 0:
        save_variations(data)
        print(f"\nSaved to {VARIATIONS_FILE}")
        print("\nNext steps:")
        print("  1. Review the changes in machine_variations.json")
        print("  2. Re-run the ETL to apply the new mappings:")
        print("     python etl/run_full_pipeline.py --seasons 18 19 20 21 22")
        print("  3. Export and import to production")
    elif dry_run:
        print("\nThis was a DRY RUN. No changes were made.")
        print("Run without --dry-run to apply changes.")


def main():
    parser = argparse.ArgumentParser(
        description='Add missing machine entries to machine_variations.json'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )

    args = parser.parse_args()
    add_missing_machines(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
