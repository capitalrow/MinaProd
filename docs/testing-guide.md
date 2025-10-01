# Testing Guide for Mina

## Overview

Mina follows a comprehensive testing strategy to ensure 100% production-ready quality. This guide covers all testing standards, practices, and procedures for the project.

> **Note**: Code examples in this guide are illustrative and may use simplified implementations. For actual test implementations, refer to the `tests/` directory.

## Testing Philosophy

- **80% Minimum Coverage**: All code must maintain at least 80% test coverage
- **Test Pyramid**: Focus on unit tests, supported by integration and E2E tests
- **Quality Over Quantity**: Tests should be meaningful and catch real issues
- **CI/CD Integration**: All tests run automatically in GitHub Actions

## Test Types

### 1. Unit Tests
**Location**: `tests/unit/`

Unit tests verify individual functions and classes in isolation.

```python
# Example unit test
def test_user_full_name(test_user):
    assert test_user.full_name() == "John Doe"
```

### 2. Integration Tests
**Location**: `tests/integration/`

Integration tests verify interactions between components, database operations, and service layer functionality.

```python
# Example integration test
def test_create_meeting_with_participants(db_session):
    meeting = create_meeting(
        title="Team Sync",
        participants=["user1@example.com", "user2@example.com"]
    )
    assert len(meeting.participants) == 2
```

### 3. E2E Tests
**Location**: `tests/e2e/`

End-to-end tests use Playwright to verify full user workflows across the application.

```python
# Example E2E test
@pytest.mark.e2e
def test_user_login_flow(page):
    page.goto('http://localhost:5000/auth/login')
    page.fill('input[name="email"]', 'test@example.com')
    page.fill('input[name="password"]', 'password123')
    page.click('button[type="submit"]')
    expect(page).to_have_url('/dashboard')
```

### 4. Accessibility Tests
**Location**: `tests/accessibility/`

WCAG 2.1 AA compliance tests using axe-core to ensure accessibility standards.

```python
# Example accessibility test
@pytest.mark.e2e
def test_page_accessibility(page, axe_builder, assert_no_violations):
    page.goto('http://localhost:5000/')
    results = axe_builder()
    assert_no_violations(results)
```

## Test Data Factories

Use factories to create test data consistently. Available factories (see [tests/factories.py](../tests/factories.py)):

- **UserFactory**: Create test users
- **SessionFactory**: Create recording sessions
- **SegmentFactory**: Create transcript segments
- **MeetingFactory**: Create meetings
- **SummaryFactory**: Create AI summaries
- **TaskFactory**: Create extracted tasks
- **WorkspaceFactory**: Create workspaces
- **ParticipantFactory**: Create meeting participants

```python
from tests.factories import UserFactory, MeetingFactory

def test_meeting_creation():
    user = UserFactory()
    meeting = MeetingFactory(created_by=user)
    assert meeting.created_by.id == user.id
```

See [tests/integration/test_factories.py](../tests/integration/test_factories.py) for factory usage examples.

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Types
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/ -m e2e

# Accessibility tests only
pytest tests/accessibility/ -m e2e
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/integration/test_meeting_service.py -v
```

### Run Specific Test Function
```bash
pytest tests/unit/test_models.py::test_user_creation -v
```

## Writing Tests

### Test Structure

Follow the Arrange-Act-Assert (AAA) pattern:

```python
def test_user_authentication():
    # Arrange
    user = UserFactory(email="test@example.com")
    user.set_password("password123")
    
    # Act
    is_valid = user.check_password("password123")
    
    # Assert
    assert is_valid is True
```

### Fixtures

Common fixtures available in [tests/conftest.py](../tests/conftest.py):

- `app`: Flask application instance
- `client`: Flask test client
- `db_session`: Database session for tests
- `test_user`: Pre-created test user
- `auth_client`: Authenticated test client

```python
def test_protected_route(auth_client):
    response = auth_client.get('/dashboard')
    assert response.status_code == 200
```

For E2E and accessibility tests, see [tests/accessibility/conftest.py](../tests/accessibility/conftest.py).

### Playwright Fixtures

Available in E2E and accessibility tests:

- `page`: Playwright page instance
- `browser`: Playwright browser instance
- `context`: Playwright browser context
- `axe_builder`: Axe-core accessibility scanner

## Coverage Requirements

### Minimum Coverage: 80%

Coverage is enforced in `pytest.ini`:

```ini
[pytest]
addopts = 
    --cov=.
    --cov-fail-under=80
    --cov-append
```

### Checking Coverage

View coverage report:
```bash
pytest --cov=. --cov-report=term-missing
```

Generate HTML coverage report:
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Coverage Exclusions

Configured in `.coveragerc` (see [.coveragerc](../.coveragerc) for complete list):

```ini
[run]
omit =
    */tests/*
    */test_*.py
    */__pycache__/*
    */venv/*
    */migrations/*
    */static/*
    */templates/*
    */attached_assets/*
    # ... and other non-application paths
```

## CI/CD Integration

### GitHub Actions Workflows

Tests run automatically on every push and pull request:

1. **Main CI Pipeline** (`.github/workflows/ci.yml`):
   - Unit and integration tests
   - Accessibility tests
   - Code quality (linting, formatting)
   - Security scanning

2. **E2E Tests** (`.github/workflows/e2e-tests.yml`):
   - Cross-browser testing (Chromium, Firefox, WebKit)
   - Screenshot and video capture on failure
   - Test result artifacts

### Required Checks

All PRs must pass:
- ✅ All test suites
- ✅ 80% minimum coverage
- ✅ Linting (Ruff)
- ✅ Code formatting (Black)
- ✅ Security scan (Bandit)
- ✅ Accessibility compliance

## Best Practices

### 1. Test Independence
Each test should be independent and not rely on other tests:

```python
# ❌ Bad - relies on test execution order
def test_create_user():
    global user
    user = UserFactory()

def test_update_user():
    user.email = "new@example.com"

# ✅ Good - independent tests
def test_create_user():
    user = UserFactory()
    assert user.id is not None

def test_update_user():
    user = UserFactory()
    user.email = "new@example.com"
    assert user.email == "new@example.com"
```

### 2. Clear Test Names
Test names should describe what they test:

```python
# ❌ Bad
def test_user():
    ...

# ✅ Good
def test_user_email_validation_rejects_invalid_format():
    ...
```

### 3. One Assertion Concept Per Test
Focus each test on a single concept:

```python
# ❌ Bad - testing multiple concepts
def test_user():
    user = UserFactory()
    assert user.email is not None
    assert user.password_hash is not None
    assert user.created_at is not None

# ✅ Good - separate focused tests
def test_user_has_email():
    user = UserFactory()
    assert user.email is not None

def test_user_has_password_hash():
    user = UserFactory()
    assert user.password_hash is not None
```

### 4. Use Factories Over Raw Objects
Always use factories for consistent test data:

```python
# ❌ Bad
def test_meeting():
    user = User(id=1, email="test@example.com")
    meeting = Meeting(id=1, title="Test", created_by_id=1)

# ✅ Good
def test_meeting():
    user = UserFactory()
    meeting = MeetingFactory(created_by=user)
```

### 5. Clean Up After Tests
Use fixtures and context managers for cleanup:

```python
@pytest.fixture
def temp_file():
    path = "/tmp/test_file.txt"
    yield path
    if os.path.exists(path):
        os.remove(path)
```

### 6. Mock External Services
Mock external APIs and services:

```python
from unittest.mock import patch

def test_openai_integration(mocker):
    mock_response = {"choices": [{"text": "Mocked response"}]}
    mocker.patch('openai.Completion.create', return_value=mock_response)
    
    result = generate_summary("Test transcript")
    assert "Mocked response" in result
```

### 7. Test Error Cases
Don't just test the happy path:

```python
def test_user_login_with_wrong_password():
    user = UserFactory()
    user.set_password("correct_password")
    
    assert not user.check_password("wrong_password")

def test_meeting_creation_without_title():
    with pytest.raises(ValueError):
        MeetingFactory(title=None)
```

## Accessibility Testing

### WCAG 2.1 AA Compliance

All public pages must pass axe-core accessibility scans:

```python
@pytest.mark.e2e
def test_page_accessibility(page, axe_builder, assert_no_violations):
    page.goto('http://localhost:5000/')
    page.wait_for_load_state('networkidle')
    
    results = axe_builder()
    assert_no_violations(results)
```

### Keyboard Navigation

Test keyboard accessibility:

```python
def test_keyboard_navigation(page):
    page.goto('http://localhost:5000/')
    page.keyboard.press('Tab')
    
    focused = page.evaluate('document.activeElement.tagName')
    assert focused in ['A', 'BUTTON', 'INPUT']
```

### Form Labels

Ensure all form inputs have proper labels:

```python
def test_form_labels(page):
    page.goto('http://localhost:5000/auth/login')
    
    inputs = page.locator('input').all()
    for input_elem in inputs:
        input_id = input_elem.get_attribute('id')
        aria_label = input_elem.get_attribute('aria-label')
        
        if input_id:
            assert page.locator(f'label[for="{input_id}"]').count() > 0
        else:
            assert aria_label is not None
```

## Debugging Tests

### Run Tests in Verbose Mode
```bash
pytest -v
```

### Show Print Statements
```bash
pytest -s
```

### Debug with PDB
```python
def test_complex_logic():
    import pdb; pdb.set_trace()
    # Test code here
```

### Playwright Debug Mode
```bash
PWDEBUG=1 pytest tests/e2e/test_login.py
```

### View Test Logs
```bash
pytest --log-cli-level=DEBUG
```

## Performance Testing

Performance tests ensure the application meets speed requirements:

```python
import time

def test_meeting_list_performance(auth_client):
    # Create 100 meetings
    for _ in range(100):
        MeetingFactory()
    
    start = time.time()
    response = auth_client.get('/meetings')
    duration = time.time() - start
    
    assert duration < 0.5  # Should load in < 500ms
```

## Security Testing

Security tests verify authentication, authorization, and data protection:

```python
def test_unauthorized_access(client):
    response = client.get('/dashboard')
    assert response.status_code == 302  # Redirect to login

def test_csrf_protection(client):
    response = client.post('/meetings/create', data={})
    assert response.status_code == 400  # Missing CSRF token
```

## Common Issues and Solutions

### Issue: Database not found
**Solution**: Ensure test database is initialized in conftest.py

### Issue: Tests fail in CI but pass locally
**Solution**: Check environment variables and database configuration

### Issue: Playwright tests timeout
**Solution**: Increase timeout or check server startup

### Issue: Coverage below 80%
**Solution**: Add tests for uncovered code paths

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Playwright Python Documentation](https://playwright.dev/python/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [axe-core Documentation](https://www.deque.com/axe/core-documentation/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

## Support

For testing questions or issues:
1. Check this guide first
2. Review existing test examples in `tests/`
3. Ask in the team's development channel
4. Consult the testing lead

---

**Last Updated**: October 2025
**Version**: 1.0
