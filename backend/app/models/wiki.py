"""
World Wiki models - the unified narrative backbone.

WikiEntry: Core building block of the World Wiki
WikiChange: Pending AI changes awaiting author approval
WikiCrossReference: Links between wiki entries
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

from app.database import Base


class WikiEntryType(str, Enum):
    """Types of wiki entries"""
    # Characters
    CHARACTER = "character"
    CHARACTER_ARC = "character_arc"
    CHARACTER_RELATIONSHIP = "character_relationship"

    # Locations
    LOCATION = "location"
    LOCATION_HISTORY = "location_history"

    # World Rules
    MAGIC_SYSTEM = "magic_system"
    WORLD_RULE = "world_rule"
    TECHNOLOGY = "technology"
    CULTURE = "culture"
    RELIGION = "religion"

    # Narrative Elements
    FACTION = "faction"
    ARTIFACT = "artifact"
    CREATURE = "creature"
    EVENT = "event"  # Historical events

    # Meta
    TIMELINE_FACT = "timeline_fact"
    THEME = "theme"


class WikiEntryStatus(str, Enum):
    """Status of wiki entries"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class WikiChangeType(str, Enum):
    """Types of wiki changes"""
    CREATE = "create"
    UPDATE = "update"
    MERGE = "merge"
    DELETE = "delete"


class WikiChangeStatus(str, Enum):
    """Status of wiki changes in approval queue"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class WikiReferenceType(str, Enum):
    """Types of cross-references between wiki entries"""
    MENTIONS = "mentions"
    RELATED_TO = "related_to"
    PART_OF = "part_of"
    CONFLICTS_WITH = "conflicts_with"
    DEPENDS_ON = "depends_on"
    CHILD_OF = "child_of"
    ALLY_OF = "ally_of"
    ENEMY_OF = "enemy_of"
    OWNS = "owns"
    MEMBER_OF = "member_of"
    LOCATED_IN = "located_in"

    # Culture-specific reference types
    BORN_IN = "born_in"
    EXILED_FROM = "exiled_from"
    ADOPTED_INTO = "adopted_into"
    LEADER_OF = "leader_of"
    REBEL_AGAINST = "rebel_against"
    WORSHIPS = "worships"
    TRADES_WITH = "trades_with"
    ORIGINATED_IN = "originated_in"
    SACRED_TO = "sacred_to"
    RESENTS = "resents"


class WikiEntry(Base):
    """
    Core wiki entry - the building block of the World Wiki.

    Lives at World/Series level and is shared across manuscripts.
    Can be auto-populated by AI or manually created by author.
    """
    __tablename__ = "wiki_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)

    # Entry metadata
    entry_type = Column(String, nullable=False)  # WikiEntryType value
    title = Column(String, nullable=False)
    slug = Column(String, nullable=False)  # URL-friendly: "john-smith"

    # Content (structured JSON for type-specific fields + free-form)
    structured_data = Column(JSON, default=dict)  # Type-specific fields
    content = Column(Text)  # Free-form markdown content
    summary = Column(Text)  # AI-generated summary

    # Image/visual
    image_url = Column(String, nullable=True)
    image_seed = Column(Integer, nullable=True)

    # Hierarchical organization
    parent_id = Column(String, ForeignKey("wiki_entries.id"), nullable=True)

    # Link to Codex entity (if this wiki entry originated from an entity)
    linked_entity_id = Column(String, ForeignKey("entities.id"), nullable=True)

    # Source tracking - which manuscripts/chapters reference this
    source_manuscripts = Column(JSON, default=list)  # List of manuscript IDs
    source_chapters = Column(JSON, default=list)  # List of {manuscript_id, chapter_id, excerpt}

    # Status and confidence
    status = Column(String, default=WikiEntryStatus.DRAFT.value)
    confidence_score = Column(Float, default=1.0)  # How confident is the data (1.0 = manual, <1.0 = AI)
    last_verified_at = Column(DateTime, nullable=True)

    # Metadata
    tags = Column(JSON, default=list)  # User-defined tags
    aliases = Column(JSON, default=list)  # Alternative names for search

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, default="author")  # "ai" or "author"

    # Relationships
    world = relationship("World", backref="wiki_entries")
    parent = relationship("WikiEntry", remote_side=[id], backref="children")
    linked_entity = relationship("Entity", backref="wiki_entry")

    # Cross-references (outgoing)
    outgoing_references = relationship(
        "WikiCrossReference",
        foreign_keys="WikiCrossReference.source_entry_id",
        back_populates="source_entry",
        cascade="all, delete-orphan"
    )

    # Cross-references (incoming)
    incoming_references = relationship(
        "WikiCrossReference",
        foreign_keys="WikiCrossReference.target_entry_id",
        back_populates="target_entry",
        cascade="all, delete-orphan"
    )

    # Pending changes
    pending_changes = relationship(
        "WikiChange",
        back_populates="wiki_entry",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<WikiEntry(id={self.id}, type={self.entry_type}, title='{self.title}')>"


class WikiChange(Base):
    """
    Pending changes from AI that need author approval.

    All AI-suggested updates go through this approval queue
    before being applied to wiki entries.
    """
    __tablename__ = "wiki_changes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    wiki_entry_id = Column(String, ForeignKey("wiki_entries.id"), nullable=True)  # Null for new entries
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)

    # Change details
    change_type = Column(String, nullable=False)  # WikiChangeType value
    field_changed = Column(String, nullable=True)  # Which field, or null for full entry
    old_value = Column(JSON, nullable=True)  # Previous value (for updates)
    new_value = Column(JSON, nullable=False)  # Proposed new value

    # For CREATE changes, this holds the full proposed entry
    proposed_entry = Column(JSON, nullable=True)

    # AI reasoning
    reason = Column(Text)  # Why AI suggests this change
    source_text = Column(Text)  # The manuscript text that triggered this
    source_chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)
    source_manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=True)
    confidence = Column(Float, default=0.8)  # AI confidence in this suggestion

    # Status
    status = Column(String, default=WikiChangeStatus.PENDING.value)
    reviewed_at = Column(DateTime, nullable=True)
    reviewer_note = Column(Text, nullable=True)  # Author's note on approval/rejection

    # Priority for sorting in queue
    priority = Column(Integer, default=0)  # Higher = more important

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    wiki_entry = relationship("WikiEntry", back_populates="pending_changes")
    world = relationship("World", backref="wiki_changes")
    source_chapter = relationship("Chapter", foreign_keys=[source_chapter_id])
    source_manuscript = relationship("Manuscript", foreign_keys=[source_manuscript_id])

    def __repr__(self):
        return f"<WikiChange(id={self.id}, type={self.change_type}, status={self.status})>"


class WikiCrossReference(Base):
    """
    Links between wiki entries.

    Enables rich interconnections like:
    - Character A is an ally of Character B
    - Location X is part of Region Y
    - Artifact Z is owned by Character A
    """
    __tablename__ = "wiki_cross_references"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_entry_id = Column(String, ForeignKey("wiki_entries.id"), nullable=False)
    target_entry_id = Column(String, ForeignKey("wiki_entries.id"), nullable=False)

    # Reference type
    reference_type = Column(String, nullable=False)  # WikiReferenceType value

    # Additional context
    context = Column(Text, nullable=True)  # Where/why this reference exists
    context_chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)

    # Display options
    bidirectional = Column(Integer, default=1)  # Show on both entries? (1=yes, 0=no)
    display_label = Column(String, nullable=True)  # Custom label override

    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, default="author")  # "ai" or "author"

    # Relationships
    source_entry = relationship(
        "WikiEntry",
        foreign_keys=[source_entry_id],
        back_populates="outgoing_references"
    )
    target_entry = relationship(
        "WikiEntry",
        foreign_keys=[target_entry_id],
        back_populates="incoming_references"
    )
    context_chapter = relationship("Chapter", foreign_keys=[context_chapter_id])

    def __repr__(self):
        return f"<WikiCrossReference({self.reference_type}: {self.source_entry_id} -> {self.target_entry_id})>"
