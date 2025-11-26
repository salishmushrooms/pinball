# MNP Deployment Checklist

**Quick Reference Guide for Deployment Tasks**

Use this checklist to track progress through the deployment phases outlined in [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md).

---

## Pre-Deployment Setup

### Domain & Branding
- [ ] Choose final domain name
  - Options: `mnpstats.com`, `mnpdata.io`, `mondaynightpinball.app`
  - Check availability at Namecheap, Google Domains, or Cloudflare
- [ ] Register domain ($10-15/year)
- [ ] Point DNS to Cloudflare (free tier)
- [ ] Create logo/favicon
- [ ] Define color scheme and basic design system
- [ ] Write attribution statement

### Hosting Platform Selection
- [ ] Compare hosting providers (Railway, Render, Fly.io)
- [ ] Create account on chosen platform
- [ ] Set up payment method
- [ ] Review pricing and resource limits

---

## Phase 1: Static API (Weeks 1-2)

**Goal:** Simple static JSON API hosted on CDN

### Export Scripts
- [ ] Create `scripts/export_static_api.py` to export database to JSON
- [ ] Export `/api/v1/seasons.json`
- [ ] Export `/api/v1/seasons/{season}/matches.json` for each season
- [ ] Export `/api/v1/machines.json`
- [ ] Export `/api/v1/venues.json`
- [ ] Export `/api/v1/teams.json`
- [ ] Export `/api/v1/players.json`

### Hosting Setup
- [ ] Create Vercel/Netlify/Cloudflare Pages project
- [ ] Configure custom domain
- [ ] Set up CORS headers in `_headers` file
- [ ] Enable HTTPS (automatic with most platforms)
- [ ] Test API endpoints

### Automation
- [ ] Create GitHub Action to auto-export on data changes
- [ ] Set up weekly scheduled export (cron)
- [ ] Test automated deployment pipeline

### Documentation
- [ ] Create basic API documentation (markdown)
- [ ] Add usage examples (curl, Python, JavaScript)
- [ ] Document rate limits (if any)
- [ ] Add attribution and links to MNP data source

**Phase 1 Complete:** Static API is live and accessible ✅

---

## Phase 2: Dynamic API Backend (Weeks 2-6)

**Goal:** Deploy FastAPI application with PostgreSQL database

### Local Testing
- [ ] Review existing FastAPI code in `/api`
- [ ] Ensure all endpoints work locally
- [ ] Test database migrations
- [ ] Verify data loading from GitHub repo
- [ ] Run tests (if they exist)

### Docker Configuration
- [ ] Create `Dockerfile` for FastAPI app
- [ ] Create `docker-compose.yml` for local testing
- [ ] Test Docker build locally
- [ ] Optimize image size (multi-stage build)

### Database Setup
- [ ] Choose PostgreSQL provider (Railway, Render, Supabase)
- [ ] Create production database
- [ ] Run schema migrations
- [ ] Load initial data from GitHub repository
- [ ] Set up connection pooling
- [ ] Configure backup schedule (daily)

### API Deployment
- [ ] Create project on chosen platform (Railway/Render/Fly.io)
- [ ] Configure environment variables (DATABASE_URL, etc.)
- [ ] Deploy FastAPI application
- [ ] Connect to managed PostgreSQL
- [ ] Test all API endpoints in production
- [ ] Verify database queries work correctly

### Performance & Caching
- [ ] Set up Redis instance (optional, for caching)
- [ ] Implement caching for expensive queries (percentiles)
- [ ] Add database indexes for common queries
- [ ] Configure connection pooling (pgbouncer or built-in)
- [ ] Test response times (<1s for most queries)

### Security & Rate Limiting
- [ ] Add CORS middleware configuration
- [ ] Implement rate limiting (100-1000 requests/hour per IP)
- [ ] Create read-only database user for API
- [ ] Configure HTTPS (should be automatic)
- [ ] Add security headers (HSTS, CSP, etc.)
- [ ] Set up environment variables properly (no secrets in code)

### Monitoring & Logging
- [ ] Set up Sentry account for error tracking
- [ ] Configure Sentry in FastAPI app
- [ ] Set up uptime monitoring (Better Uptime, UptimeRobot)
- [ ] Configure alerts (email/Slack for downtime)
- [ ] Set up structured logging (JSON format)
- [ ] Review logs in hosting platform dashboard

### API Documentation
- [ ] Verify OpenAPI/Swagger docs at `/docs`
- [ ] Add description and examples to endpoints
- [ ] Document query parameters and filters
- [ ] Add authentication docs (if applicable)
- [ ] Create getting-started guide
- [ ] Add code examples for common queries

### Testing & Validation
- [ ] Load test API with realistic traffic (Apache Bench, k6)
- [ ] Verify all query parameters work
- [ ] Test error handling (404s, 500s, etc.)
- [ ] Check CORS from different origins
- [ ] Validate response formats
- [ ] Test rate limiting behavior

### Data Update Strategy
- [ ] Create script to sync data from GitHub repo
- [ ] Set up GitHub Action or cron job for automated sync
- [ ] Test data update process
- [ ] Document manual update procedure (if needed)

**Phase 2 Complete:** Dynamic API is live and serving Pin Stats app ✅

---

## Phase 3: Web Frontend (Weeks 6-12)

**Goal:** Public website for browsing MNP data

### Framework Setup
- [ ] Choose framework (Next.js recommended)
- [ ] Create new project
- [ ] Set up Tailwind CSS for styling
- [ ] Configure TypeScript (optional but recommended)
- [ ] Set up ESLint and Prettier

### Core Pages
- [ ] Homepage
  - [ ] Current season overview
  - [ ] Recent matches
  - [ ] Top teams/players
  - [ ] Navigation to other sections
- [ ] Team Pages
  - [ ] Team standings/rankings
  - [ ] Individual team detail page
  - [ ] Match history for team
  - [ ] Team statistics
- [ ] Player Pages
  - [ ] Player search/directory
  - [ ] Individual player profile
  - [ ] Player statistics and history
  - [ ] Performance charts
- [ ] Machine Pages
  - [ ] Machine directory/list
  - [ ] Individual machine statistics
  - [ ] High scores by venue
  - [ ] Percentile charts
- [ ] Venue Pages
  - [ ] Venue list
  - [ ] Machines at each venue
  - [ ] Match history at venue
- [ ] Match Pages
  - [ ] Match browser/search
  - [ ] Individual match details
  - [ ] Scores and results

### Data Visualization
- [ ] Choose charting library (Chart.js, Recharts)
- [ ] Create score distribution charts
- [ ] Create percentile visualizations
- [ ] Add win/loss charts
- [ ] Create performance trend lines
- [ ] Make charts responsive (mobile-friendly)

### Search & Filtering
- [ ] Add search bar (teams, players, machines)
- [ ] Implement filters (season, venue, team)
- [ ] Add sorting options (by date, score, etc.)
- [ ] Create filter UI components

### Responsive Design
- [ ] Test on mobile devices
- [ ] Test on tablet devices
- [ ] Test on desktop
- [ ] Optimize for different screen sizes
- [ ] Ensure touch-friendly navigation

### API Integration
- [ ] Create API client/service layer
- [ ] Implement data fetching with React Query or SWR
- [ ] Add loading states
- [ ] Add error handling
- [ ] Implement caching strategy

### Footer & Legal
- [ ] Add attribution statement
- [ ] Link to official MNP data repository
- [ ] Add contact/about page
- [ ] Create privacy policy (if collecting analytics)
- [ ] Add terms of service (basic)

### Deployment
- [ ] Deploy to Vercel or Netlify
- [ ] Configure custom domain
- [ ] Set up environment variables (API URL)
- [ ] Test production build
- [ ] Verify all pages work in production

### SEO & Analytics
- [ ] Add meta tags for SEO
- [ ] Create sitemap.xml
- [ ] Set up Plausible or Simple Analytics (privacy-friendly)
- [ ] Add Open Graph tags for social sharing
- [ ] Test Google search console

### Testing
- [ ] Test all navigation links
- [ ] Test all search/filter combinations
- [ ] Verify data accuracy
- [ ] Test performance (Lighthouse score)
- [ ] Cross-browser testing (Chrome, Firefox, Safari)

**Phase 3 Complete:** Public website is live ✅

---

## Phase 4: Advanced Features (Weeks 12+)

**Goal:** Community features and automation

### User Accounts (Optional)
- [ ] Choose auth provider (Supabase Auth, Auth0, Clerk)
- [ ] Implement sign up/login
- [ ] Create user profile pages
- [ ] Add "favorite teams" feature
- [ ] Add "favorite players" feature
- [ ] Store user preferences

### Notifications (Optional)
- [ ] Set up email service (SendGrid, Mailgun)
- [ ] Create notification preferences UI
- [ ] Implement weekly summary emails
- [ ] Add new match notifications
- [ ] Add high score notifications

### Admin Dashboard
- [ ] Create admin authentication
- [ ] Build data management UI
- [ ] Add manual data correction tools
- [ ] Create data validation checks
- [ ] Add audit logging

### API Enhancements
- [ ] Add API key system for high-volume users
- [ ] Create tiered rate limits
- [ ] Add webhook support (for Pin Stats app)
- [ ] Implement GraphQL endpoint (optional)

### Automated Reports
- [ ] Create automated weekly report generator
- [ ] Generate season summary reports
- [ ] Create player/team comparison tools
- [ ] Build custom report builder UI

### Community Features (Optional)
- [ ] Add comments on matches (moderated)
- [ ] Create community forum or discussion board
- [ ] Add "match of the week" voting
- [ ] Create leaderboards and challenges

**Phase 4 Complete:** Full-featured community platform ✅

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
- [ ] Review and respond to user feedback

### Seasonal Tasks
- [ ] Prepare for new season data
- [ ] Update season selectors in UI
- [ ] Generate end-of-season reports
- [ ] Archive old data (if needed)

---

## Rollback Procedures

### If API Goes Down
1. Check hosting platform status page
2. Review error logs in Sentry
3. Check database connection
4. Verify environment variables
5. Rollback to previous deployment if needed
6. Post status update for users

### If Database Issues Occur
1. Check database connection limits
2. Review slow query log
3. Verify backups are recent
4. Restore from backup if needed
5. Contact hosting provider support

### If Frontend Issues Occur
1. Check deployment logs
2. Test API endpoints separately
3. Review browser console errors
4. Rollback to previous deployment
5. Fix and redeploy

---

## Success Metrics

### Phase 1 Success
- [ ] Static API is accessible publicly
- [ ] Response time <500ms
- [ ] Zero downtime during deployment

### Phase 2 Success
- [ ] Dynamic API is live
- [ ] Response time <1s for 95% of requests
- [ ] 99.5% uptime
- [ ] Pin Stats iOS app successfully connects
- [ ] 100+ API requests/day

### Phase 3 Success
- [ ] Website is live and accessible
- [ ] Page load time <2s
- [ ] Mobile-friendly (responsive)
- [ ] 100+ monthly active users
- [ ] Positive community feedback

---

## Resources & Links

### Documentation
- [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md) - Full deployment plan
- [MNP_Data_Structure_Reference.md](../MNP_Data_Structure_Reference.md) - Data structure
- [README.md](../README.md) - Project overview

### Tools & Services
- **Domain Registration:** Namecheap, Google Domains, Cloudflare
- **Hosting:** Railway, Render, Fly.io
- **Database:** PostgreSQL (managed by hosting provider)
- **CDN:** Cloudflare (free tier)
- **Monitoring:** Sentry, Better Uptime
- **Analytics:** Plausible, Simple Analytics

### External Links
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Railway Documentation](https://docs.railway.app/)
- [Render Documentation](https://render.com/docs)

---

**Last Updated:** 2025-11-26
**Document Owner:** JJC
