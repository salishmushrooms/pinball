# MNP Analyzer - Development Environment Setup Guide

**Computer**: New Development Machine
**Date**: 2025-11-24
**Purpose**: Complete setup instructions for running the MNP Analyzer app (backend + frontend)

---

## 📋 Prerequisites

Before starting, ensure you have:

1. **PostgreSQL 15** installed and running
2. **Python 3.12+** installed
3. **Node.js 18+** and npm installed
4. **Conda** or **venv** for Python environment management
5. **Git** (already set up based on git status)

---

## 🚀 Quick Start (Step-by-Step)

### Step 1: Check Current Directory

```bash
cd /Users/JJC/Pinball/MNP
pwd  # Should show: /Users/JJC/Pinball/MNP
```

### Step 2: Set Up Python Environment

**Option A: Using Conda (Recommended)**

```bash
# Check if mnp environment exists
conda env list

# If it doesn't exist, create it
conda create -n mnp python=3.12 -y

# Activate the environment
conda activate mnp

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import uvicorn; import fastapi; import sqlalchemy; print('✓ All dependencies installed')"
```

**Option B: Using venv**

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Verify Database Setup

```bash
# Check if PostgreSQL is running
pg_isready

# If not running, start it (macOS with Homebrew)
brew services start postgresql@15

# Check database exists and has data
psql -d mnp_analyzer -c "
SELECT
  'machines' as table, COUNT(*) FROM machines
  UNION ALL SELECT 'scores', COUNT(*) FROM scores
  UNION ALL SELECT 'players', COUNT(*) FROM players;
"

# Expected output:
#   table    | count
# -----------+-------
#  machines  |   341
#  scores    | 10680
#  players   |   523
```

**If database is empty or doesn't exist**, you'll need to:

```bash
# Create database and schema (if needed)
cd schema
./setup_database.sh

# Load Season 22 data
cd ..
python etl/load_season.py --season 22

# Calculate percentiles and stats
python etl/calculate_percentiles.py --season 22
python etl/calculate_player_stats.py --season 22
```

### Step 4: Start Backend API

```bash
# Make sure you're in the project root and conda env is activated
cd /Users/JJC/Pinball/MNP
conda activate mnp  # or source venv/bin/activate

# Start the FastAPI server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process
```

**Test the API**:

Open a new terminal and run:

```bash
# Test health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","database":"connected","timestamp":"..."}

# Test players endpoint
curl http://localhost:8000/players?limit=3

# Browse API docs
# Open in browser: http://localhost:8000/docs
```

### Step 5: Set Up Frontend

Open a **new terminal** (keep the API running in the first terminal):

```bash
# Navigate to frontend directory
cd /Users/JJC/Pinball/MNP/frontend

# Install Node.js dependencies
npm install

# Create environment configuration
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# Start the development server
npm run dev

# You should see:
# ▲ Next.js 14.x.x
# - Local:        http://localhost:3000
# - Ready in 2.5s
```

**Test the Frontend**:

Open your browser to: http://localhost:3000

You should see the MNP Analyzer home page with:
- Total players, machines, matches, scores
- Links to Players and Machines pages

---

## 🧪 Verify Everything Works

### Backend Tests

```bash
# Terminal 1 - API should be running on port 8000
curl http://localhost:8000/health
curl http://localhost:8000/players?limit=1
curl http://localhost:8000/machines?limit=1
```

### Frontend Tests

1. Open http://localhost:3000
2. Click "Browse Players" → Should show player list
3. Click on any player → Should show player details and machine stats
4. Click "Browse Machines" → Should show machine list
5. Click on any machine → Should show machine details with percentiles

### Integration Test

The frontend repo includes an integration test script:

```bash
cd /Users/JJC/Pinball/MNP/frontend
node test-api-integration.js
```

---

## 📂 Project Structure Overview

```
/Users/JJC/Pinball/MNP/
├── .env                          # Database credentials
├── requirements.txt              # Python dependencies
│
├── schema/                       # Database schema and migrations
│   ├── migrations/
│   └── setup_database.sh
│
├── etl/                          # ETL pipeline
│   ├── load_season.py           # Load match data
│   ├── calculate_percentiles.py # Calculate score percentiles
│   └── calculate_player_stats.py # Calculate player stats
│
├── api/                          # FastAPI backend
│   ├── main.py                  # Main API entry point
│   ├── routers/                 # API endpoints
│   │   ├── players.py
│   │   └── machines.py
│   └── models/                  # Pydantic models
│
├── frontend/                     # Next.js frontend
│   ├── app/                     # Pages (App Router)
│   │   ├── page.tsx             # Home page
│   │   ├── players/
│   │   └── machines/
│   ├── components/              # React components
│   ├── lib/
│   │   ├── api.ts              # API client
│   │   └── types.ts            # TypeScript types
│   ├── package.json
│   ├── .env.local              # Frontend config (create this!)
│   └── node_modules/           # Dependencies (npm install)
│
└── mnp-data-archive/            # Data source (git submodule)
    └── season-22/
        └── matches/*.json
```

---

## 🔧 Common Issues & Solutions

### Issue: "conda: command not found"

**Solution**: Initialize conda in your shell

```bash
# Add conda to PATH
echo 'export PATH="/opt/homebrew/anaconda3/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Or find where conda is installed
which conda
ls -la ~/anaconda3/bin/conda
ls -la /opt/homebrew/anaconda3/bin/conda
```

### Issue: "psql: command not found"

**Solution**: Add PostgreSQL to PATH

```bash
# For Homebrew PostgreSQL 15
echo 'export PATH="/usr/local/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Or use full path
/usr/local/opt/postgresql@15/bin/psql mnp_analyzer
```

### Issue: "Database 'mnp_analyzer' does not exist"

**Solution**: Run database setup

```bash
cd /Users/JJC/Pinball/MNP/schema
./setup_database.sh
```

### Issue: "Module not found: uvicorn, fastapi, etc."

**Solution**: Make sure conda environment is activated and dependencies installed

```bash
conda activate mnp
pip install -r requirements.txt
```

### Issue: "ECONNREFUSED localhost:8000" (Frontend can't reach API)

**Solution**: Make sure the FastAPI server is running

```bash
# Check if API is running
curl http://localhost:8000/health

# If not running, start it in a separate terminal
python -m uvicorn api.main:app --reload
```

### Issue: "node_modules missing" or npm errors

**Solution**: Install frontend dependencies

```bash
cd /Users/JJC/Pinball/MNP/frontend
npm install
```

### Issue: Frontend shows "Failed to fetch" errors

**Solution**: Check `.env.local` exists and API URL is correct

```bash
cd /Users/JJC/Pinball/MNP/frontend
cat .env.local
# Should show: NEXT_PUBLIC_API_URL=http://localhost:8000

# If missing, create it:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

---

## 🎯 What You Should See When Everything Works

### Terminal 1 (Backend API)
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2 (Frontend Dev Server)
```
▲ Next.js 14.2.18
- Local:        http://localhost:3000
- Environments: .env.local

✓ Ready in 2.1s
```

### Browser (http://localhost:3000)
- Home page with data summary
- Navigation bar with Players and Machines links
- Functioning search and filter controls
- Player detail pages showing machine stats
- Machine detail pages showing percentile charts

---

## 📚 Reference Documentation

- [CURRENT_STATUS.md](CURRENT_STATUS.md) - Current project status and progress
- [SESSION_CONTEXT.md](SESSION_CONTEXT.md) - Quick-start context for development
- [frontend/README.md](frontend/README.md) - Frontend-specific documentation
- [mnp-app-docs/](mnp-app-docs/) - Complete architecture documentation

---

## 🚦 Environment Variables Summary

### Backend (.env in project root)
```bash
DATABASE_URL=postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mnp_analyzer
DB_USER=mnp_user
DB_PASSWORD=changeme
```

### Frontend (.env.local in frontend/)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## ✅ Setup Checklist

Use this checklist to verify your setup:

- [ ] Python 3.12+ installed
- [ ] Conda environment created and activated
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] PostgreSQL 15 running
- [ ] Database `mnp_analyzer` exists with data
- [ ] `.env` file exists in project root
- [ ] Backend API starts successfully (`python -m uvicorn api.main:app --reload`)
- [ ] API health check returns 200 (`curl http://localhost:8000/health`)
- [ ] Node.js 18+ and npm installed
- [ ] Frontend dependencies installed (`npm install`)
- [ ] `.env.local` file created in `frontend/`
- [ ] Frontend dev server starts (`npm run dev`)
- [ ] Frontend loads at http://localhost:3000
- [ ] Can browse players and machines
- [ ] Player detail pages work
- [ ] Machine detail pages work

---

## 🎉 You're Ready!

Once all checklist items are complete, you have a fully functional development environment for the MNP Analyzer app.

**Next steps**:
- Explore the app at http://localhost:3000
- Try searching for players and machines
- View the API documentation at http://localhost:8000/docs
- Make changes to the code (both backend and frontend support hot reload)

**Happy coding!** 🚀
