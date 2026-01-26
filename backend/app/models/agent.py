"""
Agent Database Models

Models for agent analysis results, coaching sessions, and author learning.
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class AgentAnalysis(Base):
    """
    Stores results from agent analysis runs.

    Captures what agents found, recommendations made, and performance metrics.
    Used for:
    - Displaying results to users
    - Learning from patterns
    - Tracking agent performance
    """
    __tablename__ = "agent_analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False, index=True)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)

    # What was analyzed
    input_text = Column(Text, nullable=False)
    input_hash = Column(String, nullable=True)  # For deduplication

    # Which agents ran
    agent_types = Column(JSON, nullable=False)  # List of agent types that ran

    # Combined results
    recommendations = Column(JSON, default=list)  # List of recommendation objects
    issues = Column(JSON, default=list)  # List of issue objects
    teaching_points = Column(JSON, default=list)  # List of teaching strings

    # Individual agent results (for debugging/analysis)
    agent_results = Column(JSON, default=dict)  # {agent_type: result_dict}

    # Performance metrics
    total_cost = Column(Float, default=0.0)  # Total USD cost
    total_tokens = Column(Integer, default=0)  # Total tokens used
    execution_time_ms = Column(Integer, default=0)  # Total time in ms

    # User feedback on this analysis
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    user_feedback = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", backref="agent_analyses")
    chapter = relationship("Chapter", foreign_keys=[chapter_id])

    def __repr__(self):
        return f"<AgentAnalysis(id={self.id}, agents={self.agent_types})>"


class CoachSession(Base):
    """
    Coaching conversation session.

    Tracks a conversation between the user and the Smart Coach agent.
    """
    __tablename__ = "coach_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=True)

    # Session metadata
    title = Column(String, default="Coaching Session")
    status = Column(String, default="active")  # active, archived

    # Context at session start
    initial_context = Column(JSON, default=dict)  # Chapter ID, selected text, etc.

    # Session metrics
    message_count = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    total_tokens = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)

    # Relationships
    manuscript = relationship("Manuscript", backref="coach_sessions")
    messages = relationship("CoachMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CoachSession(id={self.id}, messages={self.message_count})>"


class CoachMessage(Base):
    """
    Individual message in a coaching session.
    """
    __tablename__ = "coach_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("coach_sessions.id"), nullable=False)

    # Message content
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text, nullable=False)

    # For assistant messages: what tools were used
    tools_used = Column(JSON, default=list)  # List of tool names
    tool_results = Column(JSON, default=dict)  # Tool outputs (summarized)

    # Cost tracking (for assistant messages)
    cost = Column(Float, default=0.0)
    tokens = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("CoachSession", back_populates="messages")

    def __repr__(self):
        return f"<CoachMessage(id={self.id}, role={self.role})>"


class AuthorLearning(Base):
    """
    Tracks what the system has learned about an author's preferences.

    Aggregates feedback patterns to personalize future suggestions.
    """
    __tablename__ = "author_learning"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("writing_profiles.user_id"), nullable=False, index=True)

    # Learning category
    category = Column(String, nullable=False)  # style, structure, voice, general

    # Pattern data
    pattern_type = Column(String, nullable=False)  # accepted_suggestion, rejected_suggestion, preference, etc.
    pattern_key = Column(String, nullable=False)  # Specific pattern identifier

    # Pattern details
    pattern_data = Column(JSON, default=dict)
    # Structure depends on pattern_type:
    # accepted_suggestion: {suggestion_type, count, examples}
    # rejected_suggestion: {suggestion_type, count, reasons}
    # preference: {preference_key, value, confidence}

    # Confidence score (0.0 to 1.0)
    confidence = Column(Float, default=0.5)

    # How many times this pattern has been observed
    observation_count = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AuthorLearning(user={self.user_id}, pattern={self.pattern_key})>"


class SuggestionFeedback(Base):
    """
    Tracks user response to individual suggestions.

    Used to train the learning system and improve personalization.
    """
    __tablename__ = "suggestion_feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    analysis_id = Column(String, ForeignKey("agent_analyses.id"), nullable=True)

    # What suggestion this feedback is for
    agent_type = Column(String, nullable=False)  # Which agent made the suggestion
    suggestion_type = Column(String, nullable=False)  # Type of suggestion
    suggestion_text = Column(Text, nullable=False)

    # Context
    original_text = Column(Text, nullable=True)  # What was being analyzed
    manuscript_id = Column(String, nullable=True)

    # User's response
    action = Column(String, nullable=False)  # accepted, rejected, modified, ignored

    # For modifications: what did they change it to?
    modified_text = Column(Text, nullable=True)

    # Optional explanation from user
    user_explanation = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SuggestionFeedback(id={self.id}, action={self.action})>"
