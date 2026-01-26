"""
Outline Tools for Maxwell Agents

Tools for querying story structure, plot beats, and outline data.
"""

from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool

from app.database import SessionLocal
from app.models.outline import Outline, PlotBeat, ITEM_TYPE_BEAT, ITEM_TYPE_SCENE
from app.models.manuscript import Chapter


class QueryOutlineInput(BaseModel):
    """Input for querying outline"""
    manuscript_id: str = Field(description="The manuscript ID")


class QueryOutline(BaseTool):
    """Query the manuscript's outline"""

    name: str = "query_outline"
    description: str = """Get the manuscript's story outline including structure type, premise, and synopsis.
    Use this to understand the overall story structure and intended narrative arc."""
    args_schema: Type[BaseModel] = QueryOutlineInput

    def _run(self, manuscript_id: str) -> str:
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

            # Format output
            lines = [
                f"## Story Outline",
                f"Structure: {outline.structure_type}",
                f"Genre: {outline.genre or 'Not specified'}",
                f"Target Word Count: {outline.target_word_count:,}",
            ]

            if outline.premise:
                lines.append(f"\n### Premise\n{outline.premise}")

            if outline.logline:
                lines.append(f"\n### Logline\n{outline.logline}")

            if outline.synopsis:
                lines.append(f"\n### Synopsis\n{outline.synopsis[:500]}")
                if len(outline.synopsis) > 500:
                    lines.append("...[truncated]")

            if outline.notes:
                lines.append(f"\n### Notes\n{outline.notes[:300]}")

            # Count beats
            beat_count = db.query(PlotBeat).filter(
                PlotBeat.outline_id == outline.id,
                PlotBeat.item_type == ITEM_TYPE_BEAT
            ).count()

            completed_count = db.query(PlotBeat).filter(
                PlotBeat.outline_id == outline.id,
                PlotBeat.is_completed == True
            ).count()

            lines.append(f"\n### Progress")
            lines.append(f"Beats: {completed_count}/{beat_count} completed")

            return "\n".join(lines)

        finally:
            db.close()


class QueryPlotBeatsInput(BaseModel):
    """Input for querying plot beats"""
    manuscript_id: str = Field(description="The manuscript ID")
    include_scenes: bool = Field(
        default=False,
        description="Whether to include user-added scenes between beats"
    )
    completed_only: bool = Field(
        default=False,
        description="Only return completed beats"
    )


class QueryPlotBeats(BaseTool):
    """Query plot beats from the outline"""

    name: str = "query_plot_beats"
    description: str = """Get detailed plot beats from the story structure.
    Returns beat names, descriptions, target positions, and completion status.
    Use this to understand story pacing and check if scenes align with structure."""
    args_schema: Type[BaseModel] = QueryPlotBeatsInput

    def _run(
        self,
        manuscript_id: str,
        include_scenes: bool = False,
        completed_only: bool = False
    ) -> str:
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

            # Build query
            query = db.query(PlotBeat).filter(
                PlotBeat.outline_id == outline.id
            )

            if not include_scenes:
                query = query.filter(PlotBeat.item_type == ITEM_TYPE_BEAT)

            if completed_only:
                query = query.filter(PlotBeat.is_completed == True)

            beats = query.order_by(PlotBeat.order_index).all()

            if not beats:
                return "No plot beats found"

            # Get chapter info
            chapter_ids = [b.chapter_id for b in beats if b.chapter_id]
            chapters = db.query(Chapter).filter(Chapter.id.in_(chapter_ids)).all()
            chapter_map = {c.id: c.title for c in chapters}

            # Format output
            lines = [f"## Plot Beats ({outline.structure_type})"]

            for beat in beats:
                status = "[DONE]" if beat.is_completed else "[    ]"
                position = f"({int(beat.target_position_percent * 100)}%)"
                type_badge = "SCENE" if beat.item_type == ITEM_TYPE_SCENE else ""

                lines.append(f"\n{status} {beat.beat_label} {position} {type_badge}")

                if beat.beat_description:
                    lines.append(f"   {beat.beat_description[:150]}")

                if beat.user_notes:
                    lines.append(f"   Notes: {beat.user_notes[:100]}")

                if beat.chapter_id:
                    chapter_title = chapter_map.get(beat.chapter_id, "Unknown")
                    lines.append(f"   Linked to: {chapter_title}")

                if beat.actual_word_count:
                    target = beat.target_word_count or 0
                    lines.append(
                        f"   Words: {beat.actual_word_count:,} "
                        f"(target: {target:,})"
                    )

            return "\n".join(lines)

        finally:
            db.close()


# Create tool instances
query_outline = QueryOutline()
query_plot_beats = QueryPlotBeats()
