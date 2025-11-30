# Monday Night Pinball - Public Deployment Plan

**Document Version**: 2.0
**Created**: 2025-11-26
**Last Updated**: 2025-11-29
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
- 🔜 Domain name to be chosen
- 🔜 Hosting platform selection for production

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

## Revised Deployment Architecture

### Recommended: Option D - Platform-as-a-Service

Given the existing codebase and need for rapid deployment:

**Components:**
- **Frontend**: Vercel (free tier sufficient)
- **Backend**: Railway or Render ($5-25/month)
- **Database**: Managed PostgreSQL from hosting provider ($10-25/month)
- **CDN**: Cloudflare (free tier)

**Total Estimated Cost:** $15-50/month

**Why This Approach:**
- Fastest time to deployment with existing code
- Minimal DevOps required
- Built-in CI/CD from GitHub
- Auto-scaling capabilities
- Good developer experience

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
- [ ] Create Dockerfile for API
- [ ] Deploy to Railway/Render
- [ ] Set up production PostgreSQL
- [ ] Configure environment variables
- [ ] Enable CORS for production domain
- [ ] Add rate limiting
- [ ] Set up Sentry monitoring

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
- [ ] Set up custom domain
- [ ] Add SEO meta tags
- [ ] Create sitemap.xml
- [ ] Add analytics (Plausible)

---

### Phase 4: Production Deployment 🎯 CURRENT PHASE

**Goal:** Deploy existing local application to production

**Timeline:** 1-2 weeks

#### Step 1: Pre-Deployment Setup (Day 1-2)
- [ ] Choose and register domain name
- [ ] Create accounts on hosting platforms
- [ ] Set up Cloudflare for DNS
- [ ] Create Sentry account for monitoring

#### Step 2: Backend Deployment (Day 3-5)
- [ ] Create `Dockerfile` for FastAPI app
- [ ] Create `docker-compose.yml` for local testing
- [ ] Deploy to Railway/Render
- [ ] Create production PostgreSQL database
- [ ] Run data migration to production
- [ ] Configure environment variables
- [ ] Test all API endpoints in production
- [ ] Set up rate limiting

#### Step 3: Frontend Deployment (Day 6-8)
- [ ] Configure Vercel project
- [ ] Set production environment variables
- [ ] Deploy Next.js application
- [ ] Configure custom domain
- [ ] Test all pages in production
- [ ] Verify API integration

#### Step 4: Production Hardening (Day 9-10)
- [ ] Configure HTTPS (automatic with Vercel/Railway)
- [ ] Set up Sentry error monitoring
- [ ] Configure uptime monitoring (Better Uptime)
- [ ] Add security headers
- [ ] Test CORS configuration
- [ ] Load test API endpoints

#### Step 5: Launch (Day 11-14)
- [ ] Soft launch to beta testers
- [ ] Monitor for errors
- [ ] Gather feedback
- [ ] Fix any critical issues
- [ ] Public announcement

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
- **Frontend Hosting:** Vercel
- **Backend Hosting:** Railway or Render
- **Database:** Managed PostgreSQL
- **CDN:** Cloudflare (free tier)
- **DNS:** Cloudflare
- **Monitoring:** Sentry
- **Analytics:** Plausible Analytics

### DevOps 🔜 To Configure
- **CI/CD:** GitHub Actions
- **Containers:** Docker
- **Secrets:** GitHub Secrets + hosting provider vault
- **Backups:** Automated daily database backups

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

### API Security (To Implement)
- [ ] Rate limiting (100-1000 requests/hour per IP)
- [ ] HTTPS only (automatic with hosting platforms)
- [ ] CORS configuration (allow production domain)
- [ ] Input validation (already implemented via Pydantic)
- [ ] SQL injection prevention (using SQLAlchemy ORM)

### Database Security (To Implement)
- [ ] Read-only database user for public API
- [ ] Regular backups (daily automated)
- [ ] Encrypted connections
- [ ] No direct database access from internet

### Infrastructure Security (To Implement)
- [ ] Environment variables for secrets
- [ ] No secrets in code/git
- [ ] Security headers (CSP, HSTS)
- [ ] DDoS protection (Cloudflare)

---

## Cost Analysis (Updated)

### Production Deployment - Month 1
| Item | Cost |
|------|------|
| Domain registration | $15/year (~$1.25/mo) |
| Frontend (Vercel free tier) | $0 |
| Backend (Railway Hobby) | $5-20/month |
| Database (Railway PostgreSQL) | $5-15/month |
| Monitoring (Sentry free tier) | $0 |
| CDN (Cloudflare free tier) | $0 |
| **Total** | **$10-35/month** |

### Steady State - Ongoing
| Item | Cost |
|------|------|
| Domain renewal | $15/year |
| Hosting (Backend + DB) | $15-35/month |
| Monitoring upgrades (if needed) | $0-20/month |
| **Total** | **$15-55/month** |

### Annual Estimate
- **Year 1:** $200-500 (includes setup)
- **Year 2+:** $200-700 (steady state)

---

## Branding & Naming

### Site Name
**Recommendation:** "MNP Stats"
- Short, memorable
- Clearly affiliated but independent
- Searchable

### Domain Options (Check Availability)
1. `mnpstats.com` - First choice
2. `mnpdata.io` - Tech-focused alternative
3. `mondaynightpinball.app` - Descriptive

### Attribution Statement
Include on every page:
> "MNP Stats is an independent analytics platform for Monday Night Pinball Seattle. This site is not officially affiliated with Monday Night Pinball. Data sourced from the [official MNP data repository](https://github.com/mondaynightpinball/mnp-data-archive)."

---

## Monitoring & Observability

### Metrics to Track
- API request volume and latency
- Error rates (4xx, 5xx)
- Database query performance
- Page load times
- User geography (basic analytics)

### Tools
- **Application Monitoring:** Sentry
- **Uptime Monitoring:** Better Uptime or UptimeRobot
- **Analytics:** Plausible Analytics
- **Logs:** Hosting provider dashboards

### Alerts
- API downtime (>5 minutes)
- Error rate spike (>5% of requests)
- Database connection issues

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

### Pre-Deployment ✅ Simplified
1. ~~Get approval from MNP league organizers~~ (Data already public)
2. ~~Review player privacy considerations~~ (Players already consented)
3. ~~Build API~~ (Complete)
4. ~~Build Frontend~~ (Complete)
5. **Choose domain name and register it** 🔜
6. **Decide on hosting provider** 🔜

### Deployment Tasks
1. **Create Docker configuration** for API
2. **Set up Railway/Render project**
3. **Deploy backend and database**
4. **Configure Vercel for frontend**
5. **Set up monitoring and alerts**
6. **Test in production**
7. **Soft launch to beta testers**

---

## Open Questions

### Resolved ✅
1. ~~League Approval~~ - Data is already public
2. ~~Player Consent~~ - Players have already consented
3. ~~Branding~~ - Independent project with references to MNP
4. ~~Frontend Framework~~ - Next.js selected and implemented
5. ~~Backend Framework~~ - FastAPI selected and implemented

### Outstanding 🔜
1. **Domain Name:** What domain should we use?
2. **Hosting Provider:** Railway vs Render for backend?
3. **Data Freshness:** How quickly should new match data appear?
4. **Admin Access:** Who has admin rights to update data?

---

## Appendix A: Hosting Provider Comparison

| Provider | Pros | Cons | Cost (Starter) |
|----------|------|------|----------------|
| **Railway** | Great DX, simple deployment, PostgreSQL included | Newer platform | $5-20/month |
| **Render** | Free tier, good docs | Can be slow on free tier | $7-25/month |
| **Fly.io** | Global edge deployment | Steeper learning curve | $0-30/month |
| **Vercel** | Excellent for Next.js | Backend via serverless only | $0-20/month |

**Recommendation:** Railway for backend + Vercel for frontend

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

---

**Next Review Date:** After production deployment
**Document Owner:** JJC
**Status:** Ready for Production Deployment
