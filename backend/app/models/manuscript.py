"""
Manuscript and Scene models
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


# Document type constants for Chapter model
DOCUMENT_TYPE_CHAPTER = "CHAPTER"
DOCUMENT_TYPE_FOLDER = "FOLDER"
DOCUMENT_TYPE_CHARACTER_SHEET = "CHARACTER_SHEET"
DOCUMENT_TYPE_NOTES = "NOTES"
DOCUMENT_TYPE_TITLE_PAGE = "TITLE_PAGE"


class Manuscript(Base):
    """Main manuscript/book entity"""
    __tablename__ = "manuscripts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    author = Column(String, default="")
    description = Column(Text, default="")

    # Series relationship (nullable for standalone manuscripts)
    series_id = Column(String, ForeignKey("series.id"), nullable=True)

    # Lexical editor state (JSON string)
    lexical_state = Column(Text, default="")

    # Metadata
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Display ordering within series
    order_index = Column(Integer, default=0)

    # Settings
    settings = Column(JSON, default=dict)  # Editor preferences, etc.

    # Relationships
    series = relationship("Series", back_populates="manuscripts")
    scenes = relationship("Scene", back_populates="manuscript", cascade="all, delete-orphan")
    chapters = relationship("Chapter", back_populates="manuscript", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="manuscript", foreign_keys="Entity.manuscript_id", cascade="all, delete-orphan")
    snapshots = relationship("Snapshot", back_populates="manuscript", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Manuscript(id={self.id}, title='{self.title}')>"


class Chapter(Base):
    """Chapter or folder in hierarchical document structure (Scrivener-like)"""
    __tablename__ = "chapters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)
    parent_id = Column(String, ForeignKey("chapters.id"), nullable=True)  # For nested folders

    # Chapter metadata
    title = Column(String, nullable=False, default="Untitled")
    is_folder = Column(Integer, default=0)  # 0 = document, 1 = folder (legacy, use document_type)
    order_index = Column(Integer, nullable=False, default=0)  # Order within parent

    # Document type: CHAPTER, FOLDER, CHARACTER_SHEET, NOTES, TITLE_PAGE
    document_type = Column(String, default=DOCUMENT_TYPE_CHAPTER, nullable=False)

    # Link to Codex entity (for CHARACTER_SHEET documents)
    linked_entity_id = Column(String, ForeignKey("entities.id"), nullable=True)

    # Structured metadata for non-chapter document types
    # CHARACTER_SHEET: character data fields
    # NOTES: tags, category
    # TITLE_PAGE: title, subtitle, author, synopsis, dedication, epigraph
    document_metadata = Column(JSON, default=dict)

    # Content (only for documents, not folders)
    lexical_state = Column(Text, default="")  # Lexical editor JSON state
    content = Column(Text, default="")  # Plain text version for search/analysis

    # Metadata
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", back_populates="chapters")
    parent = relationship("Chapter", remote_side=[id], backref="children")
    chapter_scenes = relationship("ChapterScene", back_populates="chapter", cascade="all, delete-orphan")
    linked_entity = relationship("Entity", foreign_keys=[linked_entity_id])

    def __repr__(self):
        return f"<Chapter(id={self.id}, title='{self.title}', type={self.document_type})>"


class Scene(Base):
    """Individual scene within a manuscript"""
    __tablename__ = "scenes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)  # Link to chapter

    # Scene content
    content = Column(Text, nullable=False)
    summary = Column(Text, default="")  # Auto-generated summary

    # Position in manuscript
    position = Column(Integer, nullable=False)

    # Scene metadata
    title = Column(String, default="")
    beats = Column(JSON, default=list)  # Story beats for this scene
    setting_id = Column(String, ForeignKey("entities.id"), nullable=True)  # Location
    pov_character_id = Column(String, ForeignKey("entities.id"), nullable=True)  # POV character

    # Metrics
    word_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    manuscript = relationship("Manuscript", back_populates="scenes")
    chapter = relationship("Chapter", foreign_keys=[chapter_id])
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
