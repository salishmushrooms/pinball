#!/usr/bin/env python3
"""
MNP Team Venue Pick Frequency Report Generator

Shows what machines a team picks most often at a specific venue,
separated by doubles rounds and singles rounds.
"""

import json
import os
import glob
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any


class TeamVenuePickFrequencyReporter:
    """Generate pick frequency reports for a team at a specific venue."""

    def __init__(self, config_path: str):
        """Initialize reporter with configuration file."""
        self.config = self._load_config(config_path)
        self.season = str(self.config['season'])
        self.team_key = self.config['team']['key']
        self.team_name = self.config['team']['name']
        self.team_home_venue_key = self.config['team_home_venue_key']
        self.target_venue_key = self.config['target_venue']['key']
        self.target_venue_name = self.config['target_venue']['name']

        # Optional: filter to only current machines at venue
        self.current_machines = self.config.get('current_machines', None)

        # Data storage
        # doubles_picks: Counter of machines picked in doubles rounds (R4 home, R1 away)
        # singles_picks: Counter of machines picked in singles rounds (R2 home, R3 away)
        self.doubles_picks = Counter()
        self.singles_picks = Counter()

        self.machine_variations = {}
        self.machine_aliases = {}

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)

    def load_machine_variations(self) -> None:
        """Load machine name variations for data cleaning."""
        variations_file = "machine_variations.json"
        try:
            with open(variations_file, 'r') as f:
                variations_data = json.load(f)
                self.machine_variations = variations_data

                # Convert variations format to alias mapping
                self.machine_aliases = {}
                for canonical_key, machine_info in variations_data.items():
                    if isinstance(machine_info, dict) and 'variations' in machine_info:
                        self.machine_aliases[canonical_key] = canonical_key
                        for variation in machine_info['variations']:
                            self.machine_aliases[variation.lower()] = canonical_key
                            self.machine_aliases[variation] = canonical_key

            print(f"Loaded machine variations for {len(variations_data)} machines")
        except FileNotFoundError:
            print(f"Warning: {variations_file} not found.")
        except json.JSONDecodeError:
            print(f"Warning: Error reading {variations_file}.")

    def normalize_machine_key(self, machine_key: str) -> str:
        """Normalize machine key using alias mapping."""
        if machine_key in self.machine_aliases:
            return self.machine_aliases[machine_key]
        cleaned_key = machine_key.strip()
        if cleaned_key in self.machine_aliases:
            return self.machine_aliases[cleaned_key]
        return cleaned_key

    def get_machine_display_name(self, machine_key: str) -> str:
        """Get the full display name for a machine."""
        normalized_key = self.normalize_machine_key(machine_key)
        if normalized_key in self.machine_variations:
            info = self.machine_variations[normalized_key]
            if isinstance(info, dict):
                return info.get('name', normalized_key)
        return normalized_key

    def process_matches(self, data_path: str) -> None:
        """Process all matches at target venue involving target team."""
        matches_pattern = f"{data_path}/season-{self.season}/matches/*.json"
        processed_count = 0

        for match_file in glob.glob(matches_pattern):
            with open(match_file, 'r') as f:
                match_data = json.load(f)

            # Filter: only target venue
            if match_data.get('venue', {}).get('key') != self.target_venue_key:
                continue

            # Filter: only matches with target team
            home_team = match_data.get('home', {}).get('key')
            away_team = match_data.get('away', {}).get('key')

            if home_team != self.team_key and away_team != self.team_key:
                continue

            # Determine if team is home at this venue
            is_team_home = (home_team == self.team_key)

            # Process rounds
            for round_data in match_data.get('rounds', []):
                round_num = round_data['n']

                for game in round_data.get('games', []):
                    if not game.get('done', False):
                        continue

                    machine = self.normalize_machine_key(game['machine'])

                    # Filter to current machines if specified
                    if self.current_machines and machine not in self.current_machines:
                        continue

                    # Determine if team picked this machine and what type of round
                    if is_team_home:
                        # Home: team picks R2 (singles) and R4 (doubles)
                        if round_num == 2:
                            # Singles round
                            self.singles_picks[machine] += 1
                        elif round_num == 4:
                            # Doubles round
                            self.doubles_picks[machine] += 1
                    else:
                        # Away: team picks R1 (doubles) and R3 (singles)
                        if round_num == 1:
                            # Doubles round
                            self.doubles_picks[machine] += 1
                        elif round_num == 3:
                            # Singles round
                            self.singles_picks[machine] += 1

            processed_count += 1

        print(f"Processed {processed_count} matches at {self.target_venue_key} involving {self.team_key}")
        print(f"Found {sum(self.doubles_picks.values())} doubles picks")
        print(f"Found {sum(self.singles_picks.values())} singles picks")

    def generate_report(self) -> str:
        """Generate the pick frequency report."""
        report_lines = []
        report_lines.append(f"# {self.team_name} Machine Pick Frequency at {self.target_venue_name}")
        report_lines.append(f"## Season {self.season}")
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")

        if self.current_machines:
            report_lines.append(f"**Filtered to current machines at {self.target_venue_name}**")
            report_lines.append("")

        report_lines.append("---")
        report_lines.append("")

        # Analysis rules
        report_lines.append("## Pick Rules")
        report_lines.append("")
        is_home_venue = (self.target_venue_key == self.team_home_venue_key)
        if is_home_venue:
            report_lines.append(f"**{self.target_venue_name} is {self.team_name}'s home venue**")
            report_lines.append("- Team picks in **Round 2** (singles)")
            report_lines.append("- Team picks in **Round 4** (doubles)")
        else:
            report_lines.append(f"**{self.target_venue_name} is an away venue for {self.team_name}**")
            report_lines.append("- Team picks in **Round 1** (doubles)")
            report_lines.append("- Team picks in **Round 3** (singles)")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Summary
        total_doubles = sum(self.doubles_picks.values())
        total_singles = sum(self.singles_picks.values())
        total_picks = total_doubles + total_singles

        report_lines.append("## Summary")
        report_lines.append("")
        report_lines.append(f"| Pick Type | Count |")
        report_lines.append(f"|-----------|-------|")
        report_lines.append(f"| Doubles Rounds | {total_doubles} |")
        report_lines.append(f"| Singles Rounds | {total_singles} |")
        report_lines.append(f"| **Total Picks** | **{total_picks}** |")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Doubles picks
        report_lines.append("## Doubles Round Picks")
        report_lines.append("")
        report_lines.append("*Machines picked in 4-player rounds*")
        report_lines.append("")

        if self.doubles_picks:
            sorted_doubles = self.doubles_picks.most_common()
            report_lines.append(f"| Rank | Machine | Times Picked | % of Doubles |")
            report_lines.append(f"|------|---------|--------------|--------------|")

            for rank, (machine, count) in enumerate(sorted_doubles, 1):
                machine_name = self.get_machine_display_name(machine)
                percentage = (count / total_doubles * 100) if total_doubles > 0 else 0
                report_lines.append(f"| {rank} | {machine_name} | {count} | {percentage:.1f}% |")
        else:
            report_lines.append("*No doubles picks found*")

        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Singles picks
        report_lines.append("## Singles Round Picks")
        report_lines.append("")
        report_lines.append("*Machines picked in 2-player rounds*")
        report_lines.append("")

        if self.singles_picks:
            sorted_singles = self.singles_picks.most_common()
            report_lines.append(f"| Rank | Machine | Times Picked | % of Singles |")
            report_lines.append(f"|------|---------|--------------|--------------|")

            for rank, (machine, count) in enumerate(sorted_singles, 1):
                machine_name = self.get_machine_display_name(machine)
                percentage = (count / total_singles * 100) if total_singles > 0 else 0
                report_lines.append(f"| {rank} | {machine_name} | {count} | {percentage:.1f}% |")
        else:
            report_lines.append("*No singles picks found*")

        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Combined ranking
        report_lines.append("## Combined Ranking (All Picks)")
        report_lines.append("")

        combined_picks = Counter()
        for machine in set(list(self.doubles_picks.keys()) + list(self.singles_picks.keys())):
            combined_picks[machine] = self.doubles_picks[machine] + self.singles_picks[machine]

        if combined_picks:
            sorted_combined = combined_picks.most_common()
            report_lines.append(f"| Rank | Machine | Total Picks | Doubles | Singles |")
            report_lines.append(f"|------|---------|-------------|---------|---------|")

            for rank, (machine, total) in enumerate(sorted_combined, 1):
                machine_name = self.get_machine_display_name(machine)
                doubles = self.doubles_picks[machine]
                singles = self.singles_picks[machine]
                report_lines.append(f"| {rank} | {machine_name} | {total} | {doubles} | {singles} |")

        report_lines.append("")

        return "\n".join(report_lines)

    def save_report(self, output_path: str) -> None:
        """Save the generated report to file."""
        report = self.generate_report()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)

        print(f"Report saved to: {output_path}")


def main():
    """Main execution function."""
    import sys

    if len(sys.argv) != 2:
        print("Usage: python team_venue_pick_frequency_report.py <config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    # Initialize reporter
    reporter = TeamVenuePickFrequencyReporter(config_file)

    # Load and process data
    data_path = "mnp-data-archive"
    reporter.load_machine_variations()
    reporter.process_matches(data_path)

    # Generate and save report
    output_file = f"reports/output/{reporter.team_key}_{reporter.target_venue_key}_pick_frequency_season_{reporter.season}.md"
    reporter.save_report(output_file)


if __name__ == "__main__":
    main()
