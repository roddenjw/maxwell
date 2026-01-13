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
5. Two relarted points of feedback in 5a and 5b.
   5a. Outlines should default with story beats but allow authors to add scenes in between the beats. The beats are a starting point to structure a story but there is a still alot to outline in between to make sure they are bridging between the beats.
   5b. Driving off of feedback point 5a. We should have an AI Component here to help brainstorm how to move the story between the beats. For example if the Inciting Incident is "Boy finds magic sword" and the First Plot Point is "Boy fights evil wizard" help the author get them from point a to point b following best practices for structuring and outlining stories.
6. Story premise in the outline view seems to just be taking text from the actual manuscript and not creating a premise. How should this work?
7. After running AI insights for story beat suggestions users should be able to provide feedback to the beat suggestion, what they liked and didn't liked and then regenerate a few suggestions for that beat with their refinements added.
8. The outlines tab on the left just opens a page in the middle with no real content besides placeholder text and a sidebar windown on the right. Closing the side causes an 'Oops! Something went wrong.' error. Additionally this middle part of the outline seems to serve no purpose. Why dont we allow the collapsible sidebar for outline in the text editor but clicking the outline tab displays all the outline info in the larger middle window. You can see this in the Outline Photo.png

Timeline View:

1. ✅ **RESOLVED (2026-01-10)** - In the timeline view when hovering over the events most of the text is cut off to the left of the event summary and I can't see anything else about it.
   - **Fix:** Added smart tooltip positioning in TimelineView.tsx. Tooltips at edges (<20% or >80%) now align to left/right instead of center to prevent cutoff. Also made beat description scrollable with max-h-12 overflow-y-auto.
2. In the Swimlanes feature it mentions that I need characters. My manuscript has characters but theyre not being tied to events. How does the swimlane feature intend to work? How are characters linked to Events?

Time Machine

1. Would be nice to note the changes in between versions. Almost like auto generated commit messages that are detailing the edits made and progress in the story.

Text Editor

1. UI is cluttered with options are the top. In an ideal world I want to mimic the features of scriveners text editor and a similar layout.
2. We should have more options for fonts.

Binder/Chapter Features

1. Allow a card based view with summaries of each chapter presented (AI Generated or User Entered if theyd like) In this view allow drag and drop.
2. Mimic Scrivener with its folder structure and file types like character sheets and notes and title pages. For the character sheets these be able to relate to manuscripts but also be a standalone type of document accessible from the Library

Brainstorming

1. It may be worthwhile to have the entities and lore created from brainstorming output into a standardized format and have these records available as another tab in the library.
2. Potentially also have the Library view have a higher up view of 'World' or 'Series' and then within this are manuscripts, lore, history, locations, creatures, magic/technology, characters. The worldbuilding components can be related to multiple manuscripts within.
3. Give users guided help brainstorming locations, creatures, magic/technology, history, and characters.

Quick Reference

1. Allow users to highlight words or text, or when we pick up the name of an already defined entity allow a hover to remind them of quick descriptions of the entities state at that point in time.

Entity Creation

1. Allow users to hover over a word or words and turn them into an entity right within the text editor.
