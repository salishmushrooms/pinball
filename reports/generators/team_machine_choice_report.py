#!/usr/bin/env python3
"""
MNP Team Machine Choice Report Generator

Analyzes a team's machine choices (home vs away picks) on specific machines.
Filters scores based on:
- Home venue (rounds 2 & 4 = team's choice)
- Away venue (rounds 1 & 3 = team's choice)
"""

import json
import os
import glob
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any


class TeamMachineChoiceReporter:
    """Analyze a team's machine selection patterns and performance."""

    def __init__(self, config_path: str):
        """Initialize reporter with configuration file."""
        self.config = self._load_config(config_path)

        # Handle single or multiple seasons
        season_config = self.config['seasons']
        if isinstance(season_config, list):
            self.seasons = season_config
        else:
            self.seasons = [str(season_config)]

        self.team_key = self.config['team']['key']
        self.team_name = self.config['team']['name']
        self.home_venue_key = self.config['home_venue_key']
        self.target_machines = self.config['target_machines']

        # Data storage
        self.matches = []
        # Structure: machine -> {'team_picked': [], 'opponent_picked': []}
        self.machine_data = defaultdict(lambda: {'team_picked': [], 'opponent_picked': []})
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
        """Load all matches for the specified seasons."""
        loaded_matches = []

        for season in self.seasons:
            matches_pattern = f"{data_path}/season-{season}/matches/*.json"
            season_matches = 0

            for match_file in glob.glob(matches_pattern):
                with open(match_file, 'r') as f:
                    match_data = json.load(f)

                # Only include complete matches
                if match_data.get('state') == 'complete':
                    loaded_matches.append(match_data)
                    season_matches += 1

            print(f"Loaded {season_matches} matches from season {season}")

        self.matches = loaded_matches
        print(f"Total: {len(self.matches)} matches from season(s) {', '.join(self.seasons)}")

    def extract_team_choices(self) -> None:
        """Extract scores based on who picked the machine (team vs opponent)."""
        for match in self.matches:
            venue_key = match.get('venue', {}).get('key', '')

            # Determine if this is a home or away match for our team
            home_team = match['home']['key']
            away_team = match['away']['key']

            is_team_home = (home_team == self.team_key)
            is_team_away = (away_team == self.team_key)

            # Skip matches where our team isn't playing
            if not is_team_home and not is_team_away:
                continue

            # Determine if venue is team's home venue
            is_home_venue = (venue_key == self.home_venue_key)

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

                    # Determine who picked this machine based on venue and round
                    team_picked_machine = False

                    if is_home_venue:
                        # At home venue: team picks rounds 2 & 4
                        if round_num in [2, 4]:
                            team_picked_machine = True
                    else:
                        # At away venue: team picks rounds 1 & 3
                        if round_num in [1, 3]:
                            team_picked_machine = True

                    # Determine reliable player positions based on round
                    if round_num in [1, 4]:  # 4-player rounds
                        reliable_positions = [1, 2, 3, 4]
                    else:  # 2-player rounds
                        reliable_positions = [1, 2]

                    # Extract scores for reliable positions (only for our team)
                    for pos in reliable_positions:
                        player_key = game.get(f'player_{pos}')
                        score_key = f'score_{pos}'

                        if player_key and score_key in game and player_key in match_players:
                            player_info = match_players[player_key]

                            # Only include scores from our team
                            if player_info['team'] != self.team_key:
                                continue

                            score_data = {
                                'score': game[score_key],
                                'player_key': player_key,
                                'player_name': player_info['name'],
                                'player_ipr': player_info['ipr'],
                                'team_key': player_info['team'],
                                'team_name': player_info['team_name'],
                                'round': round_num,
                                'position': pos,
                                'match_key': match['key'],
                                'week': match.get('week', ''),
                                'date': match.get('date', ''),
                                'venue_key': venue_key,
                                'venue_name': match.get('venue', {}).get('name', ''),
                                'is_home_venue': is_home_venue,
                                'opponent': away_team if is_team_home else home_team
                            }

                            if team_picked_machine:
                                self.machine_data[machine]['team_picked'].append(score_data)
                            else:
                                self.machine_data[machine]['opponent_picked'].append(score_data)

        # Count total scores
        total_team_picked = sum(len(data['team_picked']) for data in self.machine_data.values())
        total_opponent_picked = sum(len(data['opponent_picked']) for data in self.machine_data.values())
        print(f"Extracted {total_team_picked} scores when {self.team_name} picked the machine")
        print(f"Extracted {total_opponent_picked} scores when opponent picked the machine")
        print(f"Found data for {len(self.machine_data)} machines")

    def generate_report(self) -> str:
        """Generate the machine choice report."""
        report_lines = []
        report_lines.append(f"# Team Machine Choice Report")
        report_lines.append(f"## {self.team_name}")
        report_lines.append(f"**Seasons {', '.join(self.seasons)}**")
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")
        report_lines.append("### Analysis Rules")
        report_lines.append("")
        report_lines.append(f"- **Home Venue** ({self.home_venue_key}): Team picks machines in Rounds 2 & 4")
        report_lines.append(f"- **Away Venues**: Team picks machines in Rounds 1 & 3")
        report_lines.append("- Only scores by team members included")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Summary statistics
        report_lines.append("## Summary")
        report_lines.append("")

        total_team_picks = 0
        total_opponent_picks = 0
        machines_team_picked = 0
        machines_opponent_picked = 0

        for machine, data in self.machine_data.items():
            team_count = len(data['team_picked'])
            opp_count = len(data['opponent_picked'])

            total_team_picks += team_count
            total_opponent_picks += opp_count

            if team_count > 0:
                machines_team_picked += 1
            if opp_count > 0:
                machines_opponent_picked += 1

        report_lines.append("| Metric | Count |")
        report_lines.append("|--------|-------|")
        report_lines.append(f"| **Machines Tracked** | {len(self.target_machines)} |")
        report_lines.append(f"| **Machines Team Picked** | {machines_team_picked} |")
        report_lines.append(f"| **Machines Opponent Picked** | {machines_opponent_picked} |")
        report_lines.append(f"| **Total Scores (Team Picked)** | {total_team_picks} |")
        report_lines.append(f"| **Total Scores (Opponent Picked)** | {total_opponent_picks} |")
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

            team_picked_scores = data['team_picked']
            opponent_picked_scores = data['opponent_picked']

            # Skip machines with no scores
            if not team_picked_scores and not opponent_picked_scores:
                continue

            report_lines.append(f"## {machine_name}")
            report_lines.append("")

            # Team picked section
            report_lines.append(f"### When {self.team_name} Picked This Machine")
            report_lines.append("")

            if team_picked_scores:
                # Sort by score descending
                team_picked_scores.sort(key=lambda x: x['score'], reverse=True)

                report_lines.append("| Score | Player | IPR | Venue | Date | Opponent |")
                report_lines.append("|-------|--------|-----|-------|------|----------|")

                for score_data in team_picked_scores:
                    score = f"{score_data['score']:,}"
                    player = score_data['player_name']
                    ipr = score_data['player_ipr']
                    venue = score_data['venue_name']
                    date = score_data['date']
                    opponent = score_data['opponent']
                    report_lines.append(f"| {score} | {player} | {ipr} | {venue} | {date} | {opponent} |")

                report_lines.append("")

                # Stats
                scores_only = [s['score'] for s in team_picked_scores]
                report_lines.append(f"**Stats:** {len(scores_only)} times picked | ")
                report_lines.append(f"High: {max(scores_only):,} | ")
                report_lines.append(f"Average: {sum(scores_only) / len(scores_only):,.0f}")
                report_lines.append("")
            else:
                report_lines.append("*Never picked this machine*")
                report_lines.append("")

            # Opponent picked section
            report_lines.append(f"### When Opponent Picked This Machine")
            report_lines.append("")

            if opponent_picked_scores:
                # Sort by score descending
                opponent_picked_scores.sort(key=lambda x: x['score'], reverse=True)

                report_lines.append("| Score | Player | IPR | Venue | Date | Opponent |")
                report_lines.append("|-------|--------|-----|-------|------|----------|")

                for score_data in opponent_picked_scores:
                    score = f"{score_data['score']:,}"
                    player = score_data['player_name']
                    ipr = score_data['player_ipr']
                    venue = score_data['venue_name']
                    date = score_data['date']
                    opponent = score_data['opponent']
                    report_lines.append(f"| {score} | {player} | {ipr} | {venue} | {date} | {opponent} |")

                report_lines.append("")

                # Stats
                scores_only = [s['score'] for s in opponent_picked_scores]
                report_lines.append(f"**Stats:** {len(scores_only)} times faced | ")
                report_lines.append(f"High: {max(scores_only):,} | ")
                report_lines.append(f"Average: {sum(scores_only) / len(scores_only):,.0f}")
                report_lines.append("")
            else:
                report_lines.append("*Opponent never picked this machine*")
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
        print("Usage: python team_machine_choice_report.py <config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    # Initialize reporter
    reporter = TeamMachineChoiceReporter(config_file)

    # Load and process data
    data_path = "mnp-data-archive"
    reporter.load_machine_variations()
    reporter.load_matches(data_path)
    reporter.extract_team_choices()

    # Generate and save report
    seasons_code = "-".join(reporter.seasons)
    output_file = f"reports/output/machine_choices_{reporter.team_key}_seasons_{seasons_code}.md"
    reporter.save_report(output_file)


if __name__ == "__main__":
    main()
