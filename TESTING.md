# Testing Guide for Django Task List Application

This document provides comprehensive information about the testing infrastructure and how to run various types of tests.

## Overview

Our testing strategy covers both functional and non-functional requirements:

### Functional Tests
- **Unit Tests**: Test individual components (models, serializers, views)
- **Integration Tests**: Test API endpoints and user workflows
- **End-to-End Tests**: Test complete user journeys in the browser

### Non-Functional Tests
- **Performance Tests**: Test response times and load handling
- **Security Tests**: Test authentication, authorization, and input validation
- **Accessibility Tests**: Test WCAG compliance and screen reader compatibility

## Quick Start

### Run All Tests
```bash
python scripts/run_tests.py
```

### Run Specific Test Types
```bash
# Unit tests only
python scripts/run_tests.py unit

# Integration tests only
python scripts/run_tests.py integration

# End-to-end tests only
python scripts/run_tests.py e2e

# Performance tests only
python scripts/run_tests.py performance

# Security tests only
python scripts/run_tests.py security

# Accessibility tests only
python scripts/run_tests.py accessibility

# Generate coverage report
python scripts/run_tests.py coverage
```

## Test Structure

```
tests/
├── backend/                    # Django backend tests
│   ├── test_models.py         # Model unit tests
│   ├── test_serializers.py    # Serializer unit tests
│   ├── test_views.py          # View unit tests
│   └── test_api_integration.py # API integration tests
├── frontend/                   # JavaScript unit tests
│   ├── auth.test.js           # Authentication tests
│   ├── tasks.test.js          # Task management tests
│   └── setup.js               # Jest configuration
├── e2e/                       # End-to-end tests
│   └── user-journey.spec.js   # Complete user workflows
├── performance/                # Performance tests
│   ├── test_performance.py    # Django performance tests
│   └── locustfile.py          # Load testing scenarios
├── security/                   # Security tests
│   ├── test_authentication_security.py # Auth security
│   └── test_api_security.py    # API security
├── accessibility/              # Accessibility tests
│   └── test_a11y.spec.js      # WCAG compliance tests
└── factories.py               # Test data factories
```

## Prerequisites

### Backend Testing
```bash
pip install -e ".[test]"
```

### Frontend Testing (Optional)
```bash
npm install  # Installs Jest and testing utilities
```

### End-to-End Testing
```bash
playwright install  # Installs browser drivers
```

### Performance Testing
```bash
pip install locust  # For load testing
```

## Backend Tests

### Unit Tests

Test individual Django components:

```bash
# Run all unit tests
pytest tests/backend/test_models.py tests/backend/test_serializers.py tests/backend/test_views.py

# Run with coverage
pytest tests/backend/ --cov=. --cov-report=html
```

**Key Test Files:**
- `test_models.py`: Task model validation, relationships, constraints
- `test_serializers.py`: Data serialization/deserialization, validation
- `test_views.py`: API endpoints, authentication, permissions

### Integration Tests

Test complete API workflows:

```bash
pytest tests/backend/test_api_integration.py -v
```

**Covers:**
- Complete user registration → login → task management flow
- Cross-user data isolation
- JWT token functionality
- Error handling scenarios

### Running Backend Tests

```bash
# All backend tests
pytest tests/backend/ -v

# With coverage report
pytest tests/backend/ --cov=. --cov-report=html --cov-report=term-missing

# Specific test file
pytest tests/backend/test_models.py::TestTaskModel::test_task_creation -v

# Performance tests only
pytest tests/performance/ -m performance
```

## Frontend Tests

### JavaScript Unit Tests

Test frontend JavaScript classes:

```bash
# Run frontend tests (requires npm)
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode during development
npm run test:watch
```

**Test Files:**
- `auth.test.js`: AuthManager class functionality
- `tasks.test.js`: TaskManager class functionality

**Features Tested:**
- API communication
- Local storage management
- Error handling
- State management

## End-to-End Tests

### Browser-Based Tests

Test complete user workflows in real browsers:

```bash
# Run all E2E tests
playwright test tests/e2e/

# Run specific test
playwright test tests/e2e/user-journey.spec.js

# Run in headed mode (see browser)
playwright test tests/e2e/ --headed

# Run on specific browser
playwright test tests/e2e/ --project=chromium
```

**Test Scenarios:**
- Complete user registration and login
- Task creation, editing, deletion
- Task completion toggling
- Form validation
- Session persistence
- Responsive design
- Keyboard navigation

## Performance Tests

### Backend Performance

```bash
# Run performance tests
pytest tests/performance/test_performance.py -m performance
```

**Metrics Tested:**
- API response times
- Database query efficiency
- Memory usage
- Concurrent user handling

### Load Testing

```bash
# Quick load test
locust -f tests/performance/locustfile.py --headless --users 10 --spawn-rate 2 --run-time 30s --host http://127.0.0.1:8000

# Interactive load testing
locust -f tests/performance/locustfile.py --host http://127.0.0.1:8000
```

**Load Test Scenarios:**
- Normal user behavior
- Heavy user activity
- Anonymous browsing
- Concurrent task operations

## Security Tests

### Authentication Security

```bash
pytest tests/security/test_authentication_security.py -v
```

**Security Aspects Tested:**
- Password hashing
- JWT token security
- Brute force protection
- Session management
- User enumeration protection

### API Security

```bash
pytest tests/security/test_api_security.py -v
```

**Security Vulnerabilities Tested:**
- SQL injection
- XSS attacks
- CSRF protection
- Input validation
- Authorization bypass
- Path traversal

## Accessibility Tests

### WCAG Compliance

```bash
# Run accessibility tests
playwright test tests/accessibility/

# Specific accessibility test
playwright test tests/accessibility/test_a11y.spec.js
```

**Accessibility Features Tested:**
- Screen reader compatibility
- Keyboard navigation
- Color contrast (WCAG AA)
- Form labels and associations
- ARIA attributes
- Focus management

## Test Coverage

### Generate Coverage Reports

```bash
# Backend coverage
pytest tests/backend/ --cov=. --cov-report=html --cov-report=term-missing

# Frontend coverage
npm run test:coverage

# Combined coverage report
python scripts/run_tests.py coverage
```

### Coverage Goals
- **Backend**: 90%+ line coverage
- **Frontend**: 85%+ line coverage
- **Critical paths**: 100% coverage

### View Coverage Reports

```bash
# Open HTML coverage report
open htmlcov/index.html  # Backend

# Frontend coverage report
open coverage-frontend/lcov-report/index.html
```

## Continuous Integration

### GitHub Actions

Our CI pipeline runs on every push and pull request:

1. **Backend Tests**: Unit, integration, and security tests
2. **Frontend Tests**: JavaScript unit tests
3. **E2E Tests**: Browser-based testing
4. **Accessibility Tests**: WCAG compliance
5. **Performance Tests**: Load testing (main branch only)
6. **Code Quality**: Linting and formatting checks

### Local CI Simulation

```bash
# Run the same tests as CI
python scripts/run_tests.py all
```

## Test Data Management

### Factories

We use Factory Boy for generating test data:

```python
# Create test user
user = UserFactory(username='testuser')

# Create test task
task = TaskFactory(user=user, title='Test Task')

# Create batch of tasks
tasks = TaskFactory.create_batch(5, user=user)
```

### Database Isolation

Tests use separate test databases:
- SQLite in-memory database for speed
- Each test gets a clean database state
- Transactions are rolled back after each test

## Troubleshooting

### Common Issues

1. **Tests fail with database errors**
   ```bash
   python manage.py migrate --settings=tasklist_project.settings.test
   ```

2. **Frontend tests not running**
   ```bash
   npm install  # Install Jest and dependencies
   ```

3. **Playwright tests fail**
   ```bash
   playwright install  # Install browser drivers
   ```

4. **Performance tests timeout**
   - Increase timeout values in test configuration
   - Run tests on a faster machine

### Debug Mode

```bash
# Run tests with verbose output
pytest tests/backend/ -v -s

# Run single test with debugging
pytest tests/backend/test_models.py::TestTaskModel::test_task_creation -v -s --pdb

# Playwright debug mode
playwright test tests/e2e/ --debug
```

## Best Practices

### Writing Tests

1. **Follow AAA pattern**: Arrange, Act, Assert
2. **Use descriptive test names**: `test_user_cannot_access_other_user_tasks`
3. **Test edge cases**: Empty strings, null values, boundary conditions
4. **Mock external dependencies**: Use factories for test data
5. **Keep tests fast**: Use in-memory databases, mock slow operations

### Test Organization

1. **Group related tests**: Use test classes for logical grouping
2. **Use fixtures**: Share common setup across tests
3. **Mark slow tests**: Use pytest markers for performance tests
4. **Document test purpose**: Clear docstrings explaining what's being tested

### Maintenance

1. **Regular updates**: Keep test dependencies updated
2. **Review coverage**: Aim for high but meaningful coverage
3. **Update tests with features**: New features should include tests
4. **Clean up**: Remove obsolete tests when refactoring

## Resources

- [Django Testing Documentation](https://docs.djangoproject.com/en/stable/topics/testing/)
- [pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)
- [Jest Documentation](https://jestjs.io/)
- [Locust Documentation](https://locust.io/)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all test types pass
3. Maintain or improve code coverage
4. Update documentation as needed
5. Consider security implications