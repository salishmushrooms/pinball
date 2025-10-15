# MNP & Pinball Rules Project Guide

## Project Overview

This repository contains two main components:

1. **MNP Data Archive**: Minnesota Pinball League match data, analytics, and reporting tools
2. **Pinball Rules Documentation**: LLM-friendly pinball machine rulesheets and strategy guides

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

/Users/JJC/Library/Mobile Documents/com~apple~CloudDocs/pinball-rules/
├── games/                      # Game rulesheets
│   ├── {game}-original.md     # Source rulesheets
│   ├── {game}.json            # LLM-optimized structured data
│   └── {game}-quick-reference.md (future)
├── docs/
│   ├── rulesheet-template.md  # JSON template (old format)
│   └── template-examples/     # Reference examples
├── WORKFLOW.md                 # Documentation creation workflow
└── machine_variations.json     # Machine key lookups
```

---

## 1. MNP Data Archive (League Data)

### Purpose
Analyze Minnesota Pinball League match data including scores, teams, venues, and player performance.

### Key Files

**Data Reference Guides:**
- `MNP_Data_Structure_Reference.md` - Overview of data structure and file organization
- `MNP_Match_Data_Analysis_Guide.md` - Detailed analysis guide with scoring mechanics
- `README.md` - High-level project overview

**Data Files:**
- `mnp-data-archive/season-XX/matches/*.json` - Individual match files
- `mnp-data-archive/machines.json` - Machine definitions and names
- `mnp-data-archive/venues.json` - Venue information
- `mnp-data-archive/IPR.csv` - Individual Player Ratings

**Machine Lookups:**
- `machine_variations.json` - Maps machine keys to full names and variations

### Report Generation

Located in `reports/` directory:
- `generators/` - Python scripts for generating reports
- `configs/` - Configuration files for report parameters

Common report generators:
- `venue_summary_report.py` - Venue-specific analysis
- `score_percentile_report.py` - Score distribution analysis
- Various home advantage analysis scripts

### Match Data Structure

Matches follow this pattern:
- **File naming**: `mnp-{season}-{week}-{away}-{home}.json`
- **4 rounds**: Round 1 & 4 (doubles, 4 players), Round 2 & 3 (singles, 2 players)
- **Scoring**: Points awarded based on head-to-head performance
- **Teams**: Each team plays 5 home and 5 away matches per season

### Important Notes

- **Player 4 scores in doubles may be unreliable** (early game completion)
- **Scores are NOT comparable across different machines** (use percentiles)
- **Home venue advantage exists** - see analysis guides for details

---

## 2. Pinball Rules Documentation

### Purpose
Create comprehensive, LLM-friendly rulesheets for pinball machines that support:
- AI-assisted strategy recommendations
- Quick reference for players
- Structured learning for new players

### Key Files

**Workflow & Templates:**
- `/Users/JJC/Library/Mobile Documents/com~apple~CloudDocs/pinball-rules/WORKFLOW.md` - **Primary workflow document** for creating rulesheets
- `docs/rulesheet-template.md` - JSON template structure (older format)
- `docs/template-examples/` - Reference examples for strategic documentation

**Machine Documentation:**
Located in `/Users/JJC/Library/Mobile Documents/com~apple~CloudDocs/pinball-rules/games/`:
- `{game}-original.md` - Source rulesheet from community (Tilt Forums, Pinside, etc.)
- `{game}.json` - LLM-optimized structured rules and strategy
- `{game}-quick-reference.md` - Mobile-friendly quick reference (future)

**Current Games Documented:**
- James Bond 007 (Stern 2022)
- King Kong: Myth of Terror Island (reference template)

### Documentation Workflow

When creating new game documentation:

1. **Collect Source** (`{game}-original.md`)
   - Source from Tilt Forums Wiki, official rulesheets, or Pinside
   - Include source URL and code revision
   - Preserve all original details

2. **Create Structured JSON** (`{game}.json`)
   - Use WORKFLOW.md as primary guide
   - Reference `king-kong.json` for structure
   - Focus on beginner-friendly quick_start_guide section
   - Include strategic context ("why" not just "what")

3. **Create Quick Reference** (`{game}-quick-reference.md`) *(future)*
   - Mobile-optimized formatting
   - Opening strategy first
   - Emoji markers for scanning
   - Checkboxes for actionable items

### JSON Structure Sections

Key sections in game JSON files:
- `overview` - Game summary and core loop
- `basic_scoring` - Shot values and lane awards
- `skill_shots` - All skill shot types and execution
- `modes` - Villain, henchmen, timed modes, etc.
- `multiball` - Qualification, jackpots, strategy
- `bond_women_and_007_scoring` (or equivalent game-specific features)
- `smart_missiles` (or equivalent game-specific features)
- `wizard_modes` - Mini-wizards and final wizard
- `strategy_guide` - Beginner/intermediate/advanced approaches

### Machine Key Lookups

**In MNP context:** Use `/Users/JJC/Pinball/MNP/machine_variations.json`
- Maps abbreviations (e.g., "MM", "AFM", "007") to full names
- Includes common variations and alternate spellings
- Used for data analysis and match tracking

**In Pinball Rules context:** Use `/Users/JJC/Library/Mobile Documents/com~apple~CloudDocs/pinball-rules/machine_variations.json` (if exists)
- Same purpose but for rules documentation

---

## Common Tasks

### MNP Data Analysis

**Generate a venue report:**
```bash
python reports/generators/venue_summary_report.py
```

**Generate percentile analysis:**
```bash
python reports/generators/score_percentile_report.py
```

**Find machine key:**
1. Check `machine_variations.json`
2. Search for machine name or abbreviation
3. Use `key` field for match data queries

### Pinball Rules Creation

**Start new game documentation:**
1. Read `WORKFLOW.md` thoroughly
2. Collect original rulesheet → `games/{game}-original.md`
3. Create structured JSON → `games/{game}.json` (use king-kong.json as template)
4. Focus on `quick_start_guide` section first
5. Validate JSON syntax
6. Cross-reference with original for accuracy

**Review existing game:**
1. Read `-original.md` for source material
2. Compare with `.json` for accuracy
3. Check completeness of all sections
4. Verify strategic guidance makes sense

---

## File Location Quick Reference

### MNP Data Files
- **Project root**: `/Users/JJC/Pinball/MNP/`
- **Data archive**: `mnp-data-archive/` (relative to project root)
- **Reports**: `reports/` (relative to project root)
- **Reference docs**: Root level `.md` files

### Pinball Rules Files
- **Rules root**: `/Users/JJC/Library/Mobile Documents/com~apple~CloudDocs/pinball-rules/`
- **Games**: `games/` (relative to rules root)
- **Templates**: `docs/` (relative to rules root)
- **Workflow**: `WORKFLOW.md` (at rules root)

---

## Important Conventions

### MNP Data
- Match files: `mnp-{season}-{week}-{away}-{home}.json`
- Team keys: 3-letter abbreviations (e.g., "ADB", "JMF")
- Venue keys: 3-4 letter codes (e.g., "JUP", "T4B")
- Machine keys: Abbreviations from `machine_variations.json`

### Pinball Rules
- Game files: `{game-name}-{type}.{ext}`
- Types: `original` (source), base name (structured JSON), `quick-reference` (mobile)
- JSON: Valid syntax, no trailing commas
- Strategy: Action-oriented language ("Shoot X" not "X can be shot")
- Focus: Beginner-first, with progressive depth

---

## Key Principles

### MNP Analysis
1. **Score normalization**: Use percentiles, not raw scores across machines
2. **Data reliability**: Player 1 > Player 2 > Player 3 > Player 4
3. **Home advantage**: Real and measurable - account for it
4. **Machine variance**: Some machines are high-variance, others consistent

### Pinball Documentation
1. **Beginner-first**: Quick start guide is most critical section
2. **Action-oriented**: Tell players what to DO, not just what exists
3. **Strategic context**: Always explain WHY, not just WHAT
4. **Accuracy**: Cross-reference original sources meticulously
5. **LLM-optimized**: Structured for AI parsing and recommendation

---

## Tools & Technologies

**MNP Analysis:**
- Python for report generation
- JSON for match data storage
- CSV for tabular data (venues, IPR, matches overview)

**Pinball Rules:**
- Markdown for original rulesheets and quick references
- JSON for structured, LLM-parseable rules
- Reference: Tilt Forums Wiki, manufacturer rulesheets, Pinside

---

## Getting Help

**For MNP Data Questions:**
- Read `MNP_Data_Structure_Reference.md` for structure
- Read `MNP_Match_Data_Analysis_Guide.md` for analysis guidance
- Check `machine_variations.json` for machine lookups

**For Pinball Rules Questions:**
- Read `WORKFLOW.md` first - **primary workflow document**
- Reference `king-kong.json` for structure examples
- Check `docs/template-examples/` for strategic documentation patterns
- Original rulesheets in `games/*-original.md` for source material

---

## Current Status

**MNP Data:**
- Season 21 data available
- Multiple report generators created
- Home advantage analysis in progress

**Pinball Rules:**
- Workflow established (WORKFLOW.md)
- King Kong complete (reference template)
- James Bond 007: JSON exists, needs verification
- Template structure evolving based on King Kong example

---

## Next Steps

**MNP:**
- Continue developing analysis reports
- Refine home advantage metrics
- Expand machine-specific analysis

**Pinball Rules:**
- Verify James Bond 007 JSON accuracy and completeness
- Format James Bond original.md for easier navigation
- Continue documenting additional machines
- Evolve template based on learnings

---

**Last Updated**: 2025-01-03
**Maintained by**: JJC
**LLM Context**: This file helps Claude understand project structure for future sessions
