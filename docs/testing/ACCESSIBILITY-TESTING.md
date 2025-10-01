# Accessibility Testing Guide

## Overview

Mina implements comprehensive accessibility testing using axe-core to ensure WCAG 2.1 AA compliance. This document describes the accessibility testing infrastructure, how to run tests, and how to fix common issues.

**Status**: ✅ Production-ready  
**Coverage**: WCAG 2.1 Level A & AA  
**Tools**: axe-core, Playwright, pytest  
**Last Updated**: October 2025

---

## Testing Infrastructure

### Tools & Frameworks

**Playwright with axe-core** (JavaScript)
- **Package**: `@axe-core/playwright@^4.10.2`
- **Test Location**: `tests/e2e/06-axe-core-automated.spec.js`
- **Purpose**: Automated accessibility scanning with axe-core
- **Coverage**: All WCAG 2.1 A/AA rules

**pytest-playwright** (Python)
- **Test Location**: `tests/accessibility/test_wcag_compliance.py`
- **Purpose**: WCAG compliance validation
- **Fixtures**: `axe_builder`, `assert_no_violations`, `save_accessibility_report`

---

## Running Tests

### Local Development

**1. Start the Flask Application**
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

**2. Run All Accessibility Tests**
```bash
./tests/run-accessibility-tests.sh
```

**3. Run Specific Test Suites**
```bash
# Playwright axe-core tests only
./tests/run-accessibility-tests.sh playwright

# Python pytest tests only
./tests/run-accessibility-tests.sh python

# Or use npm/pytest directly
npx playwright test tests/e2e/06-axe-core-automated.spec.js
pytest tests/accessibility/test_wcag_compliance.py -v
```

### CI/CD Pipeline

Accessibility tests run automatically on:
- **Push to main/develop branches**
- **Pull requests**
- **Manual workflow dispatch**

**GitHub Actions Workflow**: `.github/workflows/accessibility-tests.yml`

**CI Test Matrix**:
- Node.js: 18.x, 20.x
- Python: 3.11
- Browser: Chromium

---

## Test Coverage

### Pages Tested

| Page | URL | Critical Tests |
|------|-----|----------------|
| **Home** | `/` | WCAG 2.1 A/AA, color contrast, keyboard nav |
| **Login** | `/auth/login` | Form labels, ARIA, keyboard access |
| **Register** | `/auth/register` | Form accessibility, validation feedback |
| **Live Transcription** | `/live` | Real-time updates, ARIA live regions |
| **Dashboard** | `/dashboard` | Data tables, navigation, focus management |
| **Settings** | `/settings` | Form controls, toggle states |

### WCAG Rules Tested

**WCAG 2.1 Level A**:
- ✅ 1.1.1 Non-text Content (alt text)
- ✅ 1.3.1 Info and Relationships (semantic HTML)
- ✅ 2.1.1 Keyboard (keyboard access)
- ✅ 2.4.1 Bypass Blocks (skip links)
- ✅ 2.4.4 Link Purpose (link text)
- ✅ 4.1.1 Parsing (valid HTML)
- ✅ 4.1.2 Name, Role, Value (ARIA)

**WCAG 2.1 Level AA**:
- ✅ 1.4.3 Contrast (Minimum) - 4.5:1 for text
- ✅ 1.4.5 Images of Text (avoid text in images)
- ✅ 2.4.6 Headings and Labels (descriptive)
- ✅ 2.4.7 Focus Visible (focus indicators)
- ✅ 3.2.4 Consistent Identification (consistent UI)
- ✅ 3.3.3 Error Suggestion (error guidance)
- ✅ 3.3.4 Error Prevention (confirmation dialogs)

**Specific Feature Tests**:
- Keyboard navigation (Tab, Enter, Escape, Arrow keys)
- Screen reader announcements (ARIA live regions)
- Color contrast (4.5:1 minimum for text)
- Form labels and associations
- Focus indicators and focus management
- ARIA attributes and roles
- Heading hierarchy (h1→h2→h3, no skipping)
- Alternative text for images

---

## Test Results & Reports

### Output Locations

**Playwright Results**:
```
tests/results/accessibility/
├── home_page_axe_report.json
├── login_page_axe_report.json
├── live_page_axe_report.json
├── dashboard_axe_report.json
├── settings_page_axe_report.json
├── keyboard_navigation_axe_report.json
├── color_contrast_axe_report.json
└── form_accessibility_axe_report.json
```

**HTML Reports**:
```
tests/results/html-report/index.html  # Playwright HTML report
tests/results/accessibility/pytest_report.html  # Python test report
```

### Reading axe-core Reports

**JSON Report Structure**:
```json
{
  "violations": [
    {
      "id": "color-contrast",
      "impact": "serious",
      "description": "Elements must have sufficient color contrast",
      "help": "Ensures the contrast between foreground and background colors meets WCAG 2 AA contrast ratio thresholds",
      "helpUrl": "https://dequeuniversity.com/rules/axe/4.8/color-contrast",
      "nodes": [
        {
          "html": "<button class=\"btn\">Submit</button>",
          "target": ["button.btn"],
          "failureSummary": "Fix any of the following: Element has insufficient color contrast of 2.5:1"
        }
      ]
    }
  ],
  "passes": [...],
  "incomplete": [...],
  "inapplicable": [...]
}
```

**Violation Severity Levels**:
- **Critical**: Must fix immediately (blocks accessibility)
- **Serious**: Important to fix (significant barrier)
- **Moderate**: Should fix (usability issue)
- **Minor**: Nice to fix (best practice)

---

## Common Issues & Fixes

### 1. Color Contrast Violations

**Issue**: Text doesn't have 4.5:1 contrast ratio
```
color-contrast: Elements must have sufficient color contrast
Impact: serious
```

**Fix**:
```css
/* Before: Insufficient contrast */
.text-muted {
    color: #999;  /* 2.8:1 contrast on white */
}

/* After: Sufficient contrast */
.text-muted {
    color: #666;  /* 5.7:1 contrast on white */
}
```

### 2. Missing Form Labels

**Issue**: Input elements without associated labels
```
label: Form elements must have labels
Impact: critical
```

**Fix**:
```html
<!-- Before: No label -->
<input type="text" name="email">

<!-- After: Associated label -->
<label for="email-input">Email Address</label>
<input type="text" id="email-input" name="email">

<!-- Or: ARIA label -->
<input type="text" name="email" aria-label="Email Address">
```

### 3. Missing ARIA Attributes

**Issue**: Interactive elements without proper ARIA
```
button-name: Buttons must have discernible text
Impact: critical
```

**Fix**:
```html
<!-- Before: Icon button without label -->
<button class="icon-btn">
  <i class="fa fa-search"></i>
</button>

<!-- After: With ARIA label -->
<button class="icon-btn" aria-label="Search">
  <i class="fa fa-search"></i>
</button>
```

### 4. Heading Hierarchy

**Issue**: Skipping heading levels (h1 → h3)
```
heading-order: Heading levels should only increase by one
Impact: moderate
```

**Fix**:
```html
<!-- Before: Skips h2 -->
<h1>Dashboard</h1>
<h3>Recent Meetings</h3>

<!-- After: Proper hierarchy -->
<h1>Dashboard</h1>
<h2>Recent Meetings</h2>
```

### 5. Missing Focus Indicators

**Issue**: Invisible or removed focus outlines
```
focus-order-semantics: Elements in the focus order need a role appropriate for interactive content
Impact: serious
```

**Fix**:
```css
/* Before: Removed outline */
button:focus {
    outline: none;  /* ❌ Bad */
}

/* After: Visible focus indicator */
button:focus {
    outline: 2px solid #007bff;
    outline-offset: 2px;
}

button:focus-visible {
    outline: 2px solid #007bff;
    outline-offset: 2px;
}
```

### 6. Missing Alternative Text

**Issue**: Images without alt attributes
```
image-alt: Images must have alternate text
Impact: critical
```

**Fix**:
```html
<!-- Before: No alt text -->
<img src="logo.png">

<!-- After: Descriptive alt text -->
<img src="logo.png" alt="Mina - Meeting Insights Platform">

<!-- Decorative image: Empty alt -->
<img src="decorative-divider.png" alt="">
```

---

## Best Practices

### 1. Test Early and Often

- Run accessibility tests **before** committing code
- Fix violations immediately (don't accumulate debt)
- Test new features for accessibility from the start

### 2. Use Semantic HTML

```html
<!-- ✅ Good: Semantic HTML -->
<nav>
  <ul>
    <li><a href="/dashboard">Dashboard</a></li>
  </ul>
</nav>

<main>
  <article>
    <h1>Meeting Notes</h1>
    <section>
      <h2>Summary</h2>
      <p>...</p>
    </section>
  </article>
</main>

<!-- ❌ Bad: div soup -->
<div class="nav">
  <div class="link"><a href="/dashboard">Dashboard</a></div>
</div>
<div class="main">
  <div class="article">
    <div class="title">Meeting Notes</div>
  </div>
</div>
```

### 3. ARIA Patterns

```html
<!-- ✅ Button -->
<button onclick="doAction()">Click Me</button>

<!-- ✅ Link styled as button -->
<a href="/dashboard" role="button" class="btn">Dashboard</a>

<!-- ✅ Custom widget -->
<div role="dialog" aria-labelledby="dialog-title" aria-modal="true">
  <h2 id="dialog-title">Confirm Delete</h2>
  <button aria-label="Close dialog">×</button>
</div>

<!-- ✅ Live region for dynamic content -->
<div aria-live="polite" aria-atomic="true" role="status">
  Transcription in progress...
</div>
```

### 4. Keyboard Navigation

- All interactive elements must be keyboard accessible
- Tab order should follow visual order
- Provide skip links for repetitive navigation
- Support standard keyboard shortcuts (Escape to close, Enter to activate)

```javascript
// ✅ Keyboard event handling
button.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    button.click();
  }
});

// ✅ Trap focus in modal
const modal = document.querySelector('[role="dialog"]');
const focusableElements = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
const firstElement = focusableElements[0];
const lastElement = focusableElements[focusableElements.length - 1];

modal.addEventListener('keydown', (e) => {
  if (e.key === 'Tab') {
    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  }
  
  if (e.key === 'Escape') {
    closeModal();
  }
});
```

### 5. Color and Contrast

- Don't rely on color alone to convey information
- Ensure 4.5:1 contrast for normal text
- Ensure 3:1 contrast for large text (18pt+ or 14pt+ bold)
- Provide alternatives for color-coded information

---

## Continuous Improvement

### Adding New Tests

**1. Add page to automated scan**:
```javascript
// tests/e2e/06-axe-core-automated.spec.js
test('New page should have no accessibility violations', async ({ page }) => {
  await page.goto('/new-page');
  await page.waitForLoadState('networkidle');

  const axeResults = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();

  saveReport('new_page', axeResults);
  expect(axeResults.violations).toHaveLength(0);
});
```

**2. Add Python test**:
```python
# tests/accessibility/test_wcag_compliance.py
@pytest.mark.e2e
def test_new_page_accessibility(page: Page, axe_builder, assert_no_violations, save_accessibility_report):
    page.goto('http://localhost:5000/new-page')
    page.wait_for_load_state('networkidle')
    
    results = axe_builder()
    save_accessibility_report('new_page', results)
    assert_no_violations(results)
```

### Monitoring and Metrics

Track accessibility metrics over time:
- **Violation count** per page (target: 0)
- **Critical/serious violations** (must be 0)
- **Test coverage** (% of pages tested)
- **Fix time** (time from detection to fix)

---

## Resources

### Tools

- **axe DevTools**: Browser extension for manual testing
- **WAVE**: Web accessibility evaluation tool
- **Lighthouse**: Automated accessibility audits
- **NVDA**: Free screen reader for testing (Windows)
- **VoiceOver**: Built-in screen reader (macOS/iOS)

### Documentation

- **WCAG 2.1**: https://www.w3.org/WAI/WCAG21/quickref/
- **axe-core Rules**: https://github.com/dequelabs/axe-core/blob/master/doc/rule-descriptions.md
- **ARIA Authoring Practices**: https://www.w3.org/WAI/ARIA/apg/
- **MDN Accessibility**: https://developer.mozilla.org/en-US/docs/Web/Accessibility

### Training

- **Web Accessibility by Google**: https://www.udacity.com/course/web-accessibility--ud891
- **Deque University**: https://dequeuniversity.com/
- **A11ycasts**: https://www.youtube.com/playlist?list=PLNYkxOF6rcICWx0C9LVWWVqvHlYJyqw7g

---

## Support

For accessibility questions or issues:
1. Check this documentation
2. Review axe-core rule documentation
3. Test with screen readers
4. Consult WCAG 2.1 guidelines
5. Contact the development team

**Remember**: Accessibility is not a feature—it's a requirement. Every user deserves equal access to Mina's functionality.
