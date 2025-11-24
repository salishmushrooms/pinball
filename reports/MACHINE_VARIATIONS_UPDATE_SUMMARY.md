# Machine Variations Update Summary

**Date**: 2025-11-23
**Season Analyzed**: Season 22

## Overview

Added 27 missing machine entries to `machine_variations.json` to support Season 22 data reporting.

## Process

1. Created `reports/generators/find_missing_machines.py` - utility script to identify machines in match data that are missing from machine_variations.json
2. Ran analysis on Season 22 data
3. Cross-referenced with `mnp-data-archive/machines.json` for official names
4. Added missing entries to `machine_variations.json`

## Added Machines

| Key | Full Name | Notes |
|-----|-----------|-------|
| AS | Alien Star | |
| BOPP | Bobby Orr Power Player | |
| BallyTrek | Star Trek (Bally) | |
| Cactus Canyon Remake | Cactus Canyon Remake | |
| Captain fantastic | Captain Fantastic | Capitalized |
| DRAGON | Dragon | |
| DUNE | Dune | **New 2024 machine** |
| FHRN | Funhouse Rudy's Nightmare | |
| GF | Godfather | |
| Gamatron | Gamatron | Added GAMA variation |
| HW | Hot Wheels | |
| JB60 | James Bond 007 (60th) | Newer Bond machine |
| KONG | King Kong | **New 2024 machine** |
| LAB | Labyrinth | |
| METREM | Metallica Remastered | Updated version |
| MH | Mata Hari | |
| Outer Space | Outer Space | Added OuterSpace variation |
| PHAR | Pharaoh | |
| QS | Quicksilver | |
| RUSH | Rush | |
| SB | Sinbad | |
| SG | Star Gazer | |
| SWFOTE | Star Wars: Fall of the Empire | **New 2024 machine** |
| TS | Toy Story | |
| ULTRA | Ultraman | |
| VEN | Venom | **New 2024 machine** |
| TBL | The Big Lebowski | **New 2024 machine** |

## Data Quality Issues

Found and corrected:
- **"Woyal Wumble"** → Added as variation to RR (Royal Rumble) to catch this typo in source data

## Statistics

- **Before**: 306 machines in machine_variations.json
- **After**: 332 machines in machine_variations.json
- **Added**: 26 new machine entries
- **Season 22 Machines**: 156 unique machines used
- **Coverage**: 100% of Season 22 machines now mapped

## Usage

To find missing machines in future seasons:

```bash
python reports/generators/find_missing_machines.py <season>

# Example:
python reports/generators/find_missing_machines.py 23
```

This will:
1. Scan all match files for the specified season
2. Extract unique machine keys
3. Compare against machine_variations.json
4. Look up official names from mnp-data-archive/machines.json
5. Generate JSON entries for missing machines

## Verification

Run the score percentile report to verify all machines are properly named:

```bash
python reports/generators/score_percentile_report.py reports/configs/4bs_season22_all_machines.json
```

All 20 machines at 4Bs in Season 22 now display with proper full names:
- TBL → "The Big Lebowski"
- KONG → "King Kong"
- VEN → "Venom"
- SWFOTE → "Star Wars: Fall of the Empire"
- etc.

## Future Maintenance

As new machines are added to the league:
1. Run `find_missing_machines.py` after each new season
2. Verify machine names in `mnp-data-archive/machines.json`
3. Update `machine_variations.json` with new entries
4. Consider adding common misspellings as variations

## Files Modified

- `machine_variations.json` - Added 26 new machine entries + 1 variation
- `reports/generators/score_percentile_report.py` - Updated to use full machine names in markdown reports

## Files Created

- `reports/generators/find_missing_machines.py` - Utility for finding missing machine mappings
