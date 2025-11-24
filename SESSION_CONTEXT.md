# MNP Analyzer - Session Context

**Document Purpose**: Quick-start context for resuming development sessions

**Last Updated**: 2025-11-24 11:40 PST

**Current Status**: Week 2, Day 2 Complete ✅ | FastAPI REST API Built & Tested

---

## 🎯 Where We Are Now

### Completed (Week 1)
- ✅ PostgreSQL database fully set up with 13 tables
- ✅ Complete ETL pipeline built and tested
- ✅ Season 22 data successfully loaded:
  - 341 machines | 19 venues | 34 teams | 523 players
  - 184 matches | 3,916 games | 10,680 scores
- ✅ All data quality issues resolved

### Completed (Week 2, Day 1)
- ✅ **Score Percentiles Calculated** - 980 percentile records for 140 machines
- ✅ **Player Stats Calculated** - 5,942 player/machine combinations analyzed
- ✅ **Data Quality Verified** - Outliers identified, distributions look correct
- ✅ Scripts created:
  - `etl/calculate_percentiles.py` - Calculate score percentiles per machine
  - `etl/calculate_player_stats.py` - Calculate player performance stats

### Completed (Week 2, Day 2)
- ✅ **FastAPI Project Created** - Complete API structure with routers, models, and dependencies
- ✅ **Player Endpoints** - 3 endpoints for player data (list, details, machine stats)
- ✅ **Machine Endpoints** - 4 endpoints for machine data (list, details, percentiles, raw percentiles)
- ✅ **Pydantic Models** - Type-safe request/response schemas
- ✅ **Auto-Generated Docs** - Swagger UI at http://localhost:8000/docs
- ✅ **All Endpoints Tested** - Verified data accuracy and proper error handling
- ✅ **Health Check** - Database connectivity monitoring at /health

### What's Next (Week 2, Day 3)
1. **Frontend Development** - Begin React/Next.js frontend
2. **Player Dashboard** - Create player profile and stats views
3. **Machine Browser** - Build machine search and percentile visualizations

---

## 🚀 Quick Start Commands

```bash
# Start working
cd /Users/test_1/Pinball/MNP/pinball
conda activate mnp

# Test database connection
python3 -c "from etl.database import db; db.connect(); print('✓ Connected')"

# Check data counts
/usr/local/opt/postgresql@15/bin/psql mnp_analyzer -c "
SELECT 'scores' as table, COUNT(*) FROM scores
UNION ALL SELECT 'players', COUNT(*) FROM players
UNION ALL SELECT 'matches', COUNT(*) FROM matches;
"

# Reload data if needed (takes ~10 seconds)
python3 etl/load_season.py --season 22

# Start API server
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Or run in background
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &

# Test API endpoints
curl http://localhost:8000/                    # Root endpoint
curl http://localhost:8000/health              # Health check
curl http://localhost:8000/players?limit=3     # List players
curl http://localhost:8000/machines?limit=3    # List machines

# Access API documentation
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

## 📊 Database Overview

**Connection**: `postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer`

**Key Tables**:
- `machines` - Pinball machines (341 total, some auto-created)
- `venues` - League venues (19 total)
- `teams` - Season teams (34 total)
- `players` - All players (523 total)
- `matches` - Match metadata (184 total)
- `games` - Individual games within matches (3,916 total)
- `scores` - Player scores (10,680 total)
- `score_percentiles` - ✅ **Populated** - 980 records (140 machines × 7 percentiles)
- `player_machine_stats` - ✅ **Populated** - 5,942 player/machine combinations

**Schema Version**: 1.0.0

---

## 🔧 ETL Pipeline Architecture

### Data Flow
```
machine_variations.json → machines + machine_aliases
        ↓
mnp-data-archive/season-22/matches/*.json
        ↓
   [Parser Layer]
   - machine_parser.py
   - match_parser.py
        ↓
   [Loader Layer]
   - db_loader.py
        ↓
    PostgreSQL
```

### Key Files
- `etl/load_season.py` - Main orchestrator
- `etl/parsers/match_parser.py` - Extract data from JSON files
- `etl/parsers/machine_parser.py` - Parse machine variations
- `etl/loaders/db_loader.py` - Insert into database
- `etl/database.py` - Database connection management
- `etl/config.py` - Configuration settings

### ETL Features
✅ **Auto-creates missing machines** when encountered in data
✅ **Skips incomplete games** without machine assignments
✅ **Handles IPR=0** by converting to NULL
✅ **No score caps** - all scores preserved for statistical analysis
✅ **Upsert logic** - can be re-run safely

---

## ⚠️ Important Data Quality Notes

### 1. Auto-Created Machines (9 total)
These machines were missing from `machine_variations.json`:
- "Scooby Doo"
- "Captain fantastic " (note trailing space)
- "Harry potter" / "Harry Potter " / "Harry Potter" (3 variants!)
- "TCM"
- "" (blank entry)
- "Woyal Wumble " / "Woyal Wumble" (2 variants)

**Action Needed**: Review and add proper metadata (manufacturer, year, game_type)

### 2. High Score Outliers (Preserved)
These scores are unusually high but preserved for analysis:
- **604,000,000,150** - Jeff Gagnon on Twilight Zone (mnp-22-9-HHS-SCN)
  - Likely data entry error (extra digit?)
- **15,329,686,730** - Evan Eckles on Star Wars/Stern (mnp-22-11-ETB-NLT)
  - Legitimately possible on this machine
- **10,837,792,110** - Chris Vela on Attack From Mars (mnp-22-8-SKP-PKT)
  - Legitimately possible on this machine

**Analysis Strategy**: 3-sigma outlier detection per machine will identify true anomalies

### 3. Incomplete Matches
Some matches have no games yet (future/unplayed):
- mnp-22-12-ADB-NLT (all rounds empty)
- Others may exist

**ETL Behavior**: Gracefully skips games without `machine` field

---

## 📝 Key Design Decisions

1. **No Score Cap** - All scores preserved; outliers flagged via statistics
2. **Auto-Create Machines** - Robust to incomplete machine_variations.json
3. **IPR Handling** - 0 → NULL (some players have no IPR yet)
4. **Conda Environment** - Using existing conda instead of venv
5. **Local PostgreSQL** - On host (not Docker) for simplicity
6. **Schema Version Tracking** - `schema_version` table tracks migrations

---

## ✅ Completed Tasks (Week 2, Day 1)

### Task 1: Score Percentiles ✅
**Completed**: `etl/calculate_percentiles.py` created and tested

**Results**:
- 140 machines with percentile data (out of 155 total)
- 15 machines skipped (insufficient data: <10 scores)
- 980 percentile records created (7 percentiles per machine)
- Percentiles calculated: 10th, 25th, 50th, 75th, 90th, 95th, 99th
- Sample sizes range from 10 to 474 scores per machine

**Usage**:
```bash
python3 etl/calculate_percentiles.py --season 22
```

### Task 2: Player Machine Statistics ✅
**Completed**: `etl/calculate_player_stats.py` created and tested

**Results**:
- 5,942 player/machine stat records created
- 523 unique players analyzed
- 155 unique machines covered
- Average games played per player/machine: 1.8
- Overall average percentile: 46.4 (well-balanced distribution)

**Usage**:
```bash
python3 etl/calculate_player_stats.py --season 22
```

### Data Quality Findings ✅
**Outliers Identified** (scores >2x the 99th percentile):
1. **Jeff Gagnon on Twilight Zone**: 604 billion (58,301% of p99)
   - Likely data entry error (extra digit)
2. **Rolo Carey on Willy Wonka**: 2.87 billion (14,503% of p99)
   - Extremely high, needs review
3. **Evan Eckles on Star Wars (Stern)**: 15.3 billion (219% of p99)
   - High but potentially legitimate for this machine

**Top Performers** (by average percentile, ≥60th percentile overall):
- Sean Irby: 95.9 avg percentile
- Scott Helgason: 87.9 avg percentile across 3 machines
- Lonnie Langford: 87.0 avg percentile across 2 machines

---

## 📚 Reference Documentation

### In This Repository
- `CURRENT_STATUS.md` - Detailed current status (this session)
- `PROGRESS.md` - Original progress tracking
- `mnp-app-docs/` - Complete architecture documentation
  - `database/schema.md` - Full schema documentation
  - `data-pipeline/etl-process.md` - ETL design
  - `IMPLEMENTATION_ROADMAP.md` - 9-week plan
  - `INDEX.md` - Navigation guide

### External References
- `MNP_Data_Structure_Reference.md` - Match JSON format guide
- `MNP_Match_Data_Analysis_Guide.md` - Analysis patterns
- `machine_variations.json` - Machine name → metadata mapping

---

## 🐛 Known Issues & Gotchas

### PostgreSQL Path
Sometimes `psql` isn't in PATH. Use full path:
```bash
/usr/local/opt/postgresql@15/bin/psql mnp_analyzer
```

### Conda in Scripts
When running Python scripts, conda may not activate properly:
```bash
# Use this pattern
source ~/.zshrc && conda activate mnp && python3 script.py

# Not just this
conda activate mnp && python3 script.py
```

### Machine Key Inconsistencies
- Some machines have trailing spaces: "Captain fantastic "
- Some have case variations: "Harry potter" vs "Harry Potter"
- One blank machine key: ""
- **Impact**: May need cleanup or aliasing

### Special Venue Key Convention
- **'_ALL_'** - Special venue_key used to represent global/aggregated stats across all venues
- Added to `venues` table to satisfy foreign key constraints
- Used in `score_percentiles` and `player_machine_stats` tables
- When venue_key = '_ALL_', data represents aggregate across all venues

### Score Data Type
Scores are stored as BIGINT (up to 9.2 quintillion)
- No artificial cap
- Can handle any legitimate pinball score
- Statistical outlier detection will flag anomalies

---

## 🔍 Useful Queries

### Check Data Completeness
```sql
SELECT
  'machines' as table, COUNT(*) as count FROM machines
  UNION ALL SELECT 'venues', COUNT(*) FROM venues
  UNION ALL SELECT 'teams', COUNT(*) FROM teams
  UNION ALL SELECT 'players', COUNT(*) FROM players
  UNION ALL SELECT 'matches', COUNT(*) FROM matches
  UNION ALL SELECT 'games', COUNT(*) FROM games
  UNION ALL SELECT 'scores', COUNT(*) FROM scores;
```

### Top Scores by Machine
```sql
SELECT
  m.machine_name,
  p.name,
  s.score,
  s.match_key
FROM scores s
JOIN machines m ON s.machine_key = m.machine_key
JOIN players p ON s.player_key = p.player_key
WHERE m.machine_key = 'SternWars'
ORDER BY s.score DESC
LIMIT 10;
```

### Find Auto-Created Machines
```sql
SELECT machine_key, machine_name, manufacturer, year
FROM machines
WHERE manufacturer IS NULL;
```

### Players Without IPR
```sql
SELECT name, first_seen_season, last_seen_season
FROM players
WHERE current_ipr IS NULL
ORDER BY last_seen_season DESC;
```

### Incomplete Matches
```sql
SELECT m.match_key, m.week, m.home_team_key, m.away_team_key
FROM matches m
LEFT JOIN games g ON m.match_key = g.match_key
WHERE g.game_id IS NULL;
```

---

## 💡 Tips for Development

### When Adding New Scripts
1. Put in `etl/` directory for data processing
2. Use `etl/config.py` for configuration
3. Use `etl/database.py` for DB connection
4. Add logging: `import logging; logger = logging.getLogger(__name__)`
5. Make idempotent (safe to re-run)

### When Modifying Schema
1. Create new migration in `schema/migrations/`
2. Update `schema_version` table
3. Document in `schema/README.md`
4. Update `mnp-app-docs/database/schema.md`

### When Debugging ETL
1. Check logs for warnings (auto-created machines, etc.)
2. Use `--dry-run` if you add that flag
3. Test on subset first (add `LIMIT` to queries)
4. Database has transaction support (safe to Ctrl+C)

---

## 🎉 What's Working Great

- **ETL Pipeline**: Robust, handles edge cases, fast (~10 sec for full load)
- **Database**: Well-normalized, properly indexed, enforces data integrity
- **Data Quality**: Issues identified and documented, not hidden
- **Auto-Creation**: Makes pipeline resilient to incomplete reference data
- **Upsert Logic**: Can re-run ETL safely without duplicates

---

## 📞 Emergency Commands

### Database won't connect
```bash
# Check if PostgreSQL is running
pg_isready

# Start if needed (macOS)
brew services start postgresql@15
```

### Need to reset everything
```bash
# Full database reset (DESTRUCTIVE!)
/usr/local/opt/postgresql@15/bin/psql mnp_analyzer -c "
TRUNCATE scores, games, matches, players, teams,
         venue_machines, venues, machine_aliases, machines
RESTART IDENTITY CASCADE;"

# Then reload
python3 etl/load_season.py --season 22
```

### Check schema version
```bash
/usr/local/opt/postgresql@15/bin/psql mnp_analyzer -c "SELECT * FROM schema_version;"
```

---

## 🌐 FastAPI REST API

### API Overview

**Base URL**: `http://localhost:8000`
**Documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

#### Root & Health
- `GET /` - API information and data summary
- `GET /health` - Health check with database status

#### Player Endpoints
- `GET /players` - List all players (with pagination and filtering)
  - Query params: `season`, `min_ipr`, `max_ipr`, `search`, `limit`, `offset`
  - Example: `/players?season=22&min_ipr=1500&limit=10`

- `GET /players/{player_key}` - Get player details
  - Example: `/players/d491094f6b30d6eb67ff3d38d0f44a866846613a`

- `GET /players/{player_key}/machines` - Get player machine stats
  - Query params: `season`, `venue_key`, `min_games`, `sort_by`, `sort_order`, `limit`, `offset`
  - Example: `/players/sean_irby/machines?venue_key=_ALL_&min_games=3`

#### Machine Endpoints
- `GET /machines` - List all machines (with pagination and filtering)
  - Query params: `manufacturer`, `year`, `game_type`, `search`, `has_percentiles`, `limit`, `offset`
  - Example: `/machines?manufacturer=Stern&has_percentiles=true`

- `GET /machines/{machine_key}` - Get machine details
  - Example: `/machines/Guardians`

- `GET /machines/{machine_key}/percentiles` - Get machine percentiles (grouped)
  - Query params: `season`, `venue_key`
  - Returns: Grouped percentiles by venue/season
  - Example: `/machines/Guardians/percentiles?venue_key=_ALL_`

- `GET /machines/{machine_key}/percentiles/raw` - Get raw percentile records
  - Query params: `season`, `venue_key`, `percentile`
  - Returns: Individual percentile records
  - Example: `/machines/Guardians/percentiles/raw?percentile=50`

### API Features
- **Type-safe responses** - Pydantic models ensure data validity
- **Auto-generated docs** - Interactive API documentation
- **Error handling** - Proper HTTP status codes and error messages
- **Pagination** - All list endpoints support limit/offset
- **Filtering** - Flexible query parameters for data filtering
- **CORS enabled** - Ready for frontend integration

### Starting the API
```bash
# Development mode with auto-reload
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## ✅ Success Criteria for Week 2, Day 1 - COMPLETE!

All objectives achieved:
- ✅ `etl/calculate_percentiles.py` script created
- ✅ `score_percentiles` table populated (980 rows = 140 machines × 7 percentiles)
- ✅ `etl/calculate_player_stats.py` script created
- ✅ `player_machine_stats` table populated (5,942 player×machine combinations)
- ✅ Verification queries showing percentile data is correct
- ✅ Documentation updated with new scripts

---

## ✅ Success Criteria for Week 2, Day 2 - COMPLETE!

All objectives achieved:
- ✅ FastAPI project structure created (`api/` with routers, models, dependencies)
- ✅ 7 REST API endpoints implemented and tested
- ✅ Pydantic models for type-safe request/response handling
- ✅ Auto-generated API documentation (Swagger UI + ReDoc)
- ✅ Health check endpoint with database monitoring
- ✅ All endpoints tested and verified with real data
- ✅ CORS middleware configured for frontend integration

---

## 🎯 Next Steps (Week 2, Day 3)

**Ready for Frontend Development!**

Next session goals:
1. Set up React/Next.js frontend project
2. Create player dashboard with search and stats views
3. Build machine browser with percentile visualizations
4. Integrate with FastAPI backend

---

**Ready to code!** Start with: `cd /Users/test_1/Pinball/MNP/pinball && conda activate mnp`
