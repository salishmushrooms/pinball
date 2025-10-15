#!/usr/bin/env python3
"""
MNP Venue Home Advantage Analysis (Corrected)

Analyzes home field advantage for each venue using proper point attribution
based on the round structure and individual player points.

Round structure:
- Round 1: Away, Home, Away, Home (positions 1,2,3,4)
- Round 2: Home, Away (positions 1,2)
- Round 3: Away, Home (positions 1,2)  
- Round 4: Home, Away, Home, Away (positions 1,2,3,4)
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
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class CorrectedVenueHomeAdvantageAnalyzer:
    """Analyze home field advantage by venue using correct point attribution."""
    
    def __init__(self, season: str):
        """Initialize analyzer with season."""
        self.season = season
        self.matches = []
        self.team_venues = {}  # team_key -> venue_key
        self.venue_names = {}  # venue_key -> venue_name
        self.venue_stats = defaultdict(lambda: {
            'matches': [],
            'total_home_points': 0,
            'total_away_points': 0,
            'total_matches': 0,
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
        """Process matches to extract venue-specific data with correct point attribution."""
        for match in self.matches:
            home_team = match.get('home', {}).get('key', '')
            away_team = match.get('away', {}).get('key', '')
            match_venue = match.get('venue', {}).get('key', '')
            
            home_team_venue = self.team_venues.get(home_team, '')
            away_team_venue = self.team_venues.get(away_team, '')
            
            # Only analyze matches where home team is playing at their actual home venue
            # and away team is NOT from the same venue (exclude home vs home matches)
            if home_team_venue != match_venue or home_team_venue == away_team_venue:
                continue
            
            # Calculate match data
            home_lineup = match.get('home', {}).get('lineup', [])
            away_lineup = match.get('away', {}).get('lineup', [])
            
            home_ipr = self.calculate_team_ipr(home_lineup)
            away_ipr = self.calculate_team_ipr(away_lineup)
            ipr_differential = home_ipr - away_ipr
            
            # Use corrected point calculation
            home_points, away_points = self.calculate_correct_team_points(match)
            
            if home_points + away_points == 0:
                continue  # Skip matches with no points recorded
            
            home_won = home_points > away_points
            point_differential = home_points - away_points
            
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
                'point_differential': point_differential,
                'total_points': home_points + away_points
            }
            
            # Add to venue stats
            venue_data = self.venue_stats[match_venue]
            venue_data['matches'].append(match_data)
            venue_data['total_matches'] += 1
            venue_data['total_home_points'] += home_points
            venue_data['total_away_points'] += away_points
            venue_data['total_home_ipr'] += home_ipr
            venue_data['total_away_ipr'] += away_ipr
        
        # Filter out venues with insufficient data
        min_matches = 3
        venues_with_data = {v: data for v, data in self.venue_stats.items() 
                           if data['total_matches'] >= min_matches}
        
        print(f"Processed matches for {len(venues_with_data)} venues with ≥{min_matches} home matches")
        self.venue_stats = venues_with_data
    
    def calculate_ipr_adjusted_advantage(self, matches: List[Dict]) -> Dict[str, float]:
        """Calculate home advantage adjusted for IPR differential using regression."""
        if len(matches) < 5:
            return {'raw_advantage': np.nan, 'ipr_adjusted_advantage': np.nan, 'ipr_effect': np.nan}
        
        # Prepare data for regression
        ipr_diffs = [m['ipr_differential'] for m in matches]
        point_diffs = [m['point_differential'] for m in matches]
        
        # Check if we have enough IPR variation for meaningful regression
        if max(ipr_diffs) - min(ipr_diffs) < 3:
            return {'raw_advantage': np.mean(point_diffs), 'ipr_adjusted_advantage': np.nan, 'ipr_effect': np.nan}
        
        try:
            # Linear regression: point_differential = intercept + coefficient * ipr_differential
            # intercept = home advantage when IPR is equal
            # coefficient = how much each IPR point is worth in match points
            slope, intercept, r_value, p_value, std_err = stats.linregress(ipr_diffs, point_diffs)
            
            return {
                'raw_advantage': np.mean(point_diffs),
                'ipr_adjusted_advantage': intercept,  # Home advantage at IPR=0
                'ipr_effect': slope,  # Points per IPR differential
                'r_squared': r_value ** 2,
                'p_value': p_value
            }
        except:
            return {'raw_advantage': np.mean(point_diffs), 'ipr_adjusted_advantage': np.nan, 'ipr_effect': np.nan}
    
    def calculate_venue_advantages(self) -> List[Dict[str, Any]]:
        """Calculate home advantage metrics for each venue."""
        venue_advantages = []
        
        for venue_key, data in self.venue_stats.items():
            total_matches = data['total_matches']
            matches = data['matches']
            
            # Basic statistics
            home_wins = sum(1 for m in matches if m['home_won'])
            home_win_pct = (home_wins / total_matches) * 100
            
            total_home_points = sum(m['home_points'] for m in matches)
            total_away_points = sum(m['away_points'] for m in matches)
            total_points = total_home_points + total_away_points
            home_point_pct = (total_home_points / total_points) * 100 if total_points > 0 else 0
            
            # Calculate averages
            avg_ipr_diff = np.mean([m['ipr_differential'] for m in matches])
            avg_point_diff = np.mean([m['point_differential'] for m in matches])
            avg_home_points = np.mean([m['home_points'] for m in matches])
            avg_away_points = np.mean([m['away_points'] for m in matches])
            
            # IPR-adjusted analysis
            ipr_analysis = self.calculate_ipr_adjusted_advantage(matches)
            
            venue_advantages.append({
                'venue_key': venue_key,
                'venue_name': self.venue_names.get(venue_key, venue_key),
                'total_matches': total_matches,
                'home_wins': home_wins,
                'home_win_pct': home_win_pct,
                'total_home_points': total_home_points,
                'total_away_points': total_away_points,
                'home_point_pct': home_point_pct,
                'avg_ipr_diff': avg_ipr_diff,
                'avg_point_diff': avg_point_diff,
                'avg_home_points': avg_home_points,
                'avg_away_points': avg_away_points,
                'raw_advantage': ipr_analysis['raw_advantage'],
                'ipr_adjusted_advantage': ipr_analysis['ipr_adjusted_advantage'],
                'ipr_effect': ipr_analysis['ipr_effect'],
                'r_squared': ipr_analysis.get('r_squared', np.nan),
                'p_value': ipr_analysis.get('p_value', np.nan)
            })
        
        # Sort by IPR-adjusted advantage (or raw advantage if IPR adjustment unavailable)
        def sort_key(x):
            if not np.isnan(x['ipr_adjusted_advantage']):
                return x['ipr_adjusted_advantage']
            else:
                return x['raw_advantage']
        
        venue_advantages.sort(key=sort_key, reverse=True)
        
        return venue_advantages
    
    def generate_chart(self, venue_advantages: List[Dict], output_dir: str = "reports/charts") -> str:
        """Generate visualization of venue home advantages."""
        if not venue_advantages:
            return ""
        
        # Create figure with three subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12))
        
        # Prepare data
        venue_names = [v['venue_name'][:15] + ('...' if len(v['venue_name']) > 15 else '') 
                      for v in venue_advantages]
        
        # Plot 1: Home point percentage
        home_point_pcts = [v['home_point_pct'] for v in venue_advantages]
        colors1 = ['darkgreen' if pct >= 55 else 'green' if pct >= 52 else 'orange' if pct >= 48 else 'red' 
                  for pct in home_point_pcts]
        
        bars1 = ax1.barh(venue_names, home_point_pcts, color=colors1, alpha=0.7)
        ax1.axvline(x=50, color='black', linestyle='--', alpha=0.5, label='50% (No Advantage)')
        ax1.set_xlabel('Home Team Point Percentage (%)')
        ax1.set_title(f'Home Field Advantage by Venue - Season {self.season}\\n(% of Total Points Earned by Home Team)', fontweight='bold')
        ax1.legend()
        ax1.grid(True, axis='x', alpha=0.3)
        ax1.set_xlim(30, 70)
        
        # Plot 2: Raw point advantage
        raw_advantages = [v['raw_advantage'] for v in venue_advantages]
        colors2 = ['darkgreen' if diff >= 3 else 'green' if diff >= 1 else 'orange' if diff >= -1 else 'red' 
                  for diff in raw_advantages]
        
        bars2 = ax2.barh(venue_names, raw_advantages, color=colors2, alpha=0.7)
        ax2.axvline(x=0, color='black', linestyle='--', alpha=0.5, label='0 (No Advantage)')
        ax2.set_xlabel('Average Point Differential (Home - Away)')
        ax2.set_title('Raw Point Advantage by Venue', fontweight='bold')
        ax2.legend()
        ax2.grid(True, axis='x', alpha=0.3)
        
        # Plot 3: IPR-adjusted advantage (where available)
        ipr_adjusted = [v['ipr_adjusted_advantage'] if not np.isnan(v['ipr_adjusted_advantage']) else v['raw_advantage'] 
                       for v in venue_advantages]
        has_adjustment = [not np.isnan(v['ipr_adjusted_advantage']) for v in venue_advantages]
        colors3 = ['darkblue' if has_adj else 'lightblue' for has_adj in has_adjustment]
        
        bars3 = ax3.barh(venue_names, ipr_adjusted, color=colors3, alpha=0.7)
        ax3.axvline(x=0, color='black', linestyle='--', alpha=0.5, label='0 (No Advantage)')
        ax3.set_xlabel('IPR-Adjusted Point Advantage')
        ax3.set_title('IPR-Adjusted Home Advantage (Dark = Regression Available)', fontweight='bold')
        ax3.legend()
        ax3.grid(True, axis='x', alpha=0.3)
        
        plt.tight_layout()
        
        # Save chart
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"corrected_venue_home_advantage_season_{self.season}.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_report(self, venue_advantages: List[Dict]) -> str:
        """Generate comprehensive venue home advantage report."""
        if not venue_advantages:
            return "No venue data available for analysis."
        
        report_lines = []
        report_lines.append(f"# Corrected Home Field Advantage by Venue")
        report_lines.append(f"## Season {self.season}")
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")
        report_lines.append("**Analysis Method**: Individual player points correctly attributed to home/away teams")
        report_lines.append("based on round structure. IPR-adjusted advantage controls for team strength differences.")
        report_lines.append("")
        
        # Summary statistics
        total_venues = len(venue_advantages)
        total_matches = sum(v['total_matches'] for v in venue_advantages)
        avg_home_point_pct = np.mean([v['home_point_pct'] for v in venue_advantages])
        
        venues_with_regression = len([v for v in venue_advantages if not np.isnan(v['ipr_adjusted_advantage'])])
        
        report_lines.append("## 📊 Summary Statistics")
        report_lines.append("")
        report_lines.append(f"- **Venues Analyzed**: {total_venues} (with ≥3 home matches)")
        report_lines.append(f"- **Total Home Matches**: {total_matches}")
        report_lines.append(f"- **Average Home Point %**: {avg_home_point_pct:.1f}%")
        report_lines.append(f"- **Venues with IPR Regression**: {venues_with_regression} (≥5 matches with IPR variation)")
        report_lines.append("")
        
        # Top venues
        report_lines.append("## 🏆 Best Home Field Advantages")
        report_lines.append("")
        report_lines.append("| Rank | Venue | Matches | Points % | Raw Adv | IPR Adj | IPR Effect |")
        report_lines.append("|------|-------|---------|----------|---------|---------|------------|")
        
        for i, venue in enumerate(venue_advantages[:10], 1):  # Top 10
            ipr_adj = f"{venue['ipr_adjusted_advantage']:.1f}" if not np.isnan(venue['ipr_adjusted_advantage']) else "N/A"
            ipr_effect = f"{venue['ipr_effect']:.2f}" if not np.isnan(venue['ipr_effect']) else "N/A"
            report_lines.append(f"| {i} | **{venue['venue_name']}** | {venue['total_matches']} | {venue['home_point_pct']:.1f}% | +{venue['raw_advantage']:.1f} | {ipr_adj} | {ipr_effect} |")
        
        report_lines.append("")
        report_lines.append("*Points %: Percentage of total match points earned by home team*")
        report_lines.append("*Raw Adv: Average point differential (home - away)*")  
        report_lines.append("*IPR Adj: Home advantage adjusted for team IPR differences*")
        report_lines.append("*IPR Effect: Additional points per IPR point advantage*")
        report_lines.append("")
        
        # Bottom venues
        if len(venue_advantages) > 10:
            report_lines.append("## 🔻 Weakest Home Field Advantages")
            report_lines.append("")
            report_lines.append("| Rank | Venue | Matches | Points % | Raw Adv | IPR Adj | IPR Effect |")
            report_lines.append("|------|-------|---------|----------|---------|---------|------------|")
            
            bottom_venues = venue_advantages[-5:]  # Bottom 5
            for i, venue in enumerate(bottom_venues, len(venue_advantages) - 4):
                ipr_adj = f"{venue['ipr_adjusted_advantage']:.1f}" if not np.isnan(venue['ipr_adjusted_advantage']) else "N/A"
                ipr_effect = f"{venue['ipr_effect']:.2f}" if not np.isnan(venue['ipr_effect']) else "N/A"
                report_lines.append(f"| {i} | **{venue['venue_name']}** | {venue['total_matches']} | {venue['home_point_pct']:.1f}% | {venue['raw_advantage']:+.1f} | {ipr_adj} | {ipr_effect} |")
            
            report_lines.append("")
        
        # Insights
        report_lines.append("## 🔍 Key Insights")
        report_lines.append("")
        
        best_venue = venue_advantages[0]
        worst_venue = venue_advantages[-1]
        
        report_lines.append(f"1. **Strongest Home Advantage**: {best_venue['venue_name']} ({best_venue['home_point_pct']:.1f}% of points)")
        report_lines.append(f"2. **Weakest Home Advantage**: {worst_venue['venue_name']} ({worst_venue['home_point_pct']:.1f}% of points)")
        report_lines.append(f"3. **Point Percentage Range**: {best_venue['home_point_pct'] - worst_venue['home_point_pct']:.1f} percentage point spread")
        
        # IPR analysis insights
        venues_with_good_regression = [v for v in venue_advantages 
                                     if not np.isnan(v['r_squared']) and v['r_squared'] > 0.3]
        
        if venues_with_good_regression:
            avg_ipr_effect = np.mean([v['ipr_effect'] for v in venues_with_good_regression])
            report_lines.append(f"4. **IPR Effect**: Average {avg_ipr_effect:.2f} points per IPR differential across venues with good regression")
        
        # Venue-specific findings
        strong_ipr_adjusted = [v for v in venue_advantages 
                             if not np.isnan(v['ipr_adjusted_advantage']) and v['ipr_adjusted_advantage'] > 2]
        
        if strong_ipr_adjusted:
            report_lines.append(f"5. **Strong IPR-Adjusted Advantages**: {len(strong_ipr_adjusted)} venues show >2 point advantage even after controlling for team strength")
            report_lines.append(f"   - Top: {', '.join([v['venue_name'] for v in strong_ipr_adjusted[:3]])}")
        
        return "\\n".join(report_lines)
    
    def run_analysis(self, data_path: str) -> Tuple[str, str]:
        """Run complete corrected venue home advantage analysis."""
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
        report_path = f"reports/output/corrected_venue_home_advantage_season_{self.season}.md"
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"\\nCorrected venue home advantage analysis complete:")
        print(f"  Report: {report_path}")
        print(f"  Chart: {chart_path}")
        
        return report_path, chart_path


def main():
    """Main execution function."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python venue_home_advantage_corrected.py <season>")
        print("Example: python venue_home_advantage_corrected.py 21")
        sys.exit(1)
    
    season = sys.argv[1]
    
    # Run analysis
    analyzer = CorrectedVenueHomeAdvantageAnalyzer(season)
    data_path = "mnp-data-archive"
    
    try:
        report_path, chart_path = analyzer.run_analysis(data_path)
        if report_path:
            print(f"\\n🏟️ Corrected venue home advantage analysis complete for Season {season}")
        else:
            print("No venue data available for analysis")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()