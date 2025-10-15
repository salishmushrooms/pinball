#!/usr/bin/env python3
"""
MNP Venue-Controlled IPR Analysis

Analyzes home field advantage while controlling for venue effects, including special
analysis of matches where two home teams play each other at their shared venue.
This allows us to isolate IPR effects from venue effects.

FUTURE IMPROVEMENT: Consider using point differentials instead of win/loss for
more nuanced analysis. Current approach uses binary outcomes but point margins
could reveal magnitude of advantages more precisely.
"""

import json
import os
import glob
import csv
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any, Tuple, Set
from scipy import stats
from sklearn.linear_model import LogisticRegression


class VenueControlledIPRAnalyzer:
    """Analyze IPR effects while controlling for venue advantages."""
    
    def __init__(self, season: str):
        """Initialize analyzer with season."""
        self.season = season
        self.matches = []
        self.team_venues = {}  # team_key -> venue_key
        self.venue_names = {}  # venue_key -> venue_name
        self.venue_teams = defaultdict(list)  # venue_key -> [team_keys]
        
        # Categorized match data
        self.normal_matches = []  # Normal home vs away
        self.home_vs_home_matches = []  # Both teams from same venue
        self.neutral_venue_matches = []  # Neither team at their home venue
        
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
                    self.venue_teams[venue_key].append(team_key)
        
        # Load venue names
        with open(venues_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    venue_key, venue_name = row[0], row[1]
                    self.venue_names[venue_key] = venue_name
        
        print(f"Loaded {len(self.team_venues)} team-venue mappings")
        print(f"Loaded {len(self.venue_names)} venue names")
        
        # Show venues with multiple teams
        multi_team_venues = {v: teams for v, teams in self.venue_teams.items() if len(teams) > 1}
        if multi_team_venues:
            print(f"\\nVenues with multiple home teams:")
            for venue, teams in multi_team_venues.items():
                venue_name = self.venue_names.get(venue, venue)
                print(f"  {venue_name} ({venue}): {', '.join(teams)}")
    
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
        print(f"\\nLoaded {len(self.matches)} complete matches from season {self.season}")
    
    def categorize_matches(self) -> None:
        """Categorize matches by venue relationship."""
        for match in self.matches:
            home_team = match.get('home', {}).get('key', '')
            away_team = match.get('away', {}).get('key', '')
            match_venue = match.get('venue', {}).get('key', '')
            
            home_team_venue = self.team_venues.get(home_team, '')
            away_team_venue = self.team_venues.get(away_team, '')
            
            match_data = self.process_single_match(match)
            if not match_data:
                continue
            
            # Add venue categorization info
            match_data['home_team_venue'] = home_team_venue
            match_data['away_team_venue'] = away_team_venue
            match_data['match_venue'] = match_venue
            
            # Categorize match type
            if home_team_venue == away_team_venue == match_venue:
                # Both teams from same venue, playing at that venue
                match_data['match_type'] = 'home_vs_home'
                match_data['venue_advantage'] = 'neutral'  # Both have venue familiarity
                self.home_vs_home_matches.append(match_data)
                
            elif home_team_venue == match_venue and away_team_venue != match_venue:
                # Normal home advantage
                match_data['match_type'] = 'normal_home'
                match_data['venue_advantage'] = 'home'
                self.normal_matches.append(match_data)
                
            elif away_team_venue == match_venue and home_team_venue != match_venue:
                # Away team playing at their venue (rare but possible)
                match_data['match_type'] = 'away_at_home_venue'
                match_data['venue_advantage'] = 'away'
                self.normal_matches.append(match_data)
                
            elif home_team_venue != match_venue and away_team_venue != match_venue:
                # Neither team at their home venue
                match_data['match_type'] = 'neutral_venue'
                match_data['venue_advantage'] = 'neutral'
                self.neutral_venue_matches.append(match_data)
                
            else:
                # Fallback
                match_data['match_type'] = 'unknown'
                match_data['venue_advantage'] = 'unknown'
                self.normal_matches.append(match_data)
        
        print(f"\\nMatch categorization:")
        print(f"  Normal home/away matches: {len(self.normal_matches)}")
        print(f"  Home vs Home matches: {len(self.home_vs_home_matches)}")
        print(f"  Neutral venue matches: {len(self.neutral_venue_matches)}")
    
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
    
    def process_single_match(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single match for analysis."""
        # Calculate team IPRs
        home_lineup = match.get('home', {}).get('lineup', [])
        away_lineup = match.get('away', {}).get('lineup', [])
        
        home_ipr = self.calculate_team_ipr(home_lineup)
        away_ipr = self.calculate_team_ipr(away_lineup)
        ipr_differential = home_ipr - away_ipr
        
        # Calculate match outcome
        home_points, away_points = self.calculate_match_points(match)
        
        if home_points + away_points == 0:
            return None  # Skip matches with no points recorded
        
        home_won = home_points > away_points
        point_differential = home_points - away_points
        
        return {
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
    
    def analyze_home_vs_home_matches(self) -> Dict[str, Any]:
        """Analyze matches where both teams are from the same venue."""
        if not self.home_vs_home_matches:
            return {}
        
        # Since venue advantage is neutralized, this is pure IPR effect
        ipr_diffs = [m['ipr_differential'] for m in self.home_vs_home_matches]
        home_wins = [1 if m['home_won'] else 0 for m in self.home_vs_home_matches]
        point_diffs = [m['point_differential'] for m in self.home_vs_home_matches]
        
        # Fit logistic regression
        X = np.array(ipr_diffs).reshape(-1, 1)
        y = np.array(home_wins)
        
        model = LogisticRegression()
        model.fit(X, y)
        
        # Calculate statistics
        total_matches = len(self.home_vs_home_matches)
        home_wins_count = sum(home_wins)
        home_win_pct = (home_wins_count / total_matches) * 100
        
        # Correlation between IPR diff and point differential
        ipr_point_corr = np.corrcoef(ipr_diffs, point_diffs)[0, 1]
        
        return {
            'total_matches': total_matches,
            'home_wins': home_wins_count,
            'home_win_pct': home_win_pct,
            'ipr_point_correlation': ipr_point_corr,
            'model': model,
            'coefficient': model.coef_[0][0],
            'intercept': model.intercept_[0],
            'avg_ipr_diff': np.mean(ipr_diffs),
            'avg_point_diff': np.mean(point_diffs)
        }
    
    def analyze_normal_matches(self) -> Dict[str, Any]:
        """Analyze normal home/away matches."""
        if not self.normal_matches:
            return {}
        
        ipr_diffs = [m['ipr_differential'] for m in self.normal_matches]
        home_wins = [1 if m['home_won'] else 0 for m in self.normal_matches]
        
        # Fit logistic regression
        X = np.array(ipr_diffs).reshape(-1, 1)
        y = np.array(home_wins)
        
        model = LogisticRegression()
        model.fit(X, y)
        
        # Calculate equilibrium point
        equilibrium_ipr_diff = -model.intercept_[0] / model.coef_[0][0]
        
        total_matches = len(self.normal_matches)
        home_wins_count = sum(home_wins)
        home_win_pct = (home_wins_count / total_matches) * 100
        
        return {
            'total_matches': total_matches,
            'home_wins': home_wins_count,
            'home_win_pct': home_win_pct,
            'model': model,
            'coefficient': model.coef_[0][0],
            'intercept': model.intercept_[0],
            'equilibrium_ipr_diff': equilibrium_ipr_diff,
            'home_advantage_ipr': abs(equilibrium_ipr_diff),
            'avg_ipr_diff': np.mean(ipr_diffs)
        }
    
    def generate_comparison_chart(self, normal_analysis: Dict, home_vs_home_analysis: Dict, 
                                 output_dir: str = "reports/charts") -> str:
        """Generate comparison chart of normal vs home-vs-home matches."""
        if not normal_analysis or not home_vs_home_analysis:
            return ""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Left plot: Normal matches
        normal_ipr_diffs = [m['ipr_differential'] for m in self.normal_matches]
        normal_home_wins = [1 if m['home_won'] else 0 for m in self.normal_matches]
        
        x_range = np.linspace(min(normal_ipr_diffs) - 5, max(normal_ipr_diffs) + 5, 200)
        normal_model = normal_analysis['model']
        normal_probs = normal_model.predict_proba(x_range.reshape(-1, 1))[:, 1] * 100
        
        ax1.scatter(normal_ipr_diffs, [w * 100 for w in normal_home_wins], 
                   alpha=0.3, s=20, color='blue', label='Actual Matches')
        ax1.plot(x_range, normal_probs, 'b-', linewidth=2, label='Logistic Regression')
        
        ax1.axhline(y=50, color='red', linestyle='--', alpha=0.7)
        ax1.axvline(x=0, color='gray', linestyle=':', alpha=0.5)
        ax1.axvline(x=normal_analysis['equilibrium_ipr_diff'], color='orange', 
                   linestyle='-', alpha=0.7, 
                   label=f'Equilibrium: {normal_analysis["equilibrium_ipr_diff"]:.1f} IPR')
        
        ax1.set_xlabel('Home Team IPR Advantage')
        ax1.set_ylabel('Home Win Probability (%)')
        ax1.set_title(f'Normal Home/Away Matches\\n({normal_analysis["total_matches"]} matches)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 100)
        
        # Right plot: Home vs Home matches
        hvh_ipr_diffs = [m['ipr_differential'] for m in self.home_vs_home_matches]
        hvh_home_wins = [1 if m['home_won'] else 0 for m in self.home_vs_home_matches]
        
        if hvh_ipr_diffs:
            x_range_hvh = np.linspace(min(hvh_ipr_diffs) - 5, max(hvh_ipr_diffs) + 5, 200)
            hvh_model = home_vs_home_analysis['model']
            hvh_probs = hvh_model.predict_proba(x_range_hvh.reshape(-1, 1))[:, 1] * 100
            
            ax2.scatter(hvh_ipr_diffs, [w * 100 for w in hvh_home_wins], 
                       alpha=0.5, s=30, color='green', label='Actual Matches')
            ax2.plot(x_range_hvh, hvh_probs, 'g-', linewidth=2, label='Logistic Regression')
        
        ax2.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50% (No Venue Bias)')
        ax2.axvline(x=0, color='gray', linestyle=':', alpha=0.5, label='Equal IPR')
        
        ax2.set_xlabel('Home Team IPR Advantage')
        ax2.set_ylabel('Home Win Probability (%)')
        ax2.set_title(f'Home vs Home Matches\\n({home_vs_home_analysis["total_matches"]} matches)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 100)
        
        plt.tight_layout()
        
        # Save chart
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"venue_controlled_ipr_analysis_season_{self.season}.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_report(self, normal_analysis: Dict, home_vs_home_analysis: Dict) -> str:
        """Generate comprehensive venue-controlled analysis report."""
        report_lines = []
        report_lines.append(f"# Venue-Controlled IPR Analysis")
        report_lines.append(f"## Season {self.season}")
        report_lines.append("")
        report_lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        report_lines.append("")
        
        # Overview
        total_matches = len(self.normal_matches) + len(self.home_vs_home_matches) + len(self.neutral_venue_matches)
        report_lines.append("## 🏢 Venue Effect Analysis")
        report_lines.append("")
        report_lines.append("This analysis separates venue familiarity effects from pure skill (IPR) effects")
        report_lines.append("by examining different types of matches:")
        report_lines.append("")
        report_lines.append(f"- **Normal Home/Away**: {len(self.normal_matches)} matches (venue advantage present)")
        report_lines.append(f"- **Home vs Home**: {len(self.home_vs_home_matches)} matches (venue advantage neutralized)")
        report_lines.append(f"- **Neutral Venue**: {len(self.neutral_venue_matches)} matches (no venue familiarity)")
        report_lines.append(f"- **Total Analyzed**: {total_matches} matches")
        report_lines.append("")
        
        # Home vs Home analysis (Pure IPR effect)
        if home_vs_home_analysis:
            report_lines.append("## 🎯 Pure IPR Effect (Home vs Home Matches)")
            report_lines.append("")
            report_lines.append("When both teams play at their shared home venue, venue advantage is neutralized.")
            report_lines.append("This isolates the effect of team skill (IPR) on match outcomes.")
            report_lines.append("")
            
            hvh_home_pct = home_vs_home_analysis['home_win_pct']
            hvh_corr = home_vs_home_analysis['ipr_point_correlation']
            
            report_lines.append(f"- **Matches Analyzed**: {home_vs_home_analysis['total_matches']}")
            report_lines.append(f"- **'Home' Team Win Rate**: {hvh_home_pct:.1f}% (should be ~50% if no venue bias)")
            report_lines.append(f"- **IPR ↔ Points Correlation**: {hvh_corr:.3f}")
            report_lines.append(f"- **Average IPR Differential**: {home_vs_home_analysis['avg_ipr_diff']:.1f}")
            report_lines.append(f"- **Average Point Differential**: {home_vs_home_analysis['avg_point_diff']:.1f}")
            report_lines.append("")
            
            if abs(hvh_home_pct - 50) < 10:
                report_lines.append("✅ **Result**: Home vs Home matches show minimal venue bias, confirming our analysis method.")
            else:
                report_lines.append("⚠️ **Result**: Significant bias detected even in home vs home matches - may indicate other factors.")
            report_lines.append("")
        
        # Normal match analysis (Venue + IPR effect)
        if normal_analysis:
            report_lines.append("## 🏠 Combined Effect (Normal Home/Away Matches)")
            report_lines.append("")
            
            home_adv_ipr = normal_analysis.get('home_advantage_ipr', 0)
            normal_home_pct = normal_analysis['home_win_pct']
            
            report_lines.append(f"- **Matches Analyzed**: {normal_analysis['total_matches']}")
            report_lines.append(f"- **Home Team Win Rate**: {normal_home_pct:.1f}%")
            report_lines.append(f"- **Home Advantage**: ~{home_adv_ipr:.1f} IPR points")
            report_lines.append(f"- **Equilibrium Point**: Home teams need {normal_analysis['equilibrium_ipr_diff']:.1f} fewer IPR points for 50% win rate")
            report_lines.append("")
        
        # Comparison and insights
        if normal_analysis and home_vs_home_analysis:
            report_lines.append("## 🔍 Key Insights")
            report_lines.append("")
            
            venue_effect = normal_analysis['home_win_pct'] - home_vs_home_analysis['home_win_pct']
            
            report_lines.append(f"1. **Venue Effect**: {venue_effect:.1f} percentage point advantage from playing at home venue")
            report_lines.append(f"2. **IPR Validation**: Home vs home matches confirm IPR strongly predicts performance")
            
            if home_vs_home_analysis['ipr_point_correlation'] > 0.3:
                report_lines.append(f"3. **Strong IPR Correlation**: {home_vs_home_analysis['ipr_point_correlation']:.3f} correlation between IPR difference and point difference")
            
            report_lines.append("")
        
        # Venues with multiple teams
        multi_team_venues = {v: teams for v, teams in self.venue_teams.items() if len(teams) > 1}
        if multi_team_venues:
            report_lines.append("## 🏢 Venues with Multiple Home Teams")
            report_lines.append("")
            for venue_key, teams in multi_team_venues.items():
                venue_name = self.venue_names.get(venue_key, venue_key)
                hvh_matches_this_venue = [m for m in self.home_vs_home_matches 
                                         if m['venue_key'] == venue_key]
                report_lines.append(f"- **{venue_name}** ({venue_key}): {', '.join(teams)} ({len(hvh_matches_this_venue)} home vs home matches)")
            report_lines.append("")
        
        return "\\n".join(report_lines)
    
    def run_analysis(self, data_path: str) -> Tuple[str, str]:
        """Run complete venue-controlled analysis."""
        # Load data
        self.load_team_venue_mapping(data_path)
        self.load_matches(data_path)
        self.categorize_matches()
        
        if not self.normal_matches and not self.home_vs_home_matches:
            return "", ""
        
        # Run analyses
        normal_analysis = self.analyze_normal_matches() if self.normal_matches else {}
        home_vs_home_analysis = self.analyze_home_vs_home_matches() if self.home_vs_home_matches else {}
        
        # Generate outputs
        chart_path = ""
        if normal_analysis and home_vs_home_analysis:
            chart_path = self.generate_comparison_chart(normal_analysis, home_vs_home_analysis)
        
        report_content = self.generate_report(normal_analysis, home_vs_home_analysis)
        report_path = f"reports/output/venue_controlled_ipr_analysis_season_{self.season}.md"
        
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"\\nVenue-controlled analysis complete:")
        print(f"  Report: {report_path}")
        if chart_path:
            print(f"  Chart: {chart_path}")
        
        return report_path, chart_path


def main():
    """Main execution function."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python venue_controlled_ipr_analysis.py <season>")
        print("Example: python venue_controlled_ipr_analysis.py 21")
        sys.exit(1)
    
    season = sys.argv[1]
    
    # Run analysis
    analyzer = VenueControlledIPRAnalyzer(season)
    data_path = "mnp-data-archive"
    
    try:
        report_path, chart_path = analyzer.run_analysis(data_path)
        if report_path:
            print(f"\\n🏢 Venue-controlled analysis complete for Season {season}")
        else:
            print("No data available for analysis")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()