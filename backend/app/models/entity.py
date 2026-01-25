"""
Entity models for The Codex (characters, locations, items, lore)
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


# Entity scope constants
ENTITY_SCOPE_MANUSCRIPT = "MANUSCRIPT"  # Entity belongs to single manuscript
ENTITY_SCOPE_SERIES = "SERIES"          # Entity shared across series
ENTITY_SCOPE_WORLD = "WORLD"            # Entity shared across entire world


# Entity template type constants (for structured templates)
TEMPLATE_TYPE_CHARACTER = "CHARACTER"
TEMPLATE_TYPE_LOCATION = "LOCATION"
TEMPLATE_TYPE_ITEM = "ITEM"
TEMPLATE_TYPE_MAGIC_SYSTEM = "MAGIC_SYSTEM"
TEMPLATE_TYPE_CREATURE = "CREATURE"
TEMPLATE_TYPE_ORGANIZATION = "ORGANIZATION"
TEMPLATE_TYPE_CUSTOM = "CUSTOM"  # User-defined structure


class Entity(Base):
    """Base entity for characters, locations, items, and lore"""
    __tablename__ = "entities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Manuscript scope (nullable when scope is WORLD or SERIES)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=True)

    # World scope (nullable when scope is MANUSCRIPT)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=True)

    # Scope determines visibility: MANUSCRIPT, SERIES, or WORLD
    scope = Column(String, default=ENTITY_SCOPE_MANUSCRIPT, nullable=False)

    # Entity type: CHARACTER, LOCATION, ITEM, LORE
    type = Column(String, nullable=False)

    # Template type for structured entity creation (CHARACTER, LOCATION, ITEM, MAGIC_SYSTEM, CREATURE, etc.)
    # When set, template_data follows a pre-defined structure
    template_type = Column(String, nullable=True)

    # Basic info
    name = Column(String, nullable=False)
    aliases = Column(JSON, default=list)  # Alternative names

    # Entity-specific attributes (stored as JSON for flexibility)
    # For CHARACTER: age, appearance, voice, personality, backstory
    # For LOCATION: description, atmosphere, geography
    # For ITEM: description, significance
    # For LORE: description, significance
    attributes = Column(JSON, default=dict)

    # Structured template data (follows template_type structure)
    # Example CHARACTER template_data:
    # {
    #   "role": "Protagonist",
    #   "physical": {"age": "32", "appearance": "...", "distinguishing_features": "..."},
    #   "personality": {"traits": [...], "flaws": "...", "strengths": "..."},
    #   "backstory": {"origin": "...", "key_events": "...", "secrets": "..."},
    #   "motivation": {"want": "...", "need": "..."},
    #   "relationships": [{"entity_id": "...", "type": "...", "notes": "..."}]
    # }
    template_data = Column(JSON, default=dict)

    # Appearance history
    # List of {scene_id, description, timestamp}
    appearance_history = Column(JSON, default=list)

    # For potential image generation
    image_seed = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", back_populates="entities", foreign_keys=[manuscript_id])
    world = relationship("World", back_populates="world_entities", foreign_keys=[world_id])
    source_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.source_entity_id",
        back_populates="source_entity",
        cascade="all, delete-orphan"
    )
    target_relationships = relationship(
        "Relationship",
        foreign_keys="Relationship.target_entity_id",
        back_populates="target_entity",
        cascade="all, delete-orphan"
    )
    appearances = relationship("EntityAppearance", back_populates="entity", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Entity(id={self.id}, type={self.type}, name='{self.name}')>"


class Relationship(Base):
    """Relationships between entities"""
    __tablename__ = "relationships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # The two entities involved
    source_entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    target_entity_id = Column(String, ForeignKey("entities.id"), nullable=False)

    # Relationship metadata
    relationship_type = Column(String, nullable=False)  # ROMANTIC, CONFLICT, ALLIANCE, etc.
    strength = Column(Integer, default=1)  # How many times they've interacted

    # Context - list of {scene_id, description}
    context = Column(JSON, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source_entity = relationship(
        "Entity",
        foreign_keys=[source_entity_id],
        back_populates="source_relationships"
    )
    target_entity = relationship(
        "Entity",
        foreign_keys=[target_entity_id],
        back_populates="target_relationships"
    )

    def __repr__(self):
        return f"<Relationship({self.relationship_type}, strength={self.strength})>"


class EntitySuggestion(Base):
    """Suggested entities detected by NLP that need user approval"""
    __tablename__ = "entity_suggestions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)

    # Suggested entity details
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    context = Column(Text)  # The text where it was found

    # Extracted information from NLP analysis
    # Description extracted from patterns like "X is a..." or "X was a..."
    extracted_description = Column(Text, nullable=True)
    # Categorized attributes: appearance, personality, actions, background
    extracted_attributes = Column(JSON, nullable=True)

    # Status: PENDING, APPROVED, REJECTED
    status = Column(String, default="PENDING")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EntitySuggestion(name='{self.name}', type={self.type}, status={self.status})>"


class EntitySourceReference(Base):
    """
    Tracks where entity information came from in the manuscript.
    Links entity template fields to specific text locations for:
    - Auto-population from manuscript text
    - Conflict detection ("we found conflicting descriptions")
    - Source attribution ("this came from Chapter 3")
    """
    __tablename__ = "entity_source_references"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)

    # Which template field this reference populates
    # e.g., "physical.appearance", "backstory.origin", "motivation.want"
    field_path = Column(String, nullable=False)

    # Source location in manuscript
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)

    # The actual text excerpt that was extracted
    text_excerpt = Column(Text, nullable=False)

    # Position in chapter (for precise location)
    character_offset = Column(Integer, nullable=True)

    # Whether user confirmed this auto-extraction
    is_confirmed = Column(String, default="PENDING")  # PENDING, CONFIRMED, REJECTED

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    entity = relationship("Entity", backref="source_references")
    chapter = relationship("Chapter", foreign_keys=[chapter_id])

    def __repr__(self):
        return f"<EntitySourceReference(entity_id={self.entity_id}, field='{self.field_path}')>"
