"""
Character Voice Profile Models

Stores analyzed voice profiles for characters and detected inconsistencies.
Used by the Voice Consistency Analyzer to track dialogue patterns.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Integer, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.database import Base


class CharacterVoiceProfile(Base):
    """
    Stored voice profile for a character.

    Contains analyzed metrics from all dialogue attributed to this character,
    including vocabulary patterns, sentence structure, and speech habits.
    """
    __tablename__ = "character_voice_profiles"

    id = Column(String, primary_key=True)
    character_id = Column(String, ForeignKey("entities.id"), nullable=False)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)

    # Cached profile data - computed from dialogue analysis
    profile_data = Column(JSON, default=dict)
    # Profile data structure:
    # {
    #   "avg_sentence_length": float,        # Words per sentence
    #   "sentence_length_variance": float,   # How much sentence length varies
    #   "vocabulary_complexity": float,      # Average syllables per word
    #   "vocabulary_richness": float,        # Type-token ratio
    #   "contraction_rate": float,           # % of contractions used
    #   "question_rate": float,              # % of sentences that are questions
    #   "exclamation_rate": float,           # % of sentences with exclamations
    #   "common_phrases": [["phrase", count], ...],  # Repeated phrases
    #   "signature_words": ["word1", ...],   # Words this character uses often
    #   "filler_words": {"um": count, ...},  # Filler word usage
    #   "formality_score": float,            # 0 (casual) to 1 (formal)
    #   "emotion_markers": {                 # Emotional language patterns
    #       "positive": float,
    #       "negative": float,
    #       "neutral": float
    #   },
    #   "dialogue_samples": int,             # Number of dialogue samples analyzed
    #   "total_words": int,                  # Total words in dialogue
    # }

    # Confidence score for the profile (higher = more dialogue samples)
    confidence_score = Column(Float, default=0.0)

    # When profile was last calculated
    calculated_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    character = relationship("Entity", foreign_keys=[character_id])
    manuscript = relationship("Manuscript", foreign_keys=[manuscript_id])


class VoiceInconsistency(Base):
    """
    Detected voice inconsistency for a character.

    Flags when dialogue doesn't match the established voice profile,
    helping writers maintain consistent character voices.
    """
    __tablename__ = "voice_inconsistencies"

    id = Column(String, primary_key=True)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)
    character_id = Column(String, ForeignKey("entities.id"), nullable=False)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=False)
    profile_id = Column(String, ForeignKey("character_voice_profiles.id"), nullable=True)

    # Type of inconsistency
    inconsistency_type = Column(String)
    # Types: VOCABULARY, SENTENCE_LENGTH, FORMALITY, CONTRACTION,
    #        EMOTION, PHRASE_STYLE, COMPLEXITY

    # Severity level
    severity = Column(String, default="medium")  # low, medium, high

    # Detailed description
    description = Column(Text)

    # The problematic dialogue excerpt
    dialogue_excerpt = Column(Text)

    # Character offset in the chapter
    start_offset = Column(Integer)
    end_offset = Column(Integer)

    # What the profile expected vs what was found
    expected_value = Column(String)
    actual_value = Column(String)

    # Suggestion for fixing
    suggestion = Column(Text)

    # Teaching point about voice consistency
    teaching_point = Column(Text)

    # User feedback
    is_resolved = Column(Integer, default=0)  # 0=open, 1=resolved, 2=dismissed
    user_feedback = Column(String)  # "correct", "incorrect", "uncertain"

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    character = relationship("Entity", foreign_keys=[character_id])
    chapter = relationship("Chapter", foreign_keys=[chapter_id])
    manuscript = relationship("Manuscript", foreign_keys=[manuscript_id])


class VoiceComparison(Base):
    """
    Comparison between two character voices.

    Stores analysis of how distinct two characters' voices are,
    helping writers ensure characters don't sound too similar.
    """
    __tablename__ = "voice_comparisons"

    id = Column(String, primary_key=True)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)
    character_a_id = Column(String, ForeignKey("entities.id"), nullable=False)
    character_b_id = Column(String, ForeignKey("entities.id"), nullable=False)

    # Similarity scores (0-1, lower = more distinct)
    overall_similarity = Column(Float)
    vocabulary_similarity = Column(Float)
    structure_similarity = Column(Float)
    formality_similarity = Column(Float)

    # Detailed comparison data
    comparison_data = Column(JSON, default=dict)
    # {
    #   "distinguishing_features_a": ["uses contractions", ...],
    #   "distinguishing_features_b": ["formal vocabulary", ...],
    #   "shared_traits": ["short sentences", ...],
    #   "recommendations": ["Consider having X use more...", ...]
    # }

    # When comparison was calculated
    calculated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    character_a = relationship("Entity", foreign_keys=[character_a_id])
    character_b = relationship("Entity", foreign_keys=[character_b_id])
    manuscript = relationship("Manuscript", foreign_keys=[manuscript_id])
