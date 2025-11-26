#!/usr/bin/env python3
"""Analyze Monster Bash scores by venue across all matches in Season 22."""

import json
import glob
import statistics
from collections import defaultdict

# Find all matches in season 22
matches_pattern = "mnp-data-archive/season-22/matches/*.json"
venue_scores = defaultdict(list)

for match_file in glob.glob(matches_pattern):
    with open(match_file, 'r') as f:
        match_data = json.load(f)

    venue_key = match_data.get('venue', {}).get('key')
    venue_name = match_data.get('venue', {}).get('name')

    if not venue_key:
        continue

    # Process rounds
    for round_data in match_data.get('rounds', []):
        for game in round_data.get('games', []):
            if not game.get('done', False):
                continue

            machine = game.get('machine', '')
            if machine not in ['MB', 'MonsterBash']:
                continue

            # Collect all scores from this Monster Bash game
            for pos in [1, 2, 3, 4]:
                score_key = f'score_{pos}'
                if score_key in game:
                    venue_scores[venue_key].append({
                        'venue_name': venue_name,
                        'score': game[score_key]
                    })

# Sort venues by number of games played (descending)
venue_stats = []
for venue_key, score_data in venue_scores.items():
    scores = [d['score'] for d in score_data]
    venue_name = score_data[0]['venue_name'] if score_data else venue_key

    venue_stats.append({
        'venue_key': venue_key,
        'venue_name': venue_name,
        'count': len(scores),
        'median': statistics.median(scores) if scores else 0,
        'mean': statistics.mean(scores) if scores else 0,
        'min': min(scores) if scores else 0,
        'max': max(scores) if scores else 0,
        'scores': sorted(scores)
    })

# Sort by count (most played venues first)
venue_stats.sort(key=lambda x: x['count'], reverse=True)

print("=" * 80)
print("MONSTER BASH SCORES BY VENUE - SEASON 22")
print("=" * 80)
print()

for venue in venue_stats:
    print(f"### {venue['venue_name']} ({venue['venue_key']})")
    print(f"Games: {venue['count']}")
    print(f"Median: {venue['median']:,.0f}")
    print(f"Average: {venue['mean']:,.0f}")
    print(f"Range: {venue['min']:,.0f} - {venue['max']:,.0f}")

    # Show all scores if there are 20 or fewer
    if venue['count'] <= 20:
        print("All scores:", ", ".join([f"{s:,}" for s in venue['scores']]))
    else:
        # Show first 10 and last 10
        print("First 10:", ", ".join([f"{s:,}" for s in venue['scores'][:10]]))
        print("Last 10:", ", ".join([f"{s:,}" for s in venue['scores'][-10:]]))

    print()
    print("-" * 80)
    print()

# Summary table
print("\n" + "=" * 80)
print("SUMMARY TABLE")
print("=" * 80)
print()
print(f"{'Venue':<25} {'Code':<6} {'Games':>6} {'Median':>15} {'Average':>15}")
print("-" * 80)

for venue in venue_stats:
    print(f"{venue['venue_name']:<25} {venue['venue_key']:<6} {venue['count']:>6} {venue['median']:>15,.0f} {venue['mean']:>15,.0f}")

print()
print(f"Total venues with Monster Bash: {len(venue_stats)}")
print(f"Total Monster Bash games: {sum(v['count'] for v in venue_stats)}")
