# MNP Analyzer - Quick Start Guide

> **For detailed workflows**: See [.claude/DEVELOPMENT_GUIDE.md](.claude/DEVELOPMENT_GUIDE.md)

---

## 🔄 Daily Development (Restart Services)

**Already have the project set up?** Use these commands:

### Restart API
```bash
conda activate mnp
uvicorn api.main:app --reload --port 8000
```

### Restart Frontend
```bash
cd frontend
npm run dev
```

### Force Kill (if needed)
```bash
lsof -ti:3000 | xargs kill -9  # Kill frontend
lsof -ti:8000 | xargs kill -9  # Kill API
```

---

## 🚀 Initial Setup (First Time)

**Setting up for the first time?** Follow these steps:

### 1. Python Environment
```bash
conda create -n mnp python=3.12
conda activate mnp
pip install -r requirements.txt
```

### 2. PostgreSQL Database
```bash
createdb mnp_analyzer
psql -h localhost -U mnp_user -d mnp_analyzer -f schema/001_complete_schema.sql
```

### 3. Environment Variables
Create a `.env` file in the project root:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mnp_analyzer
DB_USER=mnp_user
DB_PASSWORD=your_password
```

### 4. Load Data
```bash
python etl/load_season.py --season 22
python etl/calculate_percentiles.py
python etl/calculate_player_stats.py
```

### 5. Start Services
```bash
# Terminal 1 - API
uvicorn api.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend && npm install && npm run dev
```

---

## 📚 Additional Resources

- **[README.md](README.md)** - Project overview
- **[.claude/DEVELOPMENT_GUIDE.md](.claude/DEVELOPMENT_GUIDE.md)** - Complete development workflows
- **[mnp-app-docs/DATABASE_OPERATIONS.md](mnp-app-docs/DATABASE_OPERATIONS.md)** - Database operations
- **API Docs**: http://localhost:8000/docs (when running)
