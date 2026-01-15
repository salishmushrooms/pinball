# MNP Project Structure - Detailed Directory Layout

> **Purpose**: Comprehensive directory structure reference for AI assistants
> **Last Updated**: 2026-01-02

---

## Complete Directory Tree

```
/Users/JJC/Pinball/MNP/
├── .claude/                           # LLM context documentation
│   ├── CLAUDE.md                      # Main context guide (THIS IS LOADED FIRST)
│   ├── MNP_MATCH_STRUCTURE.md         # Match JSON format reference
│   ├── PROJECT_STRUCTURE.md           # This file - detailed directory layout
│   ├── DEVELOPMENT_GUIDE.md           # Dev workflows & commands
│   ├── DATA_CONVENTIONS.md            # MNP-specific data patterns
│   └── settings.local.json            # Claude Code settings
│
├── api/                               # FastAPI backend application
│   ├── main.py                        # App entry point, CORS, router registration
│   ├── __init__.py
│   ├── requirements.txt               # API-specific Python dependencies
│   ├── routers/                       # API endpoint routers (8 total)
│   │   ├── __init__.py
│   │   ├── machines.py                # Machine data, percentiles, statistics
│   │   ├── matchplay.py               # Matchplay.events integration
│   │   ├── matchups.py                # Team matchup predictions
│   │   ├── players.py                 # Player stats, performance data
│   │   ├── predictions.py             # Score predictions
│   │   ├── seasons.py                 # Season metadata
│   │   ├── teams.py                   # Team data, rosters
│   │   └── venues.py                  # Venue info, machines at venues
│   ├── models/                        # Pydantic schemas for API
│   │   ├── __init__.py
│   │   └── [various model files]
│   └── services/                      # Business logic services
│       ├── __init__.py
│       ├── matchplay_client.py        # Matchplay.events API client
│       └── player_matcher.py          # Match player names across sources
│
├── frontend/                          # Next.js 16 frontend application
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── .env.local                     # Frontend environment variables
│   ├── DESIGN_SYSTEM.md               # Component design patterns
│   ├── app/                           # Next.js App Router pages
│   │   ├── layout.tsx                 # Root layout
│   │   ├── page.tsx                   # Home page
│   │   ├── players/                   # Players list & detail pages
│   │   │   ├── page.tsx               # Players list
│   │   │   └── [key]/page.tsx         # Player detail
│   │   ├── teams/                     # Teams list & detail pages
│   │   │   ├── page.tsx
│   │   │   └── [key]/page.tsx
│   │   ├── machines/                  # Machines list & detail pages
│   │   │   ├── page.tsx
│   │   │   └── [key]/page.tsx
│   │   ├── venues/                    # Venues list & detail pages
│   │   │   ├── page.tsx
│   │   │   └── [key]/page.tsx
│   │   └── matchups/                  # Matchup predictions
│   │       └── page.tsx
│   ├── components/                    # React components
│   │   ├── ui/                        # Reusable UI components (19 total)
│   │   │   ├── Alert.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Collapsible.tsx
│   │   │   ├── ContentContainer.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── FilterPanel.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── MultiSelect.tsx
│   │   │   ├── MultiSelectDropdown.tsx
│   │   │   ├── PageHeader.tsx
│   │   │   ├── README.md              # Component usage guide
│   │   │   ├── Select.tsx
│   │   │   ├── StatCard.tsx
│   │   │   ├── Table.tsx
│   │   │   ├── Tabs.tsx
│   │   │   ├── TruncatedText.tsx
│   │   │   └── index.ts               # Barrel exports
│   │   ├── Navigation.tsx             # Main navigation
│   │   ├── RoundMultiSelect.tsx       # Multi-select for rounds
│   │   ├── SeasonMultiSelect.tsx      # Multi-select for seasons
│   │   ├── TeamBadge.tsx              # Team display badge
│   │   ├── TeamSelect.tsx             # Team selection dropdown
│   │   └── VenueSelect.tsx            # Venue selection dropdown
│   └── lib/                           # Utilities and API client
│       ├── api.ts                     # API client with typed endpoints
│       ├── types.ts                   # TypeScript type definitions
│       └── utils.ts                   # Helper functions
│
├── etl/                               # Data pipeline scripts
│   ├── database.py                    # Database connection utilities
│   ├── load_season.py                 # Main script: load season data
│   ├── update_ipr.py                  # Update IPR ratings from CSV
│   ├── calculate_percentiles.py       # Calculate score percentiles
│   ├── calculate_player_stats.py      # Aggregate player statistics
│   ├── calculate_player_totals.py     # Calculate player totals
│   ├── calculate_team_machine_picks.py # Track machine selection patterns
│   ├── calculate_match_points.py      # Calculate match point totals
│   ├── parsers/                       # Data parsing modules
│   │   ├── __init__.py
│   │   ├── match_parser.py            # Parse match JSON files
│   │   ├── machine_parser.py          # Parse machine definitions
│   │   └── ipr_parser.py              # Parse IPR CSV files
│   └── loaders/                       # Database loading modules
│       ├── __init__.py
│       ├── match_loader.py            # Load matches to database
│       ├── player_loader.py           # Load players to database
│       └── score_loader.py            # Load scores to database
│
├── schema/                            # Database schema and migrations
│   ├── 001_complete_schema.sql        # Consolidated schema (current)
│   └── migrations/                    # Historical SQL migrations
│       ├── 001_initial_schema.sql
│       ├── 002_add_percentiles.sql
│       ├── 003_add_player_stats.sql
│       ├── 004_add_team_picks.sql
│       ├── 005_add_match_points.sql
│       ├── 006_add_indexes.sql
│       ├── 007_add_venue_machines.sql
│       └── 008_add_ipr_data.sql
│
├── mnp-data-archive/                  # Git submodule - league data
│   ├── season-14/                     # Season 14 data
│   │   └── matches/*.json
│   ├── season-15/                     # Season 15 data
│   │   └── matches/*.json
│   ├── season-16/ ... season-22/      # Seasons 16-22 data
│   ├── machines.json                  # Machine definitions
│   ├── venues.json                    # Venue information
│   └── IPR.csv                        # Individual Player Ratings
│
├── mnp-app-docs/                      # Comprehensive documentation
│   ├── README.md                      # Docs overview
│   ├── DATABASE_OPERATIONS.md         # Database operations guide
│   ├── DEPLOYMENT_CHECKLIST.md        # Deployment checklist
│   ├── DEPLOYMENT_PLAN.md             # Deployment planning
│   ├── IMPLEMENTATION_ROADMAP.md      # Historical implementation roadmap
│   ├── SESSION_SUMMARY.md             # Development session notes
│   ├── api/                           # API documentation
│   │   └── endpoints.md               # Complete API reference
│   ├── database/                      # Database documentation
│   │   └── schema.md                  # Database schema reference
│   ├── data-pipeline/                 # ETL documentation
│   │   └── etl-process.md             # ETL process documentation
│   └── frontend/                      # Frontend documentation
│       └── ui-design.md               # UI design specifications
│
├── docs/                              # Additional project documentation
│   ├── IPR_CALCULATOR_PLANNING.md     # IPR calculator planning (future)
│   ├── MATCHPLAY_INTEGRATION_PLAN.md  # Matchplay integration notes
│   ├── PERFORMANCE_IMPROVEMENTS.md    # Performance optimization notes
│   └── TASKS_DEC_11.md                # Task tracking (historical)
│
├── reports/                           # Report generation (ARCHIVED)
│   ├── generators/                    # Python report generators
│   │   └── (archived - no longer maintained)
│   ├── configs/                       # Report configuration files
│   │   └── (archived)
│   ├── output/                        # Generated reports (.gitignored)
│   └── charts/                        # Generated charts (.gitignored)
│
├── .env                               # Environment variables (gitignored)
├── .gitignore                         # Git ignore rules
├── .gitmodules                        # Git submodule configuration
├── Procfile                           # Railway deployment command
├── railway.toml                       # Railway configuration
├── vercel.json                        # Vercel deployment config
├── requirements.txt                   # Root Python dependencies
├── README.md                          # Main project README
├── MNP_Data_Structure_Reference.md    # Data structure overview
├── MNP_Match_Data_Analysis_Guide.md   # Analysis methodology guide
├── machine_variations.json            # Machine name lookup table
├── DATA_UPDATE_STRATEGY.md            # Data update strategy (operational)
├── RESTART_GUIDE.md                   # Project restart guide (operational)
├── SETUP_GUIDE.md                     # Initial setup guide
├── SYNC_CHECKLIST.md                  # Multi-computer sync checklist
├── UPDATE_DATABASE_GUIDE.md           # Database update guide
└── WORKING_ACROSS_COMPUTERS.md        # Multi-computer workflow guide

```

---

## Key Directories Explained

### `.claude/` - LLM Context
Documentation specifically for AI assistants. Loaded as context for every conversation.
- **CLAUDE.md**: Main entry point - essential context only
- **MNP_MATCH_STRUCTURE.md**: Detailed match JSON format
- **PROJECT_STRUCTURE.md**: This file - directory layout
- **DEVELOPMENT_GUIDE.md**: Common development workflows
- **DATA_CONVENTIONS.md**: MNP-specific data patterns

### `api/` - Backend Application
FastAPI REST API serving data to frontend and external consumers.
- **8 routers**: machines, matchplay, matchups, players, predictions, seasons, teams, venues
- **Services**: External integrations (Matchplay.events), player matching
- **Models**: Pydantic schemas for request/response validation

### `frontend/` - Web Application
Next.js 16 frontend with React 19 and TypeScript.
- **6 main page routes**: players, teams, machines, venues, matchups, home
- **19 reusable UI components**: Button, Card, Table, Select, etc.
- **Specialized components**: SeasonMultiSelect, RoundMultiSelect, TeamBadge
- **Type-safe API client**: Full TypeScript typing for all endpoints

### `etl/` - Data Pipeline
Python scripts for loading and transforming match data.
- **load_season.py**: Primary data loading script
- **calculate_*.py**: Aggregate calculations (percentiles, stats, totals)
- **parsers/**: Parse JSON/CSV source files
- **loaders/**: Load parsed data into PostgreSQL

### `schema/` - Database Schema
PostgreSQL schema definitions and migrations.
- **001_complete_schema.sql**: Current consolidated schema
- **migrations/**: Historical incremental migrations (for reference)

### `mnp-data-archive/` - Source Data (Git Submodule)
Raw league data in JSON/CSV format.
- **Seasons 14-22**: 9 seasons of match data
- **machines.json**: Machine definitions and variations
- **venues.json**: Venue information
- **IPR.csv**: Individual Player Ratings

### `mnp-app-docs/` - Comprehensive Documentation
Detailed documentation for development and deployment.
- **DATABASE_OPERATIONS.md**: Database management guide
- **DEPLOYMENT_CHECKLIST.md**: Production deployment steps
- **api/endpoints.md**: Complete API reference
- **database/schema.md**: Database schema documentation

### `reports/` - Archived Report Generators
**ARCHIVED - No longer actively maintained.**
Historical Python scripts for generating statistical reports. All active analysis now happens through the web application.

---

## File Naming Conventions

### Match Data Files
```
mnp-{season}-{week}-{away_team}-{home_team}.json
Example: mnp-22-01-TRL-SKP.json
```

### Environment Files
```
.env                  # Root environment (database credentials) - gitignored
frontend/.env.local   # Frontend environment (API URL) - gitignored
```

### Config Files
```
Procfile              # Railway deployment command
railway.toml          # Railway service configuration
vercel.json           # Vercel deployment settings
requirements.txt      # Root Python dependencies
api/requirements.txt  # API-specific dependencies
```

---

## Important Paths for Development

### Starting Services
```bash
# API
/Users/JJC/Pinball/MNP/
uvicorn api.main:app --reload --port 8000

# Frontend
/Users/JJC/Pinball/MNP/frontend/
npm run dev
```

### Database Connection
```bash
# Local
psql -h localhost -U mnp_user -d mnp_analyzer

# Production
railway connect postgres
```

### Loading Data
```bash
# From repo root
python etl/load_season.py --season 22
python etl/calculate_percentiles.py
```

---

## Ignored Directories

These directories are gitignored (not in version control):

```
.env                          # Environment secrets
frontend/.env.local           # Frontend environment
frontend/.next/               # Next.js build output
frontend/node_modules/        # npm dependencies
reports/output/               # Generated reports
reports/charts/               # Generated charts
api/__pycache__/              # Python bytecode
etl/__pycache__/              # Python bytecode
*.pyc                         # Python bytecode files
.DS_Store                     # macOS files
```

---

## Component Count Summary

- **API Routers**: 8
- **Frontend Pages**: 6 main routes (+ detail pages)
- **UI Components**: 19 reusable components
- **Specialized Components**: 6 (SeasonMultiSelect, RoundMultiSelect, etc.)
- **ETL Scripts**: 8 main scripts
- **Database Migrations**: 8 historical migrations
- **Documentation Files**: 20+ markdown files

---

**Note**: This structure reflects the current state as of 2026-01-02. The project is in active production use with ongoing development.
