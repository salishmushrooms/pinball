# MNP Analyzer Documentation Index

## Quick Start Guide

**New to this project?** Start here:
1. Read [README.md](README.md) for project overview
2. Review [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) for timeline
3. Check current phase and jump to relevant docs below

**Current Phase**: Planning & Documentation (Week 0)
**Next Phase**: Backend Foundation (Weeks 1-2)

---

## Documentation Structure

### 📘 Core Documents

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [README.md](README.md) | Project overview, architecture, tech stack | First time / onboarding |
| [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) | Week-by-week implementation plan | Planning / tracking progress |

### 🗄️ Database Documentation

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [database/schema.md](database/schema.md) | Complete database schema design | Before implementing database |
| [database/indexes.md](database/indexes.md) | Index strategy and optimization | During database setup |
| [database/sample-queries.sql](database/sample-queries.sql) | Example SQL queries | When writing queries |
| [database/migration-plan.md](database/migration-plan.md) | Schema evolution strategy | Before schema changes |

**Status**: Schema design complete, implementation files TBD

### 🔌 API Documentation

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [api/endpoints.md](api/endpoints.md) | Complete API specification | Before implementing API |
| [api/response-formats.md](api/response-formats.md) | JSON response schemas | When writing API responses |
| [api/error-handling.md](api/error-handling.md) | Error codes and messages | When handling errors |
| [api/authentication.md](api/authentication.md) | Future auth strategy (Phase 2) | Before adding user accounts |

**Status**: Endpoints specification complete, implementation files TBD

### 🎨 Frontend Documentation

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [frontend/ui-design.md](frontend/ui-design.md) | Screen mockups and component designs | Before building UI |
| [frontend/components.md](frontend/components.md) | Component library documentation | When building components |
| [frontend/state-management.md](frontend/state-management.md) | Data flow and caching strategy | When integrating API |
| [frontend/pwa-strategy.md](frontend/pwa-strategy.md) | Offline support and caching | When implementing PWA |

**Status**: UI design complete, implementation files TBD

### ⚙️ Data Pipeline Documentation

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [data-pipeline/etl-process.md](data-pipeline/etl-process.md) | ETL pipeline documentation | Before loading data |
| [data-pipeline/data-quality.md](data-pipeline/data-quality.md) | Validation and cleaning rules | When implementing ETL |
| [data-pipeline/percentile-calculation.md](data-pipeline/percentile-calculation.md) | Algorithm documentation | Before calculating percentiles |

**Status**: ETL design complete, implementation files TBD

### 🚀 Deployment Documentation

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [deployment/infrastructure.md](deployment/infrastructure.md) | Hosting setup and configuration | Before deploying |
| [deployment/ci-cd.md](deployment/ci-cd.md) | Build and deployment pipeline | When setting up CI/CD |
| [deployment/monitoring.md](deployment/monitoring.md) | Logging and error tracking | After deployment |

**Status**: TBD (Week 4 and Week 9)

---

## By Development Phase

### Phase 1: Backend Foundation (Weeks 1-2)

**Week 1: Database & ETL**
- [ ] [database/schema.md](database/schema.md) - Implement schema
- [ ] [data-pipeline/etl-process.md](data-pipeline/etl-process.md) - Build ETL pipeline
- [ ] [data-pipeline/data-quality.md](data-pipeline/data-quality.md) - Add validation

**Week 2: API Setup**
- [ ] [api/endpoints.md](api/endpoints.md) - Implement endpoints
- [ ] [api/response-formats.md](api/response-formats.md) - Format responses
- [ ] [api/error-handling.md](api/error-handling.md) - Handle errors

### Phase 2: API Development (Weeks 3-4)

**Week 3: API Polish**
- [ ] [database/indexes.md](database/indexes.md) - Optimize queries
- [ ] Performance testing and optimization

**Week 4: Frontend Prep**
- [ ] [frontend/components.md](frontend/components.md) - Component library
- [ ] Project setup and structure

### Phase 3: Frontend Development (Weeks 5-6)

**Week 5: Core Screens**
- [ ] [frontend/ui-design.md](frontend/ui-design.md) - Build screens
- [ ] [frontend/state-management.md](frontend/state-management.md) - State and API integration

**Week 6: Features**
- [ ] [frontend/ui-design.md](frontend/ui-design.md) - Complete all screens
- [ ] [frontend/components.md](frontend/components.md) - Polish components

### Phase 4: Feature Complete (Weeks 7-8)

**Week 7: Visualization & PWA**
- [ ] [frontend/pwa-strategy.md](frontend/pwa-strategy.md) - PWA setup
- [ ] Charts and data visualization

**Week 8: Polish**
- [ ] Performance optimization
- [ ] Accessibility compliance

### Phase 5: Production (Week 9)

**Week 9: Launch**
- [ ] [deployment/infrastructure.md](deployment/infrastructure.md) - Deploy
- [ ] [deployment/monitoring.md](deployment/monitoring.md) - Monitor
- [ ] [deployment/ci-cd.md](deployment/ci-cd.md) - CI/CD pipeline

---

## By Feature

### Player Statistics
**API**: [api/endpoints.md](api/endpoints.md) → Player Endpoints
**Frontend**: [frontend/ui-design.md](frontend/ui-design.md) → Player Detail Screen
**Data**: [database/schema.md](database/schema.md) → `players`, `scores`, `player_machine_stats`

### Machine Picker
**API**: [api/endpoints.md](api/endpoints.md) → `GET /players/{key}/best-machines`
**Frontend**: [frontend/ui-design.md](frontend/ui-design.md) → Machine Picker Screen
**Data**: [database/schema.md](database/schema.md) → `player_machine_stats`, `venue_machines`

### Score Distribution
**API**: [api/endpoints.md](api/endpoints.md) → `GET /machines/{key}/percentiles`
**Frontend**: [frontend/ui-design.md](frontend/ui-design.md) → Machine Detail Screen
**Data**: [database/schema.md](database/schema.md) → `score_percentiles`, `scores`
**Algorithm**: [data-pipeline/percentile-calculation.md](data-pipeline/percentile-calculation.md)

### Team Intelligence
**API**: [api/endpoints.md](api/endpoints.md) → Team Endpoints
**Frontend**: [frontend/ui-design.md](frontend/ui-design.md) → Team Intel Screen
**Data**: [database/schema.md](database/schema.md) → `teams`, `team_machine_picks`

### Player Comparison
**API**: [api/endpoints.md](api/endpoints.md) → `GET /matchups/compare`
**Frontend**: [frontend/ui-design.md](frontend/ui-design.md) → Player Comparison Screen
**Data**: [database/schema.md](database/schema.md) → `player_machine_stats`

---

## By Role

### For Database Developers
1. [database/schema.md](database/schema.md) - Schema design
2. [database/indexes.md](database/indexes.md) - Index strategy
3. [data-pipeline/etl-process.md](data-pipeline/etl-process.md) - Data loading

### For Backend Developers
1. [api/endpoints.md](api/endpoints.md) - API specification
2. [api/response-formats.md](api/response-formats.md) - Response structure
3. [database/sample-queries.sql](database/sample-queries.sql) - Query examples

### For Frontend Developers
1. [frontend/ui-design.md](frontend/ui-design.md) - Screen designs
2. [frontend/components.md](frontend/components.md) - Component library
3. [api/endpoints.md](api/endpoints.md) - API integration

### For DevOps/Deployment
1. [deployment/infrastructure.md](deployment/infrastructure.md) - Hosting setup
2. [deployment/ci-cd.md](deployment/ci-cd.md) - Deployment pipeline
3. [deployment/monitoring.md](deployment/monitoring.md) - Monitoring

---

## Reference Documents (Existing)

These documents already exist in the parent project and contain important context:

| Document | Location | Purpose |
|----------|----------|---------|
| MNP Data Structure Reference | `../MNP_Data_Structure_Reference.md` | Match JSON structure |
| MNP Match Data Analysis Guide | `../MNP_Match_Data_Analysis_Guide.md` | Analytical guidance |
| Machine Variations | `../machine_variations.json` | Machine name mappings |
| Existing Reports | `../reports/generators/` | Current analysis scripts |

---

## Document Status

| Status | Meaning |
|--------|---------|
| ✅ Complete | Design complete, ready for implementation |
| 🚧 In Progress | Being written |
| 📝 Planned | On roadmap, not started |
| ❌ Not Planned | Not in current scope |

### Current Status

| Document | Status |
|----------|--------|
| README.md | ✅ Complete |
| IMPLEMENTATION_ROADMAP.md | ✅ Complete |
| database/schema.md | ✅ Complete |
| database/indexes.md | 📝 Planned |
| database/sample-queries.sql | 📝 Planned |
| database/migration-plan.md | 📝 Planned |
| api/endpoints.md | ✅ Complete |
| api/response-formats.md | 📝 Planned |
| api/error-handling.md | 📝 Planned |
| api/authentication.md | 📝 Planned (Phase 2) |
| frontend/ui-design.md | ✅ Complete |
| frontend/components.md | 📝 Planned |
| frontend/state-management.md | 📝 Planned |
| frontend/pwa-strategy.md | 📝 Planned |
| data-pipeline/etl-process.md | ✅ Complete |
| data-pipeline/data-quality.md | 📝 Planned |
| data-pipeline/percentile-calculation.md | 📝 Planned |
| deployment/infrastructure.md | 📝 Planned |
| deployment/ci-cd.md | 📝 Planned |
| deployment/monitoring.md | 📝 Planned |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-01-23 | Initial documentation structure created |
| 0.2.0 | TBD | Database implementation files added |
| 0.3.0 | TBD | API implementation files added |
| 0.4.0 | TBD | Frontend implementation files added |
| 1.0.0 | TBD | MVP launch documentation complete |

---

## Contributing to Documentation

When adding new documentation:

1. **Add to appropriate directory**: database/, api/, frontend/, data-pipeline/, or deployment/
2. **Update this INDEX.md**: Add entry in relevant sections
3. **Follow markdown format**: Use headers, code blocks, tables for clarity
4. **Include examples**: Show, don't just tell
5. **Update status**: Mark as complete when ready for use

---

## Questions or Issues?

- **Design questions**: Check relevant doc, ask in design review
- **Implementation questions**: Check code comments, ask in PR
- **Documentation gaps**: File issue or add TODO section
- **Clarifications needed**: Comment inline or create discussion

---

**Last Updated**: 2025-01-23
**Maintained By**: JJC
**Current Phase**: Planning & Documentation (Pre-implementation)
