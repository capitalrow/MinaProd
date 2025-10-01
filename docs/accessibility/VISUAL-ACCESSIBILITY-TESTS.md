# Visual Accessibility Tests

**WCAG 2.1 Level AA** | **Test Duration**: ~25 minutes

---

## Test 1: Color Contrast (10 min)

### WCAG Requirements
- **Normal text** (< 18pt): 4.5:1 minimum
- **Large text** (≥ 18pt or ≥ 14pt bold): 3:1 minimum  
- **UI components**: 3:1 minimum

### Tools
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Browser DevTools (Inspect → Computed → Color)
- Chrome DevTools Contrast Ratio indicator

### Test Procedure

1. **Inspect text colors** using DevTools
2. **Copy color values** (foreground + background)
3. **Test in contrast checker**
4. **Record results** below

### Elements to Test

#### Dashboard Page

| Element | Foreground | Background | Ratio | Pass/Fail |
|---------|------------|------------|-------|-----------|
| Primary heading (h1) | `#ffffff` | `#0a0e14` | ___ : 1 | [ ] |
| Body text | `#e0e6ed` | `#0a0e14` | ___ : 1 | [ ] |
| Secondary text | `#8b95a5` | `#0a0e14` | ___ : 1 | [ ] |
| Link text | `#60a5fa` | `#0a0e14` | ___ : 1 | [ ] |
| Button text (primary) | `#ffffff` | `#2563eb` | ___ : 1 | [ ] |
| Button text (secondary) | `#e0e6ed` | `#1e293b` | ___ : 1 | [ ] |
| Success badge | `#ffffff` | `#10b981` | ___ : 1 | [ ] |
| Warning badge | `#0a0e14` | `#f59e0b` | ___ : 1 | [ ] |
| Error badge | `#ffffff` | `#ef4444` | ___ : 1 | [ ] |

#### Glass UI Elements

| Element | Foreground | Background | Ratio | Pass/Fail |
|---------|------------|------------|-------|-----------|
| Card text | `#e0e6ed` | `rgba(30,41,59,0.7)` | ___ : 1 | [ ] |
| Modal text | `#e0e6ed` | `rgba(15,23,42,0.95)` | ___ : 1 | [ ] |
| Tooltip text | `#ffffff` | `#1e293b` | ___ : 1 | [ ] |

#### Interactive States

| Element | Foreground | Background | Ratio | Pass/Fail |
|---------|------------|------------|-------|-----------|
| Button hover | `#ffffff` | `#1d4ed8` | ___ : 1 | [ ] |
| Link hover | `#93c5fd` | `#0a0e14` | ___ : 1 | [ ] |
| Focus indicator | `#60a5fa` | `#0a0e14` | ___ : 1 | [ ] |
| Disabled text | `#64748b` | `#0a0e14` | ___ : 1 | [ ] |

**Pass Criteria**:
- ✅ All normal text: ≥ 4.5:1
- ✅ All large text: ≥ 3:1
- ✅ UI components: ≥ 3:1
- ✅ No failures on primary content

**Common Fixes**:
```css
/* Insufficient contrast fix */
.text-muted {
    color: #a0aec0; /* Instead of #8b95a5 */
}

/* Disabled state should still meet 3:1 */
button:disabled {
    color: #94a3b8;
    opacity: 0.7;
}
```

---

## Test 2: Zoom and Reflow (8 min)

### WCAG Requirements
- **200% zoom**: All content visible, no loss of functionality
- **400% zoom**: Content readable (horizontal scroll acceptable)
- **No overlapping text** at any zoom level

### Test Procedure

1. **Set browser zoom** (Ctrl/Cmd + +)
2. **Test at each level**: 100%, 200%, 400%
3. **Check for issues**: text overlap, truncation, broken layout
4. **Test scrolling**: vertical only at 200% (except tables)

### 200% Zoom Test

| Page/Component | Layout | Text | Scroll | Functionality | Pass/Fail |
|----------------|--------|------|--------|---------------|-----------|
| Dashboard | [ ] | [ ] | [ ] | [ ] | [ ] |
| Live recording | [ ] | [ ] | [ ] | [ ] | [ ] |
| Sessions table | [ ] | [ ] | [ ] | [ ] | [ ] |
| Upload modal | [ ] | [ ] | [ ] | [ ] | [ ] |
| Settings | [ ] | [ ] | [ ] | [ ] | [ ] |
| Navigation | [ ] | [ ] | [ ] | [ ] | [ ] |

**Check for**:
- [ ] No text truncation or cut-off
- [ ] No overlapping elements
- [ ] All buttons/links clickable
- [ ] Vertical scroll only (except tables)
- [ ] No content hidden off-screen

### 400% Zoom Test

| Page/Component | Readable | Usable | Pass/Fail |
|----------------|----------|--------|-----------|
| Dashboard | [ ] | [ ] | [ ] |
| Live recording | [ ] | [ ] | [ ] |
| Forms | [ ] | [ ] | [ ] |
| Modals | [ ] | [ ] | [ ] |

**Check for**:
- [ ] Text remains readable
- [ ] Core functionality works
- [ ] No broken layouts (some issues acceptable)

**Pass Criteria**:
- ✅ 200% zoom: Perfect layout, vertical scroll only
- ✅ 400% zoom: Readable and functional
- ✅ No text truncation at any level
- ✅ All interactive elements accessible

**Common Issues**:
```css
/* Fix: Text overflow */
.card-title {
    overflow-wrap: break-word;
    word-wrap: break-word;
}

/* Fix: Container doesn't reflow */
.container {
    max-width: 100%;
    overflow-x: auto;
}

/* Fix: Fixed widths break at zoom */
.sidebar {
    width: 300px; /* Bad */
    width: min(300px, 30vw); /* Good */
}
```

---

## Test 3: High Contrast Mode (4 min)

### Platform Setup

**Windows 10/11**:
1. Press `Alt + Shift + PrtScn`
2. Or: Settings → Ease of Access → High Contrast
3. Select "High Contrast Black" theme

**macOS**:
1. System Preferences → Accessibility → Display
2. Enable "Increase Contrast"

**Browser Extension** (fallback):
- Chrome: "High Contrast" extension
- Firefox: "High Contrast Mode" extension

### Test Checklist

| Element | Visible | Borders | Focus | Pass/Fail |
|---------|---------|---------|-------|-----------|
| Text | [ ] | N/A | N/A | [ ] |
| Headings | [ ] | N/A | N/A | [ ] |
| Links | [ ] | [ ] | [ ] | [ ] |
| Buttons | [ ] | [ ] | [ ] | [ ] |
| Form inputs | [ ] | [ ] | [ ] | [ ] |
| Cards | N/A | [ ] | N/A | [ ] |
| Modals | N/A | [ ] | N/A | [ ] |
| Tables | [ ] | [ ] | N/A | [ ] |
| Icons | [ ] | N/A | N/A | [ ] |
| Focus indicators | N/A | N/A | [ ] | [ ] |
| Separators | N/A | [ ] | N/A | [ ] |

**Pass Criteria**:
- ✅ All text clearly visible
- ✅ Focus indicators visible (3px minimum)
- ✅ Borders/separators present
- ✅ Interactive elements distinguishable
- ✅ No reliance on color alone

**Common Issues**:
```css
/* Fix: Borders disappear in high contrast */
.card {
    border: 1px solid transparent;
    /* Windows high contrast will force visible border */
}

/* Fix: Focus indicator not visible */
button:focus {
    outline: 3px solid;
    /* High contrast mode will use system color */
}

/* Fix: Icons disappear */
.icon {
    fill: currentColor;
    /* Inherits text color in high contrast */
}
```

---

## Test 4: Reduced Motion (3 min)

### WCAG Requirements
- **Respect user preference** for reduced motion
- **Disable non-essential animations**
- **Preserve essential motion** (loading states, alerts)

### Platform Setup

**Windows 10/11**:
1. Settings → Ease of Access → Display
2. Turn OFF "Show animations in Windows"

**macOS**:
1. System Preferences → Accessibility → Display
2. Enable "Reduce motion"

**Browser DevTools** (simulate):
1. Open DevTools
2. Cmd/Ctrl + Shift + P → "Emulate CSS prefers-reduced-motion"

### Test Checklist

| Animation Type | Disabled? | Functionality OK? | Pass/Fail |
|----------------|-----------|-------------------|-----------|
| Page transitions | [ ] | [ ] | [ ] |
| Hover effects | [ ] | [ ] | [ ] |
| Modal animations | [ ] | [ ] | [ ] |
| Loading spinners | [ ] Keep | [ ] | [ ] |
| Scroll animations | [ ] | [ ] | [ ] |
| Toast notifications | [ ] | [ ] | [ ] |
| Parallax effects | [ ] | [ ] | [ ] |
| Audio visualizer | [ ] | [ ] | [ ] |

**Essential Motion** (should remain):
- [ ] Loading indicators
- [ ] Focus highlights
- [ ] Status changes (error→success)

**Pass Criteria**:
- ✅ Non-essential animations disabled
- ✅ Essential motion preserved
- ✅ No functionality lost
- ✅ Transitions instant or < 200ms

**CSS Implementation**:
```css
/* Respect reduced motion preference */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
    
    /* Keep essential motion */
    .loading-spinner,
    .status-indicator {
        animation-duration: inherit;
    }
}
```

---

## Test 5: Focus Indicators (5 min)

### WCAG Requirements
- **Visible focus**: 3px minimum outline or equivalent
- **Contrast**: 3:1 against adjacent colors
- **No reliance on color alone**: Shape or size change required

### Test Procedure

1. **Tab through page** with keyboard
2. **Observe focus indicator** on each element
3. **Measure outline width** (DevTools)
4. **Check contrast** against background

### Focus Indicator Checklist

| Element | Visible? | Size (px) | Contrast | Color/Shape | Pass/Fail |
|---------|----------|-----------|----------|-------------|-----------|
| Links | [ ] | ___ | ___ : 1 | [ ] | [ ] |
| Buttons | [ ] | ___ | ___ : 1 | [ ] | [ ] |
| Form inputs | [ ] | ___ | ___ : 1 | [ ] | [ ] |
| Cards (clickable) | [ ] | ___ | ___ : 1 | [ ] | [ ] |
| Dropdown triggers | [ ] | ___ | ___ : 1 | [ ] | [ ] |
| Table cells | [ ] | ___ | ___ : 1 | [ ] | [ ] |
| Custom components | [ ] | ___ | ___ : 1 | [ ] | [ ] |

**Pass Criteria**:
- ✅ Focus visible on ALL interactive elements
- ✅ Outline ≥ 3px or equivalent visual change
- ✅ Contrast ≥ 3:1 against background
- ✅ Not hidden by other elements

**Common Issues**:
```css
/* Fix: No focus indicator */
button {
    outline: none; /* Bad! */
}
button:focus {
    outline: 3px solid var(--color-brand-500);
    outline-offset: 2px;
}

/* Fix: Low contrast outline */
a:focus {
    outline-color: #60a5fa; /* Good: High contrast */
}

/* Fix: Hidden by z-index */
*:focus {
    position: relative;
    z-index: 1;
}
```

---

## Issue Severity Guide

### Critical (Must Fix)
- Contrast ratio < 3:1 on primary text
- Focus indicators missing
- Content not visible at 200% zoom
- High contrast mode unusable

### Major (Should Fix)
- Contrast ratio 3:1-4.5:1 on normal text
- Focus indicators barely visible
- Minor layout issues at 200% zoom
- Some animations not disabled with reduced motion

### Minor (Nice to Fix)
- Contrast ratio < 3:1 on decorative elements
- Focus indicators could be more prominent
- Minor reflow issues at 400% zoom
- Non-essential animations remain with reduced motion

---

## Test Report Template

```markdown
## Visual Accessibility Test Results

**Date**: [Date]
**Tester**: [Name]
**Browser**: [Browser + Version]
**OS**: [Operating System]

### Test Summary

| Test | Pass | Fail | Issues |
|------|------|------|--------|
| Color Contrast | [ ] | [ ] | ___ |
| 200% Zoom | [ ] | [ ] | ___ |
| 400% Zoom | [ ] | [ ] | ___ |
| High Contrast | [ ] | [ ] | ___ |
| Reduced Motion | [ ] | [ ] | ___ |
| Focus Indicators | [ ] | [ ] | ___ |

### Critical Issues

1. **[Issue Title]**
   - Element: [Element name/selector]
   - Expected: [Requirement]
   - Actual: [What was found]
   - Fix: [Recommended solution]

### Compliance Status

- WCAG 1.4.3 (Contrast): ✅/❌
- WCAG 1.4.4 (Resize Text): ✅/❌
- WCAG 1.4.10 (Reflow): ✅/❌
- WCAG 2.4.7 (Focus Visible): ✅/❌

**Overall**: ✅ Pass / 🟡 Conditional / ❌ Fail
```
