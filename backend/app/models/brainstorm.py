"""
Brainstorming models for AI-powered idea generation
Supports character, plot, world-building, and conflict brainstorming
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class BrainstormSession(Base):
    """Brainstorming session tracker"""
    __tablename__ = "brainstorm_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)
    outline_id = Column(String, ForeignKey("outlines.id"), nullable=True)

    # Session metadata
    session_type = Column(String, nullable=False)  # 'CHARACTER', 'PLOT_BEAT', 'WORLD', 'CONFLICT'
    context_data = Column(JSON, default=dict)  # Genre, structure, existing entities, etc.

    # Status tracking
    status = Column(String, default='IN_PROGRESS')  # IN_PROGRESS, COMPLETED, ABANDONED

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", backref="brainstorm_sessions")
    outline = relationship("Outline", backref="brainstorm_sessions")
    ideas = relationship("BrainstormIdea", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BrainstormSession(id={self.id}, type='{self.session_type}', status='{self.status}')>"


class BrainstormIdea(Base):
    """Individual ideas generated during brainstorming"""
    __tablename__ = "brainstorm_ideas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("brainstorm_sessions.id"), nullable=False)

    # Idea content
    idea_type = Column(String, nullable=False)  # Matches session_type
    title = Column(String, nullable=False)  # Short title/name
    description = Column(Text, nullable=False)  # Full AI-generated content
    idea_metadata = Column(JSON, default=dict)  # Type-specific attributes (want, need, flaw, etc.)

    # User actions
    is_selected = Column(Boolean, default=False)
    user_notes = Column(Text, default="")
    edited_content = Column(Text, nullable=True)  # User's edited version

    # Integration tracking
    integrated_to_outline = Column(Boolean, default=False)
    integrated_to_codex = Column(Boolean, default=False)
    plot_beat_id = Column(String, ForeignKey("plot_beats.id"), nullable=True)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=True)

    # AI metadata
    ai_cost = Column(Float, default=0.0)
    ai_tokens = Column(Integer, default=0)
    ai_model = Column(String, default="anthropic/claude-3.5-sonnet")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("BrainstormSession", back_populates="ideas")
    plot_beat = relationship("PlotBeat", foreign_keys=[plot_beat_id])
    entity = relationship("Entity", foreign_keys=[entity_id])

    def __repr__(self):
        status_icon = "✓" if self.is_selected else "○"
        return f"<BrainstormIdea(id={self.id}, title='{self.title}', {status_icon})>"
