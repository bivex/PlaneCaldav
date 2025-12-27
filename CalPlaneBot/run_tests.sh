#!/bin/bash
# Test runner script for CalPlaneBot

set -e

echo "🧪 CalPlaneBot Test Suite"
echo "=========================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found. Installing test dependencies...${NC}"
    pip install -r tests/requirements-test.txt
fi

# Parse arguments
FAST_MODE=false
COVERAGE=false
PARALLEL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            FAST_MODE=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

if [ "$FAST_MODE" = true ]; then
    echo -e "${YELLOW}⚡ Running in FAST mode (unit tests only)${NC}"
    PYTEST_CMD="$PYTEST_CMD -m 'unit and not slow'"
fi

if [ "$COVERAGE" = true ]; then
    echo -e "${YELLOW}📊 Coverage reporting enabled${NC}"
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=html --cov-report=term"
fi

if [ "$PARALLEL" = true ]; then
    echo -e "${YELLOW}🚀 Parallel execution enabled${NC}"
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

# Add any additional arguments
if [ $# -gt 0 ]; then
    PYTEST_CMD="$PYTEST_CMD $@"
fi

echo ""
echo "Running: $PYTEST_CMD"
echo ""

# Run tests
if $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
