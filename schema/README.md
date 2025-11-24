# MNP Analyzer Database Setup

## Overview

This directory contains SQL migration files for creating the MNP Analyzer PostgreSQL database schema.

## Prerequisites

- PostgreSQL 15+ installed
- `psql` command-line tool available
- Sufficient permissions to create databases

## Installation

### macOS

```bash
# Install PostgreSQL using Homebrew
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Verify installation
psql --version
```

### Linux (Ubuntu/Debian)

```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Update and install
sudo apt-get update
sudo apt-get install postgresql-15

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Verify installation
psql --version
```

### Windows

Download and install from: https://www.postgresql.org/download/windows/

## Database Setup

### 1. Create Database and User

```bash
# Connect to PostgreSQL as superuser
psql postgres

# Inside psql, run:
CREATE DATABASE mnp_analyzer;
CREATE USER mnp_user WITH ENCRYPTED PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE mnp_analyzer TO mnp_user;

# Exit psql
\q
```

### 2. Run Migrations

Execute the migration files in order:

```bash
# Connect to the database
psql -U mnp_user -d mnp_analyzer

# Or if using default user:
psql mnp_analyzer

# Run migrations in order:
\i migrations/001_initial_schema.sql
\i migrations/002_indexes.sql
\i migrations/003_constraints.sql

# Verify schema
\dt  # List tables
\di  # List indexes
```

### Alternative: One-Command Setup

```bash
# From the schema directory:
psql mnp_analyzer < migrations/001_initial_schema.sql
psql mnp_analyzer < migrations/002_indexes.sql
psql mnp_analyzer < migrations/003_constraints.sql
```

## Verification

After running migrations, verify the schema:

```sql
-- Connect to database
psql mnp_analyzer

-- Check tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Check schema version
SELECT * FROM schema_version;

-- Count tables (should be 16)
SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';

-- Check constraints
SELECT
    table_name,
    constraint_type,
    COUNT(*) as count
FROM information_schema.table_constraints
WHERE table_schema = 'public'
GROUP BY table_name, constraint_type
ORDER BY table_name;
```

Expected output:
- 16 tables total
- Multiple foreign key constraints
- Multiple check constraints
- 30+ indexes

## Migration Files

| File | Description | Tables Created |
|------|-------------|----------------|
| `001_initial_schema.sql` | Core tables and aggregate tables | 16 tables |
| `002_indexes.sql` | Strategic indexes for performance | 30+ indexes |
| `003_constraints.sql` | Foreign keys and check constraints | 20+ constraints |

## Table Summary

### Core Tables (9)
- `players` - Player identity and ratings
- `teams` - Team information by season
- `venues` - Venue definitions
- `machines` - Machine catalog
- `machine_aliases` - Machine name variations
- `venue_machines` - Machine locations by season
- `matches` - Match metadata
- `games` - Individual game records
- `scores` - Player scores with context

### Aggregate Tables (3)
- `score_percentiles` - Pre-calculated percentile thresholds
- `player_machine_stats` - Player performance by machine
- `team_machine_picks` - Team machine selection patterns

### Utility Tables (1)
- `schema_version` - Schema version tracking

## Connection String

For application use:

```
postgresql://mnp_user:your_password@localhost:5432/mnp_analyzer
```

## Environment Variables

Create a `.env` file in your project root:

```bash
DATABASE_URL=postgresql://mnp_user:your_password@localhost:5432/mnp_analyzer
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mnp_analyzer
DB_USER=mnp_user
DB_PASSWORD=your_password
```

**IMPORTANT**: Add `.env` to your `.gitignore` to avoid committing credentials!

## Common Issues

### Issue: "role does not exist"
**Solution**: Create the user first using `CREATE USER` command above

### Issue: "database does not exist"
**Solution**: Create the database first using `CREATE DATABASE` command above

### Issue: "permission denied"
**Solution**: Grant privileges using `GRANT ALL PRIVILEGES` command above

### Issue: "psql: command not found"
**Solution**: PostgreSQL not installed or not in PATH. Reinstall and add to PATH.

### Issue: Can't connect to PostgreSQL
**Solution**: Check if PostgreSQL is running:
```bash
# macOS
brew services list

# Linux
sudo systemctl status postgresql

# Windows
# Check Services app for PostgreSQL service
```

## Next Steps

After database setup:
1. ✅ Database schema created
2. ⏭️ Build ETL pipeline to load data
3. ⏭️ Test with sample match data
4. ⏭️ Set up FastAPI backend

See [mnp-app-docs/IMPLEMENTATION_ROADMAP.md](../mnp-app-docs/IMPLEMENTATION_ROADMAP.md) for next steps.

## Maintenance

### Backup Database
```bash
pg_dump mnp_analyzer > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
psql mnp_analyzer < backup_20250123.sql
```

### Reset Database
```bash
# Drop and recreate (WARNING: Destroys all data!)
psql postgres -c "DROP DATABASE IF EXISTS mnp_analyzer;"
psql postgres -c "CREATE DATABASE mnp_analyzer;"

# Then re-run migrations
```

## Support

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- MNP Analyzer Docs: [../mnp-app-docs/](../mnp-app-docs/)
- Database Schema Design: [../mnp-app-docs/database/schema.md](../mnp-app-docs/database/schema.md)

---

**Schema Version**: 1.0.0
**Last Updated**: 2025-01-23
**Status**: Ready for use
