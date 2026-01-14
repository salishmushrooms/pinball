# MNP Data Archive - LLM Context Guide

> **Last Updated**: 2026-01-02
> **Purpose**: Essential context for AI assistants working with Monday Night Pinball data analysis project

---

## 🎯 Project Overview

Production-deployed full-stack data analysis platform for Monday Night Pinball (MNP) league.

- **API**: FastAPI + PostgreSQL (LIVE on Railway)
- **Frontend**: Next.js 16 (LIVE on Vercel)
- **ETL**: Python scripts for data loading
- **Data**: 10 seasons (14-23) in git submodule, 6 seasons (18-23) in production DB

**Production URLs:**
- API: https://pinball-production.up.railway.app
- API Docs: https://pinball-production.up.railway.app/docs

---

## 📁 Quick Reference

### Tech Stack
- **Backend**: Python 3.12, FastAPI, PostgreSQL 15, SQLAlchemy
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS v4
- **Deployment**: Railway ($5/month) + Vercel

### Production Stats
- **Seasons**: 18-23 (6 seasons loaded)
- **Matches**: 943+ | **Scores**: 56,504+ | **Players**: 938+

### Key Locations
```
/Users/JJC/Pinball/MNP/
├── .claude/              # LLM context docs (THIS FILE)
├── api/                  # FastAPI backend (8 routers)
├── frontend/             # Next.js app (19 UI components)
├── etl/                  # Data loading scripts
├── schema/               # PostgreSQL schema
├── mnp-data-archive/     # Match data (git submodule)
└── mnp-app-docs/         # Deployment & operations docs
```

**See [PROJECT_STRUCTURE.md](.claude/PROJECT_STRUCTURE.md) for detailed directory layout.**

---

## 📚 Documentation Map

### For LLM Context (in .claude/)
- **[MNP_MATCH_STRUCTURE.md](.claude/MNP_MATCH_STRUCTURE.md)** - Match JSON format
- **[PROJECT_STRUCTURE.md](.claude/PROJECT_STRUCTURE.md)** - Detailed directory structure
- **[DEVELOPMENT_GUIDE.md](.claude/DEVELOPMENT_GUIDE.md)** - Dev workflows & commands
- **[DATA_CONVENTIONS.md](.claude/DATA_CONVENTIONS.md)** - MNP-specific patterns

### For Humans (in repo root)
- **[README.md](../README.md)** - Project overview & quick start
- **[MNP_Data_Structure_Reference.md](../MNP_Data_Structure_Reference.md)** - Data structure overview
- **[MNP_Match_Data_Analysis_Guide.md](../MNP_Match_Data_Analysis_Guide.md)** - Analysis methodology
- **[machine_variations.json](../machine_variations.json)** - Machine name lookups

### API & Database (in mnp-app-docs/)
- **[api/endpoints.md](../mnp-app-docs/api/endpoints.md)** - API documentation
- **[database/schema.md](../mnp-app-docs/database/schema.md)** - Database schema
- **[DATABASE_OPERATIONS.md](../mnp-app-docs/DATABASE_OPERATIONS.md)** - DB operations guide

### Frontend (in frontend/)
- **[DESIGN_SYSTEM.md](../frontend/DESIGN_SYSTEM.md)** - Component patterns & conventions

---

## ⚡ Quick Start Commands

```bash
# Start API (from repo root)
conda activate mnp
uvicorn api.main:app --reload --port 8000

# Start frontend
cd frontend && npm run dev

# Local database
psql -h localhost -U mnp_user -d mnp_analyzer

# Production database
railway connect postgres

# Load season data
python etl/load_season.py --season 22
python etl/calculate_percentiles.py
```

**See [DEVELOPMENT_GUIDE.md](.claude/DEVELOPMENT_GUIDE.md) for complete workflows.**

---

## 🎮 MNP Data Essentials

### Match Structure
- **File naming**: `mnp-{season}-{week}-{away}-{home}.json`
- **4 rounds per match**: Rounds 1&4 (doubles, 4 players), Rounds 2&3 (singles, 2 players)
- **Home/Away selection**: Home team picks rounds 2&4, away team picks rounds 1&3

### Common Keys
**Teams**: SKP, TRL, ADB, JMF | **Venues**: T4B, KRA, 8BT, JUP | **Machines**: See [machine_variations.json](../machine_variations.json)

### Critical Data Notes
- ⚠️ **Player 4 scores unreliable** in doubles (early game completion)
- ⚠️ **Never compare raw scores** across different machines (use percentiles)
- ⚠️ **Home advantage is real** - account for it in analysis
- ✅ **Player reliability**: Player 1 > Player 2 > Player 3 > Player 4

**See [DATA_CONVENTIONS.md](.claude/DATA_CONVENTIONS.md) for filtering patterns and detailed conventions.**

---

## 🔧 Frontend Development

### Component Architecture
- **19 UI components** in `frontend/components/ui/` (Button, Card, Table, etc.)
- **Specialized components**: SeasonMultiSelect, RoundMultiSelect, TeamBadge, etc.
- **Design system**: [DESIGN_SYSTEM.md](../frontend/DESIGN_SYSTEM.md)

### Key Principles
1. **Always check for existing components** before creating new ones
2. **Multi-season support**: All pages support analyzing across multiple seasons
3. **Type safety**: Use types from `frontend/lib/types.ts`
4. **Import from** `@/components/ui` for all standard UI elements

---

## 🎯 Development Principles

### Code Quality
1. **Security**: Avoid OWASP top 10 vulnerabilities (SQL injection, XSS, etc.)
2. **Simplicity**: Don't over-engineer - solve the current problem
3. **No speculation**: Don't add features, error handling, or abstractions "just in case"
4. **Read first**: NEVER propose changes to code you haven't read
5. **Delete unused code**: No backwards-compatibility hacks for unused code

### When to Plan vs Execute
- **Use EnterPlanMode** for: new features, multi-file changes, architectural decisions
- **Execute directly** for: typos, single-line fixes, well-specified tasks
- **Use AskUserQuestion** for: clarifying ambiguous requirements

---

## 🚨 Important Integrations

### Matchplay.events API
- **Data lookback**: Machine stats filtered to **past 1 year (365 days)**
- **Rationale**: Player skill evolves - recent data more relevant
- **Config**: `MATCHPLAY_DATA_LOOKBACK_DAYS = 365` in `api/services/matchplay_client.py`
- **Potential duplication**: MNP data may exist in Matchplay - check investigation endpoint

### Git Submodule
```bash
# Update match data
git submodule update --remote mnp-data-archive
```

---

## 📊 Related Projects

- **Pin Stats iOS App**: `/Users/JJC/Pinball/pin-stats` - iOS companion app
  - GitHub: https://github.com/salishmushrooms/pinstats.git

---

## 🆘 Getting Help

- **Project overview**: [README.md](../README.md)
- **Data structure**: [MNP_Data_Structure_Reference.md](../MNP_Data_Structure_Reference.md)
- **Machine lookups**: [machine_variations.json](../machine_variations.json)
- **API reference**: https://pinball-production.up.railway.app/docs
- **Database operations**: [mnp-app-docs/DATABASE_OPERATIONS.md](../mnp-app-docs/DATABASE_OPERATIONS.md)

---

**Maintained by**: JJC
**Last Updated**: 2026-01-02
**LLM Usage**: This file provides essential context for AI conversations about this project
