#!/usr/bin/env python3
"""
MNP Home Advantage IPR Analysis

Quantifies home field advantage in terms of IPR points by analyzing the relationship
between team IPR differentials, home/away status, and match outcomes.
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report


class HomeAdvantageIPRAnalyzer:
    """Analyze home field advantage in IPR equivalent terms."""
    
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
    
    def calculate_match_points(self, match: Dict[str, Any]) -> Tuple[int, int]:
        """Calculate total points earned by home and away teams."""
        home_points = 0
        away_points = 0
        
        for round_data in match.get('rounds', []):
            for game in round_data.get('games', []):
                if game.get('done', False):
                    home_points += game.get('home_points', 0)
                    away_points += game.get('away_points', 0)
        
        return home_points, away_points
    
    def process_matches(self) -> None:
        """Process matches to extract analysis data."""
        processed_data = []
        
        for match in self.matches:
            # Calculate team IPRs
            home_lineup = match.get('home', {}).get('lineup', [])
            away_lineup = match.get('away', {}).get('lineup', [])
            
            home_ipr = self.calculate_team_ipr(home_lineup)
            away_ipr = self.calculate_team_ipr(away_lineup)
            ipr_differential = home_ipr - away_ipr
            
            # Calculate match outcome
            home_points, away_points = self.calculate_match_points(match)
            
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
        """Analyze home win rates by IPR differential bins."""
        if not self.match_data:
            return {}
        
        # Create bins
        ipr_diffs = [m['ipr_differential'] for m in self.match_data]
        min_diff = min(ipr_diffs)
        max_diff = max(ipr_diffs)
        
        # Round to bin boundaries
        min_bin = (min_diff // bin_size) * bin_size
        max_bin = ((max_diff // bin_size) + 1) * bin_size
        
        bin_data = defaultdict(lambda: {'wins': 0, 'total': 0, 'matches': []})
        
        for match in self.match_data:
            ipr_diff = match['ipr_differential']
            bin_center = (ipr_diff // bin_size) * bin_size + bin_size // 2
            
            bin_data[bin_center]['total'] += 1
            bin_data[bin_center]['matches'].append(match)
            if match['home_won']:
                bin_data[bin_center]['wins'] += 1
        
        # Calculate win percentages
        results = {}
        for bin_center, data in bin_data.items():
            if data['total'] > 0:
                win_pct = (data['wins'] / data['total']) * 100
                results[bin_center] = {
                    'bin_center': bin_center,
                    'bin_range': f"{bin_center - bin_size//2} to {bin_center + bin_size//2}",
                    'matches': data['total'],
                    'home_wins': data['wins'],
                    'home_win_pct': win_pct
                }
        
        return results
    
    def fit_logistic_regression(self) -> Dict[str, Any]:
        """Fit logistic regression model to predict home wins."""
        if not self.match_data:
            return {}
        
        # Prepare data
        X = np.array([[m['ipr_differential']] for m in self.match_data])
        y = np.array([1 if m['home_won'] else 0 for m in self.match_data])
        
        # Fit model
        model = LogisticRegression()
        model.fit(X, y)
        
        # Calculate predictions
        y_pred = model.predict(X)
        y_prob = model.predict_proba(X)[:, 1]
        
        # Find equilibrium points
        # Where P(home_win) = 0.5
        equilibrium_ipr_diff = -model.intercept_[0] / model.coef_[0][0]
        
        # Home advantage in IPR terms
        # At 0 IPR differential, what's the probability of home winning?
        prob_at_zero = model.predict_proba([[0]])[0][1]
        
        # What IPR differential would give 50% chance on neutral field?
        # This is our "home advantage in IPR points"
        home_advantage_ipr = equilibrium_ipr_diff
        
        return {
            'model': model,
            'coefficient': model.coef_[0][0],
            'intercept': model.intercept_[0],
            'equilibrium_ipr_diff': equilibrium_ipr_diff,
            'prob_at_zero_diff': prob_at_zero,
            'home_advantage_ipr': home_advantage_ipr,
            'accuracy': (y_pred == y).mean(),
            'total_matches': len(y)
        }
    
    def generate_chart(self, bin_analysis: Dict, regression_analysis: Dict, output_dir: str = "reports/charts") -> str:
        """Generate visualization of home advantage analysis."""
        if not bin_analysis or not regression_analysis:
            return ""
        
        # Create chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Left plot: Binned analysis
        bin_centers = sorted(bin_analysis.keys())
        win_pcts = [bin_analysis[bc]['home_win_pct'] for bc in bin_centers]
        match_counts = [bin_analysis[bc]['matches'] for bc in bin_centers]
        
        bars = ax1.bar(bin_centers, win_pcts, width=4, alpha=0.7, color='steelblue')
        
        # Add match counts on bars
        for i, (bar, count) in enumerate(zip(bars, match_counts)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'n={count}', ha='center', va='bottom', fontsize=8)
        
        ax1.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50% (Equilibrium)')
        ax1.axvline(x=0, color='gray', linestyle=':', alpha=0.5, label='Equal IPR')
        
        ax1.set_xlabel('Home Team IPR Advantage')
        ax1.set_ylabel('Home Team Win Percentage')
        ax1.set_title('Home Win Rate by IPR Differential\n(5-point bins)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Right plot: Logistic regression curve
        ipr_diffs = [m['ipr_differential'] for m in self.match_data]
        home_wins = [1 if m['home_won'] else 0 for m in self.match_data]
        
        # Create smooth curve
        x_range = np.linspace(min(ipr_diffs) - 5, max(ipr_diffs) + 5, 200)
        model = regression_analysis['model']
        y_probs = model.predict_proba(x_range.reshape(-1, 1))[:, 1] * 100
        
        # Plot actual data points
        ax2.scatter(ipr_diffs, [w * 100 for w in home_wins], alpha=0.3, s=20, color='gray', label='Actual Matches')
        
        # Plot regression curve
        ax2.plot(x_range, y_probs, 'b-', linewidth=2, label='Logistic Regression')
        
        # Add key lines
        ax2.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50% (Equilibrium)')
        ax2.axvline(x=0, color='gray', linestyle=':', alpha=0.5, label='Equal IPR')
        
        # Mark equilibrium point
        eq_point = regression_analysis['equilibrium_ipr_diff']
        ax2.axvline(x=eq_point, color='orange', linestyle='-', alpha=0.7, 
                   label=f'Equilibrium: {eq_point:.1f} IPR')
        
        ax2.set_xlabel('Home Team IPR Advantage')
        ax2.set_ylabel('Probability of Home Win (%)')
        ax2.set_title('Logistic Regression: Home Win Probability')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 100)
        
        plt.tight_layout()
        
        # Save chart
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"home_advantage_ipr_analysis_season_{self.season}.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_report(self, bin_analysis: Dict, regression_analysis: Dict) -> str:
        """Generate comprehensive analysis report."""
        if not self.match_data:
            return "No match data available for analysis."
        
        report_lines = []
        report_lines.append(f"# Home Field Advantage IPR Analysis")
        report_lines.append(f"## Season {self.season}")
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")
        
        # Summary statistics
        total_matches = len(self.match_data)
        home_wins = sum(1 for m in self.match_data if m['home_won'])
        overall_home_win_pct = (home_wins / total_matches) * 100
        
        ipr_diffs = [m['ipr_differential'] for m in self.match_data]
        avg_ipr_diff = np.mean(ipr_diffs)
        
        report_lines.append("## Summary Statistics")
        report_lines.append("")
        report_lines.append(f"- **Total Matches Analyzed**: {total_matches}")
        report_lines.append(f"- **Home Team Wins**: {home_wins} ({overall_home_win_pct:.1f}%)")
        report_lines.append(f"- **Average IPR Differential**: {avg_ipr_diff:.1f} (Home - Away)")
        report_lines.append("")
        
        # Regression analysis results
        if regression_analysis:
            eq_diff = regression_analysis['equilibrium_ipr_diff']
            prob_at_zero = regression_analysis['prob_at_zero_diff'] * 100
            home_adv_ipr = abs(regression_analysis['home_advantage_ipr'])
            
            report_lines.append("## 🏠 Home Field Advantage Analysis")
            report_lines.append("")
            report_lines.append(f"**Key Finding: Home field advantage is worth approximately {home_adv_ipr:.1f} IPR points**")
            report_lines.append("")
            report_lines.append("### Logistic Regression Results")
            report_lines.append("")
            report_lines.append(f"- **Model Accuracy**: {regression_analysis['accuracy']:.1%}")
            report_lines.append(f"- **Home win probability at equal IPR**: {prob_at_zero:.1f}%")
            report_lines.append(f"- **Equilibrium point**: Home team needs {eq_diff:.1f} fewer IPR points for 50% win chance")
            report_lines.append(f"- **Coefficient**: {regression_analysis['coefficient']:.4f} (log-odds per IPR point)")
            report_lines.append("")
            
            # Interpretation
            report_lines.append("### Interpretation")
            report_lines.append("")
            if eq_diff < 0:
                report_lines.append(f"🏠 **Home teams can win 50% of matches even when their total IPR is {abs(eq_diff):.1f} points lower than the away team.**")
            else:
                report_lines.append(f"✈️ **Away teams actually have an advantage - home teams need {eq_diff:.1f} extra IPR points for 50% win rate.**")
            report_lines.append("")
            report_lines.append(f"This means playing at home is equivalent to having {home_adv_ipr:.1f} additional IPR points distributed across your team.")
            report_lines.append("")
        
        # Binned analysis
        if bin_analysis:
            report_lines.append("## 📊 Win Rate by IPR Differential")
            report_lines.append("")
            report_lines.append("| IPR Advantage Range | Matches | Home Wins | Win Rate |")
            report_lines.append("|---------------------|---------|-----------|----------|")
            
            for bin_center in sorted(bin_analysis.keys()):
                data = bin_analysis[bin_center]
                report_lines.append(f"| {data['bin_range']} | {data['matches']} | {data['home_wins']} | {data['home_win_pct']:.1f}% |")
            
            report_lines.append("")
        
        # Practical implications
        report_lines.append("## 🎯 Practical Implications")
        report_lines.append("")
        if regression_analysis and regression_analysis['home_advantage_ipr'] < 0:
            home_adv = abs(regression_analysis['home_advantage_ipr'])
            report_lines.append(f"1. **Team Strategy**: Home teams can compete effectively even with {home_adv:.1f} fewer total IPR points")
            report_lines.append(f"2. **Match Predictions**: Factor in ~{home_adv:.1f} IPR point advantage when predicting home games")
            report_lines.append(f"3. **Lineup Decisions**: Home teams can be more aggressive with player rotation/substitutions")
        
        return "\n".join(report_lines)
    
    def run_analysis(self, data_path: str) -> Tuple[str, str]:
        """Run complete analysis and return report and chart paths."""
        # Load and process data
        self.load_matches(data_path)
        self.process_matches()
        
        if not self.match_data:
            return "", ""
        
        # Run analyses
        bin_analysis = self.analyze_by_ipr_bins(bin_size=5)
        regression_analysis = self.fit_logistic_regression()
        
        # Generate outputs
        chart_path = self.generate_chart(bin_analysis, regression_analysis)
        
        report_content = self.generate_report(bin_analysis, regression_analysis)
        report_path = f"reports/output/home_advantage_ipr_analysis_season_{self.season}.md"
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"Analysis complete:")
        print(f"  Report: {report_path}")
        print(f"  Chart: {chart_path}")
        
        return report_path, chart_path


def main():
    """Main execution function."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python home_advantage_ipr_analysis.py <season>")
        print("Example: python home_advantage_ipr_analysis.py 20")
        sys.exit(1)
    
    season = sys.argv[1]
    
    # Run analysis
    analyzer = HomeAdvantageIPRAnalyzer(season)
    data_path = "mnp-data-archive"
    
    try:
        report_path, chart_path = analyzer.run_analysis(data_path)
        if report_path:
            print(f"\n🏠 Home advantage analysis complete for Season {season}")
        else:
            print("No data available for analysis")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()