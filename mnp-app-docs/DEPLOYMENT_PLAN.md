# Monday Night Pinball - Public Deployment Plan

**Document Version**: 3.0
**Created**: 2025-11-26
**Last Updated**: 2025-12-07
**Status**: Phase 3 Complete (Local Development) - Ready for Production Deployment

---

## Executive Summary

This document outlines the strategy for deploying the Monday Night Pinball (MNP) data platform with a public web API and interface. The MNP data is already public (GitHub repository), players have consented, and this will be an independent platform with branding that references Monday Night Pinball.

**Key Decisions Made:**
- ✅ Data is already public and accessible
- ✅ Players have consented to public data sharing
- ✅ Independent branding (references MNP, not official)
- ✅ Next.js frontend framework selected
- ✅ FastAPI backend framework selected
- ✅ PostgreSQL database implemented
- ✅ Using existing domain (subdomain)
- ✅ Cloudflare for DNS/CDN (existing account)
- ✅ Simplified deployment (no Docker, Sentry, rate limiting initially)

---

## Current State Assessment (November 2025)

### ✅ Completed Components

1. **Backend API** (`api/`)
   - FastAPI application fully functional
   - 5 routers: teams, players, machines, venues, matchups
   - PostgreSQL database with Season 21 & 22 data
   - Comprehensive Pydantic schemas
   - Local development environment working

2. **Frontend Application** (`frontend/`)
   - Next.js 16 with App Router
   - TypeScript with full type safety
   - 10 pages implemented:
     - Home page with navigation
     - Teams list + Team detail pages
     - Players list + Player detail pages
     - Machines list + Machine detail pages
     - Venues list + Venue detail pages
     - Matchups analysis page
   - 15+ reusable UI components:
     - Button, Card, Badge, Alert, Input, Select
     - MultiSelect, Table, Tabs, Collapsible
     - PageHeader, StatCard, LoadingSpinner, EmptyState
     - SeasonMultiSelect, RoundMultiSelect, FilterPanel
   - Design system with CSS variables
   - Mobile-responsive layouts
   - Multi-season data support

3. **Data Pipeline** (`reports/`)
   - Python report generators
   - Config-driven analysis
   - Season 21 & 22 data loaded

4. **Development Infrastructure**
   - Local PostgreSQL database
   - Conda environment (`mnp`)
   - Hot-reload development servers
   - Git version control

### 🔜 Remaining for Production

1. **Infrastructure**
   - Choose and configure hosting platform
   - Set up production database
   - Configure environment variables
   - Set up CI/CD pipeline

2. **Domain & Branding**
   - Register domain name
   - Configure DNS
   - Create logo/favicon

3. **Production Hardening**
   - Add rate limiting
   - Configure CORS for production
   - Set up monitoring (Sentry)
   - Add uptime monitoring
   - Enable HTTPS

---

## Deployment Architecture (Simplified)

### Platform-as-a-Service (Minimal Cost)

**Components:**
- **Frontend**: Vercel (free tier)
- **Backend + Database**: Railway Hobby ($5/month)
- **DNS/CDN/SSL**: Cloudflare (existing account)
- **Domain**: Existing domain (subdomain)

**Total Estimated Cost: $5/month**

**Why This Approach:**
- Minimal cost with existing Cloudflare setup
- No Docker configuration needed (Railway deploys from GitHub)
- No complex DevOps
- Built-in CI/CD from GitHub
- Can add monitoring/caching/rate limiting later if needed

---

## Revised Phased Deployment

### ~~Phase 1: Static Data API~~ (SKIPPED)

**Reason:** We built a dynamic API directly - no need for static JSON intermediate step.

---

### ~~Phase 2: Dynamic API Backend~~ ✅ COMPLETE (Local)

**Status:** Fully implemented and running locally

**What Was Built:**
- FastAPI application with all endpoints
- PostgreSQL database with full schema
- Season 21 & 22 data loaded
- Comprehensive API with:
  - `/api/teams` - Team listings and details
  - `/api/players` - Player search and statistics
  - `/api/machines` - Machine data and percentiles
  - `/api/venues` - Venue information
  - `/api/matchups` - Team matchup analysis

**What Remains for Production:**
- [ ] Deploy to Railway (direct from GitHub, no Docker needed)
- [ ] Set up production PostgreSQL on Railway
- [ ] Configure environment variables
- [ ] Enable CORS for production domain

---

### ~~Phase 3: Web Frontend~~ ✅ COMPLETE (Local)

**Status:** Fully implemented and running locally

**What Was Built:**
- Next.js 16 application
- 10 pages covering all core features:
  - Home page with navigation
  - Teams browsing and detail pages
  - Players search and profile pages
  - Machines list and statistics
  - Venues directory and details
  - Matchups analysis tool
- 15+ reusable UI components
- Design system with consistent styling
- Mobile-responsive layouts
- Multi-season data filtering
- TypeScript API client with full types

**What Remains for Production:**
- [ ] Deploy to Vercel
- [ ] Configure production API URL
- [ ] Set up custom domain (subdomain via Cloudflare)

---

### Phase 4: Production Deployment 🎯 CURRENT PHASE

**Goal:** Deploy existing local application to production

#### Step 1: Account Setup
- [ ] Create Railway account (railway.app)
- [ ] Create Vercel account (vercel.com)
- [ ] Choose subdomain for your existing domain

#### Step 2: Backend Deployment (Railway)
- [ ] Connect Railway to GitHub repo
- [ ] Create PostgreSQL database on Railway
- [ ] Configure environment variables (DATABASE_URL)
- [ ] Deploy FastAPI app (Railway auto-detects Python)
- [ ] Run data migration to production database
- [ ] Test API endpoints

#### Step 3: Frontend Deployment (Vercel)
- [ ] Connect Vercel to GitHub repo
- [ ] Set environment variable: `NEXT_PUBLIC_API_URL`
- [ ] Deploy Next.js application
- [ ] Test all pages

#### Step 4: Domain Setup (Cloudflare)
- [ ] Add CNAME record for frontend subdomain → Vercel
- [ ] Add CNAME record for API subdomain → Railway (or proxy through Cloudflare)
- [ ] Verify HTTPS works (automatic)
- [ ] Update CORS settings in API for production domain

#### Step 5: Launch
- [ ] Test end-to-end functionality
- [ ] Share with beta testers
- [ ] Monitor Railway/Vercel dashboards for errors

---

### Phase 5: Advanced Features (Future)

**Goal:** Add community features and automation (post-launch)

**Planned Features:**
- User accounts and authentication
- Favorite teams/players tracking
- Email notifications for new data
- Automated data sync from GitHub
- Admin dashboard for data management
- API webhooks for external integrations

**Estimated Timeline:** Weeks after launch, based on user feedback

---

## Technical Stack (Confirmed)

### Backend ✅ Implemented
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 15+
- **ORM:** SQLAlchemy
- **Validation:** Pydantic
- **Server:** Uvicorn

### Frontend ✅ Implemented
- **Framework:** Next.js 16 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS + CSS Variables
- **State Management:** React hooks + fetch
- **Charts:** Ready for Recharts integration

### Infrastructure 🔜 To Configure
- **Frontend Hosting:** Vercel (free tier)
- **Backend Hosting:** Railway Hobby ($5/month)
- **Database:** Railway PostgreSQL (included)
- **DNS/CDN/SSL:** Cloudflare (existing account)

### DevOps (Simplified)
- **CI/CD:** Automatic via Vercel + Railway GitHub integration
- **Secrets:** Hosting provider environment variables
- **Backups:** Railway automatic daily backups

### Future Additions (if needed)
- **Error Monitoring:** Sentry
- **Rate Limiting:** FastAPI middleware or Cloudflare rules
- **Caching:** Redis on Railway
- **Analytics:** Plausible or Cloudflare Analytics

---

## Data Privacy & Legal Considerations

### Privacy ✅ Resolved
- **Player Data:** Already public via GitHub repository
- **Consent:** Players have already consented
- **GDPR/Privacy:** Only need privacy policy if collecting NEW user data

### Legal
- **Attribution:** Clear independent branding
  - "MNP Stats - Unofficial analytics for Monday Night Pinball Seattle"
- **Terms of Service:** Basic open-source friendly terms
- **Data Source:** Link back to official MNP GitHub repository

---

## Security Considerations

### Already Handled
- ✅ HTTPS (automatic via Vercel + Railway)
- ✅ Input validation (Pydantic)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ DDoS protection (Cloudflare)
- ✅ Daily backups (Railway automatic)
- ✅ Environment variables for secrets

### To Configure
- [ ] CORS configuration (allow production domain)
- [ ] No secrets in code/git (verify before deploy)

### Future Additions (if needed)
- Rate limiting (Cloudflare rules or FastAPI middleware)
- Security headers (CSP, HSTS)

---

## Cost Analysis (Simplified)

### Monthly Costs
| Item | Cost |
|------|------|
| Domain | $0 (using existing) |
| Frontend (Vercel free tier) | $0 |
| Backend + Database (Railway Hobby) | $5 |
| DNS/CDN/SSL (Cloudflare) | $0 (existing account) |
| **Total** | **$5/month** |

### Annual Estimate
- **Year 1:** ~$60
- **Year 2+:** ~$60

### Scaling Costs (if needed later)
- Railway Pro: $20/month (more resources)
- Vercel Pro: $20/month (more bandwidth)
- Sentry: $0-26/month (error monitoring)
- Analytics: $0-9/month (Plausible)

---

## Branding & Naming

### Site Name
**Recommendation:** "MNP Stats"

### Domain Setup
Using subdomain on existing domain, e.g.:
- `mnp.yourdomain.com`
- `pinball.yourdomain.com`

### Attribution Statement
Include on every page:
> "MNP Stats is an independent analytics platform for Monday Night Pinball Seattle. This site is not officially affiliated with Monday Night Pinball. Data sourced from the [official MNP data repository](https://github.com/mondaynightpinball/mnp-data-archive)."

---

## Monitoring (Simplified)

### Initial Setup (Free)
- **Logs:** Railway dashboard (built-in)
- **Deployment status:** Vercel dashboard (built-in)
- **Basic analytics:** Cloudflare Analytics (free, already available)

### Future Additions (if needed)
- **Error Monitoring:** Sentry
- **Uptime Monitoring:** Better Uptime or UptimeRobot
- **Analytics:** Plausible Analytics

---

## Success Metrics

### Phase 4 (Production Deployment) Goals
- [ ] API accessible at production URL
- [ ] Frontend live at custom domain
- [ ] Response time <1s for 95% of requests
- [ ] 99% uptime in first week
- [ ] Zero critical errors

### Post-Launch Goals (30 days)
- [ ] 100+ unique visitors
- [ ] 1000+ API requests
- [ ] Positive feedback from MNP community
- [ ] <5 bug reports
- [ ] 99.5% uptime

### Long-term Goals (6 months)
- [ ] 500+ monthly active users
- [ ] Pin Stats iOS app integration
- [ ] Community contributions
- [ ] Sustainable hosting costs

---

## Immediate Next Steps

### Pre-Deployment ✅ Complete
1. ~~Get approval from MNP league organizers~~ (Data already public)
2. ~~Review player privacy considerations~~ (Players already consented)
3. ~~Build API~~ (Complete)
4. ~~Build Frontend~~ (Complete)
5. ~~Domain~~ (Using existing domain)
6. ~~Hosting provider~~ (Railway + Vercel)

### Deployment Tasks
1. **Create Railway account** and connect GitHub repo
2. **Create Vercel account** and connect GitHub repo
3. **Deploy backend + PostgreSQL** on Railway
4. **Migrate data** to production database
5. **Deploy frontend** on Vercel
6. **Configure Cloudflare DNS** for subdomains
7. **Test end-to-end**
8. **Soft launch to beta testers**

---

## Open Questions

### Resolved ✅
1. ~~League Approval~~ - Data is already public
2. ~~Player Consent~~ - Players have already consented
3. ~~Branding~~ - Independent project with references to MNP
4. ~~Frontend Framework~~ - Next.js selected and implemented
5. ~~Backend Framework~~ - FastAPI selected and implemented
6. ~~Domain Name~~ - Using existing domain (subdomain)
7. ~~Hosting Provider~~ - Railway for backend, Vercel for frontend

### Outstanding 🔜
1. **Subdomain choice:** What subdomain to use? (e.g., `mnp`, `pinball`, `stats`)
2. **Data Freshness:** How quickly should new match data appear?
3. **Admin Access:** Who has admin rights to update data?

---

## Appendix A: Hosting Provider Comparison

| Provider | Pros | Cons | Cost |
|----------|------|------|------|
| **Railway** ✅ Selected | Great DX, PostgreSQL included, GitHub deploy | Newer platform | $5/month (Hobby) |
| **Render** | Free tier available | Cold starts on free tier | $7-25/month |
| **Fly.io** | Global edge, free tier | Steeper learning curve | $0-30/month |
| **Vercel** ✅ Selected | Excellent for Next.js, free tier | Backend via serverless only | $0 (free tier) |

**Decision:** Railway for backend + Vercel for frontend = **$5/month total**

---

## Appendix B: Current API Endpoints

### Teams
- `GET /api/teams` - List all teams
- `GET /api/teams/{team_key}` - Team details
- `GET /api/teams/{team_key}/players` - Team roster
- `GET /api/teams/{team_key}/machine-stats` - Team machine statistics

### Players
- `GET /api/players` - List all players
- `GET /api/players/{player_key}` - Player details
- `GET /api/players/{player_key}/machine-stats` - Player machine statistics
- `GET /api/players/{player_key}/machine-scores` - Player score history

### Machines
- `GET /api/machines` - List all machines
- `GET /api/machines/{machine_key}` - Machine details
- `GET /api/machines/{machine_key}/percentiles` - Score percentiles
- `GET /api/machines/{machine_key}/scores` - All scores
- `GET /api/machines/{machine_key}/venues` - Venues with this machine
- `GET /api/machines/{machine_key}/teams` - Teams that played this machine

### Venues
- `GET /api/venues` - List all venues
- `GET /api/venues/{venue_key}` - Venue details
- `GET /api/venues/{venue_key}/machines` - Machines at venue

### Matchups
- `GET /api/matchups/analysis` - Team matchup analysis

### System
- `GET /api/` - API info
- `GET /api/health` - Health check
- `GET /api/seasons` - Available seasons

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-26 | JJC | Initial deployment plan created |
| 1.1 | 2025-11-26 | JJC | Updated based on clarifications |
| 2.0 | 2025-11-29 | JJC | Major update reflecting completed local development. Frontend and API fully built. Updated to Phase 4 (Production Deployment). |
| 3.0 | 2025-12-07 | JJC | Simplified deployment plan. Removed Docker, Sentry, rate limiting, caching. Using existing domain + Cloudflare. Cost reduced to $5/month. |

---

**Next Review Date:** After production deployment
**Document Owner:** JJC
**Status:** Ready for Production Deployment
