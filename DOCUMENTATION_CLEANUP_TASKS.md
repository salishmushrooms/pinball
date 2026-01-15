# MNP Documentation Cleanup - Task Breakdown

**Created:** 2026-01-14
**Purpose:** Comprehensive documentation cleanup tasks that can be executed in parallel by separate agents

---

## 🎯 Overview

This document breaks down the documentation cleanup into 6 independent tasks that can be executed in parallel. Each task is self-contained and can be completed by a separate agent.

### Project Status
- **Production Status**: Live on Railway (API) + Vercel (Frontend)
- **Tech Stack**: FastAPI, PostgreSQL 15, Next.js 16, React 19
- **Data Loaded**: Seasons 18-23 (6 seasons, 56,000+ scores)
- **ETL**: Functional Python scripts in `/etl`
- **API Routers**: 8 active routers (players, machines, venues, teams, matchups, seasons, predictions, matchplay)

---

## 📋 Task 1: Create New Operational README

**Agent Focus:** Documentation writing
**Time Estimate:** 1 hour
**Dependencies:** None
**Priority:** HIGH

### Objective
Create a new `mnp-app-docs/README.md` that serves as the primary operational guide for contributors and maintainers.

### Requirements

1. **Create** `mnp-app-docs/README.md` with the following sections:
   - Project status banner (Production - Deployed)
   - Quick links to operational docs (DATABASE_OPERATIONS.md, DATA_UPDATE_STRATEGY.md)
   - Quick links to reference docs (with disclaimers that they're from planning phase)
   - Contributing guidelines (if applicable)
   - Link to main README.md

2. **Template Structure:**
```markdown
# MNP Analyzer Documentation

> **Project Status**: 🟢 Production - Deployed on Railway + Vercel

## 🚀 Quick Start

[Links to actual deployment URLs]

## 📚 Documentation Index

### Operational Guides (For Contributors)
- [DATABASE_OPERATIONS.md](DATABASE_OPERATIONS.md) - How to manage the database
- [DATA_UPDATE_STRATEGY.md](../DATA_UPDATE_STRATEGY.md) - Weekly data updates

### API & Frontend Reference
- [API Documentation](https://your-actual-railway-url.railway.app/docs) - Live API docs
- [Frontend Design System](../frontend/DESIGN_SYSTEM.md) - UI components & patterns

### Design Documentation (Historical Reference)
> ⚠️ **Note**: These docs were created during planning phase and may not match current implementation

- [api/endpoints.md](api/endpoints.md) - Original API design spec
- [database/schema.md](database/schema.md) - Database schema design
- [frontend/ui-design.md](frontend/ui-design.md) - Original UI/UX mockups
- [data-pipeline/etl-process.md](data-pipeline/etl-process.md) - ETL concepts

### Data Structure Reference
- [MNP Data Structure Reference](../MNP_Data_Structure_Reference.md)
- [Machine Variations](../machine_variations.json)

## 🛠️ Tech Stack

**Current Implementation:**
- FastAPI (Python 3.12)
- PostgreSQL 15
- Next.js 16
- React 19
- Tailwind CSS v4
- Railway (Backend + DB)
- Vercel (Frontend)

## 📊 Current Data

- **Seasons**: 18-23 (6 seasons loaded)
- **Matches**: 943+
- **Scores**: 56,504+
- **Players**: 938+

## 🤝 Contributing

[Add guidelines if applicable]

## 📝 Documentation Guidelines

When updating docs:
1. Check if doc is operational or historical
2. Update operational docs immediately when implementation changes
3. Mark historical docs with warnings if they diverge from implementation
4. Keep DATA_UPDATE_STRATEGY.md and DATABASE_OPERATIONS.md current
```

### Success Criteria
- [ ] New README.md created in `mnp-app-docs/`
- [ ] Clear distinction between operational and historical docs
- [ ] Contains actual deployment URLs (get from user or leave as TODO)
- [ ] Professional and welcoming for contributors

### Files to Reference
- `/Users/JJC/Pinball/MNP/README.md` - Main project README
- `/Users/JJC/Pinball/MNP/mnp-app-docs/DATABASE_OPERATIONS.md` - For understanding current operational docs
- `/Users/JJC/Pinball/MNP/DATA_UPDATE_STRATEGY.md` - For understanding current workflow

---

## 📋 Task 2: Update/Remove INDEX.md

**Agent Focus:** Documentation cleanup
**Time Estimate:** 30 minutes
**Dependencies:** None
**Priority:** HIGH

### Objective
Either remove `mnp-app-docs/INDEX.md` entirely, or drastically simplify it to reflect reality.

### Option A: Remove (Recommended)
**Rationale:** The file references 20+ docs that don't exist and is more confusing than helpful.

1. **Delete** `/Users/JJC/Pinball/MNP/mnp-app-docs/INDEX.md`
2. **Update any references** to INDEX.md in other docs (unlikely to exist)
3. **Update** `.claude/CLAUDE.md` to remove INDEX.md from documentation map if referenced

### Option B: Simplify
If deletion is not preferred, replace entire contents with:

```markdown
# MNP Analyzer Documentation

This directory contains documentation for the MNP Analyzer project.

**Current Status:** Production (Deployed)

## Documentation Files

### Operational Guides
- [README.md](README.md) - Start here
- [DATABASE_OPERATIONS.md](DATABASE_OPERATIONS.md) - Database management
- [../DATA_UPDATE_STRATEGY.md](../DATA_UPDATE_STRATEGY.md) - Weekly updates

### Design Documentation
- [api/endpoints.md](api/endpoints.md) - API endpoint reference
- [database/schema.md](database/schema.md) - Database schema
- [frontend/ui-design.md](frontend/ui-design.md) - UI/UX design
- [data-pipeline/etl-process.md](data-pipeline/etl-process.md) - ETL process

> **Note:** Design docs are from planning phase and may not reflect current implementation.

**Last Updated:** 2026-01-14
```

### Success Criteria
- [ ] INDEX.md either deleted or drastically simplified
- [ ] No broken references to non-existent docs
- [ ] If simplified, references only docs that actually exist

### Files to Modify
- `/Users/JJC/Pinball/MNP/mnp-app-docs/INDEX.md`
- Possibly `/Users/JJC/Pinball/MNP/.claude/CLAUDE.md` (check for INDEX.md references)

---

## 📋 Task 3: Update Status Sections Across All Docs

**Agent Focus:** Find and replace
**Time Estimate:** 30 minutes
**Dependencies:** None
**Priority:** MEDIUM

### Objective
Update all "Status" and outdated timeline references across documentation files.

### Files to Update

1. **`mnp-app-docs/README.md`** (if it wasn't deleted in restructure)
   - Find: `Status: Design Phase`
   - Replace with: `Status: Production - Deployed`
   - Remove: Timeline section (Weeks 1-9)

2. **`mnp-app-docs/api/endpoints.md`**
   - Find: `Status: Design Phase - Not yet implemented`
   - Replace with: `Status: Production - Implementation may differ from this spec`
   - Add at top:
   ```markdown
   > ⚠️ **Note:** This document was created during planning phase.
   > See actual API docs at https://your-api.railway.app/docs for current implementation.
   ```

3. **`mnp-app-docs/database/schema.md`**
   - Find: `Status: Design Phase - Not yet implemented`
   - Replace with: `Status: Implemented - Using PostgreSQL 15 on Railway`
   - Add note about Alembic vs SQL migrations:
   ```markdown
   > **Note:** Originally planned to use Alembic, but implementation uses raw SQL migrations in `schema/migrations/`.
   ```

4. **`mnp-app-docs/data-pipeline/etl-process.md`**
   - Find: `Status: Design Phase`
   - Replace with: `Status: Conceptual documentation - See actual scripts in /etl`
   - Add at top:
   ```markdown
   > ⚠️ **Note:** This is conceptual documentation from planning phase.
   > Actual ETL scripts are in `/etl` directory and may differ from examples below.
   > See DATA_UPDATE_STRATEGY.md for operational ETL documentation.
   ```

5. **`mnp-app-docs/frontend/ui-design.md`**
   - Find: `Status: Dark mode implemented, Filter guidelines added`
   - This is actually accurate! Just update date:
   - Change: `Last Updated: 2025-12-10`
   - To: `Last Updated: 2026-01-14` (or current date)

6. **`schema/README.md`**
   - Find: `Status: Ready for use`
   - Replace with: `Status: Production - In use on Railway and local development`
   - Update date if needed

### Success Criteria
- [ ] All "Design Phase" references updated
- [ ] All "Not yet implemented" references updated
- [ ] Warning banners added where appropriate
- [ ] Dates updated to reflect current status

### Search Commands for Agent
```bash
# Find all "Design Phase" references
grep -r "Design Phase" /Users/JJC/Pinball/MNP/mnp-app-docs/

# Find all "Not yet implemented"
grep -r "Not yet implemented" /Users/JJC/Pinball/MNP/mnp-app-docs/

# Find all "Status:" lines
grep -r "Status:" /Users/JJC/Pinball/MNP/mnp-app-docs/
```

---

## 📋 Task 4: Verify and Document Actual API Endpoints

**Agent Focus:** Code analysis + documentation
**Time Estimate:** 2 hours
**Dependencies:** None
**Priority:** MEDIUM

### Objective
Create accurate API endpoint documentation based on actual implementation.

### Process

1. **Analyze API Routers**
   - Read all files in `/Users/JJC/Pinball/MNP/api/routers/`
   - Extract actual endpoint paths, methods, and parameters
   - Note which endpoints exist vs what's in `api/endpoints.md`

2. **Create New Doc:** `mnp-app-docs/api/ACTUAL_ENDPOINTS.md`

3. **Document Each Router:**

For each router file, document:
- Router prefix (e.g., `/players`, `/machines`)
- All GET/POST/PUT/DELETE endpoints
- Path parameters
- Query parameters (from function signatures)
- Brief description

**Format:**
```markdown
# MNP Analyzer API - Actual Endpoints

**Generated:** 2026-01-14
**Source:** Live production API
**API Docs:** https://your-api.railway.app/docs

> **Note:** For interactive documentation, see the live API docs above.
> This document provides a quick reference of available endpoints.

## Routers

### `/players` - Player Statistics

#### GET `/players`
- **Description:** Search and list players
- **Query Params:**
  - `search` (string, optional): Search by name
  - `season` (int, optional): Filter by season
  - `limit` (int, default: 50): Results per page
  - `offset` (int, default: 0): Pagination offset
- **Returns:** List of players with basic stats

#### GET `/players/{player_key}`
[Continue for each endpoint...]

### `/machines` - Machine Data

[Document all machine endpoints...]

[Continue for all 8 routers]
```

4. **Create Comparison Table**

Add section comparing designed vs actual endpoints:

```markdown
## Designed vs Actual Endpoints

| Designed Endpoint | Actual Implementation | Notes |
|-------------------|----------------------|-------|
| GET /api/v1/players/search | GET /players?search={q} | No /api/v1 prefix, uses query param |
| [List all differences] | | |
```

### Files to Read
- `/Users/JJC/Pinball/MNP/api/routers/players.py`
- `/Users/JJC/Pinball/MNP/api/routers/machines.py`
- `/Users/JJC/Pinball/MNP/api/routers/venues.py`
- `/Users/JJC/Pinball/MNP/api/routers/teams.py`
- `/Users/JJC/Pinball/MNP/api/routers/matchups.py`
- `/Users/JJC/Pinball/MNP/api/routers/seasons.py`
- `/Users/JJC/Pinball/MNP/api/routers/predictions.py`
- `/Users/JJC/Pinball/MNP/api/routers/matchplay.py`
- `/Users/JJC/Pinball/MNP/api/main.py` (for router prefixes and middleware)

### Files to Create
- `/Users/JJC/Pinball/MNP/mnp-app-docs/api/ACTUAL_ENDPOINTS.md`

### Success Criteria
- [ ] All 8 routers documented
- [ ] Each endpoint has method, path, params, and description
- [ ] Comparison table shows differences from original design
- [ ] Link to live API docs included

---

## 📋 Task 5: Document Actual ETL Scripts

**Agent Focus:** Code analysis + documentation
**Time Estimate:** 1.5 hours
**Dependencies:** None
**Priority:** HIGH

### Objective
Document the actual ETL scripts that exist in `/etl`, replacing the theoretical documentation in `data-pipeline/etl-process.md`.

### Process

1. **Analyze ETL Scripts**
   - List all Python files in `/Users/JJC/Pinball/MNP/etl/`
   - Read each script to understand:
     - Purpose (from docstrings and code)
     - Command-line arguments (argparse)
     - Dependencies (which scripts must run before others)
     - Database tables affected

2. **Create New Doc:** `mnp-app-docs/data-pipeline/ACTUAL_ETL_SCRIPTS.md`

**Structure:**
```markdown
# MNP ETL Scripts - Actual Implementation

**Last Updated:** 2026-01-14
**Location:** `/etl` directory

> **Note:** This documents the actual ETL implementation.
> For operational guidance on running these scripts, see [DATA_UPDATE_STRATEGY.md](../../DATA_UPDATE_STRATEGY.md).

## Script Overview

| Script | Purpose | Dependencies | Frequency |
|--------|---------|--------------|-----------|
| load_season.py | Load match data from JSON | None | Weekly |
| load_preseason.py | Load preseason schedule | None | Once per season |
| calculate_percentiles.py | Calculate score percentiles | load_season.py | After loading data |
| calculate_player_stats.py | Calculate player aggregates | calculate_percentiles.py | After percentiles |
| [List all scripts] | | | |

## Script Details

### `load_season.py`

**Purpose:** Load completed match data from JSON files into database

**Usage:**
```bash
python etl/load_season.py --season 22
```

**Arguments:**
- `--season` (required): Season number to load

**What it loads:**
- Match metadata
- Games (4 per match)
- Scores (8-12 per match)
- Players (if new)
- Updates match state to 'complete'

**Database tables affected:**
- `matches`
- `games`
- `scores`
- `players` (upsert)

**Dependencies:** None (can run independently)

**Notes:**
- Uses ON CONFLICT DO UPDATE for idempotency
- Safe to run multiple times
- Only loads matches with complete JSON data

---

### `calculate_percentiles.py`

[Continue for each script...]

## Execution Order

### Weekly Update (After Matches Complete)
```bash
# 1. Load new match data
python etl/load_season.py --season 23

# 2. Recalculate percentiles (required before player stats)
python etl/calculate_percentiles.py

# 3. Recalculate player stats
python etl/calculate_player_stats.py

# 4. Optional: Recalculate other aggregates
python etl/calculate_team_machine_picks.py
python etl/calculate_player_totals.py
python etl/calculate_match_points.py
```

### Preseason Setup
```bash
python etl/load_preseason.py --season 23
```

### Full Pipeline (All Seasons)
```bash
python etl/run_full_pipeline.py --seasons 18,19,20,21,22,23
```

## Configuration

Scripts use environment variables from `.env`:
- `DATABASE_URL`: PostgreSQL connection string

For local execution, override:
```bash
DATABASE_URL=postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer \
  python etl/load_season.py --season 22
```

## Common Issues

[Document common errors and solutions]
```

### Files to Read
- All `.py` files in `/Users/JJC/Pinball/MNP/etl/`:
  - `load_season.py`
  - `load_preseason.py`
  - `calculate_percentiles.py`
  - `calculate_player_stats.py`
  - `calculate_team_machine_picks.py`
  - `calculate_player_totals.py`
  - `calculate_match_points.py`
  - `run_full_pipeline.py`
  - `update_season.py`
  - `update_team_venues.py`
  - `update_ipr.py`
  - `export_machine_stats.py`
  - `config.py`
  - `database.py`

### Files to Create
- `/Users/JJC/Pinball/MNP/mnp-app-docs/data-pipeline/ACTUAL_ETL_SCRIPTS.md`

### Files to Update
- Add disclaimer to top of `data-pipeline/etl-process.md`:
  ```markdown
  > ⚠️ **Outdated:** This is theoretical documentation from planning phase.
  > See [ACTUAL_ETL_SCRIPTS.md](ACTUAL_ETL_SCRIPTS.md) for actual implementation.
  ```

### Success Criteria
- [ ] All ETL scripts documented with purpose, usage, and arguments
- [ ] Execution order clearly documented
- [ ] Dependencies between scripts explained
- [ ] Common issues section included
- [ ] Links to DATA_UPDATE_STRATEGY.md for operational guidance

---

## 📋 Task 6: Update Tech Stack and URLs

**Agent Focus:** Find and replace
**Time Estimate:** 30 minutes
**Dependencies:** Task 1 (needs actual URLs from user)
**Priority:** HIGH

### Objective
Update all references to tech stack versions and deployment URLs to match current implementation.

### Tech Stack Updates

**Find and Replace across all docs:**

| Find | Replace | Files |
|------|---------|-------|
| `Next.js 14` | `Next.js 16` | README.md, mnp-app-docs/README.md, .claude/CLAUDE.md |
| `React` (when referring to version) | `React 19` | Same as above |
| `Tailwind CSS` | `Tailwind CSS v4` | Same as above |
| `Python 3.11` | `Python 3.12` | README.md, API docs |
| `PostgreSQL` (when referring to version) | `PostgreSQL 15` | Database docs |

### URL Updates

**Placeholder URLs to Replace:**
- `https://api.mnp-analyzer.com` → Get actual Railway URL from user
- `https://mnp-analyzer.vercel.app` → Get actual Vercel URL from user
- `https://your-api.railway.app` → Actual Railway URL

**Files containing placeholder URLs:**
1. `/Users/JJC/Pinball/MNP/README.md`
2. `/Users/JJC/Pinball/MNP/mnp-app-docs/README.md` (if exists)
3. `/Users/JJC/Pinball/MNP/mnp-app-docs/DATABASE_OPERATIONS.md`
4. `/Users/JJC/Pinball/MNP/DATA_UPDATE_STRATEGY.md`
5. `/Users/JJC/Pinball/MNP/.claude/CLAUDE.md`

### Additional Updates

**Remove/Update Timeline References:**
- Find: "Week 1-2", "Week 3-4", etc. (implementation timeline)
- Action: Remove these sections entirely OR move to "Project History" section

**Update Storage Estimates:**
- In `database/schema.md`: Update storage estimates table with note:
  ```markdown
  > **Note:** These are initial estimates. Actual production database is larger.
  > Check Railway dashboard for current storage usage.
  ```

### Path Corrections

**DATABASE_OPERATIONS.md:**
- Find: `/Users/test_1/Pinball/MNP/pinball`
- Replace: `/Users/JJC/Pinball/MNP`

### Success Criteria
- [ ] All Next.js 14 → Next.js 16
- [ ] All React → React 19
- [ ] All Python 3.11 → Python 3.12
- [ ] All placeholder URLs replaced (or marked as TODO)
- [ ] Path corrected in DATABASE_OPERATIONS.md
- [ ] Timeline sections removed or moved to history

### Action Required from User
**Before starting this task, get:**
1. Actual Railway API URL
2. Actual Vercel frontend URL

---

## 🎯 Task Execution Order

### Parallel Execution (Recommended)
These can all be done simultaneously by different agents:
- **Agent 1:** Task 1 (New README)
- **Agent 2:** Task 2 (INDEX cleanup)
- **Agent 3:** Task 3 (Status updates)
- **Agent 4:** Task 4 (API endpoints)
- **Agent 5:** Task 5 (ETL scripts)

**Wait for Task 1 completion before:**
- **Agent 6:** Task 6 (URLs - needs actual URLs from user first)

### Sequential Execution (If needed)
If running tasks sequentially, recommended order:
1. Task 6 (URLs - quick, foundational)
2. Task 3 (Status updates - quick)
3. Task 2 (INDEX cleanup - quick)
4. Task 1 (New README - references other docs)
5. Task 5 (ETL docs - important, complex)
6. Task 4 (API docs - important, complex)

---

## ✅ Final Checklist

After all tasks complete, verify:

- [ ] `mnp-app-docs/README.md` exists and is accurate
- [ ] `mnp-app-docs/INDEX.md` is deleted or simplified
- [ ] No docs claim "Design Phase" or "Not implemented"
- [ ] Warning banners added to theoretical docs
- [ ] Actual API endpoints documented
- [ ] Actual ETL scripts documented
- [ ] All tech stack versions correct (Next.js 16, React 19, Python 3.12)
- [ ] All placeholder URLs replaced or marked as TODO
- [ ] Path corrections made in DATABASE_OPERATIONS.md
- [ ] All dates updated to 2026-01-14 or later
- [ ] Links between docs are not broken

---

## 📝 Notes for Agents

### General Guidelines
- When in doubt, add a warning banner rather than claiming accuracy
- Reference actual code files when documenting implementation
- Keep operational docs (DATABASE_OPERATIONS.md, DATA_UPDATE_STRATEGY.md) as source of truth
- Mark theoretical/design docs clearly as historical reference

### File Modification Safety
- All tasks involve only documentation files (`.md`)
- No code changes required
- Safe to execute in any order (except Task 6 dependencies)

### Context Files to Reference
- `/Users/JJC/Pinball/MNP/.claude/CLAUDE.md` - Project overview
- `/Users/JJC/Pinball/MNP/DATA_UPDATE_STRATEGY.md` - Current operational workflow
- `/Users/JJC/Pinball/MNP/mnp-app-docs/DATABASE_OPERATIONS.md` - Current DB operations

---

**Document Version:** 1.0
**Created:** 2026-01-14
**For:** MNP Analyzer documentation cleanup project
