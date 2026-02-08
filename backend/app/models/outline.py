"""
Outline and Plot Beat models for story structure planning
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib
import uuid

from app.database import Base


# Item type constants for PlotBeat
ITEM_TYPE_BEAT = "BEAT"    # Major story beat from structure template
ITEM_TYPE_SCENE = "SCENE"  # User-added scene between beats

# Outline scope constants
OUTLINE_SCOPE_MANUSCRIPT = "MANUSCRIPT"  # Single manuscript outline
OUTLINE_SCOPE_SERIES = "SERIES"          # Series-level outline spanning multiple books
OUTLINE_SCOPE_WORLD = "WORLD"            # World-level meta-arc across all series


class Outline(Base):
    """Story outline with structure template - supports manuscript, series, or world scope"""
    __tablename__ = "outlines"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Scope anchors (one should be set based on scope)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=True)  # For MANUSCRIPT scope
    series_id = Column(String, ForeignKey("series.id"), nullable=True)  # For SERIES scope
    world_id = Column(String, ForeignKey("worlds.id"), nullable=True)  # For WORLD scope

    # Scope determines the level of this outline
    scope = Column(String, default=OUTLINE_SCOPE_MANUSCRIPT, nullable=False)

    # Structure configuration
    structure_type = Column(String, nullable=False)  # 'story-arc-9', 'screenplay-15', 'mythic-quest', '3-act', 'trilogy-arc', 'custom'
    genre = Column(String, nullable=True)  # 'fantasy', 'thriller', 'romance', 'mystery', 'sci-fi', etc.

    # Series-specific fields
    arc_type = Column(String, nullable=True)  # For series: 'trilogy', 'ongoing', 'duology', 'saga'
    book_count = Column(Integer, nullable=True)  # Planned number of books in series

    # Target metrics
    target_word_count = Column(Integer, default=80000)  # Default novel length (or series total)

    # Outline content
    premise = Column(Text, default="")  # One-sentence story premise
    logline = Column(Text, default="")  # Marketing logline
    synopsis = Column(Text, default="")  # Full story synopsis

    # Additional metadata
    notes = Column(Text, default="")  # User notes
    settings = Column(JSON, default=dict)  # Custom settings for outline

    # Status
    is_active = Column(Boolean, default=True)  # Is this the active outline for the manuscript/series/world?

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", backref="outlines", foreign_keys=[manuscript_id])
    series = relationship("Series", backref="outlines", foreign_keys=[series_id])
    world = relationship("World", backref="outlines", foreign_keys=[world_id])
    plot_beats = relationship("PlotBeat", back_populates="outline", cascade="all, delete-orphan", order_by="PlotBeat.order_index", foreign_keys="[PlotBeat.outline_id]")

    def __repr__(self):
        return f"<Outline(id={self.id}, structure='{self.structure_type}', genre='{self.genre}')>"


class PlotBeat(Base):
    """Individual plot beat/story structure checkpoint or user-added scene"""
    __tablename__ = "plot_beats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    outline_id = Column(String, ForeignKey("outlines.id"), nullable=False)

    # Item type: BEAT (major story beat) or SCENE (user-added between beats)
    item_type = Column(String, default=ITEM_TYPE_BEAT, nullable=False)

    # For SCENE items: links to the beat this scene follows
    parent_beat_id = Column(String, ForeignKey("plot_beats.id"), nullable=True)

    # Beat identification
    beat_name = Column(String, nullable=False)  # 'hook', 'inciting-incident', 'first-plot-point', 'midpoint', or 'scene-{n}' for scenes
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

    # Series outline linking
    linked_manuscript_outline_id = Column(String, ForeignKey("outlines.id"), nullable=True)  # Link series beat to specific manuscript outline
    target_book_index = Column(Integer, nullable=True)  # Which book in the series (1, 2, 3...)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)  # When was this beat completed?

    # Relationships
    outline = relationship("Outline", back_populates="plot_beats", foreign_keys=[outline_id])
    chapter = relationship("Chapter", foreign_keys=[chapter_id])
    linked_manuscript_outline = relationship("Outline", foreign_keys=[linked_manuscript_outline_id])

    # Self-referential relationship for scenes following a beat
    parent_beat = relationship(
        "PlotBeat",
        remote_side=[id],
        foreign_keys=[parent_beat_id],
        backref="child_scenes"
    )

    def __repr__(self):
        type_indicator = "📍" if self.item_type == ITEM_TYPE_BEAT else "🎬"
        status = "✓" if self.is_completed else "○"
        return f"<PlotBeat(id={self.id}, type={type_indicator}, beat='{self.beat_name}', {status})>"


def compute_plot_hole_hash(issue: str, location: str) -> str:
    """Compute a short hash to identify a specific plot hole across re-analyses"""
    return hashlib.sha256(f"{issue}:{location}".encode()).hexdigest()[:16]


class PlotHoleDismissal(Base):
    """Tracks user responses to AI-detected plot holes (dismissed or accepted)"""
    __tablename__ = "plot_hole_dismissals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    outline_id = Column(String, ForeignKey("outlines.id"), nullable=False)

    # Plot hole identity — hash of issue+location to match across re-analyses
    plot_hole_hash = Column(String, nullable=False)

    # The original plot hole data (for display)
    severity = Column(String, nullable=False)  # high, medium, low
    location = Column(String, nullable=False)
    issue = Column(String, nullable=False)
    suggestion = Column(String, nullable=True)

    # User response
    status = Column(String, nullable=False, default="dismissed")  # dismissed, accepted
    user_explanation = Column(Text, nullable=True)  # Why it's intentional (for dismissed)
    ai_fix_suggestions = Column(JSON, nullable=True)  # AI-generated fix suggestions (for accepted)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    outline = relationship("Outline", backref="plot_hole_dismissals")
