# Timeline Orchestrator - Complete Documentation for Claude Code

## 📋 Overview

This documentation package contains everything Claude Code needs to develop the Timeline Orchestrator feature - a timeline validation and teaching system for fantasy/sci-fi writers with multi-POV narratives.

**Phase**: Phase 2A (Weeks 1-4)
**Complexity**: High (5 feature sets, complex validation logic)
**Status**: Ready for development

---

## 📁 File Structure

### 1. **TIMELINE-ORCHESTRATOR-SPEC.md** ⭐ START HERE
   - **Purpose**: Master specification document
   - **Contains**: Goals, architecture, features, examples, acceptance criteria
   - **For Claude Code**: Use this as your north star for what to build
   - **Time to Read**: 30 minutes
   - **Key Sections**:
     - Project Goals (what you're building and why)
     - Architecture Overview (how pieces fit together)
     - 9 Core Features (detailed with examples)
     - Acceptance Criteria (how to know it's done)
     - Testing Scenarios (real test cases)

### 2. **01-DATABASE-SCHEMA.md**
   - **Purpose**: Prisma schema with explanations
   - **Contains**: All models, relationships, design decisions
   - **For Claude Code**: Copy the schema additions and run migrations
   - **Time to Read**: 15 minutes
   - **Key Sections**:
     - Model definitions with field explanations
     - Relationships diagram
     - Example data structure
     - Migration commands

### 3. **02-BACKEND-SERVICE.md**
   - **Purpose**: Core validation service implementation
   - **Contains**: TimelineOrchestratorService with all validation logic
   - **For Claude Code**: This is nearly complete - refine and integrate
   - **Time to Read**: 20 minutes
   - **Key Sections**:
     - Full service code (copy-paste ready)
     - 5 validators (impossible travel, dependencies, presence, gaps, paradoxes)
     - Helper functions
     - Integration instructions

### 4. **03-API-ROUTES.md**
   - **Purpose**: Express REST routes
   - **Contains**: 9 API endpoints with handlers
   - **For Claude Code**: Implement these routes
   - **Time to Read**: 15 minutes
   - **Key Sections**:
     - 9 endpoint definitions with detailed explanations
     - Request/response examples
     - Error handling patterns
     - Comprehensive data endpoint

---

## 🚀 How to Use With Claude Code

### Step 1: Read the Specification (30 min)
1. Open `TIMELINE-ORCHESTRATOR-SPEC.md`
2. Focus on sections:
   - 🎯 Project Goals
   - 🏗️ Architecture Overview
   - ✨ Core Features (read first 3)
3. Understand: what problem you're solving

### Step 2: Set Up Database (1 hour)
1. Read: `01-DATABASE-SCHEMA.md` (the schema section)
2. Ask Claude Code to:
   ```
   Read 01-DATABASE-SCHEMA.md and add these Prisma models to 
   backend/prisma/schema.prisma:
   - TimelineEvent
   - Location
   - TravelLeg
   - TravelSpeedProfile
   - LocationDistance
   - TimelineIssue
   
   Then run the migration and verify all tables are created.
   ```

### Step 3: Build Backend Service (2-3 hours)
1. Read: `02-BACKEND-SERVICE.md`
2. Ask Claude Code to:
   ```
   Implement TimelineOrchestratorService in backend/src/services/analysis/
   
   Include all 5 validators:
   - checkImpossibleTravel()
   - checkDependencyViolations()
   - checkCharacterPresence()
   - checkTimingGaps()
   - checkParadoxes()
   
   Each validator should return TimelineIssue[] with detailed 
   descriptions and teaching points.
   ```

### Step 4: Build API Routes (1-2 hours)
1. Read: `03-API-ROUTES.md`
2. Ask Claude Code to:
   ```
   Implement Timeline REST routes in backend/src/routes/timeline.ts
   
   Include endpoints for:
   - POST /validate (main validation)
   - GET/POST /events (event CRUD)
   - GET/POST /locations (location CRUD)
   - GET/POST /travel-legs (travel CRUD)
   - GET/PUT /travel-speeds (world rules)
   - POST /location-distances (location matrix)
   - GET /comprehensive (all data at once)
   ```

### Step 5: Build Frontend Components (3-4 hours)
1. Use component architecture from SPEC
2. Ask Claude Code to build:
   ```
   React components in frontend/src/components/Timeline/:
   
   Main: TimelineOrchestrator.tsx
   - Container component
   - Loads data from API
   - Manages view modes and filters
   
   Display: TimelineVisualization.tsx
   - Renders events chronologically
   - Shows relationships between events
   
   Cards: TimelineEventCard.tsx
   - Individual event display
   - Shows issues inline
   - Expandable for details
   
   Issues: TimelineIssuesPanel.tsx
   - Lists all issues by severity
   - Color-coded by severity
   - Mark resolved functionality
   
   Teaching: TimelineTeachingPanel.tsx
   - Extracts learning moments
   - Shows patterns across timeline
   
   Controls: TimelineControls.tsx
   - Character filter
   - View mode selector
   - Validate button
   - Summary statistics
   ```

### Step 6: Integration (1 hour)
1. Connect routes to main backend
2. Import components in main app
3. Test end-to-end with real data

---

## 💡 Key Concepts for Claude Code

### Concept 1: Teaching-First Approach
Every issue should include:
- **Description**: What the problem is
- **Suggestion**: How to fix it (multiple options)
- **Teaching Point**: Why it matters to readers

❌ Bad: "Impossible travel"
✅ Good: "Character appears 900km away in 25 days, but needs 11 days minimum at horse speed. Fantasy readers subconsciously track travel time. If your character can teleport, readers will wonder why they don't use it elsewhere."

### Concept 2: Multi-POV Timeline Complexity
Fantasy/sci-fi writers struggle with:
- Multiple characters in different locations
- Days vs weeks of travel time
- Causality across POV switches
- Hidden character journeys (e.g., Arya's escape)

Timeline Orchestrator simplifies by:
- Centralizing all events in one view
- Validating against physical constraints
- Showing character presence/absence
- Detecting logical inconsistencies

### Concept 3: Validation as Teaching
The validation system IS the teaching system. When writers see:
> "Arya travels 900km in 25 days... Fantasy readers track distance subconsciously..."

They're learning about reader expectations while fixing their story.

### Concept 4: Non-Prescriptive Design
Never tell writers what to do. Instead:
- Flag the issue
- Suggest 3-4 options
- Explain the reader impact
- Let them choose

✅ "Options: 1) Extend timeline, 2) Use faster travel, 3) Add magic portal, 4) Hide journey"
❌ "You should extend the timeline to 40 days"

---

## 🎯 Priority for Claude Code

### Must Have (Week 1-2)
1. ✅ Database schema created
2. ✅ TimelineOrchestratorService validates impossible travel
3. ✅ API validation endpoint works
4. ✅ Frontend shows validation results

### Should Have (Week 2-4)
5. ✅ All 5 validators implemented
6. ✅ Visual timeline component
7. ✅ Character filter working
8. ✅ Issue resolution tracking

### Nice to Have (Future)
9. ⭕ Heat map visualizations
10. ⭕ Dependency graphs
11. ⭕ Advanced teaching system
12. ⭕ Collaboration features

---

## 📊 Data Flow Diagram

```
WRITER CREATES EVENT
        ↓
API POST /timeline/events
        ↓
Service validates:
  ├─ Check travel time
  ├─ Check dependencies
  ├─ Check presence
  ├─ Check gaps
  └─ Check paradoxes
        ↓
Issues stored in DB
        ↓
Frontend fetches /comprehensive
        ↓
TimelineOrchestrator displays:
  ├─ Visual timeline
  ├─ Issue badges on events
  ├─ Teaching points
  └─ Resolution options
        ↓
Writer marks issue resolved
        ↓
Issue stored as resolved
        ↓
Next validation notes it's fixed ✓
```

---

## 🔧 Common Implementation Patterns

### Pattern 1: Validation with Teaching
```typescript
if (travelDaysBetween < minDaysNeeded) {
  issues.push({
    type: 'impossible_travel',
    severity: 'critical',
    description: `Character travels ${distance}km in ${days} days`,
    suggestion: '3-4 specific options to fix',
    teachingPoint: 'Why reader psychology cares about this'
  });
}
```

### Pattern 2: Multiple Validation Checks
```typescript
async validateTimeline() {
  const issues = [];
  issues.push(...this.checkImpossibleTravel());
  issues.push(...this.checkDependencyViolations());
  issues.push(...this.checkCharacterPresence());
  issues.push(...this.checkTimingGaps());
  issues.push(...this.checkParadoxes());
  return this.deduplicateAndSort(issues);
}
```

### Pattern 3: Frontend Issue Display
```typescript
issues.map(issue => (
  <IssueCard
    severity={issue.severity}  // critical/major/minor
    description={issue.description}
    suggestion={issue.suggestion}
    teaching={issue.teachingPoint}
  />
))
```

---

## 🧪 Testing Strategy for Claude Code

### Unit Tests (Service Layer)
- Test each validator independently
- Mock database responses
- Verify issue types and severity
- Check teaching point content

### Integration Tests (API Layer)
- Create event → Validate → Check issue
- Test all endpoints
- Verify error handling
- Check response format

### E2E Tests (Frontend)
- Load timeline
- Filter by character
- Validate and see issues
- Mark issues resolved

### Real-World Test Case
Use the example from SPEC:
- Create Robb, Arya, Tyrion characters
- Create King's Landing (900km from Winterfell)
- Create events with tight travel windows
- Run validation
- Expect: impossible_travel issue with teaching point

---

## 📚 Reference Materials

### For Writing Teaching Points
- *Timeframe* by K.M. Weiland (pacing, structure)
- *Anatomy of Story* by John Truby (causality, structure)
- *The Anatomy of Story* by John Truby (narrative principles)

### For Fantasy Timeline Reference
- *Game of Thrones*: Multi-POV, complex timelines
- *Dune*: Intricate world rules about travel
- *Mistborn*: Clear magic system rules

### Technical References
- Prisma docs: https://www.prisma.io/docs
- React docs: https://react.dev
- TypeScript handbook: https://www.typescriptlang.org/docs

---

## 🎓 Learning Path for Claude Code

**If unfamiliar with timeline systems:**
1. Read a chapter of Game of Thrones
2. Notice how often travel is mentioned
3. Count days between scenes in different locations
4. Understand why readers care about timing

**If unfamiliar with validation systems:**
1. Think about linting (code quality checker)
2. Timeline Orchestrator is like a linter for story logic
3. Issues have: type, severity, fix suggestion, education

**If unfamiliar with teaching systems:**
1. Good teaching explains the "why" not just the "what"
2. Every issue is a teaching moment
3. Writer should learn something about craft from validation

---

## 📞 Asking Claude Code Effectively

### Good Prompts
```
"Implement TimelineOrchestratorService.checkImpossibleTravel(). 
It should detect when a character appears in two locations 
too close in time based on distance and travel speed. 
Reference the code in 02-BACKEND-SERVICE.md for structure."
```

### Less Helpful
```
"Make a timeline thing"
```

### Include Context
```
"We're building a validation system. The rule is: if character 
travels distance D at speed S, they need at least distance/speed 
days. If they're at two locations with less time than needed, 
flag as impossible_travel severity:critical. 
See 02-BACKEND-SERVICE.md line 120+ for details."
```

---

## ✅ Definition of Done

### Feature Complete When:
- [ ] All 9 features from SPEC have acceptance criteria met
- [ ] All 5 validators detect their issue type
- [ ] All teaching points are written and contextual
- [ ] API returns consistent error format
- [ ] Frontend displays issues with clarity
- [ ] Database migrations run cleanly
- [ ] No N+1 queries
- [ ] Code is TypeScript with proper types
- [ ] Components are responsive

### Ready for Testing When:
- [ ] Can create events with full timeline
- [ ] Can validate and get real issues
- [ ] Can filter by character
- [ ] Can see teaching points
- [ ] Can mark issues resolved
- [ ] Frontend and backend communicate properly

### Deployable When:
- [ ] All acceptance criteria met
- [ ] Code reviewed for edge cases
- [ ] Error handling covers bad data
- [ ] Performance acceptable (validation <500ms)
- [ ] Documentation updated

---

## 🎯 Success Criteria

### For Writers
- Writers understand WHY timeline consistency matters
- Writers can manage 20+ events across 5+ POVs
- Writers catch their own logic errors before publication
- Writers improve their temporal reasoning skills

### For Development
- Service validates 1000+ events in <500ms
- API response time <200ms
- Frontend loads in <1s
- Zero data loss in any operation
- >80% code test coverage

### For Product
- Writers validate timeline >3x per project
- Writers find teaching points valuable (survey)
- Writers complete timeline features (not abandoned)
- Feature adoption >60% of active users

---

## 🚀 Next Steps

1. **Today**: Read TIMELINE-ORCHESTRATOR-SPEC.md
2. **Hour 1**: Understand architecture and features
3. **Hour 2-3**: Ask Claude Code to implement database
4. **Hour 4-6**: Ask Claude Code to implement service
5. **Hour 7-8**: Ask Claude Code to implement API routes
6. **Hour 9-12**: Ask Claude Code to implement components
7. **Hour 13-16**: Integration and testing
8. **Hour 17-20**: Refinement and bug fixes

**Total Estimated Time**: 4 weeks for Phase 2A

---

## 📧 Questions?

If anything in this documentation is unclear:
1. Check the specific feature section in TIMELINE-ORCHESTRATOR-SPEC.md
2. Look at the examples provided
3. Review the acceptance criteria
4. Ask Claude Code to clarify or implement step-by-step

**This is a living document. Update as you build.**

---

**Ready to build something amazing. Let's go! 🚀**
