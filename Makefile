# Django Task List Application - Makefile
# Provides convenient commands for development and testing

.PHONY: help install test test-unit test-integration test-frontend test-e2e test-security test-performance test-accessibility test-coverage test-quick test-all clean setup dev server migrate collectstatic lint format

# Default target
help:
	@echo "Django Task List Application"
	@echo "============================"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "Setup & Development:"
	@echo "  setup              Set up development environment"
	@echo "  install            Install all dependencies"
	@echo "  dev                Start development server"
	@echo "  migrate            Run database migrations"
	@echo "  server             Start Django server"
	@echo ""
	@echo "Testing:"
	@echo "  test               Run all tests (default)"
	@echo "  test-quick         Run quick unit tests only"
	@echo "  test-unit          Run Django unit tests"
	@echo "  test-integration   Run API integration tests"
	@echo "  test-frontend      Run JavaScript unit tests"
	@echo "  test-e2e           Run end-to-end tests"
	@echo "  test-security      Run security tests"
	@echo "  test-performance   Run performance tests"
	@echo "  test-accessibility Run accessibility tests"
	@echo "  test-coverage      Generate coverage report"
	@echo "  test-all           Run comprehensive test suite"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint               Run linting checks"
	@echo "  format             Format code"
	@echo "  clean              Clean up build artifacts"
	@echo ""
	@echo "Examples:"
	@echo "  make setup         # First time setup"
	@echo "  make test-quick    # Quick development testing"
	@echo "  make test-coverage # Full testing with coverage"
	@echo "  make dev           # Start development server"

# Variables
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest
PLAYWRIGHT = $(VENV)/bin/playwright

# Setup and installation
setup: $(VENV)/bin/activate install migrate
	@echo "✅ Development environment set up successfully!"
	@echo "Run 'make dev' to start the development server"

$(VENV)/bin/activate:
	@echo "🔄 Creating virtual environment..."
	python -m venv $(VENV)
	$(PIP) install --upgrade pip

install: $(VENV)/bin/activate
	@echo "📦 Installing dependencies..."
	$(PIP) install -e ".[test]"
	@echo "🎭 Installing Playwright browsers..."
	$(PLAYWRIGHT) install --with-deps || echo "⚠️  Playwright installation failed, E2E tests may not work"
	@echo "📦 Installing frontend dependencies..."
	npm install || echo "⚠️  npm install failed, frontend tests may not work"

# Database operations
migrate:
	@echo "🔄 Running database migrations..."
	$(PYTHON) manage.py migrate

migrate-test:
	@echo "🔄 Running test database migrations..."
	$(PYTHON) manage.py migrate --settings=tasklist_project.settings.test

# Development server
dev: migrate
	@echo "🚀 Starting development server..."
	$(PYTHON) manage.py runserver

server: migrate
	@echo "🚀 Starting Django server..."
	$(PYTHON) manage.py runserver

# Testing targets
test: ./run_tests.sh
	@./run_tests.sh all

test-quick: $(PYTEST)
	@echo "⚡ Running quick tests..."
	@./test.sh quick

test-unit: $(PYTEST) migrate-test
	@echo "🔧 Running unit tests..."
	@./run_tests.sh unit

test-integration: $(PYTEST) migrate-test
	@echo "🌐 Running integration tests..."
	@./run_tests.sh integration

test-frontend:
	@echo "🎨 Running frontend tests..."
	@./run_tests.sh frontend

test-e2e: migrate-test
	@echo "🖥️  Running end-to-end tests..."
	@./run_tests.sh e2e

test-security: $(PYTEST) migrate-test
	@echo "🔒 Running security tests..."
	@./run_tests.sh security

test-performance: $(PYTEST) migrate-test
	@echo "⚡ Running performance tests..."
	@./run_tests.sh performance

test-accessibility: migrate-test
	@echo "♿ Running accessibility tests..."
	@./run_tests.sh accessibility

test-coverage: $(PYTEST) migrate-test
	@echo "📊 Generating coverage report..."
	@./run_tests.sh coverage

test-all: migrate-test
	@echo "🚀 Running comprehensive test suite..."
	@./run_tests.sh all

# Quick test variants
quick: test-quick

coverage: test-coverage

security: test-security

e2e: test-e2e

# Code quality
lint: $(VENV)/bin/activate
	@echo "🔍 Running linting checks..."
	$(PIP) install flake8 black isort mypy --quiet
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	black --check . --diff
	isort --check-only . --diff

format: $(VENV)/bin/activate
	@echo "✨ Formatting code..."
	$(PIP) install black isort --quiet
	black .
	isort .

# Maintenance
clean:
	@echo "🧹 Cleaning up build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf playwright-report/
	rm -rf test-results/
	rm -rf coverage-frontend/
	rm -rf node_modules/.cache/
	@echo "✅ Cleanup complete!"

# Utility targets
collectstatic:
	@echo "📁 Collecting static files..."
	$(PYTHON) manage.py collectstatic --noinput

shell:
	@echo "🐍 Starting Django shell..."
	$(PYTHON) manage.py shell

check:
	@echo "✅ Running Django system check..."
	$(PYTHON) manage.py check

# Default target
.DEFAULT_GOAL := test-quick