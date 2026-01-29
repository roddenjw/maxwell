"""
Versioning models for Time Machine functionality
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Snapshot(Base):
    """Git-backed snapshot of manuscript state"""
    __tablename__ = "snapshots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)

    # Git commit hash
    commit_hash = Column(String, nullable=False)

    # Snapshot metadata
    label = Column(String, default="")  # User-provided label
    description = Column(Text, default="")

    # Trigger type: MANUAL, AUTO, CHAPTER_COMPLETE, PRE_GENERATION, SESSION_END
    trigger_type = Column(String, nullable=False)

    # Word count at time of snapshot
    word_count = Column(Integer, default=0)

    # Auto-generated changeset summary (like commit messages)
    auto_summary = Column(Text, default="")

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", back_populates="snapshots")

    def __repr__(self):
        return f"<Snapshot(id={self.id}, label='{self.label}', trigger={self.trigger_type})>"
