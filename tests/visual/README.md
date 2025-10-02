# Visual Regression Testing

This directory contains visual regression tests using Playwright's built-in screenshot comparison.

## Overview

Visual regression tests capture screenshots of pages/components and compare them against baseline images. Any visual differences trigger test failures.

## Running Visual Tests

### Update Baseline Screenshots
```bash
# Generate/update baseline screenshots
pytest tests/visual/ --update-snapshots
```

### Run Visual Tests
```bash
# Run visual regression tests
pytest tests/visual/ -v

# Run specific test
pytest tests/visual/test_visual_regression.py::TestVisualRegression::test_homepage_visual -v
```

### CI/CD Integration
Visual tests run automatically in GitHub Actions. The workflow:
1. Runs tests against baseline screenshots
2. Uploads diff images if tests fail
3. Requires manual review of visual changes

## Test Coverage

Current visual tests cover:
- **Homepage**: Desktop & mobile views
- **Live Transcription Page**: Default & recording states
- **Dashboard**: Overview layout
- **Navigation Component**: Header consistency
- **Footer Component**: Footer layout
- **Theme Variants**: Dark mode, high contrast
- **Mobile Views**: Responsive layouts at 375x667

## Screenshot Storage

- **Baseline Images**: `tests/visual/__screenshots__/*.png`
- **Diff Images** (on failure): `tests/results/screenshots/diff/*.png`

## Configuration

Screenshot comparison settings:
- **Threshold**: 0.2 (20% pixel difference tolerance)
- **Full Page**: Captures entire scrollable page
- **Max Diff Pixels**: 100 pixels allowed variation

## Best Practices

1. **Run locally first**: Always update baselines locally before CI
2. **Review changes**: Manually inspect diff images before approving
3. **Isolate dynamic content**: Mock timestamps, random data
4. **Use stable viewports**: Test at consistent breakpoints
5. **Wait for load**: Ensure `networkidle` before capture

## Adding New Visual Tests

```python
@pytest.mark.visual
async def test_new_page_visual(self, page: Page):
    await page.goto('http://localhost:5000/new-page')
    await page.wait_for_load_state('networkidle')
    await expect(page).to_have_screenshot('new-page.png', full_page=True)
```

## Troubleshooting

### Flaky Tests
- Add explicit waits: `await page.wait_for_timeout(500)`
- Wait for animations: `await page.wait_for_selector('[data-animation-complete]')`

### Different OS/Browser Rendering
- Run in Docker/CI environment for consistency
- Use `max_diff_pixels` parameter to allow minor OS-level rendering differences

### Large Diffs
- Check for dynamic content (timestamps, random IDs)
- Verify fonts are loaded: `await page.wait_for_load_state('networkidle')`
