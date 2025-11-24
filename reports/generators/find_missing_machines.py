#!/usr/bin/env python3
"""
Find machines that are missing from machine_variations.json
by comparing against machines used in actual match data.
"""

import json
import glob
import sys


def load_machine_variations(variations_file='machine_variations.json'):
    """Load existing machine variations."""
    try:
        with open(variations_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {variations_file} not found")
        return {}


def load_official_machines(machines_file='mnp-data-archive/machines.json'):
    """Load official machine definitions."""
    try:
        with open(machines_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {machines_file} not found")
        return {}


def extract_machines_from_matches(season, data_path='mnp-data-archive'):
    """Extract all unique machine keys from match data for a given season."""
    machines = set()

    matches_pattern = f"{data_path}/season-{season}/matches/*.json"

    for match_file in glob.glob(matches_pattern):
        try:
            with open(match_file, 'r') as f:
                match_data = json.load(f)

            for round_data in match_data.get('rounds', []):
                for game in round_data.get('games', []):
                    machine_key = game.get('machine')
                    if machine_key:
                        machines.add(machine_key.strip())
        except Exception as e:
            print(f"Error reading {match_file}: {e}")
            continue

    return machines


def find_missing_machines(season, variations_file='machine_variations.json',
                         machines_file='mnp-data-archive/machines.json'):
    """Find machines used in match data that are missing from variations file."""

    print(f"=== Analyzing Season {season} ===\n")

    # Load data
    variations = load_machine_variations(variations_file)
    official_machines = load_official_machines(machines_file)
    used_machines = extract_machines_from_matches(season)

    print(f"Machines in variations file: {len(variations)}")
    print(f"Machines in official machines.json: {len(official_machines)}")
    print(f"Unique machines used in season {season}: {len(used_machines)}\n")

    # Find missing machines
    missing = []
    for machine_key in sorted(used_machines):
        if machine_key not in variations:
            # Look up the official name
            official_name = None
            if machine_key in official_machines:
                machine_info = official_machines[machine_key]
                if isinstance(machine_info, dict):
                    official_name = machine_info.get('name', machine_key)

            missing.append({
                'key': machine_key,
                'name': official_name or machine_key
            })

    return missing, variations, official_machines


def generate_missing_entries(missing_machines):
    """Generate JSON entries for missing machines."""
    entries = {}

    for machine in missing_machines:
        key = machine['key']
        name = machine['name']

        # Generate common variations
        variations = [key.lower()]

        # Add the full name if different from key
        if name != key and name.lower() != key.lower():
            variations.append(name)

        entries[key] = {
            "name": name,
            "variations": variations
        }

    return entries


def main():
    if len(sys.argv) < 2:
        print("Usage: python find_missing_machines.py <season>")
        print("Example: python find_missing_machines.py 22")
        sys.exit(1)

    season = sys.argv[1]

    # Find missing machines
    missing, variations, official_machines = find_missing_machines(season)

    if not missing:
        print("✅ No missing machines found! All machines in season data are in machine_variations.json")
        return

    print(f"❌ Found {len(missing)} missing machines:\n")
    print("=" * 80)

    # Display missing machines
    for machine in missing:
        print(f"  {machine['key']:20} → {machine['name']}")

    print("\n" + "=" * 80)

    # Generate new entries
    new_entries = generate_missing_entries(missing)

    print("\n=== JSON Entries to Add to machine_variations.json ===\n")
    print(json.dumps(new_entries, indent=2))

    # Ask if user wants to update the file
    print("\n" + "=" * 80)
    print("\nTo update machine_variations.json:")
    print("1. Copy the JSON above")
    print("2. Add it to machine_variations.json (maintaining alphabetical order if desired)")
    print("3. Or run with --auto-update flag to automatically merge (future feature)")


if __name__ == "__main__":
    main()
