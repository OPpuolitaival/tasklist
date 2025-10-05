# Django Task List Application

A simple task list application built with Django REST Framework backend and pure JavaScript frontend.

Main purpose of this project is to demonstrate doing testing with LLM.

## Features

- User registration and authentication
- JWT token-based API authentication
- Create, read, update, and delete tasks
- Mark tasks as complete/incomplete
- Pure JavaScript frontend (no frameworks)
- Responsive design

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Run database migrations:
   ```bash
   uv run manage.py migrate
   ```

3. Start the development server:
   ```bash
   uv run manage.py runserver
   ```

4. Open http://127.0.0.1:8000 in your browser

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login

### Tasks
- `GET /api/tasks/` - List user's tasks
- `POST /api/tasks/` - Create a new task
- `GET /api/tasks/{id}/` - Get a specific task
- `PATCH /api/tasks/{id}/` - Update a task
- `DELETE /api/tasks/{id}/` - Delete a task

## Project Structure

- `tasklist_project/` - Django project settings
- `accounts/` - User authentication app
- `tasks/` - Task management app
- `static/` - Frontend files (HTML, CSS, JavaScript)

## Testing

This application includes comprehensive testing infrastructure covering functional and non-functional requirements.

### Quick Testing

```bash
# Quick unit tests (fastest)
make test-quick
# or
./test.sh quick

# All backend tests with coverage
make test-coverage
# or
./test.sh coverage
```

### Complete Test Suite

```bash
# Run all tests (unit, integration, E2E, security, accessibility, performance)
./run_tests.sh all
# or
make test-all

# Run specific test types
./run_tests.sh unit           # Django unit tests
./run_tests.sh integration    # API integration tests
./run_tests.sh frontend       # JavaScript unit tests
./run_tests.sh e2e           # End-to-end browser tests
./run_tests.sh security      # Security vulnerability tests
./run_tests.sh accessibility # WCAG compliance tests
./run_tests.sh performance   # Performance and load tests
```

### Test Options

```bash
# Fast mode (skip slow tests)
./run_tests.sh all --fast

# Verbose output
./run_tests.sh unit --verbose

# Show browser during E2E tests
./run_tests.sh e2e --headed

# Run tests in parallel
./run_tests.sh all --parallel
```

### Make Commands

```bash
make setup           # First-time development setup
make test           # Run all tests
make test-quick     # Quick unit tests
make test-coverage  # Generate coverage report
make dev            # Start development server
make clean          # Clean build artifacts
```

### Test Coverage

- **Backend**: 90%+ line coverage
- **Frontend**: 85%+ line coverage
- **Security**: 100% critical path coverage

View coverage reports:
```bash
make test-coverage
open htmlcov/index.html  # Backend coverage
```

For detailed testing information, see [TESTING.md](TESTING.md).

## Usage

1. Register a new account or login with existing credentials
2. Add new tasks using the form
3. Mark tasks as complete by clicking the "Complete" button
4. Edit tasks by clicking the "Edit" button
5. Delete tasks by clicking the "Delete" button

## Development

### First-time Setup

```bash
make setup
```

This will:
- Create virtual environment
- Install all dependencies
- Install Playwright browsers
- Install npm packages
- Run database migrations

### Development Server

```bash
make dev
# or
python manage.py runserver
```

### Code Quality

```bash
make lint      # Check code style
make format    # Format code with black and isort
```