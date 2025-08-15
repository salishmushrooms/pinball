# MNP Data Archive Structure Reference

## Directory Structure
```
mnp-data-archive/
├── season-21/                    # Current season data
│   ├── venues.csv               # Venue codes and names
│   ├── matches.csv              # Match schedule overview
│   ├── teams.csv                # Team information
│   ├── rosters.csv              # Player rosters by team
│   ├── groups.csv               # Group/division information
│   ├── season.json              # Season metadata
│   └── matches/                 # Individual match JSON files
│       └── mnp-21-{week}-{away}-{home}.json
├── machines.json                # Global machine definitions
└── venues.json                  # Global venue information
```

## Key Data Files

### venues.csv
- Format: `{venue_code},{venue_name}`
- Example: `T4B,4Bs Tavern`
- Maps venue codes to full names

### Match JSON Files
- Naming: `mnp-{season}-{week}-{away_team}-{home_team}.json`
- Example: `mnp-21-1-TWC-TBT.json` (Week 1, The Wrecking Crew @ 4Bs Tavern)

## Match JSON Structure

### Top Level Fields
- `key`: Unique match identifier
- `name`: Human readable match name
- `week`: Week number (1-10)
- `date`: Match date
- `state`: Match status ("complete", "playing", etc.)
- `venue`: Venue information with machine list
- `away`/`home`: Team information

### Venue Object
```json
{
  "key": "T4B",
  "name": "4Bs Tavern",
  "machines": ["UXMEN", "Taxi", "Godzilla", ...]
}
```

### Team Objects (away/home)
```json
{
  "name": "Team Name",
  "key": "TEAM",
  "captains": [...],
  "lineup": [
    {
      "key": "player_hash_id",
      "name": "Player Name", 
      "IPR": 4,
      "num_played": 3,
      "sub": false
    }
  ]
}
```

### Rounds Array
Each match has 4 rounds with games:
```json
{
  "n": 1,                        # Round number
  "games": [
    {
      "n": 1,                    # Game number
      "machine": "UXMEN",        # Machine code
      "player_1": "player_hash", # Player identifiers
      "player_2": "player_hash",
      "player_3": "player_hash", # Only in 4-player games
      "player_4": "player_hash", # Only in 4-player games
      "score_1": 150000000,      # Individual scores
      "score_2": 75000000,
      "score_3": 120000000,
      "score_4": 45000000,
      "done": true               # Game completion status
    }
  ]
}
```

## Data Quality Notes

### Finding Venue Matches
To find all matches at venue T4B:
1. Search for `"key": "T4B"` in venue object within match files
2. Or grep for `T4B` across all match JSON files

### Player Identification
- Players identified by hash keys (e.g., `"72cf88bd05692a3d53cf4381ca846c7a383933ce"`)
- Names provided for human readability
- IPR (Individual Player Rating) ranges 1-6 (6 = highest skill)

### Score Reliability
- Rounds 1,4: 4-player games (player_1 through player_4)
- Rounds 2,3: 2-player games (player_1, player_2 only)
- Player 4 scores in 4-player games may be unreliable (early game completion)
- Player 1 scores generally most reliable

### Machine Codes
- Machine codes used throughout data (e.g., "UXMEN", "MM", "TZ")
- Full names available in `machines.json`
- Scores only comparable within same machine type