# MNP Match Data Analysis Guide

## Overview
This document provides a comprehensive guide to analyzing Monday Night Pinball (MNP) match data, including data structure, scoring mechanics, reliability considerations, and analytical opportunities.

## Season Structure

### Organization
- **Available Seasons**: Season 21 & 22 (`mnp-data-archive/season-21`, `mnp-data-archive/season-22`)
- **Regular Season**: 10 weeks of matches
- **Teams**: Up to 10 players per team
- **Match Distribution**: Each team plays 5 home matches and 5 away matches
- **File Naming**: `mnp-{season}-{week}-{away}-{home}.json`

### Venue Considerations
- Teams typically play at their designated home venue
- **Exception**: When both teams share the same home venue, one team is designated as "home" and one as "away" for match purposes

## Match Structure

### Round Format
Each match consists of 4 rounds with alternating machine selection:

| Round | Machine Selection | Player Configuration | Game Type |
|-------|-------------------|---------------------|-----------|
| 1 | Away Team | 4-player (P1: Away, P2: Home, P3: Away, P4: Home) | Doubles |
| 2 | Home Team | 2-player (P1: Home, P2: Away) | Singles |
| 3 | Away Team | 2-player (P1: Away, P2: Home) | Singles |
| 4 | Home Team | 4-player (P1: Home, P2: Away, P3: Home, P4: Away) | Doubles |

### Player Positioning
- **Rounds 1 & 4 (Doubles)**: 4 players total
- **Rounds 2 & 3 (Singles)**: 2 players total
- **Strategic Importance**: Machine selection alternates to balance competitive advantage

## Scoring Mechanics & Data Reliability

### Score Reliability by Position

#### Highly Reliable Scores
- **4-player games (Rounds 1, 4)**: Players 1, 2, and 3 scores are generally reliable
- **2-player games (Rounds 2, 3)**: Player 1 scores are most reliable

#### Potentially Skewed Scores
- **4-player games**: Player 4 scores may be inflated if they don't need to complete their full game after seeing opponents' scores
- **2-player games**: Player 2 scores may be affected by strategic play once Player 1's score is known

### Cross-Machine Score Comparisons
- **Within Machine**: Scores are directly comparable and meaningful
- **Between Machines**: Scores are NOT directly comparable due to vastly different scoring mechanisms
- **Analysis Approach**: Normalize scores by machine or use percentile rankings within machine

## Player Rating System

### IPR (Individual Player Rating)
- **Scale**: 1-6 (6 = highest skill level)
- **Purpose**: Correlates with player skill level
- **Analytical Use**: Compare performance expectations vs. actual results by IPR level

## Key Analytical Opportunities

### Performance Analysis
1. **Home Venue Advantage**
   - Compare home vs. away team performance
   - Identify venues with strongest home field advantage
   - Account for venue-specific machine availability

2. **Score Variability by Machine**
   - Calculate coefficient of variation for each machine
   - Identify "high-variance" vs. "consistent" machines
   - Correlate with strategic machine selection

3. **IPR vs. Performance Correlation**
   - Machine-specific IPR performance correlation
   - Identify machines that favor higher/lower IPR players
   - Validate IPR accuracy through performance data

### Strategic Analysis
4. **Machine Selection Patterns**
   - Predict machine choices based on:
     - Team composition (IPR distribution)
     - Historical performance on specific machines
     - Venue availability
   - Identify "signature" machines for teams/players

5. **Competitive Balance**
   - Away team win percentage by machine
   - Home team win percentage by machine
   - Machine selection impact on match outcomes

### Advanced Analytics
6. **Performance Prediction Models**
   - Player performance on specific machines given IPR
   - Team performance based on lineup composition
   - Machine selection optimization

7. **Venue-Specific Analysis**
   - Machine performance consistency across venues
   - Venue-specific advantages for certain play styles
   - Impact of machine condition/maintenance on scores

## Data Processing Considerations

### Score Normalization Approaches
1. **Z-Score by Machine**: `(score - machine_mean) / machine_std`
2. **Percentile Ranking**: Position within machine score distribution (RECOMMENDED)
3. **IPR-Adjusted Performance**: Compare to expected performance by IPR level

### Filtering Strategies
- Exclude potentially unreliable Player 4 scores in doubles rounds
- Focus on Player 1 scores in singles rounds for most analyses
- Consider game completion status when available

### Statistical Considerations
- Account for small sample sizes on individual machines
- Consider seasonal effects and learning curves
- Handle missing data appropriately (incomplete games, etc.)

## Advanced Filtering Patterns

### Venue-Specific Score Filtering

When analyzing performance at a specific venue, filter matches by venue key:

```python
# Only include matches played at specific venue
venue_key = match.get('venue', {}).get('key', '')
if venue_key == 'T4B':  # 4Bs Tavern
    # Process this match
```

**Use Cases:**
- Venue-specific score distributions
- Home venue advantage analysis
- Machine performance at different locations

### Machine Selection Analysis (Home/Away)

Understanding who picked which machine is critical for strategic analysis:

**Machine Selection Rules:**
- **Home Team** picks machines in Rounds 2 & 4
- **Away Team** picks machines in Rounds 1 & 3

**Implementation Pattern:**
```python
# Determine if team picked the machine based on venue and round
is_home_venue = (venue_key == team_home_venue_key)

if is_home_venue:
    # At home venue: team picks rounds 2 & 4
    team_picked_machine = (round_num in [2, 4])
else:
    # At away venues: team picks rounds 1 & 3
    team_picked_machine = (round_num in [1, 3])
```

**Analytical Applications:**
- Compare team performance on self-selected vs opponent-selected machines
- Identify team's preferred machines
- Analyze strategic machine selection patterns
- Evaluate performance advantage from machine choice

### Multi-Season Analysis

When analyzing across multiple seasons, handle both single and multi-season configs:

```python
# Support flexible season configuration
seasons = config['seasons']
if isinstance(seasons, list):
    season_list = seasons
else:
    season_list = [str(seasons)]

# Load matches from all specified seasons
for season in season_list:
    matches_pattern = f"mnp-data-archive/season-{season}/matches/*.json"
    # Process matches...
```

### Team-Specific Filtering

Extract scores only for specific team members:

```python
# Build player lookup
match_players = {}
for team_type in ['home', 'away']:
    for player in match[team_type].get('lineup', []):
        match_players[player['key']] = {
            'team': match[team_type]['key'],
            'name': player['name']
        }

# Filter scores by team
if player_info['team'] == target_team_key:
    # Include this score
```

### IPR-Based Filtering

Filter scores by player skill level for fair comparisons:

```python
# Only include players within IPR range
player_ipr = player_info.get('ipr', 0)
if min_ipr <= player_ipr <= max_ipr:
    # Include this score
```

**Use Cases:**
- Compare performance within skill tiers
- Analyze machine difficulty by skill level
- Create skill-normalized benchmarks

### Reliable Position Filtering

Standard pattern for excluding unreliable scores:

```python
# Define reliable positions by round type
if round_num in [1, 4]:  # 4-player doubles
    reliable_positions = [1, 2, 3, 4]
    # Or more conservative: [1, 2, 3] to exclude P4
else:  # 2-player singles
    reliable_positions = [1, 2]
    # Or most conservative: [1] for highest reliability

# Only process reliable positions
for pos in reliable_positions:
    if f'score_{pos}' in game:
        # Process this score
```



---

**Last Updated**: 2025-11-10
**Version**: 2.0
**Maintainer**: JJC

*This document is continuously updated as new analysis patterns and insights are discovered. For practical report generation, see [reports/README.md](reports/README.md).*