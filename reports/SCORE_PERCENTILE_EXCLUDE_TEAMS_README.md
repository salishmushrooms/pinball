# Score Percentile Report - Excluding Specific Teams

## Overview

This document describes the new `score_percentile_report_exclude_venues.py` script and its configuration for generating score percentile reports while excluding scores from players on specific teams.

## Purpose

The script generates score vs percentile charts and reports for pinball machines while filtering out scores from players whose teams have home venues at The 4 Bs (T4B) or Ice Box (IBX). This is useful for analyzing venue performance without the potential bias from teams playing at their home venue.

## Key Features

- **Player-level filtering**: Excludes individual scores from specific teams rather than entire matches
- **Venue-specific analysis**: Can analyze scores at a specific venue (e.g., The 4 Bs)
- **Automatic team detection**: Reads `teams.csv` to identify which teams have home venues at excluded locations
- **Detailed reporting**: Shows how many scores were excluded per machine

## Files Created

### Script
- `reports/generators/score_percentile_report_exclude_venues.py` - Modified version of the score percentile report that excludes scores from specific teams

### Configuration File
- `reports/configs/4bs_venue_exclude_home_teams.json` - Configuration for analyzing The 4 Bs venue while excluding home team scores

## Excluded Teams (Season 22)

The following teams are automatically excluded based on their home venues:

**Teams with home venue at The 4 Bs (T4B):**
- TBT - The B Team
- TRL - Trolls!
- RTR - Ramp Tramps

**Teams with home venue at Ice Box (IBX):**
- LAS - Little League All Stars
- PYC - Pinballycule
- POW - The Power

## Usage

### Basic Usage
```bash
python reports/generators/score_percentile_report_exclude_venues.py reports/configs/4bs_venue_exclude_home_teams.json
```

### Custom Excluded Venues
```bash
python reports/generators/score_percentile_report_exclude_venues.py <config_file> <venue1,venue2>
```

Example:
```bash
python reports/generators/score_percentile_report_exclude_venues.py reports/configs/season22_all_machines.json T4B,IBX
```

## Configuration Options

The configuration file supports all standard score percentile report options:

```json
{
  "description": "The 4 Bs Venue - Season 22 - Excluding scores from teams with home venue at 4Bs or Ice Box",
  "season": "22",
  "target_machine": null,  // null = all machines
  "target_venue": {
    "code": "T4B",
    "name": "4Bs Tavern"
  },
  "ipr_filter": null,  // Optional: {"min_ipr": 3, "max_ipr": 6}
  "outlier_filter": null,  // Optional outlier filtering
  "data_filters": {
    "include_incomplete_matches": false
  },
  "score_reliability": {
    "rounds_1_4": {
      "reliable_positions": [1, 2, 3, 4]
    },
    "rounds_2_3": {
      "reliable_positions": [1, 2]
    }
  }
}
```

## Output

### Generated Reports (Example: 007 at The 4 Bs)
- **Chart**: `reports/charts/007_percentile_season_22_T4B_exclude_T4B_IBX.png`
- **Report**: `reports/output/007_percentile_season_22_T4B_exclude_T4B_IBX.md`

### Chart Titles
Charts automatically include information about excluded venues:
```
Score vs Percentile: James Bond 007 (Stern 2022) at 4Bs Tavern (Excluding home games at: T4B, IBX)
Season 22
```

### Console Output
The script provides detailed feedback:
```
Extracted 20 scores for machine '007' (excluded 30 scores from filtered teams)
```

## How It Works

1. **Load team-venue mapping** from `mnp-data-archive/season-XX/teams.csv`
2. **Identify excluded teams** based on home venues (T4B, IBX by default)
3. **Load matches** (optionally filtered by venue)
4. **Extract scores** while skipping scores from excluded teams
5. **Generate charts and reports** with filtered data

## Example Results (Season 22 at The 4 Bs)

The script processed 13 matches at The 4 Bs and generated reports for 20 machines:

| Machine | Scores Included | Scores Excluded |
|---------|-----------------|-----------------|
| 007 | 20 | 30 |
| Baywatch | 24 | 36 |
| Jaws | 21 | 39 |
| MM | 22 | 40 |
| TOM | 28 | 40 |
| TOTAN | 24 | 40 |

## Notes

- The script automatically reads team-venue mappings from `teams.csv` for each season
- Teams are excluded based on their **home venue**, not where the match is played
- Individual **scores** are filtered, not entire matches
- This allows analysis of visiting team performance at a venue

## Comparison with Original Script

| Feature | Original Script | Exclude Venues Script |
|---------|----------------|----------------------|
| Team filtering | None | Excludes specific teams |
| Filter level | N/A | Individual scores |
| Team detection | N/A | Automatic from teams.csv |
| Output naming | Standard | Includes "_exclude_T4B_IBX" |
| Chart titles | Standard | Includes exclusion info |

## Future Enhancements

Potential improvements:
- Support for excluding specific teams by name (not just by home venue)
- Option to exclude only when teams play at their home venue
- Comparison charts showing filtered vs unfiltered data
- Statistical analysis of home venue advantage

---

**Created**: 2025-01-23
**Author**: Claude Code
**Purpose**: Document the score percentile report with team exclusion functionality
