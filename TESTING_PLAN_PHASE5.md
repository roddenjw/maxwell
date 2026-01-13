# Phase 5 Testing Plan - Multi-Type Brainstorming

**Date:** 2026-01-13
**Phase:** 5 (Brainstorming & Ideation) - 80%
**Scope:** End-to-end testing of plot generation, location generation, and session history

---

## Test Environment

- **Backend:** http://localhost:8000
- **Frontend:** http://localhost:5173
- **Database:** SQLite (local)

---

## Test Cases

### 1. Character Generation (Baseline - Already Working)

**Status:** ✅ Previously tested and working

**Steps:**
1. Open Maxwell and create/select a manuscript
2. Open brainstorming modal (should default to Characters tab)
3. Fill in genre: "Epic Fantasy"
4. Fill in premise: "Young warrior must unite warring kingdoms to face ancient evil"
5. Enter OpenRouter API key
6. Set number of ideas: 3
7. Click "Generate Character Ideas"

**Expected Results:**
- Loading spinner appears
- Cost estimation shown (~$0.045 for 3 characters)
- After 10-30 seconds, 3 character ideas appear in Results tab
- Each character has: name, role, WANT, NEED, FLAW, STRENGTH, ARC
- Ideas can be selected and integrated to Codex

---

### 2. Plot Generation (New Feature)

**Priority:** HIGH

**Pre-requisites:**
- Backend running on port 8000
- Frontend running on port 5173
- Valid OpenRouter API key

**Steps:**
1. Open brainstorming modal
2. Click "📖 Plots" tab at top
3. Verify header changes to "Plot Brainstorming"
4. Fill in genre: "Thriller"
5. Fill in premise: "Detective tracks serial killer who leaves cryptic clues"
6. Enter OpenRouter API key
7. Set number of ideas: 5
8. Click "Generate Plot Ideas"

**Expected Results:**
- Loading spinner appears
- Cost estimation shown (~$0.060 for 5 plots)
- New session created with type: PLOT_BEAT
- After 10-30 seconds, 5 plot ideas appear in Results tab
- Each plot idea shows:
  - Title (e.g., "The Copycat's Game")
  - Central conflict description
  - Plot twist description
  - Subplot description
  - Complication description
- Ideas can be expanded/collapsed
- Ideas can be selected
- Cost per idea displayed (~$0.012)

**Error Cases to Test:**
- Missing genre → Error: "Please enter a genre"
- Missing premise → Error: "Please enter a story premise"
- Missing API key → Error: "Please enter your OpenRouter API key"
- Invalid API key → API error with clear message
- Network timeout → Retry button appears

---

### 3. Location Generation (New Feature)

**Priority:** HIGH

**Steps:**
1. Open brainstorming modal
2. Click "🌍 Locations" tab at top
3. Verify header changes to "Location Brainstorming"
4. Fill in genre: "Urban Fantasy"
5. Fill in premise: "Hidden magical world exists beneath modern city"
6. Enter OpenRouter API key
7. Set number of ideas: 3
8. Click "Generate Location Ideas"

**Expected Results:**
- Loading spinner appears
- Cost estimation shown (~$0.042 for 3 locations)
- New session created with type: WORLD
- After 10-30 seconds, 3 location ideas appear in Results tab
- Each location shows:
  - Title/name (e.g., "The Undercroft Markets")
  - Atmosphere description
  - Culture description
  - Geography description
  - History description
  - Secrets/hidden elements
- Ideas can be selected
- Ideas can be integrated to Codex as LOCATION entities

---

### 4. Multi-Type Tab Switching

**Priority:** HIGH

**Steps:**
1. Start in Characters tab, generate 2 characters
2. Switch to Plots tab
3. Verify new session is created (session ID changes)
4. Generate 3 plot ideas
5. Switch to Locations tab
6. Verify new session is created again
7. Generate 2 locations
8. Switch back to Characters tab
9. Verify you see a NEW empty session (not the original)

**Expected Results:**
- Each tab creates its own session
- Switching tabs doesn't lose data (data persists in store)
- Session IDs are different for each type
- Header and description update correctly
- Cost tracker resets for each new session
- Results tab shows ideas from current session only

---

### 5. Session History

**Priority:** MEDIUM

**Pre-requisites:**
- At least 3 sessions created (1 character, 1 plot, 1 location)

**Steps:**
1. Open brainstorming modal
2. Click "History" tab (rightmost workflow tab)
3. Verify all previous sessions are listed
4. Verify sessions are grouped by type (default view)
5. Click "By Date" button
6. Verify sessions are now sorted chronologically
7. Find a previous session with ideas
8. Click "Continue" button

**Expected Results:**
- History panel shows all previous sessions
- Each session card shows:
  - Type emoji and label (👤 Characters, 📖 Plots, 🌍 Locations)
  - Status badge (IN_PROGRESS, COMPLETED)
  - Relative timestamp ("2h ago", "3d ago")
  - Idea count ("5 ideas")
  - "Continue" button
- Grouping by type shows sessions under category headers
- Grouping by date shows newest first
- Clicking "Continue" loads that session and switches to Results tab
- Loaded session's ideas appear in Results tab
- Can select and integrate ideas from resumed session

**Edge Cases:**
- No sessions yet → Shows empty state with message
- Only one session → Still renders correctly
- Very old session (>7 days) → Shows formatted date

---

### 6. Idea Integration to Codex

**Priority:** HIGH

**Steps:**
1. Generate 3 character ideas
2. In Results tab, select 2 ideas (checkboxes)
3. Switch to right panel (Integration panel)
4. Verify selected count shows "2 selected"
5. Click "Integrate to Codex" button
6. Wait for success message

**Expected Results:**
- Integration panel shows selected count
- "Integrate to Codex" button is enabled
- After clicking, loading state appears
- Success toast: "2 ideas integrated to Codex"
- Ideas marked as integrated (checkmark icon)
- Integrated ideas have `integrated_to_codex: true` flag
- Opening Codex sidebar shows new CHARACTER entities

**Test for Plot Ideas:**
- Plot ideas should integrate to Outline (not Codex)
- Integration should create PlotBeat records
- Success message: "2 ideas integrated to Outline"

**Test for Location Ideas:**
- Location ideas should integrate to Codex as LOCATION type
- Success message: "2 ideas integrated to Codex"

---

### 7. Cost Tracking

**Priority:** MEDIUM

**Steps:**
1. Generate 5 character ideas (cost: ~$0.075)
2. Note the session cost in header
3. Generate 3 more characters (cost: ~$0.045)
4. Verify total session cost: ~$0.120

**Expected Results:**
- Cost tracker in header updates after each generation
- Cost accumulates across multiple generations in same session
- Cost resets when creating new session (switching types)
- Individual idea cost shown in idea metadata
- Token count shown in idea metadata

---

### 8. Performance & Error Handling

**Priority:** MEDIUM

**Scenarios to Test:**

**A. Large Batch Generation**
- Generate 10 ideas at once
- Should complete within 60 seconds
- Should not freeze UI
- Should handle rate limits gracefully

**B. Network Interruption**
- Start generation, disable network mid-request
- Should show error message
- Should not leave session in broken state
- Retry should work

**C. Invalid API Key**
- Enter fake API key
- Should get clear error: "Invalid API key" or similar
- Should not create idea records
- Should allow retry with correct key

**D. Concurrent Requests**
- Click generate button multiple times rapidly
- Should prevent duplicate requests (button disabled)
- Should not create duplicate sessions

**E. Browser Refresh During Generation**
- Start generation
- Refresh browser mid-request
- Session should persist
- Can retry generation

---

## Backend API Verification

### Check Endpoints Exist

**Character Generation:**
```bash
curl -X POST http://localhost:8000/api/brainstorming/sessions/{session_id}/generate/characters \
  -H "Content-Type: application/json" \
  -d '{"api_key":"test","genre":"Fantasy","story_premise":"Test","num_ideas":1}'
```

**Plot Generation:**
```bash
curl -X POST http://localhost:8000/api/brainstorming/sessions/{session_id}/generate/plots \
  -H "Content-Type: application/json" \
  -d '{"api_key":"test","genre":"Thriller","premise":"Test","num_ideas":1}'
```

**Location Generation:**
```bash
curl -X POST http://localhost:8000/api/brainstorming/sessions/{session_id}/generate/locations \
  -H "Content-Type: application/json" \
  -d '{"api_key":"test","genre":"Fantasy","premise":"Test","num_ideas":1}'
```

**Session List:**
```bash
curl http://localhost:8000/api/brainstorming/manuscripts/{manuscript_id}/sessions
```

---

## Known Issues & Limitations

1. **OpenRouter API Required:**
   - Cannot test without valid API key
   - Costs real money ($0.01-0.02 per generation)
   - Rate limits may apply

2. **AI Response Variability:**
   - AI may not always return valid JSON
   - Fallback parsing handles this
   - Some generations may fail randomly

3. **Session Management:**
   - Each tab switch creates new session (by design)
   - No way to "save and return" to same session
   - Session history shows all sessions (no filtering by status)

---

## Success Criteria

**Minimum Requirements (Must Pass):**
- ✅ Plot generation creates valid ideas with all required fields
- ✅ Location generation creates valid ideas with all required fields
- ✅ Tab switching works without errors
- ✅ Session history displays correctly
- ✅ Ideas can be integrated to Codex/Outline
- ✅ No console errors during normal workflow
- ✅ No backend errors during generation

**Nice-to-Have (Should Pass):**
- ⚠️ Cost tracking is accurate
- ⚠️ Error messages are clear and actionable
- ⚠️ Loading states are smooth
- ⚠️ Retry mechanisms work
- ⚠️ Performance is acceptable (< 60s per generation)

---

## Manual Testing Checklist

Use this checklist when manually testing the application:

### Pre-Flight Checks
- [ ] Backend running without errors
- [ ] Frontend dev server running
- [ ] No TypeScript errors in console
- [ ] Can access http://localhost:5173

### Character Generation (Baseline)
- [ ] Characters tab opens by default
- [ ] Can generate 3 characters
- [ ] Characters have all required fields
- [ ] Can integrate to Codex

### Plot Generation
- [ ] Plots tab accessible
- [ ] Header updates to "Plot Brainstorming"
- [ ] Can generate 5 plot ideas
- [ ] Plot ideas have conflict/twist/subplot/complication
- [ ] Cost estimation shows (~$0.012/idea)
- [ ] Ideas appear in Results tab
- [ ] Can select and integrate to Outline

### Location Generation
- [ ] Locations tab accessible
- [ ] Header updates to "Location Brainstorming"
- [ ] Can generate 3 location ideas
- [ ] Locations have atmosphere/culture/geography/history
- [ ] Can integrate to Codex as LOCATION

### Session History
- [ ] History tab shows all sessions
- [ ] Sessions grouped by type
- [ ] Can switch to "By Date" view
- [ ] "Continue" button loads previous session
- [ ] Results tab shows resumed session's ideas

### Multi-Type Workflow
- [ ] Switching between types creates new sessions
- [ ] Each session maintains its own ideas
- [ ] Cost tracker resets per session
- [ ] No data loss when switching tabs

### Error Handling
- [ ] Missing genre shows error
- [ ] Missing premise shows error
- [ ] Invalid API key shows clear error
- [ ] Network errors are handled gracefully

### Integration
- [ ] Character ideas integrate to Codex
- [ ] Plot ideas integrate to Outline
- [ ] Location ideas integrate to Codex
- [ ] Integrated ideas show checkmark
- [ ] Success toasts appear

---

## Regression Testing

After fixing any bugs, re-test:
- All character generation flows
- Multi-type tab switching
- Session persistence across refreshes
- Integration to Codex/Outline

---

## Bug Reporting Template

If bugs found, report with this format:

```
**Title:** [Brief description]

**Severity:** Critical / High / Medium / Low

**Steps to Reproduce:**
1. Step one
2. Step two
3. Expected vs actual

**Environment:**
- Browser: Chrome/Firefox/Safari
- OS: macOS/Windows/Linux
- Backend version: [git commit hash]

**Error Messages:**
[Console errors, backend logs, screenshots]

**Workaround:**
[If any]
```

---

## Test Results (To Be Filled)

**Date Tested:** _____________

**Tested By:** _____________

**Results:**
- [ ] All tests passed
- [ ] Some tests failed (see below)
- [ ] Blocked by: _____________

**Failed Tests:**
1. _____________
2. _____________

**Notes:**
_____________________________________________
_____________________________________________
