#!/bin/bash
#
# Weekly MNP data update
#
# Runs the full incremental weekly update workflow:
#   1. Pull latest match data from archive (git submodule)
#   2. Load new matches into local database
#   3. Recalculate weekly aggregates (team picks, match points)
#   4. Sync to production database and refresh frontend
#
# Usage:
#   ./scripts/run_weekly_update.sh
#
# Prerequisites:
#   - conda mnp environment is active
#   - DATABASE_PUBLIC_URL is set in .env
#   - Run from the repo root

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SEASON=23
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}MNP Weekly Update - Season $SEASON${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Step 1: Update submodule
echo -e "${YELLOW}Step 1/4: Pulling latest match data...${NC}"
cd "$REPO_ROOT"
git submodule update --remote mnp-data-archive
echo -e "${GREEN}✓${NC} Match data archive updated"
echo ""

# Step 2: Load new match data
echo -e "${YELLOW}Step 2/4: Loading season $SEASON data...${NC}"
python etl/update_season.py --season $SEASON --skip-aggregations
echo -e "${GREEN}✓${NC} Season data loaded"
echo ""

# Step 3: Calculate weekly aggregates
echo -e "${YELLOW}Step 3/4: Calculating weekly aggregates...${NC}"
python etl/calculate_team_machine_picks.py --season $SEASON
echo -e "${GREEN}✓${NC} Team machine picks updated"

python etl/calculate_match_points.py --season $SEASON
echo -e "${GREEN}✓${NC} Match points updated"
echo ""

# Step 4: Sync to production
echo -e "${YELLOW}Step 4/4: Syncing to production...${NC}"
"$SCRIPT_DIR/sync_to_production.sh"
