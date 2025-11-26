# MNP Data Archive

This repository contains data from the Monday Night Pinball (MNP) starting with season 14. The data is organized by season and includes match results, machine information, and other league data.

## Directory Structure

```
mnp-data-archive/
├── season-XX/           # Data for each season
│   └── matches/        # Match JSON files
├── machines.json       # Machine definitions and names
├── venues.json        # Venue information
└── IPR.csv           # Individual Player Ratings
└── matches.csv      # 10 weeks of matchups using team key
 
```

## Match Structure

Matches are played between two league teams during the regular season (not playoffs) at one of the team's home venues. Each team plays 5 home and 5 away matches per season.

### Match Format

A match consists of four rounds with the following structure:

#### Pre-Match (8:15pm)
- Captains from both teams declare lineups
- Captains confirm each other's lineups

#### Round 1 (Doubles)
- Away team picks 4 machines and 4 pairs of players [8:15pm]
- Home team picks 4 pairs of players to match up [8:20pm]
- Four-player games on chosen machines (Players 1,3: away team; 2,4: home team) [8:30pm]
- Scores and photos entered
- Captains review and confirm round
- Expected duration: 30 minutes

#### Round 2 (Singles)
- Home team picks 7 machines and 7 players [8:50pm]
- Away team picks 7 players to match up [8:55pm]
- Two-player games on chosen machines [9:05pm]
- Scores and photos entered
- Captains review and confirm round
- Expected duration: 20 minutes

#### Round 3 (Singles)
- Away team picks 7 machines and 7 players [9:35pm]
- Home team picks 7 players to match up [9:40pm]
- Two-player games on chosen machines [9:50pm]
- Scores and photos entered
- Captains review and confirm round
- Expected duration: 20 minutes

#### Round 4 (Doubles)
- Home team picks 4 machines and 4 pairs of players [10:20pm]
- Away team picks 4 pairs of players to match up [10:25pm]
- Four-player games on chosen machines (Players 1,3: home team; 2,4: away team) [10:35pm]
- Scores and photos entered
- Captains review and confirm round [11:05pm]
- Expected duration: 30 minutes

### Scoring System

#### Doubles Games (5 points total)
- 1 point for each opponent's score beaten
- 1 additional point for the team with highest combined score

#### Singles Games (3 points total)
- 2 points awarded to the player with higher score
- 1 additional point awarded to the winner if their score is double the loser's score
- 1 point awarded to the loser if their score was not doubled

## JSON File Structure

### Match Files (mnp-XX-YY-TEAM1-TEAM2.json)

```json
{
  "key": "mnp-21-1-ADB-JMF",
  "name": "WK1 ADB @ JMF",
  "type": "manual",
  "week": "1",
  "round": 4,
  "create_at": 1738448652376,
  "date": "02/03/2025",
  "state": "complete",
  "venue": {
    "key": "JUP",
    "name": "Jupiter",
    "machines": ["UXMEN", "Getaway", ...]
  },
  "away": {
    "name": "Admiraballs",
    "key": "ADB",
    "captains": [...],
    "lineup": [...],
    "ready": true,
    "confirmed": {...}
  },
  "home": {
    "name": "Middle Flippers",
    "key": "JMF",
    "captains": [...],
    "lineup": [...],
    "ready": true,
    "confirmed": {...}
  },
  "rounds": [
    {
      "n": 1,
      "games": [
        {
          "n": 1,
          "machine": "VEN",
          "player_1": "...",
          "player_2": "...",
          "player_3": "...",
          "player_4": "...",
          "done": true,
          "photos": [...],
          "score_1": 99337870,
          "score_2": 26798880,
          "score_3": 50205800,
          "score_4": 19860680,
          "points_1": 2.5,
          "points_2": 0,
          "points_3": 2.5,
          "points_4": 0,
          "score_13": 149543670,
          "score_24": 46659560,
          "points_13": 5,
          "points_24": 0,
          "away_points": 5,
          "home_points": 0
        }
      ],
      "done": true,
      "right_confirmed": {...},
      "left_confirmed": {...}
    }
  ]
}
```

### Key Fields in Match Files

- `key`: Unique identifier for the match (format: mnp-SEASON-WEEK-TEAM1-TEAM2)
- `name`: Human-readable match name
- `type`: Match type (manual, playoff, etc.)
- `week`: Week number in the season
- `round`: Round number in the season
- `date`: Match date
- `state`: Match state (complete, in_progress, etc.)
- `venue`: Venue information including available machines
- `away`/`home`: Team information including:
  - `name`: Team name
  - `key`: Team identifier
  - `captains`: List of team captains
  - `lineup`: List of players with their details
  - `ready`: Team ready status
  - `confirmed`: Confirmation details
- `rounds`: Array of match rounds, each containing:
  - `n`: Round number
  - `games`: Array of games played in the round
  - `done`: Round completion status
  - `right_confirmed`/`left_confirmed`: Confirmation details

### Game Structure

Each game in a round contains:
- `n`: Game number
- `machine`: Machine identifier
- `player_1` through `player_4`: Player identifiers (4 players for doubles, 2 for singles)
- `done`: Game completion status
- `photos`: Array of score photos
- `score_1` through `score_4`: Individual player scores
- `points_1` through `points_4`: Points awarded to each player
- `score_13`/`score_24`: Combined scores for doubles games
- `points_13`/`points_24`: Points awarded to each pair
- `away_points`/`home_points`: Total points awarded to each team for the game

## Machine Definitions

The `machines.json` file contains a mapping of machine keys to their full names:

```json
{
  "TAF": {
    "key": "TAF",
    "name": "The Addams Family"
  },
  "AIQ": {
    "key": "AIQ",
    "name": "Avengers Infinity Quest"
  }
  // ... more machines
}
```

## Venue Information

The `venues.json` file contains information about venues where matches are played, including:
- Venue name and identifier
- Available machines
- Other venue-specific details

## Individual Player Ratings

The `IPR.csv` file contains Individual Player Ratings for all players in the league, which are used for team balancing and match organization.
