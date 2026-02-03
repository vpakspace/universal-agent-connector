#!/bin/bash
#
# Load Testing Script for Universal Agent Connector
#
# Usage:
#   ./run_load_test.sh [mode] [options]
#
# Modes:
#   quick     - Quick smoke test (10 users, 30s)
#   standard  - Standard load test (50 users, 2min)
#   stress    - Stress test (200 users, 5min)
#   endurance - Endurance test (100 users, 30min)
#   custom    - Custom parameters (requires options)
#
# Options:
#   -u, --users       Number of users (default: 50)
#   -r, --spawn-rate  Users per second (default: 10)
#   -t, --time        Test duration (default: 2m)
#   -h, --host        Target host (default: http://localhost:5000)
#   --web             Enable web UI instead of headless mode
#
# Examples:
#   ./run_load_test.sh quick
#   ./run_load_test.sh standard
#   ./run_load_test.sh custom -u 100 -r 20 -t 5m
#   ./run_load_test.sh standard --web
#

set -e

# Default values
HOST="http://localhost:5000"
USERS=50
SPAWN_RATE=10
DURATION="2m"
HEADLESS=true
RESULTS_DIR="results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Universal Agent Connector Load Test${NC}"
    echo -e "${GREEN}========================================${NC}"
}

print_usage() {
    echo "Usage: $0 [mode] [options]"
    echo ""
    echo "Modes:"
    echo "  quick     - Quick smoke test (10 users, 30s)"
    echo "  standard  - Standard load test (50 users, 2min)"
    echo "  stress    - Stress test (200 users, 5min)"
    echo "  endurance - Endurance test (100 users, 30min)"
    echo "  custom    - Custom parameters"
    echo ""
    echo "Options:"
    echo "  -u, --users       Number of users"
    echo "  -r, --spawn-rate  Users spawned per second"
    echo "  -t, --time        Test duration (e.g., 30s, 2m, 1h)"
    echo "  -h, --host        Target host URL"
    echo "  --web             Enable web UI mode"
    echo ""
    echo "Examples:"
    echo "  $0 quick"
    echo "  $0 standard"
    echo "  $0 custom -u 100 -r 20 -t 5m"
}

# Check if locust is installed
check_locust() {
    if ! command -v locust &> /dev/null; then
        echo -e "${RED}Error: locust is not installed${NC}"
        echo "Install with: pip install locust"
        exit 1
    fi
}

# Check if server is running
check_server() {
    echo -n "Checking server at ${HOST}... "
    if curl -s -o /dev/null -w "%{http_code}" "${HOST}/health" 2>/dev/null | grep -q "200\|404"; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}Warning: Server may not be running${NC}"
        echo "Make sure to start the server with: python main_simple.py"
    fi
}

# Set mode presets
set_mode() {
    case $1 in
        quick)
            USERS=10
            SPAWN_RATE=5
            DURATION="30s"
            ;;
        standard)
            USERS=50
            SPAWN_RATE=10
            DURATION="2m"
            ;;
        stress)
            USERS=200
            SPAWN_RATE=20
            DURATION="5m"
            ;;
        endurance)
            USERS=100
            SPAWN_RATE=10
            DURATION="30m"
            ;;
        custom)
            # Use defaults or command line args
            ;;
        *)
            echo -e "${RED}Unknown mode: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
}

# Parse arguments
MODE="standard"
while [[ $# -gt 0 ]]; do
    case $1 in
        quick|standard|stress|endurance|custom)
            MODE=$1
            set_mode $1
            shift
            ;;
        -u|--users)
            USERS=$2
            shift 2
            ;;
        -r|--spawn-rate)
            SPAWN_RATE=$2
            shift 2
            ;;
        -t|--time)
            DURATION=$2
            shift 2
            ;;
        -h|--host)
            HOST=$2
            shift 2
            ;;
        --web)
            HEADLESS=false
            shift
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Main execution
print_header
check_locust
check_server

echo ""
echo -e "${YELLOW}Test Configuration:${NC}"
echo "  Mode:       ${MODE}"
echo "  Host:       ${HOST}"
echo "  Users:      ${USERS}"
echo "  Spawn Rate: ${SPAWN_RATE}/s"
echo "  Duration:   ${DURATION}"
echo "  Headless:   ${HEADLESS}"
echo ""

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Build locust command
LOCUST_CMD="locust -f locustfile.py --host=${HOST}"

if [ "$HEADLESS" = true ]; then
    LOCUST_CMD+=" --headless"
    LOCUST_CMD+=" -u ${USERS}"
    LOCUST_CMD+=" -r ${SPAWN_RATE}"
    LOCUST_CMD+=" -t ${DURATION}"
    LOCUST_CMD+=" --csv=${RESULTS_DIR}/load_test_${TIMESTAMP}"
    LOCUST_CMD+=" --html=${RESULTS_DIR}/load_test_${TIMESTAMP}.html"

    echo -e "${GREEN}Starting headless load test...${NC}"
    echo "Results will be saved to ${RESULTS_DIR}/"
else
    echo -e "${GREEN}Starting Locust web UI...${NC}"
    echo "Open http://localhost:8089 in your browser"
    echo "Press Ctrl+C to stop"
fi

echo ""
echo "Command: ${LOCUST_CMD}"
echo ""

# Run locust
eval ${LOCUST_CMD}

# Print results location
if [ "$HEADLESS" = true ]; then
    echo ""
    echo -e "${GREEN}Load test complete!${NC}"
    echo ""
    echo "Results saved to:"
    echo "  - ${RESULTS_DIR}/load_test_${TIMESTAMP}_stats.csv"
    echo "  - ${RESULTS_DIR}/load_test_${TIMESTAMP}_stats_history.csv"
    echo "  - ${RESULTS_DIR}/load_test_${TIMESTAMP}_failures.csv"
    echo "  - ${RESULTS_DIR}/load_test_${TIMESTAMP}.html"
fi
