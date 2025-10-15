#!/usr/bin/env python3
"""
MNP Home vs Away Team Advantage Report Generator

Analyzes the point advantage of home teams vs away teams for each machine
at a specific venue. Points are different from scores - they represent the
actual match points earned (0-5 for doubles, 0-3 for singles).

FUTURE IMPROVEMENT: This analysis uses total points per team per machine,
but could be enhanced to analyze point differentials per game on each machine
while controlling for IPR differentials. This would reveal which specific 
machines provide the strongest home field advantages.
"""

import json
import os
import glob
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any


class HomeAwayAdvantageReporter:
    """Generate home vs away team point advantage reports by machine."""
    
    def __init__(self, venue_code: str, venue_name: str, season: str):
        """Initialize reporter with venue and season."""
        self.venue_code = venue_code
        self.venue_name = venue_name
        self.season = season
        
        # Data storage
        self.matches = []
        self.machine_points = defaultdict(lambda: {'home': 0, 'away': 0, 'games': 0})
        self.machine_aliases = {}
        
    def load_machine_variations(self) -> None:
        """Load machine name variations for data cleaning."""
        variations_file = "machine_variations.json"
        try:
            with open(variations_file, 'r') as f:
                variations_data = json.load(f)
                
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
    
    def load_venue_matches(self, data_path: str) -> None:
        """Load all matches played at the target venue."""
        matches_pattern = f"{data_path}/season-{self.season}/matches/*.json"
        venue_matches = []
        
        for match_file in glob.glob(matches_pattern):
            with open(match_file, 'r') as f:
                match_data = json.load(f)
                
            # Check if match was played at target venue
            if match_data.get('venue', {}).get('key') == self.venue_code:
                if match_data.get('state') == 'complete':
                    venue_matches.append(match_data)
                    
        self.matches = venue_matches
        print(f"Loaded {len(self.matches)} complete matches for venue {self.venue_code}")
    
    def process_matches(self) -> None:
        """Process all loaded matches to extract point data by machine."""
        for match in self.matches:
            # Process each round
            for round_data in match.get('rounds', []):
                for game in round_data.get('games', []):
                    if not game.get('done', False):
                        continue
                    
                    machine = self.normalize_machine_key(game['machine'])
                    
                    # Get points for home and away teams
                    home_points = game.get('home_points', 0)
                    away_points = game.get('away_points', 0)
                    
                    # Accumulate points for this machine
                    self.machine_points[machine]['home'] += home_points
                    self.machine_points[machine]['away'] += away_points
                    self.machine_points[machine]['games'] += 1
        
        total_games = sum(data['games'] for data in self.machine_points.values())
        print(f"Processed {total_games} games across {len(self.machine_points)} machines")
    
    def calculate_machine_stats(self) -> List[Dict[str, Any]]:
        """Calculate home vs away statistics for each machine."""
        stats = []
        
        for machine, points_data in self.machine_points.items():
            home_points = points_data['home']
            away_points = points_data['away']
            total_games = points_data['games']
            total_points = home_points + away_points
            
            if total_points == 0:
                continue
                
            # Calculate percentage advantage for home team
            home_percentage = (home_points / total_points) * 100
            away_percentage = (away_points / total_points) * 100
            
            # Calculate home advantage ratio (home/away)
            if away_points > 0:
                home_advantage_ratio = home_points / away_points
            else:
                home_advantage_ratio = float('inf') if home_points > 0 else 1.0
            
            stats.append({
                'machine': machine,
                'home_points': home_points,
                'away_points': away_points,
                'total_games': total_games,
                'total_points': total_points,
                'home_percentage': home_percentage,
                'away_percentage': away_percentage,
                'home_advantage_ratio': home_advantage_ratio
            })
        
        # Sort by home advantage ratio (highest home advantage first)
        stats.sort(key=lambda x: x['home_advantage_ratio'], reverse=True)
        
        return stats
    
    def generate_report(self) -> str:
        """Generate the home vs away advantage report."""
        if not self.matches:
            return "No matches found for venue."
        
        machine_stats = self.calculate_machine_stats()
        
        if not machine_stats:
            return "No game data found for analysis."
        
        # Generate report
        report_lines = []
        report_lines.append(f"# Home vs Away Team Advantage Report")
        report_lines.append(f"## {self.venue_name} ({self.venue_code}) - Season {self.season}")
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")
        report_lines.append("Machines ordered by home team advantage (home/away ratio)")
        report_lines.append("")
        
        # Summary statistics
        total_matches = len(self.matches)
        total_games = sum(stats['total_games'] for stats in machine_stats)
        total_home_points = sum(stats['home_points'] for stats in machine_stats)
        total_away_points = sum(stats['away_points'] for stats in machine_stats)
        overall_home_pct = (total_home_points / (total_home_points + total_away_points)) * 100
        
        report_lines.append(f"**Overall Summary:** {total_matches} matches, {total_games} games")
        report_lines.append(f"**Total Points:** Home {total_home_points}, Away {total_away_points}")
        report_lines.append(f"**Overall Home Advantage:** {overall_home_pct:.1f}% vs {100-overall_home_pct:.1f}%")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # Machine-by-machine breakdown
        for i, stats in enumerate(machine_stats, 1):
            machine = stats['machine']
            home_pts = stats['home_points']
            away_pts = stats['away_points']
            games = stats['total_games']
            home_pct = stats['home_percentage']
            ratio = stats['home_advantage_ratio']
            
            if ratio == float('inf'):
                ratio_str = "∞ (all home)"
            else:
                ratio_str = f"{ratio:.2f}"
            
            report_lines.append(f"{i:2d}. **{machine}** - {games} games | Home: {home_pts} ({home_pct:.1f}%) | Away: {away_pts} | Ratio: {ratio_str}")
        
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
    
    if len(sys.argv) != 4:
        print("Usage: python home_away_advantage_report.py <venue_code> <venue_name> <season>")
        print("Example: python home_away_advantage_report.py 8BT '8-bit Arcade Bar' 20")
        sys.exit(1)
    
    venue_code = sys.argv[1]
    venue_name = sys.argv[2]
    season = sys.argv[3]
    
    # Initialize reporter
    reporter = HomeAwayAdvantageReporter(venue_code, venue_name, season)
    
    # Load and process data
    data_path = "mnp-data-archive"
    reporter.load_machine_variations()
    reporter.load_venue_matches(data_path)
    reporter.process_matches()
    
    # Generate and save report
    output_file = f"reports/output/{venue_code}_home_away_advantage_season_{season}.md"
    reporter.save_report(output_file)


if __name__ == "__main__":
    main()