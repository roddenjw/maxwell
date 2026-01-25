"""
Shareable Recap Model
Stores generated recap cards for sharing with Open Graph support
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, LargeBinary
from datetime import datetime
import uuid

from app.database import Base


class ShareableRecap(Base):
    """Stores shareable recap cards with OG metadata"""
    __tablename__ = "shareable_recaps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Short share ID for URLs (6 chars)
    share_id = Column(String(6), unique=True, nullable=False, index=True)

    # Source reference
    manuscript_id = Column(String, nullable=False)
    chapter_id = Column(String, nullable=True)  # Null for writing stats recaps

    # Recap type: 'chapter' or 'writing_stats'
    recap_type = Column(String, default="chapter", nullable=False)

    # Open Graph metadata
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Image data (PNG blob, cached for performance)
    image_data = Column(LargeBinary, nullable=True)
    image_content_type = Column(String, default="image/png")

    # Template used to generate
    template = Column(String, default="dark")

    # Analytics
    view_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)

    # Full recap content for regeneration
    recap_content = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration

    def __repr__(self):
        return f"<ShareableRecap(share_id={self.share_id}, type={self.recap_type})>"


def generate_share_id() -> str:
    """Generate a short, URL-safe share ID"""
    import random
    import string
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(6))
