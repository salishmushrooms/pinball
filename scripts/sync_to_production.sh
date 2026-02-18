#!/bin/bash
#
# Sync local MNP database to Railway production
#
# This script:
# 1. Exports local database to temporary SQL file
# 2. Truncates production tables
# 3. Imports data to production
# 4. Verifies the import
# 5. Refreshes frontend static pages
# 6. Cleans up temporary files
#
# Usage:
#   ./scripts/sync_to_production.sh              # Sync and revalidate
#   ./scripts/sync_to_production.sh --skip-revalidation  # Sync only
#
# Prerequisites:
#   - Local database is up-to-date with latest data
#   - DATABASE_PUBLIC_URL is set in .env file
#   - REVALIDATION_SECRET is set in .env file (optional, for step 5)
#   - psql is installed and available

set -e  # Exit on error

# Parse arguments
SKIP_REVALIDATION=false
if [ "$1" = "--skip-revalidation" ]; then
    SKIP_REVALIDATION=true
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Temp file for SQL export
TEMP_SQL="/tmp/mnp_data_$(date +%Y%m%d_%H%M%S).sql"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}MNP Production Database Sync${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check for .env file
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: .env file not found${NC}"
    echo "Make sure you're running this from the repo root"
    exit 1
fi

# Step 2: Read DATABASE_PUBLIC_URL from .env
echo -e "${YELLOW}Reading production credentials from .env...${NC}"
source .env

if [ -z "$DATABASE_PUBLIC_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_PUBLIC_URL not found in .env${NC}"
    exit 1
fi

# Parse connection string: postgresql://user:pass@host:port/database
# Extract components using parameter expansion
CONN_STRING="${DATABASE_PUBLIC_URL#postgresql://}"  # Remove protocol
USER_PASS="${CONN_STRING%%@*}"                      # Get user:pass
HOST_PORT_DB="${CONN_STRING#*@}"                    # Get host:port/db

DB_USER="${USER_PASS%%:*}"                          # Extract user
DB_PASS="${USER_PASS#*:}"                           # Extract password

HOST_PORT="${HOST_PORT_DB%%/*}"                     # Get host:port
DB_NAME="${HOST_PORT_DB#*/}"                        # Extract database

DB_HOST="${HOST_PORT%%:*}"                          # Extract host
DB_PORT="${HOST_PORT#*:}"                           # Extract port

echo -e "${GREEN}✓${NC} Connected to: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo ""

# Step 3: Export local database
echo -e "${YELLOW}Step 1/5: Exporting local database...${NC}"
pg_dump -h localhost -U mnp_user -d mnp_analyzer \
    --data-only --no-owner --no-acl > "$TEMP_SQL"

FILE_SIZE=$(du -h "$TEMP_SQL" | cut -f1)
echo -e "${GREEN}✓${NC} Exported to ${TEMP_SQL} (${FILE_SIZE})"
echo ""

# Step 4: Truncate production tables
echo -e "${YELLOW}Step 2/5: Truncating production tables...${NC}"
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
TRUNCATE TABLE scores, games, matches, player_machine_stats,
  score_percentiles, team_machine_picks, venue_machines,
  pre_calculated_matchups, players, teams, venues,
  machine_aliases, machines, schema_version
RESTART IDENTITY CASCADE;" > /dev/null

echo -e "${GREEN}✓${NC} Production tables cleared"
echo ""

# Step 5: Import data to production
echo -e "${YELLOW}Step 3/5: Importing data to production...${NC}"
echo -e "  ${BLUE}(This may take 1-2 minutes for large datasets)${NC}"

# Capture output to check for errors
IMPORT_OUTPUT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$TEMP_SQL" 2>&1)
IMPORT_STATUS=$?

if [ $IMPORT_STATUS -ne 0 ]; then
    # Check if it's just duplicate key errors (which are OK)
    if echo "$IMPORT_OUTPUT" | grep -q "duplicate key"; then
        echo -e "${YELLOW}⚠${NC}  Import completed with duplicate key warnings (this is OK)"
    else
        echo -e "${RED}ERROR: Import failed${NC}"
        echo "$IMPORT_OUTPUT"
        rm -f "$TEMP_SQL"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} Data imported successfully"
fi
echo ""

# Step 6: Verify import
echo -e "${YELLOW}Step 4/5: Verifying import...${NC}"
VERIFY_OUTPUT=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "
SELECT
    'Matches:    ' || LPAD(COUNT(*)::text, 6, ' ') FROM matches
UNION ALL SELECT
    'Scores:     ' || LPAD(COUNT(*)::text, 6, ' ') FROM scores
UNION ALL SELECT
    'Games:      ' || LPAD(COUNT(*)::text, 6, ' ') FROM games
UNION ALL SELECT
    'Players:    ' || LPAD(COUNT(*)::text, 6, ' ') FROM players
UNION ALL SELECT
    'Machines:   ' || LPAD(COUNT(*)::text, 6, ' ') FROM machines;")

echo -e "${GREEN}Production Database Counts:${NC}"
echo "$VERIFY_OUTPUT"
echo ""

# Step 7: Revalidate frontend static pages
if [ "$SKIP_REVALIDATION" = false ]; then
    echo -e "${YELLOW}Step 5/5: Refreshing frontend static pages...${NC}"

    if [ -z "$REVALIDATION_SECRET" ]; then
        echo -e "${YELLOW}⚠${NC}  REVALIDATION_SECRET not found in .env, skipping..."
    else
        REVALIDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
            "https://pinball.salishmushrooms.com/api/revalidate?secret=$REVALIDATION_SECRET")

        HTTP_CODE=$(echo "$REVALIDATE_RESPONSE" | tail -n1)

        if [ "$HTTP_CODE" = "200" ]; then
            echo -e "${GREEN}✓${NC} Static pages refreshed successfully"
        else
            echo -e "${YELLOW}⚠${NC}  Revalidation returned HTTP ${HTTP_CODE} (may not be deployed yet)"
        fi
    fi
    echo ""
else
    echo -e "${BLUE}Step 5/5: Skipping frontend revalidation (--skip-revalidation flag)${NC}"
    echo ""
fi

# Step 8: Cleanup
echo -e "${YELLOW}Cleaning up temporary files...${NC}"
rm -f "$TEMP_SQL"
echo -e "${GREEN}✓${NC} Temporary files removed"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Sync Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Verify data at: ${BLUE}https://pinball.salishmushrooms.com${NC}"
if [ "$SKIP_REVALIDATION" = true ]; then
    echo -e "  2. Refresh static pages:"
    echo -e "     ${BLUE}curl -X POST \"https://pinball.salishmushrooms.com/api/revalidate?secret=\$REVALIDATION_SECRET\"${NC}"
fi
echo ""
