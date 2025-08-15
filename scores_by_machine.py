#!/usr/bin/env python3
import os
import json
import glob
from collections import defaultdict

# Dictionary to store machine scores
# Format: {machine_name: {team: [(score, player_name), ...]}}
machine_scores = defaultdict(lambda: defaultdict(list))

# Dictionary to store team names
# Format: {team_key: team_name}
team_names = {}

# Target teams for this match
TARGET_TEAMS = ['CDC', 'SKP']  # Contras and Skips

# Load venue information
with open('mnp-data-archive/venues.json', 'r') as f:
    VENUES = json.load(f)

# Load machine names from machines.json
with open('mnp-data-archive/machines.json', 'r') as f:
    MACHINE_NAMES = json.load(f)

def get_venue_machines(venue_key):
    """Get list of machines available at a venue."""
    if venue_key in VENUES:
        return VENUES[venue_key].get('machines', [])
    return []

def get_machine_name(machine_key):
    """Get full machine name from key."""
    return MACHINE_NAMES.get(machine_key, {}).get('name', machine_key)

def get_player_name(player_key, player_map):
    """Get player name from key using player map."""
    if player_key in player_map:
        return player_map[player_key]
    return f"Unknown ({player_key})"

def process_matches(venue_key):
    """Process all season 21 match files for a specific venue."""
    # Get machines available at this venue
    venue_machines = get_venue_machines(venue_key)
    if not venue_machines:
        print(f"No machines found for venue {venue_key}")
        return

    # Process all season 21 match files
    match_files = glob.glob('mnp-data-archive/season-21/matches/mnp-21-*.json')
    for match_file in match_files:
        try:
            with open(match_file, 'r') as f:
                match_data = json.load(f)
            
            # Check if either team is in our target teams
            away_team = match_data.get('away', {}).get('key', '')
            home_team = match_data.get('home', {}).get('key', '')
            
            if away_team not in TARGET_TEAMS and home_team not in TARGET_TEAMS:
                continue
            
            # Store team names if we haven't seen them before
            if away_team in TARGET_TEAMS and away_team not in team_names:
                team_names[away_team] = match_data.get('away', {}).get('name', away_team)
            if home_team in TARGET_TEAMS and home_team not in team_names:
                team_names[home_team] = match_data.get('home', {}).get('name', home_team)
            
            # Create player mapping for this match
            player_map = {}
            
            # Add away team players to map
            for player in match_data.get('away', {}).get('lineup', []):
                player_map[player.get('key')] = player.get('name')
            
            # Add home team players to map
            for player in match_data.get('home', {}).get('lineup', []):
                player_map[player.get('key')] = player.get('name')
            
            # Process all rounds and games
            for round_data in match_data.get('rounds', []):
                for game in round_data.get('games', []):
                    # Skip if no machine defined, game not done, or not a venue machine
                    if 'machine' not in game or not game.get('done', False):
                        continue
                    
                    machine_name = game.get('machine')
                    
                    # Skip if not one of the venue machines
                    if machine_name not in venue_machines:
                        continue
                    
                    # Check and store player 1 score if relevant
                    if 'player_1' in game and 'score_1' in game:
                        player_key = game['player_1']
                        team_key = home_team if player_key in [p.get('key') for p in match_data.get('home', {}).get('lineup', [])] else away_team
                        if team_key in TARGET_TEAMS:
                            player_name = get_player_name(player_key, player_map)
                            machine_scores[machine_name][team_key].append((int(game['score_1']), player_name))
                    
                    # Check and store player 2 score if relevant
                    if 'player_2' in game and 'score_2' in game:
                        player_key = game['player_2']
                        team_key = home_team if player_key in [p.get('key') for p in match_data.get('home', {}).get('lineup', [])] else away_team
                        if team_key in TARGET_TEAMS:
                            player_name = get_player_name(player_key, player_map)
                            machine_scores[machine_name][team_key].append((int(game['score_2']), player_name))
                    
                    # Check and store player 3 score if relevant
                    if 'player_3' in game and 'score_3' in game:
                        player_key = game['player_3']
                        team_key = home_team if player_key in [p.get('key') for p in match_data.get('home', {}).get('lineup', [])] else away_team
                        if team_key in TARGET_TEAMS:
                            player_name = get_player_name(player_key, player_map)
                            machine_scores[machine_name][team_key].append((int(game['score_3']), player_name))
                    
                    # Check and store player 4 score if relevant
                    if 'player_4' in game and 'score_4' in game:
                        player_key = game['player_4']
                        team_key = home_team if player_key in [p.get('key') for p in match_data.get('home', {}).get('lineup', [])] else away_team
                        if team_key in TARGET_TEAMS:
                            player_name = get_player_name(player_key, player_map)
                            machine_scores[machine_name][team_key].append((int(game['score_4']), player_name))
        
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error processing {match_file}: {e}")

def write_scores(venue_key):
    """Write scores to output file."""
    venue_name = VENUES.get(venue_key, {}).get('name', venue_key)
    venue_machines = get_venue_machines(venue_key)
    
    with open('player_scores_by_machine.txt', 'w') as outfile:
        outfile.write(f"Scores for {venue_name} ({venue_key})\n")
        outfile.write("=" * (len(venue_name) + len(venue_key) + 15) + "\n\n")
        
        # For each machine at the venue, sort scores in descending order
        for machine_key in sorted(venue_machines):
            machine_name = get_machine_name(machine_key)
            outfile.write(f"{machine_name}\n")
            outfile.write("----------------------------------------\n")
            
            if machine_key not in machine_scores:
                outfile.write("No scores recorded for this machine\n\n\n")
                continue
            
            # Process each team's scores
            for team_key in TARGET_TEAMS:
                team_name = team_names.get(team_key, team_key)
                scores = machine_scores[machine_key][team_key]
                
                if not scores:
                    continue
                    
                # Sort scores in descending order
                scores.sort(reverse=True)
                
                outfile.write(f"\n{team_name}:\n")
                outfile.write("-" * (len(team_name) + 1) + "\n")
                
                # List scores in descending order
                for idx, (score, player_name) in enumerate(scores):
                    outfile.write(f"Score {idx+1} - {score:,} - {player_name}\n")
            
            outfile.write("\n\n")

def main():
    # Process matches for KRA venue
    venue_key = "KRA"
    process_matches(venue_key)
    write_scores(venue_key)
    print(f"Scores have been written to player_scores_by_machine.txt")

if __name__ == "__main__":
    main() 