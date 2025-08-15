#!/usr/bin/env python3
"""
MNP Score Percentile Report Generator

Generates a chart showing scores vs percentile rankings for a specific machine,
with configurable machine and venue filtering.
"""

import json
import os
import glob
import statistics
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime
from typing import Dict, Any


class ScorePercentileReporter:
    """Generate score vs percentile charts for pinball machines."""
    
    def __init__(self, config_path: str):
        """Initialize reporter with configuration file."""
        self.config = self._load_config(config_path)
        
        # Handle single season or multiple seasons
        season_config = self.config['season']
        if isinstance(season_config, str):
            # Check if it's a comma-separated string
            if ',' in season_config:
                self.seasons = [s.strip().strip("'\"") for s in season_config.split(',')]
            else:
                self.seasons = [season_config]
        elif isinstance(season_config, list):
            self.seasons = season_config
        else:
            self.seasons = [str(season_config)]
            
        # Handle single machine, multiple machines, or auto-discovery
        machine_config = self.config.get('target_machine')
        if machine_config is None or machine_config == "auto":
            self.target_machines = None  # Will auto-discover
            self.auto_discover_machines = True
        elif isinstance(machine_config, str):
            if ',' in machine_config:
                self.target_machines = [m.strip() for m in machine_config.split(',')]
            else:
                self.target_machines = [machine_config]
            self.auto_discover_machines = False
        elif isinstance(machine_config, list):
            self.target_machines = machine_config
            self.auto_discover_machines = False
        else:
            self.target_machines = [str(machine_config)]
            self.auto_discover_machines = False
            
        self.target_venue = self.config.get('target_venue')  # Optional venue filter
        self.ipr_filter = self.config.get('ipr_filter')  # Optional IPR filtering
        self.outlier_filter = self.config.get('outlier_filter', {})  # Optional outlier filtering
        
        # Data storage
        self.matches = []
        self.machine_scores = []
        self.machine_aliases = {}
        self.machine_variations = {}
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file with support for config references."""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Load referenced config files if they exist
        config_dir = os.path.dirname(config_path) or "."
        
        # Load season from separate file if referenced
        if config.get('season_config_file'):
            season_file = os.path.join(config_dir, config['season_config_file'])
            with open(season_file, 'r') as f:
                season_config = json.load(f)
                config['season'] = season_config.get('season', config.get('season'))
        
        # Load machine from separate file if referenced
        if config.get('machine_config_file'):
            machine_file = os.path.join(config_dir, config['machine_config_file'])
            with open(machine_file, 'r') as f:
                machine_config = json.load(f)
                config['target_machine'] = machine_config.get('machine', config.get('target_machine'))
        
        # Load venue from separate file if referenced
        if config.get('venue_config_file'):
            venue_file = os.path.join(config_dir, config['venue_config_file'])
            with open(venue_file, 'r') as f:
                venue_config = json.load(f)
                config['target_venue'] = venue_config.get('venue', config.get('target_venue'))
        
        # Load IPR filter from separate file if referenced
        if config.get('ipr_config_file'):
            ipr_file = os.path.join(config_dir, config['ipr_config_file'])
            with open(ipr_file, 'r') as f:
                ipr_config = json.load(f)
                config['ipr_filter'] = ipr_config.get('ipr_filter', config.get('ipr_filter'))
        
        return config
    
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
                            self.machine_aliases[variation] = canonical_key  # Keep case-sensitive mapping
                            
            print(f"Loaded machine variations for {len(variations_data)} machines")
        except FileNotFoundError:
            print(f"Warning: {variations_file} not found. No alias mapping applied.")
        except json.JSONDecodeError:
            print(f"Warning: Error reading {variations_file}. No alias mapping applied.")
    
    def normalize_machine_key(self, machine_key: str) -> str:
        """Normalize machine key using alias mapping."""
        # First, check if this is an alias that should be mapped to a canonical key
        if machine_key in self.machine_aliases:
            return self.machine_aliases[machine_key]
        
        # Clean up trailing spaces and other normalization
        cleaned_key = machine_key.strip()
        
        # Check again after cleaning
        if cleaned_key in self.machine_aliases:
            return self.machine_aliases[cleaned_key]
        
        return cleaned_key
    
    def filter_outliers(self, machine_scores: list) -> tuple:
        """Filter outliers from machine scores and return filtered scores + outlier info."""
        if not machine_scores or not self.outlier_filter:
            return machine_scores, {"removed_count": 0, "method": "none"}
        
        scores = [s['score'] for s in machine_scores]
        original_count = len(scores)
        
        method = self.outlier_filter.get('method', 'iqr')
        removed_scores = []
        
        if method == 'iqr':
            # Interquartile Range method
            scores_sorted = sorted(scores)
            n = len(scores_sorted)
            
            if n < 4:
                return machine_scores, {"removed_count": 0, "method": method, "reason": "insufficient_data"}
            
            q1_idx = n // 4
            q3_idx = 3 * n // 4
            q1 = scores_sorted[q1_idx]
            q3 = scores_sorted[q3_idx]
            iqr = q3 - q1
            
            multiplier = self.outlier_filter.get('iqr_multiplier', 1.5)
            lower_bound = q1 - multiplier * iqr
            upper_bound = q3 + multiplier * iqr
            
            filtered_scores = []
            for score_data in machine_scores:
                score = score_data['score']
                if lower_bound <= score <= upper_bound:
                    filtered_scores.append(score_data)
                else:
                    removed_scores.append(score)
            
        elif method == 'percentile':
            # Percentile-based filtering
            import numpy as np
            lower_pct = self.outlier_filter.get('lower_percentile', 1)
            upper_pct = self.outlier_filter.get('upper_percentile', 99)
            
            lower_bound = np.percentile(scores, lower_pct)
            upper_bound = np.percentile(scores, upper_pct)
            
            filtered_scores = []
            for score_data in machine_scores:
                score = score_data['score']
                if lower_bound <= score <= upper_bound:
                    filtered_scores.append(score_data)
                else:
                    removed_scores.append(score)
        
        elif method == 'absolute':
            # Absolute bounds
            lower_bound = self.outlier_filter.get('min_score', 0)
            upper_bound = self.outlier_filter.get('max_score', float('inf'))
            
            filtered_scores = []
            for score_data in machine_scores:
                score = score_data['score']
                if lower_bound <= score <= upper_bound:
                    filtered_scores.append(score_data)
                else:
                    removed_scores.append(score)
        
        else:
            return machine_scores, {"removed_count": 0, "method": method, "error": "unknown_method"}
        
        outlier_info = {
            "removed_count": len(removed_scores),
            "method": method,
            "original_count": original_count,
            "filtered_count": len(filtered_scores),
            "removed_scores": sorted(removed_scores, reverse=True)[:5]  # Show top 5 outliers
        }
        
        if removed_scores:
            print(f"  Outlier filtering ({method}): Removed {len(removed_scores)} outliers")
            print(f"    Top outliers removed: {[f'{s:,}' for s in outlier_info['removed_scores']]}")
        
        return filtered_scores, outlier_info
    
    def discover_machines(self) -> list:
        """Discover all unique machines in the loaded matches."""
        machines = set()
        
        for match in self.matches:
            for round_data in match.get('rounds', []):
                for game in round_data.get('games', []):
                    if not game.get('done', False):
                        continue
                    machine = self.normalize_machine_key(game['machine'])
                    machines.add(machine)
        
        discovered = sorted(list(machines))
        print(f"Discovered {len(discovered)} unique machines: {', '.join(discovered)}")
        return discovered
    
    def load_matches(self, data_path: str) -> None:
        """Load all matches for the specified season(s)."""
        loaded_matches = []
        
        for season in self.seasons:
            matches_pattern = f"{data_path}/season-{season}/matches/*.json"
            season_matches = 0
            
            for match_file in glob.glob(matches_pattern):
                with open(match_file, 'r') as f:
                    match_data = json.load(f)
                    
                # Apply venue filter if specified
                if self.target_venue:
                    if match_data.get('venue', {}).get('key') != self.target_venue.get('code'):
                        continue
                        
                # Include complete matches and optionally incomplete ones
                if self.config.get('data_filters', {}).get('include_incomplete_matches', False) or \
                   match_data.get('state') == 'complete':
                    loaded_matches.append(match_data)
                    season_matches += 1
            
            print(f"Loaded {season_matches} matches from season {season}")
                    
        self.matches = loaded_matches
        venue_info = f" at venue {self.target_venue['code']}" if self.target_venue else ""
        seasons_info = ", ".join(self.seasons) if len(self.seasons) > 1 else self.seasons[0]
        print(f"Total: {len(self.matches)} matches from season(s) {seasons_info}{venue_info}")
    
    def extract_machine_scores(self, target_machine: str) -> list:
        """Extract scores for the specified machine from all matches."""
        target_machine_normalized = self.normalize_machine_key(target_machine)
        machine_scores = []
        
        for match in self.matches:
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
                        
                    machine_normalized = self.normalize_machine_key(game['machine'])
                    
                    # Only process games on our target machine
                    if machine_normalized != target_machine_normalized:
                        continue
                    
                    # Determine reliable player positions based on round
                    if round_num in [1, 4]:  # 4-player rounds
                        reliable_positions = self.config.get('score_reliability', {}).get('rounds_1_4', {}).get('reliable_positions', [1, 2, 3, 4])
                    else:  # 2-player rounds
                        reliable_positions = self.config.get('score_reliability', {}).get('rounds_2_3', {}).get('reliable_positions', [1, 2])
                    
                    # Extract scores for reliable positions
                    for pos in reliable_positions:
                        player_key = game.get(f'player_{pos}')
                        score_key = f'score_{pos}'
                        
                        if player_key and score_key in game and player_key in match_players:
                            player_info = match_players[player_key]
                            
                            # Apply IPR filter if specified
                            if self.ipr_filter:
                                player_ipr = player_info['ipr']
                                min_ipr = self.ipr_filter.get('min_ipr')
                                max_ipr = self.ipr_filter.get('max_ipr')
                                
                                # Skip if player doesn't meet IPR criteria
                                if min_ipr is not None and player_ipr < min_ipr:
                                    continue
                                if max_ipr is not None and player_ipr > max_ipr:
                                    continue
                            
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
                                'date': match.get('date', ''),
                                'venue_key': match.get('venue', {}).get('key', ''),
                                'venue_name': match.get('venue', {}).get('name', '')
                            }
                            
                            machine_scores.append(score_data)
        
        print(f"Extracted {len(machine_scores)} scores for machine '{target_machine}'")
        return machine_scores
    
    def calculate_percentiles(self, machine_scores: list) -> tuple:
        """Calculate percentiles for the collected scores."""
        if not machine_scores:
            raise ValueError("No scores found for the specified machine and filters")
        
        # Extract just the score values
        scores = [s['score'] for s in machine_scores]
        scores.sort()
        
        # Calculate percentiles (0-100)
        percentiles = []
        percentile_scores = []
        
        for i, score in enumerate(scores):
            percentile = (i / (len(scores) - 1)) * 100 if len(scores) > 1 else 0
            percentiles.append(percentile)
            percentile_scores.append(score)
        
        return percentiles, percentile_scores
    
    def generate_chart(self, target_machine: str, machine_scores: list, outlier_info: dict = {}, output_dir: str = "reports/charts") -> str:
        """Generate and save the score vs percentile chart."""
        if not machine_scores:
            raise ValueError("No scores to chart")
        
        # Calculate percentiles
        percentiles, scores = self.calculate_percentiles(machine_scores)
        
        # Create the chart
        plt.figure(figsize=(12, 8))
        plt.plot(percentiles, scores, 'b-', linewidth=2, marker='o', markersize=3, alpha=0.7)
        
        # Customize the chart
        target_machine_normalized = self.normalize_machine_key(target_machine)
        
        # Get machine display name from variations
        machine_display_name = target_machine
        if self.machine_variations and target_machine_normalized in self.machine_variations:
            info = self.machine_variations[target_machine_normalized]
            if isinstance(info, dict):
                machine_display_name = info.get('name', target_machine)
        
        venue_suffix = f" at {self.target_venue['name']}" if self.target_venue else ""
        ipr_suffix = ""
        if self.ipr_filter:
            min_ipr = self.ipr_filter.get('min_ipr')
            max_ipr = self.ipr_filter.get('max_ipr')
            if min_ipr is not None and max_ipr is not None:
                ipr_suffix = f" (IPR {min_ipr}-{max_ipr})"
            elif min_ipr is not None:
                ipr_suffix = f" (IPR ≥{min_ipr})"
            elif max_ipr is not None:
                ipr_suffix = f" (IPR ≤{max_ipr})"
        
        seasons_display = ", ".join(self.seasons) if len(self.seasons) > 1 else f"Season {self.seasons[0]}"
        if len(self.seasons) > 1:
            seasons_display = f"Seasons {seasons_display}"
        
        plt.title(f'Score vs Percentile: {machine_display_name}{venue_suffix}{ipr_suffix}\n{seasons_display}', 
                 fontsize=16, fontweight='bold', pad=20)
        
        plt.xlabel('Percentile Ranking', fontsize=14)
        plt.ylabel('Score', fontsize=14)
        
        # Format score axis with commas
        plt.gca().yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
        
        # Add grid for better readability
        plt.grid(True, alpha=0.3)
        
        # Add some key statistics as text
        min_score = min(scores)
        max_score = max(scores)
        median_score = statistics.median(scores)
        q75_score = statistics.quantiles(scores, n=4)[2] if len(scores) >= 4 else max_score
        
        stats_text = f'Total Games: {len(machine_scores)}\n'
        if outlier_info and outlier_info.get('removed_count', 0) > 0:
            stats_text += f'Outliers Removed: {outlier_info["removed_count"]}\n'
        stats_text += f'Min Score: {min_score:,}\n'
        stats_text += f'Median: {median_score:,}\n'
        stats_text += f'75th %ile: {q75_score:,}\n'
        stats_text += f'Max Score: {max_score:,}'
        
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
                verticalalignment='top', fontsize=10, 
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        venue_code = self.target_venue['code'] if self.target_venue else 'all_venues'
        ipr_code = ""
        if self.ipr_filter:
            min_ipr = self.ipr_filter.get('min_ipr')
            max_ipr = self.ipr_filter.get('max_ipr')
            if min_ipr is not None and max_ipr is not None:
                ipr_code = f"_ipr{min_ipr}-{max_ipr}"
            elif min_ipr is not None:
                ipr_code = f"_ipr{min_ipr}plus"
            elif max_ipr is not None:
                ipr_code = f"_ipr{max_ipr}minus"
        
        seasons_code = "-".join(self.seasons) if len(self.seasons) > 1 else self.seasons[0]
        filename = f"{target_machine_normalized}_percentile_season_{seasons_code}_{venue_code}{ipr_code}.png"
        output_path = os.path.join(output_dir, filename)
        
        # Save the chart
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_report(self, target_machine: str, machine_scores: list, outlier_info: dict = {}) -> str:
        """Generate a text summary report."""
        if not machine_scores:
            return "No scores found for the specified machine and filters."
        
        scores = [s['score'] for s in machine_scores]
        
        # Calculate statistics
        min_score = min(scores)
        max_score = max(scores)
        median_score = statistics.median(scores)
        mean_score = statistics.mean(scores)
        
        # Find percentile thresholds
        percentiles_to_show = [10, 25, 50, 75, 90, 95]
        percentile_values = {}
        
        for p in percentiles_to_show:
            if len(scores) > 1:
                percentile_values[p] = np.percentile(scores, p)
            else:
                percentile_values[p] = scores[0]
        
        # Build report
        venue_info = f" at {self.target_venue['name']} ({self.target_venue['code']})" if self.target_venue else ""
        ipr_info = ""
        if self.ipr_filter:
            min_ipr = self.ipr_filter.get('min_ipr')
            max_ipr = self.ipr_filter.get('max_ipr')
            if min_ipr is not None and max_ipr is not None:
                ipr_info = f" - IPR {min_ipr}-{max_ipr} Players"
            elif min_ipr is not None:
                ipr_info = f" - IPR ≥{min_ipr} Players"
            elif max_ipr is not None:
                ipr_info = f" - IPR ≤{max_ipr} Players"
        
        seasons_display = ", ".join(self.seasons) if len(self.seasons) > 1 else self.seasons[0]
        if len(self.seasons) > 1:
            seasons_title = f"**Seasons {seasons_display}**"
        else:
            seasons_title = f"**Season {seasons_display}**"
        
        report_lines = []
        report_lines.append(f"# Score Percentile Report: {target_machine}{venue_info}{ipr_info}")
        report_lines.append(seasons_title)
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")
        
        # Summary statistics
        report_lines.append("## Summary Statistics")
        report_lines.append("")
        report_lines.append(f"- **Total Games**: {len(machine_scores)}")
        report_lines.append(f"- **Minimum Score**: {min_score:,}")
        report_lines.append(f"- **Maximum Score**: {max_score:,}")
        report_lines.append(f"- **Mean Score**: {mean_score:,.0f}")
        report_lines.append(f"- **Median Score**: {median_score:,}")
        report_lines.append("")
        
        # Percentile breakdown
        report_lines.append("## Percentile Breakdown")
        report_lines.append("")
        report_lines.append("| Percentile | Score |")
        report_lines.append("|------------|-------|")
        
        for p in percentiles_to_show:
            report_lines.append(f"| {p}th | {percentile_values[p]:,.0f} |")
        
        report_lines.append("")
        
        # Top scores
        top_scores = sorted(machine_scores, key=lambda x: x['score'], reverse=True)[:10]
        report_lines.append("## Top 10 Scores")
        report_lines.append("")
        report_lines.append("| Rank | Score | Player | Date | Venue |")
        report_lines.append("|------|-------|--------|------|-------|")
        
        for i, score_data in enumerate(top_scores, 1):
            venue_name = score_data.get('venue_name', 'Unknown')
            date = score_data.get('date', 'Unknown')
            report_lines.append(f"| {i} | {score_data['score']:,} | {score_data['player_name']} | {date} | {venue_name} |")
        
        return "\n".join(report_lines)
    
    def generate_reports_for_all_machines(self, data_path: str) -> list:
        """Generate reports for all specified or discovered machines."""
        # Load data first
        self.load_machine_variations()
        self.load_matches(data_path)
        
        # Determine which machines to process
        if self.auto_discover_machines:
            machines_to_process = self.discover_machines()
            if not machines_to_process:
                print("No machines found matching the criteria.")
                return []
        else:
            machines_to_process = self.target_machines or []
        
        generated_files = []
        
        for machine in machines_to_process:
            print(f"\n=== Processing machine: {machine} ===")
            
            # Extract scores for this machine
            machine_scores = self.extract_machine_scores(machine)
            
            if not machine_scores:
                print(f"No scores found for machine '{machine}' - skipping")
                continue
            
            # Apply outlier filtering
            filtered_scores, outlier_info = self.filter_outliers(machine_scores)
            
            if not filtered_scores:
                print(f"No scores remaining after outlier filtering for machine '{machine}' - skipping")
                continue
            
            try:
                # Generate chart
                chart_path = self.generate_chart(machine, filtered_scores, outlier_info)
                print(f"Chart saved to: {chart_path}")
                
                # Generate report
                report_path = self.generate_report_file(machine, filtered_scores, outlier_info)
                print(f"Report saved to: {report_path}")
                
                generated_files.extend([chart_path, report_path])
                
            except Exception as e:
                print(f"Error processing machine '{machine}': {e}")
                continue
        
        return generated_files
    
    def generate_report_file(self, target_machine: str, machine_scores: list, outlier_info: dict = {}) -> str:
        """Generate and save a report file for a specific machine."""
        report_content = self.generate_report(target_machine, machine_scores, outlier_info)
        
        # Generate filename
        venue_code = self.target_venue['code'] if self.target_venue else 'all_venues'
        target_machine_normalized = self.normalize_machine_key(target_machine)
        ipr_code = ""
        if self.ipr_filter:
            min_ipr = self.ipr_filter.get('min_ipr')
            max_ipr = self.ipr_filter.get('max_ipr')
            if min_ipr is not None and max_ipr is not None:
                ipr_code = f"_ipr{min_ipr}-{max_ipr}"
            elif min_ipr is not None:
                ipr_code = f"_ipr{min_ipr}plus"
            elif max_ipr is not None:
                ipr_code = f"_ipr{max_ipr}minus"
        
        seasons_code = "-".join(self.seasons) if len(self.seasons) > 1 else self.seasons[0]
        output_file = f"reports/output/{target_machine_normalized}_percentile_season_{seasons_code}_{venue_code}{ipr_code}.md"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(report_content)
        
        return output_file
    


def main():
    """Main execution function."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python score_percentile_report.py <config_file>")
        print("\n=== QUICK START ===")
        print("Use pre-built configurations:")
        print("  python score_percentile_report.py reports/configs/preset_all_players.json")
        print("  python score_percentile_report.py reports/configs/preset_advanced_players.json")
        print("  python score_percentile_report.py reports/configs/comprehensive_config.json")
        print("\n=== CONFIGURATION OPTIONS ===")
        print("1. Edit reports/configs/comprehensive_config.json (all settings in one file)")
        print("2. Use reports/configs/modular_config.json and edit individual files:")
        print("   - reports/configs/seasons.json")
        print("   - reports/configs/machines.json") 
        print("   - reports/configs/venues.json")
        print("   - reports/configs/ipr_filters.json")
        print("\nSee reports/configs/README.md for detailed configuration guide")
        print("\n=== EXAMPLE CONFIG ===")
        print(json.dumps({
            "season": "21",
            "target_machine": "AFM",
            "ipr_filter": {"min_ipr": 3, "max_ipr": 6},
            "target_venue": None
        }, indent=2))
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    try:
        # Initialize reporter
        reporter = ScorePercentileReporter(config_file)
        
        # Generate reports for all machines
        data_path = "mnp-data-archive"
        generated_files = reporter.generate_reports_for_all_machines(data_path)
        
        if generated_files:
            print(f"\n=== Summary ===")
            print(f"Generated {len(generated_files)} files:")
            for file_path in generated_files:
                print(f"  - {file_path}")
        else:
            print("No reports generated.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()