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
from app.models.foreshadowing import ForeshadowingPair, ForeshadowingType
from app.models.achievement import Achievement, AchievementProgress, AchievementType, ACHIEVEMENT_METADATA
from app.models.shareable_recap import ShareableRecap
from app.models.agent import (
    AgentAnalysis, CoachSession, CoachMessage, AuthorLearning, SuggestionFeedback,
    MaxwellConversation, MaxwellInsight, MaxwellPreferences,
    ProactiveNudge, WeeklyInsight
)
from app.models.privacy import AuthorPrivacyPreferences, ConsentRecord, AIInteractionAudit, ContentSharingLevel, ConsentType
from app.models.carbon import CarbonMetric, CarbonReport, CarbonBudget, ENERGY_ESTIMATES_MICRO_KWH, CARBON_INTENSITY_BY_REGION
from app.models.wiki import (
    WikiEntry, WikiChange, WikiCrossReference,
    WikiEntryType, WikiEntryStatus, WikiChangeType, WikiChangeStatus, WikiReferenceType
)
from app.models.character_arc import CharacterArc, ArcTemplate, ARC_TEMPLATE_DEFINITIONS
from app.models.world_rule import WorldRule, RuleViolation, RuleType, RuleSeverity, RULE_TEMPLATES

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
    # Foreshadowing
    "ForeshadowingPair",
    "ForeshadowingType",
    # Achievement
    "Achievement",
    "AchievementProgress",
    "AchievementType",
    "ACHIEVEMENT_METADATA",
    # Shareable Recap
    "ShareableRecap",
    # Agent
    "AgentAnalysis",
    "CoachSession",
    "CoachMessage",
    "AuthorLearning",
    "SuggestionFeedback",
    # Maxwell Memory
    "MaxwellConversation",
    "MaxwellInsight",
    "MaxwellPreferences",
    # Proactive Suggestions
    "ProactiveNudge",
    "WeeklyInsight",
    # Privacy
    "AuthorPrivacyPreferences",
    "ConsentRecord",
    "AIInteractionAudit",
    "ContentSharingLevel",
    "ConsentType",
    # Carbon Tracking
    "CarbonMetric",
    "CarbonReport",
    "CarbonBudget",
    "ENERGY_ESTIMATES_MICRO_KWH",
    "CARBON_INTENSITY_BY_REGION",
    # Wiki
    "WikiEntry",
    "WikiChange",
    "WikiCrossReference",
    "WikiEntryType",
    "WikiEntryStatus",
    "WikiChangeType",
    "WikiChangeStatus",
    "WikiReferenceType",
    # Character Arc
    "CharacterArc",
    "ArcTemplate",
    "ARC_TEMPLATE_DEFINITIONS",
    # World Rules
    "WorldRule",
    "RuleViolation",
    "RuleType",
    "RuleSeverity",
    "RULE_TEMPLATES",
]
