#!/bin/bash

# Quick Test Runner for Django Task List Application
# Simple version for everyday use

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
VENV_PATH=".venv"
PYTHON="$VENV_PATH/bin/python"
PYTEST="$VENV_PATH/bin/pytest"

echo -e "${BLUE}🧪 Django Task List - Quick Test Runner${NC}"
echo "========================================"

# Check virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run: python -m venv .venv${NC}"
    exit 1
fi

# Activate virtual environment and check dependencies
if [ ! -f "$PYTEST" ]; then
    echo -e "${YELLOW}📦 Installing test dependencies...${NC}"
    "$PYTHON" -m pip install -e ".[test]" --quiet
fi

# Note: Test database is handled automatically by pytest-django
echo -e "${BLUE}🔄 Setting up test environment...${NC}"

# Determine what to run based on argument
case "${1:-all}" in
    "quick"|"fast")
        echo -e "${GREEN}⚡ Running quick tests...${NC}"
        "$PYTEST" tests/backend/test_models.py tests/backend/test_serializers.py -v --tb=short -x
        ;;
    "unit")
        echo -e "${GREEN}🔧 Running unit tests...${NC}"
        "$PYTEST" tests/backend/test_models.py tests/backend/test_serializers.py tests/backend/test_views.py -v
        ;;
    "api")
        echo -e "${GREEN}🌐 Running API tests...${NC}"
        "$PYTEST" tests/backend/test_api_integration.py -v
        ;;
    "security")
        echo -e "${GREEN}🔒 Running security tests...${NC}"
        "$PYTEST" tests/security/ -v --tb=short
        ;;
    "performance")
        echo -e "${GREEN}⚡ Running performance tests...${NC}"
        "$PYTEST" tests/performance/test_performance.py -v -m performance
        ;;
    "coverage")
        echo -e "${GREEN}📊 Running tests with coverage...${NC}"
        "$PYTEST" tests/backend/ --cov=. --cov-report=html --cov-report=term-missing
        echo ""
        echo -e "${BLUE}📈 Coverage report: file://$(pwd)/htmlcov/index.html${NC}"
        ;;
    "all")
        echo -e "${GREEN}🚀 Running all backend tests...${NC}"
        "$PYTEST" tests/backend/ tests/security/ -v --cov=. --cov-report=term-missing
        ;;
    *)
        echo "Usage: $0 [test_type]"
        echo ""
        echo "Test types:"
        echo "  quick      - Fast unit tests only"
        echo "  unit       - All unit tests"
        echo "  api        - API integration tests"
        echo "  security   - Security tests"
        echo "  performance - Performance tests"
        echo "  coverage   - All tests with coverage report"
        echo "  all        - All backend tests (default)"
        echo ""
        echo "Examples:"
        echo "  $0           # Run all backend tests"
        echo "  $0 quick     # Run quick tests"
        echo "  $0 coverage  # Run with coverage report"
        exit 0
        ;;
esac

echo ""
echo -e "${GREEN}✅ Tests completed!${NC}"