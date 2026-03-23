# Testing Guide for HireSense

This document provides comprehensive guidance on the automated testing suite for HireSense, including test structure, execution, coverage analysis, and best practices.

---

## Table of Contents

- [Overview](#overview)
- [Test Suite Architecture](#test-suite-architecture)
- [Prerequisites](#prerequisites)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Coverage Reports](#coverage-reports)
- [Writing New Tests](#writing-new-tests)
- [Modifying Existing Tests](#modifying-existing-tests)
- [Deleting Tests](#deleting-tests)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

The HireSense test suite is built using `pytest` and `pytest-cov`, achieving **95-97% code coverage** across the application. The suite includes:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Verify interactions between modules
- **System Tests**: Validate end-to-end user workflows

All tests are located in the `/testing` directory and use an in-memory SQLite database to avoid affecting production data.

---

## Test Suite Architecture

```
testing/
├── conftest.py                    # Shared fixtures and test configuration
├── unit/                          # Unit tests
│   ├── test_models.py            # Database model tests
│   ├── test_auth.py              # Authentication tests
│   ├── test_admin.py             # Admin functionality tests
│   └── test_roles.py             # Manager/Employee role tests
├── integration/                   # Integration tests
│   └── test_integration.py       # Cross-module integration tests
├── system/                        # End-to-end tests
│   └── test_e2e.py               # Complete workflow tests
├── coverage_html/                 # HTML coverage reports (generated)
└── coverage.xml                   # XML coverage report (generated)
```

### Key Files

- **`conftest.py`**: Contains pytest fixtures for database setup, test clients, and authenticated sessions
- **`pytest.ini`**: Pytest configuration including coverage thresholds and test discovery patterns

---

## Prerequisites

### Install Testing Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pytest==8.3.4` - Testing framework
- `pytest-cov==6.0.0` - Coverage reporting
- `pytest-mock==3.14.0` - Mocking utilities
- `pytest-flask==1.3.0` - Flask testing utilities
- `coverage==7.6.9` - Coverage analysis

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=app --cov-report=term-missing
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest testing/unit/

# Integration tests only
pytest testing/integration/

# System tests only
pytest testing/system/

# Specific test file
pytest testing/unit/test_models.py

# Specific test class
pytest testing/unit/test_models.py::TestUserModel

# Specific test function
pytest testing/unit/test_models.py::TestUserModel::test_user_creation
```

### Run Tests with Markers

```bash
# Run tests marked as 'unit'
pytest -m unit

# Run tests marked as 'integration'
pytest -m integration

# Run tests marked as 'system'
pytest -m system

# Run auth-related tests
pytest -m auth
```

### Run Tests in Parallel (faster)

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel using 4 workers
pytest -n 4
```

### Run Tests in Verbose Mode

```bash
pytest -v
```

### Run Tests and Stop at First Failure

```bash
pytest -x
```

---

## Test Categories

### Unit Tests (`testing/unit/`)

Unit tests verify individual components in isolation using mocks and patches for external dependencies.

**Files:**
- `test_models.py`: Database model tests (User, Notification)
- `test_auth.py`: Authentication logic (login, register, logout)
- `test_admin.py`: Admin operations (approval, rejection, management)
- `test_roles.py`: Role-based access control

**Example:**
```python
def test_user_creation(db_session):
    """Test basic user creation with required fields."""
    user = User(username="testuser", email="test@example.com", role="employee")
    user.set_password("SecurePass123")
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.username == "testuser"
```

### Integration Tests (`testing/integration/`)

Integration tests verify interactions between different modules, including API endpoints and database operations.

**File:**
- `test_integration.py`: Cross-module integration tests

**Example:**
```python
def test_complete_registration_and_login_flow(client, db_session):
    """Test complete user registration and login workflow."""
    # Register new user
    register_response = client.post("/auth/register", data={...})
    # Verify user exists in database
    user = User.query.filter_by(email="integration@test.com").first()
    assert user is not None
```

### System Tests (`testing/system/`)

System tests validate complete end-to-end workflows simulating real user interactions.

**File:**
- `test_e2e.py`: End-to-end workflow tests

**Example:**
```python
def test_complete_employee_registration_to_dashboard(client, db_session, admin_user):
    """Test complete workflow: employee registers, admin approves, employee logs in."""
    # Step 1: Employee registers
    # Step 2: Admin approves
    # Step 3: Employee logs in and accesses dashboard
```

---

## Coverage Reports

### Generate Coverage Reports

```bash
# Terminal report with missing lines
pytest --cov=app --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=app --cov-report=html
open testing/coverage_html/index.html  # macOS/Linux
start testing/coverage_html/index.html  # Windows

# XML report (for CI/CD)
pytest --cov=app --cov-report=xml
```

### Understanding Coverage Reports

**Terminal Output:**
```
Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
app/__init__.py            20      2    90%   15-16
app/models.py              45      3    93%   28, 35, 42
app/auth.py                78      5    94%   45-49
app/admin.py              120      8    93%   87-94
-----------------------------------------------------
TOTAL                     263     18    93%
```

- **Stmts**: Total number of statements
- **Miss**: Number of statements not covered by tests
- **Cover**: Percentage coverage
- **Missing**: Line numbers not covered

**HTML Report:**
- Navigate to `testing/coverage_html/index.html`
- Click on any file to see line-by-line coverage
- Red lines indicate uncovered code
- Green lines indicate covered code

### Coverage Threshold

The test suite enforces **85% minimum coverage**. If coverage drops below this threshold:
- Local tests will fail
- CI/CD pipeline will fail and block PR merges

---

## Writing New Tests

### Step 1: Choose the Appropriate Test Type

- **Unit Test**: Testing a single function/method in isolation
- **Integration Test**: Testing interactions between modules
- **System Test**: Testing complete user workflows

### Step 2: Create Test File

Place your test file in the appropriate directory:
- Unit tests: `testing/unit/test_<module>.py`
- Integration tests: `testing/integration/test_<feature>.py`
- System tests: `testing/system/test_<workflow>.py`

### Step 3: Use Fixtures from `conftest.py`

Available fixtures:
- `app`: Flask application instance
- `client`: Test client for HTTP requests
- `db_session`: Clean database session
- `admin_user`, `manager_user`, `employee_user`: Pre-created users
- `authenticated_admin_client`, `authenticated_manager_client`, `authenticated_employee_client`: Authenticated test clients

### Step 4: Write Your Test

```python
import pytest
from app.models import User

class TestNewFeature:
    """Test suite for new feature."""

    def test_new_functionality(self, client, db_session):
        """Test description."""
        # Arrange
        user = User(username="testuser", email="test@example.com", role="employee")
        user.set_password("Pass@123")
        db_session.add(user)
        db_session.commit()

        # Act
        response = client.post("/auth/login", data={
            "email": "test@example.com",
            "password": "Pass@123",
        }, follow_redirects=True)

        # Assert
        assert response.status_code == 200
```

### Step 5: Run Your Test

```bash
pytest testing/unit/test_<module>.py::TestNewFeature::test_new_functionality -v
```

### Step 6: Verify Coverage

```bash
pytest --cov=app --cov-report=term-missing
```

---

## Modifying Existing Tests

### Step 1: Locate the Test

```bash
# Search for test by name
grep -r "test_user_creation" testing/

# Or use pytest to find it
pytest --collect-only | grep "test_user_creation"
```

### Step 2: Edit the Test

Open the file and modify the test function. Ensure you maintain:
- Clear test naming
- Arrange-Act-Assert structure
- Proper assertions

### Step 3: Run the Modified Test

```bash
pytest testing/unit/test_models.py::TestUserModel::test_user_creation -v
```

### Step 4: Verify No Regressions

```bash
# Run all tests to ensure no side effects
pytest
```

---

## Deleting Tests

### When to Delete Tests

- Test is obsolete due to removed functionality
- Test is redundant with other tests
- Test is flaky and cannot be fixed

### Step 1: Verify Test is Safe to Delete

```bash
# Run specific test to understand what it covers
pytest testing/unit/test_models.py::TestUserModel::test_obsolete_feature -v
```

### Step 2: Delete the Test

Remove the test function from the file.

### Step 3: Verify Coverage

```bash
# Ensure coverage doesn't drop below 85%
pytest --cov=app --cov-report=term-missing --cov-fail-under=85
```

### Step 4: Update Documentation

If the test was significant, update this document or related documentation.

---

## CI/CD Integration

### GitHub Actions Workflow

The CI/CD pipeline (`.github/workflows/ci.yml`) automatically:

1. **Triggers on**:
   - Push to `main` branch
   - Pull requests to `main` branch

2. **Runs tests**:
   - Sets up Python 3.11 and 3.12
   - Installs dependencies
   - Runs full test suite with coverage
   - Enforces 85% minimum coverage

3. **Fails if**:
   - Any test fails
   - Coverage drops below 85%

4. **Outputs**:
   - Coverage reports (HTML, XML, terminal)
   - Test results uploaded as artifacts

### Viewing CI Results

1. Navigate to your PR on GitHub
2. Scroll to "Checks" section
3. Click on "CI - Automated Testing & Coverage"
4. View logs and download coverage reports

### Coverage Gate

The pipeline includes a coverage gate that **blocks PR merges** if coverage is below 85%.

---

## Troubleshooting

### Tests Fail Locally but Pass in CI

**Issue**: Environment differences

**Solution**:
```bash
# Ensure clean test environment
rm -rf testing/__pycache__
rm -rf testing/*.pyc
pytest --cache-clear
```

### Import Errors

**Issue**: Module not found

**Solution**:
```bash
# Ensure you're in project root
pwd  # Should show: /path/to/HireSense

# Reinstall dependencies
pip install -r requirements.txt
```

### Database Errors

**Issue**: Database connection issues

**Solution**:
Tests use in-memory SQLite database by default (configured in `conftest.py`). Check that `conftest.py` properly sets:
```python
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
```

### Coverage Below 85%

**Issue**: New code not covered by tests

**Solution**:
```bash
# Generate HTML coverage report to see uncovered lines
pytest --cov=app --cov-report=html
open testing/coverage_html/index.html

# Write tests for uncovered lines
```

### Fixture Not Found

**Issue**: Pytest can't find fixture

**Solution**:
- Ensure `conftest.py` is in the `testing/` directory
- Check fixture name spelling
- Verify fixture scope matches usage

---

## Best Practices

### 1. Test Naming

- Use descriptive names: `test_user_creation_with_valid_data`
- Follow pattern: `test_<what>_<condition>_<expected_result>`

### 2. Test Structure (AAA Pattern)

```python
def test_example(client):
    # Arrange: Set up test data
    user = User(...)

    # Act: Execute the functionality
    response = client.post(...)

    # Assert: Verify the outcome
    assert response.status_code == 200
```

### 3. Test Isolation

- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order

### 4. Use Descriptive Docstrings

```python
def test_user_creation(db_session):
    """
    Test that a new user can be created with valid data.

    Verifies that:
    - User is persisted to database
    - User ID is assigned
    - Default values are set correctly
    """
```

### 5. Mock External Dependencies

```python
from unittest.mock import patch

@patch('app.some_module.external_api_call')
def test_with_mock(mock_api, client):
    mock_api.return_value = {"status": "success"}
    # Test code here
```

### 6. Test Edge Cases

- Invalid inputs
- Boundary conditions
- Error handling
- Empty/null values

### 7. Keep Tests DRY

Use fixtures for repeated setup:

```python
@pytest.fixture
def sample_data(db_session):
    # Create common test data
    user = User(...)
    db_session.add(user)
    db_session.commit()
    return user
```

### 8. Avoid Test Interdependence

**Bad:**
```python
def test_step_1():
    global user_id
    user_id = create_user()

def test_step_2():
    # Uses global user_id from test_step_1
    delete_user(user_id)
```

**Good:**
```python
def test_step_1(db_session):
    user_id = create_user()
    # Test completes independently

def test_step_2(db_session):
    user_id = create_user()
    delete_user(user_id)
    # Test completes independently
```

---

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Cov Documentation](https://pytest-cov.readthedocs.io/)
- [Flask Testing Documentation](https://flask.palletsprojects.com/en/latest/testing/)
- [CONTRIBUTING.md](CONTRIBUTING.md) - See "Testing" section

---

## Questions or Issues?

If you encounter issues with the test suite:

1. Check this documentation first
2. Review existing tests for patterns
3. Check [GitHub Issues](https://github.com/paarthsiloiya/HireSense/issues)
4. Ask in team discussions

---

**Last Updated**: 2026-03-20
