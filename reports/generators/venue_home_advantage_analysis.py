#!/usr/bin/env python3
"""
MNP Venue Home Advantage Analysis

Analyzes home field advantage for each individual venue to determine which venues
provide the strongest home advantage for their teams.
"""

import json
import os
import glob
import csv
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Tuple
from sklearn.linear_model import LogisticRegression
import warnings
warnings.filterwarnings('ignore')


class VenueHomeAdvantageAnalyzer:
    """Analyze home field advantage by individual venue."""
    
    def __init__(self, season: str):
        """Initialize analyzer with season."""
        self.season = season
        self.matches = []
        self.team_venues = {}  # team_key -> venue_key
        self.venue_names = {}  # venue_key -> venue_name
        self.venue_stats = defaultdict(lambda: {
            'matches': [],
            'home_wins': 0,
            'total_matches': 0,
            'home_points': 0,
            'away_points': 0,
            'total_home_ipr': 0,
            'total_away_ipr': 0
        })
        
    def load_team_venue_mapping(self, data_path: str) -> None:
        """Load team to venue mappings."""
        teams_file = f"{data_path}/season-{self.season}/teams.csv"
        venues_file = f"{data_path}/season-{self.season}/venues.csv"
        
        # Load team venues
        with open(teams_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    team_key, venue_key = row[0], row[1]
                    self.team_venues[team_key] = venue_key
        
        # Load venue names
        with open(venues_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    venue_key, venue_name = row[0], row[1]
                    self.venue_names[venue_key] = venue_name
        
        print(f"Loaded {len(self.team_venues)} team-venue mappings")
        print(f"Loaded {len(self.venue_names)} venue names")
        
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
        """Process matches to extract venue-specific data."""
        for match in self.matches:
            home_team = match.get('home', {}).get('key', '')
            away_team = match.get('away', {}).get('key', '')
            match_venue = match.get('venue', {}).get('key', '')
            
            home_team_venue = self.team_venues.get(home_team, '')
            away_team_venue = self.team_venues.get(away_team, '')
            
            # Only analyze matches where home team is playing at their actual home venue
            # and away team is NOT from the same venue
            if home_team_venue != match_venue or home_team_venue == away_team_venue:
                continue
            
            # Calculate match data
            home_lineup = match.get('home', {}).get('lineup', [])
            away_lineup = match.get('away', {}).get('lineup', [])
            
            home_ipr = self.calculate_team_ipr(home_lineup)
            away_ipr = self.calculate_team_ipr(away_lineup)
            ipr_differential = home_ipr - away_ipr
            
            home_points, away_points = self.calculate_match_points(match)
            
            if home_points + away_points == 0:
                continue  # Skip matches with no points recorded
            
            home_won = home_points > away_points
            
            match_data = {
                'match_key': match['key'],
                'home_team': home_team,
                'away_team': away_team,
                'home_ipr': home_ipr,
                'away_ipr': away_ipr,
                'ipr_differential': ipr_differential,
                'home_points': home_points,
                'away_points': away_points,
                'home_won': home_won,
                'point_differential': home_points - away_points
            }
            
            # Add to venue stats
            venue_data = self.venue_stats[match_venue]
            venue_data['matches'].append(match_data)
            venue_data['total_matches'] += 1
            venue_data['home_points'] += home_points
            venue_data['away_points'] += away_points
            venue_data['total_home_ipr'] += home_ipr
            venue_data['total_away_ipr'] += away_ipr
            
            if home_won:
                venue_data['home_wins'] += 1
        
        # Filter out venues with insufficient data
        min_matches = 3
        venues_with_data = {v: data for v, data in self.venue_stats.items() 
                           if data['total_matches'] >= min_matches}
        
        print(f"Processed matches for {len(venues_with_data)} venues with ≥{min_matches} home matches")
        self.venue_stats = venues_with_data
    
    def calculate_venue_advantages(self) -> List[Dict[str, Any]]:
        """Calculate home advantage metrics for each venue."""
        venue_advantages = []
        
        for venue_key, data in self.venue_stats.items():
            total_matches = data['total_matches']
            home_wins = data['home_wins']
            home_win_pct = (home_wins / total_matches) * 100
            
            # Calculate average IPR differential and point differential
            matches = data['matches']
            ipr_diffs = [m['ipr_differential'] for m in matches]
            point_diffs = [m['point_differential'] for m in matches]
            
            avg_ipr_diff = np.mean(ipr_diffs)
            avg_point_diff = np.mean(point_diffs)
            
            # Try to fit logistic regression if we have enough variation in IPR
            ipr_range = max(ipr_diffs) - min(ipr_diffs) if ipr_diffs else 0
            equilibrium_ipr_diff = None
            home_advantage_ipr = None
            
            if len(matches) >= 5 and ipr_range > 5:  # Need variation for meaningful regression
                try:
                    X = np.array(ipr_diffs).reshape(-1, 1)
                    y = np.array([1 if m['home_won'] else 0 for m in matches])
                    
                    model = LogisticRegression()
                    model.fit(X, y)
                    
                    equilibrium_ipr_diff = -model.intercept_[0] / model.coef_[0][0]
                    home_advantage_ipr = abs(equilibrium_ipr_diff)
                except:
                    pass  # Regression failed, use simpler metrics
            
            venue_advantages.append({
                'venue_key': venue_key,
                'venue_name': self.venue_names.get(venue_key, venue_key),
                'total_matches': total_matches,
                'home_wins': home_wins,
                'home_win_pct': home_win_pct,
                'avg_ipr_diff': avg_ipr_diff,
                'avg_point_diff': avg_point_diff,
                'equilibrium_ipr_diff': equilibrium_ipr_diff,
                'home_advantage_ipr': home_advantage_ipr,
                'total_home_points': data['home_points'],
                'total_away_points': data['away_points']
            })
        
        # Sort by home win percentage (descending)
        venue_advantages.sort(key=lambda x: x['home_win_pct'], reverse=True)
        
        return venue_advantages
    
    def generate_chart(self, venue_advantages: List[Dict], output_dir: str = "reports/charts") -> str:
        """Generate visualization of venue home advantages."""
        if not venue_advantages:
            return ""
        
        # Prepare data for plotting
        venue_names = [v['venue_name'][:15] + ('...' if len(v['venue_name']) > 15 else '') 
                      for v in venue_advantages]
        win_pcts = [v['home_win_pct'] for v in venue_advantages]
        match_counts = [v['total_matches'] for v in venue_advantages]
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Top plot: Home win percentages
        colors = ['darkgreen' if pct >= 70 else 'green' if pct >= 60 else 'orange' if pct >= 50 else 'red' 
                 for pct in win_pcts]
        
        bars1 = ax1.barh(venue_names, win_pcts, color=colors, alpha=0.7)
        
        # Add match counts on bars
        for i, (bar, count) in enumerate(zip(bars1, match_counts)):
            width = bar.get_width()
            ax1.text(width + 1, bar.get_y() + bar.get_height()/2, 
                    f'n={count}', ha='left', va='center', fontsize=8)
        
        ax1.axvline(x=50, color='black', linestyle='--', alpha=0.5, label='50% (No Advantage)')
        ax1.axvline(x=60, color='blue', linestyle=':', alpha=0.5, label='60% (Strong Advantage)')
        
        ax1.set_xlabel('Home Team Win Percentage (%)')
        ax1.set_title(f'Home Field Advantage by Venue - Season {self.season}\\n(Ordered by Home Win %)', 
                     fontweight='bold')
        ax1.legend(loc='lower right')
        ax1.grid(True, axis='x', alpha=0.3)
        ax1.set_xlim(0, 100)
        
        # Bottom plot: Average point differential
        point_diffs = [v['avg_point_diff'] for v in venue_advantages]
        colors2 = ['darkgreen' if diff >= 3 else 'green' if diff >= 1 else 'orange' if diff >= -1 else 'red' 
                  for diff in point_diffs]
        
        bars2 = ax2.barh(venue_names, point_diffs, color=colors2, alpha=0.7)
        
        ax2.axvline(x=0, color='black', linestyle='--', alpha=0.5, label='0 (No Advantage)')
        ax2.axvline(x=2, color='blue', linestyle=':', alpha=0.5, label='+2 Points (Strong)')
        
        ax2.set_xlabel('Average Point Differential (Home - Away)')
        ax2.set_title('Average Match Point Advantage by Venue', fontweight='bold')
        ax2.legend(loc='lower right')
        ax2.grid(True, axis='x', alpha=0.3)
        
        plt.tight_layout()
        
        # Save chart
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"venue_home_advantage_season_{self.season}.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_report(self, venue_advantages: List[Dict]) -> str:
        """Generate comprehensive venue home advantage report."""
        if not venue_advantages:
            return "No venue data available for analysis."
        
        report_lines = []
        report_lines.append(f"# Home Field Advantage by Venue")
        report_lines.append(f"## Season {self.season}")
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")
        
        # Summary statistics
        total_venues = len(venue_advantages)
        total_matches = sum(v['total_matches'] for v in venue_advantages)
        avg_home_win_pct = np.mean([v['home_win_pct'] for v in venue_advantages])
        
        strong_advantage_venues = len([v for v in venue_advantages if v['home_win_pct'] >= 65])
        weak_advantage_venues = len([v for v in venue_advantages if v['home_win_pct'] < 55])
        
        report_lines.append("## 📊 Summary Statistics")
        report_lines.append("")
        report_lines.append(f"- **Venues Analyzed**: {total_venues} (with ≥3 home matches)")
        report_lines.append(f"- **Total Home Matches**: {total_matches}")
        report_lines.append(f"- **Average Home Win Rate**: {avg_home_win_pct:.1f}%")
        report_lines.append(f"- **Strong Home Advantage** (≥65%): {strong_advantage_venues} venues")
        report_lines.append(f"- **Weak Home Advantage** (<55%): {weak_advantage_venues} venues")
        report_lines.append("")
        
        # Top and bottom venues
        report_lines.append("## 🏆 Best Home Field Advantages")
        report_lines.append("")
        report_lines.append("| Rank | Venue | Matches | Home Wins | Win % | Avg Points | IPR Adv* |")
        report_lines.append("|------|-------|---------|-----------|--------|------------|-----------|")
        
        for i, venue in enumerate(venue_advantages[:10], 1):  # Top 10
            ipr_adv = f"{venue['home_advantage_ipr']:.1f}" if venue['home_advantage_ipr'] else "N/A"
            report_lines.append(f"| {i} | **{venue['venue_name']}** | {venue['total_matches']} | {venue['home_wins']} | {venue['home_win_pct']:.1f}% | +{venue['avg_point_diff']:.1f} | {ipr_adv} |")
        
        report_lines.append("")
        report_lines.append("*IPR Advantage: Estimated home advantage in IPR points (requires ≥5 matches with IPR variation)")
        report_lines.append("")
        
        # Bottom venues
        if len(venue_advantages) > 10:
            report_lines.append("## 🔻 Weakest Home Field Advantages")
            report_lines.append("")
            report_lines.append("| Rank | Venue | Matches | Home Wins | Win % | Avg Points | IPR Adv* |")
            report_lines.append("|------|-------|---------|-----------|--------|------------|-----------|")
            
            bottom_venues = venue_advantages[-5:]  # Bottom 5
            for i, venue in enumerate(bottom_venues, len(venue_advantages) - 4):
                ipr_adv = f"{venue['home_advantage_ipr']:.1f}" if venue['home_advantage_ipr'] else "N/A"
                report_lines.append(f"| {i} | **{venue['venue_name']}** | {venue['total_matches']} | {venue['home_wins']} | {venue['home_win_pct']:.1f}% | {venue['avg_point_diff']:+.1f} | {ipr_adv} |")
            
            report_lines.append("")
        
        # Detailed breakdown
        report_lines.append("## 📋 Complete Venue Rankings")
        report_lines.append("")
        report_lines.append("| Venue | Home Win % | Matches | Point Diff | Notes |")
        report_lines.append("|-------|------------|---------|------------|-------|")
        
        for venue in venue_advantages:
            # Determine category
            win_pct = venue['home_win_pct']
            if win_pct >= 70:
                category = "🔥 Dominant"
            elif win_pct >= 60:
                category = "💪 Strong"
            elif win_pct >= 55:
                category = "✅ Good"
            elif win_pct >= 45:
                category = "⚠️ Weak"
            else:
                category = "❌ Poor"
            
            report_lines.append(f"| **{venue['venue_name']}** | {win_pct:.1f}% | {venue['total_matches']} | {venue['avg_point_diff']:+.1f} | {category} |")
        
        report_lines.append("")
        
        # Insights
        report_lines.append("## 🔍 Key Insights")
        report_lines.append("")
        
        best_venue = venue_advantages[0]
        worst_venue = venue_advantages[-1]
        
        report_lines.append(f"1. **Strongest Home Advantage**: {best_venue['venue_name']} ({best_venue['home_win_pct']:.1f}% win rate)")
        report_lines.append(f"2. **Weakest Home Advantage**: {worst_venue['venue_name']} ({worst_venue['home_win_pct']:.1f}% win rate)")
        report_lines.append(f"3. **Range**: {best_venue['home_win_pct'] - worst_venue['home_win_pct']:.1f} percentage point difference between best and worst venues")
        
        # Calculate venue effect variation
        win_pct_std = np.std([v['home_win_pct'] for v in venue_advantages])
        report_lines.append(f"4. **Venue Variation**: {win_pct_std:.1f} percentage point standard deviation in home win rates")
        
        if win_pct_std > 10:
            report_lines.append("   - High variation suggests significant venue-specific effects")
        else:
            report_lines.append("   - Moderate variation suggests venue effects are relatively consistent")
        
        return "\\n".join(report_lines)
    
    def run_analysis(self, data_path: str) -> Tuple[str, str]:
        """Run complete venue home advantage analysis."""
        # Load data
        self.load_team_venue_mapping(data_path)
        self.load_matches(data_path)
        self.process_matches()
        
        if not self.venue_stats:
            return "", ""
        
        # Calculate advantages
        venue_advantages = self.calculate_venue_advantages()
        
        if not venue_advantages:
            return "", ""
        
        # Generate outputs
        chart_path = self.generate_chart(venue_advantages)
        
        report_content = self.generate_report(venue_advantages)
        report_path = f"reports/output/venue_home_advantage_season_{self.season}.md"
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"\\nVenue home advantage analysis complete:")
        print(f"  Report: {report_path}")
        print(f"  Chart: {chart_path}")
        
        return report_path, chart_path


def main():
    """Main execution function."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python venue_home_advantage_analysis.py <season>")
        print("Example: python venue_home_advantage_analysis.py 21")
        sys.exit(1)
    
    season = sys.argv[1]
    
    # Run analysis
    analyzer = VenueHomeAdvantageAnalyzer(season)
    data_path = "mnp-data-archive"
    
    try:
        report_path, chart_path = analyzer.run_analysis(data_path)
        if report_path:
            print(f"\\n🏟️ Venue home advantage analysis complete for Season {season}")
        else:
            print("No venue data available for analysis")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()