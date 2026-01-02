# MNP Data Conventions - Patterns & Filters

> **Purpose**: MNP-specific data patterns, filtering logic, and conventions for AI assistants
> **Last Updated**: 2026-01-02

---

## 📋 Key Conventions

### File Naming

```bash
# Match files
mnp-{season}-{week}-{away_team}-{home_team}.json

Examples:
mnp-22-01-TRL-SKP.json  # Season 22, Week 1, Trolls @ Slap Kraken Pop
mnp-21-05-ADB-JMF.json  # Season 21, Week 5, Add-a-Ballers @ Jupiter Morning Folks
```

### Team Keys (3-letter codes)

Common teams:
- **SKP** = Slap Kraken Pop (home venue: KRA)
- **TRL** = Trolls (home venue: varies)
- **ADB** = Add-a-Ballers (home venue: AAB)
- **JMF** = Jupiter Morning Folks (home venue: JUP)
- **FBW** = Flippin' Bout a Week (home venue: varies)
- **BSG** = Balls of Steel & Gears (home venue: varies)

### Venue Keys (3-4 letter codes)

Common venues:
- **T4B** = 4Bs Tavern
- **KRA** = Kraken Bar
- **8BT** = 8-bit Arcade Bar
- **JUP** = Jupiter Bar
- **AAB** = Add-a-Ball
- **OLF** = Olaf's
- **SHR** = Shorty's
- **GRG** = Garage
- **PIN** = Pinball Museum

### Machine Keys

Machine keys are abbreviations defined in `machine_variations.json`.

Common machines:
- **MM** = Medieval Madness
- **TZ** = Twilight Zone
- **AFM** = Attack from Mars
- **MB** = Monster Bash
- **T2** = Terminator 2
- **TOTAN** = Tales of the Arabian Nights
- **CV** = Cirqus Voltaire
- **FH** = FunHouse

**Always lookup machine keys** in [machine_variations.json](../machine_variations.json) - never assume!

---

## 🎮 Match Structure

### Round Format

Each match has **4 rounds**:
- **Round 1**: Doubles (4 players, 2 from each team)
- **Round 2**: Singles (2 players, 1 from each team)
- **Round 3**: Singles (2 players, 1 from each team)
- **Round 4**: Doubles (4 players, 2 from each team)

### Machine Selection Rules

**Critical for filtering!**

At **HOME** venue:
- Home team picks machine for **Rounds 2 & 4**
- Away team picks machine for **Rounds 1 & 3**

At **AWAY** venues:
- Home team picks machine for **Rounds 2 & 4** (still!)
- Away team picks machine for **Rounds 1 & 3** (still!)

**Note**: "Home team" = team whose venue the match is at (second team in filename).

### Player Positions

In each round, players are numbered 1-4 (doubles) or 1-2 (singles):
- **Position 1**: Most reliable score
- **Position 2**: Reliable score
- **Position 3**: Generally reliable (doubles only)
- **Position 4**: **UNRELIABLE** - may leave early (doubles only)

**Important**: Player 4 in doubles rounds often finishes their game early and leaves the machine, resulting in artificially low scores. **Never trust Player 4 scores** for statistical analysis.

---

## 🔍 Filtering Patterns

### Venue-Specific Filtering

```python
# Filter scores to specific venue only
target_venue_key = "T4B"

for match_file in match_files:
    match_data = load_json(match_file)

    # Check if match was played at target venue
    if match_data.get('venue', {}).get('key') == target_venue_key:
        # Process this match
        for round_data in match_data['rounds']:
            # Process rounds...
            pass
```

### Machine Selection Filtering (Who Picked)

```python
# Determine if team picked the machine for this round
def team_picked_machine(team_key: str, venue_key: str, team_home_venue_key: str, round_num: int) -> bool:
    """
    Returns True if the team picked the machine for this round.

    Args:
        team_key: The team we're checking (e.g., "SKP")
        venue_key: The venue where match was played (e.g., "KRA")
        team_home_venue_key: The team's home venue (e.g., "KRA" for SKP)
        round_num: Round number (1, 2, 3, or 4)

    Returns:
        True if team picked machine, False if opponent picked
    """
    # Is this team playing at their home venue?
    is_home_venue = (venue_key == team_home_venue_key)

    # At home: team picks rounds 2 & 4
    # Away: team picks rounds 1 & 3
    if is_home_venue:
        return round_num in [2, 4]
    else:
        return round_num in [1, 3]


# Usage example
for match in matches:
    venue_key = match['venue']['key']

    for round_data in match['rounds']:
        round_num = round_data['round']
        machine_key = round_data['machine']['key']

        # Check if SKP picked this machine
        skp_picked = team_picked_machine(
            team_key="SKP",
            venue_key=venue_key,
            team_home_venue_key="KRA",
            round_num=round_num
        )

        if skp_picked:
            # Analyze SKP's performance on machines they chose
            pass
```

### Reliable Score Filtering

```python
# Only use reliable score positions
def get_reliable_positions(round_num: int) -> list[int]:
    """
    Returns list of reliable player positions for this round.

    Args:
        round_num: Round number (1, 2, 3, or 4)

    Returns:
        List of reliable positions (1-indexed)
    """
    if round_num in [1, 4]:  # Doubles rounds
        return [1, 2, 3]  # Exclude position 4 (unreliable)
    else:  # Singles rounds (2, 3)
        return [1, 2]


# Usage example
for round_data in match['rounds']:
    round_num = round_data['round']
    reliable_positions = get_reliable_positions(round_num)

    for player_data in round_data['players']:
        if player_data['position'] in reliable_positions:
            score = player_data['score']
            # Use this score for analysis
```

### Multi-Season Analysis

```python
# Support both single season and multiple seasons
class ReportGenerator:
    def __init__(self, config):
        seasons = config.get('seasons', config.get('season'))

        # Normalize to list
        if isinstance(seasons, list):
            self.seasons = [str(s) for s in seasons]
        else:
            self.seasons = [str(seasons)]

    def load_matches(self):
        matches = []
        for season in self.seasons:
            season_path = f"mnp-data-archive/season-{season}/matches/"
            # Load matches from this season
            matches.extend(load_season_matches(season_path))
        return matches
```

### IPR Range Filtering

```python
# Filter players by IPR range
def filter_by_ipr(players: list, min_ipr: int = None, max_ipr: int = None) -> list:
    """
    Filter players by IPR range.

    Args:
        players: List of player data dicts
        min_ipr: Minimum IPR (inclusive), or None for no minimum
        max_ipr: Maximum IPR (inclusive), or None for no maximum

    Returns:
        Filtered list of players
    """
    filtered = players

    if min_ipr is not None:
        filtered = [p for p in filtered if p.get('ipr', 0) >= min_ipr]

    if max_ipr is not None:
        filtered = [p for p in filtered if p.get('ipr', 10) <= max_ipr]

    return filtered


# Usage example
all_scores = load_scores()

# Only include scores from players with IPR 3-6
ipr_filtered_scores = filter_by_ipr(
    all_scores,
    min_ipr=3,
    max_ipr=6
)
```

---

## 📊 Score Analysis Conventions

### Never Compare Raw Scores Across Machines

```python
# ❌ WRONG - Never do this!
player_avg_score = sum(all_scores) / len(all_scores)

# ✅ CORRECT - Use percentiles
def get_player_performance(player_scores, machine_percentiles):
    """
    Calculate player performance using percentiles.

    Args:
        player_scores: List of {machine_key, score} dicts
        machine_percentiles: Dict mapping machine_key to percentile data

    Returns:
        Average percentile rank (0-100)
    """
    percentile_ranks = []

    for score_data in player_scores:
        machine_key = score_data['machine_key']
        score = score_data['score']

        # Get percentile for this score on this machine
        percentiles = machine_percentiles[machine_key]
        percentile_rank = calculate_percentile_rank(score, percentiles)
        percentile_ranks.append(percentile_rank)

    return sum(percentile_ranks) / len(percentile_ranks)
```

### Home Venue Advantage

```python
# Always account for home venue advantage in analysis
def analyze_player_performance(player_key, matches):
    """
    Analyze player performance, accounting for home advantage.
    """
    home_scores = []
    away_scores = []

    for match in matches:
        venue_key = match['venue']['key']
        player_home_venue = get_player_home_venue(player_key)

        is_home = (venue_key == player_home_venue)

        for round_data in match['rounds']:
            for player_data in round_data['players']:
                if player_data['key'] == player_key:
                    score = player_data['score']

                    if is_home:
                        home_scores.append(score)
                    else:
                        away_scores.append(score)

    return {
        'home_avg': calculate_percentile_avg(home_scores),
        'away_avg': calculate_percentile_avg(away_scores),
        'advantage': calculate_percentile_avg(home_scores) - calculate_percentile_avg(away_scores)
    }
```

### Machine Variance

Some machines have high variance (skill-based, random features), others are consistent.

```python
# High variance machines - wide score distribution
high_variance = ['MM', 'MB', 'TZ', 'AFM']

# Low variance machines - tight score distribution
low_variance = ['T2', 'FH', 'CV']

# Account for variance in predictions
def predict_score(player, machine):
    base_prediction = calculate_base_prediction(player, machine)

    if machine in high_variance:
        # Wider confidence interval
        confidence_interval = base_prediction * 0.5
    else:
        # Tighter confidence interval
        confidence_interval = base_prediction * 0.2

    return {
        'prediction': base_prediction,
        'min': base_prediction - confidence_interval,
        'max': base_prediction + confidence_interval
    }
```

---

## 🗂️ Data File Patterns

### Match JSON Structure

See [MNP_MATCH_STRUCTURE.md](MNP_MATCH_STRUCTURE.md) for complete structure.

Key fields:
```json
{
  "season": "22",
  "week": 1,
  "awayTeam": {"key": "TRL", "name": "Trolls"},
  "homeTeam": {"key": "SKP", "name": "Slap Kraken Pop"},
  "venue": {"key": "KRA", "name": "Kraken Bar"},
  "rounds": [
    {
      "round": 1,
      "machine": {"key": "MM", "name": "Medieval Madness"},
      "players": [
        {"key": "player1", "name": "Player Name", "position": 1, "score": 50000000}
      ]
    }
  ]
}
```

### Config File Pattern

For report generators (archived):
```json
{
  "seasons": "22",           // Single season
  "seasons": ["21", "22"],   // Multiple seasons

  "target_machine": "MM",           // Single machine
  "target_machine": ["MM", "TZ"],   // Multiple machines

  "target_venue": "T4B",     // Specific venue
  "target_venue": null,      // All venues

  "team": {
    "key": "SKP",
    "name": "Slap Kraken Pop"
  },

  "ipr_filter": {
    "min_ipr": 3,
    "max_ipr": 6
  },
  "ipr_filter": null         // No IPR filtering
}
```

---

## 🎯 Common Analysis Patterns

### Player Performance on Specific Machine

```python
def analyze_player_machine_performance(player_key, machine_key, matches):
    """
    Analyze how a player performs on a specific machine.
    """
    scores = []

    for match in matches:
        for round_data in match['rounds']:
            # Check if this round used target machine
            if round_data['machine']['key'] != machine_key:
                continue

            # Find player in this round
            for player_data in round_data['players']:
                if player_data['key'] != player_key:
                    continue

                # Only use reliable positions
                round_num = round_data['round']
                reliable = get_reliable_positions(round_num)

                if player_data['position'] in reliable:
                    scores.append(player_data['score'])

    return {
        'machine': machine_key,
        'games_played': len(scores),
        'avg_score': sum(scores) / len(scores) if scores else 0,
        'avg_percentile': calculate_percentile_avg(scores, machine_key)
    }
```

### Team Machine Selection Patterns

```python
def analyze_team_picks(team_key, team_home_venue, matches):
    """
    Analyze which machines a team picks and when.
    """
    picked_machines = []
    opponent_picked_machines = []

    for match in matches:
        venue_key = match['venue']['key']

        for round_data in match['rounds']:
            round_num = round_data['round']
            machine_key = round_data['machine']['key']

            # Did team pick this machine?
            if team_picked_machine(team_key, venue_key, team_home_venue, round_num):
                picked_machines.append(machine_key)
            else:
                opponent_picked_machines.append(machine_key)

    return {
        'picked': count_frequency(picked_machines),
        'opponent_picked': count_frequency(opponent_picked_machines)
    }
```

### Venue-Specific Machine Performance

```python
def analyze_venue_machine_performance(venue_key, machine_key, matches):
    """
    Analyze how a specific machine performs at a specific venue.
    """
    scores = []

    for match in matches:
        # Only matches at target venue
        if match['venue']['key'] != venue_key:
            continue

        for round_data in match['rounds']:
            # Only rounds on target machine
            if round_data['machine']['key'] != machine_key:
                continue

            # Collect reliable scores
            round_num = round_data['round']
            reliable = get_reliable_positions(round_num)

            for player_data in round_data['players']:
                if player_data['position'] in reliable:
                    scores.append(player_data['score'])

    return {
        'venue': venue_key,
        'machine': machine_key,
        'games_played': len(scores),
        'avg_score': sum(scores) / len(scores) if scores else 0,
        'score_distribution': calculate_distribution(scores)
    }
```

---

## ⚠️ Common Pitfalls

### 1. Using Player 4 Scores
```python
# ❌ WRONG
all_scores = [p['score'] for p in round_data['players']]

# ✅ CORRECT
reliable = get_reliable_positions(round_num)
valid_scores = [p['score'] for p in round_data['players'] if p['position'] in reliable]
```

### 2. Comparing Raw Scores Across Machines
```python
# ❌ WRONG
player1_avg = avg([scores on MM, scores on TZ])

# ✅ CORRECT
player1_percentile = avg([percentile on MM, percentile on TZ])
```

### 3. Ignoring Home/Away Context
```python
# ❌ WRONG
player_avg_score = calculate_avg(all_player_scores)

# ✅ CORRECT
home_avg = calculate_avg(home_scores)
away_avg = calculate_avg(away_scores)
performance = {'home': home_avg, 'away': away_avg, 'diff': home_avg - away_avg}
```

### 4. Wrong Machine Selection Logic
```python
# ❌ WRONG - Assumes home team is always first team
team_picked = (team_key == match['homeTeam']['key'] and round_num in [2, 4])

# ✅ CORRECT - Check actual venue
team_picked = team_picked_machine(team_key, venue_key, team_home_venue, round_num)
```

---

**Remember**: Always use percentiles, respect reliability constraints, and account for home venue advantage!
