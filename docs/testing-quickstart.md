# Testing Quick Start

Quick reference for running and writing tests in Mina.

> **Note**: Examples shown are illustrative templates. See actual implementations in the `tests/` directory and [Full Testing Guide](./testing-guide.md) for complete details.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test type
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/ -m e2e    # E2E tests

# Run specific file
pytest tests/unit/test_models.py -v

# Run with live output
pytest -s -v
```

## Common Fixtures

```python
def test_example(app, client, db_session, test_user, auth_client):
    # app: Flask application
    # client: Test client (unauthenticated)
    # db_session: Database session
    # test_user: Pre-created user
    # auth_client: Authenticated test client
    pass
```

## Test Data Factories

```python
from tests.factories import (
    UserFactory,
    MeetingFactory,
    SessionFactory,
    SegmentFactory,
    SummaryFactory,
    TaskFactory,
    WorkspaceFactory,
    ParticipantFactory
)

# Create test data
user = UserFactory(email="test@example.com")
meeting = MeetingFactory(created_by=user)
session = SessionFactory(meeting=meeting)
```

## Writing Tests

### Unit Test Template

```python
def test_function_name(db_session):
    # Arrange
    user = UserFactory()
    
    # Act
    result = user.get_full_name()
    
    # Assert
    assert result == "John Doe"
```

### Integration Test Template

```python
def test_service_integration(db_session):
    # Arrange
    meeting = MeetingFactory()
    
    # Act
    summary = generate_meeting_summary(meeting.id)
    
    # Assert
    assert summary is not None
    assert len(summary.key_points) > 0
```

### E2E Test Template

```python
@pytest.mark.e2e
def test_user_flow(page):
    # Navigate
    page.goto('http://localhost:5000/')
    
    # Interact
    page.click('button#start')
    
    # Assert
    assert page.url.endswith('/dashboard')
```

### Accessibility Test Template

```python
@pytest.mark.e2e
def test_accessibility(page, axe_builder, assert_no_violations):
    page.goto('http://localhost:5000/')
    page.wait_for_load_state('networkidle')
    
    results = axe_builder()
    assert_no_violations(results)
```

## Coverage Requirements

- **Minimum**: 80% coverage required
- **Check coverage**: `pytest --cov=. --cov-report=term-missing`
- **HTML report**: `pytest --cov=. --cov-report=html` then open `htmlcov/index.html`

## CI/CD

Tests run automatically on:
- Every push to main
- Every pull request
- Manual workflow dispatch

All checks must pass:
- ✅ Tests pass
- ✅ Coverage ≥ 80%
- ✅ Linting (Ruff)
- ✅ Formatting (Black)
- ✅ Security (Bandit)
- ✅ Accessibility (axe-core)

## Debugging

```bash
# Verbose mode
pytest -v

# Show print statements
pytest -s

# Playwright debug mode
PWDEBUG=1 pytest tests/e2e/test_login.py

# Debug logs
pytest --log-cli-level=DEBUG
```

## Best Practices

1. ✅ Use factories for test data
2. ✅ One concept per test
3. ✅ Clear, descriptive test names
4. ✅ Test both success and failure cases
5. ✅ Mock external services
6. ✅ Clean up after tests
7. ✅ Keep tests independent

## Common Patterns

### Testing Authentication

```python
def test_login_success(client):
    user = UserFactory(email="test@example.com")
    user.set_password("password123")
    
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 302
```

### Testing API Endpoints

```python
def test_api_endpoint(auth_client):
    response = auth_client.get('/api/meetings')
    data = response.get_json()
    
    assert response.status_code == 200
    assert 'meetings' in data
```

### Testing Database Operations

```python
def test_database_operation(db_session):
    meeting = MeetingFactory()
    db_session.commit()
    
    retrieved = Meeting.query.get(meeting.id)
    assert retrieved is not None
    assert retrieved.title == meeting.title
```

### Testing Validation

```python
def test_validation_error():
    with pytest.raises(ValueError):
        UserFactory(email="invalid-email")
```

### Mocking External Services

```python
def test_openai_call(mocker):
    mock_openai = mocker.patch('openai.Completion.create')
    mock_openai.return_value = {'choices': [{'text': 'Summary'}]}
    
    result = generate_summary("Transcript")
    assert "Summary" in result
```

## Resources

- [Full Testing Guide](./testing-guide.md)
- [pytest Docs](https://docs.pytest.org/)
- [Playwright Docs](https://playwright.dev/python/)
- [Factory Boy Docs](https://factoryboy.readthedocs.io/)

---

For detailed information, see [Testing Guide](./testing-guide.md)
