"""
World and Series models for Library & World Management
Enables hierarchical organization: World → Series → Manuscript
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class World(Base):
    """
    A world represents a shared fictional universe.
    All entities and lore can be shared across manuscripts within the same world.
    """
    __tablename__ = "worlds"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, default="")

    # World settings (genre, magic rules, technology level, etc.)
    settings = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    series = relationship("Series", back_populates="world", cascade="all, delete-orphan")
    # World-scoped entities (shared across all manuscripts in this world)
    world_entities = relationship(
        "Entity",
        back_populates="world",
        foreign_keys="Entity.world_id",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<World(id={self.id}, name='{self.name}')>"


class Series(Base):
    """
    A series groups manuscripts within a world.
    Represents a book series, trilogy, or standalone collection.
    """
    __tablename__ = "series"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(Text, default="")

    # Display ordering within the world
    order_index = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    world = relationship("World", back_populates="series")
    manuscripts = relationship("Manuscript", back_populates="series")

    def __repr__(self):
        return f"<Series(id={self.id}, name='{self.name}', world_id={self.world_id})>"
