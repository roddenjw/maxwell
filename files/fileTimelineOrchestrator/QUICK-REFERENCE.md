# Timeline Orchestrator - Quick Reference Guide

## 📍 You Are Here

This is your **quick reference**. Use this to understand the lay of the land, then dive into the detailed documentation.

---

## 🎯 What Are We Building?

**Timeline Orchestrator** = A validation + teaching system for story timelines

**For**: Fantasy/Sci-Fi writers managing multiple POVs across complex stories

**Problem**: Writers lose track of causality, travel time, character presence across many events

**Solution**: 
1. Writers input story events with dates and dependencies
2. System validates timeline against physical/logical rules
3. System explains WHY violations matter to readers
4. Writers improve their craft while fixing their story

**Example**:
```
Writer: "Arya escapes King's Landing on Day 40"
System: "Wait - she was in Vale on Day 65 (900km away)"
        "That's impossible with horse travel (needs 11 days)"
        "Why this matters: Fantasy readers track distance subconsciously..."
        "Options: 1) Extend timeline 2) Use magic 3) Add travel scene..."
```

---

## 📁 What Files Do I Have?

| File | Purpose | Read Time | Claude Code Use |
|------|---------|-----------|-----------------|
| **README.md** | How to use all documents | 10 min | Read first, then reference |
| **TIMELINE-ORCHESTRATOR-SPEC.md** | Master spec with all features | 30 min | Your north star - reference constantly |
| **01-DATABASE-SCHEMA.md** | Prisma models and relationships | 15 min | Copy schema, run migrations |
| **02-BACKEND-SERVICE.md** | Validation service code | 20 min | Implement/refine service |
| **03-API-ROUTES.md** | REST API endpoints | 15 min | Implement routes |

**Total Read Time**: ~90 minutes

---

## 🚀 How to Use These Files

### With Claude Code - 4 Simple Steps

```
STEP 1: Read SPEC (30 min)
  ↓
STEP 2: Build Database (1 hour)
  "Use 01-DATABASE-SCHEMA.md to add these models to Prisma..."
  ↓
STEP 3: Build Service (2-3 hours)
  "Use 02-BACKEND-SERVICE.md to implement TimelineOrchestratorService..."
  ↓
STEP 4: Build Routes (1-2 hours)
  "Use 03-API-ROUTES.md to implement the 9 endpoints..."
  ↓
STEP 5: Build Components (3-4 hours)
  "Build React components for timeline visualization..."
  ↓
DONE ✓
```

---

## 🔑 Key Concepts

### Concept 1: The 5 Validators
These are the core of the system. Each detects one type of issue:

```
1. IMPOSSIBLE TRAVEL
   What: Character in Location A, then Location B too fast
   Example: 900km in 25 days (needs 11 days minimum)
   Severity: CRITICAL
   Teaching: "Readers track distance subconsciously"

2. DEPENDENCY VIOLATION
   What: Prerequisite event happens after dependent event
   Example: "Trial ends" before "Trial begins"
   Severity: CRITICAL
   Teaching: "Causality is sacred - cause before effect"

3. CHARACTER PRESENCE
   What: Character appears 0 or 1 time on timeline
   Example: Character created but never used
   Severity: MAJOR (0x) / MINOR (1x)
   Teaching: "Characters need 2+ events to feel real"

4. TIMING GAPS
   What: Large time gaps between events (>30 days)
   Example: Event Day 1, next event Day 100
   Severity: MINOR
   Teaching: "Readers notice gaps - explain them"

5. TEMPORAL PARADOXES
   What: Circular dependencies (A→B→C→A)
   Example: Event A depends on B, B on C, C on A
   Severity: CRITICAL
   Teaching: "This is logically impossible"
```

### Concept 2: Teaching-First Design
Every issue has three parts:

```javascript
{
  description: "What's wrong",
  suggestion: "How to fix (3-4 options)",
  teachingPoint: "Why it matters to readers + examples"
}
```

This is NOT "fix your writing" - it's "here's what readers experience when..."

### Concept 3: Timeline Data Structure
```
Project
  └── Characters (Robb, Arya, Tyrion)
      └── Events (15 total)
          ├── Event 1: "Robb crowned" (Day 1, Winterfell)
          ├── Event 2: "Robb marches" (Day 15, travel)
          └── Event 3: "Battle" (Day 50, Whispering Wood)
      └── Locations (4 total)
          ├── Winterfell (900km from King's Landing)
          ├── King's Landing
          ├── Casterly Rock (1200km from Winterfell)
          └── Whispering Wood
      └── Travel Legs (record of character movements)
          └── Robb: Winterfell→Battle site (15 days, horse)
      └── Issues (3 detected)
          ├── Arya travels 900km in 25 days ⚠️ CRITICAL
          ├── Tyrion lonely (1 event only) ⚠️ MINOR
          └── Gap before Day 100 ⚠️ MINOR
```

---

## 🎯 The 9 Features (Elevator Pitch)

| # | Feature | What Writer Can Do | Acceptance Criteria |
|---|---------|-------------------|-------------------|
| 1 | Event Management | Create/edit/delete timeline events | CRUD works, events sort by date |
| 2 | Location Management | Define story locations and distances | Can add locations, set distances |
| 3 | Travel Tracking | Record character movements | Can create travel legs with dates |
| 4 | Travel Rules | Customize world-specific travel speeds | Can edit speeds (horse, magic, etc) |
| 5 | Timeline Validation | Validate entire timeline at once | Detects all 5 issue types |
| 6 | Visual Timeline | See events in chronological order | Events display with characters/locations |
| 7 | Teaching System | Learn WHY issues matter | Every issue has teaching point |
| 8 | Issue Resolution | Mark issues as fixed | Can resolve issues, add notes |
| 9 | Data Retrieval | Get all timeline data efficiently | Single endpoint returns all data |

---

## 💻 Technology Stack (What You're Using)

```
Frontend:
  - React 18 (components)
  - TypeScript (types)
  - Tailwind CSS (styling)
  - Axios (API calls)

Backend:
  - Node.js (runtime)
  - Express (server)
  - TypeScript (types)
  - Prisma (database ORM)

Database:
  - SQLite (development)
  - PostgreSQL (production)
  - 6 models total

API:
  - REST endpoints
  - JSON request/response
  - Consistent error format
```

---

## 🎬 Example: Complete Data Flow

```
SCENARIO: Writer adds "Arya escapes King's Landing" event

1. Frontend UI: Writer fills form
   ├─ Name: "Arya escapes King's Landing"
   ├─ Date: 2024-01-40
   ├─ Character: Arya
   ├─ Location: King's Landing
   └─ Click: "Create Event"

2. API Call: POST /api/timeline/events
   {
     projectId: "proj-123",
     name: "Arya escapes",
     storyDate: "2024-01-40",
     characterIds: ["char-arya"],
     locationId: "loc-kings-landing"
   }

3. Backend: Event saved to database

4. Writer: Clicks "Validate Timeline"

5. API Call: POST /api/timeline/validate
   { projectId: "proj-123" }

6. Service Runs:
   ├─ checkImpossibleTravel()
   │  └─ Finds Arya was in Vale on Day 65 (900km away)
   │     "25 days for 900km is impossible with horse"
   │     Severity: CRITICAL
   │
   ├─ checkDependencyViolations()
   │  └─ No issues
   │
   ├─ checkCharacterPresence()
   │  └─ Arya has 2 events (OK)
   │
   ├─ checkTimingGaps()
   │  └─ Gap between Day 40 and Day 65 is 25 days (OK)
   │
   └─ checkParadoxes()
      └─ No cycles

7. API Response:
   {
     "issues": [
       {
         "type": "impossible_travel",
         "severity": "critical",
         "description": "Arya appears 900km away in 25 days",
         "suggestion": "1) Extend timeline 2) Use magic 3) Add travel",
         "teachingPoint": "Fantasy readers track distance..."
       }
     ]
   }

8. Frontend Displays:
   Timeline view shows:
   - Event card for "Arya escapes" 
   - RED BORDER (critical issue)
   - Issue details appear when expanded
   - Writer can mark resolved
```

---

## 🧪 Quick Test Case

**Setup**:
- Character: Aragorn
- Event 1: Day 1, Rivendell
- Event 2: Day 5, Moria (100km away)
- Travel time needed: 2 days minimum (horse)

**Validation**:
- Should detect: OK (5 days for 2-day journey is fine)
- No issue expected

---

**Setup**:
- Character: Arya
- Event 1: Day 40, King's Landing
- Event 2: Day 65, Winterfell (900km away)
- Travel time needed: 11 days minimum (horse)

**Validation**:
- Should detect: CRITICAL impossible travel
- Days available: 25
- Days needed: 11
- Status: ✓ Possible, but will flag if location distance set

**Setup**:
- Event A depends on Event B
- Event A: Day 50
- Event B: Day 100

**Validation**:
- Should detect: CRITICAL dependency violation
- Issue: B must happen before A
- Suggestion: Reorder events

---

## 🎓 How Claude Code Should Think

### When Building Database
```
"I'm creating tables to store:
- Story events with dates and relationships
- Physical locations with distances
- Character movements between locations
- Validation results with teaching points
- World-specific rules (how fast magic travel is)"
```

### When Building Service
```
"I'm checking 5 types of problems:
1. Can characters physically get where they are?
2. Do events depend on things that haven't happened?
3. Are characters developed (multiple events)?
4. Are time gaps explained or intentional?
5. Are there circular dependencies?

For EACH problem, I provide:
- Clear description
- Multiple fix options (not prescriptive)
- Why readers care about this"
```

### When Building API
```
"I'm providing endpoints to:
- Create/read/update/delete events, locations, travels
- Configure world rules (travel speeds)
- Validate entire timeline
- Get all data efficiently for visualization

Every response is consistent JSON format
with proper error handling"
```

### When Building Components
```
"I'm creating a timeline view that:
- Shows events chronologically
- Highlights issues with colors
- Lets writers filter by character
- Shows teaching points
- Lets writers mark issues resolved

Design is clean, responsive, uses Tailwind"
```

---

## 📊 Progress Checklist

### Phase 2A - Week by Week

**Week 1: Database Setup** (8 hours)
- [ ] Read SPEC (2h)
- [ ] Create Prisma schema from 01-DATABASE-SCHEMA.md (2h)
- [ ] Run migrations (1h)
- [ ] Verify all 6 models created (1h)
- [ ] Buffer (2h)

**Week 2: Backend Service** (8 hours)
- [ ] Implement TimelineOrchestratorService (4h)
- [ ] Implement all 5 validators (4h)

**Week 3: API Routes** (8 hours)
- [ ] Implement 9 REST endpoints (5h)
- [ ] Test endpoints with Postman (2h)
- [ ] Fix any issues (1h)

**Week 4: Frontend Components** (8 hours)
- [ ] Build main container (2h)
- [ ] Build visualization component (2h)
- [ ] Build controls and filters (2h)
- [ ] Style and polish (2h)

**Week 4: Integration & Testing** (8 hours)
- [ ] Connect frontend to API (2h)
- [ ] End-to-end testing (3h)
- [ ] Bug fixes (2h)
- [ ] Documentation (1h)

---

## 🔗 How Features Connect

```
EVENT MANAGEMENT (Feature 1)
    ↓
CHARACTER PRESENCE VALIDATION (Feature 5/Validator 3)
    ↓
LOCATION MANAGEMENT (Feature 2)
    ↓
TRAVEL TRACKING (Feature 3)
    ↓
IMPOSSIBLE TRAVEL VALIDATION (Feature 5/Validator 1)
    ↓
TRAVEL RULES (Feature 4)
    ↓
DEPENDENCY VALIDATION (Feature 5/Validator 2)
    ↓
VISUAL TIMELINE (Feature 6)
    ↓
ISSUE DISPLAY WITH TEACHING (Features 7+8)
    ↓
RESOLUTION TRACKING (Feature 8)
```

---

## 💡 Pro Tips for Claude Code

### Tip 1: Copy-Paste Ready Code
The markdown files contain code that's close to production-ready. Don't rewrite - build on it.

### Tip 2: Teaching Points First
When writing issue detection, write the teaching point FIRST. The teaching point explains why the issue matters, which guides your implementation.

### Tip 3: Multiple Solutions
Never suggest one fix. Always offer 3-4 options. This empowers writers.

### Tip 4: Test with Real Data
Don't just test with minimal data. Use the complete example from the SPEC (Robb, Arya, Tyrion timeline) to verify everything works.

### Tip 5: Performance Matters
Timeline validation should run in <500ms even with 1000+ events. Use efficient database queries.

---

## 🆘 If Claude Code Gets Stuck

### Stuck on Database?
→ Read 01-DATABASE-SCHEMA.md, focus on relationships diagram

### Stuck on Validation Logic?
→ Read 02-BACKEND-SERVICE.md, look at one validator at a time

### Stuck on API Design?
→ Read 03-API-ROUTES.md, copy endpoint structure

### Stuck on Components?
→ Read TIMELINE-ORCHESTRATOR-SPEC.md Feature 6 and 7, study examples

### Stuck on Teaching Points?
→ Ask: "What would a professional writer learn from this issue?"

---

## 📈 Success Looks Like

### After 1 Week
- [ ] Database tables exist and are empty
- [ ] Can manually insert test data

### After 2 Weeks
- [ ] Validation service runs and detects issues
- [ ] Issues have descriptions, suggestions, teaching points
- [ ] API endpoint returns validation results

### After 3 Weeks
- [ ] All 9 API routes work
- [ ] Can create/read/update/delete all entities
- [ ] Comprehensive data endpoint works

### After 4 Weeks
- [ ] Timeline visualization renders
- [ ] Issues display with colors
- [ ] Character filter works
- [ ] Writing teaching points visible
- [ ] End-to-end flow works

---

## 🎉 When You're Done

You've built a system that:
- ✅ Helps writers manage complex timelines
- ✅ Detects logical inconsistencies automatically
- ✅ Teaches about narrative principles
- ✅ Doesn't prescribe solutions (empowers writers)
- ✅ Scales to large projects

**This is genuinely innovative.** No other writing tool does this.

---

## 📞 Next Step

→ **Open README.md**
→ Follow the "How to Use With Claude Code" section
→ Start with database setup
→ Reference these specs as you build

**You've got this! 🚀**
