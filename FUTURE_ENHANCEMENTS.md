# Future Enhancements for Maxwell

**Last Updated:** 2026-01-25

This document tracks feature ideas and enhancements for future development.

---

## Recent Completions (Moved from Future to Done)

### Brainstorming Enhancements (Phase 5 - Completed Jan 21, 2026)
The following future enhancement ideas were fully implemented in Phase 5:
- ✅ **Character Development Worksheets** - Full/quick/interview worksheets with Brandon Sanderson methodology
- ✅ **AI Entity Expansion** - Deepen, expand, connect existing entities
- ✅ **Plot Twist Generator** - Included in PlotBrainstorm component
- ✅ **Mind Mapping Tool** - MindMapCanvas with draggable nodes and connections
- ✅ **Conflict Generation** - Internal, interpersonal, external, societal conflicts
- ✅ **Scene Ideation** - Beat-specific scene ideas with purposes

### World Management (Phase 8 - Completed Jan 18, 2026)
- ✅ **World-building Consistency** - World/Series hierarchy with entity scoping

---

## AI Analysis Improvements

### Plot Hole Interaction System
**Priority:** Medium
**Requested By:** User feedback (2026-01-08)

**Problem:**
Currently, plot holes are detected but users can't interact with them. Some "plot holes" are intentional creative choices (like intentionally vague character backgrounds), while others are genuine issues that need fixing.

**Proposed Solution:**

Add two action buttons for each detected plot hole:

#### 1. "Explain / Dismiss" Option
- User provides explanation for why it's intentional
- Example: "Jarn's background is intentionally mysterious - it's revealed in Act 2"
- AI stores this explanation and excludes it from future analyses
- Context is preserved: If user later asks AI to help with Act 2, AI remembers Jarn's background needs revealing

**Implementation Notes:**
- Add `plot_hole_dismissals` table:
  ```sql
  CREATE TABLE plot_hole_dismissals (
    id UUID PRIMARY KEY,
    outline_id UUID REFERENCES outlines(id),
    plot_hole_signature TEXT,  -- Hash of plot hole description
    user_explanation TEXT,
    dismissed_at TIMESTAMP,
    ai_context TEXT  -- Store for future AI calls
  )
  ```
- Update AI prompts to include: "Previously dismissed plot holes with explanations: [...]"

#### 2. "Accept / Get Help" Option
- User acknowledges it's a real plot hole
- AI generates specific suggestions to fix it
- Example: "Add a scene in Chapter 5 where Farid mentions his childhood to establish backstory"

**Implementation Notes:**
- Similar to existing Beat AI Suggestions
- Could integrate with beat content suggestions
- Might suggest creating new scenes or modifying existing ones

**User Story:**
> As a writer, I want to explain why certain story elements are intentionally vague, so the AI doesn't flag them as plot holes in future analyses.

> As a writer, when I accept a plot hole is real, I want the AI to suggest specific ways to fix it in my manuscript.

---

### Character Description Consistency Checker
**Priority:** Medium
**Requested By:** User feedback (2026-01-08)

**Problem:**
Writers sometimes accidentally change character descriptions (eye color, height, appearance) across chapters. The AI should detect these inconsistencies.

**Proposed Solution:**

Add a new analysis type: "Character Consistency Check"

**What It Should Detect:**
- Physical description changes (eye color, hair color, height, build)
- Character age inconsistencies
- Personality trait contradictions
- Character ability changes (skills they suddenly have/lose)

**Example Output:**
```
Character Inconsistency Found:
- Character: Sarah
- Issue: Eye color changes from blue (Chapter 2) to green (Chapter 8)
- Location:
  - Chapter 2, paragraph 5: "Sarah's blue eyes sparkled"
  - Chapter 8, paragraph 12: "She brushed her green eyes"
- Severity: Low (minor continuity error)
- Suggestion: Decide on one eye color and update Chapter 2 or Chapter 8
```

**Implementation Notes:**
- Extend `_get_manuscript_context()` to include all chapters (not just linked beats)
- New AI prompt specifically for character consistency
- Could use Entity extraction from Codex to track character attributes
- Store baseline character descriptions from first mentions

**Integration with Codex:**
- Could populate Entity attributes automatically from AI analysis
- Warn when manuscript contradicts Codex entries

**User Story:**
> As a writer, I want to be alerted when I accidentally change a character's description, so I can maintain consistency throughout my manuscript.

---

### Pacing Score Explanations
**Priority:** Low
**Requested By:** User feedback (2026-01-08)

**Problem:**
The pacing analysis shows a score (e.g., "7.5/10") but doesn't explain what makes a good vs. bad score or how the score is calculated.

**Proposed Solution:**

Add tooltips and detailed breakdowns for pacing scores.

**Score Breakdown:**
```
Overall Pacing Score: 7.5/10

Scoring Factors:
✅ Act Balance (2.5/3):
   Your story follows the 25-50-25 structure well

⚠️  Beat Spacing (2/3):
   Some beats are too close together in Act 2

✅ Climax Positioning (1.5/2):
   Climax is at 85% (ideal: 80-90%)

⚠️  Resolution Length (1.5/2):
   Resolution feels rushed (only 5% of story)
   Recommendation: Extend to 10-15% for satisfying conclusion
```

**UI Changes:**
- Add "ℹ️" icon next to overall score
- Clicking shows detailed breakdown modal
- Visual gauge showing score ranges:
  - 9-10: Excellent pacing
  - 7-8: Good pacing with minor issues
  - 5-6: Needs work
  - 0-4: Significant pacing problems

**Educational Tooltips:**
- Hover over "Act Balance" → Shows what ideal percentages are for selected structure type
- Hover over "Beat Spacing" → Explains rhythm and momentum

**User Story:**
> As a writer, I want to understand what my pacing score means and how to improve it, not just see a number.

---

## Implementation Priority

1. **DONE:** API Credit Error Handling ✅
2. **DONE:** Story-Specific AI Responses ✅
3. Plot Hole Interaction System (Medium priority)
4. Character Description Consistency (Medium priority)
5. Pacing Score Explanations (Low priority)

---

## Technical Notes

### Database Changes Required
- `plot_hole_dismissals` table (for plot hole explanations)
- `character_baselines` table (for consistency checking)
- Add `ai_context` JSON column to track user explanations

### AI Prompt Updates
- Include dismissed plot holes with explanations
- Add character consistency analysis prompt
- Enhance pacing analysis to return scoring breakdown

### UI Components Needed
- Plot hole action buttons (Explain/Accept)
- Character inconsistency panel
- Pacing score breakdown modal
- Tooltips throughout AI Insights panel

---

## Future Brainstorming

**Other Ideas to Consider:**
- Timeline Orchestrator integration with plot hole detection
- Scene-level AI suggestions (not just beat-level)
- Character arc tracking and analysis
- Dialogue consistency checker (character voice)
- Theme and motif tracking
- Foreshadowing analyzer
- World-building consistency (if sci-fi/fantasy)

---

**How to Use This Document:**
- Add new enhancement ideas as they come up
- Update priorities based on user feedback
- Move completed items to PROGRESS.md
- Reference this when planning sprints/milestones
