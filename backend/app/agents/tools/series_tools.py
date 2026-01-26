"""
Series Tools for Maxwell Agents

Tools for querying cross-book context within a series.
"""

from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool

from app.database import SessionLocal
from app.models.world import World, Series
from app.models.manuscript import Manuscript
from app.models.entity import Entity, ENTITY_SCOPE_SERIES
from app.models.timeline import TimelineEvent
from app.models.outline import Outline, PlotBeat


class QuerySeriesContextInput(BaseModel):
    """Input for querying series context"""
    manuscript_id: str = Field(description="The manuscript ID")


class QuerySeriesContext(BaseTool):
    """Query series-level context"""

    name: str = "query_series_context"
    description: str = """Get information about the series this manuscript belongs to.
    Returns other books in the series, their order, and overall series arc.
    Use this to understand where the current book fits in the larger story."""
    args_schema: Type[BaseModel] = QuerySeriesContextInput

    def _run(self, manuscript_id: str) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Get manuscript
            manuscript = db.query(Manuscript).filter(
                Manuscript.id == manuscript_id
            ).first()

            if not manuscript:
                return f"Manuscript {manuscript_id} not found"

            if not manuscript.series_id:
                return "This manuscript is not part of a series"

            # Get series
            series = db.query(Series).filter(
                Series.id == manuscript.series_id
            ).first()

            if not series:
                return "Series not found"

            # Get all manuscripts in series
            manuscripts = db.query(Manuscript).filter(
                Manuscript.series_id == series.id
            ).order_by(Manuscript.order_index).all()

            # Get series outline if exists
            series_outline = db.query(Outline).filter(
                Outline.series_id == series.id
            ).first()

            # Format output
            lines = [
                f"## Series: {series.name}",
            ]

            if series.description:
                lines.append(f"\n{series.description}")

            # Current position
            current_index = next(
                (i for i, m in enumerate(manuscripts) if m.id == manuscript_id),
                -1
            )
            lines.append(f"\n### Current Position: Book {current_index + 1} of {len(manuscripts)}")

            # List books
            lines.append("\n### Books in Series:")
            for i, ms in enumerate(manuscripts):
                marker = ">>> " if ms.id == manuscript_id else "    "
                status = f"({ms.word_count:,} words)"
                lines.append(f"{marker}{i + 1}. {ms.title} {status}")

            # Series outline info
            if series_outline:
                lines.append("\n### Series Arc")
                lines.append(f"Structure: {series_outline.structure_type}")

                if series_outline.premise:
                    lines.append(f"Premise: {series_outline.premise}")

                # Get series-level beats
                beats = db.query(PlotBeat).filter(
                    PlotBeat.outline_id == series_outline.id
                ).order_by(PlotBeat.order_index).all()

                if beats:
                    lines.append("\n### Series Beats:")
                    for beat in beats[:10]:
                        book_marker = ""
                        if beat.target_book_index:
                            book_marker = f"[Book {beat.target_book_index}]"
                        status = "[DONE]" if beat.is_completed else "[    ]"
                        lines.append(f"{status} {beat.beat_label} {book_marker}")

            # Get timeline events from previous books (for continuity)
            previous_manuscripts = [m for m in manuscripts if m.order_index < manuscript.order_index]
            if previous_manuscripts:
                prev_ids = [m.id for m in previous_manuscripts]

                # Get important events from previous books
                important_events = db.query(TimelineEvent).filter(
                    TimelineEvent.manuscript_id.in_(prev_ids),
                    TimelineEvent.narrative_importance >= 7
                ).order_by(TimelineEvent.order_index).limit(10).all()

                if important_events:
                    lines.append("\n### Key Events from Previous Books:")
                    for event in important_events:
                        book = next(
                            (m.title for m in manuscripts if m.id == event.manuscript_id),
                            "Unknown"
                        )
                        lines.append(f"- [{book}] {event.description[:100]}")

            return "\n".join(lines)

        finally:
            db.close()


class QueryCrossBookEntitiesInput(BaseModel):
    """Input for querying cross-book entities"""
    manuscript_id: str = Field(description="The manuscript ID")
    entity_type: Optional[str] = Field(
        default=None,
        description="Optional type filter: CHARACTER, LOCATION, ITEM, LORE"
    )
    entity_name: Optional[str] = Field(
        default=None,
        description="Optional: search for specific entity by name"
    )


class QueryCrossBookEntities(BaseTool):
    """Query entities that appear across multiple books"""

    name: str = "query_cross_book_entities"
    description: str = """Get entities that are shared across books in the series.
    This includes series-scoped characters, locations, and lore.
    Use this to check character consistency across books."""
    args_schema: Type[BaseModel] = QueryCrossBookEntitiesInput

    def _run(
        self,
        manuscript_id: str,
        entity_type: Optional[str] = None,
        entity_name: Optional[str] = None
    ) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Get manuscript -> series -> world
            manuscript = db.query(Manuscript).filter(
                Manuscript.id == manuscript_id
            ).first()

            if not manuscript or not manuscript.series_id:
                return "This manuscript is not part of a series"

            series = db.query(Series).filter(
                Series.id == manuscript.series_id
            ).first()

            if not series:
                return "Series not found"

            # Get series-scoped entities
            query = db.query(Entity).filter(
                Entity.world_id == series.world_id,
                Entity.scope == ENTITY_SCOPE_SERIES
            )

            if entity_type:
                query = query.filter(Entity.type == entity_type)

            if entity_name:
                query = query.filter(Entity.name.ilike(f"%{entity_name}%"))

            entities = query.all()

            # Also get entities that appear in multiple manuscripts
            manuscripts = db.query(Manuscript).filter(
                Manuscript.series_id == series.id
            ).all()
            manuscript_ids = [m.id for m in manuscripts]

            # Get all manuscript-scoped entities
            ms_entities = db.query(Entity).filter(
                Entity.manuscript_id.in_(manuscript_ids)
            )

            if entity_type:
                ms_entities = ms_entities.filter(Entity.type == entity_type)

            ms_entities = ms_entities.all()

            # Find entities with same name across manuscripts
            name_to_entities = {}
            for e in ms_entities:
                name_lower = e.name.lower()
                if name_lower not in name_to_entities:
                    name_to_entities[name_lower] = []
                name_to_entities[name_lower].append(e)

            cross_book_entities = [
                entities_list for entities_list in name_to_entities.values()
                if len(entities_list) > 1
            ]

            # Format output
            lines = [f"## Cross-Book Entities in {series.name}"]

            if entities:
                lines.append(f"\n### Series-Scoped Entities ({len(entities)}):")
                for entity in entities:
                    aliases = f" (aka: {', '.join(entity.aliases)})" if entity.aliases else ""
                    lines.append(f"- {entity.name}{aliases} [{entity.type}]")

                    if entity.template_data and entity_name:
                        # Show more detail for specific entity search
                        td = entity.template_data
                        if td.get("role"):
                            lines.append(f"  Role: {td['role']}")
                        if td.get("physical", {}).get("appearance"):
                            lines.append(f"  Appearance: {td['physical']['appearance'][:100]}")

            if cross_book_entities:
                lines.append(f"\n### Entities Appearing in Multiple Books ({len(cross_book_entities)}):")

                # Get manuscript names
                ms_names = {m.id: m.title for m in manuscripts}

                for entity_list in cross_book_entities:
                    name = entity_list[0].name
                    books = [ms_names.get(e.manuscript_id, "?") for e in entity_list]
                    lines.append(f"- {name}: appears in {', '.join(books)}")

            if not entities and not cross_book_entities:
                lines.append("\nNo cross-book entities found.")
                lines.append("Consider creating series-scoped entities for recurring characters.")

            return "\n".join(lines)

        finally:
            db.close()


# Create tool instances
query_series_context = QuerySeriesContext()
query_cross_book_entities = QueryCrossBookEntities()
