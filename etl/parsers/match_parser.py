"""
Parser for match JSON files.
Extracts players, teams, matches, games, and scores from match data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class MatchParser:
    """Parse match JSON files"""

    def __init__(self):
        self.matches_loaded = 0

    def load_match_file(self, file_path: Path) -> Dict:
        """Load a single match JSON file"""
        try:
            with open(file_path, 'r') as f:
                match_data = json.load(f)

            self.matches_loaded += 1
            return match_data

        except FileNotFoundError:
            logger.error(f"Match file not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in match file {file_path}: {e}")
            raise

    def load_all_matches(self, matches_dir: Path) -> List[Dict]:
        """Load all match JSON files from a directory"""
        matches = []

        if not matches_dir.exists():
            logger.error(f"Matches directory not found: {matches_dir}")
            return matches

        match_files = sorted(matches_dir.glob("*.json"))

        for match_file in match_files:
            try:
                match_data = self.load_match_file(match_file)
                matches.append(match_data)
            except Exception as e:
                logger.warning(f"Skipping {match_file.name}: {e}")
                continue

        logger.info(f"Loaded {len(matches)} matches from {matches_dir}")
        return matches

    def extract_season_from_key(self, match_key: str) -> int:
        """Extract season number from match key (e.g., 'mnp-22-1-ADB-TBT' -> 22)"""
        parts = match_key.split('-')
        if len(parts) >= 2:
            return int(parts[1])
        return None

    def extract_players_from_match(self, match: Dict) -> List[Dict]:
        """Extract unique players from a match"""
        players = {}
        season = self.extract_season_from_key(match['key'])

        for team_type in ['home', 'away']:
            team = match.get(team_type, {})
            for player in team.get('lineup', []):
                player_key = player['key']

                if player_key not in players:
                    players[player_key] = {
                        'player_key': player_key,
                        'name': player['name'],
                        'current_ipr': player.get('IPR'),
                        'first_seen_season': season,
                        'last_seen_season': season
                    }

        return list(players.values())

    def extract_teams_from_match(self, match: Dict) -> List[Dict]:
        """Extract team information from a match"""
        teams = []
        season = self.extract_season_from_key(match['key'])

        for team_type in ['home', 'away']:
            team = match.get(team_type, {})
            teams.append({
                'team_key': team['key'],
                'season': season,
                'team_name': team['name'],
                'home_venue_key': match['venue']['key'] if team_type == 'home' else None
            })

        return teams

    def extract_venue_from_match(self, match: Dict) -> Dict:
        """Extract venue information from a match"""
        venue = match.get('venue', {})
        return {
            'venue_key': venue['key'],
            'venue_name': venue['name']
        }

    def extract_venue_machines(self, match: Dict) -> List[Dict]:
        """Extract venue-machine relationships from a match"""
        venue = match.get('venue', {})
        season = self.extract_season_from_key(match['key'])

        machines = []
        for machine_key in venue.get('machines', []):
            machines.append({
                'venue_key': venue['key'],
                'machine_key': machine_key,
                'season': season,
                'active': True
            })

        return machines

    def extract_match_metadata(self, match: Dict) -> Dict:
        """Extract match metadata"""
        season = self.extract_season_from_key(match['key'])

        # Parse date if present
        date = match.get('date')
        if date:
            try:
                # Try parsing MM/DD/YYYY format
                date_obj = datetime.strptime(date, '%m/%d/%Y')
                date = date_obj.strftime('%Y-%m-%d')
            except:
                date = None

        return {
            'match_key': match['key'],
            'season': season,
            'week': int(match.get('week', 0)),
            'date': date,
            'venue_key': match['venue']['key'],
            'home_team_key': match['home']['key'],
            'away_team_key': match['away']['key'],
            'state': match.get('state', 'unknown')
        }

    def extract_games_from_match(self, match: Dict) -> List[Dict]:
        """Extract game records from a match"""
        games = []
        season = self.extract_season_from_key(match['key'])

        for round_data in match.get('rounds', []):
            round_num = round_data['n']

            for game in round_data.get('games', []):
                # Skip games that haven't been set up yet (no machine assigned)
                if 'machine' not in game:
                    continue

                game_data = {
                    'match_key': match['key'],
                    'round_number': round_num,
                    'game_number': game.get('n', 1),
                    'machine_key': game['machine'],
                    'done': game.get('done', False),
                    'season': season,
                    'week': int(match.get('week', 0)),
                    'venue_key': match['venue']['key']
                }
                games.append(game_data)

        return games

    def extract_scores_from_match(self, match: Dict, machine_normalizer=None) -> List[Dict]:
        """Extract all scores from a match with full context"""
        scores = []
        season = self.extract_season_from_key(match['key'])

        # Parse date
        date = match.get('date')
        if date:
            try:
                date_obj = datetime.strptime(date, '%m/%d/%Y')
                date = date_obj.strftime('%Y-%m-%d')
            except:
                date = None

        # Build player lookup
        player_lookup = {}
        for team_type in ['home', 'away']:
            team = match.get(team_type, {})
            for player in team.get('lineup', []):
                player_lookup[player['key']] = {
                    'name': player['name'],
                    'team_key': team['key'],
                    'team_name': team['name'],
                    'is_home': team_type == 'home',
                    'ipr': player.get('IPR')
                }

        # Extract scores from each round
        for round_data in match.get('rounds', []):
            round_num = round_data['n']

            for game in round_data.get('games', []):
                if not game.get('done', False):
                    continue  # Skip incomplete games

                # Get machine key (normalize if normalizer provided)
                machine_key = game['machine']
                if machine_normalizer:
                    machine_key = machine_normalizer.normalize_machine_key(machine_key)

                # Determine how many players based on round
                max_position = 4 if round_num in [1, 4] else 2

                for position in range(1, max_position + 1):
                    player_key = game.get(f'player_{position}')
                    score = game.get(f'score_{position}')

                    if not player_key or score is None:
                        continue

                    player_info = player_lookup.get(player_key)
                    if not player_info:
                        continue

                    score_data = {
                        'player_key': player_key,
                        'player_position': position,
                        'score': score,
                        'team_key': player_info['team_key'],
                        'is_home_team': player_info['is_home'],
                        'player_ipr': player_info['ipr'],
                        # Denormalized context
                        'match_key': match['key'],
                        'venue_key': match['venue']['key'],
                        'machine_key': machine_key,
                        'round_number': round_num,
                        'season': season,
                        'week': int(match.get('week', 0)),
                        'date': date
                    }

                    scores.append(score_data)

        return scores
