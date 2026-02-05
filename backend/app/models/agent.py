"""
Agent Database Models

Models for agent analysis results, coaching sessions, and author learning.
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, JSON, Boolean
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


# ==================== Maxwell Memory Models ====================


class MaxwellConversation(Base):
    """
    Stores Maxwell conversation history for persistent memory.

    Enables Maxwell to reference previous conversations:
    "You mentioned before that pacing was a concern..."
    """
    __tablename__ = "maxwell_conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=True, index=True)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)

    # Interaction details
    interaction_type = Column(String, nullable=False)  # chat, analysis, quick_check, explain
    user_message = Column(Text, nullable=True)  # User's input (for chat)
    analyzed_text = Column(Text, nullable=True)  # Text that was analyzed
    maxwell_response = Column(Text, nullable=False)  # Maxwell's response
    response_type = Column(String, nullable=False)  # chat, analysis, quick_check, explanation

    # Structured feedback data (for analysis responses)
    feedback_data = Column(JSON, default=dict)  # {priorities, highlights, teaching_moments}

    # Context
    agents_consulted = Column(JSON, default=list)  # Which agents contributed
    focus_area = Column(String, nullable=True)  # For quick checks: style, voice, etc.

    # Performance metrics
    cost = Column(Float, default=0.0)
    tokens = Column(Integer, default=0)
    execution_time_ms = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", foreign_keys=[manuscript_id])
    insights = relationship("MaxwellInsight", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MaxwellConversation(id={self.id}, type={self.interaction_type})>"


class MaxwellInsight(Base):
    """
    Extracted insights from Maxwell conversations.

    Enables quick retrieval of key points for context-aware responses.
    """
    __tablename__ = "maxwell_insights"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=True, index=True)
    conversation_id = Column(String, ForeignKey("maxwell_conversations.id"), nullable=False)

    # Insight details
    category = Column(String, nullable=False)  # character, plot, style, pacing, dialogue, etc.
    insight_text = Column(Text, nullable=False)
    subject = Column(String, nullable=True)  # Character name, chapter, etc.

    # Sentiment and importance
    sentiment = Column(String, default="neutral")  # positive, negative, suggestion, neutral
    importance = Column(Float, default=0.5)  # 0.0 to 1.0

    # Resolution tracking
    resolved = Column(String, default="pending")  # pending, addressed, dismissed

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("MaxwellConversation", back_populates="insights")

    def __repr__(self):
        return f"<MaxwellInsight(id={self.id}, category={self.category})>"


class MaxwellPreferences(Base):
    """
    User preferences for Maxwell's behavior.

    Allows customization of tone, depth, and focus areas.
    """
    __tablename__ = "maxwell_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, unique=True, index=True)

    # Voice preferences
    preferred_tone = Column(String, default="encouraging")  # encouraging, direct, teaching, celebratory, formal, casual
    feedback_depth = Column(String, default="standard")  # brief, standard, comprehensive
    teaching_mode = Column(String, default="auto")  # on, off, auto
    priority_focus = Column(String, default="all")  # plot, character, prose, pacing, all

    # Proactive suggestions
    proactive_suggestions = Column(String, default="on")  # on, off, minimal

    # Additional preferences as JSON for flexibility
    extra_preferences = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MaxwellPreferences(user={self.user_id})>"


# ==================== Proactive Suggestions Models ====================


class ProactiveNudge(Base):
    """
    Proactive suggestions from Maxwell.

    Gentle nudges based on detected patterns or issues.
    """
    __tablename__ = "proactive_nudges"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=True, index=True)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)

    # Nudge content
    nudge_type = Column(String, nullable=False)  # consistency_issue, pacing_concern, character_drift, etc.
    priority = Column(String, default="medium")  # low, medium, high
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)

    # Deduplication
    content_hash = Column(String, nullable=True, index=True)

    # Status
    dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime, nullable=True)
    viewed = Column(Boolean, default=False)
    viewed_at = Column(DateTime, nullable=True)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ProactiveNudge(id={self.id}, type={self.nudge_type})>"


class WeeklyInsight(Base):
    """
    Weekly writing insights for users.

    Summarizes writing activity and patterns over the past week.
    """
    __tablename__ = "weekly_insights"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)

    # Insight content
    summary = Column(Text, nullable=False)
    highlights = Column(JSON, default=list)  # What went well
    areas_to_improve = Column(JSON, default=list)  # Suggestions

    # Activity metrics
    word_count_total = Column(Integer, default=0)
    chapters_worked_on = Column(Integer, default=0)
    most_active_day = Column(String, nullable=True)

    # Analysis stats
    analyses_run = Column(Integer, default=0)
    issues_found = Column(Integer, default=0)
    issues_addressed = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WeeklyInsight(user={self.user_id}, week={self.week_start})>"
