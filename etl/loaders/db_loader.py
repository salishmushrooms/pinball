"""
Database loader for inserting extracted data into PostgreSQL.
Uses batch inserts and upsert logic for efficient loading.
"""

import logging
from typing import List, Dict
from sqlalchemy import text

from etl.database import db
from etl.config import config

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Load transformed data into PostgreSQL"""

    def __init__(self):
        self.db = db
        if not self.db.engine:
            self.db.connect()

    def load_venues(self, venues: List[Dict]) -> int:
        """Load venues with upsert logic"""
        if not venues:
            return 0

        count = 0
        with self.db.engine.begin() as conn:
            for venue in venues:
                conn.execute(text("""
                    INSERT INTO venues (venue_key, venue_name, city, state, active)
                    VALUES (:venue_key, :venue_name, :city, :state, :active)
                    ON CONFLICT (venue_key) DO UPDATE SET
                        venue_name = EXCLUDED.venue_name,
                        city = EXCLUDED.city,
                        state = EXCLUDED.state,
                        active = EXCLUDED.active
                """), {
                    'venue_key': venue['venue_key'],
                    'venue_name': venue['venue_name'],
                    'city': venue.get('city'),
                    'state': venue.get('state'),
                    'active': venue.get('active', True)
                })
                count += 1

        logger.info(f"Loaded {count} venues")
        return count

    def load_machines(self, machines: List[Dict]) -> int:
        """Load machines with upsert logic"""
        if not machines:
            return 0

        count = 0
        with self.db.engine.begin() as conn:
            for machine in machines:
                conn.execute(text("""
                    INSERT INTO machines (machine_key, machine_name, manufacturer, year, game_type)
                    VALUES (:machine_key, :machine_name, :manufacturer, :year, :game_type)
                    ON CONFLICT (machine_key) DO UPDATE SET
                        machine_name = EXCLUDED.machine_name,
                        manufacturer = EXCLUDED.manufacturer,
                        year = EXCLUDED.year,
                        game_type = EXCLUDED.game_type
                """), machine)
                count += 1

        logger.info(f"Loaded {count} machines")
        return count

    def load_machine_aliases(self, aliases: List[Dict]) -> int:
        """Load machine aliases with upsert logic"""
        if not aliases:
            return 0

        count = 0
        with self.db.engine.begin() as conn:
            for alias in aliases:
                conn.execute(text("""
                    INSERT INTO machine_aliases (alias, machine_key, alias_type)
                    VALUES (:alias, :machine_key, :alias_type)
                    ON CONFLICT (alias) DO UPDATE SET
                        machine_key = EXCLUDED.machine_key,
                        alias_type = EXCLUDED.alias_type
                """), alias)
                count += 1

        logger.info(f"Loaded {count} machine aliases")
        return count

    def load_teams(self, teams: List[Dict]) -> int:
        """Load teams with upsert logic"""
        if not teams:
            return 0

        count = 0
        with self.db.engine.begin() as conn:
            for team in teams:
                conn.execute(text("""
                    INSERT INTO teams (team_key, season, team_name, home_venue_key)
                    VALUES (:team_key, :season, :team_name, :home_venue_key)
                    ON CONFLICT (team_key, season) DO UPDATE SET
                        team_name = EXCLUDED.team_name,
                        home_venue_key = EXCLUDED.home_venue_key
                """), team)
                count += 1

        logger.info(f"Loaded {count} teams")
        return count

    def load_players(self, players: List[Dict]) -> int:
        """
        Load players with upsert logic.

        NOTE: This does NOT update current_ipr from match files.
        IPR values should be loaded separately using load_ipr() to ensure
        IPR.csv is the source of truth.
        """
        if not players:
            return 0

        count = 0
        with self.db.engine.begin() as conn:
            for player in players:
                # Convert IPR of 0 to None (NULL) to satisfy check constraint
                ipr = player.get('current_ipr')
                if ipr == 0 or ipr is None:
                    ipr = None

                conn.execute(text("""
                    INSERT INTO players (
                        player_key, name, current_ipr,
                        first_seen_season, last_seen_season
                    )
                    VALUES (
                        :player_key, :name, :current_ipr,
                        :first_seen_season, :last_seen_season
                    )
                    ON CONFLICT (player_key) DO UPDATE SET
                        name = EXCLUDED.name,
                        -- Do NOT update current_ipr here - use load_ipr() instead
                        first_seen_season = LEAST(players.first_seen_season, EXCLUDED.first_seen_season),
                        last_seen_season = GREATEST(players.last_seen_season, EXCLUDED.last_seen_season)
                """), {
                    'player_key': player['player_key'],
                    'name': player['name'],
                    'current_ipr': ipr,
                    'first_seen_season': player['first_seen_season'],
                    'last_seen_season': player['last_seen_season']
                })
                count += 1

        logger.info(f"Loaded {count} players")
        return count

    def load_ipr(self, ipr_updates: List[Dict]) -> int:
        """
        Load IPR data from IPR.csv (source of truth for player ratings).

        Args:
            ipr_updates: List of dicts with 'player_name' and 'current_ipr'

        Returns:
            Number of players updated
        """
        if not ipr_updates:
            return 0

        count = 0
        updated = 0
        not_found = 0

        with self.db.engine.begin() as conn:
            for update in ipr_updates:
                player_name = update['player_name']
                ipr = update['current_ipr']

                # Convert IPR of 0 to None (NULL)
                if ipr == 0 or ipr is None:
                    ipr = None

                # Update player by name
                result = conn.execute(text("""
                    UPDATE players
                    SET current_ipr = :current_ipr,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = :player_name
                """), {
                    'current_ipr': ipr,
                    'player_name': player_name
                })

                if result.rowcount > 0:
                    updated += 1
                else:
                    not_found += 1
                    logger.debug(f"Player not found in database: {player_name}")

                count += 1

        logger.info(f"Processed {count} IPR updates: {updated} updated, {not_found} not found")
        return updated

    def load_venue_machines(self, venue_machines: List[Dict]) -> int:
        """Load venue-machine relationships, auto-creating missing machines"""
        if not venue_machines:
            return 0

        count = 0
        machines_created = 0

        with self.db.engine.begin() as conn:
            for vm in venue_machines:
                # First, ensure the machine exists - create if missing
                # Check if machine exists
                result = conn.execute(text("""
                    SELECT machine_key FROM machines WHERE machine_key = :machine_key
                """), {'machine_key': vm['machine_key']})

                if result.fetchone() is None:
                    # Machine doesn't exist - create it with minimal info
                    logger.warning(f"Auto-creating missing machine: {vm['machine_key']}")
                    conn.execute(text("""
                        INSERT INTO machines (machine_key, machine_name)
                        VALUES (:machine_key, :machine_name)
                        ON CONFLICT (machine_key) DO NOTHING
                    """), {
                        'machine_key': vm['machine_key'],
                        'machine_name': vm['machine_key']  # Use key as name
                    })
                    machines_created += 1

                # Now insert the venue-machine relationship
                conn.execute(text("""
                    INSERT INTO venue_machines (venue_key, machine_key, season, active)
                    VALUES (:venue_key, :machine_key, :season, :active)
                    ON CONFLICT (venue_key, machine_key, season) DO UPDATE SET
                        active = EXCLUDED.active
                """), vm)
                count += 1

        if machines_created > 0:
            logger.info(f"Auto-created {machines_created} missing machines")
        logger.info(f"Loaded {count} venue-machine relationships")
        return count

    def load_matches(self, matches: List[Dict]) -> int:
        """Load matches with upsert logic"""
        if not matches:
            return 0

        count = 0
        with self.db.engine.begin() as conn:
            for match in matches:
                conn.execute(text("""
                    INSERT INTO matches (
                        match_key, season, week, date,
                        venue_key, home_team_key, away_team_key, state
                    )
                    VALUES (
                        :match_key, :season, :week, :date,
                        :venue_key, :home_team_key, :away_team_key, :state
                    )
                    ON CONFLICT (match_key) DO UPDATE SET
                        state = EXCLUDED.state,
                        updated_at = CURRENT_TIMESTAMP
                """), match)
                count += 1

        logger.info(f"Loaded {count} matches")
        return count

    def load_games(self, games: List[Dict]) -> int:
        """Load games, auto-creating missing machines"""
        if not games:
            return 0

        count = 0
        machines_created = 0

        with self.db.engine.begin() as conn:
            for game in games:
                # First, ensure the machine exists - create if missing
                result = conn.execute(text("""
                    SELECT machine_key FROM machines WHERE machine_key = :machine_key
                """), {'machine_key': game['machine_key']})

                if result.fetchone() is None:
                    # Machine doesn't exist - create it with minimal info
                    logger.warning(f"Auto-creating missing machine: {game['machine_key']}")
                    conn.execute(text("""
                        INSERT INTO machines (machine_key, machine_name)
                        VALUES (:machine_key, :machine_name)
                        ON CONFLICT (machine_key) DO NOTHING
                    """), {
                        'machine_key': game['machine_key'],
                        'machine_name': game['machine_key']  # Use key as name
                    })
                    machines_created += 1

                # Now insert the game
                result = conn.execute(text("""
                    INSERT INTO games (
                        match_key, round_number, game_number, machine_key, done,
                        season, week, venue_key
                    )
                    VALUES (
                        :match_key, :round_number, :game_number, :machine_key, :done,
                        :season, :week, :venue_key
                    )
                    ON CONFLICT (match_key, round_number, game_number) DO NOTHING
                    RETURNING game_id
                """), game)

                # Store game_id for scores loading
                row = result.fetchone()
                if row:
                    game['game_id'] = row[0]
                    count += 1

        if machines_created > 0:
            logger.info(f"Auto-created {machines_created} missing machines")
        logger.info(f"Loaded {count} games")
        return count

    def load_scores_batch(self, scores: List[Dict], batch_size: int = None) -> int:
        """Load scores in batches for performance"""
        if not scores:
            return 0

        if batch_size is None:
            batch_size = config.BATCH_SIZE

        # First, we need to get game_ids for the scores
        # Build a map of (match_key, round_number, game_number) -> game_id
        with self.db.engine.connect() as conn:
            # Get all game_ids
            result = conn.execute(text("""
                SELECT game_id, match_key, round_number
                FROM games
                WHERE match_key = ANY(:match_keys)
            """), {
                'match_keys': list(set(s['match_key'] for s in scores))
            })

            game_id_map = {}
            for row in result:
                game_id, match_key, round_number = row
                key = (match_key, round_number)
                game_id_map[key] = game_id

        # Add game_id to each score
        scores_with_game_id = []
        for score in scores:
            key = (score['match_key'], score['round_number'])
            if key in game_id_map:
                score['game_id'] = game_id_map[key]
                scores_with_game_id.append(score)

        # Insert scores in batches
        count = 0
        with self.db.engine.begin() as conn:
            for i in range(0, len(scores_with_game_id), batch_size):
                batch = scores_with_game_id[i:i + batch_size]

                for score in batch:
                    # Convert IPR of 0 to None (NULL) to satisfy check constraint
                    ipr = score.get('player_ipr')
                    if ipr == 0 or ipr is None:
                        ipr = None

                    conn.execute(text("""
                        INSERT INTO scores (
                            game_id, player_key, player_position, score,
                            team_key, is_home_team, player_ipr, is_substitute,
                            match_key, venue_key, machine_key,
                            round_number, season, week, date
                        )
                        VALUES (
                            :game_id, :player_key, :player_position, :score,
                            :team_key, :is_home_team, :player_ipr, :is_substitute,
                            :match_key, :venue_key, :machine_key,
                            :round_number, :season, :week, :date
                        )
                        ON CONFLICT DO NOTHING
                    """), {
                        'game_id': score['game_id'],
                        'player_key': score['player_key'],
                        'player_position': score['player_position'],
                        'score': score['score'],
                        'team_key': score['team_key'],
                        'is_home_team': score['is_home_team'],
                        'player_ipr': ipr,
                        'is_substitute': score.get('is_substitute', False),
                        'match_key': score['match_key'],
                        'venue_key': score['venue_key'],
                        'machine_key': score['machine_key'],
                        'round_number': score['round_number'],
                        'season': score['season'],
                        'week': score['week'],
                        'date': score.get('date')
                    })
                    count += 1

        logger.info(f"Loaded {count} scores")
        return count
