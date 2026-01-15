# ETL Pipeline Documentation

> ⚠️ **Outdated:** This is conceptual documentation from planning phase.
> See [ACTUAL_ETL_SCRIPTS.md](ACTUAL_ETL_SCRIPTS.md) for actual implementation.
> For operational guidance, see [DATA_UPDATE_STRATEGY.md](../../DATA_UPDATE_STRATEGY.md).

## Overview

The ETL (Extract, Transform, Load) pipeline is responsible for loading MNP match data from JSON files into the PostgreSQL database. It handles data extraction, normalization, validation, and loading into the appropriate database tables.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                             │
├─────────────────────────────────────────────────────────────┤
│  • mnp-data-archive/season-*/matches/*.json                 │
│  • machine_variations.json                                  │
│  • season-*/teams.csv                                       │
│  • season-*/venues.csv                                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXTRACT                                  │
├─────────────────────────────────────────────────────────────┤
│  • Parse JSON files                                         │
│  • Read CSV files                                           │
│  • Validate file structure                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    TRANSFORM                                │
├─────────────────────────────────────────────────────────────┤
│  • Normalize machine keys                                   │
│  • Extract player information                               │
│  • Calculate denormalized fields                            │
│  • Validate data quality                                    │
│  • Handle duplicates                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    LOAD                                     │
├─────────────────────────────────────────────────────────────┤
│  • Insert into PostgreSQL                                   │
│  • Handle conflicts (upsert)                                │
│  • Maintain referential integrity                           │
│  • Batch operations for performance                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    POST-PROCESSING                          │
├─────────────────────────────────────────────────────────────┤
│  • Calculate percentiles                                    │
│  • Generate aggregate tables                                │
│  • Update statistics                                        │
│  • Run data quality checks                                  │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Extract Phase

#### Input Files

**Match JSON Files**
- Location: `mnp-data-archive/season-{season}/matches/mnp-{season}-{week}-{away}-{home}.json`
- Format: JSON
- Structure: See [MNP_Data_Structure_Reference.md](../../MNP_Data_Structure_Reference.md)

**Machine Variations**
- Location: `machine_variations.json`
- Format: JSON
- Purpose: Canonical machine names and aliases

**Team Data**
- Location: `mnp-data-archive/season-{season}/teams.csv`
- Format: CSV
- Columns: `team_key, venue_key, team_name`

**Venue Data**
- Location: `mnp-data-archive/season-{season}/venues.csv`
- Format: CSV
- Columns: `venue_key, venue_name`

#### Extraction Logic

```python
def extract_matches(season: int, data_path: str) -> List[Dict]:
    """Extract all match JSON files for a season."""
    matches_pattern = f"{data_path}/season-{season}/matches/*.json"
    matches = []

    for match_file in glob.glob(matches_pattern):
        with open(match_file, 'r') as f:
            match_data = json.load(f)
            matches.append(match_data)

    return matches

def extract_machine_variations(variations_path: str) -> Dict:
    """Load machine variations for key normalization."""
    with open(variations_path, 'r') as f:
        return json.load(f)

def extract_teams(season: int, data_path: str) -> List[Dict]:
    """Extract team data from CSV."""
    teams_file = f"{data_path}/season-{season}/teams.csv"
    teams = []

    with open(teams_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            teams.append({
                'team_key': row['team_key'],
                'team_name': row['team_name'],
                'venue_key': row['venue_key'],
                'season': season
            })

    return teams
```

---

### 2. Transform Phase

#### Machine Key Normalization

**Problem**: Machine names appear in various formats across match files
- "MM" vs "MedievalMadness" vs "Medieval Madness"
- Trailing spaces
- Typos and variations

**Solution**: Normalize all machine keys to canonical form using machine_variations.json

```python
class MachineKeyNormalizer:
    def __init__(self, variations: Dict):
        self.variations = variations
        self.alias_map = self._build_alias_map()

    def _build_alias_map(self) -> Dict[str, str]:
        """Build mapping from all variations to canonical keys."""
        alias_map = {}

        for canonical_key, machine_info in self.variations.items():
            # Map canonical key to itself
            alias_map[canonical_key] = canonical_key

            # Map all variations to canonical key
            if 'variations' in machine_info:
                for variation in machine_info['variations']:
                    alias_map[variation.strip().lower()] = canonical_key

        return alias_map

    def normalize(self, machine_key: str) -> str:
        """Normalize a machine key to its canonical form."""
        # Clean the input
        cleaned = machine_key.strip()

        # Try exact match first
        if cleaned in self.alias_map:
            return self.alias_map[cleaned]

        # Try case-insensitive match
        if cleaned.lower() in self.alias_map:
            return self.alias_map[cleaned.lower()]

        # Return cleaned key if no match found
        return cleaned
```

#### Player Extraction

**Challenge**: Player information spread across lineup and game results

**Approach**: Build player lookup from lineups, then reference in scores

```python
def extract_players_from_match(match: Dict) -> List[Dict]:
    """Extract all unique players from a match."""
    players = {}

    for team_type in ['home', 'away']:
        team = match[team_type]
        for player in team['lineup']:
            player_key = player['key']

            if player_key not in players:
                players[player_key] = {
                    'player_key': player_key,
                    'name': player['name'],
                    'current_ipr': player.get('IPR'),
                    'first_seen_season': match.get('season'),
                    'last_seen_season': match.get('season')
                }

    return list(players.values())
```

#### Score Extraction with Context

**Goal**: Extract scores with full denormalized context for query performance

```python
def extract_scores_from_match(match: Dict, normalizer: MachineKeyNormalizer) -> List[Dict]:
    """Extract all scores from a match with full context."""
    scores = []

    # Build player lookup
    player_lookup = {}
    for team_type in ['home', 'away']:
        team = match[team_type]
        for player in team['lineup']:
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

            # Normalize machine key
            machine_key = normalizer.normalize(game['machine'])

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

                scores.append({
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
                    'season': extract_season_from_key(match['key']),
                    'week': match.get('week'),
                    'date': match.get('date')
                })

    return scores
```

#### Data Quality Validation

**Validation Rules:**

```python
class DataValidator:
    """Validate extracted data quality."""

    @staticmethod
    def validate_match(match: Dict) -> List[str]:
        """Validate match data structure."""
        errors = []

        # Required fields
        required = ['key', 'season', 'week', 'venue', 'home', 'away', 'rounds']
        for field in required:
            if field not in match:
                errors.append(f"Missing required field: {field}")

        # Round count
        if 'rounds' in match and len(match['rounds']) != 4:
            errors.append(f"Expected 4 rounds, found {len(match['rounds'])}")

        # Player positions
        for round_data in match.get('rounds', []):
            round_num = round_data['n']
            expected_players = 4 if round_num in [1, 4] else 2

            for game in round_data.get('games', []):
                if not game.get('done'):
                    continue

                actual_players = sum(1 for i in range(1, 5)
                                   if f'player_{i}' in game)

                if actual_players != expected_players:
                    errors.append(
                        f"Round {round_num} game expected {expected_players} "
                        f"players, found {actual_players}"
                    )

        return errors

    @staticmethod
    def validate_score(score: Dict) -> List[str]:
        """Validate individual score data."""
        errors = []

        # Score range
        if score['score'] < 0:
            errors.append(f"Negative score: {score['score']}")

        if score['score'] > 10_000_000_000:
            errors.append(f"Suspiciously high score: {score['score']}")

        # IPR range
        if score.get('player_ipr'):
            ipr = score['player_ipr']
            if not (1 <= ipr <= 6):
                errors.append(f"Invalid IPR: {ipr}")

        # Round/position consistency
        round_num = score['round_number']
        position = score['player_position']

        if round_num in [1, 4] and position > 4:
            errors.append(f"Invalid position {position} for round {round_num}")

        if round_num in [2, 3] and position > 2:
            errors.append(f"Invalid position {position} for round {round_num}")

        return errors
```

---

### 3. Load Phase

#### Database Loading Strategy

**Approach**: Use upsert (INSERT ... ON CONFLICT) to handle incremental loads

```python
class DatabaseLoader:
    """Load transformed data into PostgreSQL."""

    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)

    def load_players(self, players: List[Dict]):
        """Load players with upsert logic."""
        with self.engine.begin() as conn:
            for player in players:
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
                        current_ipr = EXCLUDED.current_ipr,
                        last_seen_season = EXCLUDED.last_seen_season
                """), player)

    def load_matches(self, matches: List[Dict]):
        """Load matches."""
        with self.engine.begin() as conn:
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

    def load_scores_batch(self, scores: List[Dict], batch_size: int = 1000):
        """Load scores in batches for performance."""
        with self.engine.begin() as conn:
            for i in range(0, len(scores), batch_size):
                batch = scores[i:i + batch_size]

                # Build multi-row insert
                conn.execute(text("""
                    INSERT INTO scores (
                        player_key, player_position, score,
                        team_key, is_home_team, player_ipr,
                        match_key, venue_key, machine_key,
                        round_number, season, week, date
                    )
                    VALUES (
                        :player_key, :player_position, :score,
                        :team_key, :is_home_team, :player_ipr,
                        :match_key, :venue_key, :machine_key,
                        :round_number, :season, :week, :date
                    )
                    ON CONFLICT DO NOTHING
                """), batch)
```

#### Loading Order (Respects Foreign Keys)

```python
def load_season_data(season: int, data_path: str, db_loader: DatabaseLoader):
    """Load all data for a season in correct order."""

    # 1. Load reference data (no dependencies)
    print("Loading venues...")
    venues = extract_venues(data_path)
    db_loader.load_venues(venues)

    print("Loading machines...")
    machines = extract_machines()
    db_loader.load_machines(machines)

    # 2. Load teams (depends on venues)
    print("Loading teams...")
    teams = extract_teams(season, data_path)
    db_loader.load_teams(teams)

    # 3. Load players (no dependencies)
    print("Loading players...")
    matches = extract_matches(season, data_path)
    all_players = []
    for match in matches:
        all_players.extend(extract_players_from_match(match))

    # Deduplicate players
    unique_players = {p['player_key']: p for p in all_players}
    db_loader.load_players(list(unique_players.values()))

    # 4. Load matches (depends on venues, teams)
    print("Loading matches...")
    match_records = [transform_match_for_db(m) for m in matches]
    db_loader.load_matches(match_records)

    # 5. Load games (depends on matches)
    print("Loading games...")
    all_games = []
    for match in matches:
        all_games.extend(extract_games_from_match(match))
    db_loader.load_games(all_games)

    # 6. Load scores (depends on players, games)
    print("Loading scores...")
    all_scores = []
    normalizer = MachineKeyNormalizer(extract_machine_variations())
    for match in matches:
        all_scores.extend(extract_scores_from_match(match, normalizer))

    db_loader.load_scores_batch(all_scores)

    print(f"Season {season} loaded successfully!")
    print(f"  Matches: {len(matches)}")
    print(f"  Games: {len(all_games)}")
    print(f"  Scores: {len(all_scores)}")
```

---

### 4. Post-Processing Phase

#### Percentile Calculation

**Algorithm**: Calculate percentile for each score on each machine/venue combination

```python
def calculate_percentiles(season: int, db_connection):
    """Calculate and store percentile data."""

    # Get all machine/venue combinations
    combinations = db_connection.execute("""
        SELECT DISTINCT machine_key, venue_key
        FROM scores
        WHERE season = :season
    """, {'season': season}).fetchall()

    for machine_key, venue_key in combinations:
        # Get all scores for this combination
        scores = db_connection.execute("""
            SELECT score
            FROM scores
            WHERE season = :season
              AND machine_key = :machine_key
              AND venue_key = :venue_key
            ORDER BY score ASC
        """, {
            'season': season,
            'machine_key': machine_key,
            'venue_key': venue_key
        }).fetchall()

        score_values = [s[0] for s in scores]
        n = len(score_values)

        if n < 3:
            continue  # Skip if insufficient data

        # Calculate percentile thresholds
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]

        for p in percentiles:
            # Calculate score at this percentile
            index = int((p / 100.0) * (n - 1))
            score_threshold = score_values[index]

            # Insert into percentiles table
            db_connection.execute("""
                INSERT INTO score_percentiles (
                    machine_key, venue_key, season,
                    percentile, score_threshold, sample_size
                )
                VALUES (
                    :machine_key, :venue_key, :season,
                    :percentile, :score_threshold, :sample_size
                )
                ON CONFLICT (machine_key, venue_key, season, percentile)
                DO UPDATE SET
                    score_threshold = EXCLUDED.score_threshold,
                    sample_size = EXCLUDED.sample_size,
                    last_calculated = CURRENT_TIMESTAMP
            """, {
                'machine_key': machine_key,
                'venue_key': venue_key,
                'season': season,
                'percentile': p,
                'score_threshold': score_threshold,
                'sample_size': n
            })

        print(f"Calculated percentiles for {machine_key} at {venue_key} (n={n})")
```

#### Aggregate Table Generation

**Player Machine Stats:**

```python
def generate_player_machine_stats(season: int, db_connection):
    """Generate player_machine_stats aggregate table."""

    db_connection.execute("""
        INSERT INTO player_machine_stats (
            player_key, machine_key, venue_key, season,
            games_played, median_score, avg_score, best_score, worst_score,
            median_percentile, avg_percentile
        )
        SELECT
            s.player_key,
            s.machine_key,
            s.venue_key,
            s.season,
            COUNT(*) as games_played,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.score) as median_score,
            AVG(s.score)::bigint as avg_score,
            MAX(s.score) as best_score,
            MIN(s.score) as worst_score,
            -- Calculate percentile rankings
            PERCENTILE_CONT(0.5) WITHIN GROUP (
                ORDER BY calculate_score_percentile(s.score, s.machine_key, s.venue_key, s.season)
            ) as median_percentile,
            AVG(calculate_score_percentile(s.score, s.machine_key, s.venue_key, s.season)) as avg_percentile
        FROM scores s
        WHERE s.season = :season
        GROUP BY s.player_key, s.machine_key, s.venue_key, s.season
        HAVING COUNT(*) >= 3  -- Minimum 3 games for stats
        ON CONFLICT (player_key, machine_key, venue_key, season)
        DO UPDATE SET
            games_played = EXCLUDED.games_played,
            median_score = EXCLUDED.median_score,
            avg_score = EXCLUDED.avg_score,
            best_score = EXCLUDED.best_score,
            worst_score = EXCLUDED.worst_score,
            median_percentile = EXCLUDED.median_percentile,
            avg_percentile = EXCLUDED.avg_percentile,
            last_calculated = CURRENT_TIMESTAMP
    """, {'season': season})
```

**Team Machine Picks:**

```python
def generate_team_machine_picks(season: int, db_connection):
    """Generate team_machine_picks aggregate table."""

    # This requires tracking machine selection, which may need
    # additional logic to determine who picked which machine
    # Based on round number and home/away status

    db_connection.execute("""
        INSERT INTO team_machine_picks (
            team_key, machine_key, season, is_home, round_type,
            times_picked, wins, total_points, avg_score
        )
        SELECT
            s.team_key,
            s.machine_key,
            s.season,
            s.is_home_team as is_home,
            CASE
                WHEN s.round_number IN (1, 4) THEN 'doubles'
                ELSE 'singles'
            END as round_type,
            COUNT(DISTINCT s.match_key || '-' || s.round_number) as times_picked,
            -- Wins calculated based on game outcomes (TBD)
            0 as wins,
            0 as total_points,
            AVG(s.score)::bigint as avg_score
        FROM scores s
        WHERE s.season = :season
        GROUP BY
            s.team_key, s.machine_key, s.season,
            s.is_home_team, round_type
        ON CONFLICT (team_key, machine_key, season, is_home, round_type)
        DO UPDATE SET
            times_picked = EXCLUDED.times_picked,
            avg_score = EXCLUDED.avg_score,
            last_calculated = CURRENT_TIMESTAMP
    """, {'season': season})
```

---

## Command-Line Interface

### Main ETL Script

```bash
# Load a single season
python etl/load_matches.py --season 22

# Load multiple seasons
python etl/load_matches.py --seasons 20,21,22

# Load with specific data path
python etl/load_matches.py --season 22 --data-path /path/to/mnp-data-archive

# Skip percentile calculation (faster for testing)
python etl/load_matches.py --season 22 --skip-percentiles

# Dry run (validate only, don't load)
python etl/load_matches.py --season 22 --dry-run

# Verbose output
python etl/load_matches.py --season 22 --verbose
```

### Percentile Recalculation

```bash
# Recalculate percentiles for a season
python etl/calculate_percentiles.py --season 22

# Recalculate for specific machine
python etl/calculate_percentiles.py --season 22 --machine MM

# Recalculate for all seasons
python etl/calculate_percentiles.py --all-seasons
```

### Data Quality Report

```bash
# Generate data quality report
python etl/data_quality_report.py --season 22

# Output formats
python etl/data_quality_report.py --season 22 --format json
python etl/data_quality_report.py --season 22 --format markdown
```

---

## Error Handling

### Recoverable Errors
- Missing player IPR → Use NULL
- Invalid machine key → Skip game, log warning
- Duplicate score → Skip insert (ON CONFLICT DO NOTHING)

### Fatal Errors
- Database connection failure → Abort
- JSON parse error → Abort file, continue with others
- Missing required match fields → Skip match, log error

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('mnp-etl')

# Usage
logger.info(f"Loading season {season}")
logger.warning(f"Invalid machine key: {machine_key}")
logger.error(f"Failed to parse match file: {file_path}", exc_info=True)
```

---

## Performance Considerations

### Batch Operations
- Insert scores in batches of 1000 for ~10x speedup
- Use multi-row INSERT statements
- Transaction per batch, not per row

### Indexes
- Drop indexes before bulk load
- Recreate indexes after load
- Can reduce load time by 50%+

### Parallel Processing
- Process multiple seasons in parallel
- Use multiprocessing for CPU-bound transformations
- Database connection pooling for concurrent writes

---

## Testing Strategy

### Unit Tests
```python
def test_machine_key_normalization():
    variations = load_test_variations()
    normalizer = MachineKeyNormalizer(variations)

    assert normalizer.normalize("MM") == "MedievalMadness"
    assert normalizer.normalize("mm") == "MedievalMadness"
    assert normalizer.normalize(" MM ") == "MedievalMadness"

def test_player_extraction():
    match_data = load_test_match()
    players = extract_players_from_match(match_data)

    assert len(players) > 0
    assert all('player_key' in p for p in players)
```

### Integration Tests
```python
def test_full_etl_pipeline():
    # Use test database
    test_db = create_test_database()

    # Load small test dataset
    load_season_data(season=99, data_path='test/fixtures', db_loader=test_db)

    # Verify counts
    assert test_db.count_matches() == 5
    assert test_db.count_scores() == 60

    # Verify data quality
    assert test_db.count_invalid_scores() == 0
```

---

## Monitoring & Maintenance

### Load Metrics to Track
- Total execution time
- Records processed per second
- Error count by type
- Data quality score

### Regular Maintenance
- Weekly: Load new matches
- Monthly: Recalculate all percentiles
- Quarterly: Full data quality audit
- Annually: Archive old seasons

---

**Document Version**: 1.0
**Last Updated**: 2026-01-14
**Status**: Conceptual documentation - See actual scripts in /etl
