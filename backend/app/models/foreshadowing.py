"""
Foreshadowing Database Models

Tracks setup/payoff pairs for narrative foreshadowing including:
- Chekhov's guns (objects that must be used)
- Prophecies (predictions to fulfill)
- Symbols (recurring symbols)
- Hints (subtle clues)
- Parallels (repeated patterns)
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum
from app.database import Base
import uuid
from datetime import datetime
import enum


class ForeshadowingType(enum.Enum):
    """Types of foreshadowing"""
    CHEKHOV_GUN = "CHEKHOV_GUN"  # Object that must be used
    PROPHECY = "PROPHECY"  # Prediction to fulfill
    SYMBOL = "SYMBOL"  # Recurring symbol
    HINT = "HINT"  # Subtle clue
    PARALLEL = "PARALLEL"  # Repeated pattern


class ForeshadowingPair(Base):
    """
    Represents a foreshadowing setup/payoff pair.

    Tracks:
    - The setup event (where foreshadowing is introduced)
    - The payoff event (where foreshadowing is resolved)
    - The type of foreshadowing
    - Resolution status
    - Confidence level (how obvious the connection is)
    """
    __tablename__ = "foreshadowing_pairs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, nullable=False, index=True)

    # Foreshadowing setup
    foreshadowing_event_id = Column(String, ForeignKey("timeline_events.id"), nullable=False)
    foreshadowing_type = Column(String, nullable=False, default="HINT")  # CHEKHOV_GUN, PROPHECY, etc.
    foreshadowing_text = Column(Text, nullable=False)  # Description of the setup

    # Payoff (nullable - may not be resolved yet)
    payoff_event_id = Column(String, ForeignKey("timeline_events.id"), nullable=True)
    payoff_text = Column(Text, nullable=True)  # Description of the payoff

    # Status
    is_resolved = Column(Integer, default=0)  # 0 = unresolved, 1 = resolved
    confidence = Column(Integer, default=5)  # 1-10 scale (how obvious the connection is)

    # Notes
    notes = Column(Text, nullable=True)  # Author's notes about the connection

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# Export for alembic migrations
__all__ = ["ForeshadowingPair", "ForeshadowingType"]
