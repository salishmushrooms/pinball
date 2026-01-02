# Monday Night Pinball (MNP) Data Archive & Analytics

A comprehensive data analysis platform for Monday Night Pinball league matches, providing statistical insights, score predictions, and performance analytics.

## 🎯 What is This?

This project visualizes MNP league data to help players and teams:
- **Understand machine score distribution** through score percentiles
- **Track player performance** across different machines and venues
- **Predict player machine choices**
- **Compare teams** and predict match outcomes
- **Analyze trends** in machine selection and home venue advantage

## 🌐 Live API

The API is publicly available for read-only access:

- **API Base URL**: https://pinball-production.up.railway.app
- **Interactive Docs**: https://pinball-production.up.railway.app/docs
- **ReDoc**: https://pinball-production.up.railway.app/redoc

### Quick API Examples

```bash
# Get all available seasons
curl https://pinball-production.up.railway.app/seasons

# Search for players
curl https://pinball-production.up.railway.app/players?search=smith

# Get machine percentiles
curl "https://pinball-production.up.railway.app/machines/MM/percentiles?seasons=22"

# Get team matchup predictions
curl "https://pinball-production.up.railway.app/matchups/analyze?team1=SKP&team2=TRL&season=22"
```

**API Usage Guidelines:**
- Free to use for personal projects, research, and education
- Read-only access (no authentication required)
- Rate limited to prevent abuse
- Please be respectful of server resources
- For high-volume usage, consider deploying your own instance

## ✨ Features

### 📊 Web Application (Next.js)
- Browse players, teams, machines, and venues
- Multi-season analysis and filtering
- Interactive score distributions
- Team matchup predictions

### 🔌 REST API (FastAPI)
- **Player Stats**: Individual performance, machine-specific stats
- **Machine Data**: Score percentiles, difficulty analysis
- **Team Analysis**: Matchup predictions, machine selection patterns
- **Venue Stats**: Home advantage analysis
- **Matchplay Integration**: External tournament data integration

### 📈 Report Generators (Python)
- Score percentile analysis with visualizations
- Venue-specific performance reports
- Home advantage calculations
- Team comparison reports
- Machine selection pattern analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 15+
- Node.js 18+ (for frontend)
- Conda (recommended for Python environment)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mnp-data-archive.git
   cd mnp-data-archive
   git submodule update --init --recursive
   ```

2. **Set up Python environment**
   ```bash
   conda create -n mnp python=3.12
   conda activate mnp
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**
   ```bash
   # Create database and user
   psql -U postgres
   CREATE DATABASE mnp_analyzer;
   CREATE USER mnp_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE mnp_analyzer TO mnp_user;
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Load data**
   ```bash
   # Apply schema
   psql -h localhost -U mnp_user -d mnp_analyzer -f schema/001_complete_schema.sql

   # Load season data
   python etl/load_season.py --season 22

   # Calculate aggregates
   python etl/calculate_percentiles.py
   python etl/calculate_player_stats.py
   ```

6. **Start the API**
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

7. **Start the frontend** (optional)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

Visit http://localhost:8000/docs for API documentation and http://localhost:3000 for the web interface.

## 📚 Documentation

### For Developers & AI Assistants
- **[.claude/CLAUDE.md](.claude/CLAUDE.md)** - LLM context & essential project info
- **[.claude/DEVELOPMENT_GUIDE.md](.claude/DEVELOPMENT_GUIDE.md)** - Complete development workflows
- **[.claude/PROJECT_STRUCTURE.md](.claude/PROJECT_STRUCTURE.md)** - Detailed directory structure
- **[.claude/DATA_CONVENTIONS.md](.claude/DATA_CONVENTIONS.md)** - MNP-specific data patterns

### Operations & Deployment
- **[mnp-app-docs/DATABASE_OPERATIONS.md](mnp-app-docs/DATABASE_OPERATIONS.md)** - Database setup and operations
- **[mnp-app-docs/DEPLOYMENT_CHECKLIST.md](mnp-app-docs/DEPLOYMENT_CHECKLIST.md)** - Deploy your own instance
- **[DATA_UPDATE_STRATEGY.md](DATA_UPDATE_STRATEGY.md)** - Weekly data update guide

### API & Frontend
- **[mnp-app-docs/api/endpoints.md](mnp-app-docs/api/endpoints.md)** - Full API endpoint reference
- **[frontend/DESIGN_SYSTEM.md](frontend/DESIGN_SYSTEM.md)** - Frontend component patterns

### Data Structure Reference
- **[MNP_Data_Structure_Reference.md](MNP_Data_Structure_Reference.md)** - Match data overview
- **[MNP_Match_Data_Analysis_Guide.md](MNP_Match_Data_Analysis_Guide.md)** - Analysis methodology
- **[machine_variations.json](machine_variations.json)** - Machine name lookups

## 🏗️ Project Structure

```
MNP/
├── api/                    # FastAPI backend
│   ├── routers/           # API endpoints
│   ├── services/          # Business logic
│   └── models/            # Pydantic schemas
├── frontend/              # Next.js frontend
│   ├── app/              # App router pages
│   ├── components/       # React components
│   └── lib/              # API client & types
├── etl/                   # Data pipeline
│   ├── load_season.py    # Load match data
│   ├── calculate_*.py    # Aggregate calculations
│   └── parsers/          # Data parsers
├── reports/               # Analysis & report generation
│   ├── generators/       # Python report scripts
│   ├── configs/          # Report configurations
│   └── output/           # Generated reports (gitignored)
├── schema/                # Database schema & migrations
├── mnp-data-archive/     # League data (git submodule)
│   ├── season-XX/        # Match data by season
│   ├── machines.json     # Machine definitions
│   ├── venues.json       # Venue information
│   └── IPR.csv          # Individual Player Ratings
└── mnp-app-docs/         # Comprehensive documentation
```

## 🛠️ Technology Stack

**Backend:**
- FastAPI (Python 3.12)
- PostgreSQL 15
- SQLAlchemy ORM

**Frontend:**
- Next.js 16
- React 19
- TypeScript
- Tailwind CSS v4

**Deployment:**
- Railway (API + Database)
- Vercel (Frontend)

**Data Processing:**
- Python scripts for ETL
- Matplotlib for visualizations

## 📊 Data

The project includes match data from Monday Night Pinball seasons 14-22:
- **943 matches** across 9 seasons
- **56,504 individual scores**
- **938 players**
- **400+ pinball machines**
- **Multiple venues** across the Seattle area

Data is stored in the `mnp-data-archive` git submodule. To update:
```bash
git submodule update --remote mnp-data-archive
```

## 🔐 Security & Privacy

- This project contains **public league data** only (no personal information beyond player names)
- **Never commit** `.env` files or API tokens
- Production credentials managed via Railway/Vercel environment variables
- To report security issues: [create an issue](https://github.com/yourusername/mnp-data-archive/issues)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For major changes, please open an issue first to discuss.

## 📈 Report Generation

Generate analysis reports using Python scripts:

```bash
# Score percentile analysis
python reports/generators/score_percentile_report.py reports/configs/4bs_machines_config.json

# Team comparison
python reports/generators/team_machine_comparison_report.py reports/configs/trolls_vs_slapkrakenpop_config.json

# Venue summary
python reports/generators/venue_summary_report.py reports/configs/venue_summary_config.json
```

See [reports/README.md](reports/README.md) for all available generators.

## 🎮 Related Projects

- **[Pin Stats iOS App](https://github.com/salishmushrooms/pinstats)** - iOS companion app for viewing MNP analytics

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Monday Night Pinball league organizers and players
- [Matchplay.events](https://matchplay.events) for tournament management platform
- IFPA for player rating systems

---

**Questions?** Open an issue or check the [documentation](mnp-app-docs/)

**Want to analyze your own league data?** This project is designed to be adaptable - see [DATABASE_OPERATIONS.md](mnp-app-docs/DATABASE_OPERATIONS.md) for guidance.
