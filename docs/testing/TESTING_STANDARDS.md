# Testing Standards & Guidelines

## Overview

This document outlines the testing standards, best practices, and guidelines for the Mina platform. All code must meet these standards to be merged into production.

## Testing Philosophy

**Core Principles:**
1. **Quality over Quantity**: Focus on meaningful tests that catch real bugs
2. **Test Pyramid**: More unit tests, fewer integration tests, minimal E2E tests
3. **Fast Feedback**: Tests should run quickly to enable rapid iteration
4. **Reliability**: Tests must be deterministic and not flaky
5. **Maintainability**: Tests should be easy to understand and update

## Coverage Requirements

### Minimum Coverage Targets
- **Overall Coverage**: 80% minimum (enforced by pytest)
- **Critical Paths**: 95%+ (authentication, payments, data processing)
- **New Code**: 90%+ (all new features must be well-tested)
- **Bug Fixes**: 100% (every bug fix must include a regression test)

### Coverage Metrics
```bash
# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term-missing

# View coverage report
open tests/results/coverage/index.html
```

## Test Types & When to Use Them

### 1. Unit Tests (`tests/unit/`)
**Purpose**: Test individual functions/classes in isolation

**Use When:**
- Testing pure functions
- Testing business logic
- Testing utility functions
- Testing individual methods

**Characteristics:**
- Fast (<10ms per test)
- No external dependencies
- Use mocks/stubs for dependencies
- Should be deterministic

**Example:**
```python
@pytest.mark.unit
def test_validate_email():
    from services.input_validation import InputValidationService
    
    validator = InputValidationService()
    assert validator.validate_email('test@example.com') == True
    assert validator.validate_email('invalid') == False
```

### 2. Integration Tests (`tests/integration/`)
**Purpose**: Test component interactions and integrations

**Use When:**
- Testing database operations
- Testing service layer integrations
- Testing API endpoints
- Testing external service integrations

**Characteristics:**
- Slower than unit tests (<500ms per test)
- May use real database (test DB)
- Tests real component interactions
- Uses fixtures for setup/teardown

**Example:**
```python
@pytest.mark.integration
def test_create_user(db_session):
    from models import User
    
    user = User(username='testuser', email='test@example.com')
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
```

### 3. E2E Tests (`tests/e2e/`)
**Purpose**: Test complete user workflows end-to-end

**Use When:**
- Testing critical user journeys
- Testing UI interactions
- Testing full system integration
- Smoke testing

**Characteristics:**
- Slowest tests (<30s per test)
- Uses real browser (Playwright)
- Tests user perspective
- Most brittle, use sparingly

**Example:**
```python
@pytest.mark.e2e
async def test_user_login_flow(page: Page):
    await page.goto('http://localhost:5000/login')
    await page.fill('#username', 'testuser')
    await page.fill('#password', 'password123')
    await page.click('#login-button')
    await expect(page).to_have_url('http://localhost:5000/dashboard')
```

### 4. Accessibility Tests (`tests/accessibility/`)
**Purpose**: Ensure WCAG 2.1 AA compliance

**Use When:**
- Testing new UI components
- Testing page accessibility
- Verifying ARIA attributes
- Testing keyboard navigation

**Tools:**
- axe-core (automated)
- Manual keyboard testing
- Screen reader testing (manual)

**Example:**
```python
@pytest.mark.accessibility
async def test_homepage_accessibility(page: Page):
    await page.goto('http://localhost:5000/')
    
    results = await page.evaluate('axe.run()')
    violations = results['violations']
    
    assert len(violations) == 0, f"Accessibility violations: {violations}"
```

### 5. Visual Regression Tests (`tests/visual/`)
**Purpose**: Catch unintended visual changes

**Use When:**
- Testing UI component changes
- Verifying responsive design
- Testing theme changes
- Ensuring visual consistency

**Workflow:**
```bash
# Update baseline screenshots
pytest tests/visual/ --update-snapshots

# Run visual regression tests
pytest tests/visual/ -v
```

### 6. Performance Tests (`tests/performance/`)
**Purpose**: Ensure system meets performance SLOs

**Use When:**
- Testing API response times
- Load testing
- Stress testing
- Verifying performance budgets

**Tools:**
- k6 (load testing)
- Lighthouse CI (frontend performance)
- pytest-benchmark (Python benchmarks)

## Test Organization

### Directory Structure
```
tests/
├── unit/               # Unit tests
├── integration/        # Integration tests
├── e2e/                # E2E tests (Playwright)
├── accessibility/      # Accessibility tests
├── visual/             # Visual regression tests
├── performance/        # Performance tests
├── data/               # Test data and fixtures
├── results/            # Test results and reports
├── conftest.py         # Root pytest configuration
└── factories.py        # Test data factories
```

### Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*` (e.g., `TestUserAuthentication`)
- Test functions: `test_*` (e.g., `test_user_login`)
- Fixtures: Descriptive names (e.g., `authenticated_client`, `test_user`)

## Test Data Management

### Using Factories
Always use factories for test data generation:

```python
from tests.factories import UserFactory, SessionFactory

def test_with_factory():
    user = UserFactory()
    session = SessionFactory(user_id=user['id'])
    assert session['user_id'] == user['id']
```

### Fixtures
Use fixtures for reusable test setup:

```python
@pytest.fixture
def test_user(db_session):
    user = User(username='testuser', email='test@example.com')
    db_session.add(user)
    db_session.commit()
    return user
```

## Test Markers

### Available Markers
```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.e2e           # E2E test
@pytest.mark.accessibility # Accessibility test
@pytest.mark.visual        # Visual regression test
@pytest.mark.smoke         # Smoke test
@pytest.mark.asyncio       # Async test
```

### Running Specific Tests
```bash
# Run only unit tests
pytest -m unit

# Run unit and integration tests
pytest -m "unit or integration"

# Run all except E2E tests
pytest -m "not e2e"

# Run specific test file
pytest tests/unit/test_app_basic.py

# Run specific test
pytest tests/unit/test_app_basic.py::test_home_page
```

## Best Practices

### 1. Test Naming
- **Descriptive**: `test_user_cannot_login_with_invalid_password`
- **Not**: `test_login_fail`

### 2. AAA Pattern
Arrange-Act-Assert structure:

```python
def test_user_creation():
    # Arrange
    username = 'testuser'
    email = 'test@example.com'
    
    # Act
    user = User(username=username, email=email)
    
    # Assert
    assert user.username == username
    assert user.email == email
```

### 3. Test Isolation
Each test should be independent:

```python
# GOOD: Use fixtures for clean state
def test_with_fixture(db_session):
    user = User(username='testuser')
    db_session.add(user)
    db_session.commit()
    assert user.id is not None

# BAD: Relying on previous test state
def test_depends_on_previous():
    user = User.query.first()  # Assumes user exists
    assert user is not None
```

### 4. Avoid Test Interdependence
Never rely on test execution order:

```python
# BAD: Tests depend on each other
def test_1_create_user():
    global user
    user = User(username='test')
    
def test_2_update_user():
    user.email = 'new@example.com'  # Depends on test_1
```

### 5. Mock External Services
Always mock external APIs in tests:

```python
@pytest.fixture
def mock_openai_api(mocker):
    return mocker.patch('openai.ChatCompletion.create', return_value={
        'choices': [{'message': {'content': 'Test response'}}]
    })

def test_with_mocked_api(mock_openai_api):
    response = call_openai_api()
    assert response == 'Test response'
```

### 6. Use Parametrize for Multiple Cases
```python
@pytest.mark.parametrize('email,expected', [
    ('valid@example.com', True),
    ('invalid', False),
    ('test@', False),
    ('@example.com', False),
])
def test_email_validation(email, expected):
    assert validate_email(email) == expected
```

### 7. Test Error Cases
```python
def test_user_creation_with_duplicate_email(db_session):
    user1 = User(username='user1', email='test@example.com')
    db_session.add(user1)
    db_session.commit()
    
    user2 = User(username='user2', email='test@example.com')
    db_session.add(user2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
```

## CI/CD Integration

### GitHub Actions
All tests run automatically on:
- Push to `main` or `develop`
- Pull requests

### Test Jobs
1. **Unit & Integration Tests**: Fast tests (<5 min)
2. **E2E Tests**: Browser tests (~10 min)
3. **Accessibility Tests**: axe-core validation (~5 min)
4. **Lighthouse CI**: Performance budgets (~5 min)
5. **Visual Regression**: Screenshot comparison (~5 min)

### Required Checks
All PRs must pass:
- ✅ All tests passing
- ✅ 80%+ code coverage
- ✅ No accessibility violations
- ✅ Lighthouse scores >90
- ✅ No visual regressions

## Debugging Failed Tests

### 1. Read the Error Message
```bash
pytest -v --tb=short  # Short traceback
pytest -v --tb=long   # Full traceback
```

### 2. Run Single Test
```bash
pytest tests/unit/test_app_basic.py::test_specific_test -v
```

### 3. Use pdb Debugger
```python
def test_with_debugger():
    import pdb; pdb.set_trace()
    result = function_to_test()
    assert result == expected
```

### 4. Check Logs
```bash
# Run with logging
pytest -v --log-cli-level=DEBUG

# Check test output
cat tests/results/test-output/test.log
```

### 5. Visual Test Debugging
```bash
# View diff images
open tests/results/screenshots/diff/

# Update baseline if changes are intentional
pytest tests/visual/ --update-snapshots
```

## Performance Testing

### API Performance
```python
def test_api_response_time(client):
    import time
    start = time.time()
    response = client.get('/api/sessions')
    duration = time.time() - start
    
    assert duration < 0.5  # Must respond in <500ms
    assert response.status_code == 200
```

### Database Query Performance
```python
def test_query_performance(db_session):
    import time
    start = time.time()
    users = db_session.query(User).limit(100).all()
    duration = time.time() - start
    
    assert duration < 0.1  # Query must complete in <100ms
```

## Documentation Requirements

### Test Documentation
Every test file should have:
1. Module docstring explaining purpose
2. Docstrings on test classes
3. Docstrings on complex test functions

```python
"""
Integration tests for user authentication flow.
Tests cover login, logout, password reset, and session management.
"""

class TestUserAuthentication:
    """Test user authentication workflows."""
    
    def test_user_login_with_valid_credentials(self, client):
        """Test that user can log in with correct username/password."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        assert response.status_code == 302  # Redirect after login
```

## Review Checklist

Before submitting code for review, verify:

- [ ] All tests pass locally
- [ ] Added tests for new features
- [ ] Added tests for bug fixes
- [ ] Coverage >80% for new code
- [ ] No flaky tests
- [ ] Tests follow naming conventions
- [ ] Tests are isolated (no interdependence)
- [ ] External services are mocked
- [ ] Test documentation is complete
- [ ] CI/CD checks pass

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Playwright documentation](https://playwright.dev/python/)
- [axe-core documentation](https://www.deque.com/axe/)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)

## Questions?

For testing questions or guidance, refer to:
- This document
- `tests/README.md`
- `tests/e2e/test_strategy.md`
- `tests/visual/README.md`
