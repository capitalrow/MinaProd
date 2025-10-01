# Keyboard Navigation Test Scripts

**WCAG 2.1 Level AA** | **Test Duration**: ~30 minutes

---

## Setup

1. **Disable mouse/trackpad** - Physically disconnect or use accessibility settings
2. **Clear browser cache** - Start fresh
3. **Use keyboard only** - No mouse, trackpad, or touch

---

## Test 1: Dashboard Flow (10 min)

### Expected Tab Order

```
1.  Skip link ("Skip to main content")
2.  Mina logo/home
3.  Dashboard nav link
4.  Live nav link  
5.  Meetings nav link
6.  Analytics nav link
7.  More dropdown button
8.  Menu button
9.  Start Live Transcription card
10. View All Sessions card
11. Upload Audio File button
12. System Analytics link
13. Export Data button
14. Settings button
15. [If sessions exist] View session button
16. [If sessions exist] Download session button
17. Footer status link
```

### Keyboard Test Script

| Action | Key | Expected Result | ✓ |
|--------|-----|-----------------|---|
| First focus | `Tab` | Skip link appears and receives focus | [ ] |
| Activate skip | `Enter` | Focus moves to main content | [ ] |
| Navigate nav | `Tab` × 6 | Cycles through nav items | [ ] |
| Open dropdown | `Enter` on More | Dropdown opens | [ ] |
| Navigate menu | `↓` | Highlights first item | [ ] |
| Select item | `Enter` | Navigates to page | [ ] |
| Close dropdown | `Esc` | Dropdown closes | [ ] |
| Navigate cards | `Tab` × 6 | Cycles through action cards | [ ] |
| Activate card | `Space` or `Enter` | Card action triggers | [ ] |
| Navigate table | `Tab` | Moves through action buttons | [ ] |
| Reverse navigate | `Shift+Tab` | Moves backwards | [ ] |

**Pass Criteria**:
- ✅ All elements receive focus in logical order
- ✅ Skip link works correctly
- ✅ Dropdowns open/close with keyboard
- ✅ All actions work with Enter/Space
- ✅ Shift+Tab reverses navigation

---

## Test 2: Live Recording Flow (8 min)

### Expected Tab Order

```
1.  Skip link
2.  Navigation (skip with skip link)
3.  Record button
4.  Clear transcript button
5.  Copy transcript button
6.  Download transcript button
7.  Language select
8.  Auto-scroll checkbox
9.  Speaker detection checkbox
```

### Keyboard Test Script

| Action | Key | Expected Result | ✓ |
|--------|-----|-----------------|---|
| Navigate to record | `Tab` × 3 | Record button focused | [ ] |
| Start recording | `Space` | Recording starts, button state changes | [ ] |
| Verify state | Screen reader | "Stop recording, pressed" announced | [ ] |
| Stop recording | `Space` | Recording stops, button state changes | [ ] |
| Clear transcript | `Tab` + `Enter` | Transcript cleared | [ ] |
| Copy transcript | `Tab` + `Enter` | Transcript copied | [ ] |
| Download | `Tab` + `Enter` | Download initiated | [ ] |
| Change language | `Tab` + `↓` | Language dropdown opens | [ ] |
| Select language | `↓` + `Enter` | Language selected | [ ] |
| Toggle checkbox | `Tab` + `Space` | Checkbox toggles | [ ] |
| Keyboard shortcut | `Ctrl+R` (or `Cmd+R`) | Toggles recording | [ ] |

**Pass Criteria**:
- ✅ Record button works with Space and Enter
- ✅ Button state (aria-pressed) updates correctly
- ✅ All action buttons keyboard accessible
- ✅ Form controls work with keyboard
- ✅ Keyboard shortcuts work

---

## Test 3: Modal Dialog Flow (5 min)

### Upload Modal Test

| Action | Key | Expected Result | ✓ |
|--------|-----|-----------------|---|
| Navigate to upload | `Tab` to card | Upload card focused | [ ] |
| Open modal | `Enter` | Modal opens, focus moves to modal | [ ] |
| Check focus trap | `Tab` × 10 | Focus stays within modal | [ ] |
| Navigate fields | `Tab` | Cycles: file → title → language → buttons | [ ] |
| Select file | `Enter` on file input | File picker opens | [ ] |
| Fill title | Type text | Text enters field | [ ] |
| Select language | `↓` on select | Options appear | [ ] |
| Submit | `Enter` on button | Form submits | [ ] |
| Close modal | `Esc` | Modal closes | [ ] |
| Focus return | After close | Focus returns to upload card | [ ] |

**Pass Criteria**:
- ✅ Focus moves to modal on open
- ✅ Focus trapped in modal (cannot Tab outside)
- ✅ All form fields keyboard accessible
- ✅ Escape closes modal
- ✅ Focus returns to trigger element

### Settings Modal Test

| Action | Key | Expected Result | ✓ |
|--------|-----|-----------------|---|
| Open settings | Click settings button | Modal opens | [ ] |
| Navigate controls | `Tab` | Cycles through form controls | [ ] |
| Adjust slider | `←` `→` | VAD sensitivity changes | [ ] |
| Toggle checkbox | `Space` | Checkbox toggles | [ ] |
| Save | `Enter` on Save | Settings saved, modal closes | [ ] |
| Cancel | `Esc` or Cancel button | Modal closes, no changes | [ ] |

**Pass Criteria**:
- ✅ Range slider works with arrow keys
- ✅ Checkboxes work with Space
- ✅ Save/cancel accessible via keyboard

---

## Test 4: Table Navigation (4 min)

### Sessions Table Test

| Action | Key | Expected Result | ✓ |
|--------|-----|-----------------|---|
| Navigate to table | `Tab` to first cell | Table row focused | [ ] |
| Navigate columns | `Tab` | Moves through action buttons | [ ] |
| Activate view | `Enter` on view button | Session detail opens | [ ] |
| Navigate back | Browser back or link | Returns to dashboard | [ ] |
| Download session | `Enter` on download | Download initiated | [ ] |

**Pass Criteria**:
- ✅ Table cells receive focus in logical order
- ✅ Action buttons work with Enter
- ✅ Table navigation doesn't trap focus

---

## Test 5: Dropdown Menus (3 min)

### More Dropdown Test

| Action | Key | Expected Result | ✓ |
|--------|-----|-----------------|---|
| Navigate to More | `Tab` to dropdown | More button focused | [ ] |
| Open dropdown | `Enter` or `Space` | Menu opens | [ ] |
| Navigate items | `↓` | Highlights next item | [ ] |
| Navigate up | `↑` | Highlights previous item | [ ] |
| Select item | `Enter` | Navigates to page | [ ] |
| Close dropdown | `Esc` | Menu closes | [ ] |
| Close by Tab | `Tab` outside | Menu closes | [ ] |

**Pass Criteria**:
- ✅ Enter/Space opens dropdown
- ✅ Arrow keys navigate items
- ✅ Enter selects item
- ✅ Escape closes dropdown

### User Menu Test

| Action | Key | Expected Result | ✓ |
|--------|-----|-----------------|---|
| Navigate to menu | `Tab` to menu button | Menu button focused | [ ] |
| Open menu | `Enter` | Menu opens | [ ] |
| Navigate sections | `↓` | Moves through menu items | [ ] |
| Select settings | `Enter` on Settings | Settings page opens | [ ] |

**Pass Criteria**:
- ✅ Menu accessible via keyboard
- ✅ All menu items keyboard accessible

---

## Common Issues Checklist

### Focus Management
- [ ] No invisible elements receive focus
- [ ] Focus indicators visible on all elements (3px outline minimum)
- [ ] Tab order follows visual layout (top→bottom, left→right)
- [ ] No keyboard traps (except intentional modal traps)
- [ ] Shift+Tab reverses correctly

### Interactive Controls
- [ ] Buttons work with Space and Enter
- [ ] Links work with Enter
- [ ] Checkboxes toggle with Space
- [ ] Radio buttons select with Space, navigate with arrows
- [ ] Select dropdowns open with Space/Enter, navigate with arrows

### Modals
- [ ] Focus moves to modal on open
- [ ] Focus trapped in modal
- [ ] Escape closes modal
- [ ] Focus returns to trigger on close

### Custom Components
- [ ] Dropdowns have keyboard support
- [ ] Tabs have keyboard support (if any)
- [ ] Sliders work with arrow keys
- [ ] Custom controls have ARIA roles

---

## Accessibility Quick Fixes

If you find issues during testing:

### Missing Focus Indicator
```css
button:focus, a:focus {
    outline: 3px solid var(--color-brand-400);
    outline-offset: 2px;
}
```

### Keyboard Trap
```javascript
// Trap focus in modal
if (isLastElement && event.key === 'Tab' && !event.shiftKey) {
    event.preventDefault();
    firstElement.focus();
}
```

### Missing ARIA
```html
<!-- Dropdown button -->
<button aria-expanded="false" aria-haspopup="true" aria-controls="menu-id">
    More
</button>

<!-- Toggle button -->
<button aria-pressed="false">
    Toggle
</button>
```

---

## Report Template

```markdown
## Keyboard Navigation Test Results

**Date**: [Date]
**Tester**: [Name]
**Browser**: [Browser + Version]

### Summary
- Total tests: 5
- Passed: ___
- Failed: ___

### Issues Found

#### Issue 1: [Title]
- **Severity**: Critical/Major/Minor
- **Location**: [Page/Component]
- **Expected**: [What should happen]
- **Actual**: [What happened]
- **Fix**: [Suggested solution]

### Overall Result
- ✅ Pass (all critical tests passed)
- 🟡 Conditional Pass (minor issues only)
- ❌ Fail (critical issues present)
```

---

## Best Practices Verified

- [ ] Skip link present and functional
- [ ] Logical tab order throughout
- [ ] Focus indicators visible (3px minimum)
- [ ] No keyboard traps
- [ ] Modal focus management correct
- [ ] Dropdown keyboard support
- [ ] All actions keyboard accessible
- [ ] Shift+Tab reverses correctly
- [ ] Custom components have keyboard support
- [ ] Keyboard shortcuts don't conflict with browser
