# MNP Analyzer Documentation

> **Project Status**: 🟢 Production - Deployed on Railway + Vercel

Welcome to the MNP Analyzer documentation! This project is a full-stack data analysis platform for Monday Night Pinball league, providing statistical insights, performance analytics, and match predictions.

---

## 🚀 Quick Start

### Live Deployments

- **API Base URL**: https://your-api.railway.app
- **API Documentation**: https://your-api.railway.app/docs (Interactive Swagger UI)
- **API ReDoc**: https://your-api.railway.app/redoc (Alternative documentation view)
- **Frontend Application**: Deployed on Vercel

### Quick API Examples

```bash
# Get all available seasons
curl https://your-api.railway.app/seasons

# Search for players
curl https://your-api.railway.app/players?search=smith

# Get machine percentiles
curl "https://your-api.railway.app/machines/MM/percentiles?seasons=22"

# Get team matchup predictions
curl "https://your-api.railway.app/matchups/analyze?team1=SKP&team2=TRL&season=22"
```

---

## 📚 Documentation Index

### Operational Guides (For Contributors)

**Start here if you're maintaining or contributing to the project:**

- **[DATABASE_OPERATIONS.md](DATABASE_OPERATIONS.md)** - Database management, loading data, running migrations
- **[DATA_UPDATE_STRATEGY.md](../DATA_UPDATE_STRATEGY.md)** - Weekly data update workflow and ETL pipeline
- **[Main README.md](../README.md)** - Project overview and quick start guide

These operational guides reflect the **current production implementation** and are kept up-to-date.

### API & Frontend Reference

- **[API Documentation](https://your-api.railway.app/docs)** - Live interactive API docs (Swagger UI)
- **[Frontend Design System](../frontend/DESIGN_SYSTEM.md)** - UI components, patterns, and conventions

### Data Structure Reference

Essential references for understanding MNP data:

- **[MNP Data Structure Reference](../MNP_Data_Structure_Reference.md)** - Match JSON format and data conventions
- **[MNP Match Data Analysis Guide](../MNP_Match_Data_Analysis_Guide.md)** - Analysis methodology and best practices
- **[Machine Variations](../machine_variations.json)** - Machine name lookups and aliases

### LLM Context Documentation

For AI assistants and comprehensive project context:

- **[.claude/CLAUDE.md](../.claude/CLAUDE.md)** - Essential LLM context and project guide
- **[.claude/DEVELOPMENT_GUIDE.md](../.claude/DEVELOPMENT_GUIDE.md)** - Development workflows and commands
- **[.claude/PROJECT_STRUCTURE.md](../.claude/PROJECT_STRUCTURE.md)** - Detailed directory structure
- **[.claude/DATA_CONVENTIONS.md](../.claude/DATA_CONVENTIONS.md)** - MNP-specific data patterns

### Design Documentation (Historical Reference)

> ⚠️ **Note**: These documents were created during the planning phase and may not match the current implementation. They are preserved for historical reference and architectural context. For accurate implementation details, consult the actual code or live API documentation.

- **[api/endpoints.md](api/endpoints.md)** - Original API design specification
- **[database/schema.md](database/schema.md)** - Database schema design document
- **[frontend/ui-design.md](frontend/ui-design.md)** - Original UI/UX mockups and design concepts
- **[data-pipeline/etl-process.md](data-pipeline/etl-process.md)** - ETL conceptual documentation

**When to use these:** Refer to design docs when you need to understand the original architectural vision or design decisions. For current implementation, always check the actual code in `/api`, `/frontend`, `/etl`, and `/schema` directories.

---

## 🛠️ Tech Stack

**Current Production Implementation:**

### Backend
- **Python 3.12** - Modern Python with type hints
- **FastAPI** - High-performance async web framework
- **PostgreSQL 15** - Production database on Railway
- **SQLAlchemy** - ORM for database operations
- **Pydantic v2** - Data validation and serialization

### Frontend
- **Next.js 16** - React framework with App Router
- **React 19** - Latest React with Server Components
- **TypeScript** - Type-safe development
- **Tailwind CSS v4** - Utility-first styling
- **shadcn/ui** - Component library

### Deployment
- **Railway** - Backend API + PostgreSQL database hosting ($5/month)
- **Vercel** - Frontend hosting (free tier)

### Data Processing
- **Python ETL Scripts** - Located in `/etl` directory
- **Raw SQL Migrations** - Located in `/schema/migrations`
- **Git Submodule** - Match data in `/mnp-data-archive`

---

## 📊 Current Data

**Production Database Statistics (as of last update):**

- **Seasons Loaded**: 18-23 (6 complete seasons)
- **Matches**: 943+
- **Individual Scores**: 56,504+
- **Players**: 938+
- **Machines**: 400+
- **Venues**: Multiple across Seattle area

**Data Source**: Monday Night Pinball league match data stored in the `mnp-data-archive` git submodule.

---

## 🔄 Common Operations

### Updating Data Weekly

After Monday night matches complete:

1. Pull latest match data: `cd mnp-data-archive && git pull origin main && cd ..`
2. Run ETL locally: `python etl/load_season.py --season 23`
3. Recalculate aggregates: `python etl/calculate_percentiles.py && python etl/calculate_player_stats.py`
4. Export and import to Railway (see [DATA_UPDATE_STRATEGY.md](../DATA_UPDATE_STRATEGY.md))

### Connecting to Production Database

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and link project
railway login
railway link

# Connect to PostgreSQL
railway connect postgres
```

### Starting Local Development

```bash
# Backend API
conda activate mnp
uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend
npm run dev

# Local database
psql -h localhost -U mnp_user -d mnp_analyzer
```

---

## 🤝 Contributing

### Getting Started

1. **Clone the repository** with submodules:
   ```bash
   git clone <repository-url>
   cd MNP
   git submodule update --init --recursive
   ```

2. **Set up local environment**:
   - Follow setup instructions in [Main README.md](../README.md)
   - Configure local PostgreSQL database
   - Load sample data using ETL scripts

3. **Read the documentation**:
   - Start with [DATABASE_OPERATIONS.md](DATABASE_OPERATIONS.md) for database setup
   - Review [DATA_UPDATE_STRATEGY.md](../DATA_UPDATE_STRATEGY.md) for ETL workflow
   - Check [.claude/DEVELOPMENT_GUIDE.md](../.claude/DEVELOPMENT_GUIDE.md) for development commands

### Code Organization

```
MNP/
├── api/                    # FastAPI backend (8 routers)
├── frontend/               # Next.js frontend (19+ UI components)
├── etl/                    # Data loading and processing scripts
├── schema/                 # Database schema and migrations
├── reports/                # Analysis report generators
├── mnp-data-archive/       # Match data (git submodule)
└── mnp-app-docs/           # This documentation directory
```

### Making Changes

- **Backend changes**: Modify files in `/api`, test locally, update API docs if endpoints change
- **Frontend changes**: Modify files in `/frontend`, follow the [Design System](../frontend/DESIGN_SYSTEM.md)
- **Database changes**: Create new migration in `/schema/migrations`, test locally before production
- **ETL changes**: Modify scripts in `/etl`, test with local database first

---

## 📝 Documentation Guidelines

When updating or creating documentation:

1. **Classify the document type**:
   - **Operational**: Current implementation, how-to guides, workflows → Keep current
   - **Design/Historical**: Planning documents, original specs → Mark with warnings
   - **Reference**: Data structures, API specs → Update when implementation changes

2. **Keep operational docs current**:
   - Update `DATABASE_OPERATIONS.md` when database procedures change
   - Update `DATA_UPDATE_STRATEGY.md` when ETL workflow changes
   - Update this README when tech stack or deployment changes

3. **Mark historical docs clearly**:
   - Add warning banners if design docs diverge from implementation
   - Preserve them for architectural context
   - Don't delete unless completely obsolete

4. **Update dates**:
   - Always update "Last Updated" dates when modifying docs
   - Include version numbers for major changes

5. **Test instructions**:
   - Verify all commands and code snippets work
   - Test database operations on local instance first
   - Validate API endpoints before documenting them

---

## 🎯 Project Goals

### Current Focus

- **Data Quality**: Ensure accurate, up-to-date match data across all seasons
- **Performance**: Fast API responses and efficient database queries
- **Usability**: Intuitive web interface for exploring statistics
- **Reliability**: 99%+ uptime during match nights

### Future Enhancements

- **Real-time Updates**: Automatic data refresh after matches
- **Advanced Analytics**: Machine learning predictions and trend analysis
- **Mobile App**: Native iOS/Android companion apps
- **Social Features**: Player profiles, strategy sharing, comments

---

## 🆘 Getting Help

### Quick Resources

- **Project Overview**: [Main README.md](../README.md)
- **Database Questions**: [DATABASE_OPERATIONS.md](DATABASE_OPERATIONS.md)
- **Data Updates**: [DATA_UPDATE_STRATEGY.md](../DATA_UPDATE_STRATEGY.md)
- **API Reference**: https://your-api.railway.app/docs
- **Machine Lookups**: [machine_variations.json](../machine_variations.json)

### Troubleshooting

Common issues and solutions are documented in:
- [DATABASE_OPERATIONS.md](DATABASE_OPERATIONS.md) - Database and deployment issues
- [DATA_UPDATE_STRATEGY.md](../DATA_UPDATE_STRATEGY.md) - ETL and data loading issues

### Support

- **Issues**: Open an issue in the repository
- **Questions**: Check existing documentation first
- **Security Issues**: Create a private issue report

---

## 📈 Production Status

### Current Deployment

- **Backend**: ✅ Live on Railway
- **Frontend**: ✅ Live on Vercel
- **Database**: ✅ PostgreSQL 15 on Railway
- **Data**: ✅ Seasons 18-23 loaded and updated

### API Endpoints

The production API has **8 active routers**:

1. **Players** - Player statistics and performance data
2. **Machines** - Machine stats, percentiles, and difficulty analysis
3. **Venues** - Venue information and home advantage analysis
4. **Teams** - Team performance and machine selection patterns
5. **Matchups** - Head-to-head predictions and analysis
6. **Seasons** - Season information and status
7. **Predictions** - Match outcome predictions
8. **Matchplay** - External tournament data integration

See [live API documentation](https://your-api.railway.app/docs) for complete endpoint details.

### Frontend Pages

The Next.js frontend includes:

- **Home/Search** - Quick player and machine lookups
- **Players** - Player profiles and statistics
- **Machines** - Machine stats and score distributions
- **Teams** - Team analysis and comparisons
- **Venues** - Venue information and statistics
- **Matchups** - Match predictions and analysis

---

## 🔐 Security & Privacy

- **Data**: Public league data only (no personal information beyond player names)
- **API**: Read-only public access with rate limiting
- **Credentials**: Managed via Railway/Vercel environment variables
- **HTTPS**: All communication encrypted
- **Git**: Never commit `.env` files or secrets

---

## 📜 License

MIT License - See [LICENSE](../LICENSE) file for details

---

## 🙏 Acknowledgments

- **Monday Night Pinball** - League organizers and players
- **Matchplay.events** - Tournament management platform
- **IFPA** - Player rating systems

---

**Last Updated**: 2026-01-14
**Maintained By**: JJC
**Project Version**: Production 1.0

For the most current information, always refer to:
- Live API: https://your-api.railway.app/docs
- This documentation: Keep it updated as the project evolves
