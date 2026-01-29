 This document is used for containing my feedback as I'm testing different components for future phases. It should be read and then once incorporated into a main implementation plan marked as resolved in here.

Outline

1. ✅ **RESOLVED (2026-01-10)** - There are UX issues across the board that prevent text from being fully readable. These are the examples: 1. In the Outline section the summary below the story beat is not fully visible.
   - **Fix:** Added max-height with scrollable overflow to beat descriptions in PlotBeatCard.tsx (max-h-40 with overflow-y-auto)
2. ✅ **RESOLVED (2026-01-10)** - Additionally the Timeline tab and Analytics tab withing Outline don't do anything.
   - **Fix:** Timeline and Analytics tabs ARE fully functional. TimelineView shows horizontal beat visualization with hover tooltips. ProgressDashboard shows completion analytics, word count progress, act breakdown, pacing heatmap, and quick insights.
3. ✅ **RESOLVED (2026-01-10)** - Also in the new view I cannot navigate to different story beats within the outline.
   - **Fix:** Clicking beats in Timeline view now navigates to List view, scrolls to the beat, and expands it with smooth animation. Added beat refs and scroll-into-view functionality in OutlineSidebar.tsx. Updated to use store's expandedBeatId instead of local state for consistency across components.
4. ✅ **RESOLVED (2026-01-10)** - Outline button on editor breadcrumb causes navigation issues / stuck on single beat view.
   - **Fix:** Fixed state management mismatch in OutlineSidebar - now uses store's expandedBeatId consistently instead of local state. Added auto-navigation effect that responds to expandedBeatId changes from external sources (breadcrumb button, timeline clicks). Removed buggy scroll-to-element-by-ID logic in App.tsx handleViewBeat. Navigation now correctly switches to List view and scrolls to selected beat.
5. ✅ **RESOLVED (2026-01-25)** - Two related points of feedback in 5a and 5b.
   5a. Outlines should default with story beats but allow authors to add scenes in between the beats. The beats are a starting point to structure a story but there is a still alot to outline in between to make sure they are bridging between the beats.
   5b. Driving off of feedback point 5a. We should have an AI Component here to help brainstorm how to move the story between the beats. For example if the Inciting Incident is "Boy finds magic sword" and the First Plot Point is "Boy fights evil wizard" help the author get them from point a to point b following best practices for structuring and outlining stories.
   - **Fix:** AddSceneButton.tsx exists between beats in list view, allowing custom scenes to be added. AI bridge scene generation via generateBridgeScenes() provides "AI: Bridge This Gap" button with intelligent scene suggestions for transitioning between plot beats.
6. ✅ **CLARIFIED (2026-01-25)** - Story premise in the outline view seems to just be taking text from the actual manuscript and not creating a premise. How should this work?
   - **Clarification:** The user may be confusing two different fields:
     - **Premise** (outline-level): Set manually by user via Settings button in sidebar or during outline creation. Starts empty and should be user-entered. Shown at top of OutlineMainView.
     - **Written Content / content_summary** (beat-level): Automatically extracted from linked chapter text. This CORRECTLY shows manuscript content.
   - **UI improvements:** OutlineMainView now clearly displays premise at the top with "Story Summary" section. PlotBeatCard labels content_summary as "Written Content:" to avoid confusion.
   - **How premise works:** User sets it via Settings modal (cogwheel button in sidebar header) or during outline creation with optional AI brainstorming helper.
7. ✅ **RESOLVED (2026-01-25)** - After running AI insights for story beat suggestions users should be able to provide feedback to the beat suggestion, what they liked and didn't liked and then regenerate a few suggestions for that beat with their refinements added.
   - **Fix:** Added comprehensive feedback loop to AISuggestionsPanel Beat Ideas tab:
     - Like/dislike buttons on each AI suggestion
     - Optional notes field for specific feedback per beat
     - Feedback summary banner showing when feedback is ready
     - "Regenerate with Feedback" button that sends all feedback to AI
     - Backend endpoint `/ai-analyze-with-feedback` incorporates user feedback into prompts
     - Feedback state managed in outlineStore with `beatFeedback` Map
8. ✅ **RESOLVED (2026-01-25)** - The outlines tab on the left just opens a page in the middle with no real content besides placeholder text and a sidebar windown on the right. Closing the side causes an 'Oops! Something went wrong.' error. Additionally this middle part of the outline seems to serve no purpose. Why dont we allow the collapsible sidebar for outline in the text editor but clicking the outline tab displays all the outline info in the larger middle window. You can see this in the Outline Photo.png
   - **Fix:** Created OutlineMainView.tsx component that displays full outline info in center area including: structure type, progress bar, premise/logline/synopsis, and all beats organized by act. Sidebar remains as an optional quick-access panel. Error handling improved with proper null checks.
9. ✅ **RESOLVED (2026-01-25)** - There's an annoying Create Outline popup that appears in a manuscript with out one and it cant be dismissed until you make one. Users should be able to close it out.
   - **Fix:** Added "Maybe Later" button to the no-outline state in OutlineSidebar.tsx. Users can now dismiss the panel without creating an outline. The header close button (X) also works.
10. ✅ **RESOLVED (2026-01-29)** - Scene suggestions and beat suggestions should take into account the current manuscript rather than generic scene suggestions. If I have a manuscript or idea or premise I want those taken into account. Before I got generic ones that didn't fit the story or the genre even.
    - **Fix:** Updated `generate_beat_content_suggestions()` in ai_outline_service.py to:
      - Include manuscript context via `_get_manuscript_context()` (chapter content)
      - Include Codex entities (characters, locations, items) from the manuscript
      - System prompt now instructs AI to reference specific characters and story elements
      - AI suggestions must use actual character names instead of generic placeholders

Timeline View:

1. ✅ **RESOLVED (2026-01-10)** - In the timeline view when hovering over the events most of the text is cut off to the left of the event summary and I can't see anything else about it.
   - **Fix:** Added smart tooltip positioning in TimelineView.tsx. Tooltips at edges (<20% or >80%) now align to left/right instead of center to prevent cutoff. Also made beat description scrollable with max-h-12 overflow-y-auto.
2. In the Swimlanes feature it mentions that I need characters. My manuscript has characters but theyre not being tied to events. How does the swimlane feature intend to work? How are characters linked to Events?
3. ✅ **RESOLVED (2026-01-25)** - Timeline doesn't actually seem to detect across the whole manuscript when you use the detection feature or Analyze featue. It seems to be stuck on the crrent chapter.
   - **Fix:** Created new AnalyzeModal component with scope selection. Users can now choose "Current Chapter" or "Entire Manuscript" when clicking the Analyze button. Manuscript-wide analysis fetches all chapters, combines their content, and runs both Codex (entity detection) and Timeline (event detection) analysis on the full text.

Time Machine

1. Would be nice to note the changes in between versions. Almost like auto generated commit messages that are detailing the edits made and progress in the story.

Text Editor

1. ✅ **RESOLVED (2026-01-25)** - UI is cluttered with options are the top. In an ideal world I want to mimic the features of scriveners text editor and a similar layout.
   - **Fix:** Grouped paragraph formatting options (alignment, lists) into dropdown menu. Added Focus Mode for distraction-free writing that hides toolbar and shows only keyboard shortcut hints. Cleaner, less cluttered toolbar design.
2. ✅ **RESOLVED (2026-01-25)** - We should have more options for fonts.
   - **Fix:** Expanded font selector from 5 to 15+ writing-friendly fonts organized by category: Serif Traditional (Garamond, Georgia, Palatino, Baskerville), Serif Modern (Merriweather, Lora, Crimson Text), Sans-Serif (Inter, Arial, Open Sans), and Monospace (Courier, Consolas).

Binder/Chapter Features

1. ✅ **RESOLVED (2026-01-25)** - Allow a card based view with summaries of each chapter presented (AI Generated or User Entered if theyd like) In this view allow drag and drop.
   - **Fix:** Created ChapterCorkboard component with visual card-based chapter view. Cards show title, word count, and color-coded progress bars. Supports drag-and-drop reordering, inline rename, duplicate, and delete. Toggle button in DocumentNavigator header switches between Tree and Corkboard views. View preference persisted in localStorage.
2. Mimic Scrivener with its folder structure and file types like character sheets and notes and title pages. For the character sheets these be able to relate to manuscripts but also be a standalone type of document accessible from the Library

Brainstorming

1. It may be worthwhile to have the entities and lore created from brainstorming output into a standardized format and have these records available as another tab in the library.
2. ✅ **RESOLVED (2026-01-18)** - Potentially also have the Library view have a higher up view of 'World' or 'Series' and then within this are manuscripts, lore, history, locations, creatures, magic/technology, characters. The worldbuilding components can be related to multiple manuscripts within.
   - **Fix:** Phase 8 (Library & World Management) implemented full World → Series → Manuscript hierarchy. WorldLibrary component with 5 sub-components (WorldCard, CreateWorldModal, SeriesExplorer, SharedEntityLibrary). Entity scoping allows MANUSCRIPT, SERIES, or WORLD level entities. 18 new API endpoints for world/series CRUD and entity management.
3. ✅ **RESOLVED (2026-01-21)** - Give users guided help brainstorming locations, creatures, magic/technology, history, and characters.
   - **Fix:** Phase 5 (Brainstorming & Ideation) implemented full suite of guided generators: CharacterBrainstorm, PlotBrainstorm, LocationBrainstorm, ConflictBrainstorm, SceneBrainstorm components. EntityTemplateWizard provides step-by-step guided creation for 6 entity types (CHARACTER, LOCATION, ITEM, MAGIC_SYSTEM, CREATURE, ORGANIZATION). Character worksheets with Brandon Sanderson methodology.
4. ✅ **RESOLVED (2026-01-21)** - **AI-Powered Entity Expansion** (2026-01-18): Brainstorming should actively consider existing entities and offer a mixture of ideas.
   - **Fix:** Phase 5 implemented `expand_entity()` and `generate_related_entities()` methods. API endpoints: `POST /api/brainstorming/entities/{id}/expand` (deepen, expand, connect modes) and `POST /api/brainstorming/entities/{id}/generate-related`. IdeaCard component has Refine/Expand/Contrast buttons. Existing entity chips shown in brainstorming UI for context-aware generation.

Quick Reference

1. ✅ **RESOLVED (2026-01-29)** - Allow users to highlight words or text, or when we pick up the name of an already defined entity allow a hover to remind them of quick descriptions of the entities state at that point in time.
   - **Fix:** Created EntityHoverCard component (frontend/src/components/Editor/EntityHoverCard.tsx):
     - Hovering over EntityMentionNodes in editor shows floating tooltip card
     - Displays entity type icon, name, description, and key attributes
     - "View in Codex" button opens full entity details in sidebar
     - Integrated into EntityMentionNode component with 150ms hover delay to prevent flash

Entity Creation

1. ✅ **RESOLVED (2026-01-29)** - Allow users to hover over a word or words and turn them into an entity or entity description right within the text editor.
   - **Fix:** Created SelectionToolbar and QuickEntityModal components:
     - SelectionToolbar: Floating toolbar appears when text is selected in editor
     - "Create Entity" button opens QuickEntityModal with selection pre-filled as name
     - QuickEntityModal: Minimal form with name, type (CHARACTER/LOCATION/ITEM/LORE), and optional description
     - Option to replace selected text with EntityMentionNode (clickable link in editor)
     - Full integration with Codex store for entity management

Codex

1. ✅ **RESOLVED (2026-01-25)** - We should allow for the entire file to be scanned at once for entities. Potentially upon import but also within the text.
   - **Fix:** Created AnalyzeModal component with scope selection ("Current Chapter" vs "Entire Manuscript"). Clicking Analyze button opens modal where users choose scope. Manuscript-wide analysis fetches all chapters, shows progress indicator ("Loading chapter X of Y"), combines text, and runs NLP entity detection on the full manuscript. Now supports extracting entities from entire manuscripts.
2. ✅ **RESOLVED (2026-01-25)** - It would be great to be able to Edit suggested entities to correct them. Many are almost picked up but its still finding things like 'Mother of X Character' rather than the actual characters name. You can look at the file called Path of Fools v1, Dramatis Personae chapter for reference this is where I noticed these.
   - **Fix:** Added "Edit & Approve" mode to SuggestionCard component. Users now have two options when reviewing suggestions:
     - "Quick Approve": Creates entity with NLP-suggested values (existing behavior)
     - "Edit & Approve": Expands card into edit mode with editable name field, type dropdown (CHARACTER/LOCATION/ITEM/LORE), and description textarea. Users can correct names, change types, and add descriptions before creating the entity.
   - Also added extracted_description and extracted_attributes fields to suggestions. NLP now extracts descriptions from patterns like "X is a..." and categorized attributes (appearance, personality) which are displayed on suggestion cards and pre-filled in edit mode.
