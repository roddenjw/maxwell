"""
Privacy and AI Training Consent models

These models track author preferences for AI data usage and ensure
manuscripts are protected from being used for AI training while still
allowing AI assistance features.
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class ContentSharingLevel(str, enum.Enum):
    """
    How content can be shared with AI services.

    DEFAULT is ASSIST_NO_TRAINING - AI helps you write, but your content
    is never used to train AI models.
    """
    NO_AI = "no_ai"  # Paranoid mode: No AI access at all (fully offline)
    ASSIST_NO_TRAINING = "assist_no_training"  # DEFAULT: AI helps, but NO training
    ASSIST_WITH_TRAINING = "assist_with_training"  # Opt-in: AI helps AND can train

    # Aliases for backwards compatibility
    PRIVATE = "no_ai"
    AI_ASSIST_ONLY = "assist_no_training"
    FULL = "assist_with_training"


class ConsentType(str, enum.Enum):
    """Types of consent that can be granted"""
    AI_ASSISTANCE = "ai_assistance"
    TRAINING_DATA = "training_data"
    ANALYTICS = "analytics"


class AuthorPrivacyPreferences(Base):
    """
    Author-level privacy preferences for AI interactions.

    This tracks what AI features an author allows and whether they
    consent to any training data usage (default: NO).
    """
    __tablename__ = "author_privacy_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Link to manuscript (author is implicit from manuscript ownership)
    # In a multi-user system, this would link to a user_id instead
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False, unique=True)

    # Core privacy setting - NEVER train on user content by default
    allow_training_data = Column(Boolean, default=False, nullable=False)  # CRITICAL: default FALSE

    # Optional: completely disable AI (paranoid mode) - defaults to enabled
    allow_ai_assistance = Column(Boolean, default=True, nullable=False)

    # Data retention preferences
    ai_context_retention_days = Column(Integer, default=0)  # 0 = no retention

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    manuscript = relationship("Manuscript", backref="privacy_preferences")

    def __repr__(self):
        return f"<AuthorPrivacyPreferences(manuscript_id={self.manuscript_id}, training={self.allow_training_data})>"


class ConsentRecord(Base):
    """
    Audit log of consent changes for compliance (GDPR, CCPA, etc.)

    Every time an author changes their privacy preferences, we record it here.
    """
    __tablename__ = "consent_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)

    # What consent was given/revoked
    consent_type = Column(String, nullable=False)  # ConsentType value
    granted = Column(Boolean, nullable=False)

    # Consent metadata
    version = Column(String, default="1.0.0")  # Consent form version
    ip_address = Column(String, nullable=True)  # For audit trail
    user_agent = Column(String, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    manuscript = relationship("Manuscript", backref="consent_records")

    def __repr__(self):
        return f"<ConsentRecord(type={self.consent_type}, granted={self.granted})>"


class AIInteractionAudit(Base):
    """
    Audit log for AI interactions - tracks what was sent to AI providers.

    IMPORTANT: This does NOT store the actual content, only metadata
    about the interaction for auditing purposes.
    """
    __tablename__ = "ai_interaction_audit"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)

    # Interaction details (no raw content!)
    interaction_type = Column(String, nullable=False)  # 'edit_suggestion', 'summary', etc.
    provider = Column(String, nullable=False)  # 'anthropic', 'openai', etc.
    model = Column(String, nullable=False)

    # Token counts (for carbon tracking too)
    tokens_sent = Column(Integer, default=0)
    tokens_received = Column(Integer, default=0)

    # Privacy verification flags
    training_opted_out = Column(Boolean, default=True, nullable=False)
    zero_data_retention = Column(Boolean, default=False)

    # Content hash for verification (not the content itself)
    content_hash = Column(String(64), nullable=True)

    # Cost tracking
    estimated_cost_usd = Column(Integer, default=0)  # In microdollars (1M = $1)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    manuscript = relationship("Manuscript", backref="ai_interactions")

    def __repr__(self):
        return f"<AIInteractionAudit(type={self.interaction_type}, tokens={self.tokens_sent + self.tokens_received})>"
