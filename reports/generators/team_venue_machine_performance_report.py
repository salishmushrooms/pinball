#!/usr/bin/env python3
"""
MNP Team Venue Machine Performance Report Generator

Analyzes team performance on specific machines at a specific venue,
calculating points earned by team vs opponents, sorted by total points.
"""

import json
import os
import glob
import statistics
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any


class TeamVenueMachinePerformanceReporter:
    """Generate team performance reports for specific venue."""

    def __init__(self, config_path: str):
        """Initialize reporter with configuration file."""
        self.config = self._load_config(config_path)
        self.season = str(self.config['season'])
        self.target_team_key = self.config['team']['key']
        self.target_team_name = self.config['team']['name']
        self.target_venue_key = self.config['target_venue']['key']
        self.target_venue_name = self.config['target_venue']['name']
        self.team_home_venue_key = self.config['team_home_venue_key']

        # Data storage: machine -> {team_points, opponent_points, scores}
        self.machine_data = defaultdict(lambda: {
            'team_points': 0,
            'opponent_points': 0,
            'scores': []
        })

        self.machine_names = {}
        self.machine_aliases = {}

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with open(config_path, 'r') as f:
            return json.load(f)

    def load_machine_names(self, data_path: str) -> None:
        """Load machine name mappings from machines.json and aliases."""
        # Load official machine names
        machines_file = f"{data_path}/machines.json"
        try:
            with open(machines_file, 'r') as f:
                machines_data = json.load(f)
                for key, data in machines_data.items():
                    self.machine_names[key] = data.get('name', key)
            print(f"Loaded {len(self.machine_names)} machine name mappings")
        except FileNotFoundError:
            print(f"Warning: {machines_file} not found. Using machine keys as names.")
        except json.JSONDecodeError:
            print(f"Warning: Error reading {machines_file}. Using machine keys as names.")

        # Load machine variations
        variations_file = "machine_variations.json"
        try:
            with open(variations_file, 'r') as f:
                variations_data = json.load(f)
                self.machine_aliases = {}
                alias_count = 0
                for canonical_key, machine_info in variations_data.items():
                    if isinstance(machine_info, dict) and 'variations' in machine_info:
                        for variation in machine_info['variations']:
                            self.machine_aliases[variation.lower()] = canonical_key
                            self.machine_aliases[variation] = canonical_key
                            alias_count += 1
            print(f"Loaded {alias_count} machine variations")
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
        display_name = self.machine_names.get(normalized_key, normalized_key)
        return display_name.strip()

    def _get_team_positions_for_round(self, round_num: int, is_home_at_venue: bool) -> List[int]:
        """
        Determine which player positions belong to the target team based on round and home/away status.

        At HOME venue: Team picks rounds 2 & 4, opponent picks rounds 1 & 3
        - Round 1 (4-player): Team is players 2, 4
        - Round 2 (2-player): Team is player 1
        - Round 3 (2-player): Team is player 2
        - Round 4 (4-player): Team is players 1, 3

        At AWAY venues: Team picks rounds 1 & 3, opponent picks rounds 2 & 4
        - Round 1 (4-player): Team is players 1, 3
        - Round 2 (2-player): Team is player 2
        - Round 3 (2-player): Team is player 1
        - Round 4 (4-player): Team is players 2, 4
        """
        if is_home_at_venue:
            # Home positions
            if round_num == 1:
                return [2, 4]
            elif round_num == 2:
                return [1]
            elif round_num == 3:
                return [2]
            elif round_num == 4:
                return [1, 3]
        else:
            # Away positions
            if round_num == 1:
                return [1, 3]
            elif round_num == 2:
                return [2]
            elif round_num == 3:
                return [1]
            elif round_num == 4:
                return [2, 4]
        return []

    def _process_match(self, match: Dict[str, Any]) -> None:
        """Process a single match and extract team performance data."""
        # Determine if target team is home or away at this venue
        is_home_at_venue = (match['home']['key'] == self.target_team_key)
        is_away_at_venue = (match['away']['key'] == self.target_team_key)

        if not (is_home_at_venue or is_away_at_venue):
            return  # Target team not in this match

        # Process each round
        for round_data in match.get('rounds', []):
            round_num = round_data['n']

            for game in round_data.get('games', []):
                if not game.get('done', False):
                    continue

                machine = self.normalize_machine_key(game['machine'])

                # Get team positions for this round
                team_positions = self._get_team_positions_for_round(round_num, is_home_at_venue)

                # Calculate points
                team_points = 0
                opponent_points = 0
                all_scores = []

                # Collect all player scores and points
                for pos in range(1, 5):
                    points_key = f'points_{pos}'
                    score_key = f'score_{pos}'

                    if points_key in game and score_key in game:
                        points = game[points_key]
                        score = game[score_key]

                        if pos in team_positions:
                            team_points += points
                            all_scores.append(score)
                        else:
                            opponent_points += points
                            all_scores.append(score)

                # Store the data
                self.machine_data[machine]['team_points'] += team_points
                self.machine_data[machine]['opponent_points'] += opponent_points
                self.machine_data[machine]['scores'].extend(all_scores)

    def load_and_process_matches(self, data_path: str) -> None:
        """Load all matches at target venue with target team."""
        matches_pattern = f"{data_path}/season-{self.season}/matches/*.json"
        processed_count = 0

        for match_file in glob.glob(matches_pattern):
            with open(match_file, 'r') as f:
                match_data = json.load(f)

            # Check if match was at target venue
            if match_data.get('venue', {}).get('key') != self.target_venue_key:
                continue

            # Check if target team was in the match
            home_team = match_data.get('home', {}).get('key')
            away_team = match_data.get('away', {}).get('key')

            if home_team == self.target_team_key or away_team == self.target_team_key:
                self._process_match(match_data)
                processed_count += 1

        print(f"Processed {processed_count} matches at {self.target_venue_key} involving {self.target_team_key}")
        print(f"Found data for {len(self.machine_data)} unique machines")

    def generate_report(self) -> str:
        """Generate the performance report."""
        if not self.machine_data:
            return f"No data found for {self.target_team_name} at {self.target_venue_name}"

        report_lines = []
        report_lines.append(f"# {self.target_team_name} Performance at {self.target_venue_name}")
        report_lines.append(f"## Season {self.season}")
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Calculate summary statistics
        total_team_points = sum(data['team_points'] for data in self.machine_data.values())
        total_opponent_points = sum(data['opponent_points'] for data in self.machine_data.values())
        total_points = total_team_points + total_opponent_points

        if total_points > 0:
            team_pops = (total_team_points / total_points) * 100
        else:
            team_pops = 0

        report_lines.append("## Overall Performance")
        report_lines.append("")
        report_lines.append(f"| Metric | Value |")
        report_lines.append(f"|--------|-------|")
        report_lines.append(f"| **{self.target_team_name} Points** | {total_team_points:.1f} |")
        report_lines.append(f"| **Opponent Points** | {total_opponent_points:.1f} |")
        report_lines.append(f"| **Total Points** | {total_points:.1f} |")
        report_lines.append(f"| **{self.target_team_name} POPS** | {team_pops:.1f}% |")
        report_lines.append(f"| **Machines Analyzed** | {len(self.machine_data)} |")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Sort machines by total points (descending)
        sorted_machines = sorted(
            self.machine_data.items(),
            key=lambda x: x[1]['team_points'] + x[1]['opponent_points'],
            reverse=True
        )

        report_lines.append("## Machine Performance (Sorted by Total Points)")
        report_lines.append("")
        report_lines.append("*Machines ranked by total points across all games*")
        report_lines.append("")

        for machine_key, data in sorted_machines:
            machine_name = self.get_machine_display_name(machine_key)

            team_points = data['team_points']
            opponent_points = data['opponent_points']
            total_machine_points = team_points + opponent_points

            if total_machine_points > 0:
                pops = (team_points / total_machine_points) * 100
            else:
                pops = 0

            # Calculate median score
            scores = data['scores']
            if scores:
                median_score = statistics.median(scores)
            else:
                median_score = 0

            report_lines.append(f"### {machine_name}")
            report_lines.append("")
            report_lines.append(f"| Metric | Value |")
            report_lines.append(f"|--------|-------|")
            report_lines.append(f"| **{self.target_team_name} Points** | {team_points:.1f} |")
            report_lines.append(f"| **Opponent Points** | {opponent_points:.1f} |")
            report_lines.append(f"| **Total Points** | {total_machine_points:.1f} |")
            report_lines.append(f"| **POPS** | {pops:.1f}% |")
            report_lines.append(f"| **Median Score** | {int(median_score):,} |")
            report_lines.append(f"| **Games Played** | {len(scores)} |")
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
        print("Usage: python team_venue_machine_performance_report.py <config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    # Initialize reporter
    reporter = TeamVenueMachinePerformanceReporter(config_file)

    # Load and process data
    data_path = "mnp-data-archive"
    reporter.load_machine_names(data_path)
    reporter.load_and_process_matches(data_path)

    # Generate and save report
    output_file = f"reports/output/{reporter.target_team_key}_{reporter.target_venue_key}_performance_season_{reporter.season}.md"
    reporter.save_report(output_file)


if __name__ == "__main__":
    main()
