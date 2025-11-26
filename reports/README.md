# MNP Report Generation Guide

This directory contains Python-based report generators for analyzing Monday Night Pinball match data.

---

## Directory Structure

```
reports/
├── generators/          # Python report generator scripts
├── configs/            # JSON configuration files
├── output/             # Generated markdown reports
└── charts/             # Generated PNG charts and visualizations
```

---

## Available Report Generators

### 1. Score Percentile Report (`score_percentile_report.py`)

**Purpose:** Generate score distribution charts and percentile analysis for pinball machines.

**Features:**
- Percentile vs score charts for individual machines
- Multi-machine processing (creates individual + aggregate charts)
- Multi-season analysis
- Venue filtering (analyze scores at specific venues)
- IPR filtering (filter by player skill level)
- Outlier filtering (percentile, IQR, or absolute bounds)
- Auto-discovery mode (analyze all machines in dataset)

**Usage:**
```bash
python3 reports/generators/score_percentile_report.py <config_file>
```

**Example Config:**
```json
{
  "season": ["21", "22"],
  "target_machine": ["MM", "TZ", "AFM"],
  "target_venue": "T4B",
  "ipr_filter": {"min_ipr": 3, "max_ipr": 6},
  "outlier_filter": {
    "method": "percentile",
    "lower_percentile": 5,
    "upper_percentile": 95
  },
  "data_filters": {
    "include_incomplete_matches": false
  },
  "score_reliability": {
    "rounds_1_4": {"reliable_positions": [1, 2, 3]},
    "rounds_2_3": {"reliable_positions": [1, 2]}
  }
}
```

**Outputs:**
- Individual PNG charts for each machine
- Markdown reports with statistics
- Aggregate grid image (2-column layout)

**Example:**
```bash
python3 reports/generators/score_percentile_report.py reports/configs/4bs_machines_config.json
```

---

### 2. Venue Summary Report (`venue_summary_report.py`)

**Purpose:** Generate comprehensive statistics for machines at a specific venue.

**Features:**
- Machine-by-machine statistics (median, percentiles, high scores)
- Selection analysis (most picked by home/away teams)
- Round-by-round game counts
- Home team high scores
- Simplified or detailed output formats

**Usage:**
```bash
python3 reports/generators/venue_summary_report.py <config_file>
```

**Example Config:**
```json
{
  "season": "22",
  "target_venue": {
    "code": "T4B",
    "name": "4Bs Tavern"
  },
  "data_filters": {
    "include_incomplete_matches": false
  },
  "score_reliability": {
    "rounds_1_4": {"reliable_positions": [1, 2, 3, 4]},
    "rounds_2_3": {"reliable_positions": [1, 2]}
  },
  "output_format": {
    "style": "detailed"
  }
}
```

**Outputs:**
- Markdown report with venue statistics
- Machine selection analysis
- High score information

---

### 3. Team Machine Comparison Report (`team_machine_comparison_report.py`)

**Purpose:** Compare two teams' performance on specific machines across all venues.

**Features:**
- Head-to-head team comparison on selected machines
- Scores from all venues (not venue-filtered)
- Sorted by score (descending)
- Player details (name, IPR, venue, date)
- Summary statistics per team per machine

**Usage:**
```bash
python3 reports/generators/team_machine_comparison_report.py <config_file>
```

**Example Config:**
```json
{
  "season": "22",
  "team1": {
    "key": "TRL",
    "name": "Trolls!"
  },
  "team2": {
    "key": "SKP",
    "name": "Slap Kraken Pop"
  },
  "target_machines": [
    "MM", "TZ", "Godzilla", "IronMaiden", "Jaws"
  ]
}
```

**Outputs:**
- Markdown report with side-by-side team comparison
- Score tables sorted by performance
- Statistics (count, high, average)

**Example:**
```bash
python3 reports/generators/team_machine_comparison_report.py reports/configs/trolls_vs_slapkrakenpop_config.json
```

---

### 4. Team Machine Choice Report (`team_machine_choice_report.py`)

**Purpose:** Analyze when a team picked specific machines vs when opponents picked them.

**Features:**
- Identifies machine picker based on home/away and round rules
- Shows team performance on self-selected machines
- Shows team performance on opponent-selected machines
- Multi-season support
- Venue-aware (home venue vs away venues)

**Machine Selection Rules:**
- **At Home Venue**: Team picks rounds 2 & 4, opponent picks rounds 1 & 3
- **At Away Venues**: Team picks rounds 1 & 3, opponent picks rounds 2 & 4

**Usage:**
```bash
python3 reports/generators/team_machine_choice_report.py <config_file>
```

**Example Config:**
```json
{
  "seasons": ["21", "22"],
  "team": {
    "key": "SKP",
    "name": "Slap Kraken Pop"
  },
  "home_venue_key": "KRA",
  "target_machines": [
    "MM", "TZ", "Godzilla", "IronMaiden", "Jaws"
  ]
}
```

**Outputs:**
- Markdown report showing machine choices
- Separate sections for "Team Picked" vs "Opponent Picked"
- Performance statistics for each scenario

**Example:**
```bash
python3 reports/generators/team_machine_choice_report.py reports/configs/skp_machine_choices_config.json
```

---

### 5. Team Venue Machine Performance Report (`team_venue_machine_performance_report.py`)

**Purpose:** Analyze a team's performance on all machines at a specific venue, showing points earned vs opponents.

**Features:**
- Calculates points earned by team vs opponents for each machine
- Automatically determines team positions based on home/away status and round
- Sorts machines by total points (descending)
- Shows POPS (Percentage of Points Scored) for each machine
- Includes median scores and game counts
- Identifies strongest and weakest machines at the venue

**Player Position Rules:**
- **At Home Venue**:
  - Round 1 (4-player): Team is players 2, 4
  - Round 2 (2-player): Team is player 1
  - Round 3 (2-player): Team is player 2
  - Round 4 (4-player): Team is players 1, 3
- **At Away Venues**: Positions are reversed

**Usage:**
```bash
python3 reports/generators/team_venue_machine_performance_report.py <config_file>
```

**Example Config:**
```json
{
  "season": "22",
  "team": {
    "key": "DTP",
    "name": "DTP"
  },
  "team_home_venue_key": "JUP",
  "target_venue": {
    "key": "JUP",
    "name": "Jupiter"
  }
}
```

**Outputs:**
- Markdown report with overall team performance summary
- Machine-by-machine breakdown sorted by total points
- Team points, opponent points, POPS, and median scores
- Identifies machines where team has strongest advantage

**Example:**
```bash
python3 reports/generators/team_venue_machine_performance_report.py reports/configs/dtp_jupiter_performance_config.json
```

---

### 6. Team Venue Pick Frequency Report (`team_venue_pick_frequency_report.py`)

**Purpose:** Show which machines a team picks most often at a specific venue, separated by doubles vs singles rounds.

**Features:**
- Counts machine selections (not performance)
- Separates picks by round type (doubles vs singles)
- Filters to specific venue
- Optional filter to only current machines at venue
- Shows pick frequency percentages
- Combined ranking showing total picks

**Pick Rules:**
- **At Home Venue**: Team picks Round 2 (singles) and Round 4 (doubles)
- **At Away Venues**: Team picks Round 1 (doubles) and Round 3 (singles)

**Usage:**
```bash
python3 reports/generators/team_venue_pick_frequency_report.py <config_file>
```

**Example Config:**
```json
{
  "season": "22",
  "team": {
    "key": "DTP",
    "name": "DTP"
  },
  "team_home_venue_key": "JUP",
  "target_venue": {
    "key": "JUP",
    "name": "Jupiter"
  },
  "current_machines": ["MM", "TZ", "AFM", "GOT"]
}
```

**Outputs:**
- Pick frequency counts for doubles rounds
- Pick frequency counts for singles rounds
- Combined ranking showing all picks
- Percentage breakdown by round type

**Example:**
```bash
python3 reports/generators/team_venue_pick_frequency_report.py reports/configs/dtp_jupiter_pick_frequency_config.json
```

---

## Configuration Patterns

### Common Configuration Fields

#### Season Selection
```json
// Single season
"season": "22"

// Multiple seasons
"season": ["21", "22"]
"seasons": ["21", "22"]  // Alternative field name
```

#### Machine Selection
```json
// Single machine
"target_machine": "MM"

// Multiple machines
"target_machine": ["MM", "TZ", "AFM"]

// Auto-discover all machines
"target_machine": null
"target_machine": "auto"
```

#### Venue Filtering
```json
// All venues
"target_venue": null

// Single venue
"target_venue": "T4B"

// Legacy format
"target_venue": {"code": "T4B", "name": "4Bs Tavern"}
```

#### IPR Filtering
```json
// No filtering
"ipr_filter": null

// Range filtering
"ipr_filter": {
  "min_ipr": 3,
  "max_ipr": 6
}

// Minimum only
"ipr_filter": {"min_ipr": 4}

// Maximum only
"ipr_filter": {"max_ipr": 5}
```

#### Score Reliability
```json
"score_reliability": {
  "rounds_1_4": {
    "reliable_positions": [1, 2, 3, 4]  // Or [1, 2, 3] to exclude P4
  },
  "rounds_2_3": {
    "reliable_positions": [1, 2]  // Or [1] for maximum reliability
  }
}
```

---

## Common Use Cases

### Use Case 1: Analyze Machines at a Specific Venue

**Goal:** Get score distributions for all machines currently at 4Bs Tavern (season 22 only).

**Config:** `reports/configs/4bs_machines_config.json`
```json
{
  "season": "22",
  "target_machine": ["MM", "TZ", "Godzilla", "IronMaiden", "Jaws"],
  "target_venue": "T4B",
  "ipr_filter": null,
  "outlier_filter": null
}
```

**Command:**
```bash
python3 reports/generators/score_percentile_report.py reports/configs/4bs_machines_config.json
```

---

### Use Case 2: Compare Two Teams

**Goal:** Compare Trolls! vs Slap Kraken Pop on specific machines across all venues.

**Config:** `reports/configs/trolls_vs_slapkrakenpop_config.json`
```json
{
  "season": "22",
  "team1": {"key": "TRL", "name": "Trolls!"},
  "team2": {"key": "SKP", "name": "Slap Kraken Pop"},
  "target_machines": ["MM", "TZ", "Godzilla"]
}
```

**Command:**
```bash
python3 reports/generators/team_machine_comparison_report.py reports/configs/trolls_vs_slapkrakenpop_config.json
```

---

### Use Case 3: Analyze Team Machine Choices

**Goal:** See which machines Slap Kraken Pop chooses vs which they're forced to play.

**Config:** `reports/configs/skp_machine_choices_config.json`
```json
{
  "seasons": ["21", "22"],
  "team": {"key": "SKP", "name": "Slap Kraken Pop"},
  "home_venue_key": "KRA",
  "target_machines": ["MM", "TZ", "Godzilla"]
}
```

**Command:**
```bash
python3 reports/generators/team_machine_choice_report.py reports/configs/skp_machine_choices_config.json
```

---

### Use Case 4: Advanced Players Only

**Goal:** Score distributions for IPR 4-6 players only.

**Config:**
```json
{
  "season": "22",
  "target_machine": "MM",
  "target_venue": null,
  "ipr_filter": {"min_ipr": 4, "max_ipr": 6}
}
```

---

### Use Case 5: Team Performance at Home Venue

**Goal:** Analyze which machines DTP performs best on at their home venue (Jupiter).

**Config:** `reports/configs/dtp_jupiter_performance_config.json`
```json
{
  "season": "22",
  "team": {"key": "DTP", "name": "DTP"},
  "team_home_venue_key": "JUP",
  "target_venue": {"key": "JUP", "name": "Jupiter"}
}
```

**Command:**
```bash
python3 reports/generators/team_venue_machine_performance_report.py reports/configs/dtp_jupiter_performance_config.json
```

---

## Key Reference Data

### Important Venue Codes

| Code | Venue Name | Notes |
|------|------------|-------|
| T4B | 4Bs Tavern | Frequently analyzed venue |
| KRA | Kraken | Home venue for Slap Kraken Pop |
| 8BT | 8-bit Arcade Bar | Large machine collection |
| AAB | Add-a-Ball | Home venue for Add-a-Ballers |
| JUP | Jupiter | Large machine collection |
| OLF | Olaf's | Large machine collection |
| SHR | Shorty's | Downtown Seattle venue |

### Important Team Keys

| Code | Team Name | Notes |
|------|-----------|-------|
| SKP | Slap Kraken Pop | Home venue: KRA |
| TRL | Trolls! | Frequently analyzed team |
| ADB | Add-a-Ballers | Home venue: AAB |
| JMF | Jupiter Morning Folks | Home venue: JUP |
| DTP | DTP | Home venue: JUP |

### Common Machine Keys

Full list in [machine_variations.json](../machine_variations.json). Examples:

| Key | Machine Name |
|-----|--------------|
| MM | Medieval Madness |
| TZ | Twilight Zone |
| AFM | Attack From Mars |
| TOTAN | Tales of the Arabian Nights |
| TOM | Theatre of Magic |
| Godzilla | Godzilla (Stern) |
| IronMaiden | Iron Maiden |
| Jaws | Jaws |
| JW | John Wick |
| SDND | Dungeons and Dragons (Stern) |
| SternWars | Star Wars (Stern) |
| StrangerThings | Stranger Things |

---

## Output Locations

### Charts
- **Location:** `reports/charts/`
- **Format:** PNG (300 DPI)
- **Naming:** `{machine}_percentile_season_{season}_{venue}.png`
- **Aggregate:** `aggregate_grid_percentile_season_{season}_{venue}.png`

### Reports
- **Location:** `reports/output/`
- **Format:** Markdown
- **Naming Patterns:**
  - Score percentile: `{machine}_percentile_season_{season}_{venue}.md`
  - Venue summary: `{venue}_venue_summary_season_{season}.md`
  - Team comparison: `team_comparison_{team1}_vs_{team2}_season_{season}.md`
  - Machine choices: `machine_choices_{team}_seasons_{seasons}.md`

---

## Extending the Report Generators

### Creating a New Report Generator

1. **Copy an existing generator** as a template
2. **Modify the `__init__` method** to load your config structure
3. **Update the extraction logic** to filter/process data as needed
4. **Customize the report output** format
5. **Create a config file** in `reports/configs/`
6. **Test thoroughly** with known data

### Common Patterns to Reuse

#### Machine Name Normalization
```python
def normalize_machine_key(self, machine_key: str) -> str:
    """Normalize machine key using alias mapping."""
    if machine_key in self.machine_aliases:
        return self.machine_aliases[machine_key]
    return machine_key.strip()
```

#### Player Lookup Building
```python
match_players = {}
for team_type in ['home', 'away']:
    for player in match[team_type].get('lineup', []):
        match_players[player['key']] = {
            'name': player['name'],
            'team': match[team_type]['key'],
            'ipr': player.get('IPR', 0)
        }
```

#### Venue Filtering
```python
if self.target_venues:
    if match_data.get('venue', {}).get('key') not in self.target_venues:
        continue
```

---

## Troubleshooting

### Common Issues

**Issue:** No scores found for machine
- Check machine key spelling (case-sensitive)
- Verify machine was played in specified season/venue
- Check machine_variations.json for correct key

**Issue:** Empty reports
- Verify venue code is correct
- Check season number
- Ensure matches are marked as complete

**Issue:** Incorrect team data
- Verify team key (3-letter code)
- Check team played in specified season
- Ensure match files have complete lineup data

---

## Best Practices

1. **Always use venue codes from venues.json**
2. **Always use machine keys from machine_variations.json**
3. **Test configs with small datasets first**
4. **Document custom configs with `_notes` field**
5. **Use meaningful config filenames** (e.g., `skp_season22_4bs.json`)
6. **Back up generated reports** before regenerating
7. **Use IPR filtering carefully** - may reduce sample size significantly
8. **Consider outlier filtering** for percentile charts with extreme values

---

## LLM-Specific Notes

When assisting with report generation:

1. **Always check existing configs** in `reports/configs/` before creating new ones
2. **Verify venue/team codes** against `venues.json` and match files
3. **Use machine_variations.json** for machine key lookups
4. **Reference this README** for config patterns
5. **Check [MNP_Match_Data_Analysis_Guide.md](../MNP_Match_Data_Analysis_Guide.md)** for filtering patterns
6. **Suggest appropriate generator** based on user's analysis goals
7. **Validate config structure** before running generators
8. **Provide full command** with config file path

---

**Last Updated:** 2025-11-11
**Maintained by:** JJC
**For Data Structure Reference:** See [MNP_Data_Structure_Reference.md](../MNP_Data_Structure_Reference.md)
**For Analysis Patterns:** See [MNP_Match_Data_Analysis_Guide.md](../MNP_Match_Data_Analysis_Guide.md)
