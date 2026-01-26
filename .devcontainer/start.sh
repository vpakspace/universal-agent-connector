#!/bin/bash
# Start script for GitHub Codespaces / VS Code Dev Containers
# Runs when container starts

set -e

echo "=========================================="
echo "🚀 Starting AI Agent Connector"
echo "=========================================="
echo ""

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f .env ]; then
  export $(cat .env | grep -v '^#' | xargs)
fi

# Set defaults
export FLASK_ENV=${FLASK_ENV:-development}
export PORT=${PORT:-5000}
export HOST=${HOST:-0.0.0.0}

# Generate encryption key if not set
if [ -z "$ENCRYPTION_KEY" ]; then
  export ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
fi

# Display welcome message
cat << 'EOF'

╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🎉 Welcome to AI Agent Connector Playground! 🎉         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

Your environment is ready! Here's what's available:

✅ Python environment with all dependencies
✅ PostgreSQL database with demo data
✅ All 3 demo databases loaded:
   • ecommerce_demo (10 customers, 20 products, 20 orders)
   • saas_demo (18 users, 4 plans, 18 subscriptions)
   • financial_demo (5 accounts, 25 transactions)

📚 Quick Links:
   • Dashboard: http://localhost:5000/dashboard
   • API Docs: http://localhost:5000/api/api-docs
   • GraphQL Playground: http://localhost:5000/graphql/playground

🎯 Next Steps:
   1. Open PLAYGROUND_TUTORIAL.md for guided tutorial
   2. Visit the dashboard to register an agent
   3. Try natural language queries with demo data

🚀 Starting server...

EOF

# Start the application
python main.py

