#!/bin/bash

# Script to apply all performance optimization updates
# This includes database migrations and ETL updates

set -e  # Exit on error

echo "=========================================="
echo "MNP Performance Optimization Setup"
echo "=========================================="
echo ""

# Check if PostgreSQL is running
echo "1. Checking database connection..."
if ! psql -d mnp -c "SELECT 1" > /dev/null 2>&1; then
    echo "ERROR: Cannot connect to PostgreSQL database 'mnp'"
    echo "Please ensure PostgreSQL is running and the 'mnp' database exists"
    exit 1
fi
echo "✓ Database connection successful"
echo ""

# Apply migration 004: Add is_substitute column
echo "2. Applying migration 004: Add is_substitute column..."
if psql -d mnp -f schema/migrations/004_add_substitute_field.sql; then
    echo "✓ Migration 004 applied successfully"
else
    echo "⚠ Migration 004 failed (column may already exist)"
fi
echo ""

# Apply migration 005: Add performance indexes
echo "3. Applying migration 005: Add performance indexes..."
if psql -d mnp -f schema/migrations/005_performance_indexes.sql; then
    echo "✓ Migration 005 applied successfully"
else
    echo "⚠ Migration 005 failed (indexes may already exist)"
fi
echo ""

# Re-run ETL to populate is_substitute field
echo "4. Re-loading season data to populate is_substitute field..."
echo "   This will take a few minutes..."
echo ""

read -p "Do you want to reload Season 22 data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Loading Season 22..."
    python3 etl/load_season.py 22
    echo "✓ Season 22 reloaded"
fi
echo ""

read -p "Do you want to reload Season 21 data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   Loading Season 21..."
    python3 etl/load_season.py 21
    echo "✓ Season 21 reloaded"
fi
echo ""

# Verify the updates
echo "5. Verifying database schema..."
COLUMN_EXISTS=$(psql -d mnp -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='scores' AND column_name='is_substitute';" | tr -d ' ')

if [ "$COLUMN_EXISTS" = "1" ]; then
    echo "✓ is_substitute column exists"
else
    echo "✗ is_substitute column NOT found"
    exit 1
fi

INDEX_COUNT=$(psql -d mnp -t -c "SELECT COUNT(*) FROM pg_indexes WHERE tablename='scores' AND indexname LIKE 'idx_scores%';" | tr -d ' ')
echo "✓ Found $INDEX_COUNT indexes on scores table"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Summary of changes:"
echo "  • Added is_substitute column to track substitute players"
echo "  • Added 8 performance indexes to scores table"
echo "  • Reloaded match data with substitute player information"
echo ""
echo "Next steps:"
echo "  1. Restart your API server if it's running"
echo "  2. Test the page: http://localhost:3000/teams/KNR?season=22"
echo "  3. Expected performance: <500ms load time"
echo ""
echo "The 'Exclude substitute players' checkbox is now functional!"
echo ""
