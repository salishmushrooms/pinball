# Score Percentile Report Configuration Guide

## Quick Start

1. **Use a preset**: Start with one of the preset configurations
2. **Edit settings**: Modify the values in the config files
3. **Run the report**: `python reports/generators/score_percentile_report.py reports/configs/[config_file].json`

## Configuration Options

### Option 1: Comprehensive Config (All-in-One)
Edit `comprehensive_config.json` - all settings in one file:

```json
{
  "season": "21",
  "target_machine": "AFM", 
  "target_venue": null,
  "ipr_filter": {
    "min_ipr": 3,
    "max_ipr": 6
  }
}
```

### Option 2: Modular Config (Separate Files)
Use `modular_config.json` and edit individual files:

- **Season**: Edit `seasons.json` 
- **Machine**: Edit `machines.json`
- **Venue**: Edit `venues.json`
- **IPR Filter**: Edit `ipr_filters.json`

### Option 3: Preset Configs
Ready-to-use configurations:

- `preset_all_players.json` - All skill levels
- `preset_advanced_players.json` - IPR 5-6 only

## Configuration Fields

### Season
```json
"season": "21"
```
Available: "14", "15", "16", "17", "18", "19", "20", "21"

### Machine
```json
"target_machine": "AFM"
```
Popular machines: AFM, MM, MB, TZ, STTNG, T2, TOM, CFTBL, TAF, FH

### Venue (Optional)
```json
"target_venue": null                    // All venues
"target_venue": {                       // Specific venue
  "code": "8BT",
  "name": "8-bit Arcade Bar"
}
```

### IPR Filter (Optional)
```json
"ipr_filter": null                      // All players
"ipr_filter": {                         // Skill range
  "min_ipr": 3,
  "max_ipr": 6
}
```

**IPR Presets:**
- Beginners: IPR 1-2
- Intermediate: IPR 3-4  
- Advanced: IPR 5-6
- Intermediate+: IPR 3-6

## Examples

### Analyze AFM scores from advanced players in season 21:
```bash
python reports/generators/score_percentile_report.py reports/configs/preset_advanced_players.json
```

### Analyze Medieval Madness scores from all players:
1. Edit `comprehensive_config.json`: change `"target_machine": "MM"`
2. Run: `python reports/generators/score_percentile_report.py reports/configs/comprehensive_config.json`

### Compare different skill levels:
1. Run with `preset_all_players.json`
2. Run with `preset_advanced_players.json` 
3. Compare the percentile charts

## Answering Your Key Questions

### "What score do I need to beat 75% of intermediate players?"
1. Set IPR filter to 3-4 in any config
2. Look at 75th percentile in the generated report

### "How does 1M more points help against advanced players?"
1. Run with IPR 5-6 filter
2. Find your current score on the chart
3. See how adding 1M points moves you up the percentile scale

## File Structure
```
reports/configs/
├── README.md                    # This guide
├── comprehensive_config.json    # All-in-one config
├── modular_config.json         # References separate files
├── seasons.json                # Season settings
├── machines.json               # Machine settings  
├── venues.json                 # Venue settings
├── ipr_filters.json            # IPR filter presets
├── preset_all_players.json     # All skill levels
└── preset_advanced_players.json # Advanced only
```