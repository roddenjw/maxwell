"""
Outline and Plot Beat models for story structure planning
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Outline(Base):
    """Story outline with structure template"""
    __tablename__ = "outlines"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)

    # Structure configuration
    structure_type = Column(String, nullable=False)  # 'story-arc-9', 'screenplay-15', 'mythic-quest', '3-act', 'custom'
    genre = Column(String, nullable=True)  # 'fantasy', 'thriller', 'romance', 'mystery', 'sci-fi', etc.

    # Target metrics
    target_word_count = Column(Integer, default=80000)  # Default novel length

    # Outline content
    premise = Column(Text, default="")  # One-sentence story premise
    logline = Column(Text, default="")  # Marketing logline
    synopsis = Column(Text, default="")  # Full story synopsis

    # Additional metadata
    notes = Column(Text, default="")  # User notes
    settings = Column(JSON, default=dict)  # Custom settings for outline

    # Status
    is_active = Column(Boolean, default=True)  # Is this the active outline for the manuscript?

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", backref="outlines")
    plot_beats = relationship("PlotBeat", back_populates="outline", cascade="all, delete-orphan", order_by="PlotBeat.order_index")

    def __repr__(self):
        return f"<Outline(id={self.id}, structure='{self.structure_type}', genre='{self.genre}')>"


class PlotBeat(Base):
    """Individual plot beat/story structure checkpoint"""
    __tablename__ = "plot_beats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    outline_id = Column(String, ForeignKey("outlines.id"), nullable=False)

    # Beat identification
    beat_name = Column(String, nullable=False)  # 'hook', 'inciting-incident', 'first-plot-point', 'midpoint', etc.
    beat_label = Column(String, nullable=False)  # User-facing label (can be customized)
    beat_description = Column(Text, default="")  # Template description of what should happen

    # Position in story
    target_position_percent = Column(Float, nullable=False)  # 0.0 to 1.0 (e.g., 0.12 = 12%)
    target_word_count = Column(Integer, default=0)  # Calculated from target_position_percent * outline.target_word_count
    actual_word_count = Column(Integer, default=0)  # Actual word count at this beat
    order_index = Column(Integer, nullable=False)  # Order within outline

    # Content
    user_notes = Column(Text, default="")  # User's planned content for this beat
    content_summary = Column(Text, default="")  # Summary of what was written

    # Linking to manuscript
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)  # Which chapter contains this beat?
    is_completed = Column(Boolean, default=False)  # Has this beat been written?

    # Brainstorming integration
    brainstorm_source_id = Column(String, ForeignKey("brainstorm_ideas.id"), nullable=True)  # Which brainstorm idea generated this?

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)  # When was this beat completed?

    # Relationships
    outline = relationship("Outline", back_populates="plot_beats")
    chapter = relationship("Chapter", foreign_keys=[chapter_id])

    def __repr__(self):
        status = "✓" if self.is_completed else "○"
        return f"<PlotBeat(id={self.id}, beat='{self.beat_name}', {status})>"
