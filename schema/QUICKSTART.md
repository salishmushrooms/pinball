# Database Setup - Quick Start

## Step 1: Install PostgreSQL

```bash
# Install PostgreSQL 15
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Verify installation
psql --version
```

This will take a few minutes to download and install.

## Step 2: Run Automated Setup

Once PostgreSQL is installed, run the automated setup script:

```bash
cd schema
./setup_database.sh
```

This script will:
- ✅ Create the `mnp_analyzer` database
- ✅ Create the `mnp_user` user
- ✅ Run all migrations (tables, indexes, constraints)
- ✅ Verify the setup
- ✅ Create a `.env` file with connection details

## Step 3: Verify Installation

```bash
# Connect to the database
psql mnp_analyzer

# Inside psql, check tables:
\dt

# Check schema version:
SELECT * FROM schema_version;

# Exit:
\q
```

You should see 16 tables listed.

## Manual Setup (Alternative)

If you prefer to do it manually:

```bash
# 1. Create database and user
psql postgres

CREATE DATABASE mnp_analyzer;
CREATE USER mnp_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE mnp_analyzer TO mnp_user;
\q

# 2. Run migrations
psql mnp_analyzer < migrations/001_initial_schema.sql
psql mnp_analyzer < migrations/002_indexes.sql
psql mnp_analyzer < migrations/003_constraints.sql
```

## Troubleshooting

**PostgreSQL won't start?**
```bash
# Check if it's running
brew services list

# Restart it
brew services restart postgresql@15
```

**Can't connect?**
```bash
# Check logs
tail -f /usr/local/var/log/postgresql@15.log
```

**Permission denied?**
```bash
# Make sure you have privileges
psql postgres -c "ALTER USER $USER WITH SUPERUSER;"
```

## Next Steps

After database setup:
1. ✅ Database ready
2. ⏭️ Build ETL pipeline (Week 1, Day 3-5)
3. ⏭️ Load Season 22 data

See: [../mnp-app-docs/IMPLEMENTATION_ROADMAP.md](../mnp-app-docs/IMPLEMENTATION_ROADMAP.md)

---

**Need help?** See [README.md](README.md) for detailed documentation.
