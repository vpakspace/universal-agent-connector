#!/bin/bash
# Run Admin Dashboard
# Usage: ./run_admin.sh [port]

PORT=${1:-8502}

echo "Starting Admin Dashboard on port $PORT..."
echo "Open http://localhost:$PORT in your browser"
echo ""

streamlit run admin_dashboard.py --server.port=$PORT --server.address=0.0.0.0
