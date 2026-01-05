"""
Scene and Entity Appearance Models
Track where entities appear in the manuscript with scene-level granularity
"""

from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class ChapterScene(Base):
    """
    ChapterScene - A detected scene within a chapter (from scene breaks or paragraph analysis)
    Different from the standalone Scene model - this tracks scenes WITHIN chapters
    """
    __tablename__ = "chapter_scenes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chapter_id = Column(String, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    manuscript_id = Column(String, ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False)

    # Scene metadata
    title = Column(String, nullable=True)  # Optional scene title
    sequence_order = Column(Integer, nullable=False)  # Order within chapter
    word_count = Column(Integer, default=0)

    # Scene boundaries (character positions in chapter content)
    start_position = Column(Integer, nullable=False)  # Start character position
    end_position = Column(Integer, nullable=False)    # End character position

    # Scene summary (AI-generated or user-provided)
    summary = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chapter = relationship("Chapter", back_populates="chapter_scenes")
    appearances = relationship("EntityAppearance", back_populates="chapter_scene", cascade="all, delete-orphan")


class EntityAppearance(Base):
    """
    EntityAppearance - Tracks where an entity appears in the manuscript
    Links entities to specific chapters/scenes with context
    """
    __tablename__ = "entity_appearances"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    manuscript_id = Column(String, ForeignKey("manuscripts.id", ondelete="CASCADE"), nullable=False)
    chapter_id = Column(String, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    chapter_scene_id = Column(String, ForeignKey("chapter_scenes.id", ondelete="CASCADE"), nullable=True)  # Optional

    # Timeline integration
    timeline_event_id = Column(String, ForeignKey("timeline_events.id", ondelete="SET NULL"), nullable=True)

    # Appearance context
    summary = Column(Text, nullable=False)  # "John confronted the king about the missing sword"
    context_text = Column(Text, nullable=True)  # Relevant excerpt from the text
    sequence_order = Column(Integer, nullable=False)  # Order within chapter/scene

    # AI metadata
    ai_generated = Column(Integer, default=0)  # Boolean: was this AI-detected?
    confidence = Column(Float, nullable=True)  # NLP confidence score (0-1)

    # Additional metadata
    appearance_metadata = Column(JSON, default=dict)  # Flexible storage for future features

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entity = relationship("Entity", back_populates="appearances")
    chapter = relationship("Chapter")
    chapter_scene = relationship("ChapterScene", back_populates="appearances")
    timeline_event = relationship("TimelineEvent")


# Update existing models to add relationships
def update_entity_model():
    """
    Add this to app/models/codex.py Entity class:

    # Relationships
    appearances = relationship("EntityAppearance", back_populates="entity", cascade="all, delete-orphan")
    """
    pass


def update_chapter_model():
    """
    Add this to app/models/chapter.py Chapter class:

    # Relationships
    scenes = relationship("Scene", back_populates="chapter", cascade="all, delete-orphan")
    """
    pass
