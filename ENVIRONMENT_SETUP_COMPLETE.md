# ✅ MNP Analyzer - Environment Setup Complete!

**Date**: 2025-11-24
**Computer**: JJC@Mini
**Status**: **FULLY OPERATIONAL** 🚀

---

## 🎉 Setup Summary

Your development environment is now fully configured and running!

### ✅ Completed Setup Tasks

1. **PostgreSQL 15** - Installed, running, and configured
2. **Conda Environment** - Created `mnp` environment with Python 3.12.12
3. **Python Dependencies** - All packages installed (FastAPI, SQLAlchemy, pandas, etc.)
4. **Database** - `mnp_analyzer` database created with schema v1.0.0
5. **Data Loaded** - Season 22 complete:
   - 332 machines + 10 auto-created
   - 525 players
   - 184 matches
   - 11,040 scores
6. **Percentiles Calculated** - 140 machines with 980 percentile records
7. **Player Stats Calculated** - 6,058 player/machine combinations
8. **Backend API** - FastAPI server running on http://localhost:8000
9. **Frontend** - Dependencies installed, configured, ready to run

---

## 🚀 How to Start Working

### Start Development Session

```bash
# Terminal 1: Backend API (already running)
cd /Users/JJC/Pinball/MNP
conda activate mnp
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend Dev Server
cd /Users/JJC/Pinball/MNP/frontend
npm run dev
```

### Quick Access URLs

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health
- **ReDoc**: http://localhost:8000/redoc

---

## 📊 Current Status

### Backend API ✅ RUNNING
- **URL**: http://localhost:8000
- **Status**: Healthy
- **Database**: Connected
- **Process ID**: Background task `06520c`

### Frontend
- **Status**: Ready (not started yet)
- **Port**: 3000
- **Config**: `.env.local` created
- **Dependencies**: Installed

### Database
- **Name**: `mnp_analyzer`
- **Version**: 1.0.0
- **Records**:
  - Machines: 342 (332 + 10 auto-created)
  - Players: 525
  - Scores: 11,040
  - Percentiles: 980
  - Player Stats: 6,058

---

## 🛠️ Useful Commands

### Database
```bash
# Connect to database
psql mnp_analyzer

# Check data counts
psql mnp_analyzer -c "SELECT 'scores' as table, COUNT(*) FROM scores
  UNION ALL SELECT 'players', COUNT(*) FROM players
  UNION ALL SELECT 'machines', COUNT(*) FROM machines;"
```

### Backend
```bash
# Test API health
curl http://localhost:8000/health

# Get players
curl http://localhost:8000/players?limit=5

# Get machines
curl http://localhost:8000/machines?limit=5
```

### Data Reload (if needed)
```bash
conda activate mnp
python etl/load_season.py --season 22
python etl/calculate_percentiles.py --season 22
python etl/calculate_player_stats.py --season 22
```

---

## 🐛 Fixed Issues

During setup, we encountered and fixed several issues:

1. **Score Constraint** - Removed `chk_scores_reasonable` constraint to allow high scores (15.3B on Star Wars)
2. **Missing Venue** - Added special `_ALL_` venue for aggregate statistics
3. **Percentile Query** - Fixed to use `venue_key = '_ALL_'` instead of `IS NULL`
4. **Column Names** - Fixed player stats to use `median_percentile` and `avg_percentile`

All fixes are documented in the code and work as expected.

---

## 📁 Project Structure

```
/Users/JJC/Pinball/MNP/
├── .env                    # Database credentials ✅
├── requirements.txt        # Python dependencies ✅
│
├── schema/                 # Database schema
│   └── migrations/         # SQL migration files
│
├── etl/                    # Data pipeline
│   ├── load_season.py
│   ├── calculate_percentiles.py
│   └── calculate_player_stats.py
│
├── api/                    # FastAPI backend ✅ RUNNING
│   ├── main.py
│   ├── routers/
│   └── models/
│
├── frontend/               # Next.js frontend ✅ READY
│   ├── .env.local         # Environment config ✅
│   ├── node_modules/      # Dependencies ✅
│   ├── app/               # Pages
│   ├── components/        # React components
│   └── lib/               # API client & types
│
└── mnp-data-archive/      # Data source
    └── season-22/
        └── matches/        # 184 JSON files
```

---

## 🎯 Next Steps

### To Start the Frontend

```bash
cd /Users/JJC/Pinball/MNP/frontend
npm run dev
```

Then open http://localhost:3000 in your browser!

### What You'll See

1. **Home Page** - Data summary with total players, machines, matches
2. **Players Page** - Search and filter players, view stats
3. **Player Detail** - Individual player performance by machine
4. **Machines Page** - Browse pinball machines
5. **Machine Detail** - Machine stats with percentile visualizations

---

## 🔧 Environment Details

### Python (Conda)
- **Environment**: `mnp`
- **Python**: 3.12.12
- **Location**: `/usr/local/Caskroom/miniforge/base/envs/mnp`
- **Activation**: `conda activate mnp`

### Node.js
- **Version**: 20.15.0
- **npm**: 10.7.0

### PostgreSQL
- **Version**: 15.15
- **Location**: `/usr/local/opt/postgresql@15`
- **Database**: `mnp_analyzer`
- **User**: `mnp_user`

---

## 📚 Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete setup instructions
- [CURRENT_STATUS.md](CURRENT_STATUS.md) - Project progress and status
- [SESSION_CONTEXT.md](SESSION_CONTEXT.md) - Quick-start context
- [frontend/README.md](frontend/README.md) - Frontend documentation
- [mnp-app-docs/](mnp-app-docs/) - Architecture documentation

---

## ✨ Success!

Your environment is fully configured and ready for development!

**Backend API**: ✅ Running on http://localhost:8000
**Frontend**: ✅ Ready to start with `npm run dev`
**Database**: ✅ Loaded with Season 22 data

Happy coding! 🎯🚀
