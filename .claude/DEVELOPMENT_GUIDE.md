# MNP Development Guide - Workflows & Commands

> **Purpose**: Common development workflows and commands for AI assistants
> **Last Updated**: 2026-01-02

---

## 🚀 Quick Start

### First Time Setup

```bash
# Clone repository with submodule
git clone https://github.com/yourusername/mnp-data-archive.git
cd MNP
git submodule update --init --recursive

# Set up Python environment
conda create -n mnp python=3.12
conda activate mnp
pip install -r requirements.txt

# Set up PostgreSQL
createdb mnp_analyzer
psql -h localhost -U mnp_user -d mnp_analyzer -f schema/001_complete_schema.sql

# Configure environment
cp .env.example .env
# Edit .env with database credentials

# Load initial data
python etl/load_season.py --season 22
python etl/calculate_percentiles.py
python etl/calculate_player_stats.py

# Set up frontend
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with API URL
```

---

## 📦 Environment Management

### Python Environment

```bash
# Activate environment
conda activate mnp

# Install new dependency
pip install package_name
pip freeze > requirements.txt

# Deactivate
conda deactivate
```

### Frontend Environment

```bash
cd frontend

# Install dependencies
npm install

# Add new package
npm install package_name

# Update packages
npm update
```

### Environment Variables

**Root `.env`** (gitignored):
```bash
# PostgreSQL connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mnp_analyzer
DB_USER=mnp_user
DB_PASSWORD=your_password

# Railway production (optional)
DATABASE_URL=postgresql://user:password@host:port/database
```

**Frontend `.env.local`** (gitignored):
```bash
# API endpoint
NEXT_PUBLIC_API_URL=http://localhost:8000

# Production
# NEXT_PUBLIC_API_URL=https://your-api.railway.app
```

---

## 🔧 Development Server

### Start API (Backend)

```bash
# From repo root
conda activate mnp
uvicorn api.main:app --reload --port 8000

# View at: http://localhost:8000
# API docs: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Start Frontend

```bash
# From frontend directory
cd frontend
npm run dev

# View at: http://localhost:3000
```

### Start Both (Separate Terminals)

```bash
# Terminal 1 - API
conda activate mnp
uvicorn api.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend && npm run dev
```

---

## 🗄️ Database Operations

### Local Database

```bash
# Connect to database
psql -h localhost -U mnp_user -d mnp_analyzer

# Run SQL file
psql -h localhost -U mnp_user -d mnp_analyzer -f schema/001_complete_schema.sql

# Dump database
pg_dump -h localhost -U mnp_user -d mnp_analyzer > backup.sql

# Dump data only (no schema)
pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > data.sql

# Restore database
psql -h localhost -U mnp_user -d mnp_analyzer < backup.sql
```

### Production Database (Railway)

```bash
# Connect to production
railway connect postgres

# View logs
railway logs -s pinball

# Check status
railway status

# Export production data
railway connect postgres -c "pg_dump --data-only --no-owner --no-acl" > production_data.sql

# Import to production
railway connect postgres < data.sql
```

### Common Database Queries

```sql
-- Check loaded seasons
SELECT DISTINCT season FROM matches ORDER BY season;

-- Count matches by season
SELECT season, COUNT(*) FROM matches GROUP BY season ORDER BY season;

-- Check player count
SELECT COUNT(DISTINCT key) FROM players;

-- View recent scores
SELECT * FROM scores ORDER BY id DESC LIMIT 10;

-- Check percentile data
SELECT machine_key, COUNT(*) FROM score_percentiles GROUP BY machine_key;
```

---

## 📊 ETL Pipeline

### Load Season Data

```bash
# Load a specific season
python etl/load_season.py --season 22

# Load multiple seasons
for season in 18 19 20 21 22; do
  python etl/load_season.py --season $season
done
```

### Calculate Aggregates

```bash
# Must run in this order after loading new data

# 1. Calculate score percentiles (required for other calculations)
python etl/calculate_percentiles.py

# 2. Calculate player statistics
python etl/calculate_player_stats.py

# 3. Calculate player totals
python etl/calculate_player_totals.py

# 4. Calculate team machine picks
python etl/calculate_team_machine_picks.py

# 5. Calculate match points
python etl/calculate_match_points.py
```

### Update IPR Data

```bash
# Update IPR ratings from CSV
python etl/update_ipr.py
```

### Full Data Reload

```bash
# Complete data reload from scratch
# WARNING: This drops and recreates all data

# 1. Reset database
psql -h localhost -U mnp_user -d mnp_analyzer -f schema/001_complete_schema.sql

# 2. Load all seasons
for season in 18 19 20 21 22; do
  echo "Loading season $season..."
  python etl/load_season.py --season $season
done

# 3. Calculate all aggregates
python etl/calculate_percentiles.py
python etl/calculate_player_stats.py
python etl/calculate_player_totals.py
python etl/calculate_team_machine_picks.py
python etl/calculate_match_points.py

# 4. Update IPR
python etl/update_ipr.py
```

---

## 🎨 Frontend Development

### Component Development

```bash
# Always check existing components first
ls frontend/components/ui/

# Create new component (if needed)
# Location: frontend/components/ui/ComponentName.tsx
# Export in: frontend/components/ui/index.ts
```

### Type Definitions

```typescript
// Import types from lib/types.ts
import { Player, Team, Machine, Venue } from '@/lib/types'

// Use API client from lib/api.ts
import { api } from '@/lib/api'
```

### Styling

```tsx
// Use Tailwind CSS classes
<div className="container mx-auto p-4">
  <h1 className="text-2xl font-bold">Title</h1>
</div>

// Import UI components
import { Button, Card, Table } from '@/components/ui'
```

### Build for Production

```bash
cd frontend

# Build
npm run build

# Start production server
npm start
```

---

## 🧪 Testing

### API Testing

```bash
# Test endpoints with curl
curl http://localhost:8000/seasons
curl http://localhost:8000/players?search=smith
curl "http://localhost:8000/machines/MM/percentiles?seasons=22"

# Or use API docs
# http://localhost:8000/docs
```

### Frontend Testing

```bash
# Run development server and test manually
cd frontend
npm run dev

# Test production build
npm run build
npm start
```

---

## 📤 Deployment

### Deploy API (Railway)

```bash
# Railway CLI
railway login
railway link
railway up

# View deployment
railway open

# View logs
railway logs

# Set environment variables
railway variables set KEY=value
```

**Railway Configuration:**
- Deploy from: Repo root (not `api/`)
- Start command: In `Procfile`
- Port: 8080 (set via `PORT` env var)
- Database: PostgreSQL addon

### Deploy Frontend (Vercel)

```bash
# Vercel CLI
vercel login
vercel link
vercel deploy

# Production deployment
vercel --prod
```

**Vercel Configuration:**
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `.next`
- Environment variable: `NEXT_PUBLIC_API_URL`

### Full Deployment Workflow

```bash
# 1. Commit changes
git add .
git commit -m "Description of changes"
git push origin main

# 2. API deploys automatically on Railway (connected to GitHub)
# Check: railway logs

# 3. Frontend deploys automatically on Vercel (connected to GitHub)
# Check: vercel logs
```

---

## 🔄 Git Workflow

### Basic Workflow

```bash
# Check status
git status

# Stage changes
git add .

# Commit
git commit -m "Descriptive commit message"

# Push to remote
git push origin main
```

### Working with Submodule

```bash
# Update submodule to latest
git submodule update --remote mnp-data-archive

# Commit submodule update
git add mnp-data-archive
git commit -m "Update data archive"
git push
```

### Branching

```bash
# Create feature branch
git checkout -b feature/new-feature

# Work on feature
git add .
git commit -m "Add new feature"

# Push branch
git push origin feature/new-feature

# Merge to main (after review)
git checkout main
git merge feature/new-feature
git push origin main
```

---

## 🐛 Debugging

### API Debugging

```bash
# View API logs
uvicorn api.main:app --reload --port 8000 --log-level debug

# Check database connections
psql -h localhost -U mnp_user -d mnp_analyzer -c "SELECT version();"

# Test specific endpoint
curl -v http://localhost:8000/seasons
```

### Frontend Debugging

```bash
# Run with verbose logging
npm run dev -- --turbo

# Check build errors
npm run build

# Clear cache and rebuild
rm -rf .next
npm run dev
```

### Database Debugging

```sql
-- Check if data loaded
SELECT COUNT(*) FROM matches;
SELECT COUNT(*) FROM scores;
SELECT COUNT(*) FROM players;

-- Check for missing data
SELECT season, COUNT(*) FROM matches GROUP BY season;

-- Verify percentiles calculated
SELECT machine_key, COUNT(*) FROM score_percentiles GROUP BY machine_key ORDER BY machine_key;
```

---

## 📝 Common Tasks

### Add New Season Data

```bash
# 1. Update submodule
git submodule update --remote mnp-data-archive

# 2. Load new season
python etl/load_season.py --season 23

# 3. Recalculate aggregates
python etl/calculate_percentiles.py
python etl/calculate_player_stats.py
python etl/calculate_player_totals.py
python etl/calculate_team_machine_picks.py
python etl/calculate_match_points.py

# 4. Test locally
curl http://localhost:8000/seasons

# 5. Export data
pg_dump -h localhost -U mnp_user -d mnp_analyzer --data-only --no-owner --no-acl > season_23_data.sql

# 6. Import to production
railway connect postgres < season_23_data.sql

# 7. Verify production
curl https://your-api.railway.app/seasons
```

### Add New API Endpoint

```python
# 1. Create router function in api/routers/[router].py
@router.get("/new-endpoint")
async def new_endpoint():
    # Implementation
    return {"data": "response"}

# 2. Add types in frontend/lib/types.ts
export interface NewType {
  // fields
}

# 3. Add to API client in frontend/lib/api.ts
async getNewData(): Promise<NewType> {
  const response = await fetch(`${this.baseUrl}/new-endpoint`)
  return response.json()
}

# 4. Test
curl http://localhost:8000/new-endpoint
```

### Add New Frontend Page

```bash
# 1. Create page file
mkdir -p frontend/app/new-page
touch frontend/app/new-page/page.tsx

# 2. Implement page component
# Use existing patterns from other pages

# 3. Add navigation link in frontend/components/Navigation.tsx

# 4. Test
# Visit http://localhost:3000/new-page
```

---

## 🆘 Troubleshooting

### "Module not found" errors

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### Database connection errors

```bash
# Check PostgreSQL is running
pg_isready

# Check credentials in .env
cat .env

# Test connection
psql -h localhost -U mnp_user -d mnp_analyzer
```

### Frontend build errors

```bash
# Clear cache
rm -rf frontend/.next
rm -rf frontend/node_modules
cd frontend && npm install
npm run build
```

### Submodule issues

```bash
# Reset submodule
git submodule deinit -f mnp-data-archive
git submodule update --init --recursive
```

---

**Note**: For production operations, always test changes locally first, then deploy to production.
