# MNP Deployment Checklist

**Quick Reference Guide for Deployment Tasks**

Use this checklist to track progress through the deployment phases outlined in [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md).

**Last Updated:** 2025-11-29
**Current Phase:** Phase 4 - Production Deployment

---

## Pre-Deployment Setup

### Domain & Branding
- [ ] Choose final domain name
  - Options: `mnpstats.com`, `mnpdata.io`, `mondaynightpinball.app`
  - Check availability at Namecheap, Google Domains, or Cloudflare
- [ ] Register domain ($10-15/year)
- [ ] Point DNS to Cloudflare (free tier)
- [ ] Create logo/favicon
- [x] Define color scheme and basic design system ✅ (in frontend/DESIGN_SYSTEM.md)
- [ ] Write attribution statement for footer

### Hosting Platform Selection
- [ ] Compare hosting providers (Railway vs Render)
- [ ] Create account on chosen platform
- [ ] Set up payment method
- [ ] Review pricing and resource limits

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

### Docker Configuration (For Production)
- [ ] Create `Dockerfile` for FastAPI app
- [ ] Create `docker-compose.yml` for local testing
- [ ] Test Docker build locally
- [ ] Optimize image size (multi-stage build)

### Production Database Setup
- [ ] Choose PostgreSQL provider (Railway recommended)
- [ ] Create production database
- [ ] Run schema migrations
- [ ] Load data from local database
- [ ] Set up connection pooling
- [ ] Configure backup schedule (daily)

### API Deployment
- [ ] Create project on Railway/Render
- [ ] Configure environment variables (DATABASE_URL, etc.)
- [ ] Deploy FastAPI application
- [ ] Connect to managed PostgreSQL
- [ ] Test all API endpoints in production
- [ ] Verify database queries work correctly

### Performance & Caching
- [ ] Add database indexes for common queries
- [ ] Configure connection pooling
- [ ] Test response times (<1s for most queries)
- [ ] Set up Redis instance (optional, for caching)

### Security & Rate Limiting
- [ ] Add CORS middleware configuration for production domain
- [ ] Implement rate limiting (100-1000 requests/hour per IP)
- [ ] Create read-only database user for API
- [ ] Configure HTTPS (automatic with Railway/Render)
- [ ] Add security headers (HSTS, CSP, etc.)
- [ ] Verify no secrets in code/git

### Monitoring & Logging
- [ ] Set up Sentry account for error tracking
- [ ] Configure Sentry in FastAPI app
- [ ] Set up uptime monitoring (Better Uptime, UptimeRobot)
- [ ] Configure alerts (email for downtime)
- [ ] Review logs in hosting platform dashboard

### API Documentation
- [x] OpenAPI/Swagger docs at `/docs` (auto-generated)
- [ ] Add description and examples to endpoints
- [ ] Create getting-started guide for external users

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

### Data Visualization
- [ ] Choose charting library (Recharts recommended)
- [ ] Create score distribution charts
- [ ] Create percentile visualizations
- [ ] Add performance trend charts
- [ ] Make charts responsive (mobile-friendly)

### Search & Filtering ✅ Partial
- [x] Season filtering (multi-select)
- [x] Round filtering
- [x] Venue filtering
- [ ] Add global search bar
- [ ] Add sorting options

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
- [ ] Add about/contact info
- [ ] Create privacy policy (if collecting analytics)

### Production Deployment
- [ ] Deploy to Vercel
- [ ] Configure custom domain
- [ ] Set environment variables (API URL)
- [ ] Test production build
- [ ] Verify all pages work in production

### SEO & Analytics
- [ ] Add meta tags for SEO
- [ ] Create sitemap.xml
- [ ] Set up Plausible or Simple Analytics
- [ ] Add Open Graph tags for social sharing

### Testing
- [ ] Test all navigation links
- [ ] Verify data accuracy
- [ ] Test performance (Lighthouse score)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)

**Phase 3 Production Deployment:** Pending ⏳

---

## Phase 4: Production Deployment 🎯 CURRENT PHASE

**Goal:** Deploy existing local application to production

### Step 1: Pre-Deployment Setup (Day 1-2)
- [ ] Choose and register domain name
- [ ] Create accounts on hosting platforms (Railway, Vercel)
- [ ] Set up Cloudflare for DNS
- [ ] Create Sentry account for monitoring

### Step 2: Backend Deployment (Day 3-5)
- [ ] Create `Dockerfile` for FastAPI app
- [ ] Deploy to Railway/Render
- [ ] Create production PostgreSQL database
- [ ] Run data migration to production
- [ ] Configure environment variables
- [ ] Test all API endpoints in production
- [ ] Set up rate limiting

### Step 3: Frontend Deployment (Day 6-8)
- [ ] Configure Vercel project
- [ ] Set production environment variables
- [ ] Deploy Next.js application
- [ ] Configure custom domain
- [ ] Test all pages in production
- [ ] Verify API integration

### Step 4: Production Hardening (Day 9-10)
- [ ] Configure HTTPS (automatic)
- [ ] Set up Sentry error monitoring
- [ ] Configure uptime monitoring
- [ ] Add security headers
- [ ] Test CORS configuration
- [ ] Load test API endpoints

### Step 5: Launch (Day 11-14)
- [ ] Soft launch to beta testers
- [ ] Monitor for errors
- [ ] Gather feedback
- [ ] Fix any critical issues
- [ ] Public announcement

**Phase 4 Complete:** API and Website deployed ⏳

---

## Phase 5: Advanced Features (Future)

**Goal:** Community features and automation

### User Accounts (Optional)
- [ ] Choose auth provider (Supabase Auth, Auth0, Clerk)
- [ ] Implement sign up/login
- [ ] Create user profile pages
- [ ] Add "favorite teams" feature
- [ ] Add "favorite players" feature

### Notifications (Optional)
- [ ] Set up email service (SendGrid, Mailgun)
- [ ] Create notification preferences UI
- [ ] Implement weekly summary emails

### Admin Dashboard
- [ ] Create admin authentication
- [ ] Build data management UI
- [ ] Add manual data correction tools

### API Enhancements
- [ ] Add API key system for high-volume users
- [ ] Create tiered rate limits
- [ ] Add webhook support (for Pin Stats app)

### Automated Data Updates
- [ ] Create script to sync data from GitHub repo
- [ ] Set up GitHub Action or cron job for automated sync
- [ ] Document manual update procedure

**Phase 5 Complete:** Full-featured community platform ⏳

---

## Ongoing Maintenance

### Weekly Tasks
- [ ] Monitor API uptime and performance
- [ ] Check error logs in Sentry
- [ ] Review traffic analytics
- [ ] Verify data sync is working

### Monthly Tasks
- [ ] Review hosting costs
- [ ] Update dependencies (security patches)
- [ ] Analyze usage patterns
- [ ] Optimize slow queries

### Seasonal Tasks
- [ ] Prepare for new season data
- [ ] Update season selectors in UI
- [ ] Generate end-of-season reports

---

## Rollback Procedures

### If API Goes Down
1. Check hosting platform status page
2. Review error logs in Sentry
3. Check database connection
4. Verify environment variables
5. Rollback to previous deployment if needed

### If Database Issues Occur
1. Check database connection limits
2. Review slow query log
3. Verify backups are recent
4. Restore from backup if needed
5. Contact hosting provider support

### If Frontend Issues Occur
1. Check Vercel deployment logs
2. Test API endpoints separately
3. Review browser console errors
4. Rollback to previous deployment

---

## Success Metrics

### Phase 4 Success (Production Deployment)
- [ ] API is accessible publicly
- [ ] Website is accessible at custom domain
- [ ] Response time <1s for 95% of requests
- [ ] 99% uptime in first week
- [ ] Zero critical errors

### Post-Launch Success (30 days)
- [ ] 100+ unique visitors
- [ ] 1000+ API requests
- [ ] Positive community feedback
- [ ] <5 bug reports
- [ ] 99.5% uptime

---

## Resources & Links

### Documentation
- [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md) - Full deployment plan
- [MNP_Data_Structure_Reference.md](../MNP_Data_Structure_Reference.md) - Data structure
- [RESTART_GUIDE.md](../RESTART_GUIDE.md) - Local development restart guide
- [frontend/DESIGN_SYSTEM.md](../frontend/DESIGN_SYSTEM.md) - UI design system

### Tools & Services
- **Domain Registration:** Namecheap, Google Domains, Cloudflare
- **Frontend Hosting:** Vercel (recommended)
- **Backend Hosting:** Railway (recommended), Render
- **Database:** PostgreSQL (managed by hosting provider)
- **CDN:** Cloudflare (free tier)
- **Monitoring:** Sentry, Better Uptime
- **Analytics:** Plausible, Simple Analytics

### External Links
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Railway Documentation](https://docs.railway.app/)
- [Vercel Documentation](https://vercel.com/docs)

---

## Summary of Current Progress

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Static API | SKIPPED | Built dynamic API directly |
| Phase 2: Dynamic API | ✅ Local Complete | Ready for production deployment |
| Phase 3: Web Frontend | ✅ Local Complete | Ready for production deployment |
| Phase 4: Production | 🎯 Current | Next step: domain & hosting setup |
| Phase 5: Advanced | Future | Post-launch enhancements |

**Immediate Next Steps:**
1. Choose and register domain name
2. Create Railway account for backend
3. Create Vercel account for frontend
4. Begin production deployment

---

**Last Updated:** 2025-11-29
**Document Owner:** JJC
