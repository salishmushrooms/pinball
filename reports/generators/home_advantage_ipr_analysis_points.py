#!/usr/bin/env python3
"""
MNP Home Advantage IPR Analysis (Point Differential Based)

Quantifies home field advantage in terms of IPR points by analyzing the relationship
between team IPR differentials and POINT DIFFERENTIALS (not just win/loss).
This provides more nuanced insights into the magnitude of home advantage effects.

Updated approach uses linear regression: point_diff = intercept + slope * ipr_diff
Where intercept = pure home advantage in points, slope = points per IPR differential
"""

import json
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Tuple
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


class HomeAdvantageIPRPointAnalyzer:
    """Analyze home field advantage using point differentials instead of win/loss."""
    
    def __init__(self, season: str):
        """Initialize analyzer with season."""
        self.season = season
        self.matches = []
        self.match_data = []  # Processed match data for analysis
        
    def load_matches(self, data_path: str) -> None:
        """Load all complete matches for the season."""
        matches_pattern = f"{data_path}/season-{self.season}/matches/*.json"
        loaded_matches = []
        
        for match_file in glob.glob(matches_pattern):
            with open(match_file, 'r') as f:
                match_data = json.load(f)
                
            if match_data.get('state') == 'complete':
                loaded_matches.append(match_data)
                
        self.matches = loaded_matches
        print(f"Loaded {len(self.matches)} complete matches from season {self.season}")
    
    def calculate_team_ipr(self, team_lineup: List[Dict]) -> int:
        """Calculate total IPR for a team lineup."""
        return sum(player.get('IPR', 0) for player in team_lineup)
    
    def calculate_correct_team_points(self, match: Dict[str, Any]) -> Tuple[float, float]:
        """Calculate correct home and away team points based on round structure."""
        home_points = 0.0
        away_points = 0.0
        
        # Round structure mapping
        round_structures = {
            1: ['away', 'home', 'away', 'home'],  # positions 1,2,3,4
            2: ['home', 'away'],                  # positions 1,2
            3: ['away', 'home'],                  # positions 1,2
            4: ['home', 'away', 'home', 'away']   # positions 1,2,3,4
        }
        
        for round_data in match.get('rounds', []):
            round_num = round_data['n']
            structure = round_structures.get(round_num, [])
            
            for game in round_data.get('games', []):
                if not game.get('done', False):
                    continue
                
                # Add up points for each position based on round structure
                for pos_idx, team_type in enumerate(structure, 1):
                    points_key = f'points_{pos_idx}'
                    if points_key in game:
                        points = game[points_key]
                        if team_type == 'home':
                            home_points += points
                        else:  # away
                            away_points += points
        
        return home_points, away_points
    
    def process_matches(self) -> None:
        """Process matches to extract analysis data with correct point calculations."""
        processed_data = []
        
        for match in self.matches:
            # Calculate team IPRs
            home_lineup = match.get('home', {}).get('lineup', [])
            away_lineup = match.get('away', {}).get('lineup', [])
            
            home_ipr = self.calculate_team_ipr(home_lineup)
            away_ipr = self.calculate_team_ipr(away_lineup)
            ipr_differential = home_ipr - away_ipr
            
            # Calculate match outcome using corrected point calculation
            home_points, away_points = self.calculate_correct_team_points(match)
            
            if home_points + away_points == 0:
                continue  # Skip matches with no points recorded
            
            home_won = home_points > away_points
            point_differential = home_points - away_points
            
            match_info = {
                'match_key': match['key'],
                'venue_key': match.get('venue', {}).get('key', ''),
                'venue_name': match.get('venue', {}).get('name', ''),
                'home_team': match.get('home', {}).get('key', ''),
                'away_team': match.get('away', {}).get('key', ''),
                'home_ipr': home_ipr,
                'away_ipr': away_ipr,
                'ipr_differential': ipr_differential,
                'home_points': home_points,
                'away_points': away_points,
                'point_differential': point_differential,
                'home_won': home_won,
                'total_points': home_points + away_points
            }
            
            processed_data.append(match_info)
        
        self.match_data = processed_data
        print(f"Processed {len(processed_data)} matches for analysis")
    
    def analyze_by_ipr_bins(self, bin_size: int = 5) -> Dict[str, Any]:
        """Analyze point differentials by IPR differential bins."""
        if not self.match_data:
            return {}
        
        # Create bins
        ipr_diffs = [m['ipr_differential'] for m in self.match_data]
        min_diff = min(ipr_diffs)
        max_diff = max(ipr_diffs)
        
        # Round to bin boundaries
        min_bin = (min_diff // bin_size) * bin_size
        max_bin = ((max_diff // bin_size) + 1) * bin_size
        
        bin_data = defaultdict(lambda: {'point_diffs': [], 'matches': []})
        
        for match in self.match_data:
            ipr_diff = match['ipr_differential']
            bin_center = (ipr_diff // bin_size) * bin_size + bin_size // 2
            
            bin_data[bin_center]['point_diffs'].append(match['point_differential'])
            bin_data[bin_center]['matches'].append(match)
        
        # Calculate statistics for each bin
        results = {}
        for bin_center, data in bin_data.items():
            if len(data['point_diffs']) > 0:
                point_diffs = data['point_diffs']
                results[bin_center] = {
                    'bin_center': bin_center,
                    'bin_range': f"{bin_center - bin_size//2} to {bin_center + bin_size//2}",
                    'matches': len(point_diffs),
                    'avg_point_diff': np.mean(point_diffs),
                    'std_point_diff': np.std(point_diffs),
                    'home_wins': sum(1 for m in data['matches'] if m['home_won']),
                    'home_win_pct': (sum(1 for m in data['matches'] if m['home_won']) / len(data['matches'])) * 100
                }
        
        return results
    
    def fit_linear_regression(self) -> Dict[str, Any]:
        """Fit linear regression model to predict point differentials from IPR differentials."""
        if not self.match_data:
            return {}
        
        # Prepare data
        X = np.array([[m['ipr_differential']] for m in self.match_data])
        y = np.array([m['point_differential'] for m in self.match_data])
        
        # Fit linear regression
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate predictions and statistics
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        
        # Calculate residual standard error
        residuals = y - y_pred
        mse = np.mean(residuals**2)
        rmse = np.sqrt(mse)
        
        # Home advantage interpretation
        home_advantage_points = model.intercept_  # Expected point diff when IPR diff = 0
        ipr_effect = model.coef_[0]  # Additional points per IPR point advantage
        
        # Statistical significance testing
        from scipy.stats import t
        n = len(y)
        
        # Standard error of intercept (home advantage)
        X_mean = np.mean(X)
        sum_sq_x = np.sum((X.flatten() - X_mean)**2)
        se_intercept = rmse * np.sqrt(1/n + X_mean**2/sum_sq_x)
        
        # t-test for home advantage
        t_stat_intercept = home_advantage_points / se_intercept
        p_value_intercept = 2 * (1 - t.cdf(abs(t_stat_intercept), n-2))
        
        # Standard error of slope (IPR effect)
        se_slope = rmse / np.sqrt(sum_sq_x)
        t_stat_slope = ipr_effect / se_slope
        p_value_slope = 2 * (1 - t.cdf(abs(t_stat_slope), n-2))
        
        return {
            'model': model,
            'intercept': home_advantage_points,
            'slope': ipr_effect,
            'r_squared': r2,
            'rmse': rmse,
            'total_matches': len(y),
            'se_intercept': se_intercept,
            'se_slope': se_slope,
            'p_value_intercept': p_value_intercept,
            'p_value_slope': p_value_slope,
            't_stat_intercept': t_stat_intercept,
            't_stat_slope': t_stat_slope
        }
    
    def generate_chart(self, bin_analysis: Dict, regression_analysis: Dict, output_dir: str = "reports/charts") -> str:
        """Generate visualization of home advantage analysis using point differentials."""
        if not bin_analysis or not regression_analysis:
            return ""
        
        # Create chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Left plot: Binned analysis - point differentials
        bin_centers = sorted(bin_analysis.keys())
        avg_point_diffs = [bin_analysis[bc]['avg_point_diff'] for bc in bin_centers]
        match_counts = [bin_analysis[bc]['matches'] for bc in bin_centers]
        std_errors = [bin_analysis[bc]['std_point_diff'] / np.sqrt(bin_analysis[bc]['matches']) 
                     for bc in bin_centers]
        
        bars = ax1.bar(bin_centers, avg_point_diffs, width=4, alpha=0.7, color='steelblue',
                      yerr=std_errors, capsize=3)
        
        # Add match counts on bars
        for i, (bar, count) in enumerate(zip(bars, match_counts)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + (0.5 if height >= 0 else -1),
                    f'n={count}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)
        
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7, label='0 (No Advantage)')
        ax1.axvline(x=0, color='gray', linestyle=':', alpha=0.5, label='Equal IPR')
        
        ax1.set_xlabel('Home Team IPR Advantage')
        ax1.set_ylabel('Average Point Differential (Home - Away)')
        ax1.set_title('Point Differential by IPR Differential\\n(5-point bins with std error)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Right plot: Linear regression
        ipr_diffs = [m['ipr_differential'] for m in self.match_data]
        point_diffs = [m['point_differential'] for m in self.match_data]
        
        # Create regression line
        x_range = np.linspace(min(ipr_diffs) - 5, max(ipr_diffs) + 5, 100)
        model = regression_analysis['model']
        y_line = model.predict(x_range.reshape(-1, 1))
        
        # Plot actual data points
        ax2.scatter(ipr_diffs, point_diffs, alpha=0.4, s=20, color='gray', label='Actual Matches')
        
        # Plot regression line
        ax2.plot(x_range, y_line, 'b-', linewidth=2, label=f'Linear Regression (R² = {regression_analysis["r_squared"]:.3f})')
        
        # Add key lines
        ax2.axhline(y=0, color='red', linestyle='--', alpha=0.7, label='0 (No Advantage)')
        ax2.axvline(x=0, color='gray', linestyle=':', alpha=0.5, label='Equal IPR')
        
        # Mark home advantage
        home_adv = regression_analysis['intercept']
        ax2.axhline(y=home_adv, color='orange', linestyle='-', alpha=0.7, 
                   label=f'Home Advantage: {home_adv:.1f} pts')
        
        ax2.set_xlabel('Home Team IPR Advantage')
        ax2.set_ylabel('Point Differential (Home - Away)')
        ax2.set_title('Linear Regression: Point Differential vs IPR')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save chart
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"home_advantage_ipr_points_analysis_season_{self.season}.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_report(self, bin_analysis: Dict, regression_analysis: Dict) -> str:
        """Generate comprehensive analysis report using point differentials."""
        if not self.match_data:
            return "No match data available for analysis."
        
        report_lines = []
        report_lines.append(f"# Home Field Advantage IPR Analysis (Point Differential Based)")
        report_lines.append(f"## Season {self.season}")
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")
        report_lines.append("**Analysis Method**: Linear regression of point differentials vs IPR differentials")
        report_lines.append("provides more nuanced insights than binary win/loss analysis.")
        report_lines.append("")
        
        # Summary statistics
        total_matches = len(self.match_data)
        point_diffs = [m['point_differential'] for m in self.match_data]
        ipr_diffs = [m['ipr_differential'] for m in self.match_data]
        
        home_wins = sum(1 for m in self.match_data if m['home_won'])
        overall_home_win_pct = (home_wins / total_matches) * 100
        
        avg_point_diff = np.mean(point_diffs)
        avg_ipr_diff = np.mean(ipr_diffs)
        
        report_lines.append("## Summary Statistics")
        report_lines.append("")
        report_lines.append(f"- **Total Matches Analyzed**: {total_matches}")
        report_lines.append(f"- **Home Team Wins**: {home_wins} ({overall_home_win_pct:.1f}%)")
        report_lines.append(f"- **Average Point Differential**: {avg_point_diff:.2f} (Home - Away)")
        report_lines.append(f"- **Average IPR Differential**: {avg_ipr_diff:.1f} (Home - Away)")
        report_lines.append("")
        
        # Regression analysis results
        if regression_analysis:
            home_adv = regression_analysis['intercept']
            ipr_effect = regression_analysis['slope']
            r2 = regression_analysis['r_squared']
            p_val_home = regression_analysis['p_value_intercept']
            p_val_ipr = regression_analysis['p_value_slope']
            
            report_lines.append("## 🏠 Linear Regression Results")
            report_lines.append("")
            report_lines.append(f"**Model**: Point Differential = {home_adv:.2f} + {ipr_effect:.3f} × IPR Differential")
            report_lines.append("")
            report_lines.append(f"- **Home Field Advantage**: {home_adv:.2f} points (p = {p_val_home:.4f})")
            report_lines.append(f"- **IPR Effect**: {ipr_effect:.3f} points per IPR point (p = {p_val_ipr:.4f})")
            report_lines.append(f"- **R-squared**: {r2:.3f} ({r2*100:.1f}% of variance explained)")
            report_lines.append(f"- **RMSE**: {regression_analysis['rmse']:.2f} points")
            report_lines.append("")
            
            # Statistical significance interpretation
            home_significant = p_val_home < 0.05
            ipr_significant = p_val_ipr < 0.001  # Stricter threshold for IPR
            
            if home_significant:
                report_lines.append(f"✅ **Home advantage is statistically significant** (p < 0.05)")
            else:
                report_lines.append(f"⚠️ **Home advantage is not statistically significant** (p = {p_val_home:.3f})")
            
            if ipr_significant:
                report_lines.append(f"✅ **IPR effect is highly significant** (p < 0.001)")
            else:
                report_lines.append(f"⚠️ **IPR effect significance**: p = {p_val_ipr:.3f}")
            
            report_lines.append("")
            
            # Practical interpretation
            report_lines.append("### Interpretation")
            report_lines.append("")
            
            if home_adv > 0:
                report_lines.append(f"🏠 **Home teams score {home_adv:.1f} more points on average** when team strengths are equal")
            else:
                report_lines.append(f"✈️ **Away teams actually score {abs(home_adv):.1f} more points on average** when team strengths are equal")
            
            report_lines.append(f"📈 **Each IPR point advantage is worth {ipr_effect:.2f} additional match points**")
            report_lines.append("")
            
            # Convert to win probability implications
            if home_adv > 0:
                # Rough conversion: assume ~15 points per match on average
                typical_match_points = 15
                home_advantage_pct = (home_adv / typical_match_points) * 100
                report_lines.append(f"🎯 **Estimated impact**: Home advantage worth ~{home_advantage_pct:.1f}% of typical match points")
            
            report_lines.append("")
        
        # Binned analysis
        if bin_analysis:
            report_lines.append("## 📊 Point Differential by IPR Range")
            report_lines.append("")
            report_lines.append("| IPR Advantage Range | Matches | Avg Point Diff | Std Error | Home Win % |")
            report_lines.append("|---------------------|---------|----------------|-----------|------------|")
            
            for bin_center in sorted(bin_analysis.keys()):
                data = bin_analysis[bin_center]
                std_err = data['std_point_diff'] / np.sqrt(data['matches'])
                report_lines.append(f"| {data['bin_range']} | {data['matches']} | {data['avg_point_diff']:+.1f} | ±{std_err:.1f} | {data['home_win_pct']:.1f}% |")
            
            report_lines.append("")
        
        # Practical implications
        report_lines.append("## 🎯 Practical Implications")
        report_lines.append("")
        if regression_analysis:
            home_adv = regression_analysis['intercept']
            ipr_effect = regression_analysis['slope']
            
            report_lines.append(f"1. **Match Predictions**: Add {home_adv:.1f} points for home field advantage")
            report_lines.append(f"2. **IPR Value**: Each IPR point difference is worth {ipr_effect:.2f} match points")
            
            if ipr_effect > 0:
                ipr_for_home_adv = home_adv / ipr_effect if ipr_effect > 0 else 0
                report_lines.append(f"3. **Home Advantage Equivalent**: Playing at home is worth {ipr_for_home_adv:.1f} IPR points")
            
            if home_adv > 1:
                report_lines.append(f"4. **Strategic Value**: Home field advantage provides meaningful scoring benefit")
            elif abs(home_adv) < 0.5:
                report_lines.append(f"4. **Strategic Value**: Home field advantage appears minimal in this data")
        
        return "\\n".join(report_lines)
    
    def run_analysis(self, data_path: str) -> Tuple[str, str]:
        """Run complete analysis and return report and chart paths."""
        # Load and process data
        self.load_matches(data_path)
        self.process_matches()
        
        if not self.match_data:
            return "", ""
        
        # Run analyses
        bin_analysis = self.analyze_by_ipr_bins(bin_size=5)
        regression_analysis = self.fit_linear_regression()
        
        # Generate outputs
        chart_path = self.generate_chart(bin_analysis, regression_analysis)
        
        report_content = self.generate_report(bin_analysis, regression_analysis)
        report_path = f"reports/output/home_advantage_ipr_points_analysis_season_{self.season}.md"
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"Point differential analysis complete:")
        print(f"  Report: {report_path}")
        print(f"  Chart: {chart_path}")
        
        return report_path, chart_path


def main():
    """Main execution function."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python home_advantage_ipr_analysis_points.py <season>")
        print("Example: python home_advantage_ipr_analysis_points.py 20")
        sys.exit(1)
    
    season = sys.argv[1]
    
    # Run analysis
    analyzer = HomeAdvantageIPRPointAnalyzer(season)
    data_path = "mnp-data-archive"
    
    try:
        report_path, chart_path = analyzer.run_analysis(data_path)
        if report_path:
            print(f"\\n📊 Point differential home advantage analysis complete for Season {season}")
        else:
            print("No data available for analysis")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()