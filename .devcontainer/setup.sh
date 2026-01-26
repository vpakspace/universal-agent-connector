#!/bin/bash
# Setup script for GitHub Codespaces / VS Code Dev Containers
# Runs once when container is created

set -e

echo "=========================================="
echo "🚀 Setting up AI Agent Connector Playground"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Install PostgreSQL client
echo -e "${BLUE}Installing PostgreSQL client...${NC}"
sudo apt-get update
sudo apt-get install -y postgresql-client

# Create virtual environment
echo -e "${BLUE}Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Wait for PostgreSQL to be ready
echo -e "${BLUE}Waiting for PostgreSQL to be ready...${NC}"
until pg_isready -h localhost -p 5432 -U postgres; do
  echo "  Waiting for PostgreSQL..."
  sleep 2
done
echo -e "${GREEN}✓ PostgreSQL is ready!${NC}"

# Set PostgreSQL environment
export PGHOST=localhost
export PGPORT=5432
export PGUSER=postgres
export PGPASSWORD=postgres

# Create demo databases
echo -e "${BLUE}Creating demo databases...${NC}"
createdb ecommerce_demo 2>/dev/null || echo "  ecommerce_demo already exists"
createdb saas_demo 2>/dev/null || echo "  saas_demo already exists"
createdb financial_demo 2>/dev/null || echo "  financial_demo already exists"

# Load sample data
echo -e "${BLUE}Loading demo data...${NC}"
echo "  Loading e-commerce demo..."
psql -d ecommerce_demo -f demos/ecommerce/setup.sql > /dev/null 2>&1 || echo "    (already loaded)"

echo "  Loading SaaS demo..."
psql -d saas_demo -f demos/saas/setup.sql > /dev/null 2>&1 || echo "    (already loaded)"

echo "  Loading financial demo..."
psql -d financial_demo -f demos/financial/setup.sql > /dev/null 2>&1 || echo "    (already loaded)"

echo -e "${GREEN}✓ All demo databases loaded!${NC}"
echo ""

# Generate encryption key
if [ -z "$ENCRYPTION_KEY" ]; then
  echo -e "${BLUE}Generating encryption key...${NC}"
  export ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
  echo "  ENCRYPTION_KEY generated"
fi

# Create .env file
echo -e "${BLUE}Creating .env file...${NC}"
cat > .env << EOF
FLASK_ENV=development
PORT=5000
HOST=0.0.0.0
SECRET_KEY=dev-secret-key-change-in-production
ENCRYPTION_KEY=${ENCRYPTION_KEY}
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=postgres
EOF

echo -e "${GREEN}✓ Environment file created${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}✅ Setup complete!${NC}"
echo "=========================================="
echo ""
echo "Next: The server will start automatically."
echo "Check the 'Start Server' terminal tab."
echo ""

