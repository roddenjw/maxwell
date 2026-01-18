"""
Entity Timeline State model for tracking entity states at different narrative points.

Enables tracking how characters, locations, or other entities change throughout
the story across multiple manuscripts in a series/world.
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class EntityTimelineState(Base):
    """
    Tracks entity state at specific points in the narrative.

    Use cases:
    - Track character age, status, allegiances at different story points
    - Track location changes (e.g., a city destroyed in Book 2)
    - Track item ownership across manuscripts
    - Compare entity states between narrative points

    Example state_data for a character:
    {
        "age": 25,
        "status": "alive",
        "location_id": "uuid",
        "allegiances": ["faction-1", "faction-2"],
        "power_level": "intermediate",
        "relationships": {
            "char-id-1": {"type": "ally", "strength": 8},
            "char-id-2": {"type": "rival", "strength": 5}
        },
        "notes": "Just discovered the truth about their past",
        "custom_fields": {}
    }
    """
    __tablename__ = "entity_timeline_states"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False, index=True)

    # Narrative position anchors (at least one should be set)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=True, index=True)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)
    timeline_event_id = Column(String, ForeignKey("timeline_events.id"), nullable=True)

    # Ordering for states within the same scope
    order_index = Column(Integer, default=0)

    # In-story timestamp (human-readable, e.g., "Day 5", "Year 1052", "Before the war")
    narrative_timestamp = Column(String, nullable=True)

    # Flexible state data - structure depends on entity type
    # Characters: age, status, location, allegiances, relationships, power_level
    # Locations: condition, population, ruler, events
    # Items: owner_id, location, condition
    state_data = Column(JSON, default=dict)

    # User-friendly label for this state snapshot
    # e.g., "End of Book 1", "After the betrayal", "Pre-transformation"
    label = Column(String, nullable=True)

    # Whether this is the canonical/official state (vs. speculative/draft)
    is_canonical = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entity = relationship("Entity", backref="timeline_states")
    manuscript = relationship("Manuscript", foreign_keys=[manuscript_id])
    chapter = relationship("Chapter", foreign_keys=[chapter_id])
    timeline_event = relationship("TimelineEvent", foreign_keys=[timeline_event_id])

    def __repr__(self):
        label_str = f"'{self.label}'" if self.label else f"order={self.order_index}"
        return f"<EntityTimelineState(id={self.id}, entity_id={self.entity_id}, {label_str})>"
