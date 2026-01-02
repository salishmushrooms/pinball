# MNP Analyzer - Setup Guide

> **Note**: This guide has been consolidated into the comprehensive development guide.
>
> **See**: [.claude/DEVELOPMENT_GUIDE.md](.claude/DEVELOPMENT_GUIDE.md) for complete setup instructions

---

## 🚀 Quick Setup

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
```bash
# Create .env file with:
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

For detailed setup, troubleshooting, and configuration options, see:
- [.claude/DEVELOPMENT_GUIDE.md](.claude/DEVELOPMENT_GUIDE.md) - Complete development workflows
- [mnp-app-docs/DATABASE_OPERATIONS.md](mnp-app-docs/DATABASE_OPERATIONS.md) - Database operations
- [README.md](README.md) - Project overview
