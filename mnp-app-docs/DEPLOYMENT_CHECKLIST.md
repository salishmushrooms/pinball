# MNP Deployment Checklist (Simplified)

**Quick Reference Guide for Deployment Tasks**

Use this checklist to track progress through the deployment phases outlined in [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md).

**Last Updated:** 2025-12-07
**Current Phase:** Phase 4 - Production Deployment
**Estimated Cost:** $5/month

---

## Pre-Deployment Setup

### Domain & Branding
- [x] Domain: Using existing domain (subdomain)
- [x] DNS/CDN: Cloudflare (existing account)
- [x] Define color scheme and basic design system ✅ (in frontend/DESIGN_SYSTEM.md)
- [ ] Choose subdomain (e.g., `mnp.yourdomain.com`)
- [ ] Create logo/favicon (optional)
- [ ] Write attribution statement for footer

### Hosting Platform Selection ✅ Complete
- [x] Backend: Railway Hobby ($5/month)
- [x] Frontend: Vercel (free tier)
- [ ] Create Railway account
- [ ] Create Vercel account

---

## ~~Phase 1: Static API~~ (SKIPPED)

**Reason:** Built dynamic API directly - no need for static JSON intermediate.

---

## Phase 2: Dynamic API Backend ✅ COMPLETE (Local)

**Goal:** FastAPI application with PostgreSQL database

### Local Development ✅ Complete
- [x] FastAPI application created in `/api`
- [x] All core endpoints implemented
- [x] Database schema created and tested
- [x] Data loaded from GitHub repo (Season 21 & 22)
- [x] Pydantic schemas for validation
- [x] Local PostgreSQL database working

### API Routers Implemented ✅
- [x] `/api/teams` - Team listings and details
- [x] `/api/players` - Player search and statistics
- [x] `/api/machines` - Machine data and percentiles
- [x] `/api/venues` - Venue information
- [x] `/api/matchups` - Team matchup analysis

### Production Database Setup (Railway)
- [ ] Create PostgreSQL database on Railway
- [ ] Run schema migrations
- [ ] Load data from local database

### API Deployment (Railway)
- [ ] Connect Railway to GitHub repo
- [ ] Configure environment variables (DATABASE_URL)
- [ ] Deploy FastAPI application (auto-detected)
- [ ] Test all API endpoints in production

### Security (Minimal)
- [ ] Configure CORS for production domain
- [ ] Verify no secrets in code/git
- [ ] HTTPS: Automatic via Railway ✅

### API Documentation
- [x] OpenAPI/Swagger docs at `/docs` (auto-generated)

**Phase 2 Production Deployment:** Pending ⏳

---

## Phase 3: Web Frontend ✅ COMPLETE (Local)

**Goal:** Public website for browsing MNP data

### Framework Setup ✅ Complete
- [x] Next.js 16 project created
- [x] Tailwind CSS configured
- [x] TypeScript configured
- [x] ESLint configured

### Core Pages ✅ Complete
- [x] **Homepage** (`/`)
  - [x] Navigation to all sections
  - [x] Overview of data available
- [x] **Team Pages**
  - [x] Team list page (`/teams`)
  - [x] Individual team detail page (`/teams/[team_key]`)
  - [x] Team roster with player stats
  - [x] Team machine statistics
- [x] **Player Pages**
  - [x] Player list/search page (`/players`)
  - [x] Individual player profile (`/players/[player_key]`)
  - [x] Player machine statistics
  - [x] Score history
- [x] **Machine Pages**
  - [x] Machine list page (`/machines`)
  - [x] Individual machine statistics (`/machines/[machine_key]`)
  - [x] Percentile data
  - [x] Scores by venue
- [x] **Venue Pages**
  - [x] Venue list page (`/venues`)
  - [x] Individual venue details (`/venues/[venue_key]`)
  - [x] Machines at venue
- [x] **Matchups Page** (`/matchups`)
  - [x] Team vs team analysis
  - [x] Multi-season support

### Component Library ✅ Complete
- [x] Button component
- [x] Card component
- [x] Badge component
- [x] Alert component
- [x] Input component
- [x] Select component
- [x] MultiSelect component
- [x] Table component
- [x] Tabs component
- [x] Collapsible component
- [x] PageHeader component
- [x] StatCard component
- [x] LoadingSpinner component
- [x] EmptyState component
- [x] SeasonMultiSelect (reusable)
- [x] RoundMultiSelect (reusable)
- [x] FilterPanel component
- [x] Navigation component

### Search & Filtering ✅ Partial
- [x] Season filtering (multi-select)
- [x] Round filtering
- [x] Venue filtering

### Responsive Design ✅ Complete
- [x] Mobile-responsive layouts
- [x] Tailwind responsive utilities
- [x] Touch-friendly navigation

### API Integration ✅ Complete
- [x] TypeScript API client (`/lib/api.ts`)
- [x] Full type definitions (`/lib/types.ts`)
- [x] Loading states
- [x] Error handling
- [x] Multi-season parameter support

### Footer & Legal
- [ ] Add attribution statement
- [ ] Link to official MNP data repository

### Production Deployment (Vercel)
- [ ] Connect Vercel to GitHub repo
- [ ] Set environment variable: `NEXT_PUBLIC_API_URL`
- [ ] Deploy Next.js application
- [ ] Test all pages work in production

### Domain Setup (Cloudflare)
- [ ] Add CNAME record for frontend subdomain → Vercel
- [ ] Add CNAME record for API subdomain → Railway
- [ ] Verify HTTPS works

**Phase 3 Production Deployment:** Pending ⏳

---

## Phase 4: Production Deployment 🎯 CURRENT PHASE

**Goal:** Deploy existing local application to production
**Estimated Cost:** $5/month

### Step 1: Account Setup
- [ ] Create Railway account (railway.app)
- [ ] Create Vercel account (vercel.com)
- [ ] Choose subdomain for existing domain

### Step 2: Backend Deployment (Railway)
- [ ] Connect Railway to GitHub repo
- [ ] Create PostgreSQL database on Railway
- [ ] Configure environment variables (DATABASE_URL)
- [ ] Deploy FastAPI app (auto-detected from repo)
- [ ] Run data migration to production database
- [ ] Test API endpoints

### Step 3: Frontend Deployment (Vercel)
- [ ] Connect Vercel to GitHub repo
- [ ] Set environment variable: `NEXT_PUBLIC_API_URL`
- [ ] Deploy Next.js application
- [ ] Test all pages

### Step 4: Domain Setup (Cloudflare)
- [ ] Add CNAME for frontend subdomain → Vercel
- [ ] Add CNAME for API subdomain → Railway
- [ ] Update CORS settings in API
- [ ] Verify HTTPS works (automatic)

### Step 5: Launch
- [ ] Test end-to-end functionality
- [ ] Share with beta testers
- [ ] Monitor dashboards for errors

**Phase 4 Complete:** API and Website deployed ⏳

---

## Phase 5: Future Enhancements (Optional)

**Add these later if needed:**

### Monitoring & Analytics
- [ ] Sentry for error tracking
- [ ] Plausible for privacy-friendly analytics
- [ ] Uptime monitoring (UptimeRobot)

### Performance
- [ ] Rate limiting (Cloudflare rules or FastAPI middleware)
- [ ] Redis caching on Railway
- [ ] Database indexes for slow queries

### Features
- [ ] Data visualization (Recharts)
- [ ] Global search
- [ ] SEO meta tags / sitemap
- [ ] Automated data sync from GitHub

**Phase 5 Complete:** Enhanced platform ⏳

---

## Ongoing Maintenance

### As Needed
- [ ] Check Railway/Vercel dashboards for errors
- [ ] Update dependencies (security patches)
- [ ] Add new season data when available

---

## Rollback Procedures

### If Something Breaks
1. Check Railway/Vercel dashboards for error logs
2. Both platforms support instant rollback to previous deployment
3. Railway has automatic daily backups for PostgreSQL

---

## Success Metrics

### Phase 4 Success (Production Deployment)
- [ ] API is accessible publicly
- [ ] Website is accessible at subdomain
- [ ] Pages load without errors

---

## Resources & Links

### Hosting Platforms
- [Railway](https://railway.app) - Backend + PostgreSQL
- [Vercel](https://vercel.com) - Frontend
- [Cloudflare](https://cloudflare.com) - DNS (existing account)

### Documentation
- [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md) - Full deployment plan
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [Railway Docs](https://docs.railway.app/)
- [Vercel Docs](https://vercel.com/docs)

---

## Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Static API | SKIPPED | Built dynamic API directly |
| Phase 2: Dynamic API | ✅ Local Complete | Ready for Railway deployment |
| Phase 3: Web Frontend | ✅ Local Complete | Ready for Vercel deployment |
| Phase 4: Production | 🎯 Current | $5/month total |
| Phase 5: Enhancements | Future | Add if needed |

**Next Steps:**
1. Create Railway account
2. Create Vercel account
3. Deploy and configure DNS

---

**Last Updated:** 2025-12-07
**Estimated Cost:** $5/month
