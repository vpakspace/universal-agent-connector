#!/bin/bash
# Setup script for all demo projects
# Creates databases and loads sample data

set -e

echo "=========================================="
echo "Setting up all demo projects"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if PostgreSQL is available
if ! command -v psql &> /dev/null; then
    echo "Error: PostgreSQL (psql) not found. Please install PostgreSQL first."
    exit 1
fi

# Get database credentials
read -p "PostgreSQL username [postgres]: " DB_USER
DB_USER=${DB_USER:-postgres}

read -sp "PostgreSQL password: " DB_PASSWORD
echo ""

read -p "PostgreSQL host [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "PostgreSQL port [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}

export PGPASSWORD=$DB_PASSWORD

# Function to setup a demo
setup_demo() {
    local demo_name=$1
    local db_name=$2
    local setup_file=$3
    
    echo -e "${BLUE}Setting up $demo_name...${NC}"
    
    # Create database
    if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $db_name; then
        echo "  Database $db_name already exists. Dropping..."
        psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "DROP DATABASE IF EXISTS $db_name;"
    fi
    
    echo "  Creating database $db_name..."
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $db_name;"
    
    echo "  Loading sample data..."
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $db_name -f $setup_file
    
    echo -e "${GREEN}✓ $demo_name setup complete!${NC}"
    echo ""
}

# Setup each demo
setup_demo "E-Commerce Demo" "ecommerce_demo" "demos/ecommerce/setup.sql"
setup_demo "SaaS Metrics Demo" "saas_demo" "demos/saas/setup.sql"
setup_demo "Financial Reporting Demo" "financial_demo" "demos/financial/setup.sql"

echo "=========================================="
echo -e "${GREEN}All demos setup complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start AI Agent Connector: python main.py"
echo "2. Visit http://localhost:5000/dashboard"
echo "3. Follow the demo walkthroughs:"
echo "   - demos/ecommerce/WALKTHROUGH.md"
echo "   - demos/saas/WALKTHROUGH.md"
echo "   - demos/financial/WALKTHROUGH.md"
echo ""

unset PGPASSWORD

