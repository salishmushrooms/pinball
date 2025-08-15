#!/usr/bin/env python3
"""
Simple Machine Score Distribution Report Generator

Uses preprocessed matches.csv data to create distribution analysis and charts.
Much faster than parsing individual JSON files.

Usage:
    python simple_distribution_report.py --machine "Attack From Mars" --seasons 4 --output-dir reports/charts
    python reports/simple_distribution_report.py --machine "Attack From Mars" --seasons 4 --outlier-method density --outlier-threshold 0.01 --output-dir reports/charts
"""

import os
import csv
import argparse
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

try:
    import matplotlib.pyplot as plt
    from scipy import stats
    import numpy as np
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    print("Warning: matplotlib/scipy/numpy not available. Only statistics will be computed.")

class SimpleDistributionAnalyzer:
    def __init__(self, csv_path: str = 'matches.csv'):
        self.csv_path = csv_path
        self.data = []
        self.load_data()
    
    def load_data(self):
        """Load data from CSV file."""
        if not os.path.exists(self.csv_path):
            print(f"Error: CSV file {self.csv_path} not found")
            return
        
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.data.append(row)
        
        print(f"Loaded {len(self.data)} score records")
    
    def get_available_machines(self) -> List[str]:
        """Get list of unique machines in the dataset."""
        machines = set()
        for row in self.data:
            machines.add(row['machine'])
        return sorted(machines)
    
    def get_available_seasons(self) -> List[int]:
        """Get list of available seasons."""
        seasons = set()
        for row in self.data:
            try:
                seasons.add(int(row['season_number']))
            except ValueError:
                continue
        return sorted(seasons, reverse=True)
    
    def collect_scores(self, machine_name: str, seasons: List[int]) -> List[int]:
        """Collect all scores for a specific machine across specified seasons."""
        scores = []
        
        for row in self.data:
            if row['machine'] != machine_name:
                continue
            
            try:
                season = int(row['season_number'])
                if season not in seasons:
                    continue
                
                score = int(row['score'])
                if score > 0:  # Only include positive scores
                    scores.append(score)
            except (ValueError, TypeError):
                continue
        
        return scores
    
    def remove_outliers(self, scores: List[int], method: str = 'iqr', threshold: float = 1.5) -> Tuple[List[int], List[int]]:
        """Remove outliers from scores using specified method."""
        if not scores:
            return [], []
        
        scores_sorted = sorted(scores)
        n = len(scores_sorted)
        
        if method == 'iqr':
            Q1_idx = int(n * 0.25)
            Q3_idx = int(n * 0.75)
            Q1 = scores_sorted[Q1_idx]
            Q3 = scores_sorted[Q3_idx]
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            clean_scores = [s for s in scores if lower_bound <= s <= upper_bound]
            outliers = [s for s in scores if s < lower_bound or s > upper_bound]
            
        elif method == 'percentile':
            lower_percentile = threshold
            upper_percentile = 100 - threshold
            lower_idx = int(n * lower_percentile / 100)
            upper_idx = int(n * upper_percentile / 100)
            lower_bound = scores_sorted[lower_idx]
            upper_bound = scores_sorted[upper_idx]
            
            clean_scores = [s for s in scores if lower_bound <= s <= upper_bound]
            outliers = [s for s in scores if s < lower_bound or s > upper_bound]
            
        elif method == 'density':
            # Remove scores where density drops below threshold
            if not HAS_PLOTTING:
                # Fall back to percentile method
                upper_idx = int(n * 0.99)  # Keep 99% of scores
                upper_bound = scores_sorted[upper_idx]
                clean_scores = [s for s in scores if s <= upper_bound]
                outliers = [s for s in scores if s > upper_bound]
            else:
                try:
                    # Calculate KDE and find where density drops below threshold
                    scores_array = np.array(scores)
                    kde = stats.gaussian_kde(scores_array)
                    
                    # Sample the KDE across the score range
                    x_min, x_max = min(scores), max(scores)
                    x_sample = np.linspace(x_min, x_max, 1000)
                    density = kde(x_sample)
                    
                    # Find the maximum density
                    max_density = np.max(density)
                    density_threshold = max_density * threshold  # threshold is fraction of max density
                    
                    # Find the rightmost point where density exceeds threshold
                    valid_indices = np.where(density >= density_threshold)[0]
                    if len(valid_indices) > 0:
                        cutoff_point = x_sample[valid_indices[-1]]
                        clean_scores = [s for s in scores if s <= cutoff_point]
                        outliers = [s for s in scores if s > cutoff_point]
                    else:
                        clean_scores = scores
                        outliers = []
                        
                except Exception as e:
                    print(f"Warning: Density-based outlier removal failed: {e}")
                    clean_scores = scores
                    outliers = []
            
        else:
            clean_scores = scores
            outliers = []
        
        return clean_scores, outliers
    
    def calculate_statistics(self, scores: List[int]) -> Dict[str, float]:
        """Calculate basic statistics."""
        if not scores:
            return {}
        
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        
        mean = sum(sorted_scores) / n
        median = sorted_scores[n//2] if n % 2 == 1 else (sorted_scores[n//2-1] + sorted_scores[n//2]) / 2
        
        variance = sum((x - mean) ** 2 for x in sorted_scores) / n
        std_dev = variance ** 0.5
        
        return {
            'count': n,
            'mean': mean,
            'median': median,
            'std_dev': std_dev,
            'min': min(sorted_scores),
            'max': max(sorted_scores),
            'q1': sorted_scores[int(n * 0.25)],
            'q3': sorted_scores[int(n * 0.75)]
        }
    
    def generate_distribution_chart(self, scores: List[int], machine_name: str, seasons: List[int], 
                                   outliers: List[int] = None, output_path: str = None):
        """Generate distribution chart with smooth curve."""
        if not scores:
            print(f"No scores found for {machine_name}")
            return
        
        if not HAS_PLOTTING:
            print("Matplotlib not available - skipping chart generation")
            return
        
        # Create figure with subplots - make wider to accommodate stats text
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        
        # Convert to millions for readability
        scores_millions = [score / 1_000_000 for score in scores]
        
        # Only show KDE (smooth curve) without histogram bars
        if len(scores_millions) > 1:
            try:
                kde_x = np.linspace(min(scores_millions), max(scores_millions), 200)
                kde = stats.gaussian_kde(scores_millions)
                ax1.plot(kde_x, kde(kde_x), color='red', linewidth=3, label='Distribution Curve')
                ax1.fill_between(kde_x, kde(kde_x), alpha=0.3, color='red')
            except Exception as e:
                print(f"Warning: Could not generate KDE curve: {e}")
        
        ax1.set_xlabel('Score (Millions)')
        ax1.set_ylabel('Density')
        ax1.set_title(f'{machine_name}\\nScore Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Box plot
        ax2.boxplot(scores_millions, vert=True, patch_artist=True,
                   boxprops=dict(facecolor='lightblue', alpha=0.7),
                   medianprops=dict(color='red', linewidth=2))
        ax2.set_ylabel('Score (Millions)')
        ax2.set_title(f'{machine_name}\\nBox Plot')
        ax2.grid(True, alpha=0.3)
        
        # Add statistics text
        stats_info = self.calculate_statistics(scores)
        stats_text = f"""
Statistics:
• Count: {stats_info['count']:,}
• Mean: {stats_info['mean']/1_000_000:.2f}M
• Median: {stats_info['median']/1_000_000:.2f}M
• Std Dev: {stats_info['std_dev']/1_000_000:.2f}M
• Min: {stats_info['min']/1_000_000:.2f}M
• Max: {stats_info['max']/1_000_000:.2f}M
        """
        
        
        # Position statistics text on the right side of the figure
        plt.figtext(0.72, 0.5, stats_text.strip(), fontsize=11, 
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8),
                   verticalalignment='center')
        
        # Adjust layout to make room for stats text
        plt.tight_layout()
        plt.subplots_adjust(right=0.7)
        
        # Save or show
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved to: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def generate_report(self, machine_name: str, num_seasons: int = 4, 
                       outlier_method: str = 'iqr', outlier_threshold: float = 1.5,
                       output_dir: str = None):
        """Generate complete distribution report for a machine."""
        # Get available seasons
        available_seasons = self.get_available_seasons()
        if not available_seasons:
            print("No seasons found in data")
            return
        
        # Select the latest N seasons
        selected_seasons = available_seasons[:num_seasons]
        
        print(f"Analyzing {machine_name} for seasons: {selected_seasons}")
        
        # Collect scores
        raw_scores = self.collect_scores(machine_name, selected_seasons)
        
        if not raw_scores:
            print(f"No scores found for {machine_name} in the specified seasons")
            return
        
        print(f"Collected {len(raw_scores)} raw scores")
        
        # Filter out negative scores (should not exist for pinball)
        positive_scores = [score for score in raw_scores if score > 0]
        
        if len(positive_scores) < len(raw_scores):
            print(f"Removed {len(raw_scores) - len(positive_scores)} negative or zero scores")
        
        # Apply outlier removal if requested
        clean_scores, outliers = self.remove_outliers(positive_scores, outlier_method, outlier_threshold)
        
        if outliers:
            print(f"Removed {len(outliers)} outliers using {outlier_method} method")
            if outlier_method == 'density':
                print(f"Density cutoff removed scores above: {max([s for s in positive_scores if s <= max(clean_scores)])/1_000_000:.2f}M")
            outliers_millions = sorted([o/1_000_000 for o in outliers], reverse=True)[:10]
            print(f"Top outlier scores removed: {outliers_millions}")
        
        # Generate chart
        if output_dir:
            filename = f"{machine_name.replace(' ', '_').replace('/', '_')}_distribution.png"
            output_path = os.path.join(output_dir, filename)
        else:
            output_path = None
        
        self.generate_distribution_chart(clean_scores, machine_name, selected_seasons, outliers, output_path)
        
        # Print summary statistics
        if clean_scores:
            stats_info = self.calculate_statistics(clean_scores)
            print(f"\\nSummary Statistics for {machine_name}:")
            print(f"Total scores: {stats_info['count']:,}")
            print(f"Mean: {stats_info['mean']/1_000_000:.2f}M")
            print(f"Median: {stats_info['median']/1_000_000:.2f}M")
            print(f"Standard deviation: {stats_info['std_dev']/1_000_000:.2f}M")
            print(f"Range: {stats_info['min']/1_000_000:.2f}M - {stats_info['max']/1_000_000:.2f}M")
            print(f"Interquartile range: {stats_info['q1']/1_000_000:.2f}M - {stats_info['q3']/1_000_000:.2f}M")

def main():
    parser = argparse.ArgumentParser(description='Generate machine score distribution report from CSV data')
    parser.add_argument('--machine', '-m', required=True, help='Machine name (e.g., "Attack From Mars", "Medieval Madness")')
    parser.add_argument('--seasons', '-s', type=int, default=4, 
                       help='Number of latest seasons to analyze (default: 4)')
    parser.add_argument('--outlier-method', choices=['iqr', 'percentile', 'density', 'none'], 
                       default='none', help='Outlier detection method (default: none)')
    parser.add_argument('--outlier-threshold', type=float, default=1.5,
                       help='Outlier threshold (default: 1.5 for IQR, 5.0 for percentile, 0.01 for density)')
    parser.add_argument('--output-dir', '-o', help='Output directory for chart (optional)')
    parser.add_argument('--csv-path', default='matches.csv', help='Path to CSV file (default: matches.csv)')
    parser.add_argument('--list-machines', action='store_true', 
                       help='List available machine names and exit')
    
    args = parser.parse_args()
    
    analyzer = SimpleDistributionAnalyzer(args.csv_path)
    
    if args.list_machines:
        machines = analyzer.get_available_machines()
        print("Available machines:")
        for machine in machines:
            print(f"  {machine}")
        return
    
    analyzer.generate_report(
        machine_name=args.machine,
        num_seasons=args.seasons,
        outlier_method=args.outlier_method,
        outlier_threshold=args.outlier_threshold,
        output_dir=args.output_dir
    )

if __name__ == "__main__":
    main()