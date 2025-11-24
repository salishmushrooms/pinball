#!/bin/bash

# MNP Analyzer Database Setup Script
# This script automates the database creation and migration process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DB_NAME="mnp_analyzer"
DB_USER="mnp_user"
DB_PASSWORD="${MNP_DB_PASSWORD:-changeme}"  # Override with environment variable

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}MNP Analyzer Database Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: PostgreSQL is not installed${NC}"
    echo ""
    echo "Install PostgreSQL:"
    echo "  macOS:  brew install postgresql@15"
    echo "  Linux:  sudo apt-get install postgresql-15"
    echo "  Windows: https://www.postgresql.org/download/windows/"
    exit 1
fi

echo -e "${GREEN}✓${NC} PostgreSQL found: $(psql --version)"
echo ""

# Check if PostgreSQL is running
if ! pg_isready &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} PostgreSQL is not running"
    echo "Starting PostgreSQL..."

    # Try to start PostgreSQL based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew services start postgresql@15 || brew services start postgresql
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo systemctl start postgresql
    fi

    sleep 2

    if ! pg_isready &> /dev/null; then
        echo -e "${RED}Error: Could not start PostgreSQL${NC}"
        echo "Please start PostgreSQL manually and try again"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} PostgreSQL is running"
echo ""

# Create database and user
echo "Creating database and user..."
echo ""

# Check if database exists
if psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${YELLOW}⚠${NC} Database '$DB_NAME' already exists"
    read -p "Do you want to drop and recreate it? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy]es$ ]]; then
        psql postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Dropped existing database"
    else
        echo "Keeping existing database"
    fi
fi

# Create database if it doesn't exist
if ! psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    psql postgres -c "CREATE DATABASE $DB_NAME;"
    echo -e "${GREEN}✓${NC} Created database '$DB_NAME'"
else
    echo -e "${GREEN}✓${NC} Database '$DB_NAME' exists"
fi

# Create user if it doesn't exist
if ! psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    psql postgres -c "CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';"
    echo -e "${GREEN}✓${NC} Created user '$DB_USER'"
else
    echo -e "${GREEN}✓${NC} User '$DB_USER' exists"
fi

# Grant privileges
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
echo -e "${GREEN}✓${NC} Granted privileges"
echo ""

# Run migrations
echo "Running migrations..."
echo ""

MIGRATION_DIR="$(dirname "$0")/migrations"

if [ ! -d "$MIGRATION_DIR" ]; then
    echo -e "${RED}Error: Migrations directory not found: $MIGRATION_DIR${NC}"
    exit 1
fi

# Run each migration file in order
for migration in "$MIGRATION_DIR"/*.sql; do
    if [ -f "$migration" ]; then
        filename=$(basename "$migration")
        echo "Running $filename..."
        psql "$DB_NAME" -f "$migration" --quiet
        echo -e "${GREEN}✓${NC} $filename completed"
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Verify setup
echo "Verifying setup..."
TABLE_COUNT=$(psql "$DB_NAME" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
INDEX_COUNT=$(psql "$DB_NAME" -tAc "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';")

echo -e "${GREEN}✓${NC} Tables created: $TABLE_COUNT (expected: 16)"
echo -e "${GREEN}✓${NC} Indexes created: $INDEX_COUNT"
echo ""

# Display connection info
echo "Connection Information:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Database:  $DB_NAME"
echo "User:      $DB_USER"
echo "Password:  $DB_PASSWORD"
echo "Host:      localhost"
echo "Port:      5432"
echo ""
echo "Connection String:"
echo "postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create .env file
ENV_FILE="../.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."
    cat > "$ENV_FILE" << EOF
# MNP Analyzer Database Configuration
# Generated on $(date)

DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
DB_HOST=localhost
DB_PORT=5432
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
EOF
    echo -e "${GREEN}✓${NC} Created .env file at $ENV_FILE"
    echo -e "${YELLOW}⚠${NC} Remember to add .env to your .gitignore!"
else
    echo -e "${YELLOW}⚠${NC} .env file already exists, not overwriting"
fi

echo ""
echo "Next Steps:"
echo "1. Test connection: psql $DB_NAME"
echo "2. Build ETL pipeline to load data"
echo "3. See: mnp-app-docs/IMPLEMENTATION_ROADMAP.md (Week 1, Day 3-5)"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
