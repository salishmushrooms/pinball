# MNP Data Archive Project Guide

## Project Overview

This repository contains Monday Night Pinball (MNP) match data, analytics, and reporting tools. It includes a full-stack web application (FastAPI + Next.js), ETL pipelines for loading match data, and Python-based report generators for statistical analysis.

---

## Directory Structure

```
/Users/JJC/Pinball/MNP/
├── api/                        # FastAPI backend
│   ├── main.py                 # App entry point
│   ├── routers/                # API endpoints (8 routers)
│   ├── models/                 # Pydantic schemas
│   ├── services/               # Business logic (matchplay, player matching)
│   └── requirements.txt
├── frontend/                   # Next.js 16 frontend
│   ├── app/                    # App router pages (6 main + detail pages)
│   ├── components/             # React components
│   │   ├── ui/                 # 16 reusable UI components
│   │   └── *.tsx               # 6 specialized components
│   └── lib/                    # API client & types
├── etl/                        # Data pipeline
│   ├── load_season.py          # Load season data
│   ├── calculate_*.py          # Aggregate calculations (5 scripts)
│   ├── update_ipr.py           # Update IPR ratings
│   ├── parsers/                # Data parsers (match, machine, ipr)
│   ├── loaders/                # Database loaders
│   └── database.py             # DB connection
├── schema/                     # Database schema
│   ├── 001_complete_schema.sql # Consolidated schema
│   └── migrations/             # 8 SQL migrations
├── mnp-data-archive/           # League data (git submodule)
│   ├── season-14/ to season-22/  # 9 seasons of match data
│   ├── machines.json
│   ├── venues.json
│   └── IPR.csv
├── mnp-app-docs/               # Comprehensive deployment docs
│   ├── DATABASE_OPERATIONS.md
│   ├── DEPLOYMENT_CHECKLIST.md
│   ├── api/endpoints.md        # API documentation
│   └── database/schema.md      # Schema documentation
├── reports/                    # Analysis and report generation
│   ├── generators/             # 15 Python report generators
│   ├── configs/                # 23 JSON config files
│   ├── output/                 # Generated markdown reports
│   └── charts/                 # Generated PNG visualizations
├── docs/                       # Additional documentation
├── Procfile                    # Railway start command
├── railway.toml                # Railway config
├── vercel.json                 # Vercel deployment config
└── requirements.txt            # Python dependencies (root)
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

**Core Reports:**
1. **score_percentile_report.py** - Score distribution analysis
   - Generates percentile charts for machines
   - Supports venue filtering, IPR filtering, multi-season analysis
   - Creates aggregate grid images for multiple machines

2. **venue_summary_report.py** - Venue-specific analysis
   - Machine statistics at specific venues
   - High scores, selection patterns, round analysis

3. **team_machine_comparison_report.py** - Team vs team comparison
   - Compare two teams' performance on specific machines
   - Scores from all venues (no venue filtering)

4. **team_machine_choice_report.py** - Machine selection analysis
   - Track when team picked machines vs opponent picked

**Home Advantage Analysis:**
5. **home_advantage_ipr_analysis.py** - IPR-based home advantage
6. **home_advantage_ipr_analysis_points.py** - Points-based analysis
7. **home_away_advantage_report.py** - General home/away comparison
8. **venue_home_advantage_analysis.py** - Per-venue home advantage
9. **venue_controlled_ipr_analysis.py** - Controlled IPR analysis

**Team Analysis:**
10. **team_venue_machine_performance_report.py** - Team performance at venues
11. **team_venue_pick_frequency_report.py** - Machine pick frequency

**Utility Reports:**
12. **score_percentile_report_exclude_venues.py** - Percentiles with venue exclusions
13. **find_missing_machines.py** - Identify missing machine data
14. **prediction_data_audit.py** - Audit prediction data quality

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

### Frontend Development
1. **Component Reuse**: Always check for existing reusable components before creating new ones
   - Check `frontend/components/` for specialized components (e.g., SeasonMultiSelect)
   - Check `frontend/components/ui/` for base UI components (Button, Card, Select, etc.)
   - When creating new components, design them to be reusable across multiple pages
   - Document reusable components so they can be easily discovered
2. **Consistent Patterns**: Follow established patterns from DESIGN_SYSTEM.md
3. **Type Safety**: Use TypeScript types from `lib/types.ts` for all API interactions
4. **Design System**: Import from `@/components/ui` for all standard UI elements

---

## Tools & Technologies

### Backend
- **Python 3.12** for ETL, API, and report generation
- **FastAPI** for REST API
- **PostgreSQL 15** for database
- **SQLAlchemy** for ORM

### Frontend
- **Next.js 16** with App Router
- **React 19** with TypeScript
- **Tailwind CSS v4** for styling

### Data Storage
- **JSON** for match data files
- **CSV** for tabular data (IPR ratings, team rosters)
- **PostgreSQL** for application data

### Deployment
- **Railway** for API and PostgreSQL hosting ($5/month)
- **Vercel** for frontend hosting

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

### Production Deployment ✅ LIVE
- **API:** https://pinball-production.up.railway.app
- **Frontend:** Deployed on Vercel
- **Database:** PostgreSQL on Railway
- **Cost:** $5/month (Railway Hobby)

### Data Available
- **Seasons 14-22** in mnp-data-archive (9 seasons total)
- **Seasons 18-22** loaded in production database
- **943 matches**, **56,504 scores**, **938 players**

### Report Generators
- **14 specialized report generators** covering:
  - Score percentile analysis (multi-machine, multi-season)
  - Venue summary and home advantage analysis
  - Team comparison and machine choice analysis
  - IPR-controlled analysis

### Frontend Application
- **16 UI components** in `components/ui/`
- **6 specialized components** (SeasonMultiSelect, RoundMultiSelect, etc.)
- **6 main pages** with detail views (players, teams, machines, venues, matchups)
- **Multi-season support**: All pages support analyzing data across multiple seasons
- **API**: Fully typed TypeScript API client with array parameter support

### API Endpoints
8 routers providing endpoints for:
- Players, Teams, Machines, Venues, Seasons
- Matchups and predictions
- Matchplay integration (external API)

---

## Production Operations

### Adding New Season Data
See [mnp-app-docs/DATABASE_OPERATIONS.md](mnp-app-docs/DATABASE_OPERATIONS.md) for:
- Loading new season data (e.g., Season 23)
- Running ETL pipelines
- Exporting/importing to production database

### Quick Commands
```bash
# Connect to production database
railway connect postgres

# View API logs
railway logs -s pinball

# Export local data
pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > /tmp/mnp_data.sql

# Import to production
railway connect postgres < /tmp/mnp_data.sql
```

### Key Configuration
- **Railway:** Deploy from repo root (not api/), Target Port: 8080
- **Vercel:** Root Directory: frontend, Env: NEXT_PUBLIC_API_URL

---

**Last Updated**: 2025-12-10
**Maintained by**: JJC
**LLM Context**: This file helps Claude understand the MNP data analysis project structure

---

## Development Environment

### Quick Start
```bash
# Activate Python environment
conda activate mnp

# Start API (from repo root)
cd /Users/JJC/Pinball/MNP
uvicorn api.main:app --reload --port 8000

# Start frontend (separate terminal)
cd /Users/JJC/Pinball/MNP/frontend
npm run dev
```

### Database Access
```bash
# Local database
psql -h localhost -U mnp_user -d mnp_analyzer

# Production database (via Railway CLI)
railway connect postgres
```

### Environment Files
- `.env` - Local database credentials
- `frontend/.env.local` - Frontend API URL (`NEXT_PUBLIC_API_URL`)

---

## ETL Pipeline

### Loading Season Data
```bash
# Load a specific season
python etl/load_season.py --season 22

# Recalculate aggregates after loading
python etl/calculate_percentiles.py
python etl/calculate_player_stats.py
python etl/calculate_player_totals.py
python etl/calculate_team_machine_picks.py
python etl/calculate_match_points.py
```

### ETL Scripts
| Script | Purpose |
|--------|---------|
| `load_season.py` | Load match data from JSON files |
| `update_ipr.py` | Update IPR ratings from CSV |
| `calculate_percentiles.py` | Calculate score percentiles per machine |
| `calculate_player_stats.py` | Aggregate player statistics |
| `calculate_player_totals.py` | Calculate player totals |
| `calculate_team_machine_picks.py` | Track machine pick patterns |
| `calculate_match_points.py` | Calculate match point totals |

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

---

## API Structure

### Routers (api/routers/)
| Router | Purpose |
|--------|---------|
| `machines.py` | Machine data and percentiles |
| `matchplay.py` | External Matchplay.events integration |
| `matchups.py` | Team matchup predictions |
| `players.py` | Player stats and performance |
| `predictions.py` | Score predictions |
| `seasons.py` | Season metadata |
| `teams.py` | Team data and rosters |
| `venues.py` | Venue information and machines |

### Services (api/services/)
- `matchplay_client.py` - Client for Matchplay.events API
- `player_matcher.py` - Match player names across data sources

---

## Documentation Index

### In This Repository
| File | Purpose |
|------|---------|
| [DESIGN_SYSTEM.md](frontend/DESIGN_SYSTEM.md) | Frontend component design system |
| [MNP_Data_Structure_Reference.md](MNP_Data_Structure_Reference.md) | Match data JSON structure |
| [MNP_Match_Data_Analysis_Guide.md](MNP_Match_Data_Analysis_Guide.md) | Analysis methodology |
| [mnp-app-docs/DATABASE_OPERATIONS.md](mnp-app-docs/DATABASE_OPERATIONS.md) | Database operations guide |
| [mnp-app-docs/api/endpoints.md](mnp-app-docs/api/endpoints.md) | API endpoint documentation |
| [reports/README.md](reports/README.md) | Report generation guide |

### Git Submodule
The `mnp-data-archive/` directory is a git submodule. To update:
```bash
git submodule update --remote mnp-data-archive
```
