# Phase 2: Timeline Visual Enhancements

## Overview

Maxwell's Timeline has been enhanced with two powerful new visualization tools for tracking character movements and story conflicts. These features help authors maintain continuity and identify story patterns.

## New Features

### 1. Character Location Tracker 🗺️

Track character movements through your story's locations with a visual journey timeline.

**Features:**
- **Character Journey View**: See every location a character visits in order
- **Location Summary**: Count of visits to each location
- **Movement Detection**: Automatically highlights when characters move between locations
- **Event Timeline**: Full chronological view of a character's scenes

**How It Works:**
1. Open Timeline sidebar (⏱️ button)
2. Click "Locations" tab (🗺️ icon)
3. Select a character from the list
4. View their complete journey through your story

**Example Use Cases:**
- Verify a character was in the right place at the right time
- Track how often characters visit key locations
- Identify location continuity errors
- Plan character movements for future scenes

**Data Shown:**
- Number of events per character
- Number of location changes
- Visited locations with visit counts
- Movement indicators between locations
- Event descriptions with location and timestamp

### 2. Conflict Tracker ⚔️

Automatically detect and visualize conflicts between characters based on story events.

**Features:**
- **Auto-Detection**: Finds conflicts using 40+ conflict keywords
- **Intensity Rating**: 1-5 scale based on keywords and sentiment
- **Conflict Status**: Active, Escalating, or Resolved
- **Timeline View**: See how conflicts develop over time
- **Keyword Highlighting**: Shows specific conflict words in each event

**Conflict Keywords Detected:**
- Physical: fight, battle, attack, war
- Verbal: argue, disagree, confront, accuse
- Emotional: anger, hate, rage, betray
- Action: oppose, resist, challenge, threaten

**How It Works:**
1. Open Timeline sidebar (⏱️ button)
2. Click "Conflicts" tab (⚔️ icon)
3. View detected conflicts sorted by intensity
4. Select a conflict to see detailed timeline

**Conflict Status Detection:**
- **Escalating**: More conflict keywords in recent events
- **Active**: Steady conflict intensity
- **Resolved**: Fewer conflict keywords in recent events

**Data Shown:**
- Character pairs in conflict
- Number of conflict events
- Intensity rating (1-5)
- Status (escalating/active/resolved)
- Timeline of all conflict events
- Highlighted conflict keywords per event

## Integration

### Timeline Sidebar Tabs

The Timeline sidebar now has 8 tabs:
1. **Visual** 📜 - Interactive timeline graph
2. **Events** 🎬 - List of all events
3. **Issues** ⚠️ - Inconsistencies detected
4. **Locations** 🗺️ - Character location tracker (NEW)
5. **Conflicts** ⚔️ - Conflict visualization (NEW)
6. **Heatmap** 🔥 - Activity heatmap
7. **Network** 🕸️ - Character relationship network
8. **Emotion** 💭 - Emotional arc visualization

## Technical Implementation

### Character Location Tracker

**File**: `frontend/src/components/Timeline/CharacterLocationTracker.tsx`

**Architecture:**
- Filters events by character appearance
- Builds journey from ordered events
- Detects location changes by comparing consecutive events
- Groups locations with visit counts

**Data Sources:**
- Timeline events (`event.character_ids`, `event.location_id`)
- Codex entities (CHARACTER and LOCATION types)
- Event metadata (`location_name` as fallback)

**Key Functions:**
- `buildCharacterJourneys()` - Creates journey data for all characters
- `getCharacterLocations()` - Aggregates location visits
- `getLocationChanges()` - Identifies movement events

### Conflict Tracker

**File**: `frontend/src/components/Timeline/ConflictTracker.tsx`

**Architecture:**
- Scans all events for conflict keywords
- Creates conflicts for character pairs that share conflict events
- Calculates intensity from keyword count + sentiment
- Determines status from temporal keyword patterns

**Detection Algorithm:**
```
For each event:
  If event has 2+ characters AND conflict keywords:
    For each character pair:
      Add to conflict or create new conflict
      Increment intensity based on:
        - Number of conflict keywords
        - Negative sentiment score (+2 bonus)
      Track event in conflict timeline

For each conflict:
  Compare recent vs early events:
    If recent > early * 1.5: status = escalating
    If recent < early * 0.5: status = resolved
    Else: status = active
```

**Intensity Scale:**
- 1: Minor tension (1-2 keywords)
- 2: Low intensity (2-3 keywords)
- 3: Medium intensity (3-4 keywords)
- 4: High intensity (4+ keywords)
- 5: Maximum intensity (many keywords + strong negative sentiment)

## Analytics Integration

**Events Tracked:**
- `timelineOpened` - When user opens location tracker
- Existing timeline analytics apply to new tabs

**Success Metrics:**
- Adoption: % of users who use Locations and Conflicts tabs
- Engagement: Average time spent in each view
- Value: Conflicts detected per 10K words
- Accuracy: Do detected conflicts match actual story conflicts?

## Usage Examples

### Example 1: Location Continuity Check

**Scenario**: You wrote "Sarah entered the library" in Chapter 5, but the last time you mentioned her she was at the harbor.

**Solution**:
1. Open Locations tracker
2. Select "Sarah"
3. Scroll through her journey
4. See: Harbor (Chapter 4) → Library (Chapter 5)
5. Missing: Travel transition

**Fix**: Add a scene showing Sarah leaving the harbor

### Example 2: Conflict Arc Planning

**Scenario**: You want to ensure the conflict between Marcus and Elena escalates properly.

**Solution**:
1. Open Conflicts tracker
2. Find "Marcus vs Elena"
3. Check status: Shows "Active" with 3/5 intensity
4. Review timeline: 3 events, steady keywords
5. Decision: Add a major confrontation scene to escalate

### Example 3: Character Movement Pattern

**Scenario**: Verify your detective character visits crime scenes in the correct order.

**Solution**:
1. Open Locations tracker
2. Select detective character
3. View location summary: Crime Scene A (×2), Crime Scene B (×1), HQ (×3)
4. Check timeline order matches investigation flow

## Future Enhancements

### Phase 3+ Improvements
- **Location Map**: Visual map showing character positions
- **Conflict Export**: Export conflict analysis as PDF
- **Custom Keywords**: Let users define their own conflict keywords
- **Relationship Heat**: Visual graph showing conflict intensity over time
- **Multi-Character Tracking**: Compare journeys of multiple characters side-by-side
- **POV Tracking**: Show which character's POV each scene is from

### API Enhancements
- Backend endpoint for conflict detection (move logic from frontend)
- Character location history API
- Conflict intensity scoring with ML
- Auto-suggestions for location transitions

## Testing Guide

### Manual Testing: Locations

1. **Create sample data**:
   - Add characters: Sarah, Marcus
   - Add locations: Harbor, Library, Castle
   - Create timeline events with characters at different locations

2. **Test location tracker**:
   - Open Timeline → Locations tab
   - Should show character list with event counts
   - Select Sarah
   - Verify journey shows all events in order
   - Check movement indicators appear when location changes

3. **Edge cases**:
   - Character with no events (should not appear)
   - Character with one location (no movements)
   - Missing location data (shows "Unknown Location")

### Manual Testing: Conflicts

1. **Create conflict events**:
   - Write event: "Marcus and Sarah fought over the stolen artifact"
   - Write event: "Sarah accused Marcus of betrayal"
   - Write event: "Marcus confronted Sarah angrily"

2. **Test conflict tracker**:
   - Open Timeline → Conflicts tab
   - Should show "Marcus vs Sarah" conflict
   - Click to view details
   - Verify all 3 events appear
   - Check keywords highlighted: "fought", "accused", "betrayal", "confronted", "angrily"
   - Verify intensity rating (should be 3-4/5)

3. **Status detection**:
   - Add more conflict events → should show "Escalating"
   - Add peaceful events → should show "Resolved"

### Automated Tests

```typescript
// Test conflict detection
describe('ConflictTracker', () => {
  it('detects conflict from keywords', () => {
    const event = {
      character_ids: ['char1', 'char2'],
      description: 'They fought bitterly'
    };
    const conflicts = detectConflicts([event]);
    expect(conflicts).toHaveLength(1);
    expect(conflicts[0].intensity).toBeGreaterThan(0);
  });
});

// Test location tracking
describe('CharacterLocationTracker', () => {
  it('builds character journey', () => {
    const events = [
      { character_ids: ['char1'], location_id: 'loc1', order_index: 1 },
      { character_ids: ['char1'], location_id: 'loc2', order_index: 2 }
    ];
    const journey = buildCharacterJourneys(events);
    expect(journey[0].locations).toHaveLength(2);
  });
});
```

---

## Files Modified

### New Components
- `frontend/src/components/Timeline/CharacterLocationTracker.tsx` (290 lines)
- `frontend/src/components/Timeline/ConflictTracker.tsx` (320 lines)

### Updated Components
- `frontend/src/components/Timeline/TimelineSidebar.tsx` - Added 2 new tabs
- `frontend/src/stores/timelineStore.ts` - Added 'locations' and 'conflicts' tab types

---

## Success Metrics

Track these in PostHog to measure success:

1. **Feature Adoption**:
   - % of users who open Locations tab
   - % of users who open Conflicts tab
   - Avg views per user per week

2. **Engagement**:
   - Avg time spent in Locations view
   - Avg time spent in Conflicts view
   - % of sessions that include Timeline tabs

3. **Value Indicators**:
   - Manuscripts with >5 characters tracked
   - Manuscripts with >3 conflicts detected
   - Correlation: Location tracking → fewer continuity errors?

4. **Quality**:
   - Conflict detection accuracy (user feedback)
   - Location data completeness
   - User reports of bugs/issues

---

**Last Updated**: January 2, 2026
**Status**: ✅ Complete - Timeline visual enhancements ready for beta
**Next**: Phase 2 Week 4 - Codex Relationship Graph Export
