#!/usr/bin/env python3
import os
import json
import glob
from collections import defaultdict
import statistics
from typing import List, Tuple, Dict

# Load venue information
with open('mnp-data-archive/venues.json', 'r') as f:
    VENUES = json.load(f)

# Load machine names from machines.json
with open('mnp-data-archive/machines.json', 'r') as f:
    MACHINE_NAMES = json.load(f)

def get_machine_name(machine_key: str) -> str:
    """Get full machine name from key."""
    return MACHINE_NAMES.get(machine_key, {}).get('name', machine_key)

def calculate_percentile(scores: List[int], percentile: float) -> int:
    """Calculate a specific percentile from a list of scores."""
    if not scores:
        return 0
    scores.sort()
    index = (len(scores) - 1) * percentile
    lower = int(index)
    upper = lower + 1
    if upper >= len(scores):
        return scores[lower]
    return int(scores[lower] + (index - lower) * (scores[upper] - scores[lower]))

def process_matches(venue_key: str) -> Tuple[Dict[str, List[int]], Dict[str, Dict[int, int]]]:
    """Process all season 21 match files for a specific venue.
    Returns:
        Tuple containing:
        - Dictionary of machine scores: {machine: [scores]}
        - Dictionary of round-based machine usage: {machine: {round: count}}
    """
    # Dictionary to store all scores for each machine
    machine_scores = defaultdict(list)
    
    # Dictionary to store round-based machine usage
    round_usage = defaultdict(lambda: defaultdict(int))
    
    # Get machines available at this venue
    venue_machines = VENUES.get(venue_key, {}).get('machines', [])
    if not venue_machines:
        print(f"No machines found for venue {venue_key}")
        return machine_scores, round_usage

    # Process all season 21 match files
    match_files = glob.glob('mnp-data-archive/season-21/matches/mnp-21-*.json')
    for match_file in match_files:
        try:
            with open(match_file, 'r') as f:
                match_data = json.load(f)
            
            # Process all rounds and games
            for round_data in match_data.get('rounds', []):
                round_num = round_data.get('n', 0)
                
                for game in round_data.get('games', []):
                    # Skip if no machine defined or game not done
                    if 'machine' not in game or not game.get('done', False):
                        continue
                    
                    machine_name = game.get('machine')
                    
                    # Skip if not one of the venue machines
                    if machine_name not in venue_machines:
                        continue
                    
                    # Count machine usage in this round
                    # For rounds 1 and 4 (doubles), count as 1 usage
                    # For rounds 2 and 3 (singles), count as 2 usages
                    if round_num in [1, 4]:
                        round_usage[machine_name][round_num] += 1
                    else:
                        round_usage[machine_name][round_num] += 2
                    
                    # Store all scores for this machine
                    for i in range(1, 5):
                        if f'player_{i}' in game and f'score_{i}' in game:
                            machine_scores[machine_name].append(int(game[f'score_{i}']))
        
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error processing {match_file}: {e}")
    
    return machine_scores, round_usage

def write_venue_stats(venue_key: str, machine_scores: Dict[str, List[int]], round_usage: Dict[str, Dict[int, int]]):
    """Write venue statistics to output file."""
    venue_name = VENUES.get(venue_key, {}).get('name', venue_key)
    venue_machines = VENUES.get(venue_key, {}).get('machines', [])
    
    with open('venue_stats.txt', 'w') as outfile:
        outfile.write(f"Statistics for {venue_name} ({venue_key})\n")
        outfile.write("=" * (len(venue_name) + len(venue_key) + 15) + "\n\n")
        
        # Write summary statistics for each machine
        outfile.write("Summary Statistics\n")
        outfile.write("-----------------\n\n")
        
        for machine_key in sorted(venue_machines):
            machine_name = get_machine_name(machine_key)
            scores = machine_scores[machine_key]
            
            if not scores:
                continue
                
            # Calculate statistics
            count = len(scores)
            median = statistics.median(scores)
            p75 = calculate_percentile(scores, 0.75)
            p90 = calculate_percentile(scores, 0.90)
            
            outfile.write(f"{machine_name}:\n")
            outfile.write(f"  Count: {count}\n")
            outfile.write(f"  Median: {median:,}\n")
            outfile.write(f"  75th percentile: {p75:,}\n")
            outfile.write(f"  90th percentile: {p90:,}\n\n")
        
        # Write detailed scores for each machine
        outfile.write("\nDetailed Scores\n")
        outfile.write("----------------\n\n")
        
        for machine_key in sorted(venue_machines):
            machine_name = get_machine_name(machine_key)
            scores = machine_scores[machine_key]
            
            if not scores:
                continue
                
            outfile.write(f"{machine_name}\n")
            outfile.write("-" * len(machine_name) + "\n")
            
            # Sort scores in descending order
            scores.sort(reverse=True)
            
            # List scores in descending order
            for idx, score in enumerate(scores):
                outfile.write(f"Score {idx+1} - {score:,}\n")
            
            outfile.write("\n")
        
        # Write round-based machine usage for Bad Cats
        outfile.write("\nBad Cats Machine Usage by Round\n")
        outfile.write("--------------------------------\n\n")
        
        for machine_key in sorted(venue_machines):
            machine_name = get_machine_name(machine_key)
            usage = round_usage[machine_key]
            
            if not usage:
                continue
                
            outfile.write(f"{machine_name}\n")
            for round_num in range(1, 5):
                count = usage.get(round_num, 0)
                outfile.write(f"Round {round_num} - {count}\n")
            outfile.write("\n")

def main():
    # Process matches for AAB venue
    venue_key = "AAB"
    machine_scores, round_usage = process_matches(venue_key)
    write_venue_stats(venue_key, machine_scores, round_usage)
    print(f"Statistics have been written to venue_stats.txt")

if __name__ == "__main__":
    main() 