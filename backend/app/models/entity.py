"""
Entity models for The Codex (characters, locations, items, lore)
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Entity(Base):
    """Base entity for characters, locations, items, and lore"""
    __tablename__ = "entities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)

    # Entity type: CHARACTER, LOCATION, ITEM, LORE
    type = Column(String, nullable=False)

    # Basic info
    name = Column(String, nullable=False)
    aliases = Column(JSON, default=list)  # Alternative names

    # Entity-specific attributes (stored as JSON for flexibility)
    # For CHARACTER: age, appearance, voice, personality, backstory
    # For LOCATION: description, atmosphere, geography
    # For ITEM: description, significance
    # For LORE: description, significance
    attributes = Column(JSON, default=dict)

    # Appearance history
    # List of {scene_id, description, timestamp}
    appearance_history = Column(JSON, default=list)

    # For potential image generation
    image_seed = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", back_populates="entities")
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

    # Status: PENDING, APPROVED, REJECTED
    status = Column(String, default="PENDING")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<EntitySuggestion(name='{self.name}', type={self.type}, status={self.status})>"
