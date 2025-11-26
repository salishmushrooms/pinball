# MNP Data Archive Project Guide

## Project Overview

This repository contains Monday Night Pinball (MNP) match data, analytics, and reporting tools.

---

## Directory Structure

```
/Users/JJC/Pinball/MNP/
├── mnp-data-archive/          # League data (submodule)
│   ├── season-XX/
│   │   └── matches/
│   ├── machines.json
│   ├── venues.json
│   └── IPR.csv
├── reports/                    # Analysis and report generation
│   ├── configs/
│   └── generators/
├── README.md
├── MNP_Data_Structure_Reference.md
├── MNP_Match_Data_Analysis_Guide.md
└── machine_variations.json
```

---

## Purpose

Analyze Monday Night Pinball match data including scores, teams, venues, and player performance.

---

## Key Files

### Data Reference Guides
- [MNP_Data_Structure_Reference.md](MNP_Data_Structure_Reference.md) - Overview of data structure and file organization
- [MNP_Match_Data_Analysis_Guide.md](MNP_Match_Data_Analysis_Guide.md) - Detailed analysis guide with scoring mechanics
- [README.md](README.md) - High-level project overview

### Data Files
- `mnp-data-archive/season-XX/matches/*.json` - Individual match files
- `mnp-data-archive/machines.json` - Machine definitions and names
- `mnp-data-archive/venues.json` - Venue information
- `mnp-data-archive/IPR.csv` - Individual Player Ratings

### Machine Lookups
- [machine_variations.json](machine_variations.json) - Maps machine keys to full names and variations

---

## Report Generation

Located in [reports/](reports/) directory:
- `generators/` - Python scripts for generating reports
- `configs/` - Configuration files for report parameters
- `output/` - Generated markdown reports
- `charts/` - Generated PNG charts and visualizations

**See [reports/README.md](reports/README.md) for comprehensive report generation guide**

### Available Report Generators

1. **score_percentile_report.py** - Score distribution analysis
   - Generates percentile charts for machines
   - Supports venue filtering, IPR filtering, multi-season analysis
   - Creates aggregate grid images for multiple machines
   - Config pattern: Specify seasons, machines, venues, IPR ranges

2. **venue_summary_report.py** - Venue-specific analysis
   - Machine statistics at specific venues
   - High scores, selection patterns, round analysis
   - Both detailed and simplified output formats

3. **team_machine_comparison_report.py** - Team vs team comparison
   - Compare two teams' performance on specific machines
   - Scores from all venues (no venue filtering)
   - Sorted by score with player details

4. **team_machine_choice_report.py** - Machine selection analysis
   - Track when team picked machines vs opponent picked
   - Home venue: team picks rounds 2 & 4
   - Away venues: team picks rounds 1 & 3
   - Shows performance on own picks vs forced picks

### Config File Pattern

All generators use JSON config files in `reports/configs/`:
```json
{
  "season": "22" or ["21", "22"],
  "target_machine": "MM" or ["MM", "TZ", "AFM"],
  "target_venue": "T4B" or null (all venues),
  "team": {"key": "SKP", "name": "Slap Kraken Pop"},
  "ipr_filter": {"min_ipr": 3, "max_ipr": 6} or null
}
```

### Quick Start Examples

```bash
# Score distributions for 4Bs machines (season 22 only)
python3 reports/generators/score_percentile_report.py reports/configs/4bs_machines_config.json

# Compare two teams on specific machines
python3 reports/generators/team_machine_comparison_report.py reports/configs/trolls_vs_slapkrakenpop_config.json

# Analyze team's machine choices (home vs away)
python3 reports/generators/team_machine_choice_report.py reports/configs/skp_machine_choices_config.json
```

---

## Match Data Structure

Matches follow this pattern:
- **File naming**: `mnp-{season}-{week}-{away}-{home}.json`
- **4 rounds**: Round 1 & 4 (doubles, 4 players), Round 2 & 3 (singles, 2 players)
- **Scoring**: Points awarded based on head-to-head performance
- **Teams**: Each team plays 5 home and 5 away matches per season

---

## Important Notes

- **Player 4 scores in doubles may be unreliable** (early game completion)
- **Scores are NOT comparable across different machines** (use percentiles)
- **Home venue advantage exists** - see analysis guides for details

---

## Common Tasks

### Generate a venue report
```bash
python reports/generators/venue_summary_report.py
```

### Generate percentile analysis
```bash
python reports/generators/score_percentile_report.py
```

### Find machine key
1. Check [machine_variations.json](machine_variations.json)
2. Search for machine name or abbreviation
3. Use `key` field for match data queries

---

## Important Conventions

### MNP Data
- **Match files**: `mnp-{season}-{week}-{away}-{home}.json`
- **Team keys**: 3-letter abbreviations (e.g., "SKP", "TRL", "ADB", "JMF")
- **Venue keys**: 3-4 letter codes (e.g., "T4B", "KRA", "JUP", "8BT")
- **Machine keys**: Abbreviations from `machine_variations.json`

### Important Venue Codes (Frequently Referenced)
- **T4B** = 4Bs Tavern
- **KRA** = Kraken (home venue for Slap Kraken Pop)
- **8BT** = 8-bit Arcade Bar
- **OLF** = Olaf's
- **SHR** = Shorty's
- **AAB** = Add-a-Ball
- **JUP** = Jupiter

### Important Team Keys (Frequently Referenced)
- **SKP** = Slap Kraken Pop
- **TRL** = Trolls!
- **ADB** = Add-a-Ballers
- **JMF** = Jupiter Morning Folks

---

## Key Principles

### MNP Analysis
1. **Score normalization**: Use percentiles, not raw scores across machines
2. **Data reliability**: Player 1 > Player 2 > Player 3 > Player 4
3. **Home advantage**: Real and measurable - account for it
4. **Machine variance**: Some machines are high-variance, others consistent

---

## Tools & Technologies

- **Python** for report generation
- **JSON** for match data storage
- **CSV** for tabular data (venues, IPR, matches overview)

---

## Getting Help

- Read [MNP_Data_Structure_Reference.md](MNP_Data_Structure_Reference.md) for structure
- Read [MNP_Match_Data_Analysis_Guide.md](MNP_Match_Data_Analysis_Guide.md) for analysis guidance
- Check [machine_variations.json](machine_variations.json) for machine lookups

---

## Related Projects

**Pin Stats iOS App** (`/Users/JJC/Pinball/pin-stats`)
- GitHub: https://github.com/salishmushrooms/pinstats.git
- iOS application for displaying charts and analysis based on MNP data
- Consumes data from this repository

---

## Current Status

- **Season 21 & 22 data available**
- **Four specialized report generators created**:
  - Score percentile analysis (multi-machine, multi-season)
  - Venue summary analysis
  - Team comparison reports
  - Machine choice analysis (home/away picks)
- Home advantage analysis in progress

---

## Next Steps

- Continue developing analysis reports
- Refine home advantage metrics
- Expand machine-specific analysis
- Support Pin Stats app with data exports and analysis

---

**Last Updated**: 2025-11-10
**Maintained by**: JJC
**LLM Context**: This file helps Claude understand the MNP data analysis project structure

---

## Key Filtering Patterns for LLM Reference

### Venue-Specific Filtering
```python
# Filter scores to only include matches played at specific venue
if match_data.get('venue', {}).get('key') == target_venue_key:
    # Process this match
```

### Machine Selection (Home/Away) Filtering
```python
# At HOME venue: Team picks rounds 2 & 4, opponent picks rounds 1 & 3
# At AWAY venues: Team picks rounds 1 & 3, opponent picks rounds 2 & 4

is_home_venue = (venue_key == team_home_venue_key)
if is_home_venue:
    team_picked_machine = (round_num in [2, 4])
else:
    team_picked_machine = (round_num in [1, 3])
```

### Reliable Score Positions
```python
# Rounds 1 & 4 (4-player): positions 1, 2, 3, 4
# Rounds 2 & 3 (2-player): positions 1, 2 only
# Player 4 in 4-player rounds may be unreliable

if round_num in [1, 4]:
    reliable_positions = [1, 2, 3, 4]
else:
    reliable_positions = [1, 2]
```

### Multi-Season Analysis
```python
# Support both single season and multiple seasons
seasons = self.config['seasons']
if isinstance(seasons, list):
    self.seasons = seasons
else:
    self.seasons = [str(seasons)]
```
