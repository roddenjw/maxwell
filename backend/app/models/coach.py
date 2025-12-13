"""
Models for The Coach - Personalized Learning Agent
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from datetime import datetime
import uuid

from app.database import Base


class WritingProfile(Base):
    """User's learned writing profile"""
    __tablename__ = "writing_profiles"

    user_id = Column(String, primary_key=True)

    # Profile data stored as JSON
    # Structure: {
    #   "style_metrics": {...},
    #   "strengths": [...],
    #   "weaknesses": [...],
    #   "preferences": {...},
    #   "overused_words": {...},
    #   "favorite_techniques": [...]
    # }
    profile_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<WritingProfile(user_id={self.user_id})>"


class CoachingHistory(Base):
    """History of coaching interactions for learning"""
    __tablename__ = "coaching_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=True)

    # The text that was analyzed
    scene_text = Column(Text, nullable=False)

    # Agent's feedback (stored as JSON)
    agent_feedback = Column(JSON, nullable=False)

    # User's reaction: ACCEPTED, REJECTED, MODIFIED, IGNORED
    user_reaction = Column(String, nullable=True)

    # Feedback type: SUGGESTION, WARNING, PRAISE, CRITIQUE
    feedback_type = Column(String, default="SUGGESTION")

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CoachingHistory(id={self.id}, reaction={self.user_reaction})>"


class FeedbackPattern(Base):
    """Recurring patterns observed in user's writing"""
    __tablename__ = "feedback_patterns"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("writing_profiles.user_id"), nullable=False)

    # Pattern type: OVERUSED_WORD, PACING_ISSUE, CONSISTENCY_ERROR, etc.
    pattern_type = Column(String, nullable=False)

    # Description of the pattern
    pattern_description = Column(Text, nullable=False)

    # How many times observed
    frequency = Column(Integer, default=1)

    # Last occurrence
    last_occurred = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FeedbackPattern(type={self.pattern_type}, freq={self.frequency})>"
