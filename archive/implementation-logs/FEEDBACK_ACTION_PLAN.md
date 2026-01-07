# Feedback Action Plan

## Testing Feedback Analysis & Implementation Plan

Based on user testing feedback from `Feedback.md`, here's a comprehensive action plan organized by priority and complexity.

---

## 🔴 Critical Issues (Fix Immediately)

### 1. Onboarding - Remove Scrivener Mention
**Feedback:** "Onboarding flow should not mention Scrivener in the comparison part."

**Issue:** Brand positioning - we shouldn't compare ourselves to competitors in onboarding.

**Action Plan:**
- [x] PRIORITY: Remove Scrivener mentions from WelcomeModal
- Search for any Scrivener references in onboarding components
- Replace with generic feature benefits
- Focus on Maxwell's unique value props

**Estimated Time:** 15 minutes
**Status:** Ready to implement

---

### 2. Sample Manuscript Creation Bug
**Feedback:** "When I selected creating a sample set of text it navigated to the home page and did not create it."

**Issue:** Critical onboarding failure - sample manuscript creation doesn't work as expected.

**Root Cause Analysis Needed:**
1. Check `backend/app/api/routes/onboarding.py` - does endpoint work?
2. Check `WelcomeModal` - is manuscriptId returned correctly?
3. Check `App.tsx` `handleWelcomeComplete` - does navigation trigger properly?
4. Verify database - is manuscript actually created?

**Action Plan:**
- [x] PRIORITY: Debug sample manuscript creation flow
- Add error logging to track where it fails
- Test backend endpoint independently
- Add loading states and error messages to onboarding
- Verify manuscript appears in library after creation

**Estimated Time:** 1 hour
**Status:** Needs debugging

---

### 3. Feature Tour Location
**Feedback:** "The notifications to introduce the features were in the top left on the home page and not within a manuscript. Those guided notifications should highlight the features within the manuscript."

**Issue:** Feature tour triggers at wrong time/place - should happen inside manuscript view, not on home page.

**Current Behavior:**
- FeatureTour component shows on manuscript library page
- Should show AFTER user opens a manuscript
- Should highlight actual UI elements (sidebar buttons, editor, etc.)

**Action Plan:**
- [x] PRIORITY: Move feature tour trigger to manuscript view
- Update `App.tsx` to delay tour until manuscript is open
- Ensure tour highlights correct elements with `data-tour` attributes
- Add separate home page tour for library-specific features

**Estimated Time:** 30 minutes
**Status:** Ready to implement

---

### 4. Settings Menu Visibility
**Feedback:** "Didn't see a settings menu anywhere for api keys."

**Issue:** Settings button may not be visible or user didn't open a manuscript.

**Current Implementation:**
- Settings button is in UnifiedSidebar footer (⚙️)
- Only visible when a manuscript is open
- May need better visual prominence

**Action Plan:**
- [x] PRIORITY: Improve settings discoverability
- Add settings to manuscript library view (for setting API key before writing)
- Make settings button more prominent (larger, different color?)
- Add tooltip/hint on first visit: "Configure AI features in Settings"
- Consider adding to onboarding flow: "Want AI suggestions? Add your API key in Settings"

**Estimated Time:** 45 minutes
**Status:** Partially done, needs enhancement

---

## 🟡 Major Features (Phase 4+)

### 5. Guided Outline Generation
**Feedback:** "When you go to create a manuscript there's an option for it to generate the structure of an outline using different prompts for the user to help them develop the structure and pacing using techniques inspired by authors like KM Weiland and others for story structure."

**Vision:** AI-powered story structure generation wizard

**Feature Breakdown:**
1. **Manuscript Creation Wizard:**
   - Step 1: Genre selection (Fantasy, Sci-Fi, Romance, Thriller, etc.)
   - Step 2: Story structure template (3-Act, Hero's Journey, Save the Cat, KM Weiland, etc.)
   - Step 3: AI-guided prompts for each plot beat
   - Step 4: Generate chapter structure from outline

2. **Story Structure Templates:**
   - **KM Weiland's Structure:**
     - Hook (0-1%)
     - Inciting Event (12%)
     - First Plot Point (25%)
     - First Pinch Point (37.5%)
     - Midpoint (50%)
     - Second Pinch Point (62.5%)
     - Third Plot Point (75%)
     - Climax (88-99%)
     - Resolution (99-100%)

   - **Save the Cat:**
     - Opening Image
     - Theme Stated
     - Setup
     - Catalyst
     - Debate
     - Break into Two
     - B Story
     - Fun and Games
     - Midpoint
     - Bad Guys Close In
     - All Is Lost
     - Dark Night of the Soul
     - Break into Three
     - Finale
     - Final Image

3. **AI Integration:**
   - Use OpenRouter to generate plot point suggestions
   - Provide 3-5 options for each beat based on established world/characters
   - Learn from user's writing style and preferences
   - Context-aware suggestions (considers genre, character motivations, world rules)

**Implementation Plan:**
- **Phase 4.1:** Create Outline Engine
  - New database table: `outlines` (manuscript_id, structure_type, plot_points)
  - Outline editor UI (separate from chapter editor)
  - Plot beat templates library

- **Phase 4.2:** Manuscript Creation Wizard
  - Multi-step form for new manuscripts
  - Genre selection with descriptions
  - Structure template picker
  - AI-powered plot beat generation

- **Phase 4.3:** Outline-to-Chapters
  - Auto-generate chapter structure from outline
  - Suggested chapter lengths based on genre
  - Chapter descriptions from plot beats

**Research Needed:**
- Study KM Weiland's "Structuring Your Novel"
- Analyze Save the Cat beat sheet
- Review Brandon Sanderson's plot structure lectures
- Research genre-specific story structures

**Estimated Time:** 4-6 weeks
**Dependencies:** AI integration (Phase 3), Outline system
**Status:** Future feature - defer to Phase 4

---

### 6. Story Structure Checkpoint Flagging
**Feedback:** "Maxwell should help flag when they should be implementing the different story structure points and explain them. For example if it's the first line of the book Maxwell should be pushing them and reviewing it to draw readers in. It should flag if the inciting event hasn't happened when it should have based on an average word count for the genre."

**Vision:** Real-time story structure analysis and guidance

**Feature Details:**

**Word Count-Based Checkpoints:**
```
Genre: Fantasy Novel (90,000 words average)

Checkpoints:
- Hook (first 500 words): "Does your opening grab the reader?"
- Inciting Event (10,800 words / 12%): "Has the protagonist's world changed?"
- First Plot Point (22,500 words / 25%): "Has your protagonist committed to the journey?"
- Midpoint (45,000 words / 50%): "Has everything changed? Is there a revelation?"
- Third Plot Point (67,500 words / 75%): "Is all hope lost? Lowest point?"
- Climax (79,200 words / 88%+): "Final confrontation happening?"
```

**UI Implementation:**
1. **Progress Bar with Checkpoints:**
   - Visual timeline showing story beats
   - Current position indicator
   - Upcoming checkpoint warnings
   - Completed checkpoints marked green

2. **Checkpoint Notifications:**
   - "You're approaching the First Plot Point (at 25% / ~22,500 words). Make sure your protagonist makes a decisive choice that propels them into Act 2."
   - "Your Inciting Event should happen around 10,800 words. You're at 15,000 - consider if it came too late."

3. **AI-Powered Analysis:**
   - Detect if key story beats have occurred
   - Analyze opening hook strength
   - Check pacing against genre norms
   - Suggest improvements for weak checkpoints

**Implementation Plan:**
- **Phase 4.4:** Checkpoint System
  - Genre-specific checkpoint definitions
  - Word count progress tracking
  - Checkpoint notification system

- **Phase 4.5:** AI Beat Detection
  - Train AI to recognize story beats in text
  - Analyze chapter content against expected beats
  - Generate checkpoint feedback

- **Phase 4.6:** Progress Dashboard
  - Visual story structure timeline
  - Checkpoint completion tracking
  - Pacing analysis graphs

**Estimated Time:** 3-4 weeks
**Dependencies:** Outline Engine (Phase 4.1), AI integration
**Status:** Future feature - defer to Phase 4

---

### 7. Brainstorming Tool
**Feedback:** "On top of the outline having a brainstorming tool to help writers come up with ideas, do some research on techniques to brainstorm character and story ideas. Brandon Sanderson has publicly available writing and YouTube videos on this."

**Vision:** Research-based ideation engine for characters, plot, worldbuilding

**Brandon Sanderson Techniques to Research:**
- **Character Development:**
  - Character flaws/strengths matrix
  - Motivations vs. obstacles
  - Character arc planning

- **Magic Systems:**
  - Sanderson's Laws of Magic
  - Hard vs. soft magic
  - Costs and limitations

- **Plot Ideas:**
  - "What if?" prompts
  - Conflict escalation
  - Subverting expectations

**Feature Components:**

1. **Idea Generator:**
   - Prompt-based brainstorming
   - AI-generated suggestions
   - Inspiration from tropes/archetypes
   - Random idea combinations

2. **Mind Mapping:**
   - Visual relationship diagrams
   - Connect characters, plot points, locations
   - Export to Codex entities

3. **Research Assistant:**
   - AI-powered research on topics
   - Historical/cultural reference gathering
   - Genre convention analysis

4. **Worksheets:**
   - Character questionnaires
   - Worldbuilding templates
   - Plot brainstorming exercises

**Implementation Plan:**
- **Phase 5.1:** Brainstorming UI
  - Dedicated brainstorming tab
  - Freeform idea capture
  - Tag and categorize ideas

- **Phase 5.2:** AI Idea Generation
  - Prompt library (characters, plot, world)
  - Context-aware suggestions
  - Combine existing ideas for new ones

- **Phase 5.3:** Mind Mapping
  - Visual idea connection tool
  - Export to Codex/Timeline
  - Collaboration features

**Research Needed:**
- Watch Brandon Sanderson's BYU lectures
- Study story brainstorming methodologies
- Research creative writing exercises
- Analyze mind mapping tools (MindMeister, Miro)

**Estimated Time:** 4-5 weeks
**Dependencies:** AI integration, Codex system
**Status:** Future feature - defer to Phase 5

---

### 8. Full Creation Engine
**Feedback:** "I want it to be a full Creation Engine to help them build their whole world, characters, magic system while also being able to prompt for help brainstorming or filling in gaps."

**Vision:** Comprehensive worldbuilding and creative development platform

**This is the NORTH STAR for Maxwell - the ultimate vision**

**Creation Engine Components:**

1. **World Builder:**
   - Geography and maps
   - Cultures and societies
   - History and timeline
   - Political systems
   - Economy and trade
   - Languages and dialects

2. **Character Creator:**
   - Detailed character profiles
   - Relationships and connections
   - Character arcs across story
   - Voice and dialogue patterns
   - Backstory development

3. **Magic System Designer:**
   - Rules and limitations
   - Power sources and costs
   - Visual effects and manifestations
   - Cultural impact
   - Power scaling

4. **Plot Outliner:**
   - Multiple outline formats
   - Plot thread tracking
   - Pacing analysis
   - Conflict development

5. **AI Creative Assistant:**
   - Gap filling suggestions
   - Consistency checking
   - "What if?" explorations
   - Research assistance
   - Draft generation

**Integration with Editor:**
- Inline reference panel showing relevant outline sections
- Quick access to character/world details while writing
- Context-aware suggestions based on world rules
- Automatic consistency checking against established lore

**Implementation Phases:**
- **Phase 6:** World Builder expansion
- **Phase 7:** Magic System designer
- **Phase 8:** Advanced AI creative assistant
- **Phase 9:** Integration and polish

**Estimated Time:** 6-12 months
**Status:** Long-term vision - continuous development

---

## 📋 Implementation Priority

### Immediate (This Week)
1. ✅ Remove Scrivener from onboarding
2. 🔧 Fix sample manuscript creation bug
3. 🔧 Move feature tour to manuscript view
4. 🔧 Improve settings visibility

### Short-term (Phase 3 Completion)
5. ✅ Complete AI integration with model selection
6. ✅ Add editor text tracking to store
7. 🧪 Test end-to-end with real API key
8. 📝 Update documentation

### Medium-term (Phase 4 - Q1 2026)
9. 📐 Outline Engine foundation
10. 🧙 Manuscript Creation Wizard
11. 📊 Story Structure Checkpoints
12. 🎯 Genre-specific templates

### Long-term (Phase 5+ - Q2-Q4 2026)
13. 💡 Brainstorming Tool
14. 🗺️ World Builder
15. ⚡ Magic System Designer
16. 🤖 Advanced AI Creative Assistant

---

## 🎯 Recommended Next Steps

### 1. Complete Phase 3 (This Session)
- [x] Add model selection to Settings ✅
- [x] Update AI panel to use selected model ✅
- [ ] Fix critical onboarding bugs
- [ ] Improve settings discoverability
- [ ] Test with real API key

### 2. Start Phase 4 Planning (Next Week)
- Research story structure methodologies
- Design Outline Engine database schema
- Wireframe Manuscript Creation Wizard
- Study Brandon Sanderson's lectures
- Analyze KM Weiland's structure templates

### 3. Long-term Roadmap
- Define Creation Engine architecture
- Plan integration points between systems
- Research worldbuilding tools and best practices
- Build out AI prompt library for creative assistance

---

## 📚 Research Resources

### Story Structure
- **KM Weiland:** "Structuring Your Novel" book
- **Save the Cat:** Blake Snyder's beat sheet
- **Story Grid:** Shawn Coyne's methodology
- **Hero's Journey:** Joseph Campbell's monomyth

### Brainstorming & Creativity
- **Brandon Sanderson:** BYU Creative Writing lectures (YouTube)
- **Brandon Sanderson:** "Sanderson's Laws of Magic"
- **James Scott Bell:** "Plot & Structure"
- **Donald Maass:** "The Emotional Craft of Fiction"

### Worldbuilding
- **Brandon Sanderson:** Worldbuilding lectures
- **On Writing and Worldbuilding:** Timothy Hickson
- **The Fantasy Worldbuilding Guide:** Various authors
- **Worldbuilding Stack Exchange:** Community resources

### AI Creative Tools
- **Sudowrite:** AI creative writing assistant (competitor analysis)
- **NovelAI:** AI storytelling platform (competitor analysis)
- **Plottr:** Outlining and timeline tool (feature inspiration)
- **Scrivener:** Research and organization (competitor analysis)

---

**Last Updated:** January 3, 2026
**Next Review:** After Phase 3 completion
