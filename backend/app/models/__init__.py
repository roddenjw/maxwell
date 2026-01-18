"""
Database models for Codex IDE
"""

from app.models.world import World, Series
from app.models.manuscript import Manuscript, Scene, SceneVariant, Chapter
from app.models.entity import Entity, Relationship, EntitySuggestion, ENTITY_SCOPE_MANUSCRIPT, ENTITY_SCOPE_SERIES, ENTITY_SCOPE_WORLD
from app.models.versioning import Snapshot
from app.models.coach import WritingProfile, CoachingHistory, FeedbackPattern
from app.models.recap import Recap
from app.models.outline import Outline, PlotBeat, OUTLINE_SCOPE_MANUSCRIPT, OUTLINE_SCOPE_SERIES, OUTLINE_SCOPE_WORLD
from app.models.brainstorm import BrainstormSession, BrainstormIdea
from app.models.entity_state import EntityTimelineState

__all__ = [
    # World/Series hierarchy
    "World",
    "Series",
    # Manuscript
    "Manuscript",
    "Scene",
    "SceneVariant",
    "Chapter",
    # Entity
    "Entity",
    "Relationship",
    "EntitySuggestion",
    "ENTITY_SCOPE_MANUSCRIPT",
    "ENTITY_SCOPE_SERIES",
    "ENTITY_SCOPE_WORLD",
    # Versioning
    "Snapshot",
    # Coach
    "WritingProfile",
    "CoachingHistory",
    "FeedbackPattern",
    # Recap
    "Recap",
    # Outline
    "Outline",
    "PlotBeat",
    "OUTLINE_SCOPE_MANUSCRIPT",
    "OUTLINE_SCOPE_SERIES",
    "OUTLINE_SCOPE_WORLD",
    # Brainstorm
    "BrainstormSession",
    "BrainstormIdea",
    # Entity State
    "EntityTimelineState",
]
