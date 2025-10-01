# Pull Request Checklist

Before submitting a PR, ensure all items are checked:

## Testing

- [ ] All tests pass locally: `pytest`
- [ ] Test coverage ≥ 80%: `pytest --cov=. --cov-report=term-missing`
- [ ] New features have unit tests
- [ ] Integration tests cover service interactions
- [ ] E2E tests cover user workflows (if applicable)
- [ ] Accessibility tests pass for new pages: `pytest tests/accessibility/ -m e2e`

## Code Quality

- [ ] Code is linted: `ruff check .`
- [ ] Code is formatted: `black --check .`
- [ ] No security issues: `bandit -r . -ll`
- [ ] Type hints added for new functions
- [ ] No debug statements or console.logs left in code

## Documentation

- [ ] Code comments for complex logic
- [ ] Docstrings for new functions/classes
- [ ] README updated (if needed)
- [ ] API documentation updated (if applicable)

## Accessibility

- [ ] WCAG 2.1 AA compliance verified
- [ ] All interactive elements are keyboard accessible
- [ ] Form inputs have proper labels
- [ ] ARIA attributes used correctly
- [ ] Color contrast meets AA standards

## Database

- [ ] Migrations created (if schema changed): `alembic revision --autogenerate`
- [ ] Migrations tested locally: `alembic upgrade head`
- [ ] No breaking changes to existing data

## Security

- [ ] No secrets or API keys committed
- [ ] User input is validated and sanitized
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF protection in place for forms

## Performance

- [ ] No N+1 query issues
- [ ] Database queries are optimized
- [ ] Large datasets are paginated
- [ ] API responses are under 500ms (for standard requests)

## Git

- [ ] Commits are logical and well-described
- [ ] Branch is up-to-date with main
- [ ] No merge conflicts
- [ ] PR description explains changes clearly

## CI/CD

- [ ] All GitHub Actions checks pass
- [ ] No failing tests in CI
- [ ] No coverage regression
- [ ] No new linting errors

## Review

- [ ] Self-review completed
- [ ] Screenshots provided (for UI changes)
- [ ] Breaking changes documented
- [ ] Reviewers assigned

---

## Quick Commands

```bash
# Run all checks locally
pytest                                      # Run tests
pytest --cov=. --cov-report=term-missing   # Check coverage
ruff check .                               # Lint code
black --check .                            # Check formatting
bandit -r . -ll                            # Security scan

# Fix common issues
black .                                    # Auto-format
ruff check . --fix                         # Auto-fix linting
```

## Resources

- [Testing Guide](./testing-guide.md)
- [Testing Quick Start](./testing-quickstart.md)
- [Development Guidelines](../README.md)
