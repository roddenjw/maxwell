"""
Hierarchical Context Loader for Maxwell Agents

Loads context from the four-level hierarchy:
1. Author Context (persistent across all work)
2. World Context (shared across universe)
3. Series Context (shared within series)
4. Manuscript Context (current work)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.database import SessionLocal
from app.models.coach import WritingProfile, CoachingHistory, FeedbackPattern
from app.models.world import World, Series
from app.models.manuscript import Manuscript, Chapter
from app.models.entity import Entity, Relationship, ENTITY_SCOPE_MANUSCRIPT, ENTITY_SCOPE_SERIES, ENTITY_SCOPE_WORLD
from app.models.timeline import TimelineEvent
from app.models.outline import Outline, PlotBeat


@dataclass
class AuthorContext:
    """Author-level context (persistent across all work)"""
    user_id: str
    style_metrics: Dict[str, Any] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    overused_words: Dict[str, int] = field(default_factory=dict)
    favorite_techniques: List[str] = field(default_factory=list)
    feedback_patterns: List[Dict[str, Any]] = field(default_factory=list)
    learning_history: List[Dict[str, Any]] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """Convert to text suitable for prompt injection"""
        parts = [f"## Author Profile (User: {self.user_id})"]

        if self.style_metrics:
            parts.append("\n### Writing Style Metrics")
            for metric, value in self.style_metrics.items():
                parts.append(f"- {metric}: {value}")

        if self.strengths:
            parts.append("\n### Strengths")
            for s in self.strengths[:5]:
                parts.append(f"- {s}")

        if self.weaknesses:
            parts.append("\n### Areas for Improvement")
            for w in self.weaknesses[:5]:
                parts.append(f"- {w}")

        if self.preferences:
            parts.append("\n### Preferences")
            for key, value in list(self.preferences.items())[:10]:
                parts.append(f"- {key}: {value}")

        if self.overused_words:
            top_overused = sorted(
                self.overused_words.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            if top_overused:
                parts.append("\n### Watch Words (overused)")
                for word, count in top_overused:
                    parts.append(f"- \"{word}\" (used {count}x)")

        return "\n".join(parts)


@dataclass
class WorldContext:
    """World-level context (shared across universe)"""
    world_id: str
    name: str
    description: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)
    world_entities: List[Dict[str, Any]] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)  # Magic systems, laws of physics, etc.
    cultures: List[Dict[str, Any]] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """Convert to text suitable for prompt injection"""
        parts = [f"## World: {self.name}"]

        if self.description:
            parts.append(f"\n{self.description}")

        if self.settings:
            parts.append("\n### World Settings")
            for key, value in self.settings.items():
                if isinstance(value, dict):
                    parts.append(f"\n#### {key}")
                    for k, v in value.items():
                        parts.append(f"- {k}: {v}")
                else:
                    parts.append(f"- {key}: {value}")

        if self.rules:
            parts.append("\n### World Rules")
            for rule in self.rules[:10]:
                parts.append(f"- {rule}")

        if self.cultures:
            parts.append(f"\n### Cultures ({len(self.cultures)} total)")
            for culture in self.cultures[:10]:
                line = f"- {culture.get('title')}"
                sd = culture.get('structured_data', {})
                if sd.get('values'):
                    line += f" — Values: {', '.join(sd['values'][:3])}"
                if sd.get('taboos'):
                    line += f" | Taboos: {', '.join(sd['taboos'][:3])}"
                parts.append(line)
                if culture.get('member_count', 0) > 0:
                    parts.append(f"  Members: {culture['member_count']}")

        if self.world_entities:
            parts.append(f"\n### World Entities ({len(self.world_entities)} total)")
            for entity in self.world_entities[:15]:
                parts.append(f"- {entity.get('name')} ({entity.get('type')})")

        return "\n".join(parts)


@dataclass
class SeriesContext:
    """Series-level context (shared within series)"""
    series_id: str
    name: str
    description: str = ""
    manuscripts: List[Dict[str, Any]] = field(default_factory=list)
    series_timeline: List[Dict[str, Any]] = field(default_factory=list)
    character_arcs: List[Dict[str, Any]] = field(default_factory=list)
    recurring_themes: List[str] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """Convert to text suitable for prompt injection"""
        parts = [f"## Series: {self.name}"]

        if self.description:
            parts.append(f"\n{self.description}")

        if self.manuscripts:
            parts.append(f"\n### Books in Series ({len(self.manuscripts)})")
            for ms in self.manuscripts:
                parts.append(f"- {ms.get('order_index', 0) + 1}. {ms.get('title')} ({ms.get('word_count', 0)} words)")

        if self.character_arcs:
            parts.append("\n### Character Arcs Across Series")
            for arc in self.character_arcs[:5]:
                parts.append(f"- {arc.get('character')}: {arc.get('arc_summary', 'No summary')}")

        if self.recurring_themes:
            parts.append("\n### Recurring Themes")
            for theme in self.recurring_themes[:5]:
                parts.append(f"- {theme}")

        return "\n".join(parts)


@dataclass
class ManuscriptContext:
    """Manuscript-level context (current work)"""
    manuscript_id: str
    title: str
    description: str = ""
    word_count: int = 0
    chapters: List[Dict[str, Any]] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    timeline_events: List[Dict[str, Any]] = field(default_factory=list)
    outline: Optional[Dict[str, Any]] = None
    current_position: Optional[Dict[str, Any]] = None  # Current chapter, beat, etc.

    def to_prompt_context(self) -> str:
        """Convert to text suitable for prompt injection"""
        parts = [f"## Current Manuscript: {self.title}"]

        if self.description:
            parts.append(f"\n{self.description}")

        parts.append(f"\nWord Count: {self.word_count}")

        if self.current_position:
            parts.append("\n### Current Position")
            for key, value in self.current_position.items():
                parts.append(f"- {key}: {value}")

        if self.chapters:
            parts.append(f"\n### Chapters ({len(self.chapters)} total)")
            for ch in self.chapters[:20]:
                status = "folder" if ch.get("is_folder") else f"{ch.get('word_count', 0)} words"
                parts.append(f"- {ch.get('title')} ({status})")

        if self.entities:
            parts.append(f"\n### Entities ({len(self.entities)} total)")
            by_type: Dict[str, List[str]] = {}
            for e in self.entities:
                t = e.get("type", "OTHER")
                if t not in by_type:
                    by_type[t] = []
                by_type[t].append(e.get("name", "Unknown"))

            for entity_type, names in by_type.items():
                parts.append(f"\n#### {entity_type}")
                for name in names[:10]:
                    parts.append(f"- {name}")

        if self.outline:
            parts.append("\n### Outline")
            parts.append(f"Structure: {self.outline.get('structure_type', 'Unknown')}")
            if self.outline.get("premise"):
                parts.append(f"Premise: {self.outline.get('premise')}")

        return "\n".join(parts)


@dataclass
class AgentContext:
    """Complete context for an agent, combining all levels"""
    author: Optional[AuthorContext] = None
    world: Optional[WorldContext] = None
    series: Optional[SeriesContext] = None
    manuscript: Optional[ManuscriptContext] = None

    # Weights for context importance (set by agent config)
    author_weight: float = 0.5
    world_weight: float = 0.5
    series_weight: float = 0.5
    manuscript_weight: float = 1.0

    def to_prompt_context(self, max_tokens: int = 8000) -> str:
        """
        Generate prompt context string, weighted by importance

        Args:
            max_tokens: Approximate max tokens (uses char count / 4 as estimate)
        """
        parts = ["# Context for Analysis\n"]
        max_chars = max_tokens * 4  # Rough estimate

        # Gather sections with weights
        sections = []

        if self.author and self.author_weight > 0:
            sections.append((self.author_weight, self.author.to_prompt_context()))

        if self.world and self.world_weight > 0:
            sections.append((self.world_weight, self.world.to_prompt_context()))

        if self.series and self.series_weight > 0:
            sections.append((self.series_weight, self.series.to_prompt_context()))

        if self.manuscript and self.manuscript_weight > 0:
            sections.append((self.manuscript_weight, self.manuscript.to_prompt_context()))

        # Sort by weight (highest first)
        sections.sort(key=lambda x: x[0], reverse=True)

        current_length = len(parts[0])

        for weight, content in sections:
            if current_length + len(content) < max_chars:
                parts.append(content)
                current_length += len(content)
            else:
                # Truncate if needed
                remaining = max_chars - current_length - 100
                if remaining > 500:
                    parts.append(content[:remaining] + "\n[Context truncated]")
                break

        return "\n\n".join(parts)


class ContextLoader:
    """
    Loads context from the database at all hierarchy levels

    Usage:
        loader = ContextLoader()
        context = loader.load_full_context(
            user_id="user123",
            manuscript_id="ms456"
        )
        prompt_text = context.to_prompt_context()
    """

    def load_author_context(self, user_id: str) -> AuthorContext:
        """Load author-level context from WritingProfile and coaching history"""
        db = SessionLocal()
        try:
            # Get writing profile
            profile = db.query(WritingProfile).filter(
                WritingProfile.user_id == user_id
            ).first()

            profile_data = profile.profile_data if profile else {}

            # Get recent feedback patterns
            patterns = db.query(FeedbackPattern).filter(
                FeedbackPattern.user_id == user_id
            ).order_by(FeedbackPattern.frequency.desc()).limit(10).all()

            # Get recent coaching history for learning
            history = db.query(CoachingHistory).filter(
                CoachingHistory.user_id == user_id
            ).order_by(CoachingHistory.created_at.desc()).limit(20).all()

            return AuthorContext(
                user_id=user_id,
                style_metrics=profile_data.get("style_metrics", {}),
                strengths=profile_data.get("strengths", []),
                weaknesses=profile_data.get("weaknesses", []),
                preferences=profile_data.get("preferences", {}),
                overused_words=profile_data.get("overused_words", {}),
                favorite_techniques=profile_data.get("favorite_techniques", []),
                feedback_patterns=[
                    {
                        "type": p.pattern_type,
                        "description": p.pattern_description,
                        "frequency": p.frequency
                    }
                    for p in patterns
                ],
                learning_history=[
                    {
                        "feedback": h.agent_feedback,
                        "reaction": h.user_reaction,
                        "type": h.feedback_type,
                        "date": h.created_at.isoformat()
                    }
                    for h in history
                ]
            )
        finally:
            db.close()

    def load_world_context(self, world_id: str) -> WorldContext:
        """Load world-level context"""
        db = SessionLocal()
        try:
            world = db.query(World).filter(World.id == world_id).first()
            if not world:
                return WorldContext(world_id=world_id, name="Unknown World")

            # Get world-scoped entities
            world_entities = db.query(Entity).filter(
                Entity.world_id == world_id,
                Entity.scope == ENTITY_SCOPE_WORLD
            ).all()

            # Extract rules from settings
            settings = world.settings or {}
            rules = []
            if "magic_system" in settings:
                rules.extend(settings["magic_system"].get("rules", []))
            if "world_rules" in settings:
                rules.extend(settings["world_rules"])

            # Load cultures from wiki
            cultures = []
            try:
                from app.services.culture_service import CultureService
                culture_service = CultureService(db)
                cultures = culture_service.get_world_cultures(world_id)
            except Exception:
                pass  # Culture data is optional context

            return WorldContext(
                world_id=world_id,
                name=world.name,
                description=world.description or "",
                settings=settings,
                world_entities=[
                    {
                        "id": e.id,
                        "name": e.name,
                        "type": e.type,
                        "attributes": e.attributes
                    }
                    for e in world_entities
                ],
                rules=rules,
                cultures=cultures,
            )
        finally:
            db.close()

    def load_series_context(self, series_id: str) -> SeriesContext:
        """Load series-level context"""
        db = SessionLocal()
        try:
            series = db.query(Series).filter(Series.id == series_id).first()
            if not series:
                return SeriesContext(series_id=series_id, name="Unknown Series")

            # Get manuscripts in series
            manuscripts = db.query(Manuscript).filter(
                Manuscript.series_id == series_id
            ).order_by(Manuscript.order_index).all()

            # Get series-level outline if exists
            series_outline = db.query(Outline).filter(
                Outline.series_id == series_id
            ).first()

            # Extract character arcs from series outline
            character_arcs = []
            if series_outline:
                beats = db.query(PlotBeat).filter(
                    PlotBeat.outline_id == series_outline.id
                ).all()
                # Process beats for character arc info
                # This would need more sophisticated extraction in production

            # Get timeline events across all manuscripts
            manuscript_ids = [m.id for m in manuscripts]
            timeline_events = db.query(TimelineEvent).filter(
                TimelineEvent.manuscript_id.in_(manuscript_ids)
            ).order_by(TimelineEvent.order_index).all()

            return SeriesContext(
                series_id=series_id,
                name=series.name,
                description=series.description or "",
                manuscripts=[
                    {
                        "id": m.id,
                        "title": m.title,
                        "order_index": m.order_index,
                        "word_count": m.word_count
                    }
                    for m in manuscripts
                ],
                series_timeline=[
                    {
                        "description": e.description,
                        "timestamp": e.timestamp,
                        "manuscript_id": e.manuscript_id
                    }
                    for e in timeline_events[:50]
                ],
                character_arcs=character_arcs,
                recurring_themes=[]  # Would need analysis to extract
            )
        finally:
            db.close()

    def load_manuscript_context(
        self,
        manuscript_id: str,
        current_chapter_id: Optional[str] = None
    ) -> ManuscriptContext:
        """Load manuscript-level context"""
        db = SessionLocal()
        try:
            manuscript = db.query(Manuscript).filter(
                Manuscript.id == manuscript_id
            ).first()
            if not manuscript:
                return ManuscriptContext(
                    manuscript_id=manuscript_id,
                    title="Unknown Manuscript"
                )

            # Get chapters
            chapters = db.query(Chapter).filter(
                Chapter.manuscript_id == manuscript_id
            ).order_by(Chapter.order_index).all()

            # Get manuscript-scoped entities
            entities = db.query(Entity).filter(
                Entity.manuscript_id == manuscript_id
            ).all()

            # Get timeline events
            timeline_events = db.query(TimelineEvent).filter(
                TimelineEvent.manuscript_id == manuscript_id
            ).order_by(TimelineEvent.order_index).all()

            # Get active outline
            outline = db.query(Outline).filter(
                Outline.manuscript_id == manuscript_id,
                Outline.is_active == True
            ).first()

            # Determine current position
            current_position = None
            if current_chapter_id:
                current_chapter = next(
                    (c for c in chapters if c.id == current_chapter_id),
                    None
                )
                if current_chapter:
                    current_position = {
                        "chapter_id": current_chapter.id,
                        "chapter_title": current_chapter.title,
                        "chapter_index": current_chapter.order_index
                    }

            return ManuscriptContext(
                manuscript_id=manuscript_id,
                title=manuscript.title,
                description=manuscript.description or "",
                word_count=manuscript.word_count,
                chapters=[
                    {
                        "id": c.id,
                        "title": c.title,
                        "is_folder": bool(c.is_folder),
                        "word_count": c.word_count,
                        "order_index": c.order_index
                    }
                    for c in chapters
                ],
                entities=[
                    {
                        "id": e.id,
                        "name": e.name,
                        "type": e.type,
                        "aliases": e.aliases,
                        "attributes": e.attributes
                    }
                    for e in entities
                ],
                timeline_events=[
                    {
                        "id": e.id,
                        "description": e.description,
                        "timestamp": e.timestamp,
                        "event_type": e.event_type
                    }
                    for e in timeline_events
                ],
                outline={
                    "id": outline.id,
                    "structure_type": outline.structure_type,
                    "premise": outline.premise,
                    "logline": outline.logline
                } if outline else None,
                current_position=current_position
            )
        finally:
            db.close()

    def load_full_context(
        self,
        user_id: str,
        manuscript_id: str,
        current_chapter_id: Optional[str] = None,
        author_weight: float = 0.5,
        world_weight: float = 0.5,
        series_weight: float = 0.5,
        manuscript_weight: float = 1.0
    ) -> AgentContext:
        """
        Load full hierarchical context

        Args:
            user_id: User ID for author context
            manuscript_id: Current manuscript ID
            current_chapter_id: Optional current chapter for position context
            *_weight: Weights for each context level (0.0 to 1.0)

        Returns:
            Complete AgentContext with all levels loaded
        """
        db = SessionLocal()
        try:
            # Get manuscript to find series/world
            manuscript = db.query(Manuscript).filter(
                Manuscript.id == manuscript_id
            ).first()

            series_id = manuscript.series_id if manuscript else None
            world_id = None

            if series_id:
                series = db.query(Series).filter(Series.id == series_id).first()
                if series:
                    world_id = series.world_id

            db.close()

            # Load all context levels
            author_ctx = self.load_author_context(user_id) if author_weight > 0 else None
            world_ctx = self.load_world_context(world_id) if world_id and world_weight > 0 else None
            series_ctx = self.load_series_context(series_id) if series_id and series_weight > 0 else None
            manuscript_ctx = self.load_manuscript_context(
                manuscript_id, current_chapter_id
            ) if manuscript_weight > 0 else None

            return AgentContext(
                author=author_ctx,
                world=world_ctx,
                series=series_ctx,
                manuscript=manuscript_ctx,
                author_weight=author_weight,
                world_weight=world_weight,
                series_weight=series_weight,
                manuscript_weight=manuscript_weight
            )
        except Exception:
            db.close()
            raise


# Global context loader instance
context_loader = ContextLoader()
