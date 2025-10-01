# Manual Accessibility Audit Guide - PG-9

**Version**: 1.0  
**Date**: October 1, 2025  
**WCAG Level**: 2.1 AA  
**Scope**: Dashboard, Live Recording, Meetings, Settings

---

## Overview

This guide provides step-by-step procedures for conducting a comprehensive manual accessibility audit. While automated testing (PG-7) catches ~40% of issues, manual testing is essential for complete WCAG 2.1 AA compliance.

**Audit Duration**: ~4-6 hours  
**Tools Required**: Screen reader (NVDA/VoiceOver), keyboard, browser dev tools

---

## Pre-Audit Setup

### 1. Testing Tools

**Screen Readers**:
- **Windows**: NVDA (free) - https://www.nvaccess.org/download/
- **macOS**: VoiceOver (built-in) - Cmd+F5 to enable
- **Backup**: JAWS (commercial) or ChromeVox (Chrome extension)

**Browsers**:
- Chrome/Edge (primary)
- Firefox (secondary)
- Safari (macOS only)

**Additional Tools**:
- Browser zoom: 200%, 400%
- High contrast mode (Windows/macOS)
- Color contrast checker: https://webaim.org/resources/contrastchecker/

### 2. Test Environment

1. Access app at production or staging URL
2. Create test user account if needed
3. Have sample meeting data ready
4. Clear browser cache before starting

---

## Audit Checklist

### ✅ Critical Tests (Must Pass)

- [ ] Screen reader can navigate entire site
- [ ] All functionality accessible via keyboard
- [ ] Skip navigation link works
- [ ] Forms have proper labels and error messages
- [ ] Tables have scope attributes
- [ ] Images have alt text
- [ ] Color contrast meets 4.5:1 ratio
- [ ] Page responds to 200% zoom
- [ ] Live regions announce updates

### ⚠️ Important Tests (Should Pass)

- [ ] Focus indicators visible on all elements
- [ ] Modal focus traps work correctly
- [ ] Dropdown menus have keyboard support
- [ ] Dynamic content announces properly
- [ ] Reduced motion respected
- [ ] High contrast mode works

### 📋 Enhanced Tests (Nice to Have)

- [ ] Keyboard shortcuts documented
- [ ] Touch targets 44×44px minimum
- [ ] Error recovery mechanisms clear
- [ ] Help text available

---

## Test Procedures

## 1. Screen Reader Testing (60 min)

### Test 1.1: Page Structure Navigation
**WCAG**: 1.3.1 (Level A), 2.4.1 (Level A)

**Procedure**:
1. Enable screen reader (NVDA: Ctrl+Alt+N, VoiceOver: Cmd+F5)
2. Press Tab to focus skip link
3. Verify announcement: "Skip to main content, link"
4. Press Enter to activate
5. Verify focus moves to main content

**Test Script**:
```
NVDA/VoiceOver: Tab → "Skip to main content, link"
Enter → Focus moves to main, announces "Dashboard, heading level 1"
```

**Pass Criteria**:
- ✅ Skip link announces correctly
- ✅ Activating skip link moves focus to main content
- ✅ Main heading announced after skip

### Test 1.2: Dashboard Navigation
**WCAG**: 2.4.3 (Level A), 2.4.6 (Level AA)

**Procedure**:
1. Navigate to dashboard
2. Use heading navigation (NVDA: H key, VoiceOver: Ctrl+Opt+Cmd+H)
3. Verify heading hierarchy (h1→h2→h3, no skipped levels)
4. Use landmarks (NVDA: D key, VoiceOver: Ctrl+Opt+U)
5. Verify navigation, main, footer landmarks present

**Test Script**:
```
H → "Dashboard, heading level 1"
H → "Quick Access, heading level 2"
H → "Recent Sessions, heading level 2"
D → "Navigation, navigation landmark"
D → "Main, main landmark"
```

**Pass Criteria**:
- ✅ Headings follow proper hierarchy
- ✅ All landmarks announce correctly
- ✅ No heading levels skipped

### Test 1.3: Interactive Elements
**WCAG**: 4.1.2 (Level A)

**Procedure**:
1. Tab through all interactive elements
2. Verify each element announces its role and state
3. Test buttons announce "button" or "toggle button"
4. Test links announce "link"
5. Test form controls announce label and type

**Test Script** (Dashboard):
```
Tab → "Start Live Transcription, link"
Tab → "View All Sessions, link"
Tab → "Upload Audio File, button"
Tab → "View details for [Session Name], button"
Tab → "Download [Session Name] transcript, button"
```

**Pass Criteria**:
- ✅ All elements announce role (button/link/etc)
- ✅ Icon-only buttons have descriptive labels
- ✅ No unlabeled interactive elements

### Test 1.4: Forms and Modals
**WCAG**: 3.3.2 (Level A), 4.1.2 (Level A)

**Procedure**:
1. Open upload modal
2. Verify modal announces as dialog
3. Tab through form fields
4. Verify each field announces label and type
5. Submit with errors
6. Verify errors announce

**Test Script**:
```
Click Upload → "Upload Audio File, dialog"
Tab → "Audio File, required, file upload button"
Tab → "Session Title, required, edit text"
Tab → "Language, combobox"
Submit → "Please select an audio file, error"
```

**Pass Criteria**:
- ✅ Modal announces "dialog"
- ✅ All fields have labels
- ✅ Required fields announce "required"
- ✅ Errors announce with aria-live

### Test 1.5: Live Transcription
**WCAG**: 4.1.3 (Level AA)

**Procedure**:
1. Navigate to live recording page
2. Focus record button
3. Verify announces "Start recording, toggle button, not pressed"
4. Activate button (Space/Enter)
5. Verify announces "Stop recording, toggle button, pressed"
6. Wait for transcript segment
7. Verify segment announces automatically

**Test Script**:
```
Tab to record button → "Start recording, toggle button, not pressed"
Enter → "Stop recording, toggle button, pressed"
[Wait for transcript] → "[Transcript text]" (announces automatically)
```

**Pass Criteria**:
- ✅ Button announces pressed state
- ✅ Label updates (Start/Stop)
- ✅ Transcript segments announce via live region
- ✅ Status updates announce ("Recording...")

### Test 1.6: Tables
**WCAG**: 1.3.1 (Level A)

**Procedure**:
1. Navigate to sessions table on dashboard
2. Enter table navigation mode (NVDA: Ctrl+Alt+Arrow, VoiceOver: Ctrl+Opt+Arrow)
3. Navigate to first cell
4. Verify header announces with data cell
5. Navigate to action buttons
6. Verify button labels announce

**Test Script**:
```
Navigate to table → "Table with 6 columns, [N] rows"
Down arrow → "Title, column header"
Down arrow → "Meeting Notes, Title column"
Right arrow → "Completed, Status column"
Right arrow → "View details for Meeting Notes, button"
```

**Pass Criteria**:
- ✅ Table announces row/column count
- ✅ Headers announce with scope="col"
- ✅ Cells announce with header association
- ✅ Action buttons have descriptive labels

---

## 2. Keyboard Navigation Testing (45 min)

### Test 2.1: Tab Order
**WCAG**: 2.4.3 (Level A)

**Procedure**:
1. Disable mouse/trackpad
2. Tab through entire page
3. Verify logical tab order (top→bottom, left→right)
4. Shift+Tab backwards
5. Verify no focus traps (except modals)

**Test Script** (Dashboard):
```
Tab 1: Skip link
Tab 2: Mina logo/home link
Tab 3: Dashboard nav link
Tab 4: Live nav link
Tab 5: Meetings nav link
Tab 6: Analytics nav link
Tab 7: More dropdown
Tab 8: Menu button
Tab 9: Start Live Transcription card
Tab 10: View All Sessions card
...
```

**Pass Criteria**:
- ✅ Tab order is logical and predictable
- ✅ No hidden elements receive focus
- ✅ No keyboard traps (except intentional modal traps)
- ✅ Shift+Tab works in reverse

### Test 2.2: Skip Navigation
**WCAG**: 2.4.1 (Level A)

**Procedure**:
1. Load page
2. Press Tab once
3. Verify skip link appears visually
4. Press Enter
5. Verify focus moves to main content (next Tab goes to first main element)

**Pass Criteria**:
- ✅ Skip link appears on first Tab
- ✅ Skip link visible when focused
- ✅ Enter activates skip
- ✅ Focus moves to main content

### Test 2.3: Interactive Controls
**WCAG**: 2.1.1 (Level A)

**Procedure**:
1. Test all buttons with Enter and Space
2. Test all links with Enter
3. Test dropdowns with Arrow keys
4. Test modals with Escape to close

**Test Script**:
```
Record Button:
- Space → Starts recording
- Enter → Starts recording
- Space (while recording) → Stops recording

Upload Modal:
- Tab to close button → Enter closes
- Escape key → Closes modal

Dropdown:
- Enter/Space → Opens menu
- Arrow Down → Navigates items
- Enter → Selects item
- Escape → Closes menu
```

**Pass Criteria**:
- ✅ All buttons work with Space and Enter
- ✅ Links work with Enter
- ✅ Dropdowns support Arrow keys
- ✅ Modals close with Escape

### Test 2.4: Modal Focus Management
**WCAG**: 2.4.3 (Level A)

**Procedure**:
1. Open upload modal
2. Verify focus moves to first element (close button or first field)
3. Tab through modal
4. Verify focus trapped in modal
5. Verify Tab wraps to first element
6. Close modal (Escape or close button)
7. Verify focus returns to trigger button

**Pass Criteria**:
- ✅ Focus moves into modal on open
- ✅ Focus trapped in modal (can't Tab outside)
- ✅ Focus returns to trigger on close
- ✅ Escape closes modal

### Test 2.5: Keyboard Shortcuts
**WCAG**: 2.1.4 (Level A)

**Procedure**:
1. Test Ctrl+R (or Cmd+R) for record toggle
2. Verify shortcut works
3. Verify shortcut doesn't interfere with browser shortcuts

**Pass Criteria**:
- ✅ Custom shortcuts documented
- ✅ Shortcuts don't override browser/OS shortcuts
- ✅ Shortcuts can be disabled if needed

---

## 3. Visual Accessibility Testing (30 min)

### Test 3.1: Color Contrast
**WCAG**: 1.4.3 (Level AA)

**Procedure**:
1. Use browser DevTools to inspect text
2. Check computed color values
3. Use WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
4. Verify 4.5:1 ratio for normal text
5. Verify 3:1 ratio for large text (18pt+ or 14pt+ bold)

**Elements to Test**:
```
Dashboard:
- Primary text (white on dark): _____________
- Secondary text (gray on dark): ___________
- Status badges (various): _________________
- Button text: ____________________________
- Link text: ______________________________
```

**Pass Criteria**:
- ✅ Normal text: 4.5:1 minimum
- ✅ Large text: 3:1 minimum
- ✅ Interactive element text: 4.5:1 minimum

### Test 3.2: Zoom and Reflow
**WCAG**: 1.4.4 (Level AA), 1.4.10 (Level AA)

**Procedure**:
1. Set browser zoom to 200% (Ctrl/Cmd + +)
2. Verify all content visible
3. Verify no horizontal scrolling (except data tables)
4. Test at 400% zoom
5. Verify content reflows correctly

**Test Script**:
```
100% zoom → Normal view
200% zoom → All content visible, vertical scroll only
400% zoom → Content readable, may need vertical/horizontal scroll
```

**Pass Criteria**:
- ✅ 200% zoom: All content accessible
- ✅ No text truncation or overlap
- ✅ Horizontal scrolling only for tables at 200%
- ✅ Layout doesn't break

### Test 3.3: High Contrast Mode
**WCAG**: 1.4.3 (Level AA)

**Procedure**:
1. Enable high contrast mode:
   - Windows: Alt+Shift+PrtScn
   - macOS: System Preferences → Accessibility → Display → Increase Contrast
2. Verify all UI elements visible
3. Verify focus indicators visible
4. Verify borders/separators visible

**Pass Criteria**:
- ✅ All text readable in high contrast
- ✅ Focus indicators visible
- ✅ Borders and separators present
- ✅ Icons/graphics distinguishable

### Test 3.4: Reduced Motion
**WCAG**: 2.3.3 (Level AAA - nice to have)

**Procedure**:
1. Enable reduced motion:
   - Windows: Settings → Ease of Access → Display → Show animations
   - macOS: System Preferences → Accessibility → Display → Reduce motion
2. Refresh page
3. Verify animations disabled or reduced
4. Verify functionality still works

**Pass Criteria**:
- ✅ Animations respect prefers-reduced-motion
- ✅ Essential motion preserved (e.g., loading states)
- ✅ No vestibular triggers (parallax, large animations)

---

## 4. Flow-Based Testing (60 min)

### Flow 1: Dashboard Access
**User Story**: As a keyboard user, I want to access dashboard features

1. [ ] Load dashboard with keyboard only
2. [ ] Use skip link to bypass navigation
3. [ ] Navigate to "Start Live Transcription" card
4. [ ] Activate with Enter/Space
5. [ ] Verify live page loads

**Pass Criteria**: Complete flow without mouse

### Flow 2: Live Recording
**User Story**: As a screen reader user, I want to record and view transcript

1. [ ] Navigate to live recording page
2. [ ] Hear all page elements announced
3. [ ] Find and activate record button
4. [ ] Hear "Stop recording, pressed" announcement
5. [ ] Hear transcript segments announce automatically
6. [ ] Find and activate stop button
7. [ ] Verify recording stopped announcement

**Pass Criteria**: Complete flow with screen reader only

### Flow 3: Upload Audio
**User Story**: As a keyboard user, I want to upload audio file

1. [ ] Navigate to dashboard
2. [ ] Tab to "Upload Audio File" card
3. [ ] Activate with Enter/Space
4. [ ] Modal opens, focus moves to modal
5. [ ] Tab through form fields
6. [ ] Fill required fields with keyboard
7. [ ] Submit or cancel with keyboard
8. [ ] Focus returns to trigger button

**Pass Criteria**: Complete flow without mouse, focus managed correctly

### Flow 4: View Session Details
**User Story**: As a screen reader user, I want to view session details

1. [ ] Navigate to dashboard
2. [ ] Navigate to sessions table
3. [ ] Find "View details" button via screen reader
4. [ ] Hear session name in button label
5. [ ] Activate button
6. [ ] Session detail page loads
7. [ ] Verify page structure announced

**Pass Criteria**: Screen reader provides sufficient context

---

## 5. Error and Edge Cases (30 min)

### Test 5.1: Form Validation Errors
**WCAG**: 3.3.1 (Level A), 3.3.3 (Level AA)

**Procedure**:
1. Open upload modal
2. Submit without filling required fields
3. Verify error messages appear
4. Verify errors announced to screen reader
5. Verify focus moves to first error or error summary
6. Verify errors have clear instructions

**Pass Criteria**:
- ✅ Errors announced via aria-live
- ✅ Error messages clear and specific
- ✅ Focus management on error
- ✅ Instructions for fixing errors

### Test 5.2: Recording Interruptions
**WCAG**: 4.1.2 (Level A)

**Procedure**:
1. Start recording on live page
2. Deny microphone permission
3. Verify error message appears
4. Verify ARIA state resets (aria-pressed="false")
5. Start recording again
6. Disconnect network
7. Verify recording stops gracefully
8. Verify ARIA state resets

**Pass Criteria**:
- ✅ Errors announced clearly
- ✅ ARIA states reset on errors
- ✅ Recovery path obvious

### Test 5.3: Session Timeout
**WCAG**: 2.2.1 (Level A)

**Procedure**:
1. Wait for session to approach timeout
2. Verify warning appears
3. Verify warning announced to screen reader
4. Verify option to extend session
5. Test extending session with keyboard

**Pass Criteria**:
- ✅ Timeout warning announced
- ✅ Sufficient time to respond (20 seconds minimum)
- ✅ Extend option keyboard accessible

---

## Test Reporting

### Issue Template

```markdown
## Issue: [Brief Description]

**WCAG Criterion**: [X.X.X Level A/AA/AAA]
**Severity**: Critical | Major | Minor
**Page/Component**: [URL or component name]

**Steps to Reproduce**:
1. 
2. 
3. 

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Screen Reader Output** (if applicable):
[What screen reader announced]

**Screenshot/Recording**:
[Attach if relevant]

**Recommended Fix**:
[Suggested solution]
```

### Pass/Fail Criteria

**Pass**: All critical and major issues resolved
**Conditional Pass**: Minor issues only, documented for future fixes
**Fail**: Any critical issues present

### Summary Report Template

```markdown
# Manual Accessibility Audit Report

**Date**: [Date]
**Auditor**: [Name]
**WCAG Level**: 2.1 AA

## Executive Summary
[Overall assessment]

## Test Coverage
- Screen Reader: ✅/❌
- Keyboard Navigation: ✅/❌
- Visual Accessibility: ✅/❌
- Flow Testing: ✅/❌

## Issues Found
- Critical: [N]
- Major: [N]
- Minor: [N]

## Recommendations
1. [Priority fix]
2. [Priority fix]
3. [Enhancement]

## Compliance Status
WCAG 2.1 Level AA: ✅ Pass / ❌ Fail / 🟡 Conditional
```

---

## Next Steps After Audit

1. **Document Issues**: File all findings using issue template
2. **Prioritize Fixes**: Critical → Major → Minor
3. **Create Tickets**: One ticket per issue or related group
4. **Retest**: After fixes, retest affected areas
5. **Update Documentation**: Update ACCESSIBILITY-AUDIT-FINDINGS.md

---

## Quick Reference

### NVDA Commands
- `Ctrl+Alt+N`: Start NVDA
- `H`: Next heading
- `D`: Next landmark
- `B`: Next button
- `K`: Next link
- `T`: Next table
- `Ctrl+Alt+Arrow`: Table navigation

### VoiceOver Commands
- `Cmd+F5`: Toggle VoiceOver
- `Ctrl+Opt+Cmd+H`: Next heading
- `Ctrl+Opt+U`: Rotor menu
- `Ctrl+Opt+Arrow`: Navigate elements
- `Ctrl+Opt+Space`: Activate

### Browser Shortcuts
- `Ctrl/Cmd + +`: Zoom in
- `Ctrl/Cmd + -`: Zoom out
- `Ctrl/Cmd + 0`: Reset zoom
- `F12`: DevTools
