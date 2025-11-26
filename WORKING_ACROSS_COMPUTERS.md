# Working Across Multiple Computers - Guide

**Purpose**: How to sync your work between computers when you have a local database

---

## 🎯 Quick Summary

**What syncs via Git:**
- ✅ Code (frontend, backend, ETL scripts)
- ✅ Configuration files (`.env`, `package.json`, `requirements.txt`)
- ✅ Schema files (`schema/migrations/*.sql`)
- ✅ Documentation

**What DOESN'T sync via Git:**
- ❌ Database data (PostgreSQL)
- ❌ `node_modules/` (frontend dependencies)
- ❌ `__pycache__/`, `.next/` (build artifacts)
- ❌ Python virtual environment

---

## 📋 Syncing Workflow

### Computer A → Computer B (Your Scenario)

You're on **Computer B (Mini)** now and made changes.
You want to work on **Computer A (Laptop)** later.

#### Step 1: Commit Changes on Computer B (Mini)

```bash
cd /Users/JJC/Pinball/MNP

# Check what changed
git status

# Stage all changes
git add .

# Commit with a descriptive message
git commit -m "Fixed frontend API integration and search functionality"

# Push to remote
git push origin main
```

#### Step 2: Pull Changes on Computer A (Laptop)

```bash
cd /path/to/MNP  # wherever it is on laptop

# Pull latest changes
git pull origin main

# Install any new Python dependencies (if requirements.txt changed)
conda activate mnp
pip install -r requirements.txt

# Install any new frontend dependencies (if package.json changed)
cd frontend
npm install
```

#### Step 3: Database on Computer A

**IMPORTANT**: The database data is NOT synced via Git!

You have two options:

**Option A: Reload Data from Source (Recommended)**
```bash
# On Computer A (Laptop)
cd /path/to/MNP
conda activate mnp

# Make sure database exists and schema is up to date
cd schema
./setup_database.sh

# Load Season 22 data
cd ..
python etl/load_season.py --season 22
python etl/calculate_percentiles.py --season 22
python etl/calculate_player_stats.py --season 22
```

**Option B: Export/Import Database (For Complex Data)**

If you've made custom changes to the database:

```bash
# On Computer B (Mini) - Export
pg_dump mnp_analyzer > ~/Desktop/mnp_backup.sql

# Transfer file to Computer A (via iCloud, USB, etc.)

# On Computer A (Laptop) - Import
psql mnp_analyzer < ~/Desktop/mnp_backup.sql
```

---

## 🔧 Setting Up a New Computer

If you're setting up on a completely new computer:

### Full Setup Checklist

```bash
# 1. Clone repository
git clone https://github.com/your-repo/MNP.git  # or use existing clone
cd MNP

# 2. Install PostgreSQL 15
brew install postgresql@15
brew services start postgresql@15
echo 'export PATH="/usr/local/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 3. Set up database
cd schema
./setup_database.sh

# 4. Create Python environment
conda create -n mnp python=3.12 -y
conda activate mnp
pip install -r requirements.txt

# 5. Load data
python etl/load_season.py --season 22
python etl/calculate_percentiles.py --season 22
python etl/calculate_player_stats.py --season 22

# 6. Set up frontend
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# 7. Test everything
# Terminal 1: Start backend
python -m uvicorn api.main:app --reload

# Terminal 2: Start frontend
cd frontend
npm run dev
```

---

## 📝 What to Commit vs. Ignore

### ✅ ALWAYS Commit (Already in Git)

- `*.py` - All Python code
- `*.tsx`, `*.ts`, `*.js` - All frontend code
- `*.sql` - Database schema files
- `*.md` - Documentation
- `*.json` - Config files (except with secrets)
- `.env.example` - Template (without real credentials)
- `requirements.txt` - Python dependencies
- `package.json`, `package-lock.json` - Frontend dependencies

### ❌ NEVER Commit (In `.gitignore`)

- `.env` - Contains database password
- `node_modules/` - Frontend dependencies (reinstall with `npm install`)
- `.next/` - Next.js build output
- `__pycache__/` - Python bytecode
- `*.pyc` - Compiled Python files
- Database files (PostgreSQL stores data elsewhere)
- Virtual environments (`venv/`, conda envs)

---

## 🔄 Typical Work Session Flow

### Starting Work on Any Computer

```bash
# 1. Pull latest changes
git pull origin main

# 2. Ensure dependencies are current
conda activate mnp
pip install -r requirements.txt  # only if requirements.txt changed

cd frontend
npm install  # only if package.json changed

# 3. Start development
# Terminal 1: Backend
python -m uvicorn api.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Ending Work Session

```bash
# 1. Check what changed
git status
git diff

# 2. Commit your changes
git add .
git commit -m "Descriptive message about what you did"

# 3. Push to remote
git push origin main
```

---

## 🚨 Common Issues & Solutions

### Issue 1: "Database doesn't exist" on other computer

**Solution**: The database only exists locally. Run the setup:
```bash
cd schema
./setup_database.sh
python ../etl/load_season.py --season 22
```

### Issue 2: "Module not found" errors (Python)

**Solution**: Dependencies not installed
```bash
conda activate mnp
pip install -r requirements.txt
```

### Issue 3: "Module not found" errors (Frontend)

**Solution**: Node modules not installed
```bash
cd frontend
npm install
```

### Issue 4: API connection refused (Frontend can't reach backend)

**Solution**: Backend not running
```bash
python -m uvicorn api.main:app --reload
```

### Issue 5: `.env.local` missing (Frontend)

**Solution**: Create it manually on each computer
```bash
cd frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### Issue 6: Git conflicts in `package-lock.json` or similar

**Solution**: Regenerate on your computer
```bash
cd frontend
rm package-lock.json
npm install
git add package-lock.json
git commit -m "Regenerate package-lock.json"
```

---

## 💡 Best Practices

### 1. Keep Database Schema in Sync

The schema files (`schema/migrations/*.sql`) ARE in git, so:
- If you modify schema on Computer A, commit it
- On Computer B, run the new migration scripts
- Keep migration files numbered and never edit old ones

### 2. Use Branches for Experimental Work

```bash
# Create a feature branch
git checkout -b feature/new-report-type

# Work on feature
# ... make changes ...

# Commit and push
git add .
git commit -m "Add new report type"
git push origin feature/new-report-type

# Later, merge to main
git checkout main
git merge feature/new-report-type
git push origin main
```

### 3. Document Database Changes

If you manually change data in the database (not via ETL):
- Document it in a markdown file
- Consider creating a migration script
- Or just note that you'll need to re-run ETL on other computer

### 4. Keep a `.env.example` Template

Create this file (commit it to git):
```bash
# .env.example
DATABASE_URL=postgresql://mnp_user:YOUR_PASSWORD@localhost:5432/mnp_analyzer
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mnp_analyzer
DB_USER=mnp_user
DB_PASSWORD=YOUR_PASSWORD
```

Then on each computer:
```bash
cp .env.example .env
# Edit .env with real password
```

---

## 📊 Database Sync Strategies

### Strategy 1: Always Reload from Source (Simplest)

**Pros**:
- Always have fresh data
- No sync issues
- Fast (~20 seconds)

**Cons**:
- Any manual database changes are lost

**When to use**: When your data comes from `mnp-data-archive/` (your case!)

### Strategy 2: Export/Import Database

**Pros**:
- Preserves any manual changes
- Faster for large databases

**Cons**:
- Extra steps
- File transfer needed

**When to use**: When you've manually edited data or have large custom datasets

```bash
# Export (Computer A)
pg_dump mnp_analyzer > mnp_backup_$(date +%Y%m%d).sql

# Import (Computer B)
psql mnp_analyzer < mnp_backup_20251124.sql
```

### Strategy 3: Cloud Database (Advanced)

**Pros**:
- Automatically synced
- Accessible from anywhere

**Cons**:
- Costs money
- Requires network
- More complex setup

**When to use**: Production deployments, team collaboration

---

## ✅ Pre-Sync Checklist

Before switching computers, verify:

- [ ] All changes committed (`git status` should be clean)
- [ ] Changes pushed to remote (`git push`)
- [ ] No uncommitted database schema changes
- [ ] Documentation updated if needed

---

## 🎯 Your Current Setup

### Computer B (Mini) - This Computer
- **Status**: ✅ Fully set up and working
- **Database**: Loaded with Season 22 data
- **Backend**: Running
- **Frontend**: Running and fixed

### Computer A (Laptop) - Your Other Computer
- **Status**: Needs update
- **To Do**:
  1. `git pull` to get latest code changes
  2. Check if database still has data (or reload)
  3. `npm install` in frontend (if needed)
  4. Start working!

---

## 📚 Quick Reference Commands

```bash
# Git Operations
git status                  # Check what changed
git pull                    # Get latest from remote
git add .                   # Stage all changes
git commit -m "message"     # Commit changes
git push origin main        # Push to remote

# Python Environment
conda activate mnp          # Activate environment
pip install -r requirements.txt   # Install dependencies

# Database
psql mnp_analyzer          # Connect to database
pg_dump mnp_analyzer > backup.sql   # Backup
psql mnp_analyzer < backup.sql      # Restore

# Start Development
python -m uvicorn api.main:app --reload   # Backend
cd frontend && npm run dev                 # Frontend
```

---

## 🎉 Summary

**The key insight**: Your database is LOCAL to each computer. The source data (`mnp-data-archive/`) IS synced via git, so you can always reload.

**Simplest workflow**:
1. Commit and push code changes
2. Pull on other computer
3. Reload database from source (fast!)
4. Keep coding

This is actually a great development workflow because you can experiment freely knowing you can always get back to clean data!

---

**Last Updated**: 2025-11-24
**For Questions**: Check SETUP_GUIDE.md or ENVIRONMENT_SETUP_COMPLETE.md
