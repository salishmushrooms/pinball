#!/usr/bin/env python3
"""
MNP Venue Summary Report Generator

Generates detailed venue statistics including machine-specific scoring data,
player performance, and home team advantage analysis.
"""

import json
import os
import glob
import statistics
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any, Optional


class VenueSummaryReporter:
    """Generate comprehensive venue reports from MNP match data."""
    
    def __init__(self, config_path: str):
        """Initialize reporter with configuration file."""
        self.config = self._load_config(config_path)
        self.season = self.config['season']
        self.venue_code = self.config['target_venue']['code']
        self.venue_name = self.config['target_venue']['name']
        
        # Data storage
        self.matches = []
        self.machine_data = defaultdict(list)
        self.player_lookup = {}
        self.team_lookup = {}
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
                # Extract machine names from the nested structure
                for key, data in machines_data.items():
                    self.machine_names[key] = data.get('name', key)
            print(f"Loaded {len(self.machine_names)} machine name mappings")
        except FileNotFoundError:
            print(f"Warning: {machines_file} not found. Using machine keys as names.")
        except json.JSONDecodeError:
            print(f"Warning: Error reading {machines_file}. Using machine keys as names.")
        
        # Load machine variations for data cleaning
        variations_file = "machine_variations.json"
        try:
            with open(variations_file, 'r') as f:
                variations_data = json.load(f)
                # Convert variations format to alias mapping for backwards compatibility
                self.machine_aliases = {}
                alias_count = 0
                for canonical_key, machine_info in variations_data.items():
                    if isinstance(machine_info, dict) and 'variations' in machine_info:
                        for variation in machine_info['variations']:
                            self.machine_aliases[variation.lower()] = canonical_key
                            self.machine_aliases[variation] = canonical_key  # Keep case-sensitive mapping
                            alias_count += 1
            print(f"Loaded {alias_count} machine variations for data cleaning")
        except FileNotFoundError:
            print(f"Warning: {variations_file} not found. No alias mapping applied.")
        except json.JSONDecodeError:
            print(f"Warning: Error reading {variations_file}. No alias mapping applied.")
    
    def normalize_machine_key(self, machine_key: str) -> str:
        """Normalize machine key using alias mapping for data cleaning."""
        # First, check if this is an alias that should be mapped to a canonical key
        if machine_key in self.machine_aliases:
            return self.machine_aliases[machine_key]
        
        # Clean up trailing spaces and other normalization
        cleaned_key = machine_key.strip()
        
        # Check again after cleaning
        if cleaned_key in self.machine_aliases:
            return self.machine_aliases[cleaned_key]
        
        return cleaned_key
    
    def get_machine_display_name(self, machine_key: str) -> str:
        """Get the full display name for a machine, fallback to key if not found."""
        # First normalize the key
        normalized_key = self.normalize_machine_key(machine_key)
        
        # Return the official name if we have it, otherwise use the normalized key
        display_name = self.machine_names.get(normalized_key, normalized_key)
        
        # Always strip trailing spaces from display names
        return display_name.strip()
    
    def load_venue_matches(self, data_path: str) -> None:
        """Load all matches played at the target venue."""
        matches_pattern = f"{data_path}/season-{self.season}/matches/*.json"
        venue_matches = []
        
        for match_file in glob.glob(matches_pattern):
            with open(match_file, 'r') as f:
                match_data = json.load(f)
                
            # Check if match was played at target venue
            if match_data.get('venue', {}).get('key') == self.venue_code:
                if self.config['data_filters']['include_incomplete_matches'] or \
                   match_data.get('state') == 'complete':
                    venue_matches.append(match_data)
                    
        self.matches = venue_matches
        print(f"Loaded {len(self.matches)} matches for venue {self.venue_code}")
    
    def _extract_scores_from_match(self, match: Dict[str, Any]) -> None:
        """Extract individual game scores and metadata from match."""
        home_team = match['home']['key']
        away_team = match['away']['key']
        
        # Build player lookup for this match
        match_players = {}
        for team_type in ['home', 'away']:
            for player in match[team_type].get('lineup', []):
                match_players[player['key']] = {
                    'name': player['name'],
                    'team': match[team_type]['key'],
                    'team_name': match[team_type]['name'],
                    'ipr': player.get('IPR', 0),
                    'is_home': team_type == 'home'
                }
        
        # Process each round
        for round_data in match.get('rounds', []):
            round_num = round_data['n']
            
            for game in round_data.get('games', []):
                if not game.get('done', False):
                    continue
                    
                machine = self.normalize_machine_key(game['machine'])
                
                # Determine reliable player positions based on round
                if round_num in [1, 4]:  # 4-player rounds
                    reliable_positions = self.config['score_reliability']['rounds_1_4']['reliable_positions']
                else:  # 2-player rounds
                    reliable_positions = self.config['score_reliability']['rounds_2_3']['reliable_positions']
                
                # Extract scores for reliable positions
                for pos in reliable_positions:
                    player_key = game.get(f'player_{pos}')
                    score_key = f'score_{pos}'
                    
                    if player_key and score_key in game and player_key in match_players:
                        player_info = match_players[player_key]
                        
                        score_data = {
                            'score': game[score_key],
                            'player_key': player_key,
                            'player_name': player_info['name'],
                            'player_ipr': player_info['ipr'],
                            'team_key': player_info['team'],
                            'team_name': player_info['team_name'],
                            'is_home_team': player_info['is_home'],
                            'round': round_num,
                            'position': pos,
                            'match_key': match['key'],
                            'week': match.get('week', ''),
                            'date': match.get('date', '')
                        }
                        
                        self.machine_data[machine].append(score_data)
    
    def process_matches(self) -> None:
        """Process all loaded matches to extract scoring data."""
        for match in self.matches:
            self._extract_scores_from_match(match)
        
        total_games = sum(len(scores) for scores in self.machine_data.values())
        print(f"Processed {total_games} individual game scores across {len(self.machine_data)} machines")
    
    def _calculate_selection_analysis(self) -> Dict[str, List[Dict]]:
        """Calculate machine selection patterns by home/away teams."""
        home_picks = defaultdict(int)  # Rounds 2 & 4
        away_picks = defaultdict(int)  # Rounds 1 & 3
        
        # Process all matches to count machine selections
        for match in self.matches:
            for round_data in match.get('rounds', []):
                round_num = round_data['n']
                
                for game in round_data.get('games', []):
                    if not game.get('done', False):
                        continue
                    
                    machine = self.normalize_machine_key(game['machine'])
                    machine_name = self.get_machine_display_name(machine)
                    
                    # Count selections with weighting for game type
                    # Rounds 1 & 4 are 4-player (weight = 1 selection but more players)
                    # Rounds 2 & 3 are 2-player (weight = 1 selection but fewer players)
                    # For fair comparison, we'll count by number of times selected, not players
                    
                    if round_num in [2, 4]:  # Home team picks
                        home_picks[machine_name] += 1
                    elif round_num in [1, 3]:  # Away team picks
                        away_picks[machine_name] += 1
        
        # Sort by selection count
        home_sorted = sorted(home_picks.items(), key=lambda x: x[1], reverse=True)
        away_sorted = sorted(away_picks.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'home_picks': [{'machine': name, 'selections': count} for name, count in home_sorted],
            'away_picks': [{'machine': name, 'selections': count} for name, count in away_sorted]
        }
    
    def _calculate_machine_stats(self, machine: str, scores: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive statistics for a single machine."""
        if not scores:
            return {}
        
        score_values = [s['score'] for s in scores]
        
        # Basic statistics
        stats = {
            'machine': machine,
            'total_games': len(scores),
            'median_score': statistics.median(score_values),
            'percentile_75': statistics.quantiles(score_values, n=4)[2] if len(score_values) >= 4 else max(score_values),
            'percentile_90': statistics.quantiles(score_values, n=10)[8] if len(score_values) >= 10 else max(score_values),
            'high_score': max(score_values),
            'low_score': min(score_values)
        }
        
        # Find high score details
        high_score_game = max(scores, key=lambda x: x['score'])
        stats['high_score_player'] = high_score_game['player_name']
        stats['high_score_date'] = high_score_game['date']
        
        # Home team high score
        home_scores = [s for s in scores if s['is_home_team']]
        if home_scores:
            home_high = max(home_scores, key=lambda x: x['score'])
            stats['home_team_high_score'] = home_high['score']
            stats['home_team_high_score_player'] = home_high['player_name']
            stats['home_team_high_score_team'] = home_high['team_name']
        
        # Games by round
        round_counts = Counter(s['round'] for s in scores)
        stats['round_1_games'] = round_counts.get(1, 0)
        stats['round_2_games'] = round_counts.get(2, 0)
        stats['round_3_games'] = round_counts.get(3, 0)
        stats['round_4_games'] = round_counts.get(4, 0)
        
        return stats
    
    def generate_report(self) -> str:
        """Generate the complete venue summary report."""
        if not self.matches:
            return "No matches found for venue."
        
        # Calculate machine statistics
        machine_stats = []
        for machine, scores in self.machine_data.items():
            stats = self._calculate_machine_stats(machine, scores)
            if stats:
                machine_stats.append(stats)
        
        # Check output style
        output_style = self.config.get('output_format', {}).get('style', 'detailed')
        
        if output_style == 'simplified':
            return self._generate_simplified_report(machine_stats)
        else:
            return self._generate_detailed_report(machine_stats)
    
    def _generate_simplified_report(self, machine_stats: List[Dict]) -> str:
        """Generate simplified report format."""
        # Sort alphabetically by machine name
        machine_stats.sort(key=lambda x: self.get_machine_display_name(x['machine']))
        
        report_lines = []
        report_lines.append(f"# {self.venue_name} ({self.venue_code}) - Season {self.season} Summary (Simplified)")
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")
        
        # Venue overview
        total_matches = len(self.matches)
        total_games = sum(len(scores) for scores in self.machine_data.values())
        unique_machines = len(self.machine_data)
        
        report_lines.append(f"**{total_matches} matches | {total_games} total games | {unique_machines} unique machines**")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        for stats in machine_stats:
            machine_key = stats['machine']
            machine_name = self.get_machine_display_name(machine_key)
            
            # Calculate 50th percentile (median) - already have this
            median = stats['median_score']
            percentile_75 = stats['percentile_75']
            total_games = stats['total_games']
            
            report_lines.append(f"**{machine_name}** - {total_games} games")
            report_lines.append(f"50th: {int(median):,} | 75th: {int(percentile_75):,}")
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def _generate_detailed_report(self, machine_stats: List[Dict]) -> str:
        """Generate detailed report format."""
        # Sort by total games played
        machine_stats.sort(key=lambda x: x['total_games'], reverse=True)
        
        # Generate report
        report_lines = []
        report_lines.append(f"# {self.venue_name} ({self.venue_code}) - Season {self.season} Summary")
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # Venue overview
        total_matches = len(self.matches)
        total_games = sum(len(scores) for scores in self.machine_data.values())
        unique_machines = len(self.machine_data)
        
        report_lines.append("## 📊 Venue Overview")
        report_lines.append("")
        report_lines.append(f"| Metric | Value |")
        report_lines.append(f"|--------|-------|")
        report_lines.append(f"| **Total Matches** | {total_matches} |")
        report_lines.append(f"| **Total Games Played** | {total_games} |")
        report_lines.append(f"| **Unique Machines Played** | {unique_machines} |")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # Machine selection analysis
        selection_analysis = self._calculate_selection_analysis()
        
        report_lines.append("## 🎲 Machine Selection Analysis")
        report_lines.append("")
        
        # Most picked by home teams
        report_lines.append("### 🏠 Most Picked By Home Teams")
        report_lines.append("*Rounds 2 & 4 selections*")
        report_lines.append("")
        
        home_picks = selection_analysis['home_picks'][:10]  # Top 10
        if home_picks:
            for i, pick in enumerate(home_picks, 1):
                report_lines.append(f"{i}. **{pick['machine']}** - {pick['selections']} selections")
        else:
            report_lines.append("No home team selections recorded.")
        
        report_lines.append("")
        
        # Most picked by away teams
        report_lines.append("### ✈️ Most Picked By Away Teams") 
        report_lines.append("*Rounds 1 & 3 selections*")
        report_lines.append("")
        
        away_picks = selection_analysis['away_picks'][:10]  # Top 10
        if away_picks:
            for i, pick in enumerate(away_picks, 1):
                report_lines.append(f"{i}. **{pick['machine']}** - {pick['selections']} selections")
        else:
            report_lines.append("No away team selections recorded.")
        
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # Machine-by-machine breakdown
        report_lines.append("## 🎯 Machine Statistics")
        report_lines.append("")
        report_lines.append("*Machines ordered by total games played*")
        report_lines.append("")
        
        for i, stats in enumerate(machine_stats, 1):
            machine_key = stats['machine']
            machine_name = self.get_machine_display_name(machine_key)
            report_lines.append(f"### {i}. {machine_name} ({machine_key})")
            report_lines.append("")
            
            # Score Statistics Table
            report_lines.append("**📈 Score Statistics**")
            report_lines.append("")
            report_lines.append("| Statistic | Value |")
            report_lines.append("|-----------|-------|")
            report_lines.append(f"| Median Score | {int(stats['median_score']):,} |")
            report_lines.append(f"| 75th Percentile | {int(stats['percentile_75']):,} |")
            report_lines.append(f"| 90th Percentile | {int(stats['percentile_90']):,} |")
            report_lines.append(f"| High Score | {int(stats['high_score']):,} |")
            report_lines.append(f"| Low Score | {int(stats['low_score']):,} |")
            report_lines.append("")
            
            # Games Played Table
            report_lines.append("**🎮 Games Played**")
            report_lines.append("")
            report_lines.append("| Round | Games |")
            report_lines.append("|-------|-------|")
            report_lines.append(f"| Round 1 (Away Pick) | {stats['round_1_games']} |")
            report_lines.append(f"| Round 2 (Home Pick) | {stats['round_2_games']} |")
            report_lines.append(f"| Round 3 (Away Pick) | {stats['round_3_games']} |")
            report_lines.append(f"| Round 4 (Home Pick) | {stats['round_4_games']} |")
            report_lines.append(f"| **Total Games** | **{stats['total_games']}** |")
            report_lines.append("")
            
            # High Score Information
            report_lines.append("**🏆 High Score Information**")
            report_lines.append("")
            report_lines.append(f"- **Overall High Score**: {int(stats['high_score']):,}")
            report_lines.append(f"- **Player**: {stats['high_score_player']}")
            if 'high_score_date' in stats and stats['high_score_date']:
                report_lines.append(f"- **Date**: {stats['high_score_date']}")
            report_lines.append("")
            
            if 'home_team_high_score' in stats:
                report_lines.append("**🏠 Home Team High Score**")
                report_lines.append("")
                report_lines.append(f"- **Score**: {int(stats['home_team_high_score']):,}")
                report_lines.append(f"- **Player**: {stats['home_team_high_score_player']}")
                report_lines.append(f"- **Team**: {stats['home_team_high_score_team']}")
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
        print("Usage: python venue_summary_report.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    # Initialize reporter
    reporter = VenueSummaryReporter(config_file)
    
    # Load and process data
    data_path = "mnp-data-archive"
    reporter.load_machine_names(data_path)
    reporter.load_venue_matches(data_path)
    reporter.process_matches()
    
    # Generate and save report
    output_file = f"reports/output/{reporter.venue_code}_venue_summary_season_{reporter.season}.md"
    reporter.save_report(output_file)


if __name__ == "__main__":
    main()