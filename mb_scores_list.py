#!/usr/bin/env python3
"""List all Monster Bash scores at Jupiter for DTP matches, sorted."""

import json
import glob
import statistics

# Find all matches at Jupiter involving DTP
matches_pattern = "mnp-data-archive/season-22/matches/*.json"
all_scores = []

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

    # Process rounds
    for round_data in match_data.get('rounds', []):
        round_num = round_data['n']

        for game in round_data.get('games', []):
            if not game.get('done', False):
                continue

            machine = game.get('machine', '')
            if machine not in ['MB', 'MonsterBash']:
                continue

            # Collect all scores
            for pos in [1, 2, 3, 4]:
                score_key = f'score_{pos}'
                if score_key in game:
                    all_scores.append(game[score_key])

# Sort and display
all_scores.sort()

print("=== ALL MONSTER BASH SCORES AT JUPITER (DTP MATCHES) ===")
print(f"Total scores: {len(all_scores)}")
print("\nScores (sorted):")
for i, score in enumerate(all_scores, 1):
    print(f"{i:2d}. {score:,}")

if all_scores:
    print(f"\nMedian: {statistics.median(all_scores):,}")
    print(f"Average: {statistics.mean(all_scores):,.0f}")
    print(f"Min: {min(all_scores):,}")
    print(f"Max: {max(all_scores):,}")

    # Show percentiles
    if len(all_scores) >= 4:
        q1, q2, q3 = statistics.quantiles(all_scores, n=4)
        print(f"\n25th percentile: {q1:,}")
        print(f"50th percentile: {q2:,}")
        print(f"75th percentile: {q3:,}")
