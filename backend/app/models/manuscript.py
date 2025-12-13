"""
Manuscript and Scene models
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Manuscript(Base):
    """Main manuscript/book entity"""
    __tablename__ = "manuscripts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    author = Column(String, default="")
    description = Column(Text, default="")

    # Lexical editor state (JSON string)
    lexical_state = Column(Text, default="")

    # Metadata
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Settings
    settings = Column(JSON, default=dict)  # Editor preferences, etc.

    # Relationships
    scenes = relationship("Scene", back_populates="manuscript", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="manuscript", cascade="all, delete-orphan")
    snapshots = relationship("Snapshot", back_populates="manuscript", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Manuscript(id={self.id}, title='{self.title}')>"


class Scene(Base):
    """Individual scene within a manuscript"""
    __tablename__ = "scenes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)

    # Scene content
    content = Column(Text, nullable=False)
    summary = Column(Text, default="")  # Auto-generated summary

    # Position in manuscript
    position = Column(Integer, nullable=False)

    # Scene metadata
    title = Column(String, default="")
    beats = Column(JSON, default=list)  # Story beats for this scene
    setting_id = Column(String, ForeignKey("entities.id"), nullable=True)  # Location

    # Metrics
    word_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", back_populates="scenes")
    setting = relationship("Entity", foreign_keys=[setting_id])
    variants = relationship("SceneVariant", back_populates="scene", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Scene(id={self.id}, position={self.position}, words={self.word_count})>"


class SceneVariant(Base):
    """Alternative versions of a scene (multiverse branching)"""
    __tablename__ = "scene_variants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id = Column(String, ForeignKey("scenes.id"), nullable=False)

    # Variant metadata
    label = Column(String, nullable=False)  # "darker ending", "alternate POV", etc.
    content = Column(Text, nullable=False)
    is_main = Column(Integer, default=0)  # 0 = variant, 1 = currently active

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scene = relationship("Scene", back_populates="variants")

    def __repr__(self):
        return f"<SceneVariant(id={self.id}, label='{self.label}')>"
