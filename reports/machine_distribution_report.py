#!/usr/bin/env python3
"""
Machine Score Distribution Report Generator

Creates configurable distribution charts for pinball machine scores by season.
Includes outlier detection and removal functionality.

Usage:
    python machine_distribution_report.py --machine "AFM" --seasons 4 --output-dir reports/charts
"""

import os
import json
import glob
import argparse
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy import stats
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    print("Warning: numpy, matplotlib, or scipy not available. Only statistics will be computed.")

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

class MachineScoreAnalyzer:
    def __init__(self, data_archive_path: str = 'mnp-data-archive'):
        self.data_archive_path = data_archive_path
        self.load_reference_data()
    
    def load_reference_data(self):
        """Load machine names and venue data."""
        machines_path = os.path.join(self.data_archive_path, 'machines.json')
        with open(machines_path, 'r') as f:
            self.machine_names = json.load(f)
        
        venues_path = os.path.join(self.data_archive_path, 'venues.json')
        with open(venues_path, 'r') as f:
            self.venues = json.load(f)
    
    def get_available_seasons(self) -> List[int]:
        """Get list of available seasons."""
        season_dirs = glob.glob(os.path.join(self.data_archive_path, 'season-*'))
        seasons = []
        for season_dir in season_dirs:
            season_num = os.path.basename(season_dir).split('-')[1]
            if season_num.isdigit():
                seasons.append(int(season_num))
        return sorted(seasons, reverse=True)
    
    def get_machine_name(self, machine_key: str) -> str:
        """Get full machine name from key."""
        return self.machine_names.get(machine_key, {}).get('name', machine_key)
    
    def collect_scores(self, machine_key: str, seasons: List[int]) -> List[int]:
        """Collect all scores for a specific machine across specified seasons."""
        all_scores = []
        
        for season in seasons:
            season_dir = os.path.join(self.data_archive_path, f'season-{season}')
            if not os.path.exists(season_dir):
                print(f"Warning: Season {season} data not found")
                continue
            
            matches_dir = os.path.join(season_dir, 'matches')
            if not os.path.exists(matches_dir):
                print(f"Warning: No matches directory for season {season}")
                continue
            
            match_files = glob.glob(os.path.join(matches_dir, f'mnp-{season}-*.json'))
            print(f"Processing {len(match_files)} matches for season {season}")
            
            for match_file in match_files:
                try:
                    with open(match_file, 'r') as f:
                        match_data = json.load(f)
                    
                    # Process all rounds and games
                    for round_data in match_data.get('rounds', []):
                        for game in round_data.get('games', []):
                            # Skip if no machine defined or game not done
                            if 'machine' not in game or not game.get('done', False):
                                continue
                            
                            # Skip if not the machine we're looking for
                            if game.get('machine') != machine_key:
                                continue
                            
                            # Collect all scores for this game
                            for i in range(1, 5):
                                score_key = f'score_{i}'
                                if score_key in game and game[score_key] is not None:
                                    try:
                                        score = int(game[score_key])
                                        if score > 0:  # Only include positive scores
                                            all_scores.append(score)
                                    except (ValueError, TypeError):
                                        continue
                
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"Error processing {match_file}: {e}")
        
        return all_scores
    
    def remove_outliers(self, scores: List[int], method: str = 'iqr', threshold: float = 1.5) -> Tuple[List[int], List[int]]:
        """Remove outliers from scores using specified method."""
        if not scores:
            return [], []
        
        if not HAS_PLOTTING:
            # Fall back to simple percentile-based outlier removal
            scores_sorted = sorted(scores)
            n = len(scores_sorted)
            Q1_idx = int(n * 0.25)
            Q3_idx = int(n * 0.75)
            Q1 = scores_sorted[Q1_idx]
            Q3 = scores_sorted[Q3_idx]
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            clean_scores = [s for s in scores if lower_bound <= s <= upper_bound]
            outliers = [s for s in scores if s < lower_bound or s > upper_bound]
            return clean_scores, outliers
        
        scores_array = np.array(scores)
        
        if method == 'iqr':
            Q1 = np.percentile(scores_array, 25)
            Q3 = np.percentile(scores_array, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            clean_mask = (scores_array >= lower_bound) & (scores_array <= upper_bound)
            clean_scores = scores_array[clean_mask].tolist()
            outliers = scores_array[~clean_mask].tolist()
            
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(scores_array))
            clean_mask = z_scores < threshold
            clean_scores = scores_array[clean_mask].tolist()
            outliers = scores_array[~clean_mask].tolist()
        
        elif method == 'percentile':
            lower_percentile = threshold
            upper_percentile = 100 - threshold
            lower_bound = np.percentile(scores_array, lower_percentile)
            upper_bound = np.percentile(scores_array, upper_percentile)
            
            clean_mask = (scores_array >= lower_bound) & (scores_array <= upper_bound)
            clean_scores = scores_array[clean_mask].tolist()
            outliers = scores_array[~clean_mask].tolist()
        
        else:
            clean_scores = scores
            outliers = []
        
        return clean_scores, outliers
    
    def generate_distribution_chart(self, scores: List[int], machine_key: str, seasons: List[int], 
                                   outliers: List[int] = None, output_path: str = None):
        """Generate distribution chart with smooth curve."""
        if not scores:
            print(f"No scores found for {machine_key}")
            return
        
        if not HAS_PLOTTING:
            print("Matplotlib not available - skipping chart generation")
            return
        
        machine_name = self.get_machine_name(machine_key)
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Convert to millions for readability
        scores_millions = [score / 1_000_000 for score in scores]
        
        # Histogram with KDE
        ax1.hist(scores_millions, bins=30, density=True, alpha=0.7, color='skyblue', edgecolor='black')
        
        # Add KDE (smooth curve)
        if len(scores_millions) > 1:
            try:
                kde_x = np.linspace(min(scores_millions), max(scores_millions), 200)
                kde = stats.gaussian_kde(scores_millions)
                ax1.plot(kde_x, kde(kde_x), color='red', linewidth=2, label='Distribution Curve')
            except Exception as e:
                print(f"Warning: Could not generate KDE curve: {e}")
        
        ax1.set_xlabel('Score (Millions)')
        ax1.set_ylabel('Density')
        ax1.set_title(f'{machine_name}\nScore Distribution (Seasons {min(seasons)}-{max(seasons)})')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Box plot
        ax2.boxplot(scores_millions, vert=True, patch_artist=True,
                   boxprops=dict(facecolor='lightblue', alpha=0.7),
                   medianprops=dict(color='red', linewidth=2))
        ax2.set_ylabel('Score (Millions)')
        ax2.set_title(f'{machine_name}\nBox Plot')
        ax2.grid(True, alpha=0.3)
        
        # Add statistics text
        def calculate_mean(values):
            return sum(values) / len(values)
        
        def calculate_median(values):
            sorted_values = sorted(values)
            n = len(sorted_values)
            if n % 2 == 0:
                return (sorted_values[n//2-1] + sorted_values[n//2]) / 2
            else:
                return sorted_values[n//2]
        
        def calculate_std(values):
            mean = calculate_mean(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            return variance ** 0.5
        
        stats_text = f"""
Statistics:
• Count: {len(scores):,}
• Mean: {calculate_mean(scores_millions):.2f}M
• Median: {calculate_median(scores_millions):.2f}M
• Std Dev: {calculate_std(scores_millions):.2f}M
• Min: {min(scores_millions):.2f}M
• Max: {max(scores_millions):.2f}M
        """
        
        if outliers:
            outliers_millions = [o / 1_000_000 for o in outliers]
            stats_text += f"• Outliers Removed: {len(outliers)}"
        
        plt.figtext(0.02, 0.02, stats_text.strip(), fontsize=9, 
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
        
        plt.tight_layout()
        
        # Save or show
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved to: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def generate_report(self, machine_key: str, num_seasons: int = 4, 
                       outlier_method: str = 'iqr', outlier_threshold: float = 1.5,
                       output_dir: str = None):
        """Generate complete distribution report for a machine."""
        # Get available seasons
        available_seasons = self.get_available_seasons()
        if not available_seasons:
            print("No seasons found in data archive")
            return
        
        # Select the latest N seasons
        selected_seasons = available_seasons[:num_seasons]
        machine_name = self.get_machine_name(machine_key)
        
        print(f"Analyzing {machine_name} ({machine_key}) for seasons: {selected_seasons}")
        
        # Collect scores
        raw_scores = self.collect_scores(machine_key, selected_seasons)
        
        if not raw_scores:
            print(f"No scores found for {machine_name} in the specified seasons")
            return
        
        print(f"Collected {len(raw_scores)} raw scores")
        
        # Remove outliers
        clean_scores, outliers = self.remove_outliers(raw_scores, outlier_method, outlier_threshold)
        
        if outliers:
            print(f"Removed {len(outliers)} outliers using {outlier_method} method")
            print(f"Outlier scores: {sorted([o/1_000_000 for o in outliers], reverse=True)[:10]}M (showing top 10)")
        
        # Generate chart
        if output_dir:
            filename = f"{machine_key}_distribution_seasons_{min(selected_seasons)}-{max(selected_seasons)}.png"
            output_path = os.path.join(output_dir, filename)
        else:
            output_path = None
        
        self.generate_distribution_chart(clean_scores, machine_key, selected_seasons, outliers, output_path)
        
        # Print summary statistics
        if clean_scores:
            def calculate_mean(values):
                return sum(values) / len(values)
            
            def calculate_median(values):
                sorted_values = sorted(values)
                n = len(sorted_values)
                if n % 2 == 0:
                    return (sorted_values[n//2-1] + sorted_values[n//2]) / 2
                else:
                    return sorted_values[n//2]
            
            def calculate_std(values):
                mean = calculate_mean(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                return variance ** 0.5
            
            print(f"\nSummary Statistics for {machine_name}:")
            print(f"Raw scores: {len(raw_scores):,}")
            print(f"Clean scores: {len(clean_scores):,}")
            print(f"Mean: {calculate_mean(clean_scores)/1_000_000:.2f}M")
            print(f"Median: {calculate_median(clean_scores)/1_000_000:.2f}M")
            print(f"Standard deviation: {calculate_std(clean_scores)/1_000_000:.2f}M")
            print(f"Range: {min(clean_scores)/1_000_000:.2f}M - {max(clean_scores)/1_000_000:.2f}M")

def main():
    parser = argparse.ArgumentParser(description='Generate machine score distribution report')
    parser.add_argument('--machine', '-m', required=True, help='Machine key (e.g., AFM, MM, TZ)')
    parser.add_argument('--seasons', '-s', type=int, default=4, 
                       help='Number of latest seasons to analyze (default: 4)')
    parser.add_argument('--outlier-method', choices=['iqr', 'zscore', 'percentile', 'none'], 
                       default='iqr', help='Outlier detection method (default: iqr)')
    parser.add_argument('--outlier-threshold', type=float, default=1.5,
                       help='Outlier threshold (default: 1.5 for IQR, 3.0 for zscore, 5.0 for percentile)')
    parser.add_argument('--output-dir', '-o', help='Output directory for chart (optional)')
    parser.add_argument('--list-machines', action='store_true', 
                       help='List available machine keys and exit')
    
    args = parser.parse_args()
    
    analyzer = MachineScoreAnalyzer()
    
    if args.list_machines:
        print("Available machines:")
        for key, info in sorted(analyzer.machine_names.items()):
            print(f"  {key}: {info.get('name', key)}")
        return
    
    # Validate machine key
    if args.machine not in analyzer.machine_names:
        print(f"Error: Machine '{args.machine}' not found.")
        print("Use --list-machines to see available options.")
        return
    
    analyzer.generate_report(
        machine_key=args.machine,
        num_seasons=args.seasons,
        outlier_method=args.outlier_method,
        outlier_threshold=args.outlier_threshold,
        output_dir=args.output_dir
    )

if __name__ == "__main__":
    main()