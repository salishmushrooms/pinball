#!/usr/bin/env python3
"""Debug script to show all Monster Bash scores at Jupiter for DTP matches."""

import json
import glob

# Find all matches at Jupiter involving DTP
matches_pattern = "mnp-data-archive/season-22/matches/*.json"
mb_scores = []

for match_file in glob.glob(matches_pattern):
    with open(match_file, 'r') as f:
        match_data = json.load(f)

    # Check if at Jupiter
    if match_data.get('venue', {}).get('key') != 'JUP':
        continue

    # Check if DTP is in the match
    home_team = match_data.get('home', {}).get('key')
    away_team = match_data.get('away', {}).get('key')

    if home_team != 'DTP' and away_team != 'DTP':
        continue

    is_dtp_home = (home_team == 'DTP')

    # Process rounds
    for round_data in match_data.get('rounds', []):
        round_num = round_data['n']

        for game in round_data.get('games', []):
            if not game.get('done', False):
                continue

            machine = game.get('machine', '')
            if machine not in ['MB', 'MonsterBash']:
                continue

            # Found a Monster Bash game!
            print(f"\n=== Match: {match_data['key']} ===")
            print(f"Round {round_num}: {machine}")
            print(f"DTP is {'HOME' if is_dtp_home else 'AWAY'}")

            # Show all scores
            for pos in [1, 2, 3, 4]:
                score_key = f'score_{pos}'
                points_key = f'points_{pos}'
                player_key = f'player_{pos}'

                if score_key in game and player_key in game:
                    score = game[score_key]
                    points = game.get(points_key, 0)

                    # Determine if this is DTP based on round and home/away
                    if is_dtp_home:
                        if round_num == 1:
                            is_dtp_player = (pos in [2, 4])
                        elif round_num == 2:
                            is_dtp_player = (pos == 1)
                        elif round_num == 3:
                            is_dtp_player = (pos == 2)
                        elif round_num == 4:
                            is_dtp_player = (pos in [1, 3])
                    else:
                        if round_num == 1:
                            is_dtp_player = (pos in [1, 3])
                        elif round_num == 2:
                            is_dtp_player = (pos == 2)
                        elif round_num == 3:
                            is_dtp_player = (pos == 1)
                        elif round_num == 4:
                            is_dtp_player = (pos in [2, 4])

                    team_label = "DTP" if is_dtp_player else "OPP"
                    print(f"  P{pos} [{team_label}]: {score:,} ({points} pts)")

            print(f"  DTP points: {game.get('home_points' if is_dtp_home else 'away_points', 0)}")
            print(f"  Opp points: {game.get('away_points' if is_dtp_home else 'home_points', 0)}")

print("\n\n=== SUMMARY ===")
print("Check if the median of 3,631,235 seems correct based on the scores above")
