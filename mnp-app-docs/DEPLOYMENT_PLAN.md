# Monday Night Pinball - Public Deployment Plan

**Document Version**: 1.1
**Created**: 2025-11-26
**Last Updated**: 2025-11-26
**Status**: Ready for Implementation

---

## Executive Summary

This document outlines the strategy for deploying the Monday Night Pinball (MNP) data platform with a public web API and interface. The MNP data is already public (GitHub repository), players have consented, and this will be an independent platform with branding that references Monday Night Pinball.

**Key Decisions Made:**
- ✅ Data is already public and accessible
- ✅ Players have consented to public data sharing
- ✅ Independent branding (references MNP, not official)
- 🔜 Domain name to be chosen
- 🔜 Hosting platform selection

---

## Current State Assessment

### Existing Components

1. **Data Archive** (`mnp-data-archive/`)
   - Season 21 & 22 match data (JSON)
   - Machine definitions, venue data, IPR ratings
   - Git submodule structure

2. **Backend API** (`api/`)
   - FastAPI application
   - Database models and schemas
   - PostgreSQL database

3. **Report Generators** (`reports/`)
   - Python scripts for analytics
   - Config-driven report generation
   - Chart/visualization output

4. **Related Projects**
   - Pin Stats iOS app (consumer of this data)

### Current Limitations

- Local development environment only
- No public API access
- Manual report generation
- Database runs locally
- No authentication/authorization
- No frontend web interface (iOS app exists)

---

## Deployment Architecture Options

### Option A: Simple Static Hosting (Minimal Cost)

**Components:**
- Static JSON files hosted on CDN (Cloudflare, Netlify, Vercel)
- Pre-generated reports as markdown/HTML
- No backend API initially

**Pros:**
- Extremely low/zero cost
- Simple to maintain
- Fast global delivery via CDN
- No server management

**Cons:**
- No dynamic queries
- Must pre-generate all reports
- Limited interactivity
- No real-time updates

**Cost Estimate:** $0-10/month

---

### Option B: Serverless API (Moderate Cost)

**Components:**
- AWS Lambda / Google Cloud Functions for API
- S3/Cloud Storage for data files
- API Gateway for routing
- CloudFront/CDN for static assets
- PostgreSQL (AWS RDS / Cloud SQL)

**Pros:**
- Pay-per-use pricing
- Auto-scaling
- No server management
- Dynamic queries supported

**Cons:**
- Cold start latency
- More complex deployment
- Vendor lock-in considerations
- Database costs always-on

**Cost Estimate:** $20-100/month (depends on usage)

---

### Option C: Container-Based Hosting (Predictable Cost)

**Components:**
- Docker containers (API + Frontend)
- Managed Kubernetes (GKE, EKS) or simpler (Railway, Render, Fly.io)
- Managed PostgreSQL database
- CDN for static assets
- Redis for caching (optional)

**Pros:**
- Consistent performance
- Full control over environment
- Easy local development parity
- Predictable pricing

**Cons:**
- Higher base cost
- Requires container expertise
- Must manage scaling

**Cost Estimate:** $25-150/month

---

### Option D: Platform-as-a-Service (Easiest)

**Components:**
- Heroku, Railway, Render, or Fly.io
- Managed PostgreSQL addon
- Built-in deployment pipelines
- Integrated monitoring

**Pros:**
- Fastest time to deployment
- Minimal DevOps required
- Good developer experience
- Easy CI/CD setup

**Cons:**
- Higher cost per resource
- Less flexibility
- Potential vendor lock-in
- Limited customization

**Cost Estimate:** $25-100/month

---

## Recommended Approach: Phased Deployment

### Phase 1: Static Data API (Weeks 1-2) ⚡ Fast Track

**Goal:** Make data publicly accessible with minimal infrastructure

**Why Start Here:**
Since data is already public and formatted, we can skip straight to hosting static exports while developing the dynamic API in parallel.

**Implementation:**
1. Export database to static JSON API files (one-time script)
2. Host on Vercel/Netlify/Cloudflare Pages (zero config)
3. Set up GitHub Actions to auto-update on data changes
4. Create simple API documentation (markdown + GitHub Pages)
5. Add CORS headers for web access

**Deliverables:**
- `/api/v1/seasons.json` - List of all seasons
- `/api/v1/seasons/{season}/matches.json` - All matches for a season
- `/api/v1/machines.json` - Machine definitions
- `/api/v1/venues.json` - Venue information
- `/api/v1/teams.json` - Team roster
- `/api/v1/players.json` - Player statistics
- Basic API documentation site

**Timeline:** 1-2 weeks (can be done in parallel with Phase 2)
**Cost:** $0-10/month
**Effort:** Low (mostly automation)

---

### Phase 2: Dynamic API Backend (Weeks 2-6) 🎯 MVP

**Goal:** Enable dynamic queries and real-time data access

**Why This Matters:**
The existing FastAPI application already works locally. This phase is about deploying it publicly with production best practices.

**Implementation:**
1. **Dockerize existing FastAPI application** (if not already)
2. **Deploy to Railway/Render/Fly.io** (choose one)
3. **Set up managed PostgreSQL database** (same provider)
4. **Database migration script** (load data from GitHub repo)
5. **Add CORS middleware** for web/mobile app access
6. **Implement rate limiting** (per-IP throttling)
7. **Set up Redis caching** for expensive queries (percentiles)
8. **Configure monitoring** (Sentry for errors, uptime checks)

**Deliverables:**
- `GET /api/v1/matches?season=22&team=SKP&venue=T4B`
- `GET /api/v1/scores?machine=MM&venue=T4B&ipr_min=3`
- `GET /api/v1/percentiles?machine=MM&season=22`
- `GET /api/v1/teams/{team_key}/stats`
- `GET /api/v1/players/{player_name}/history`
- OpenAPI/Swagger documentation at `/docs`
- Health check endpoint `/health`

**Timeline:** 3-4 weeks
**Cost:** $25-75/month (Railway: ~$20, PostgreSQL: ~$10, Redis: ~$10)
**Effort:** Medium (deployment setup + optimization)

---

### Phase 3: Web Frontend (Weeks 6-12) 🌐 Public Launch

**Goal:** Provide user-friendly web interface for casual users

**Why This Matters:**
While Pin Stats iOS app serves mobile users, a web interface makes data accessible to everyone without requiring an app download.

**Implementation:**
1. **Choose framework:** Next.js (React) or SvelteKit
2. **Build core pages:**
   - Homepage with season overview
   - Team standings and records
   - Individual team pages with match history
   - Player profile pages with statistics
   - Machine performance dashboards
   - Venue pages with machine lists
3. **Interactive visualizations:** Chart.js or Recharts
4. **Search/filter functionality:** By team, player, machine, venue
5. **Responsive design:** Mobile-first approach
6. **Deploy to Vercel/Netlify:** Free tier likely sufficient

**Deliverables:**
- Public website at chosen domain (e.g., `mnpstats.com`)
- Team standings and rankings page
- Machine performance explorer with charts
- Player statistics and history page
- Match history browser with filters
- About page with data attribution

**Timeline:** 4-6 weeks
**Cost:** +$0-15/month (Vercel/Netlify free tier, custom domain ~$15/year)
**Effort:** High (significant frontend development)

---

### Phase 4: Advanced Features (Months 6+)

**Goal:** Add community features and automation

**Implementation:**
1. User accounts and authentication
2. Favorite teams/players tracking
3. Email notifications for new data
4. Automated weekly report generation
5. Admin dashboard for data management
6. API webhooks for external integrations

**Deliverables:**
- User authentication system
- Notification system
- Admin tools
- Webhook endpoints for Pin Stats app
- API rate limiting tiers

**Cost:** Variable based on features

---

## Technical Stack Recommendations

### Backend
- **Framework:** FastAPI (already using)
- **Database:** PostgreSQL (already using)
- **ORM:** SQLAlchemy (already using)
- **Caching:** Redis (for expensive queries)
- **Task Queue:** Celery (for report generation)

### Frontend (if built)
- **Framework:** Next.js (React) or SvelteKit
- **Charts:** Chart.js or Recharts
- **Styling:** Tailwind CSS
- **State Management:** React Query or SWR

### Infrastructure
- **Hosting:** Railway, Render, or Fly.io (Phase 1)
- **Database:** Managed PostgreSQL from hosting provider
- **CDN:** Cloudflare (free tier)
- **DNS:** Cloudflare
- **Monitoring:** Sentry (errors), Better Uptime (availability)
- **Analytics:** Plausible or Simple Analytics (privacy-focused)

### DevOps
- **CI/CD:** GitHub Actions
- **Containers:** Docker
- **Secrets:** GitHub Secrets or hosting provider vault
- **Backups:** Automated daily database backups

---

## Data Privacy & Legal Considerations

### Privacy ✅ Resolved
- **Player Data:** Already public via GitHub repository
  - Public: Team names, match scores, aggregate statistics, player names
  - Private: Contact info remains private (not in dataset)
- **Consent:** Players have already consented to public data sharing
- **GDPR/Privacy:** Only need privacy policy if collecting NEW user data (analytics, accounts)

### Legal
- **Terms of Service:** Required for public API (standard open-source friendly terms)
- **Rate Limiting:** Prevent abuse and ensure fair access
- **Attribution:** Clear independent branding that references "Monday Night Pinball"
  - Example: "MNP Stats - Unofficial analytics for Monday Night Pinball Seattle"
- **Copyright:** Data is already public; clarify API usage rights
- **Data License:** Inherit from existing GitHub repository license or specify MIT/Creative Commons

### Content
- **API Documentation:** Clear usage guidelines and examples
- **Data Source Attribution:** Link back to official MNP GitHub repository
- **Acceptable Use Policy:** Encourage community use, prohibit abuse/scraping

---

## Security Considerations

### API Security
- Rate limiting (100-1000 requests/hour per IP)
- API key authentication for higher rate limits
- HTTPS only (enforce TLS)
- CORS configuration (allow specific domains)
- Input validation and sanitization
- SQL injection prevention (using ORM)

### Database Security
- Read-only database user for public API
- Regular backups (daily automated)
- Encrypted connections
- No direct database access from internet
- Separate admin database user

### Infrastructure Security
- Environment variables for secrets
- No secrets in code/git
- Regular dependency updates
- Security headers (CSP, HSTS, etc.)
- DDoS protection (Cloudflare)

---

## Performance Optimization

### Caching Strategy
- Redis cache for expensive queries (percentiles, aggregates)
- CDN caching for static assets
- Browser caching headers
- Cache invalidation on data updates

### Database Optimization
- Indexes on frequently queried columns
- Connection pooling
- Query optimization
- Read replicas if needed

### API Performance
- Pagination for large result sets
- Field selection (return only requested fields)
- Compression (gzip/brotli)
- Async operations where possible

---

## Monitoring & Observability

### Metrics to Track
- API request volume and latency
- Error rates (4xx, 5xx)
- Database query performance
- Cache hit rates
- User geography (basic analytics)

### Tools
- **Application Monitoring:** Sentry (errors and performance)
- **Uptime Monitoring:** Better Uptime or UptimeRobot
- **Analytics:** Plausible Analytics (privacy-friendly)
- **Logs:** Hosting provider logs + structured logging

### Alerts
- API downtime (>5 minutes)
- Error rate spike (>5% of requests)
- Database connection issues
- Disk space warnings
- Unusual traffic patterns

---

## Cost Analysis

### Phase 1 (Static API) - Months 1-2
- Hosting: $0 (Cloudflare Pages/Netlify free tier)
- Domain: $10-15/year
- **Monthly: ~$1-2**

### Phase 2 (Dynamic API) - Months 2-4
- Hosting: $15-25/month (Railway/Render starter)
- Database: $10-25/month (managed PostgreSQL)
- Monitoring: $0-10/month (Sentry free tier, Better Uptime)
- **Monthly: ~$25-60**

### Phase 3 (Web Frontend) - Months 4-6
- Same infrastructure as Phase 2
- CDN: $0 (Cloudflare free tier)
- **Monthly: ~$25-60** (no additional cost)

### Phase 4 (Advanced Features)
- Scaling: $50-150/month (larger database, more compute)
- Redis: $10-25/month
- Email service: $0-20/month (SendGrid/Mailgun)
- **Monthly: ~$60-195**

### Annual Cost Estimate
- Year 1: $300-800 (ramping up)
- Year 2+: $600-1200 (steady state)

---

## Data Update Strategy

### Automated Updates
- GitHub Actions to sync data from MNP source
- Daily/weekly automated imports
- Validation checks before publishing
- Rollback capability

### Manual Updates
- Admin interface for corrections
- Data validation tools
- Change logs and audit trails

### Version Control
- Keep historical data immutable
- API versioning for breaking changes
- Deprecation notices (6+ months)

---

## API Design Principles

### RESTful Endpoints
```
GET /api/v1/seasons
GET /api/v1/seasons/{season}/matches
GET /api/v1/seasons/{season}/teams
GET /api/v1/teams/{team_key}
GET /api/v1/teams/{team_key}/matches
GET /api/v1/venues/{venue_key}
GET /api/v1/machines/{machine_key}
GET /api/v1/players/{player_name}
GET /api/v1/scores?machine={key}&season={n}&venue={key}
GET /api/v1/percentiles?machine={key}&ipr_min={n}&ipr_max={n}
```

### Query Parameters
- Filtering: `?season=22&team=SKP`
- Pagination: `?page=1&limit=50`
- Sorting: `?sort=date&order=desc`
- Field selection: `?fields=score,player,date`

### Response Format
```json
{
  "data": [...],
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 523,
    "season": "22"
  },
  "links": {
    "self": "...",
    "next": "...",
    "prev": "..."
  }
}
```

---

## Branding & Naming Recommendations

Since this is an **independent platform that references Monday Night Pinball**, here are recommendations:

### Site Name Options
1. **MNP Stats** - Clear, simple, searchable
2. **Monday Night Pinball Analytics** - Descriptive, professional
3. **Pinball League Stats** - Generic, could expand beyond MNP
4. **MNP Data Hub** - Technical, data-focused
5. **Flipper Stats** - Fun, pinball-themed

**Recommendation:** "MNP Stats" - short, memorable, clearly affiliated but independent

### Domain Options
| Domain | Pros | Cons | Likely Available? |
|--------|------|------|-------------------|
| `mnpstats.com` | Perfect match, .com TLD | May be taken | Check |
| `mnpdata.io` | Tech-focused, trendy | .io premium pricing | Likely |
| `mondaynightpinball.app` | Descriptive, .app TLD | Long, might seem official | Likely |
| `seattlepinballstats.com` | Local SEO, expandable | Seattle-specific | Likely |
| `mnpleague.com` | Short, league focus | Might seem official | Check |

**Recommendation:** Check availability in order: `mnpstats.com` → `mnpdata.io` → `mondaynightpinball.app`

### Attribution Statement
Include on every page:

> "MNP Stats is an independent analytics platform for Monday Night Pinball Seattle. This site is not officially affiliated with Monday Night Pinball. Data sourced from the [official MNP data repository](https://github.com/mondaynightpinball/mnp-data-archive)."

### Visual Identity
- **Color Scheme:** Use pinball-inspired colors (neon accents, dark background)
- **Typography:** Bold, readable, retro-futuristic
- **Logo:** Consider pinball flipper, bumper, or ball imagery
- **Tagline Options:**
  - "Analytics for Seattle's Monday Night Pinball League"
  - "Stats, Charts, and Insights for MNP"
  - "Track the Flipper Action"

---

## Documentation Requirements

### API Documentation
- OpenAPI/Swagger spec (auto-generated from FastAPI)
- Interactive API explorer
- Code examples (Python, JavaScript, curl)
- Rate limit documentation
- Authentication guide

### User Documentation
- Getting started guide
- Data structure reference
- Analysis examples
- FAQ
- Changelog

### Developer Documentation
- Setup instructions
- Database schema
- Deployment guide
- Contributing guidelines

---

## Success Metrics

### Phase 1 Goals
- API endpoints live and documented
- <500ms average response time
- 99% uptime
- 100+ API requests/day

### Phase 2 Goals
- Dynamic queries working
- <1s average response time for complex queries
- 99.5% uptime
- 1000+ API requests/day

### Phase 3 Goals
- Web frontend live
- 500+ monthly active users
- <2s page load time
- Positive user feedback

### Long-term Goals
- 5000+ monthly active users
- Pin Stats app integration
- Community contributions
- Sustainable hosting costs

---

## Risk Mitigation

### Technical Risks
- **Database costs exceed budget:** Use caching aggressively, consider read replicas
- **API abuse:** Implement rate limiting and monitoring from day one
- **Performance issues:** Load testing before launch, gradual rollout
- **Data corruption:** Automated backups, validation checks, version control

### Business Risks
- **Hosting costs unsustainable:** Start with cheapest option, add features incrementally
- **Low adoption:** Focus on Pin Stats app integration, community outreach
- **Data privacy concerns:** Clear policies, get league approval upfront
- **Maintenance burden:** Automate everything possible, keep architecture simple

---

## Timeline Summary (Updated)

| Phase | Duration | Key Deliverable | Cost/Month | Status |
|-------|----------|-----------------|------------|--------|
| Phase 1 | Weeks 1-2 | Static API live | $0-2 | 🔜 Ready to start |
| Phase 2 | Weeks 2-6 | Dynamic API backend | $25-60 | 🎯 **MVP** |
| Phase 3 | Weeks 6-12 | Web frontend | $25-60 | 🌐 Public launch |
| Phase 4 | Weeks 12+ | Advanced features | $60-195 | 🚀 Future growth |

**Accelerated Timeline Benefits:**
- Existing FastAPI app = foundation already built
- Data already structured and validated
- No legal/privacy blockers to resolve
- Can work on phases in parallel

**Minimum Viable Product:** Phase 2 (Week 6) - API deployed for Pin Stats app
**Full Public Launch:** Phase 3 (Week 12) - Web interface live
**Full Featured Product:** Phase 4 (Week 12+) - Community features

---

## Immediate Next Steps

### Pre-Development ✅ Simplified
1. ~~Get approval from MNP league organizers~~ (Data already public)
2. ~~Review player privacy considerations~~ (Players already consented)
3. **Choose domain name and register it** 🔜
4. **Decide on hosting provider** 🔜
5. **Create branding assets** (logo, color scheme, site name)

### Development
1. **Review and document existing FastAPI endpoints**
2. **Create OpenAPI/Swagger documentation** (FastAPI auto-generates)
3. **Set up Docker configuration** for containerized deployment
4. **Create GitHub Actions CI/CD pipeline**
5. **Write deployment scripts** for chosen platform
6. **Add CORS configuration** for web access

### Launch Preparation
1. **Set up monitoring and alerting** (Sentry, uptime monitoring)
2. **Create public API documentation site**
3. **Load test the API** (simulate expected traffic)
4. **Set up rate limiting** (protect against abuse)
5. **Soft launch** to Pin Stats iOS app first
6. **Public launch** with announcement to MNP community

---

## Open Questions

### Resolved ✅
1. ~~**League Approval:**~~ Data is already public on GitHub
2. ~~**Player Consent:**~~ Players have already consented
3. ~~**Branding:**~~ Independent project with references to MNP

### Outstanding 🔜
1. **Domain Name:** What domain should we use?
   - Options: `mnpstats.com`, `mnpdata.io`, `pinstats.live`, `mondaynightpinball.app`, etc.
   - Consider: SEO, memorability, availability, cost
2. **Monetization:** Free forever, or eventually premium features?
   - Recommendation: Start free, consider premium tiers only if costs scale significantly
3. **Data Freshness:** How quickly should new match data appear?
   - Options: Real-time, daily sync, weekly sync
   - Depends on: How data enters GitHub repository
4. **Admin Access:** Who has admin rights to update/correct data?
   - You (JJC) initially
   - Consider: MNP league coordinators, trusted community members
5. **Community Features:** User comments, forums, etc.?
   - Recommendation: Phase 4+ feature, start with read-only API/site
6. **Hosting Provider:** Railway, Render, Fly.io, or other?
   - Consider: Cost, ease of deployment, PostgreSQL support, monitoring
7. **Frontend Framework:** Next.js, SvelteKit, or static site?
   - Depends on: Interactivity needs, development time, hosting costs

---

## Appendix A: Hosting Provider Comparison

| Provider | Pros | Cons | Cost (Starter) |
|----------|------|------|----------------|
| Railway | Great DX, simple deployment | Newer platform | $5-20/month |
| Render | Free tier, good docs | Can be slow | $7-25/month |
| Fly.io | Global edge deployment | Steeper learning curve | $0-30/month |
| Heroku | Mature, reliable | More expensive | $7-25/month |
| Vercel | Excellent for frontend | Backend limitations | $0-20/month |
| Netlify | Great static hosting | Backend via functions only | $0-19/month |

---

## Appendix B: Database Sizing

### Current Data Volume (Season 21-22)
- ~200 matches per season
- ~800 games (4 per match)
- ~50 machines
- ~10 venues
- ~100+ players

### Projected Growth
- 1 new season per year (~200 matches)
- Database size: <100MB for all data
- Query volume: 1000-10000 requests/day

### Database Requirements
- PostgreSQL 14+
- 1GB RAM minimum
- 10GB storage minimum
- Automated daily backups

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-26 | JJC | Initial deployment plan created |
| 1.1 | 2025-11-26 | JJC | Updated based on clarifications: data already public, players consented, independent branding confirmed. Accelerated timeline from months to weeks. Added branding recommendations. |

---

**Next Review Date:** After Phase 2 completion (API deployed)
**Document Owner:** JJC
**Status:** Ready for Implementation - Phase 1 can begin immediately
