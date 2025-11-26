#!/usr/bin/env python3
"""
MNP Team Machine Comparison Report Generator

Compares two teams' scores on specific machines, grouped by machine.
Includes all scores regardless of venue (not filtered by venue).
"""

import json
import os
import glob
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any


class TeamMachineComparisonReporter:
    """Compare two teams' performance on specific machines."""

    def __init__(self, config_path: str):
        """Initialize reporter with configuration file."""
        self.config = self._load_config(config_path)
        self.season = self.config['season']
        self.team1_key = self.config['team1']['key']
        self.team1_name = self.config['team1']['name']
        self.team2_key = self.config['team2']['key']
        self.team2_name = self.config['team2']['name']
        self.target_machines = self.config['target_machines']

        # Data storage
        self.matches = []
        self.machine_data = defaultdict(lambda: {'team1': [], 'team2': []})
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
                        # Map canonical key to itself
                        self.machine_aliases[canonical_key] = canonical_key
                        # Map all variations to canonical key
                        for variation in machine_info['variations']:
                            self.machine_aliases[variation.lower()] = canonical_key
                            self.machine_aliases[variation] = canonical_key

            print(f"Loaded machine variations for {len(variations_data)} machines")
        except FileNotFoundError:
            print(f"Warning: {variations_file} not found. No alias mapping applied.")
        except json.JSONDecodeError:
            print(f"Warning: Error reading {variations_file}. No alias mapping applied.")

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

    def load_matches(self, data_path: str) -> None:
        """Load all matches for the specified season."""
        matches_pattern = f"{data_path}/season-{self.season}/matches/*.json"
        loaded_matches = []

        for match_file in glob.glob(matches_pattern):
            with open(match_file, 'r') as f:
                match_data = json.load(f)

            # Only include complete matches
            if match_data.get('state') == 'complete':
                loaded_matches.append(match_data)

        self.matches = loaded_matches
        print(f"Loaded {len(self.matches)} matches from season {self.season}")

    def extract_team_scores(self) -> None:
        """Extract scores for both teams on target machines."""
        for match in self.matches:
            # Build player lookup for this match
            match_players = {}
            for team_type in ['home', 'away']:
                for player in match[team_type].get('lineup', []):
                    match_players[player['key']] = {
                        'name': player['name'],
                        'team': match[team_type]['key'],
                        'team_name': match[team_type]['name'],
                        'ipr': player.get('IPR', 0)
                    }

            # Process each round
            for round_data in match.get('rounds', []):
                round_num = round_data['n']

                for game in round_data.get('games', []):
                    if not game.get('done', False):
                        continue

                    machine = self.normalize_machine_key(game['machine'])

                    # Only process target machines
                    if machine not in self.target_machines:
                        continue

                    # Determine reliable player positions based on round
                    if round_num in [1, 4]:  # 4-player rounds
                        reliable_positions = [1, 2, 3, 4]
                    else:  # 2-player rounds
                        reliable_positions = [1, 2]

                    # Extract scores for reliable positions
                    for pos in reliable_positions:
                        player_key = game.get(f'player_{pos}')
                        score_key = f'score_{pos}'

                        if player_key and score_key in game and player_key in match_players:
                            player_info = match_players[player_key]
                            team_key = player_info['team']

                            # Check if this player is on one of our target teams
                            target_team = None
                            if team_key == self.team1_key:
                                target_team = 'team1'
                            elif team_key == self.team2_key:
                                target_team = 'team2'

                            if target_team:
                                score_data = {
                                    'score': game[score_key],
                                    'player_key': player_key,
                                    'player_name': player_info['name'],
                                    'player_ipr': player_info['ipr'],
                                    'team_key': team_key,
                                    'team_name': player_info['team_name'],
                                    'round': round_num,
                                    'position': pos,
                                    'match_key': match['key'],
                                    'week': match.get('week', ''),
                                    'date': match.get('date', ''),
                                    'venue_key': match.get('venue', {}).get('key', ''),
                                    'venue_name': match.get('venue', {}).get('name', '')
                                }

                                self.machine_data[machine][target_team].append(score_data)

        # Count total scores
        total_team1 = sum(len(data['team1']) for data in self.machine_data.values())
        total_team2 = sum(len(data['team2']) for data in self.machine_data.values())
        print(f"Extracted {total_team1} scores for {self.team1_name}")
        print(f"Extracted {total_team2} scores for {self.team2_name}")
        print(f"Found data for {len(self.machine_data)} machines")

    def generate_report(self) -> str:
        """Generate the team comparison report."""
        report_lines = []
        report_lines.append(f"# Team Machine Comparison Report")
        report_lines.append(f"## {self.team1_name} vs {self.team2_name}")
        report_lines.append(f"**Season {self.season}**")
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Sort machines by display name
        sorted_machines = sorted(self.machine_data.keys(),
                                key=lambda m: self.get_machine_display_name(m))

        # Generate report for each machine
        for machine in sorted_machines:
            machine_name = self.get_machine_display_name(machine)
            data = self.machine_data[machine]

            team1_scores = data['team1']
            team2_scores = data['team2']

            # Skip machines with no scores for either team
            if not team1_scores and not team2_scores:
                continue

            report_lines.append(f"## {machine_name}")
            report_lines.append("")

            # Team 1 scores
            report_lines.append(f"### {self.team1_name}")
            report_lines.append("")

            if team1_scores:
                # Sort by score descending
                team1_scores.sort(key=lambda x: x['score'], reverse=True)

                report_lines.append("| Score | Player | IPR | Venue | Date |")
                report_lines.append("|-------|--------|-----|-------|------|")

                for score_data in team1_scores:
                    score = f"{score_data['score']:,}"
                    player = score_data['player_name']
                    ipr = score_data['player_ipr']
                    venue = score_data['venue_name']
                    date = score_data['date']
                    report_lines.append(f"| {score} | {player} | {ipr} | {venue} | {date} |")

                report_lines.append("")

                # Stats
                scores_only = [s['score'] for s in team1_scores]
                report_lines.append(f"**Stats:** {len(scores_only)} scores | ")
                report_lines.append(f"High: {max(scores_only):,} | ")
                report_lines.append(f"Average: {sum(scores_only) / len(scores_only):,.0f}")
                report_lines.append("")
            else:
                report_lines.append("*No scores recorded*")
                report_lines.append("")

            # Team 2 scores
            report_lines.append(f"### {self.team2_name}")
            report_lines.append("")

            if team2_scores:
                # Sort by score descending
                team2_scores.sort(key=lambda x: x['score'], reverse=True)

                report_lines.append("| Score | Player | IPR | Venue | Date |")
                report_lines.append("|-------|--------|-----|-------|------|")

                for score_data in team2_scores:
                    score = f"{score_data['score']:,}"
                    player = score_data['player_name']
                    ipr = score_data['player_ipr']
                    venue = score_data['venue_name']
                    date = score_data['date']
                    report_lines.append(f"| {score} | {player} | {ipr} | {venue} | {date} |")

                report_lines.append("")

                # Stats
                scores_only = [s['score'] for s in team2_scores]
                report_lines.append(f"**Stats:** {len(scores_only)} scores | ")
                report_lines.append(f"High: {max(scores_only):,} | ")
                report_lines.append(f"Average: {sum(scores_only) / len(scores_only):,.0f}")
                report_lines.append("")
            else:
                report_lines.append("*No scores recorded*")
                report_lines.append("")

            report_lines.append("---")
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
        print("Usage: python team_machine_comparison_report.py <config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    # Initialize reporter
    reporter = TeamMachineComparisonReporter(config_file)

    # Load and process data
    data_path = "mnp-data-archive"
    reporter.load_machine_variations()
    reporter.load_matches(data_path)
    reporter.extract_team_scores()

    # Generate and save report
    output_file = f"reports/output/team_comparison_{reporter.team1_key}_vs_{reporter.team2_key}_season_{reporter.season}.md"
    reporter.save_report(output_file)


if __name__ == "__main__":
    main()
