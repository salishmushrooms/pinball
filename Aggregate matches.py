import os
import json
import csv
from datetime import datetime
import glob

# Load the machine_variations.json file
with open('machine_variations.json') as f:
    machine_variations = json.load(f)

# Create a dictionary that maps each machine key to its name
machine_key_to_name = {key: machine['name'] for key, machine in machine_variations.items()}

# Specify the paths to the directories
paths = [
    'mnp-data-archive/season-16/matches/*.json',
    'mnp-data-archive/season-17/matches/*.json',
    'mnp-data-archive/season-18/matches/*.json',
    'mnp-data-archive/season-19/matches/*.json',
    'mnp-data-archive/season-20/matches/*.json',
    'mnp-data-archive/season-21/matches/*.json'
]

# Use glob to get all the matching files
matching_files = []
for path in paths:
    matching_files.extend(glob.glob(path))

# Check if any files were found
if not matching_files:
    print("No matching files found.")
    sys.exit()

# Initialize the list to hold the data
data = []

# Define machine key replacements
machine_key_replacements = {
    'Monster Bash': 'MB',
    'Godzilla (Stern)': 'Godzilla',
    'Pulp fiction': 'Pulp Fiction',
    'Banzai Run': 'BanzaiRun',
    'Cactus Canyon Remake': 'CactusCanyon',
    'Venom Right': 'Venom',
    'Venom Left': 'Venom',
    'Venom (R)': 'Venom'
}

# Define venue name replacements
venue_name_replacements = {
    '4Bs': '4Bs Tavern'
}

# Load each JSON file
for file in matching_files:
    print(f"Processing file: {file}")  # Print the name of the file being processed
    try:
        with open(file) as f:
            json_data = json.load(f)

        # Check if the 'state' field is 'complete' in the JSON data
        if json_data.get('state', '') != 'complete':
            print(f"Skipping file (state not complete): {file}")
            continue

        # Extract the season number from the 'key' field in the JSON data
        season_number = json_data['key'].split('-')[1] if '-' in json_data['key'] else None

        # Create a mapping of player keys to names, home/away status, team name, and IPR
        player_key_to_info = {}
        for team in ['home', 'away']:
            if team in json_data and 'lineup' in json_data[team]:
                for player in json_data[team]['lineup']:
                    player_key_to_info[player['key']] = {
                        'name': player['name'],
                        'team': team,
                        'team_name': json_data[team]['name'],
                        'IPR': player.get('IPR')
                    }

        # Determine how rounds and games are stored
        if 'rounds' in json_data:
            # Original structure (seasons 16-19)
            rounds = json_data['rounds']
        elif 'games' in json_data:
            # New structure (season 20)
            rounds = [{'n': json_data.get('round', 1), 'games': json_data['games']}]
        else:
            print(f"No rounds or games data found in file {file}")
            continue

        # Extract the relevant data
        for round_info in rounds:
            for game in round_info['games']:
                for player_number in range(1, 5):
                    player_key_field = f'player_{player_number}'
                    score_field = f'score_{player_number}'

                    if player_key_field in game and score_field in game:
                        player_key = game[player_key_field]
                        player_info = player_key_to_info.get(player_key, {})
                        player_score = game[score_field]

                        # Check if the score is above 1000 to avoid outliers
                        if player_score >= 1000:
                            machine_key = game['machine']

                            # Special handling for 'Jurassic' at certain venues
                            if machine_key == 'Jurassic' and json_data['venue']['name'] in ['Another Castle', 'Ice Box']:
                                machine_key = 'SternPark'

                            # Replace the machine key using the replacements dictionary
                            machine_key = machine_key_replacements.get(machine_key, machine_key)

                            # Replace the machine key with its name
                            machine_name = machine_key_to_name.get(machine_key, machine_key)

                            venue_name = json_data['venue']['name']
                            # Replace the venue name using the replacements dictionary
                            venue_name = venue_name_replacements.get(venue_name, venue_name)

                            team_name = player_info.get('team_name')
                            if not team_name:
                                team_name = 'Unknown'

                            data.append({
                                'machine': machine_name,
                                'player_number': player_number,
                                'player_team': player_info.get('team'),
                                'player_name': player_info.get('name'),
                                'score': player_score,
                                'IPR': player_info.get('IPR'),
                                'venue_name': venue_name,
                                'team_name': team_name,
                                'week': json_data.get('week'),
                                'round_number': round_info.get('n'),
                                'season_number': season_number,
                                'date': json_data.get('date'),
                            })
                            print(f"Extracted data: {data[-1]}")  # Print the extracted data
    except Exception as e:
        print(f"Error processing file {file}: {e}")

# Convert 'date' from MM/DD/YYYY to a datetime object for correct sorting
try:
    data = sorted(
        data,
        key=lambda x: (
            datetime.strptime(x['date'], '%m/%d/%Y'),
            x.get('team_name', 'Unknown')
        )
    )
except Exception as e:
    print(f"Error during sorting: {e}")

# Print the total number of data entries
print(f"Total data entries: {len(data)}")

# Save the data to a CSV file
if data:  # Check if data is not empty
    # Adjusted the output file path to save in the current directory
    output_file = 'matches.csv'

    fieldnames = [
        'machine',
        'player_number',
        'player_team',
        'player_name',
        'score',
        'IPR',
        'venue_name',
        'team_name',
        'week',
        'round_number',
        'season_number',
        'date'
    ]

    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"Data successfully written to {output_file}")
    except Exception as e:
        print(f"Error writing data to CSV: {e}")
else:
    print("No data to write to CSV")