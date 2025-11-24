# MNP Analyzer - Implementation Roadmap

## Overview

This document outlines the step-by-step implementation plan for building the MNP Analyzer mobile-first web application over an 8-9 week timeline.

## Project Milestones

| Milestone | Week | Deliverable | Status |
|-----------|------|-------------|--------|
| M1: Backend Foundation | Week 1-2 | Database + ETL + Basic API | Not Started |
| M2: API Development | Week 3-4 | Complete REST API | Not Started |
| M3: Frontend Core | Week 5-6 | React app + routing + API integration | Not Started |
| M4: Feature Complete | Week 7-8 | All 5 core features implemented | Not Started |
| M5: Production Ready | Week 9 | Testing + deployment + polish | Not Started |

---

## Phase 1: Backend Foundation (Weeks 1-2)

### Week 1: Database & Data Pipeline

#### Day 1-2: Database Setup
**Goal**: Create PostgreSQL database with full schema

**Tasks:**
- [ ] Set up local PostgreSQL instance
- [ ] Create database schema from [database/schema.md](database/schema.md)
- [ ] Write SQL migration scripts
- [ ] Add indexes from design doc
- [ ] Test schema with sample data
- [ ] Document connection strings and credentials

**Deliverables:**
- `schema/001_initial_schema.sql`
- `schema/002_indexes.sql`
- `schema/003_constraints.sql`
- Local database running and tested

**Success Criteria:**
- All tables created without errors
- Foreign key relationships work
- Indexes exist and are used in query plans

---

#### Day 3-5: ETL Pipeline Development
**Goal**: Load Season 22 data into database

**Tasks:**
- [ ] Create ETL project structure
- [ ] Write JSON parser for match files
- [ ] Implement machine_variations.json loader
- [ ] Build data transformation logic:
  - [ ] Extract players from lineups
  - [ ] Extract teams and venues
  - [ ] Extract games and scores
  - [ ] Handle machine key normalization
- [ ] Add data quality checks:
  - [ ] Validate score ranges
  - [ ] Check for duplicate games
  - [ ] Verify round structure (4 rounds per match)
- [ ] Create percentile calculation script
- [ ] Test with Season 22 data
- [ ] Generate summary report of loaded data

**Deliverables:**
- `etl/load_matches.py` - Main ETL script
- `etl/calculate_percentiles.py` - Percentile pre-calculation
- `etl/data_quality_checks.py` - Validation script
- `etl/README.md` - Usage documentation

**Success Criteria:**
- All Season 22 matches loaded successfully
- No data integrity errors
- Percentiles calculated for all machines
- Summary report shows expected counts:
  - ~20 teams
  - ~200 players
  - ~100 matches
  - ~400 games
  - ~1200 scores

**Files to Create:**
```
etl/
├── __init__.py
├── load_matches.py           # Main ETL orchestrator
├── parsers/
│   ├── __init__.py
│   ├── match_parser.py       # Parse match JSON files
│   ├── machine_parser.py     # Parse machine_variations.json
│   └── venue_parser.py       # Parse venues.csv
├── transformers/
│   ├── __init__.py
│   ├── normalize_keys.py     # Machine key normalization
│   └── calculate_stats.py    # Aggregate calculations
├── loaders/
│   ├── __init__.py
│   ├── db_loader.py          # Insert into PostgreSQL
│   └── batch_loader.py       # Batch insert optimization
├── quality/
│   ├── __init__.py
│   ├── validators.py         # Data validation rules
│   └── reports.py            # Quality reports
└── config.py                 # Database and path configs
```

---

#### Day 6-7: Basic API Setup
**Goal**: Create FastAPI project with health check endpoint

**Tasks:**
- [ ] Initialize FastAPI project
- [ ] Set up project structure
- [ ] Configure SQLAlchemy ORM
- [ ] Create database connection pool
- [ ] Write Pydantic models for responses
- [ ] Implement health check endpoint
- [ ] Add CORS configuration
- [ ] Test API locally with curl/Postman

**Deliverables:**
- `api/main.py` - FastAPI app entry point
- `api/models/` - SQLAlchemy models
- `api/schemas/` - Pydantic schemas
- `api/database.py` - Database connection
- `requirements.txt` - Python dependencies

**Success Criteria:**
- API starts without errors
- Health check endpoint returns 200 OK
- Database connection works
- CORS allows localhost:3000

**Project Structure:**
```
api/
├── main.py                   # FastAPI app
├── config.py                 # Configuration
├── database.py               # DB connection
├── models/
│   ├── __init__.py
│   ├── player.py
│   ├── team.py
│   ├── machine.py
│   ├── venue.py
│   └── score.py
├── schemas/
│   ├── __init__.py
│   ├── player.py
│   ├── team.py
│   └── response.py
├── routers/
│   ├── __init__.py
│   ├── players.py
│   ├── teams.py
│   ├── machines.py
│   └── venues.py
├── services/
│   ├── __init__.py
│   ├── player_service.py
│   ├── percentile_service.py
│   └── stats_service.py
└── utils/
    ├── __init__.py
    └── helpers.py
```

---

### Week 2: Core API Endpoints

#### Day 8-10: Player Endpoints
**Goal**: Implement all player-related API endpoints

**Tasks:**
- [ ] GET /api/v1/players/search
  - [ ] Name search with fuzzy matching
  - [ ] Pagination support
  - [ ] Test with various queries
- [ ] GET /api/v1/players/{player_key}
  - [ ] Return player details
  - [ ] Include season stats
  - [ ] Handle not found errors
- [ ] GET /api/v1/players/{player_key}/stats
  - [ ] Venue filtering
  - [ ] Season filtering
  - [ ] Round type breakdown
- [ ] GET /api/v1/players/{player_key}/machine-picks
  - [ ] Filter by venue machines
  - [ ] Sort by pick frequency
- [ ] GET /api/v1/players/{player_key}/best-machines
  - [ ] Rank by median percentile
  - [ ] Min games filter
  - [ ] Venue filtering

**Deliverables:**
- `api/routers/players.py` - All player endpoints
- `api/services/player_service.py` - Business logic
- Unit tests for each endpoint
- API documentation (auto-generated by FastAPI)

**Success Criteria:**
- All endpoints return correct data
- Filters work as expected
- Response times < 500ms
- Error handling works (404, 400, 500)

---

#### Day 11-12: Team & Machine Endpoints
**Goal**: Implement team and machine endpoints

**Tasks:**
- [ ] Team endpoints:
  - [ ] GET /api/v1/teams/search
  - [ ] GET /api/v1/teams/{team_key}
  - [ ] GET /api/v1/teams/{team_key}/machine-picks
  - [ ] GET /api/v1/teams/{team_key}/roster
  - [ ] GET /api/v1/teams/{team_key}/player-stats
- [ ] Machine endpoints:
  - [ ] GET /api/v1/machines
  - [ ] GET /api/v1/machines/{machine_key}
  - [ ] GET /api/v1/machines/{machine_key}/scores
  - [ ] GET /api/v1/machines/{machine_key}/percentiles
- [ ] Add response caching headers
- [ ] Write integration tests

**Deliverables:**
- `api/routers/teams.py`
- `api/routers/machines.py`
- `api/services/team_service.py`
- `api/services/machine_service.py`
- Integration tests

**Success Criteria:**
- All endpoints functional
- Caching headers set correctly
- Query optimization (no N+1 queries)

---

#### Day 13-14: Utility Endpoints & Deployment Prep
**Goal**: Complete API with utility endpoints and prepare for deployment

**Tasks:**
- [ ] Utility endpoints:
  - [ ] GET /api/v1/venues
  - [ ] GET /api/v1/venues/{venue_key}
  - [ ] POST /api/v1/scores/calculate-percentile
  - [ ] GET /api/v1/matchups/compare
  - [ ] GET /api/v1/seasons
- [ ] Add rate limiting
- [ ] Implement logging
- [ ] Write API documentation
- [ ] Set up Railway/Render account
- [ ] Deploy backend to staging
- [ ] Test deployed API

**Deliverables:**
- `api/routers/venues.py`
- `api/routers/utils.py`
- `api/middleware/rate_limit.py`
- Deployment config files
- API deployed and accessible

**Success Criteria:**
- API accessible via public URL
- All endpoints work in production
- Rate limiting functional
- Logs visible in dashboard

---

## Phase 2: API Completion & Testing (Weeks 3-4)

### Week 3: API Polish & Optimization

#### Day 15-16: Performance Optimization
**Goal**: Ensure API meets performance requirements

**Tasks:**
- [ ] Profile slow queries
- [ ] Add missing indexes
- [ ] Optimize N+1 queries
- [ ] Implement query result caching
- [ ] Add database connection pooling
- [ ] Load test with k6 or Apache Bench
- [ ] Target: < 500ms p95 response time

**Deliverables:**
- Performance test results
- Optimized queries
- Caching layer implemented

---

#### Day 17-18: Error Handling & Validation
**Goal**: Robust error handling and input validation

**Tasks:**
- [ ] Comprehensive input validation
- [ ] Consistent error response format
- [ ] Handle edge cases:
  - [ ] Player with no games
  - [ ] Machine not at venue
  - [ ] Invalid season
- [ ] Add request/response logging
- [ ] Error tracking setup (Sentry)

**Deliverables:**
- `api/middleware/error_handler.py`
- Error documentation
- Sentry integration

---

#### Day 19-21: Testing & Documentation
**Goal**: Complete test coverage and API docs

**Tasks:**
- [ ] Write unit tests for services
- [ ] Write integration tests for endpoints
- [ ] Add test fixtures and factories
- [ ] Target: 80%+ code coverage
- [ ] Complete API documentation:
  - [ ] Endpoint descriptions
  - [ ] Request/response examples
  - [ ] Error codes
- [ ] Create Postman collection
- [ ] Write API usage guide

**Deliverables:**
- Test suite with 80%+ coverage
- Complete API documentation
- Postman collection for testing

---

### Week 4: Frontend Preparation

#### Day 22-24: Frontend Project Setup
**Goal**: Initialize Next.js project with proper structure

**Tasks:**
- [ ] Create Next.js 14 project
- [ ] Configure TypeScript
- [ ] Set up Tailwind CSS
- [ ] Install dependencies:
  - [ ] TanStack Query
  - [ ] Zustand
  - [ ] Recharts
  - [ ] Lucide icons
- [ ] Configure project structure:
  - [ ] app/ (App Router)
  - [ ] components/
  - [ ] lib/
  - [ ] hooks/
  - [ ] types/
- [ ] Set up environment variables
- [ ] Configure API client
- [ ] Create base layout
- [ ] Test dev server

**Deliverables:**
- Next.js project initialized
- Directory structure established
- Development environment working

**Project Structure:**
```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── players/
│   ├── teams/
│   ├── machines/
│   └── compare/
├── components/
│   ├── ui/                 # shadcn/ui components
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Navigation.tsx
│   │   └── VenueSelector.tsx
│   ├── player/
│   │   ├── PlayerCard.tsx
│   │   ├── PlayerStats.tsx
│   │   └── MachineList.tsx
│   ├── team/
│   └── machine/
├── lib/
│   ├── api.ts             # API client
│   ├── utils.ts           # Helper functions
│   └── constants.ts
├── hooks/
│   ├── usePlayer.ts
│   ├── useTeam.ts
│   └── useMachine.ts
├── types/
│   ├── player.ts
│   ├── team.ts
│   └── machine.ts
└── public/
    └── icons/
```

---

#### Day 25-28: Component Library
**Goal**: Build reusable UI components

**Tasks:**
- [ ] Set up shadcn/ui
- [ ] Create base components:
  - [ ] Button (primary, secondary, icon)
  - [ ] Card (basic, machine, player)
  - [ ] Badge (percentile colors)
  - [ ] Input (search, select)
  - [ ] Progress bar
  - [ ] Skeleton loaders
  - [ ] Empty states
- [ ] Create layout components:
  - [ ] Header with navigation
  - [ ] Venue selector dropdown
  - [ ] Search bar with autocomplete
- [ ] Test components in Storybook (optional)
- [ ] Write component documentation

**Deliverables:**
- Complete component library
- Component documentation
- Storybook stories (optional)

**Success Criteria:**
- All components mobile-responsive
- Consistent styling across components
- Accessibility features implemented

---

## Phase 3: Frontend Development (Weeks 5-6)

### Week 5: Core Screens

#### Day 29-31: Home & Search
**Goal**: Implement home screen and search functionality

**Tasks:**
- [ ] Home screen:
  - [ ] Venue selector
  - [ ] Search bar
  - [ ] Quick access cards
  - [ ] Recent matches list
- [ ] Search functionality:
  - [ ] Player search with autocomplete
  - [ ] Team search
  - [ ] Search results page
  - [ ] Result cards
- [ ] API integration with TanStack Query
- [ ] Loading states
- [ ] Error handling

**Deliverables:**
- `app/page.tsx` - Home screen
- `app/search/page.tsx` - Search results
- `hooks/useSearch.ts` - Search logic
- Mobile-responsive design

---

#### Day 32-35: Player Screens
**Goal**: Complete player detail and machine picker

**Tasks:**
- [ ] Player detail screen:
  - [ ] Player header
  - [ ] Stats summary
  - [ ] Venue filter
  - [ ] Best machines list
  - [ ] Performance breakdown
- [ ] Machine picker screen:
  - [ ] Context header
  - [ ] Round type filters
  - [ ] Top 3 picks highlighted
  - [ ] All machines list
  - [ ] Sort and filter
- [ ] Machine detail screen:
  - [ ] Performance summary
  - [ ] Score distribution chart
  - [ ] Score targets
  - [ ] Game history
- [ ] Navigation between screens
- [ ] API data fetching
- [ ] Caching strategy

**Deliverables:**
- `app/players/[key]/page.tsx`
- `app/players/[key]/machines/page.tsx`
- `app/players/[key]/machines/[machine]/page.tsx`
- Complete player flow

---

### Week 6: Team & Comparison Screens

#### Day 36-38: Team Intel
**Goal**: Implement team intelligence screens

**Tasks:**
- [ ] Team search and selection
- [ ] Team detail screen:
  - [ ] Team header
  - [ ] Home venue info
  - [ ] Filter tabs (home/away, singles/doubles)
  - [ ] Machine picks ranking
  - [ ] Top players list
- [ ] Team roster view:
  - [ ] Full roster with stats
  - [ ] Player cards
  - [ ] Sort by performance
- [ ] Player stats on machine:
  - [ ] Team member rankings
  - [ ] Detailed stats per player
- [ ] Navigation and routing

**Deliverables:**
- `app/teams/[key]/page.tsx`
- `app/teams/[key]/roster/page.tsx`
- Team intel complete

---

#### Day 39-42: Player Comparison & Polish
**Goal**: Complete comparison feature and polish UI

**Tasks:**
- [ ] Player comparison screen:
  - [ ] Player selection (search)
  - [ ] Machine and venue filters
  - [ ] Side-by-side stats
  - [ ] Advantage indicator
  - [ ] Head-to-head record
- [ ] Machine lookup feature:
  - [ ] Browse all machines
  - [ ] Filter by venue
  - [ ] View machine details
- [ ] UI polish:
  - [ ] Smooth animations
  - [ ] Transitions between pages
  - [ ] Loading states refinement
  - [ ] Empty states
  - [ ] Error boundaries
- [ ] Mobile responsiveness check
- [ ] Touch interaction testing

**Deliverables:**
- `app/compare/page.tsx`
- `app/machines/page.tsx`
- Polished, complete UI

---

## Phase 4: Feature Complete (Weeks 7-8)

### Week 7: Data Visualization & PWA

#### Day 43-45: Charts and Visualizations
**Goal**: Add data visualization with Recharts

**Tasks:**
- [ ] Score distribution charts:
  - [ ] Line chart for percentiles
  - [ ] Mobile-optimized size
  - [ ] Interactive tooltips
- [ ] Performance trend charts:
  - [ ] Player performance over time
  - [ ] Bar charts for comparisons
- [ ] Percentile indicators:
  - [ ] Visual progress bars
  - [ ] Color-coded badges
- [ ] Chart loading states
- [ ] Responsive chart sizing

**Deliverables:**
- `components/charts/PercentileChart.tsx`
- `components/charts/TrendChart.tsx`
- Charts integrated into screens

---

#### Day 46-49: PWA Setup & Offline Support
**Goal**: Convert to Progressive Web App

**Tasks:**
- [ ] Install next-pwa
- [ ] Configure service worker
- [ ] Add web app manifest:
  - [ ] App icons
  - [ ] Splash screens
  - [ ] Theme colors
- [ ] Implement offline support:
  - [ ] Cache API responses
  - [ ] Offline indicator
  - [ ] Sync when online
- [ ] Add install prompt
- [ ] Test on mobile devices
- [ ] Test offline functionality

**Deliverables:**
- PWA configuration
- Service worker caching
- Install-able app
- Offline support

---

### Week 8: Performance & Accessibility

#### Day 50-52: Performance Optimization
**Goal**: Optimize for mobile performance

**Tasks:**
- [ ] Code splitting:
  - [ ] Route-based splitting
  - [ ] Component lazy loading
- [ ] Image optimization:
  - [ ] Use Next.js Image
  - [ ] Lazy loading
  - [ ] WebP format
- [ ] Bundle size optimization:
  - [ ] Analyze bundle
  - [ ] Remove unused code
  - [ ] Tree shaking
- [ ] Lighthouse audit:
  - [ ] Target: 90+ performance score
  - [ ] Fix identified issues
- [ ] Load time optimization:
  - [ ] Target: < 2s initial load on 4G

**Deliverables:**
- Lighthouse score 90+
- Bundle size < 200KB
- Fast load times

---

#### Day 53-56: Accessibility & Testing
**Goal**: Ensure WCAG 2.1 AA compliance and thorough testing

**Tasks:**
- [ ] Accessibility audit:
  - [ ] Keyboard navigation
  - [ ] Screen reader testing
  - [ ] Color contrast checks
  - [ ] Focus indicators
  - [ ] ARIA labels
- [ ] Cross-browser testing:
  - [ ] Safari (iOS)
  - [ ] Chrome (Android)
  - [ ] Firefox
  - [ ] Edge
- [ ] Device testing:
  - [ ] iPhone (various sizes)
  - [ ] Android phones
  - [ ] Tablets
- [ ] User acceptance testing:
  - [ ] Test all 5 core features
  - [ ] Follow real-world usage patterns
  - [ ] Document bugs
- [ ] Fix critical bugs

**Deliverables:**
- Accessibility report
- Cross-browser test results
- Bug fixes completed
- UAT sign-off

---

## Phase 5: Production Launch (Week 9)

### Week 9: Testing, Documentation & Launch

#### Day 57-59: Final Testing
**Goal**: Comprehensive testing before launch

**Tasks:**
- [ ] End-to-end testing:
  - [ ] All user flows
  - [ ] Edge cases
  - [ ] Error scenarios
- [ ] Load testing:
  - [ ] API under load
  - [ ] Database performance
  - [ ] CDN caching
- [ ] Security review:
  - [ ] HTTPS everywhere
  - [ ] CORS configuration
  - [ ] Input validation
  - [ ] Rate limiting
- [ ] Data accuracy verification:
  - [ ] Compare with existing reports
  - [ ] Verify percentile calculations
  - [ ] Check machine picks
- [ ] Fix all critical and high-priority bugs

**Deliverables:**
- Test reports
- Bug fixes
- Security sign-off

---

#### Day 60-61: Documentation & Deployment
**Goal**: Complete documentation and deploy to production

**Tasks:**
- [ ] User documentation:
  - [ ] How to use guide
  - [ ] Feature explanations
  - [ ] FAQ
- [ ] Technical documentation:
  - [ ] Deployment guide
  - [ ] Database maintenance
  - [ ] ETL update process
- [ ] Production deployment:
  - [ ] Backend to Railway/Render
  - [ ] Frontend to Vercel
  - [ ] Configure custom domain (optional)
  - [ ] Set up monitoring (Sentry, Vercel Analytics)
- [ ] Post-deployment verification:
  - [ ] Smoke tests
  - [ ] Performance check
  - [ ] API health check

**Deliverables:**
- User guide
- Deployment docs
- Production app live
- Monitoring configured

---

#### Day 62-63: Launch & Feedback
**Goal**: Soft launch and gather feedback

**Tasks:**
- [ ] Soft launch to beta testers:
  - [ ] Share with team captains
  - [ ] Share with MNP organizers
- [ ] Monitor usage:
  - [ ] Analytics
  - [ ] Error logs
  - [ ] Performance metrics
- [ ] Gather feedback:
  - [ ] User interviews
  - [ ] Bug reports
  - [ ] Feature requests
- [ ] Prioritize improvements
- [ ] Create backlog for Phase 2

**Deliverables:**
- App accessible to users
- Feedback collected
- Improvement backlog
- Launch retrospective

---

## Success Metrics

### Phase 1 (Backend)
- ✅ Database schema created without errors
- ✅ Season 22 data loaded successfully
- ✅ All API endpoints functional
- ✅ API deployed and accessible

### Phase 2 (API Complete)
- ✅ All 5 core questions answerable via API
- ✅ Response times < 500ms p95
- ✅ 80%+ test coverage
- ✅ API documentation complete

### Phase 3 (Frontend)
- ✅ All screens implemented
- ✅ Mobile-responsive design
- ✅ API integration working
- ✅ PWA installable

### Phase 4 (Feature Complete)
- ✅ All 5 core features working
- ✅ Data visualizations implemented
- ✅ Offline support functional
- ✅ Performance optimized (< 2s load)

### Phase 5 (Production)
- ✅ WCAG 2.1 AA compliant
- ✅ Lighthouse score 90+
- ✅ Zero critical bugs
- ✅ Deployed and stable

---

## Risk Management

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Database performance issues | High | Pre-calculate aggregates, optimize queries, add indexes |
| API response time too slow | High | Implement caching, optimize database queries, use CDN |
| Mobile performance poor | Medium | Code splitting, lazy loading, bundle optimization |
| Data quality issues | Medium | Comprehensive validation, data quality checks |
| Deployment challenges | Low | Use proven platforms (Vercel, Railway) |

### Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Features take longer than estimated | Medium | Prioritize core features, cut nice-to-haves |
| Testing reveals major bugs | Medium | Buffer week for fixes, continuous testing |
| API changes needed mid-development | Low | Solid API design upfront, versioning strategy |

---

## Post-Launch Roadmap (Phase 2)

### Priority 1 (Weeks 10-12)
- Real-time match tracking
- Match prediction engine
- Historical season data (Season 21)
- Advanced filtering options

### Priority 2 (Weeks 13-16)
- User accounts and saved preferences
- Team roster optimization tool
- Push notifications
- Social features (comments, sharing)

### Priority 3 (Future)
- Machine learning predictions
- Tournament mode
- IFPA data integration
- Advanced analytics dashboard

---

## Development Environment

### Required Tools
- **Node.js**: 18+ for frontend
- **Python**: 3.11+ for backend and ETL
- **PostgreSQL**: 15+ for database
- **Git**: Version control
- **VS Code**: Recommended IDE

### Development Workflow
1. Create feature branch from `main`
2. Develop and test locally
3. Write tests for new features
4. Submit PR with description
5. Code review (if team project)
6. Merge to `main`
7. Deploy to staging
8. Test in staging
9. Deploy to production

---

**Roadmap Version**: 1.0
**Last Updated**: 2025-01-23
**Status**: Planning Phase
**Estimated Total Time**: 9 weeks (63 days)
**Target Completion**: March 2025
