# Tasks Page - Manual Testing Guide

## Pre-Test Setup
1. Ensure the application is running (should be at `http://localhost:5000`)
2. Login with test credentials or create a new account
3. Navigate to `/dashboard/tasks`

---

## Test Suite 1: Task Creation (Meeting-less)

### Test 1.1: Create Basic Manual Task ✓
**Steps:**
1. Click "Create Task" button
2. Fill in title: "Test Task 1"
3. Select priority: "High"
4. Click "Create" or press Enter

**Expected Results:**
- Modal closes smoothly
- New task card appears in the list
- Task shows "High" priority badge
- Task title matches "Test Task 1"
- Checkbox is unchecked

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 1.2: Form Validation
**Steps:**
1. Click "Create Task"
2. Leave title field empty
3. Try to submit form

**Expected Results:**
- Form validation prevents submission
- Error message displayed or field highlighted
- Modal remains open

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 1.3: Keyboard Shortcuts
**Steps:**
1. Open create task modal
2. Fill in title "Keyboard Test"
3. Press Escape key

**Expected Results:**
- Modal closes without creating task
- No new task appears in list

**Status:** ⬜ Pass / ⬜ Fail

---

## Test Suite 2: Inline Editing

### Test 2.1: Inline Edit with Enter Key ✓
**Steps:**
1. Click on any task title to focus it
2. Clear existing text (Ctrl+A, Delete)
3. Type new title: "Edited Task Title"
4. Press Enter

**Expected Results:**
- Saving spinner appears briefly
- Green checkmark appears after save
- Title updates to "Edited Task Title"
- Focus leaves the field

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 2.2: Inline Edit Auto-Save on Blur ✓
**Steps:**
1. Click on task title to focus
2. Edit the title text
3. Click elsewhere on the page (blur the field)

**Expected Results:**
- After ~300ms debounce, save spinner appears
- Checkmark appears on successful save
- Title persists when you reload the page

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 2.3: Cancel Edit with Escape ✓
**Steps:**
1. Click on task title "Original Title"
2. Edit to "Changed Title"
3. Press Escape key

**Expected Results:**
- Edit is cancelled
- Title reverts to "Original Title"
- No save indicator appears

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 2.4: Inline Edit Persistence Across Reload
**Steps:**
1. Edit a task title to "Persistent Edit Test"
2. Wait for save checkmark
3. Reload the page (F5)

**Expected Results:**
- After reload, task still shows "Persistent Edit Test"
- Edit was saved to database

**Status:** ⬜ Pass / ⬜ Fail

---

## Test Suite 3: Checkbox Toggle & Completion

### Test 3.1: Mark Task Complete ✓
**Steps:**
1. Find an unchecked task
2. Click the checkbox

**Expected Results:**
- Checkbox becomes checked immediately (optimistic UI)
- Task may show completion animation (strikethrough, fade, etc.)
- State persists after page reload

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 3.2: Unmark Task ✓
**Steps:**
1. Find a checked/completed task
2. Click the checkbox again

**Expected Results:**
- Checkbox becomes unchecked
- Task returns to normal appearance
- State persists after reload

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 3.3: Completion Persistence
**Steps:**
1. Check a task to complete it
2. Wait 1 second for save
3. Reload the page
4. Find the same task

**Expected Results:**
- Task is still marked as complete
- Checkbox remains checked

**Status:** ⬜ Pass / ⬜ Fail

---

## Test Suite 4: WebSocket Real-Time Sync

### Test 4.1: WebSocket Preserves Inline Edits ⭐
**Critical Test**

**Steps:**
1. Open two browser tabs/windows with the tasks page
2. In Tab 1: Create a task "WebSocket Test"
3. In Tab 2: Verify the new task appears automatically
4. In Tab 1: Inline edit the title to "WebSocket Edited"
5. Wait for save checkmark
6. In Tab 2: Verify the title updates to "WebSocket Edited"

**Expected Results:**
- New task appears in Tab 2 without manual refresh
- Edited title syncs to Tab 2 in real-time
- Title shows "WebSocket Edited" NOT empty or "Untitled Task"

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 4.2: Checkbox Sync Across Tabs
**Steps:**
1. Open two tabs with tasks page
2. In Tab 1: Toggle a task checkbox
3. In Tab 2: Observe the same task

**Expected Results:**
- Checkbox state syncs to Tab 2 without refresh
- WebSocket broadcast preserves checkbox state

**Status:** ⬜ Pass / ⬜ Fail

---

## Test Suite 5: Offline & Cache Behavior

### Test 5.1: Page Load with Cache
**Steps:**
1. Visit tasks page (loads tasks into IndexedDB)
2. Open browser DevTools → Application → IndexedDB → TasksCache
3. Verify tasks are stored

**Expected Results:**
- TasksCache database exists
- Tasks are stored in 'tasks' object store
- Timestamps are recorded

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 5.2: Offline Task Creation (Optional)
**Steps:**
1. Open DevTools → Network → Enable "Offline" mode
2. Try to create a new task
3. Go back online

**Expected Results:**
- Task queues to IndexedDB syncQueue
- After going online, task syncs to server
- Task appears in list with server-assigned ID

**Status:** ⬜ Pass / ⬜ Fail (⬜ N/A if offline queueing not fully implemented)

---

## Test Suite 6: Meeting-Linked Tasks

### Test 6.1: Tasks from Meeting Transcription
**Steps:**
1. Complete a meeting with transcription
2. Verify tasks were extracted
3. Navigate to tasks page
4. Find meeting-linked tasks

**Expected Results:**
- Tasks extracted from meetings appear in list
- Tasks show meeting association/link
- Clicking task shows source meeting (if implemented)

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 6.2: Mixed Task List (Meeting + Manual)
**Steps:**
1. Ensure you have both:
   - Tasks created manually (no meeting_id)
   - Tasks from meeting transcription (has meeting_id)
2. View tasks page

**Expected Results:**
- All tasks display correctly regardless of meeting association
- No database query errors
- LEFT JOIN query supports both types

**Status:** ⬜ Pass / ⬜ Fail

---

## Test Suite 7: Error Handling

### Test 7.1: Network Error During Save
**Steps:**
1. Open DevTools → Network → Throttle to "Offline"
2. Try to create or edit a task
3. Go back online

**Expected Results:**
- Error indication shown (toast, notification, etc.)
- Task queues for retry (if offline support enabled)
- No data loss

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 7.2: Visual Feedback for Save Errors
**Steps:**
1. Create a task that will fail (simulate server error if possible)

**Expected Results:**
- Saving spinner shows during attempt
- Error state displayed (red indicator, error message)
- User informed of failure

**Status:** ⬜ Pass / ⬜ Fail

---

## Test Suite 8: UI/UX Polish

### Test 8.1: Loading States
**Steps:**
1. Load tasks page on slow network
2. Observe initial load state

**Expected Results:**
- Loading indicator shown while fetching
- Smooth transition to loaded state
- No layout shift or flicker

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 8.2: Empty State
**Steps:**
1. Create fresh account or clear all tasks
2. View tasks page with no tasks

**Expected Results:**
- Pleasant empty state message
- Clear call-to-action to create first task
- No errors or blank screen

**Status:** ⬜ Pass / ⬜ Fail

---

### Test 8.3: Animations & Transitions
**Steps:**
1. Create multiple tasks
2. Toggle checkboxes
3. Edit task titles

**Expected Results:**
- Smooth animations (slide-in, fade, etc.)
- No janky or abrupt transitions
- CROWN⁴ event sequencing feels natural

**Status:** ⬜ Pass / ⬜ Fail

---

## Browser Console Check

### Test 9.1: No Console Errors
**Steps:**
1. Open DevTools → Console
2. Perform all above tests
3. Monitor for errors

**Expected Results:**
- No JavaScript errors
- No failed network requests (except intentional offline tests)
- Clean console output

**Status:** ⬜ Pass / ⬜ Fail

---

## Test Summary

**Total Tests:** 22
**Passed:** ___
**Failed:** ___
**N/A:** ___
**Success Rate:** ___%

---

## Critical Tests (Must Pass)
- [ ] Test 1.1: Create Basic Manual Task
- [ ] Test 2.1: Inline Edit with Enter Key
- [ ] Test 2.4: Inline Edit Persistence
- [ ] Test 3.1: Mark Task Complete
- [ ] Test 4.1: WebSocket Preserves Inline Edits ⭐⭐⭐
- [ ] Test 6.2: Mixed Task List (Meeting + Manual)

---

## Notes & Issues Found
```
[Add any bugs, issues, or observations here]




```

---

## Tested By: ________________
## Date: ________________
## Browser: ________________
## Application Version: ________________
