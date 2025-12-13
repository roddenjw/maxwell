# Timeline Orchestrator - Feature Specification

**Status**: Ready for Claude Code Development
**Priority**: Phase 2A (Weeks 1-4)
**Target Users**: Fantasy/Sci-Fi writers with multi-POV timelines

---

## 🎯 Project Goals

### Primary Goal
Create a **timeline validation and teaching system** that helps fantasy/sci-fi writers with multi-POV narratives detect logical inconsistencies, travel impossibilities, and temporal paradoxes while teaching them how professional writers handle timeline complexity.

### Key Outcomes
- Writers can input story events and validate them against physical/logical constraints
- System flags impossible travel, broken causality, and paradoxes
- Every issue includes a teaching point explaining WHY it matters to readers
- Visual timeline makes complex multi-POV stories manageable
- Writers improve understanding of temporal coherence and story structure

---

## 🏗️ Architecture Overview

```
FRONTEND (React)
├── TimelineOrchestrator (main container)
├── TimelineVisualization (visual timeline view)
├── TimelineEventCard (individual events)
├── TimelineIssuesPanel (validation results)
├── TimelineTeachingPanel (learning moments)
├── TimelineControls (filters & actions)
└── TimelineEventForm (create/edit events)

↓ (REST API via axios)

BACKEND (Node.js/Express)
├── POST /api/timeline/validate
├── GET/POST /api/timeline/events
├── GET/POST /api/timeline/locations
├── GET/POST /api/timeline/travel-legs
├── GET/POST /api/timeline/travel-speeds
└── GET /api/timeline/comprehensive

↓

SERVICES (TypeScript)
├── TimelineOrchestratorService
│   ├── validateTimeline()
│   ├── checkImpossibleTravel()
│   ├── checkDependencyViolations()
│   ├── checkCharacterPresence()
│   ├── checkTimingGaps()
│   └── checkParadoxes()
└── TimelineDataService

↓

DATABASE (Prisma + SQLite)
├── TimelineEvent
├── Location
├── TravelLeg
├── TravelSpeedProfile
├── LocationDistance
└── TimelineIssue
```

### Data Flow Example

```
User writes event: "Arya escapes King's Landing on Day 40"
         ↓
API POST /api/timeline/events
         ↓
Service checks: Is Arya already somewhere 900km away?
              Did she have time to travel there?
              Are there recorded travel legs?
         ↓
System detects: CRITICAL - impossible travel (900km in 25 days)
         ↓
Returns issue with:
  - Description: "Character appears in two locations..."
  - Suggestion: "Options: 1) Change dates, 2) Explain magic..."
  - Teaching: "Fantasy readers track travel subconsciously..."
         ↓
Frontend displays issue inline with event
```

---

## 📊 Database Schema

### Core Models

```prisma
TimelineEvent
├── id (UUID)
├── projectId (FK)
├── name (string) - "Robb crowned king"
├── description (string) - optional
├── storyDate (DateTime) - when event happens in story
├── eventType (string) - character_action | world_event | revelation | travel | meeting
├── characterIds (string[]) - JSON array of character IDs
├── locationId (FK) - optional
├── prerequisiteIds (string[]) - events that must happen first
├── narrativeImportance (0-1) - for teaching priority
└── notes (string) - writer's notes

Location
├── id (UUID)
├── projectId (FK)
├── name (string) - "King's Landing"
├── description (string)
├── travelDistanceKm (float) - optional
└── knownTravelMethods (string[]) - ["horse", "magic_portal"]

TravelLeg
├── id (UUID)
├── projectId (FK)
├── characterId (FK)
├── fromLocationId (FK)
├── toLocationId (FK)
├── departDate (DateTime)
├── arrivalDate (DateTime)
├── travelMethod (string) - "horse", "carriage", "sailing", etc.
├── estimatedDays (int)
└── notes (string) - "Took mountain pass to avoid patrol"

TravelSpeedProfile
├── id (UUID)
├── projectId (FK)
├── walking (float) - 40 km/day
├── horse (float) - 80 km/day
├── carriage (float) - 60 km/day
├── sailing (float) - 150 km/day
├── flying (float) - 200 km/day
├── teleportation (float) - 999999 (instant)
├── custom1Name/Speed
├── custom2Name/Speed
└── rules (string) - "Horses need 8 hours rest per day"

LocationDistance
├── projectId + fromLocationId + toLocationId (unique)
├── distanceKm (float)
└── notes (string) - "Mountain pass, longer but safer"

TimelineIssue
├── id (UUID)
├── projectId (FK)
├── issueType (enum) - impossible_travel | dependency_violation | character_presence | timing_gap | paradox
├── severity (enum) - critical | major | minor
├── description (string)
├── suggestion (string)
├── teachingPoint (string)
├── affectedEventIds (string[])
├── affectedCharacterId (string)
├── isResolved (boolean)
└── resolutionNotes (string)
```

---

## ✨ Core Features

### Feature 1: Timeline Event Management

**Goal**: Writers can create, view, edit, and delete story events with proper dating and dependencies.

**Acceptance Criteria**:
- [ ] Users can create new timeline events with: name, date, type, characters, location, dependencies
- [ ] Events display in chronological order
- [ ] Users can edit event details
- [ ] Users can delete events
- [ ] Event form includes helpful placeholders for each field
- [ ] Date picker ensures dates are valid
- [ ] Character selection is multi-select from project characters
- [ ] Prerequisite selection shows other events as dropdown

**Examples**:

```javascript
// Create Event
POST /api/timeline/events
{
  "projectId": "proj-123",
  "name": "Robb crowned king",
  "storyDate": "2024-01-15",
  "eventType": "world_event",
  "characterIds": ["char-robb", "char-catelyn"],
  "locationId": "loc-winterfell",
  "narrativeImportance": 0.9,
  "notes": "Pivotal moment - sets entire war in motion"
}

// Response
{
  "success": true,
  "data": {
    "id": "event-001",
    "projectId": "proj-123",
    "name": "Robb crowned king",
    // ... other fields
    "createdAt": "2024-01-01T10:00:00Z"
  }
}
```

---

### Feature 2: Location Management

**Goal**: Writers define story locations and distances between them for travel validation.

**Acceptance Criteria**:
- [ ] Users can create locations with name and description
- [ ] Users can set travel methods available from each location
- [ ] Users can view all locations in a project
- [ ] Locations can be edited
- [ ] Locations can be deleted (with confirmation if used in events)
- [ ] Location list shows event count for each location
- [ ] Distance matrix can be viewed/edited (origin → destination → km)

**Examples**:

```javascript
// Create Location
POST /api/timeline/locations
{
  "projectId": "proj-123",
  "name": "King's Landing",
  "description": "Capital city on the coast",
  "knownTravelMethods": ["horse", "carriage", "sailing"]
}

// Set Location Distance
POST /api/timeline/location-distances
{
  "projectId": "proj-123",
  "fromLocationId": "loc-winterfell",
  "toLocationId": "loc-kings-landing",
  "distanceKm": 900,
  "notes": "Direct route south"
}
```

---

### Feature 3: Travel Leg Tracking

**Goal**: Writers record character movements to validate timeline consistency.

**Acceptance Criteria**:
- [ ] Users can create travel records with: character, from location, to location, depart date, arrival date, method
- [ ] Travel legs appear on the character's timeline
- [ ] System validates travel legs against timeline events
- [ ] Users can view all travel for a character
- [ ] Travel legs can be edited and deleted
- [ ] System calculates expected travel time based on method and distance
- [ ] Users can add notes explaining unusual travel (e.g., "took detour")

**Examples**:

```javascript
// Create Travel Record
POST /api/timeline/travel-legs
{
  "projectId": "proj-123",
  "characterId": "char-robb",
  "fromLocationId": "loc-winterfell",
  "toLocationId": "loc-whispering-wood",
  "departDate": "2024-01-20",
  "arrivalDate": "2024-02-05",
  "travelMethod": "horse",
  "estimatedDays": 15,
  "notes": "Marched with army of 20,000"
}
```

---

### Feature 4: World Travel Rules

**Goal**: Writers define how travel works in their world, customizing speeds and constraints.

**Acceptance Criteria**:
- [ ] Users can view/edit travel speed profile for their project
- [ ] Default speeds provided (walking, horse, carriage, sailing, flying, teleportation)
- [ ] Users can add custom travel methods with speeds
- [ ] Users can add rules about travel (rest requirements, etc.)
- [ ] Travel speed profile affects validation calculations
- [ ] Profile can be reset to defaults
- [ ] Clear documentation explains each speed type

**Examples**:

```javascript
// Update Travel Speed Profile
PUT /api/timeline/travel-speeds
{
  "projectId": "proj-123",
  "walking": 40,
  "horse": 80,
  "carriage": 60,
  "sailing": 150,
  "flying": 200,
  "teleportation": 999999,
  "custom1Name": "dragon",
  "custom1Speed": 400,
  "rules": "Dragons tire after 6 hours of flight and need 2 hour rest"
}
```

---

### Feature 5: Timeline Validation

**Goal**: System analyzes entire timeline and detects logical/physical impossibilities with teaching explanations.

**Acceptance Criteria - Impossible Travel Detection**:
- [ ] System detects when character is in two locations too close in time
- [ ] Calculation: distance ÷ travel speed = minimum days needed
- [ ] Compares to actual days between events
- [ ] Severity: CRITICAL if impossible
- [ ] Suggestion: extend timeline, use faster travel, explain magic, remove event
- [ ] Teaching: explains reader expectations about travel time

**Acceptance Criteria - Dependency Violations**:
- [ ] System detects when prerequisite event happens after dependent event
- [ ] System detects missing prerequisite events
- [ ] Severity: CRITICAL for time violations, MAJOR for missing events
- [ ] Suggestion: reorder events or remove dependency
- [ ] Teaching: explains causality importance

**Acceptance Criteria - Character Presence**:
- [ ] System flags characters with no timeline events
- [ ] System flags characters with only one event
- [ ] Severity: MAJOR for zero events, MINOR for one event
- [ ] Suggestion: add events or delete character
- [ ] Teaching: explains character arc development

**Acceptance Criteria - Timing Gaps**:
- [ ] System detects gaps >30 days between consecutive events
- [ ] Severity: MINOR (informational)
- [ ] Suggestion: consider if gap makes sense
- [ ] Teaching: explains pacing and time passage

**Acceptance Criteria - Temporal Paradoxes**:
- [ ] System detects circular dependencies (A→B→C→A)
- [ ] Uses depth-first search for cycle detection
- [ ] Severity: CRITICAL
- [ ] Suggestion: break the dependency chain
- [ ] Teaching: explains logical impossibility

**Examples**:

```javascript
// Validate Timeline
POST /api/timeline/validate
{
  "projectId": "proj-123"
}

// Response
{
  "success": true,
  "data": {
    "projectId": "proj-123",
    "totalEvents": 15,
    "totalCharacters": 8,
    "criticalIssues": 2,
    "majorIssues": 1,
    "minorIssues": 3,
    "validationTime": 145,
    "issues": [
      {
        "id": "issue-001",
        "type": "impossible_travel",
        "severity": "critical",
        "character": "char-arya",
        "description": "Arya appears in King's Landing on Day 40, then in Vale on Day 65 (900km apart, needs 11 days minimum at horse speed)",
        "suggestion": "Options: 1) Change dates to allow 15+ days, 2) Add faster travel method or magic portal, 3) Add explicit travel scene, 4) Remove one location appearance",
        "teachingPoint": "Fantasy readers subconsciously track travel time and distance. If your character can teleport, readers will wonder why they don't use that method to escape other threats. Either make magic transportation consistent or explain why it's not available.",
        "affectedEventIds": ["event-arya-escape", "event-arya-vale"]
      },
      {
        "id": "issue-002",
        "type": "dependency_violation",
        "severity": "critical",
        "description": "Event 'Tyrion wins trial' (Day 60) depends on 'Trial begins' (Day 65), but the prerequisite happens AFTER",
        "suggestion": "Reorder these events so prerequisite comes first",
        "teachingPoint": "Causality is sacred to readers. Cause must precede effect. Violating this breaks immersion instantly.",
        "affectedEventIds": ["event-tyrion-wins", "event-trial-begins"]
      }
    ],
    "suggestions": [
      "You have 2 critical timeline issues that break story logic. Fix these first.",
      "Your characters move between locations faster than physically possible 2 times. Consider your world's travel rules or add travel scenes."
    ]
  }
}
```

---

### Feature 6: Visual Timeline Display

**Goal**: Writers see their story events in a clear, interactive visual format.

**Acceptance Criteria**:
- [ ] Events displayed in chronological order on vertical timeline
- [ ] Timeline axis (vertical line) shows story progression
- [ ] Each event is a card with name, date, type, characters
- [ ] Event type icons (🎭 character, 🌍 world, 💡 revelation, 🚶 travel)
- [ ] Characters shown as colored badges (consistent colors across timeline)
- [ ] Issues appear inline with events using color-coded borders
- [ ] Click event to expand and see full details
- [ ] Filter by character to see only their timeline
- [ ] Filter by event type
- [ ] Responsive design works on desktop and tablet

**Example Visual**:

```
Timeline Axis (vertical blue line)
   ↓
[Day 1] ● Robb crowned king
         🎭 Robb, Catelyn
         📍 Winterfell
         
[Day 15] ● Robb marches south
          🚶 Robb, 20,000 soldiers
          📍 Winterfell → South
          
[Day 40] ● Arya escapes King's Landing ⚠️ CRITICAL ISSUE
          🎭 Arya
          📍 King's Landing
          Issue: Can't travel 900km in 25 days
          
[Day 65] ● Battle of Whispering Wood
          ⚔️ Robb, Catelyn, Roose
          📍 Whispering Wood
```

---

### Feature 7: Teaching & Learning

**Goal**: Every issue includes educational content that helps writers improve their craft.

**Acceptance Criteria**:
- [ ] Every issue includes a `teachingPoint` explaining WHY it matters
- [ ] Teaching points reference reader psychology and expectations
- [ ] Teaching points include examples from professional works (where applicable)
- [ ] Writers see patterns (e.g., "3 characters appear only once - are they underdeveloped?")
- [ ] Optional: Detailed "Writing Lessons" panel explaining concepts
- [ ] Suggestions teach multiple valid approaches, not just one answer

**Examples of Teaching Points**:

```javascript
// Impossible Travel
"Fantasy readers subconsciously track travel time and distance. 
If your character can magically teleport, readers will expect you to 
use that method in other high-stakes moments too. Violating this creates 
tension between reader logic and story logic."

// Broken Dependencies
"Cause must precede effect. This is a rule readers enforce subconsciously. 
Breaking it breaks immersion. If Event B depends on Event A, Event A must 
happen first, or readers won't believe the character's motivations."

// Character Presence
"Characters with just one appearance often feel unmotivated. Even minor 
characters usually need 2-3 timeline events to feel real. They should 
show change or reveal something about the world/protagonist."

// Timing Gaps
"Time gaps can work (fairy tales, romances), but readers notice them. 
Make sure each gap either: 1) Advances story (aging, seasons), 
2) Is explained (character waiting), or 3) Is intentional (timelessness)."
```

---

### Feature 8: Issue Resolution Tracking

**Goal**: Writers can mark issues as resolved and track their progress.

**Acceptance Criteria**:
- [ ] Each issue has "Mark Resolved" button
- [ ] Users can add resolution notes explaining how they fixed it
- [ ] Resolved issues remain viewable but hidden by default
- [ ] Filter to show only unresolved issues
- [ ] View resolution history
- [ ] Re-validation can mark previously-fixed issues as fixed again (or find new ones)

**Examples**:

```javascript
// Mark Issue Resolved
PATCH /api/timeline/issues/issue-001
{
  "isResolved": true,
  "resolutionNotes": "Extended timeline - Arya now has 20 days to travel to Vale, using mountain routes"
}
```

---

### Feature 9: Comprehensive Data Retrieval

**Goal**: Frontend can fetch all timeline data in one request for efficient visualization.

**Acceptance Criteria**:
- [ ] Single GET endpoint returns: events, locations, travels, characters, issues, speed profile
- [ ] No N+1 queries (efficient database calls)
- [ ] Includes summary statistics (total events, unresolved issues, etc.)
- [ ] Response includes pre-sorted data where applicable (events by date)
- [ ] Used for initial load to minimize requests

**Examples**:

```javascript
// Get Everything at Once
GET /api/timeline/comprehensive?projectId=proj-123

{
  "success": true,
  "data": {
    "events": [...],
    "locations": [...],
    "travels": [...],
    "issues": [...],
    "characters": [...],
    "speedProfile": {...},
    "summary": {
      "totalEvents": 15,
      "totalLocations": 8,
      "totalTravelLegs": 5,
      "unresolvedIssues": 3,
      "criticalIssues": 1,
      "majorIssues": 2
    }
  }
}
```

---

## 🎭 Example: Complete Multi-POV Timeline

**Story**: War of Five Kings (fantasy)

**Characters**:
- Robb Stark (Winterfell)
- Arya Stark (King's Landing)
- Tyrion Lannister (Casterly Rock)

**Timeline Events**:

```
Day 1:   Robb crowned king
         Location: Winterfell
         Characters: [Robb, Catelyn]
         Importance: 0.9

Day 15:  Robb marches south
         Location: Winterfell → South
         Characters: [Robb, army]
         Prerequisites: ["Robb crowned"]
         
Day 40:  Arya escapes King's Landing
         Location: King's Landing
         Characters: [Arya]
         
Day 50:  Tyrion reaches Casterly Rock
         Location: Journey complete
         Characters: [Tyrion]
         Prerequisites: ["Tyrion captured"]
         
Day 65:  Battle of Whispering Wood
         Location: Whispering Wood
         Characters: [Robb, Catelyn, Roose]
         Prerequisites: ["Robb marches south"]
```

**Locations**:
- Winterfell (900km from King's Landing, 1200km from Casterly Rock)
- King's Landing (coast, accessible by horse/carriage/sailing)
- Casterly Rock (mountain stronghold, accessible by horse/carriage)
- Whispering Wood (neutral location)

**Travel Legs**:
- Robb: Winterfell → Whispering Wood (Day 15-50, horse, army)
- Tyrion: captured Day 35, reaches Casterly Rock Day 50 (15 days)

**Validation Issues**:

```
CRITICAL: Arya travels 900km in 25 days
└─ Suggestion: Extend timeline or use magic
└─ Teaching: Readers track distance subconsciously

MAJOR: Tyrion's timeline is tight but possible
└─ Status: OK (15 days for mountain travel is realistic)

MINOR: Large gap between Day 65 and end of story
└─ Teaching: Does next event justify this gap?
```

---

## 🎯 Acceptance Criteria Summary

### Backend Service
- [ ] TimelineOrchestratorService validates all 5 issue types
- [ ] Each issue includes description, suggestion, and teaching point
- [ ] Service handles 1000+ events without performance issues
- [ ] Service deduplicates identical issues
- [ ] Service sorts issues by severity (critical → major → minor)

### API Routes
- [ ] 9 major endpoints implemented (event, location, travel, validation, etc.)
- [ ] All endpoints return consistent JSON format
- [ ] All endpoints include proper error handling
- [ ] POST/PATCH validate input data
- [ ] GET endpoints support filtering where applicable

### Frontend Components
- [ ] TimelineOrchestrator main component loads and displays data
- [ ] TimelineVisualization shows events in chronological order
- [ ] TimelineEventCard displays event details with issue badges
- [ ] TimelineIssuesPanel shows all issues organized by severity
- [ ] TimelineTeachingPanel extracts and displays learning moments
- [ ] Character filter works correctly
- [ ] View mode switching (timeline → issues → teaching) works
- [ ] Validation button triggers backend validation
- [ ] Issue resolution button works
- [ ] Responsive design on desktop/tablet/mobile

### Data Integrity
- [ ] Foreign key constraints work correctly
- [ ] Cascading deletes work when project deleted
- [ ] Duplicate events prevented
- [ ] Invalid dates rejected
- [ ] Missing prerequisites detected

### User Experience
- [ ] UI clearly indicates issue severity (color coding)
- [ ] Teaching points are accessible and educational
- [ ] Timeline is easy to scan visually
- [ ] Filters work intuitively
- [ ] Loading states shown during validation
- [ ] Errors are clearly communicated

---

## 🚀 Implementation Phases

### Phase 2A: Timeline Orchestrator Core (Weeks 1-4)
1. **Week 1-2**: Database schema + Backend service
2. **Week 2-3**: API routes + integration testing  
3. **Week 3-4**: Frontend components + visual design

### Phase 2B: Integration (Weeks 5-6)
- Connect to existing defect detection
- Cross-validate with plot hole detector
- Integrate teaching system with existing features

### Phase 3: Enhancement (Weeks 7+)
- Advanced visualizations (heat maps, dependency graphs)
- Export/import timeline data
- Collaboration features

---

## 📝 Notes for Claude Code

### When Implementing:

1. **Database First**: Create schema migrations before writing services
2. **Service Layer**: Build validation logic before API routes
3. **API Before UI**: Test endpoints with Postman before building components
4. **Teaching Content**: Every issue type needs thoughtful teaching points
5. **Responsive Design**: Use Tailwind classes for mobile-first design
6. **Error Messages**: Be specific and actionable in error responses

### Key Principles:

- **Teaching-First**: Every issue should explain WHY it matters
- **No Overwrites**: Never suggest rewriting user's words, only question choices
- **Multiple Solutions**: Offer 3-4 ways to fix each issue
- **Validation as Teaching**: Validation is the primary teaching mechanism
- **Visual Clarity**: Color, icons, and spacing communicate severity

### Constraints:

- Database: SQLite for dev, PostgreSQL for production
- Frontend: React 18, TypeScript, Tailwind CSS
- Backend: Node.js, Express, Prisma ORM
- No external visualization libraries for initial version (build custom)
- API response times <500ms for single project validation

---

## 🔍 Testing Scenarios

### Test Case 1: Impossible Travel
```
Setup:
- Arya at King's Landing, Day 1
- Arya at Vale, Day 5 (900km away)
Expected: CRITICAL issue about impossible travel
```

### Test Case 2: Broken Dependency
```
Setup:
- Event A depends on Event B
- Event A on Day 1, Event B on Day 10
Expected: CRITICAL issue about prerequisite timing
```

### Test Case 3: Lonely Character
```
Setup:
- Character created but appears in 0 events
Expected: MAJOR issue about character development
```

### Test Case 4: Large Time Gap
```
Setup:
- Event on Day 1, next event on Day 100
Expected: MINOR issue noting gap
```

### Test Case 5: Circular Dependency
```
Setup:
- Event A→B, Event B→C, Event C→A
Expected: CRITICAL paradox issue
```

---

## 📚 References for Writers

These concepts should be explained in teaching points:

1. **Travel Time**: How real-world travel logistics work, impact on readers
2. **Causality**: Why cause must precede effect
3. **Character Arc**: Why characters need 2+ events minimum
4. **Pacing**: Why time gaps matter to reading experience
5. **Consistency**: Why breaking reader expectations breaks immersion
6. **World Rules**: Why magic systems must be internally consistent

Example reference: *Timeframe* by K.M. Weiland, *Anatomy of Story* by John Truby

---

## ✅ Success Metrics

**System Metrics**:
- Timeline validation completes in <500ms for 1000+ events
- Zero false positives in impossible travel detection
- 95%+ accuracy in dependency violation detection

**User Metrics**:
- Writers use timeline validation >3x per project
- Writers mark >50% of detected issues as meaningful
- 70% of first-time writers improve timeline understanding after using system
- Average session time with timeline tool increases month-over-month

**Quality Metrics**:
- All major code paths covered by tests (>80% coverage)
- Zero data loss on validation
- <0.1% error rate on API endpoints

---

## 🎓 Learning Goals for Writers

By using Timeline Orchestrator, writers should understand:

✅ How to track complex multi-POV timelines
✅ Why travel time and distance matter to readers
✅ How to structure causal chains logically
✅ How character presence affects reader perception
✅ How pacing is affected by time passages
✅ How to catch logical inconsistencies before readers notice them
✅ How professional fantasy authors handle timeline complexity

---

## 📞 Questions for Clarification (Before Development)

If Claude Code needs clarification on any feature:

1. Should closed/resolved issues appear in the UI by default? (Suggest: hidden by default, toggleable)
2. Should system auto-detect character presence in scenes? (Suggest: manual entry for MVP)
3. Should validation run automatically or only on-demand? (Suggest: on-demand with button)
4. Should travel validation account for rest days? (Suggest: configurable in speed profile)
5. Should teaching points be customizable per project? (Suggest: standard library for MVP)

---

**Ready for Claude Code to begin development. All features documented with examples and acceptance criteria.**
