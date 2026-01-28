#!/bin/bash
# Universal Agent Connector - Streamlit UI Launcher

echo "=========================================="
echo "Universal Agent Connector - Streamlit UI"
echo "=========================================="
echo ""

# Check if PostgreSQL container is running
if docker ps | grep -q "uac-postgres"; then
    echo "✅ PostgreSQL container is running"
else
    echo "⚠️  PostgreSQL container not running"
    echo "   Starting with: docker-compose up -d"
    docker-compose up -d
    sleep 3
fi

# Check if Flask API is running
if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "✅ Flask API is running"
else
    echo "⚠️  Flask API not running"
    echo "   Please start it in another terminal with:"
    echo "   python main_simple.py"
    echo ""
    echo "   Waiting for API..."

    # Wait for API to be available (max 30 seconds)
    for i in {1..30}; do
        if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
            echo "✅ Flask API started"
            break
        fi
        sleep 1
    done
fi

echo ""
echo "Starting Streamlit UI..."
echo "Open in browser: http://localhost:8501"
echo ""

# Run Streamlit
streamlit run streamlit_app.py --server.port 8501
