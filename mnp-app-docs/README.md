# MNP Analyzer - Mobile-First Pinball Analytics App

## Project Overview

**MNP Analyzer** is a mobile-first Progressive Web App (PWA) designed to provide Monday Night Pinball players with instant access to performance analytics, machine recommendations, and competitive intelligence while at venues.

## Core Value Proposition

- **Quick machine selection** based on your historical performance at the current venue
- **Score targets** to know what percentile you're hitting during a game
- **Team intelligence** to understand opponent preferences and strengths
- **Player comparisons** for strategic matchup decisions
- **Historical trends** to track improvement and identify opportunities

## Target Users

- **Primary**: MNP players using mobile devices at venues during matches
- **Secondary**: Team captains doing pre-match strategy planning
- **Tertiary**: League statisticians and analysts

## Technology Stack

### Frontend (Mobile-First PWA)
- **Framework**: Next.js 14 (App Router, React Server Components)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Charts**: Recharts (mobile-optimized)
- **PWA**: next-pwa for offline support

### Backend API
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2
- **Database**: PostgreSQL 15+
- **Caching**: Redis (optional, phase 2)
- **CORS**: Configured for Vercel frontend

### Database
- **Primary**: PostgreSQL
- **Schema**: Normalized with denormalized query tables for performance
- **Indexing**: Strategic indexes on high-frequency query patterns
- **Migrations**: Alembic

### Deployment
- **Frontend**: Vercel (free tier)
- **Backend**: Railway or Render (free tier initially)
- **Database**: Included with Railway/Render, or Supabase
- **Domain**: TBD (mnp-analyzer.vercel.app initially)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Mobile Browser (PWA)                     │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐           │
│  │ Home/Search│  │ Machine    │  │ Team Intel  │           │
│  │            │  │ Picker     │  │             │           │
│  └────────────┘  └────────────┘  └─────────────┘           │
│         │                │                 │                 │
│         └────────────────┴─────────────────┘                │
│                          │                                   │
│                 Next.js Frontend (Vercel)                    │
│                          │                                   │
│                    TanStack Query                            │
│                   (caching & sync)                           │
└──────────────────────────┼───────────────────────────────────┘
                           │ HTTPS/REST
┌──────────────────────────┼───────────────────────────────────┐
│                   FastAPI Backend                            │
│                   (Railway/Render)                           │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐           │
│  │ Player     │  │ Team       │  │ Machine     │           │
│  │ Endpoints  │  │ Endpoints  │  │ Endpoints   │           │
│  └────────────┘  └────────────┘  └─────────────┘           │
│         │                │                 │                 │
│         └────────────────┴─────────────────┘                │
│                          │                                   │
│                   SQLAlchemy ORM                             │
│                          │                                   │
│  ┌───────────────────────┴──────────────────────┐           │
│  │         PostgreSQL Database                  │           │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐     │           │
│  │  │ Core     │ │ Stats    │ │ Cache    │     │           │
│  │  │ Tables   │ │ Tables   │ │ Tables   │     │           │
│  │  └──────────┘ └──────────┘ └──────────┘     │           │
│  └──────────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────┘
                           ▲
                           │
                    ETL Pipeline (Python)
                           │
                  ┌────────┴─────────┐
                  │ mnp-data-archive │
                  │  (Season JSONs)  │
                  └──────────────────┘
```

## Key Features

### Phase 1 (MVP - 4 weeks)
1. **Player Stats Lookup**
   - Search for any player by name
   - View their machine performance at specific venues
   - See median scores and percentile rankings

2. **Machine Picker**
   - Filter machines by current venue
   - Rank by player's historical percentile performance
   - Show sample size (games played)

3. **Score Distribution**
   - View percentile curves for any machine
   - Calculate "what score do I need for X percentile?"
   - Compare venue-specific vs. all-venue stats

4. **Team Machine Picks**
   - Most frequently picked machines by team
   - Filter by home/away and singles/doubles
   - See success rates

5. **Player Comparison**
   - Compare two players on a specific machine
   - Head-to-head matchup statistics

### Phase 2 (4-8 weeks)
- Real-time match tracking
- Match prediction engine
- Team roster optimization
- Historical trend analysis
- Export/share reports
- Push notifications for league updates

### Phase 3 (Future)
- Machine learning predictions
- Social features (comments, strategy sharing)
- Tournament mode
- Integration with IFPA data
- Advanced visualizations

## Core Questions Answered

The app is designed to answer these specific analytical questions:

1. **What machines does player X most often pick?**
   - Filtered for machines currently at the venue where the match is taking place
   - Endpoint: `GET /api/players/{player_key}/machine-picks?venue={venue}`

2. **What machines does team X pick at home most often?**
   - Separate filters for singles vs. doubles rounds
   - Endpoint: `GET /api/teams/{team_key}/machine-picks?home=true&round_type={singles|doubles}`

3. **What is the distribution of scores on machine X at venue Y?**
   - Percentile curves and targets
   - Endpoint: `GET /api/machines/{machine_key}/scores?venue={venue}`

4. **Which player on team X has the highest median score on machine Y?**
   - Team roster rankings by machine
   - Endpoint: `GET /api/teams/{team_key}/player-stats?machine={machine}`

5. **For player X at venue Y, what are their best machines?**
   - Ranked by median percentile compared to all other player scores on those machines at that venue
   - Endpoint: `GET /api/players/{player_key}/best-machines?venue={venue}`

## Data Sources

### Primary Data
- **MNP Data Archive**: `/mnp-data-archive/season-*/matches/*.json`
- **Machine Variations**: `/machine_variations.json`
- **Venue Data**: `/mnp-data-archive/season-*/venues.csv`
- **Team Data**: `/mnp-data-archive/season-*/teams.csv`
- **Player Rosters**: `/mnp-data-archive/season-*/rosters.csv`

### Data Refresh Strategy
- **Initial Load**: Full ETL of all historical seasons
- **Weekly Updates**: Incremental load of new matches
- **Real-time**: Manual trigger or webhook (Phase 2)

## Performance Requirements

### Mobile-First Constraints
- **Initial page load**: < 2 seconds on 4G
- **API response time**: < 500ms for cached queries
- **PWA offline**: Core lookup features work without connection
- **Bundle size**: < 200KB initial JS bundle
- **Data usage**: Minimal - aggressive caching

### Database Query Performance
- **Player lookup**: < 100ms
- **Machine stats**: < 200ms
- **Percentile calculation**: Pre-calculated, < 50ms lookup
- **Search**: < 300ms with autocomplete

## Security & Privacy

- **No authentication required** (Phase 1 - public data)
- **Rate limiting**: Prevent abuse (100 requests/minute/IP)
- **Player data**: Already public through league website
- **CORS**: Locked to production domain
- **HTTPS only**: All communication encrypted

## Documentation Structure

```
mnp-app-docs/
├── README.md (this file)
├── database/
│   ├── schema.md              # Full database schema with relationships
│   ├── indexes.md             # Index strategy and rationale
│   ├── sample-queries.sql     # Example queries for common use cases
│   └── migration-plan.md      # Schema evolution strategy
├── api/
│   ├── endpoints.md           # Complete API specification
│   ├── response-formats.md    # JSON response schemas
│   ├── error-handling.md      # Error codes and messages
│   └── authentication.md      # Future auth strategy
├── frontend/
│   ├── ui-design.md           # Screen mockups and user flows
│   ├── components.md          # Component library documentation
│   ├── state-management.md    # Data flow and caching strategy
│   └── pwa-strategy.md        # Offline support and caching
├── data-pipeline/
│   ├── etl-process.md         # ETL pipeline documentation
│   ├── data-quality.md        # Data validation and cleaning rules
│   └── percentile-calculation.md  # Algorithm documentation
└── deployment/
    ├── infrastructure.md      # Hosting setup and configuration
    ├── ci-cd.md              # Build and deployment pipeline
    └── monitoring.md          # Logging and error tracking
```

## Project Timeline

### Week 1-2: Backend Foundation
- Database schema creation
- ETL pipeline development
- Load Season 22 data
- Basic FastAPI setup

### Week 3-4: API Development
- Implement core endpoints
- Response validation
- Caching strategy
- API documentation
- Backend deployment

### Week 5-6: Frontend Core
- Next.js project setup
- Component library
- Mobile-responsive layout
- API integration
- PWA configuration

### Week 7-8: Feature Implementation
- All 5 core features
- Data visualizations
- Search functionality
- Performance optimization

### Week 9: Testing & Launch
- Mobile device testing
- Performance tuning
- Bug fixes
- Production deployment
- User documentation

## Success Metrics

### Phase 1 (MVP)
- **Functionality**: All 5 core questions answered accurately
- **Performance**: < 2s initial load, < 500ms API responses
- **Usability**: Can complete a lookup in < 10 seconds
- **Accuracy**: Data matches existing report generators

### Phase 2 (Adoption)
- **Usage**: 10+ unique users per week
- **Engagement**: 3+ queries per user per match day
- **Reliability**: 99% uptime during match nights
- **Feedback**: Positive response from team captains

## Development Setup (Future)

This section will be expanded with:
- Local development environment setup
- Database seeding instructions
- Frontend dev server configuration
- API testing procedures

## Contributing

Currently a single-developer project. Future expansion may include:
- Code style guidelines
- PR review process
- Testing requirements

## License

TBD - Likely MIT or similar open source license for code
Data remains property of Monday Night Pinball

---

**Project Start Date**: 2025-01-23
**Target MVP Date**: 2025-03-23 (8 weeks)
**Primary Developer**: JJC
**LLM Assistant**: Claude (Anthropic)

## Questions for Next Session

Track open questions and decisions needed:

1. App naming - finalize "MNP Analyzer" or choose alternative?
2. Deployment platform preference - Railway vs. Render vs. other?
3. Domain name - purchase custom or use vercel subdomain?
4. Data refresh frequency - manual trigger vs. scheduled?
5. Multi-season support - all seasons or just current + last?
6. IPR filtering - should low-sample-size players be filtered?
7. Mobile-first vs. mobile-only - support desktop at all?

## Notes for Future LLM Context

**Key Conventions:**
- Player keys are SHA-1 hashes (40 hex chars)
- Team keys are 3-letter codes (e.g., "ADB", "TBT")
- Venue keys are 3-4 letter codes (e.g., "T4B", "JUP")
- Machine keys use variations.json canonical names
- Seasons are integers (22 = 2025 season)
- Weeks are 1-10 for regular season

**Data Quality Notes:**
- Player 4 scores in 4-player games (rounds 1,4) may be unreliable
- Scores are NOT comparable across different machines
- Always use percentiles for cross-machine comparisons
- Home venue advantage is measurable - account for it

**Existing Tools to Leverage:**
- Score percentile report generator (Python)
- Machine variations lookup
- Home advantage analysis scripts
- Venue summary reports

**Design Philosophy:**
- Mobile-first always
- Speed over features
- Accuracy over completeness
- Progressive enhancement
