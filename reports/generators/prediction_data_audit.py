#!/usr/bin/env python3
"""
Audit data availability for machine pick prediction system.
Analyzes historical patterns needed for Phase 1 predictions.
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

class PredictionDataAuditor:
    def __init__(self, seasons: List[str]):
        self.seasons = seasons
        self.base_path = Path(__file__).parent.parent.parent / "mnp-data-archive"

        # Data structures
        self.team_picks = defaultdict(lambda: {
            'home_r2': Counter(),  # Home picks round 2
            'home_r4': Counter(),  # Home picks round 4
            'away_r1': Counter(),  # Away picks round 1
            'away_r3': Counter(),  # Away picks round 3
        })
        self.venue_machines = defaultdict(set)
        self.player_round_participation = defaultdict(lambda: defaultdict(int))
        self.player_machine_games = defaultdict(lambda: defaultdict(int))

        # Load reference data
        self.load_venues()
        self.load_matches()

    def load_venues(self):
        """Load venue data to get home venues for teams."""
        venues_path = self.base_path / "venues.json"
        with open(venues_path, 'r') as f:
            self.venues = json.load(f)

        # Build team -> home venue mapping
        self.team_home_venue = {}
        for venue in self.venues.values():
            if 'home_team' in venue:
                self.team_home_venue[venue['home_team']] = venue['key']

    def load_matches(self):
        """Load all match data for specified seasons."""
        self.matches_processed = 0

        for season in self.seasons:
            season_path = self.base_path / f"season-{season}" / "matches"

            if not season_path.exists():
                print(f"Warning: Season {season} path not found: {season_path}")
                continue

            for match_file in season_path.glob("mnp-*.json"):
                self.process_match(match_file, season)

    def process_match(self, match_path: Path, season: str):
        """Process a single match file."""
        with open(match_path, 'r') as f:
            match_data = json.load(f)

        away_team = match_data['away']['key']
        home_team = match_data['home']['key']
        venue_key = match_data['venue']['key']

        # Track machines available at this venue
        for machine_key in match_data['venue'].get('machines', []):
            self.venue_machines[venue_key].add(machine_key)

        # Process rounds
        for round_data in match_data['rounds']:
            round_num = round_data['n']

            # Process each game in the round
            for game in round_data['games']:
                machine_key = game['machine']
                self.venue_machines[venue_key].add(machine_key)

                # Determine who picked this machine (only track once per round, not per game)
                # Home team picks R2 and R4, Away team picks R1 and R3
                if round_num == 1:
                    self.team_picks[away_team]['away_r1'][machine_key] += 1
                elif round_num == 2:
                    self.team_picks[home_team]['home_r2'][machine_key] += 1
                elif round_num == 3:
                    self.team_picks[away_team]['away_r3'][machine_key] += 1
                elif round_num == 4:
                    self.team_picks[home_team]['home_r4'][machine_key] += 1

                # Track player participation
                # Games have player_1, player_2, player_3, player_4 keys
                for pos in [1, 2, 3, 4]:
                    player_key_field = f'player_{pos}'
                    if player_key_field in game:
                        player_key = game[player_key_field]

                        # Find player name from lineup
                        player_name = None
                        team = None
                        for team_side in ['away', 'home']:
                            for player in match_data[team_side]['lineup']:
                                if player['key'] == player_key:
                                    player_name = player['name']
                                    team = match_data[team_side]['key']
                                    break
                            if player_name:
                                break

                        if player_name and team:
                            # Track round participation (home vs away context)
                            context = "home" if team == home_team else "away"
                            key = f"{player_key}|{player_name}|{team}"
                            self.player_round_participation[key][f"{context}_r{round_num}"] += 1

                            # Track player-machine combinations
                            self.player_machine_games[key][machine_key] += 1

        self.matches_processed += 1

    def print_report(self):
        """Generate and print the audit report."""
        print("=" * 80)
        print("PREDICTION DATA AUDIT REPORT")
        print("=" * 80)
        print(f"\nSeasons analyzed: {', '.join(self.seasons)}")
        print(f"Matches processed: {self.matches_processed}")
        print(f"Teams found: {len(self.team_picks)}")
        print(f"Unique players: {len(self.player_round_participation)}")
        print(f"Venues with machines tracked: {len(self.venue_machines)}")

        print("\n" + "=" * 80)
        print("PHASE 1: MACHINE PICK PREDICTION DATA")
        print("=" * 80)

        # Sample teams for detailed analysis
        sample_teams = list(self.team_picks.keys())[:5]

        for team in sample_teams:
            picks = self.team_picks[team]
            print(f"\n{team} - Machine Pick History:")
            print(f"  Home Round 2 picks: {sum(picks['home_r2'].values())} games")
            if picks['home_r2']:
                top_3 = picks['home_r2'].most_common(3)
                for machine, count in top_3:
                    pct = (count / sum(picks['home_r2'].values())) * 100
                    print(f"    {machine}: {count} times ({pct:.1f}%)")

            print(f"  Home Round 4 picks: {sum(picks['home_r4'].values())} games")
            if picks['home_r4']:
                top_3 = picks['home_r4'].most_common(3)
                for machine, count in top_3:
                    pct = (count / sum(picks['home_r4'].values())) * 100
                    print(f"    {machine}: {count} times ({pct:.1f}%)")

            print(f"  Away Round 1 picks: {sum(picks['away_r1'].values())} games")
            if picks['away_r1']:
                top_3 = picks['away_r1'].most_common(3)
                for machine, count in top_3:
                    pct = (count / sum(picks['away_r1'].values())) * 100
                    print(f"    {machine}: {count} times ({pct:.1f}%)")

            print(f"  Away Round 3 picks: {sum(picks['away_r3'].values())} games")
            if picks['away_r3']:
                top_3 = picks['away_r3'].most_common(3)
                for machine, count in top_3:
                    pct = (count / sum(picks['away_r3'].values())) * 100
                    print(f"    {machine}: {count} times ({pct:.1f}%)")

        print("\n" + "=" * 80)
        print("VENUE MACHINE AVAILABILITY")
        print("=" * 80)

        # Show sample venues
        sample_venues = list(self.venue_machines.keys())[:5]
        for venue in sample_venues:
            machines = self.venue_machines[venue]
            print(f"\n{venue}: {len(machines)} machines")
            print(f"  Machines: {', '.join(sorted(machines)[:10])}" +
                  (f" ... (+{len(machines)-10} more)" if len(machines) > 10 else ""))

        print("\n" + "=" * 80)
        print("DATA QUALITY ASSESSMENT")
        print("=" * 80)

        # Calculate sample size statistics
        all_pick_counts = []
        for team, picks in self.team_picks.items():
            for context in ['home_r2', 'home_r4', 'away_r1', 'away_r3']:
                total = sum(picks[context].values())
                if total > 0:
                    all_pick_counts.append(total)

        if all_pick_counts:
            print(f"\nMachine pick sample sizes:")
            print(f"  Average picks per team/context: {sum(all_pick_counts)/len(all_pick_counts):.1f}")
            print(f"  Min picks: {min(all_pick_counts)}")
            print(f"  Max picks: {max(all_pick_counts)}")

            # Confidence assessment
            good_samples = sum(1 for x in all_pick_counts if x >= 10)
            print(f"\n  Contexts with ≥10 picks (good confidence): {good_samples}/{len(all_pick_counts)}")
            print(f"  Contexts with <10 picks (low confidence): {len(all_pick_counts) - good_samples}/{len(all_pick_counts)}")

        print("\n" + "=" * 80)
        print("FUTURE PHASES: PLAYER DATA PREVIEW")
        print("=" * 80)

        # Sample player participation patterns
        sample_players = list(self.player_round_participation.keys())[:3]
        for player_key in sample_players:
            participation = self.player_round_participation[player_key]
            _, name, team = player_key.split('|')
            print(f"\n{name} ({team}):")

            total_games = sum(participation.values())
            print(f"  Total games: {total_games}")

            for context in ['home', 'away']:
                for round_num in [1, 2, 3, 4]:
                    key = f"{context}_r{round_num}"
                    count = participation.get(key, 0)
                    if count > 0:
                        pct = (count / total_games) * 100
                        print(f"    {key}: {count} ({pct:.1f}%)")

            # Show machine affinity
            machines = self.player_machine_games[player_key]
            print(f"  Machines played: {len(machines)}")
            top_machines = Counter(machines).most_common(3)
            for machine, count in top_machines:
                print(f"    {machine}: {count} games")

        print("\n" + "=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)

        avg_picks = sum(all_pick_counts)/len(all_pick_counts) if all_pick_counts else 0

        if avg_picks >= 10:
            print("\n✅ GOOD: Sufficient data for Phase 1 machine prediction")
            print("   - Average sample size is adequate for confident predictions")
            print("   - Can proceed with implementation")
        elif avg_picks >= 5:
            print("\n⚠️  FAIR: Moderate data for Phase 1 machine prediction")
            print("   - Sample sizes are workable but predictions will have wider confidence intervals")
            print("   - Recommend showing top 3-5 picks with percentage likelihoods")
        else:
            print("\n❌ LIMITED: Small sample sizes for predictions")
            print("   - May need to combine contexts or show simpler statistics")
            print("   - Consider 'most played machines' rather than 'predicted picks'")

        print("\nNext steps:")
        print("  1. Review sample teams above to validate pick patterns make sense")
        print("  2. Verify venue machine lists are current")
        print("  3. Design API endpoint for machine prediction")
        print("  4. Create frontend component to display predictions")


def main():
    # Audit seasons 21 and 22
    auditor = PredictionDataAuditor(seasons=["21", "22"])
    auditor.print_report()


if __name__ == "__main__":
    main()
