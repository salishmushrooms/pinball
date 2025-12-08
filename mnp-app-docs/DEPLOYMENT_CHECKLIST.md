# MNP Deployment Checklist

**Quick Reference Guide for Deployment Tasks**

**Last Updated:** 2025-12-08
**Current Phase:** Phase 4 - Production Deployment ✅ COMPLETE
**Estimated Cost:** $5/month

---

## Production URLs

| Service | URL |
|---------|-----|
| **API (Railway)** | https://pinball-production.up.railway.app |
| **Frontend (Vercel)** | https://pinball-ok0l4282o-jeremys-projects-09dbc42d.vercel.app |
| **API Docs** | https://pinball-production.up.railway.app/docs |

---

## Phase 4: Production Deployment ✅ COMPLETE

### Railway (Backend API + PostgreSQL)
- [x] Create Railway account (railway.app)
- [x] Connect Railway to GitHub repo (salishmushrooms/pinball)
- [x] Create PostgreSQL database on Railway
- [x] Link DATABASE_URL to FastAPI service
- [x] Set Target Port to **8080** (Railway sets PORT=8080)
- [x] Deploy from repo root (not api/ subdirectory)
- [x] Run schema migrations
- [x] Load data from local database
- [x] Test API endpoints

### Vercel (Frontend)
- [x] Connect Vercel to GitHub repo
- [x] Set Root Directory to `frontend` in Vercel dashboard
- [x] Set environment variable: `NEXT_PUBLIC_API_URL=https://pinball-production.up.railway.app`
- [x] Deploy Next.js application
- [x] Test all pages work in production

### Configuration Files (in repo)
- [x] `Procfile` - Uvicorn start command
- [x] `railway.toml` - Railway build/deploy config
- [x] `requirements.txt` (root) - Python dependencies
- [x] `vercel.json` - Vercel framework config
- [x] `.vercelignore` - Excludes api/, reports/, etc.

---

## Key Configuration Details

### Railway Settings
- **Root Directory:** (empty - deploy from repo root)
- **Target Port:** 8080
- **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}`
- **DATABASE_URL:** Linked from PostgreSQL service

### Vercel Settings
- **Root Directory:** `frontend`
- **Framework:** Next.js (auto-detected)
- **Environment Variable:** `NEXT_PUBLIC_API_URL`

### Why Deploy from Repo Root (not api/)
The `api/main.py` imports from `etl/` which is at repo root level:
```python
from api.routers import players, machines, ...
from etl.database import db
```
If Railway deploys from `api/`, these imports fail with `ModuleNotFoundError: No module named 'api'`.

---

## Data Loading Guide

See [DATABASE_OPERATIONS.md](DATABASE_OPERATIONS.md) for detailed instructions on:
- Loading new season data
- Running ETL pipelines
- Recalculating statistics

---

## Rollback Procedures

### If Something Breaks
1. Check Railway/Vercel dashboards for error logs
2. Both platforms support instant rollback to previous deployment
3. Railway has automatic daily backups for PostgreSQL

---

## Resources & Links

### Hosting Platforms
- [Railway Dashboard](https://railway.app/dashboard)
- [Vercel Dashboard](https://vercel.com/dashboard)
- [Cloudflare](https://cloudflare.com) - DNS (existing account)

### Documentation
- [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md) - Full deployment plan
- [DATABASE_OPERATIONS.md](DATABASE_OPERATIONS.md) - Data loading guide
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [Railway Docs](https://docs.railway.app/)
- [Vercel Docs](https://vercel.com/docs)

---

**Last Updated:** 2025-12-08
**Estimated Cost:** $5/month
