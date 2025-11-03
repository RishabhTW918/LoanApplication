#!/bin/bash
# Test runner script for LoanApplication services
# Run this from the LoanApplication root directory

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Running LoanApplication Tests${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Activate virtual environment if it exists
if [ -d "../.venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source ../.venv/bin/activate
fi

# Function to run tests for a service
run_service_tests() {
    local service=$1
    echo -e "\n${BLUE}Testing $service Service...${NC}"
    cd services/$service
    python3 -m pytest tests/ -v --tb=short
    cd ../..
}

# Check if a specific service was requested
if [ -n "$1" ]; then
    case $1 in
        api|credit|decision)
            run_service_tests $1
            ;;
        *)
            echo -e "${RED}Invalid service: $1${NC}"
            echo "Usage: $0 [api|credit|decision]"
            echo "  or just: $0  (to run all tests)"
            exit 1
            ;;
    esac
else
    # Run all tests
    echo -e "${GREEN}Running all tests...${NC}"

    run_service_tests "decision"
    run_service_tests "credit"
    run_service_tests "api"

    echo -e "\n${GREEN}================================${NC}"
    echo -e "${GREEN}All tests completed!${NC}"
    echo -e "${GREEN}================================${NC}"
fi
