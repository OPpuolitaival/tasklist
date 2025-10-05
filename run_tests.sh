#!/bin/bash

# Django Task List Application - Test Runner Script
# This script runs all types of tests for the Django Task List application
#
# Usage:
#   ./run_tests.sh [test_type] [options]
#
# Test types:
#   all         - Run all tests (default)
#   unit        - Run Django unit tests only
#   integration - Run API integration tests only
#   frontend    - Run JavaScript unit tests only
#   e2e         - Run end-to-end tests only
#   performance - Run performance and load tests only
#   security    - Run security tests only
#   accessibility - Run accessibility tests only
#   coverage    - Generate coverage reports only
#
# Options:
#   --verbose, -v    - Verbose output
#   --help, -h       - Show this help message
#   --fast           - Skip slow tests
#   --no-coverage    - Skip coverage reporting
#   --headless       - Run browser tests in headless mode
#   --parallel       - Run tests in parallel where possible

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
PYTHON="$VENV_PATH/bin/python"
PYTEST="$VENV_PATH/bin/pytest"
PLAYWRIGHT="node_modules/.bin/playwright"
LOCUST="$VENV_PATH/bin/locust"

# Default options
TEST_TYPE="all"
VERBOSE=false
FAST=false
NO_COVERAGE=false
HEADLESS=true
PARALLEL=false
SHOW_HELP=false

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Functions
print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${WHITE}  Django Task List Application - Test Runner${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${CYAN}────────────────────────────────────────────────────────────${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${CYAN}────────────────────────────────────────────────────────────${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_running() {
    echo -e "${PURPLE}🔄 $1${NC}"
}

show_help() {
    cat << EOF
Django Task List Application - Test Runner

Usage: $0 [test_type] [options]

Test Types:
  all           Run all tests (default)
  unit          Run Django unit tests only
  integration   Run API integration tests only
  frontend      Run JavaScript unit tests only
  e2e           Run end-to-end tests only
  performance   Run performance and load tests only
  security      Run security tests only
  accessibility Run accessibility tests only
  coverage      Generate coverage reports only

Options:
  --verbose, -v     Verbose output
  --help, -h        Show this help message
  --fast            Skip slow tests
  --no-coverage     Skip coverage reporting
  --headless        Run browser tests in headless mode (default)
  --headed          Run browser tests in headed mode
  --parallel        Run tests in parallel where possible

Examples:
  $0                    # Run all tests
  $0 unit              # Run unit tests only
  $0 e2e --headed      # Run E2E tests with visible browser
  $0 all --fast        # Run all tests but skip slow ones
  $0 coverage          # Generate coverage report only

Environment Setup:
  Make sure you have activated the virtual environment and installed dependencies:

  source .venv/bin/activate
  uv run pip install -e ".[test]"
  playwright install
  npm install  # For frontend tests

EOF
}

check_prerequisites() {
    print_section "Checking Prerequisites"

    # Check if we're in the right directory
    if [ ! -f "$PROJECT_ROOT/manage.py" ]; then
        print_error "manage.py not found. Please run this script from the project root directory."
        exit 1
    fi

    # Check virtual environment
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        print_info "Please create a virtual environment: python -m venv .venv"
        exit 1
    fi

    # Check Python
    if [ ! -f "$PYTHON" ]; then
        print_error "Python not found in virtual environment"
        exit 1
    fi

    # Check pytest
    if [ ! -f "$PYTEST" ]; then
        print_warning "pytest not found. Installing test dependencies..."
        "$PYTHON" -m pip install -e ".[test]" || {
            print_error "Failed to install test dependencies"
            exit 1
        }
    fi

    print_success "Prerequisites check passed"
}

run_django_migrations() {
    print_info "Running database migrations for tests..."
    "$PYTHON" manage.py migrate --settings=tasklist_project.settings.test --run-syncdb >/dev/null 2>&1 || {
        print_warning "Migration failed, but continuing with tests"
    }
}

run_unit_tests() {
    print_section "Running Django Unit Tests"
    print_running "Executing unit tests for models, serializers, and views..."

    local pytest_args=("$PYTEST" tests/backend/test_models.py tests/backend/test_serializers.py tests/backend/test_views.py)

    if [ "$VERBOSE" = true ]; then
        pytest_args+=("-v")
    fi

    if [ "$FAST" = true ]; then
        pytest_args+=("-m" "not slow")
    fi

    if [ "$NO_COVERAGE" = false ]; then
        pytest_args+=("--cov=." "--cov-report=term-missing")
    fi

    if [ "$PARALLEL" = true ]; then
        pytest_args+=("-n" "auto")
    fi

    if "${pytest_args[@]}" --tb=short; then
        # Unit tests passed
        print_success "Unit tests passed"
        return 0
    else
        # Unit tests failed
        print_error "Unit tests failed"
        return 1
    fi
}

run_integration_tests() {
    print_section "Running Integration Tests"
    print_running "Executing API integration tests..."

    local pytest_args=("$PYTEST" tests/backend/test_api_integration.py)

    if [ "$VERBOSE" = true ]; then
        pytest_args+=("-v")
    fi

    if "${pytest_args[@]}" --tb=short; then
        # Integration tests passed
        print_success "Integration tests passed"
        return 0
    else
        # Integration tests failed
        print_error "Integration tests failed"
        return 1
    fi
}

run_frontend_tests() {
    print_section "Running Frontend Tests"

    # Check if npm and package.json exist
    if [ ! -f "$PROJECT_ROOT/package.json" ] || ! command -v npm &> /dev/null; then
        print_warning "Frontend tests skipped: npm or package.json not found"
        # Frontend tests skipped
        return 0
    fi

    print_running "Executing JavaScript unit tests..."

    # Install dependencies if node_modules doesn't exist
    if [ ! -d "$PROJECT_ROOT/node_modules" ]; then
        print_info "Installing npm dependencies..."
        npm install || {
            print_warning "Failed to install npm dependencies, skipping frontend tests"
            # Frontend tests skipped
            return 0
        }
    fi

    # Run Jest tests
    local npm_args=("test" "--" "--watchAll=false" "--passWithNoTests")

    if [ "$NO_COVERAGE" = false ]; then
        npm_args+=("--coverage")
    fi

    if npm run "${npm_args[@]}"; then
        # Frontend tests passed
        print_success "Frontend tests passed"
        return 0
    else
        # Frontend tests failed
        print_error "Frontend tests failed"
        return 1
    fi
}

run_e2e_tests() {
    print_section "Running End-to-End Tests"

    if [ ! -f "$PLAYWRIGHT" ]; then
        print_warning "E2E tests skipped: Playwright not installed"
        print_info "Install with: playwright install"
        # E2E tests skipped
        return 0
    fi

    print_running "Executing end-to-end tests with Playwright..."

    print_info "Playwright will manage Django server automatically..."

    local playwright_args=("$PLAYWRIGHT" "test" "tests/e2e/")

    if [ "$HEADLESS" = true ]; then
        playwright_args+=("--config=playwright.config.js")
    else
        playwright_args+=("--headed" "--config=playwright.config.js")
    fi

    if [ "$PARALLEL" = true ]; then
        playwright_args+=("--workers=2")
    fi

    local e2e_result=0
    if "${playwright_args[@]}"; then
        # E2E tests passed
        print_success "End-to-end tests passed"
    else
        # E2E tests failed
        print_error "End-to-end tests failed"
        e2e_result=1
    fi

    # Django server managed by Playwright

    return $e2e_result
}

run_performance_tests() {
    print_section "Running Performance Tests"
    print_running "Executing performance tests..."

    # Run pytest performance tests
    local pytest_result=0
    if "$PYTEST" tests/performance/test_performance.py -v --tb=short -m performance; then
        print_success "Performance tests (pytest) passed"
    else
        print_error "Performance tests (pytest) failed"
        pytest_result=1
    fi

    # Run Locust load tests if available
    local locust_result=0
    if [ -f "$LOCUST" ] && [ "$FAST" = false ]; then
        print_running "Running load tests with Locust..."

        # Start Django server
        "$PYTHON" manage.py runserver 127.0.0.1:8000 --settings=tasklist_project.settings.test >/dev/null 2>&1 &
        local django_pid=$!
        sleep 3

        # Run Locust
        if "$LOCUST" -f tests/performance/locustfile.py --headless --users 10 --spawn-rate 2 --run-time 30s --host http://127.0.0.1:8000; then
            print_success "Load tests passed"
        else
            print_error "Load tests failed"
            locust_result=1
        fi

        # Kill Django server
        kill $django_pid 2>/dev/null || true
        wait $django_pid 2>/dev/null || true
    else
        if [ "$FAST" = true ]; then
            print_warning "Load tests skipped (fast mode)"
        else
            print_warning "Load tests skipped: Locust not installed"
        fi
    fi

    if [ $pytest_result -eq 0 ] && [ $locust_result -eq 0 ]; then
        # Performance tests passed
        return 0
    else
        # Performance tests failed
        return 1
    fi
}

run_security_tests() {
    print_section "Running Security Tests"
    print_running "Executing security tests..."

    local pytest_args=("$PYTEST" tests/security/)

    if [ "$VERBOSE" = true ]; then
        pytest_args+=("-v")
    fi

    if [ "$FAST" = true ]; then
        pytest_args+=("-m" "not slow")
    fi

    if "${pytest_args[@]}" --tb=short; then
        # Security tests passed
        print_success "Security tests passed"
        return 0
    else
        # Security tests failed
        print_error "Security tests failed"
        return 1
    fi
}

run_accessibility_tests() {
    print_section "Running Accessibility Tests"

    if [ ! -f "$PLAYWRIGHT" ]; then
        print_warning "Accessibility tests skipped: Playwright not installed"
        # Accessibility tests skipped
        return 0
    fi

    # Check if axe-core is installed
    if [ ! -d "$PROJECT_ROOT/node_modules/@axe-core" ] && [ ! -d "$PROJECT_ROOT/node_modules/@axe-core/playwright" ]; then
        print_info "Installing axe-core for accessibility testing..."
        npm install @axe-core/playwright >/dev/null 2>&1 || {
            print_warning "Failed to install axe-core, skipping accessibility tests"
            # Accessibility tests skipped
            return 0
        }
    fi

    print_running "Executing accessibility tests..."

    # Start Django server
    "$PYTHON" manage.py runserver 127.0.0.1:8000 --settings=tasklist_project.settings.test >/dev/null 2>&1 &
    local django_pid=$!
    sleep 3

    # Run accessibility tests using separate config file
    local playwright_args=("$PLAYWRIGHT" "test" "--config=playwright-accessibility.config.js")

    if [ "$HEADLESS" = false ]; then
        playwright_args+=("--headed")
    fi

    local a11y_result=0
    if "${playwright_args[@]}"; then
        # Accessibility tests passed
        print_success "Accessibility tests passed"
    else
        # Accessibility tests failed
        print_error "Accessibility tests failed"
        a11y_result=1
    fi

    # Django server managed by Playwright

    return $a11y_result
}

generate_coverage_report() {
    print_section "Generating Coverage Report"
    print_running "Creating comprehensive coverage report..."

    if "$PYTEST" tests/ --cov=. --cov-report=html --cov-report=term-missing --cov-report=xml --cov-fail-under=80; then
        print_success "Coverage report generated successfully"
        print_info "HTML report: file://$PROJECT_ROOT/htmlcov/index.html"
        print_info "XML report: $PROJECT_ROOT/coverage.xml"
        return 0
    else
        print_error "Coverage report generation failed"
        return 1
    fi
}

run_all_tests() {
    print_section "Running All Tests"

    local test_functions=(
        "run_unit_tests"
        "run_integration_tests"
        "run_frontend_tests"
        "run_security_tests"
        "run_e2e_tests"
        "run_performance_tests"
        "run_accessibility_tests"
    )

    for test_func in "${test_functions[@]}"; do
        if $test_func; then
            ((PASSED_TESTS++))
        else
            ((FAILED_TESTS++))
        fi
        ((TOTAL_TESTS++))
    done
}

print_summary() {
    print_section "Test Results Summary"

    echo ""
    printf "%-20s %s\n" "Test Suite" "Status"
    echo "────────────────────────────────────────"

    # Simplified summary without associative arrays

    echo ""
    echo "────────────────────────────────────────"
    printf "Total: %d, " "$TOTAL_TESTS"
    printf "${GREEN}Passed: %d${NC}, " "$PASSED_TESTS"
    printf "${RED}Failed: %d${NC}\n" "$FAILED_TESTS"
    echo ""

    if [ $FAILED_TESTS -eq 0 ]; then
        print_success "🎉 All tests passed!"
        echo ""
        print_info "Coverage report: file://$PROJECT_ROOT/htmlcov/index.html"
        return 0
    else
        print_error "❌ Some tests failed!"
        echo ""
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        all|unit|integration|frontend|e2e|performance|security|accessibility|coverage)
            TEST_TYPE="$1"
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        --fast)
            FAST=true
            shift
            ;;
        --no-coverage)
            NO_COVERAGE=true
            shift
            ;;
        --headless)
            HEADLESS=true
            shift
            ;;
        --headed)
            HEADLESS=false
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    if [ "$SHOW_HELP" = true ]; then
        show_help
        exit 0
    fi

    print_header
    check_prerequisites
    run_django_migrations

    case $TEST_TYPE in
        all)
            run_all_tests
            ;;
        unit)
            run_unit_tests || ((FAILED_TESTS++))
            ((TOTAL_TESTS++))
            ;;
        integration)
            run_integration_tests || ((FAILED_TESTS++))
            ((TOTAL_TESTS++))
            ;;
        frontend)
            run_frontend_tests || ((FAILED_TESTS++))
            ((TOTAL_TESTS++))
            ;;
        e2e)
            run_e2e_tests || ((FAILED_TESTS++))
            ((TOTAL_TESTS++))
            ;;
        performance)
            run_performance_tests || ((FAILED_TESTS++))
            ((TOTAL_TESTS++))
            ;;
        security)
            run_security_tests || ((FAILED_TESTS++))
            ((TOTAL_TESTS++))
            ;;
        accessibility)
            run_accessibility_tests || ((FAILED_TESTS++))
            ((TOTAL_TESTS++))
            ;;
        coverage)
            generate_coverage_report || ((FAILED_TESTS++))
            ((TOTAL_TESTS++))
            ;;
        *)
            print_error "Unknown test type: $TEST_TYPE"
            show_help
            exit 1
            ;;
    esac

    if [ "$TEST_TYPE" = "all" ] || [ $TOTAL_TESTS -gt 1 ]; then
        print_summary
    fi

    exit $FAILED_TESTS
}

# Run main function
main "$@"