"""
Recap models for chapter and arc summaries
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Recap(Base):
    """Aesthetic recap for chapters and story arcs"""
    __tablename__ = "recaps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)  # Null for arc recaps

    # Recap type: "chapter" or "arc"
    recap_type = Column(String, nullable=False, default="chapter")

    # Structured recap content (JSON)
    content = Column(JSON, nullable=False, default=dict)
    # {
    #   "summary": "...",
    #   "key_events": ["...", "..."],
    #   "character_developments": [{"character": "...", "development": "..."}],
    #   "themes": ["...", "..."],
    #   "emotional_tone": "...",
    #   "narrative_arc": "...",
    #   "chapter_ids": ["..."] // For arc recaps
    # }

    # Cache metadata
    source_hash = Column(String, nullable=True)  # Hash of source content to detect changes

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript")
    chapter = relationship("Chapter")

    def __repr__(self):
        return f"<Recap(id={self.id}, type={self.recap_type}, manuscript={self.manuscript_id})>"
