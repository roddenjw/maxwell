"""
Outline Guide Tools for Maxwell's Story Structure Guide Agent

Tools for analyzing and guiding story outline development:
- AnalyzeOutlineCompleteness: Find gaps, empty beats, missing scenes
- GetBeatGuidance: Get teaching explanation of what a beat needs
- SuggestScenesBetweenBeats: Generate scene ideas for a gap
- AnalyzeChapterBeatAlignment: Check how chapter fulfills its beat
- GetNextOutlineStep: Suggest what to work on next
"""

from typing import Optional, Type, List, Dict, Any
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool

from app.database import SessionLocal
from app.models.outline import Outline, PlotBeat, ITEM_TYPE_BEAT, ITEM_TYPE_SCENE
from app.models.manuscript import Manuscript, Chapter


# Beat explanations for teaching-first approach
BEAT_EXPLANATIONS = {
    # Three-Act Structure beats
    "hook": {
        "purpose": "The Hook grabs readers immediately with something compelling - a question, tension, or intriguing situation.",
        "what_it_needs": [
            "An immediate reason for readers to keep reading",
            "Introduction of the protagonist in action or under pressure",
            "Establishment of tone and genre expectations"
        ],
        "common_mistakes": "Starting with backstory or world-building instead of action or tension."
    },
    "inciting-incident": {
        "purpose": "The Inciting Incident disrupts the protagonist's status quo and sets the main story in motion.",
        "what_it_needs": [
            "A clear event that changes everything for the protagonist",
            "Stakes that matter personally to the character",
            "A situation the protagonist cannot ignore"
        ],
        "common_mistakes": "Making the incident too small or easily ignorable."
    },
    "first-plot-point": {
        "purpose": "The First Plot Point commits the protagonist to the journey - there's no going back.",
        "what_it_needs": [
            "A decision or event that locks the protagonist into the conflict",
            "Clear transition from setup to confrontation",
            "Raised stakes that make failure meaningful"
        ],
        "common_mistakes": "The protagonist being passive or dragged into the story."
    },
    "midpoint": {
        "purpose": "The Midpoint shifts the story's direction - from reactive to proactive, or reveals a major truth.",
        "what_it_needs": [
            "A significant revelation or event that reframes everything",
            "A shift in the protagonist's approach or understanding",
            "Often mirrors or inverts the ending"
        ],
        "common_mistakes": "Just being another complication rather than a true shift."
    },
    "second-plot-point": {
        "purpose": "The Second Plot Point is often the 'all is lost' moment before the final push.",
        "what_it_needs": [
            "The protagonist at their lowest point",
            "Loss of hope or key resources",
            "Discovery of what's truly needed to succeed"
        ],
        "common_mistakes": "Not making it feel truly hopeless before the turnaround."
    },
    "climax": {
        "purpose": "The Climax is the final confrontation where the protagonist faces their greatest challenge.",
        "what_it_needs": [
            "Direct confrontation with the main antagonist/obstacle",
            "Protagonist using everything they've learned",
            "Highest stakes and maximum tension"
        ],
        "common_mistakes": "Resolving through coincidence rather than protagonist agency."
    },
    "resolution": {
        "purpose": "The Resolution shows the new normal after the climax and provides emotional closure.",
        "what_it_needs": [
            "Demonstration of how the protagonist has changed",
            "Tying up major plot threads",
            "Emotional payoff for the reader's investment"
        ],
        "common_mistakes": "Rushing the ending or leaving major threads unresolved."
    },
    # Save the Cat beats
    "opening-image": {
        "purpose": "The Opening Image establishes the 'before' snapshot that will contrast with the Final Image.",
        "what_it_needs": [
            "Visual representation of the protagonist's current state",
            "Seeds of what will change by the end",
            "Tone and genre establishment"
        ],
        "common_mistakes": "Not making it visually or emotionally memorable."
    },
    "theme-stated": {
        "purpose": "Theme Stated plants the story's central message, often in dialogue the protagonist doesn't yet understand.",
        "what_it_needs": [
            "A line or moment that encapsulates the story's theme",
            "Subtlety - the protagonist shouldn't recognize it yet",
            "Connection to what the protagonist will learn"
        ],
        "common_mistakes": "Being too on-the-nose or preachy with the theme."
    },
    "catalyst": {
        "purpose": "The Catalyst is the moment that starts everything - life will never be the same.",
        "what_it_needs": [
            "A clear before/after dividing line",
            "Something the protagonist cannot ignore",
            "Direct connection to the main plot"
        ],
        "common_mistakes": "Making it too subtle or easy to dismiss."
    },
    "debate": {
        "purpose": "The Debate section shows the protagonist wrestling with the call to action.",
        "what_it_needs": [
            "Internal and/or external conflict about the decision",
            "Valid reasons to refuse the call",
            "Ultimately, a reason compelling enough to proceed"
        ],
        "common_mistakes": "Rushing through doubt or making the decision too easy."
    },
    "break-into-two": {
        "purpose": "Break into Two is the conscious decision to enter the new world/situation.",
        "what_it_needs": [
            "Active choice by the protagonist",
            "Clear threshold crossing",
            "Commitment to the journey ahead"
        ],
        "common_mistakes": "The protagonist being forced rather than choosing."
    },
    "b-story": {
        "purpose": "The B Story introduces a relationship that will help the protagonist learn the theme.",
        "what_it_needs": [
            "A new character or relationship",
            "Connection to the theme (often love interest or mentor)",
            "Contrast with the A Story"
        ],
        "common_mistakes": "Making it feel disconnected from the main story."
    },
    "fun-and-games": {
        "purpose": "Fun and Games is the 'promise of the premise' - why readers bought the book.",
        "what_it_needs": [
            "Delivery on genre expectations",
            "Exploration of the new world/situation",
            "Either upward or downward trajectory"
        ],
        "common_mistakes": "Forgetting to actually be fun or engaging."
    },
    "bad-guys-close-in": {
        "purpose": "Bad Guys Close In shows external pressure mounting while internal team fractures.",
        "what_it_needs": [
            "Escalating external threats",
            "Internal conflict within the protagonist's team/relationships",
            "Feeling of walls closing in"
        ],
        "common_mistakes": "Only showing external pressure, ignoring internal conflict."
    },
    "all-is-lost": {
        "purpose": "All Is Lost is the lowest point - death of hope, mentor, or old self.",
        "what_it_needs": [
            "A genuine sense of defeat",
            "Often a symbolic or literal death",
            "The 'whiff of death' that makes the stakes real"
        ],
        "common_mistakes": "Not going low enough emotionally."
    },
    "dark-night-of-the-soul": {
        "purpose": "Dark Night of the Soul is the emotional processing of the All Is Lost moment.",
        "what_it_needs": [
            "Time for the protagonist to sit with their failure",
            "Reflection on what brought them here",
            "The seed of the solution they'll find"
        ],
        "common_mistakes": "Rushing to the solution without emotional processing."
    },
    "break-into-three": {
        "purpose": "Break into Three is the solution - combining A and B stories into a new approach.",
        "what_it_needs": [
            "A genuine 'aha' moment",
            "Synthesis of lessons learned",
            "Renewed energy and commitment"
        ],
        "common_mistakes": "The solution feeling unearned or coming from nowhere."
    },
    "finale": {
        "purpose": "The Finale is the execution of the new plan in the final confrontation.",
        "what_it_needs": [
            "Application of everything learned",
            "Final defeat of the antagonist/obstacle",
            "Demonstration of character growth"
        ],
        "common_mistakes": "Resolving through luck rather than earned skills."
    },
    "final-image": {
        "purpose": "Final Image is the 'after' snapshot - proof of transformation.",
        "what_it_needs": [
            "Visual contrast with Opening Image",
            "Demonstration of change (or tragic lack thereof)",
            "Emotional resonance"
        ],
        "common_mistakes": "Not creating clear contrast with the opening."
    },
    # Hero's Journey beats
    "ordinary-world": {
        "purpose": "The Ordinary World establishes who the hero is before the adventure.",
        "what_it_needs": [
            "The hero's current life and limitations",
            "Seeds of their potential for growth",
            "What they lack or long for"
        ],
        "common_mistakes": "Making it boring rather than relatable."
    },
    "call-to-adventure": {
        "purpose": "The Call to Adventure presents a challenge or quest.",
        "what_it_needs": [
            "A clear call from outside the ordinary world",
            "Something that disrupts the status quo",
            "A goal or mission presented"
        ],
        "common_mistakes": "Making the call too vague or uninspiring."
    },
    "refusal-of-the-call": {
        "purpose": "Refusal of the Call shows the hero's fear or reluctance.",
        "what_it_needs": [
            "Valid reasons for hesitation",
            "Internal conflict about the challenge",
            "Setup for what will change their mind"
        ],
        "common_mistakes": "Skipping this beat entirely or making it too brief."
    },
    "meeting-the-mentor": {
        "purpose": "Meeting the Mentor provides guidance, tools, or wisdom for the journey.",
        "what_it_needs": [
            "A guide figure (person, object, or insight)",
            "Gifts or training for the journey ahead",
            "Encouragement to accept the call"
        ],
        "common_mistakes": "The mentor solving problems instead of enabling the hero."
    },
    "crossing-the-threshold": {
        "purpose": "Crossing the Threshold commits the hero to the adventure - entering the special world.",
        "what_it_needs": [
            "A clear point of no return",
            "Leaving the familiar behind",
            "First taste of the new world's challenges"
        ],
        "common_mistakes": "Not making the transition feel significant."
    },
    "tests-allies-enemies": {
        "purpose": "Tests, Allies, Enemies shows the hero learning the rules of the special world.",
        "what_it_needs": [
            "Challenges that test the hero's abilities",
            "Introduction of allies and enemies",
            "Learning the new world's rules"
        ],
        "common_mistakes": "Rushing through this developmental phase."
    },
    "approach-to-inmost-cave": {
        "purpose": "Approach to the Inmost Cave is preparation for the ordeal ahead.",
        "what_it_needs": [
            "Building tension before the crisis",
            "Gathering resources and allies",
            "Confronting inner fears"
        ],
        "common_mistakes": "Not building enough tension before the ordeal."
    },
    "ordeal": {
        "purpose": "The Ordeal is the central crisis - death and rebirth.",
        "what_it_needs": [
            "The hero's greatest challenge yet",
            "A death (literal or symbolic)",
            "Transformation through the experience"
        ],
        "common_mistakes": "Not making the ordeal feel truly dangerous."
    },
    "reward": {
        "purpose": "The Reward is what the hero gains from surviving the ordeal.",
        "what_it_needs": [
            "A tangible or intangible prize",
            "Celebration or rest after the crisis",
            "New knowledge or power gained"
        ],
        "common_mistakes": "Skipping the reward moment entirely."
    },
    "road-back": {
        "purpose": "The Road Back is the journey home, often with new complications.",
        "what_it_needs": [
            "Pursuit or consequences of the ordeal",
            "The decision to return with the prize",
            "Escalating stakes for the final act"
        ],
        "common_mistakes": "Making the return too easy."
    },
    "resurrection": {
        "purpose": "Resurrection is the final test - applying everything learned.",
        "what_it_needs": [
            "The climactic battle or test",
            "Death and rebirth at its highest",
            "Hero proving their transformation"
        ],
        "common_mistakes": "Not making it the true culmination of growth."
    },
    "return-with-elixir": {
        "purpose": "Return with the Elixir shows the hero changed and bearing gifts.",
        "what_it_needs": [
            "Integration of ordinary and special worlds",
            "Sharing of the treasure/wisdom",
            "Proof of transformation"
        ],
        "common_mistakes": "Not showing how the hero will use what they learned."
    }
}


class AnalyzeOutlineCompletenessInput(BaseModel):
    """Input for analyzing outline completeness"""
    manuscript_id: str = Field(description="The manuscript ID")
    include_scenes: bool = Field(
        default=True,
        description="Whether to include user-added scenes in the analysis"
    )


class AnalyzeOutlineCompleteness(BaseTool):
    """Analyze outline completeness and identify gaps"""

    name: str = "analyze_outline_completeness"
    description: str = """Analyze the manuscript's outline for completeness.
    Returns: empty beats, beats without chapters, scene gaps between beats,
    and overall progress percentage. Use this to understand what needs work."""
    args_schema: Type[BaseModel] = AnalyzeOutlineCompletenessInput

    def _run(self, manuscript_id: str, include_scenes: bool = True) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Get active outline
            outline = db.query(Outline).filter(
                Outline.manuscript_id == manuscript_id,
                Outline.is_active == True
            ).first()

            if not outline:
                return f"No active outline found for manuscript {manuscript_id}"

            # Get all beats
            all_items = db.query(PlotBeat).filter(
                PlotBeat.outline_id == outline.id
            ).order_by(PlotBeat.order_index).all()

            beats = [b for b in all_items if b.item_type == ITEM_TYPE_BEAT]
            scenes = [b for b in all_items if b.item_type == ITEM_TYPE_SCENE]

            # Analyze
            total_beats = len(beats)
            completed_beats = len([b for b in beats if b.is_completed])
            beats_with_notes = len([b for b in beats if b.user_notes])
            beats_with_chapters = len([b for b in beats if b.chapter_id])

            # Find empty beats (no notes, no chapter)
            empty_beats = [b for b in beats if not b.user_notes and not b.chapter_id]

            # Find beat gaps (adjacent beats with no scenes between)
            beat_gaps = []
            for i in range(len(beats) - 1):
                beat_a = beats[i]
                beat_b = beats[i + 1]

                # Count scenes between these beats
                scenes_between = [
                    s for s in scenes
                    if beat_a.order_index < s.order_index < beat_b.order_index
                ]

                # Check if there's a large position gap with no scenes
                position_gap = beat_b.target_position_percent - beat_a.target_position_percent
                if position_gap > 0.08 and len(scenes_between) == 0:  # >8% gap with no scenes
                    beat_gaps.append({
                        "from_beat": beat_a.beat_label,
                        "to_beat": beat_b.beat_label,
                        "position_gap_percent": round(position_gap * 100, 1)
                    })

            # Calculate progress
            progress_percent = (completed_beats / total_beats * 100) if total_beats > 0 else 0

            # Format output
            lines = [
                f"## Outline Analysis",
                f"Structure: {outline.structure_type}",
                f"",
                f"### Progress",
                f"- Beats completed: {completed_beats}/{total_beats} ({progress_percent:.0f}%)",
                f"- Beats with notes: {beats_with_notes}/{total_beats}",
                f"- Beats linked to chapters: {beats_with_chapters}/{total_beats}",
                f"- User-added scenes: {len(scenes)}",
            ]

            if empty_beats:
                lines.append(f"\n### Empty Beats (need content)")
                for beat in empty_beats[:5]:  # Limit to 5
                    position = f"({int(beat.target_position_percent * 100)}%)"
                    lines.append(f"- {beat.beat_label} {position}")
                if len(empty_beats) > 5:
                    lines.append(f"  ...and {len(empty_beats) - 5} more")

            if beat_gaps:
                lines.append(f"\n### Scene Gaps (consider adding scenes)")
                for gap in beat_gaps[:3]:  # Limit to 3
                    lines.append(
                        f"- Between {gap['from_beat']} and {gap['to_beat']} "
                        f"({gap['position_gap_percent']}% of story)"
                    )

            # Recommendations
            lines.append(f"\n### Recommendations")
            if empty_beats:
                next_empty = empty_beats[0]
                lines.append(f"- Start with: {next_empty.beat_label} (empty beat at {int(next_empty.target_position_percent * 100)}%)")
            elif beat_gaps:
                lines.append(f"- Consider adding scenes between {beat_gaps[0]['from_beat']} and {beat_gaps[0]['to_beat']}")
            elif completed_beats < total_beats:
                incomplete = [b for b in beats if not b.is_completed]
                lines.append(f"- Mark as complete: {incomplete[0].beat_label}")
            else:
                lines.append("- Outline is complete! Ready for writing.")

            return "\n".join(lines)

        finally:
            db.close()


class GetBeatGuidanceInput(BaseModel):
    """Input for getting beat guidance"""
    beat_type: str = Field(description="The beat type/label (e.g., 'midpoint', 'inciting-incident')")
    manuscript_id: Optional[str] = Field(
        default=None,
        description="Optional manuscript ID for story-specific context"
    )


class GetBeatGuidance(BaseTool):
    """Get teaching explanation of what a beat needs"""

    name: str = "get_beat_guidance"
    description: str = """Get detailed guidance about a specific story beat.
    Returns: the beat's purpose, what it needs, common mistakes to avoid,
    and story-specific suggestions if manuscript context is provided."""
    args_schema: Type[BaseModel] = GetBeatGuidanceInput

    def _run(self, beat_type: str, manuscript_id: Optional[str] = None) -> str:
        """Execute the tool"""
        # Normalize beat type
        beat_key = beat_type.lower().replace(" ", "-").replace("_", "-")

        # Look up beat explanation
        explanation = BEAT_EXPLANATIONS.get(beat_key)

        if not explanation:
            # Try partial match
            for key in BEAT_EXPLANATIONS:
                if beat_key in key or key in beat_key:
                    explanation = BEAT_EXPLANATIONS[key]
                    beat_key = key
                    break

        if not explanation:
            return f"No guidance found for beat type: {beat_type}. Try using a standard beat name like 'midpoint', 'inciting-incident', 'climax', etc."

        # Format output
        lines = [
            f"## {beat_key.replace('-', ' ').title()}: A Guide",
            f"",
            f"### Purpose",
            explanation["purpose"],
            f"",
            f"### What This Beat Needs"
        ]

        for need in explanation["what_it_needs"]:
            lines.append(f"- {need}")

        lines.extend([
            f"",
            f"### Common Mistakes",
            explanation["common_mistakes"]
        ])

        # Add manuscript-specific context if provided
        if manuscript_id:
            db = SessionLocal()
            try:
                # Get manuscript context
                manuscript = db.query(Manuscript).filter(
                    Manuscript.id == manuscript_id
                ).first()

                outline = db.query(Outline).filter(
                    Outline.manuscript_id == manuscript_id,
                    Outline.is_active == True
                ).first()

                if outline:
                    # Get this beat from the outline
                    beat = db.query(PlotBeat).filter(
                        PlotBeat.outline_id == outline.id,
                        PlotBeat.beat_label.ilike(f"%{beat_type}%")
                    ).first()

                    if beat:
                        lines.extend([
                            f"",
                            f"### In Your Outline"
                        ])

                        if beat.beat_description:
                            lines.append(f"Current description: {beat.beat_description}")

                        if beat.user_notes:
                            lines.append(f"Your notes: {beat.user_notes}")

                        if beat.chapter_id:
                            chapter = db.query(Chapter).filter(
                                Chapter.id == beat.chapter_id
                            ).first()
                            if chapter:
                                lines.append(f"Linked to chapter: {chapter.title}")

                        if not beat.user_notes and not beat.chapter_id:
                            lines.append("Status: Not yet developed")

            finally:
                db.close()

        return "\n".join(lines)


class SuggestScenesBetweenBeatsInput(BaseModel):
    """Input for suggesting scenes between beats"""
    manuscript_id: str = Field(description="The manuscript ID")
    from_beat_label: str = Field(description="The starting beat label")
    to_beat_label: str = Field(description="The ending beat label")


class SuggestScenesBetweenBeats(BaseTool):
    """Generate scene ideas to bridge two beats"""

    name: str = "suggest_scenes_between_beats"
    description: str = """Analyze the gap between two beats and gather context for suggesting
    bridge scenes. Returns the beat details, gap analysis, and manuscript context that can
    be used to generate scene suggestions."""
    args_schema: Type[BaseModel] = SuggestScenesBetweenBeatsInput

    def _run(
        self,
        manuscript_id: str,
        from_beat_label: str,
        to_beat_label: str
    ) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Get outline
            outline = db.query(Outline).filter(
                Outline.manuscript_id == manuscript_id,
                Outline.is_active == True
            ).first()

            if not outline:
                return f"No active outline found for manuscript {manuscript_id}"

            # Find the beats
            from_beat = db.query(PlotBeat).filter(
                PlotBeat.outline_id == outline.id,
                PlotBeat.beat_label.ilike(f"%{from_beat_label}%")
            ).first()

            to_beat = db.query(PlotBeat).filter(
                PlotBeat.outline_id == outline.id,
                PlotBeat.beat_label.ilike(f"%{to_beat_label}%")
            ).first()

            if not from_beat:
                return f"Could not find beat matching: {from_beat_label}"
            if not to_beat:
                return f"Could not find beat matching: {to_beat_label}"

            # Get any existing scenes between
            existing_scenes = db.query(PlotBeat).filter(
                PlotBeat.outline_id == outline.id,
                PlotBeat.item_type == ITEM_TYPE_SCENE,
                PlotBeat.order_index > from_beat.order_index,
                PlotBeat.order_index < to_beat.order_index
            ).all()

            # Calculate gap
            position_gap = to_beat.target_position_percent - from_beat.target_position_percent
            word_count_gap = (
                (to_beat.target_word_count or 0) -
                (from_beat.target_word_count or 0)
            )

            # Get manuscript context
            manuscript = db.query(Manuscript).filter(
                Manuscript.id == manuscript_id
            ).first()

            # Format output
            lines = [
                f"## Scene Gap Analysis",
                f"",
                f"### From Beat: {from_beat.beat_label}",
                f"Position: {int(from_beat.target_position_percent * 100)}% of story"
            ]

            if from_beat.beat_description:
                lines.append(f"Description: {from_beat.beat_description}")
            if from_beat.user_notes:
                lines.append(f"Notes: {from_beat.user_notes}")

            lines.extend([
                f"",
                f"### To Beat: {to_beat.beat_label}",
                f"Position: {int(to_beat.target_position_percent * 100)}% of story"
            ])

            if to_beat.beat_description:
                lines.append(f"Description: {to_beat.beat_description}")
            if to_beat.user_notes:
                lines.append(f"Notes: {to_beat.user_notes}")

            lines.extend([
                f"",
                f"### Gap Analysis",
                f"- Story position gap: {int(position_gap * 100)}%",
                f"- Estimated word count for gap: {max(0, word_count_gap):,}",
                f"- Existing scenes in gap: {len(existing_scenes)}"
            ])

            if existing_scenes:
                lines.append(f"  - " + ", ".join([s.beat_label for s in existing_scenes]))

            # Emotional journey guidance based on beat types
            lines.extend([
                f"",
                f"### Suggested Emotional Journey",
                f"Scenes between these beats should:"
            ])

            # Get the beat explanations for context
            from_key = from_beat.beat_label.lower().replace(" ", "-").replace("_", "-")
            to_key = to_beat.beat_label.lower().replace(" ", "-").replace("_", "-")

            from_exp = BEAT_EXPLANATIONS.get(from_key)
            to_exp = BEAT_EXPLANATIONS.get(to_key)

            if from_exp and to_exp:
                lines.append(f"- Bridge from: {from_exp['purpose'][:100]}")
                lines.append(f"- Lead into: {to_exp['purpose'][:100]}")

            # Manuscript context
            if manuscript:
                lines.extend([
                    f"",
                    f"### Manuscript Context",
                    f"Title: {manuscript.title}",
                    f"Genre: {outline.genre or 'Not specified'}"
                ])

                if outline.premise:
                    lines.append(f"Premise: {outline.premise[:200]}")

            # Scene suggestions placeholder
            lines.extend([
                f"",
                f"### Recommended Scene Count",
                f"Based on the {int(position_gap * 100)}% story gap:"
            ])

            if position_gap < 0.05:
                lines.append("- 0-1 scene (very short transition)")
            elif position_gap < 0.10:
                lines.append("- 1-2 scenes (brief transition)")
            elif position_gap < 0.20:
                lines.append("- 2-4 scenes (moderate development)")
            else:
                lines.append("- 4+ scenes (significant story section)")

            return "\n".join(lines)

        finally:
            db.close()


class AnalyzeChapterBeatAlignmentInput(BaseModel):
    """Input for analyzing chapter-beat alignment"""
    chapter_id: str = Field(description="The chapter ID to analyze")
    beat_id: Optional[str] = Field(
        default=None,
        description="Optional specific beat ID to analyze against"
    )


class AnalyzeChapterBeatAlignment(BaseTool):
    """Analyze how well a chapter fulfills its linked beat's purpose"""

    name: str = "analyze_chapter_beat_alignment"
    description: str = """Analyze how well a chapter fulfills its linked story beat's purpose.
    Returns: the beat's requirements, chapter summary, and alignment analysis.
    If no beat is linked, suggests appropriate beats based on chapter position."""
    args_schema: Type[BaseModel] = AnalyzeChapterBeatAlignmentInput

    def _run(self, chapter_id: str, beat_id: Optional[str] = None) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Get chapter
            chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()

            if not chapter:
                return f"Chapter not found: {chapter_id}"

            # Get manuscript and outline
            manuscript = db.query(Manuscript).filter(
                Manuscript.id == chapter.manuscript_id
            ).first()

            outline = db.query(Outline).filter(
                Outline.manuscript_id == chapter.manuscript_id,
                Outline.is_active == True
            ).first()

            if not outline:
                return f"No active outline for this chapter's manuscript"

            # Get the beat (either specified or linked to chapter)
            beat = None
            if beat_id:
                beat = db.query(PlotBeat).filter(PlotBeat.id == beat_id).first()
            else:
                beat = db.query(PlotBeat).filter(
                    PlotBeat.outline_id == outline.id,
                    PlotBeat.chapter_id == chapter_id
                ).first()

            lines = [
                f"## Chapter-Beat Alignment Analysis",
                f"",
                f"### Chapter: {chapter.title}"
            ]

            if chapter.synopsis:
                lines.append(f"Synopsis: {chapter.synopsis[:300]}")

            if chapter.word_count:
                lines.append(f"Word count: {chapter.word_count:,}")

            # Calculate chapter position
            chapters = db.query(Chapter).filter(
                Chapter.manuscript_id == chapter.manuscript_id
            ).order_by(Chapter.order_index).all()

            chapter_position = 0
            for i, ch in enumerate(chapters):
                if ch.id == chapter_id:
                    chapter_position = (i + 1) / len(chapters)
                    break

            lines.append(f"Position: {int(chapter_position * 100)}% of manuscript")

            if beat:
                lines.extend([
                    f"",
                    f"### Linked Beat: {beat.beat_label}",
                    f"Beat position: {int(beat.target_position_percent * 100)}%"
                ])

                if beat.beat_description:
                    lines.append(f"Description: {beat.beat_description}")

                # Get beat guidance
                beat_key = beat.beat_label.lower().replace(" ", "-").replace("_", "-")
                explanation = BEAT_EXPLANATIONS.get(beat_key)

                if explanation:
                    lines.extend([
                        f"",
                        f"### Beat Requirements",
                        f"Purpose: {explanation['purpose']}"
                    ])

                    lines.append(f"\nWhat this beat needs:")
                    for need in explanation["what_it_needs"]:
                        lines.append(f"- {need}")

                    lines.extend([
                        f"",
                        f"### Alignment Checklist",
                        f"Review your chapter against these requirements:"
                    ])

                    for need in explanation["what_it_needs"]:
                        lines.append(f"[ ] {need}")

                    lines.extend([
                        f"",
                        f"### Watch Out For",
                        explanation["common_mistakes"]
                    ])

            else:
                # No beat linked - suggest based on position
                lines.extend([
                    f"",
                    f"### No Beat Linked",
                    f"This chapter at {int(chapter_position * 100)}% position could map to:"
                ])

                # Find beats near this position
                nearby_beats = db.query(PlotBeat).filter(
                    PlotBeat.outline_id == outline.id,
                    PlotBeat.item_type == ITEM_TYPE_BEAT,
                    PlotBeat.target_position_percent.between(
                        chapter_position - 0.1,
                        chapter_position + 0.1
                    )
                ).all()

                if nearby_beats:
                    for b in nearby_beats:
                        status = "(already linked)" if b.chapter_id else "(available)"
                        lines.append(
                            f"- {b.beat_label} at {int(b.target_position_percent * 100)}% {status}"
                        )
                else:
                    lines.append("No beats found near this position.")
                    lines.append("Consider adding a user scene to the outline.")

            return "\n".join(lines)

        finally:
            db.close()


class GetNextOutlineStepInput(BaseModel):
    """Input for getting next outline step"""
    manuscript_id: str = Field(description="The manuscript ID")


class GetNextOutlineStep(BaseTool):
    """Suggest what to work on next in the outline"""

    name: str = "get_next_outline_step"
    description: str = """Analyze the outline and suggest what the writer should work on next.
    Considers: structural dependencies, current progress, and logical story flow.
    Returns: recommended next beat/scene to develop with reasoning."""
    args_schema: Type[BaseModel] = GetNextOutlineStepInput

    def _run(self, manuscript_id: str) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Get outline
            outline = db.query(Outline).filter(
                Outline.manuscript_id == manuscript_id,
                Outline.is_active == True
            ).first()

            if not outline:
                return f"No active outline found for manuscript {manuscript_id}"

            # Get all beats
            beats = db.query(PlotBeat).filter(
                PlotBeat.outline_id == outline.id,
                PlotBeat.item_type == ITEM_TYPE_BEAT
            ).order_by(PlotBeat.order_index).all()

            if not beats:
                return "No beats in outline. Start by selecting a story structure template."

            # Analyze what's done and what's not
            completed = [b for b in beats if b.is_completed]
            with_notes = [b for b in beats if b.user_notes]
            empty = [b for b in beats if not b.user_notes and not b.is_completed]

            lines = [
                f"## What to Work on Next",
                f"",
                f"### Current Progress",
                f"- {len(completed)}/{len(beats)} beats completed",
                f"- {len(with_notes)}/{len(beats)} beats have notes",
                f"- {len(empty)} beats are empty"
            ]

            # Priority logic
            # 1. If early foundation beats are empty, do those first
            foundation_beats = ["hook", "inciting-incident", "opening-image",
                              "catalyst", "ordinary-world", "call-to-adventure"]
            empty_foundation = [
                b for b in empty
                if any(fb in b.beat_label.lower().replace(" ", "-") for fb in foundation_beats)
            ]

            if empty_foundation:
                recommended = empty_foundation[0]
                lines.extend([
                    f"",
                    f"### Recommended: {recommended.beat_label}",
                    f"Position: {int(recommended.target_position_percent * 100)}%",
                    f"",
                    f"**Why this beat?**",
                    f"Foundation beats establish your story's core. {recommended.beat_label} ",
                    f"should be developed before later beats because it informs everything that follows."
                ])

                # Add beat guidance
                beat_key = recommended.beat_label.lower().replace(" ", "-").replace("_", "-")
                explanation = BEAT_EXPLANATIONS.get(beat_key)
                if explanation:
                    lines.extend([
                        f"",
                        f"**What to write:**",
                        explanation["purpose"]
                    ])

                return "\n".join(lines)

            # 2. If midpoint-ish beats are empty and early beats are done, suggest midpoint
            midpoint_beats = ["midpoint", "fun-and-games", "ordeal"]
            early_beats_done = len([
                b for b in beats
                if b.target_position_percent < 0.30 and (b.user_notes or b.is_completed)
            ]) > 0

            empty_midpoint = [
                b for b in empty
                if any(mb in b.beat_label.lower().replace(" ", "-") for mb in midpoint_beats)
            ]

            if empty_midpoint and early_beats_done:
                recommended = empty_midpoint[0]
                lines.extend([
                    f"",
                    f"### Recommended: {recommended.beat_label}",
                    f"Position: {int(recommended.target_position_percent * 100)}%",
                    f"",
                    f"**Why this beat?**",
                    f"With your opening established, the {recommended.beat_label} is a crucial ",
                    f"turning point that shapes your story's second half."
                ])

                return "\n".join(lines)

            # 3. If there are any empty beats, suggest the next one in order
            if empty:
                recommended = empty[0]
                lines.extend([
                    f"",
                    f"### Recommended: {recommended.beat_label}",
                    f"Position: {int(recommended.target_position_percent * 100)}%",
                    f"",
                    f"**Why this beat?**",
                    f"This is the next empty beat in your story structure. ",
                    f"Working through beats in order helps maintain narrative flow."
                ])

                return "\n".join(lines)

            # 4. If all beats have content but aren't complete, suggest marking complete
            incomplete = [b for b in beats if b.user_notes and not b.is_completed]
            if incomplete:
                lines.extend([
                    f"",
                    f"### Recommended: Review and Mark Complete",
                    f"",
                    f"All beats have content! Review these beats and mark them complete:",
                ])
                for b in incomplete[:5]:
                    lines.append(f"- {b.beat_label}")

                return "\n".join(lines)

            # 5. All done!
            lines.extend([
                f"",
                f"### Outline Complete!",
                f"",
                f"All beats have been developed. You're ready to:",
                f"- Review the outline as a whole",
                f"- Add scenes between beats where needed",
                f"- Start writing your manuscript!"
            ])

            return "\n".join(lines)

        finally:
            db.close()


# Create tool instances
analyze_outline_completeness = AnalyzeOutlineCompleteness()
get_beat_guidance = GetBeatGuidance()
suggest_scenes_between_beats = SuggestScenesBetweenBeats()
analyze_chapter_beat_alignment = AnalyzeChapterBeatAlignment()
get_next_outline_step = GetNextOutlineStep()
