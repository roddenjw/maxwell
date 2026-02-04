"""
World Rule models - custom validation rules for fantasy/sci-fi consistency.

Allows writers to define rules their world must follow, then validates
manuscript text against these rules.
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

from app.database import Base


class RuleType(str, Enum):
    """Types of world rules"""
    MAGIC = "magic"              # Magic system rules
    PHYSICS = "physics"          # Physical laws (gravity, FTL, etc.)
    SOCIAL = "social"            # Social/cultural rules
    TEMPORAL = "temporal"        # Time-related rules
    BIOLOGICAL = "biological"    # Biology rules (vampires, werewolves, etc.)
    TECHNOLOGICAL = "technological"  # Technology rules
    RELIGIOUS = "religious"      # Religious/spiritual rules
    POLITICAL = "political"      # Political/governmental rules
    ECONOMIC = "economic"        # Economic system rules
    LINGUISTIC = "linguistic"    # Language rules
    CUSTOM = "custom"            # User-defined category


class RuleSeverity(str, Enum):
    """Severity levels for rule violations"""
    ERROR = "error"      # Hard violation - definitely breaks world rules
    WARNING = "warning"  # Soft violation - might break rules
    INFO = "info"        # Informational - just flagging for awareness


class WorldRule(Base):
    """
    Specific rules the world must follow - for validation.

    Examples:
    - "Magic requires verbal spells" (magic rule)
    - "Vampires can't enter without invitation" (biological rule)
    - "FTL travel takes 3 days per parsec" (physics rule)
    """
    __tablename__ = "world_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    wiki_entry_id = Column(String, ForeignKey("wiki_entries.id"), nullable=True)
    world_id = Column(String, ForeignKey("worlds.id"), nullable=False)

    # Rule definition
    rule_type = Column(String, default=RuleType.CUSTOM.value)
    rule_name = Column(String, nullable=False)
    rule_description = Column(Text, nullable=True)

    # The "if X then Y" structure
    # "IF someone uses magic THEN they must speak an incantation"
    condition = Column(Text, nullable=True)  # The "IF" part
    requirement = Column(Text, nullable=True)  # The "THEN" part

    # For validation - pattern matching
    # Keywords that trigger this rule check
    validation_keywords = Column(JSON, default=list)  # ["magic", "spell", "cast", "conjure"]

    # Regex pattern for more sophisticated matching
    validation_pattern = Column(Text, nullable=True)  # r"(cast|conjure|summon).*(?!spoke|said|chanted)"

    # Keywords that exempt from the rule (exceptions)
    exception_keywords = Column(JSON, default=list)  # ["silent spell", "innate magic"]

    # Exception pattern
    exception_pattern = Column(Text, nullable=True)

    # Examples for AI and user reference
    valid_examples = Column(JSON, default=list)
    # ["She spoke the ancient words and fire erupted from her hands"]
    violation_examples = Column(JSON, default=list)
    # ["Fire erupted from her hands without warning"]

    # Teaching text for when violations are found
    violation_message = Column(Text, nullable=True)
    # "In this world, magic requires verbal incantation. Consider adding dialogue."

    # Status
    is_active = Column(Integer, default=1)  # 1 = active, 0 = disabled
    severity = Column(String, default=RuleSeverity.WARNING.value)

    # Scope - which parts of manuscript to check
    check_scope = Column(JSON, default=list)
    # ["narrative", "dialogue", "all"] - empty means "all"

    # Statistics
    violation_count = Column(Integer, default=0)
    last_violation_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    wiki_entry = relationship("WikiEntry", backref="world_rules")
    world = relationship("World", backref="world_rules")

    def __repr__(self):
        return f"<WorldRule(id={self.id}, name='{self.rule_name}', type={self.rule_type})>"


class RuleViolation(Base):
    """
    Record of a rule violation found in the manuscript.

    Stored for tracking and analysis, can be dismissed or fixed.
    """
    __tablename__ = "rule_violations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String, ForeignKey("world_rules.id"), nullable=False)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)
    chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)

    # The violating text
    text_excerpt = Column(Text, nullable=False)
    character_offset = Column(Integer, nullable=True)  # Position in chapter

    # Context
    surrounding_text = Column(Text, nullable=True)  # Broader context

    # Status
    status = Column(String, default="active")  # active, dismissed, fixed
    dismissed_reason = Column(Text, nullable=True)  # Why user dismissed (intentional, false positive, etc.)

    # AI confidence
    confidence = Column(Float, default=0.8)

    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    rule = relationship("WorldRule", backref="violations")
    manuscript = relationship("Manuscript", backref="rule_violations")
    chapter = relationship("Chapter", foreign_keys=[chapter_id])

    def __repr__(self):
        return f"<RuleViolation(id={self.id}, rule={self.rule_id}, status={self.status})>"


# Pre-defined rule templates for common fantasy/sci-fi rules
RULE_TEMPLATES = {
    "magic_verbal": {
        "rule_type": RuleType.MAGIC.value,
        "rule_name": "Magic Requires Verbal Component",
        "rule_description": "All magic spells require the caster to speak an incantation",
        "validation_keywords": ["cast", "spell", "magic", "conjure", "summon", "enchant"],
        "exception_keywords": ["silent spell", "innate magic", "passive magic", "enchanted"],
        "violation_message": "Magic was used without verbal component. In this world, spells require incantation.",
        "valid_examples": [
            "She spoke the ancient words and fire erupted from her palms.",
            "\"Ignis!\" he shouted, and flames consumed the enemy."
        ],
        "violation_examples": [
            "Fire erupted from her palms without warning.",
            "He conjured a shield with a mere thought."
        ]
    },
    "vampire_invitation": {
        "rule_type": RuleType.BIOLOGICAL.value,
        "rule_name": "Vampires Require Invitation",
        "rule_description": "Vampires cannot enter a private dwelling without explicit invitation",
        "validation_keywords": ["vampire", "enter", "home", "house", "dwelling", "threshold"],
        "exception_keywords": ["invited", "invitation", "come in", "welcome"],
        "violation_message": "Vampire entered without invitation. Consider adding invitation dialogue or changing the location.",
        "valid_examples": [
            "\"Please, come in,\" she said, and the vampire crossed the threshold.",
            "The vampire waited at the door, unable to enter without permission."
        ],
        "violation_examples": [
            "The vampire strode into the house without hesitation.",
            "He appeared in her bedroom, having entered through the window."
        ]
    },
    "ftl_travel_time": {
        "rule_type": RuleType.PHYSICS.value,
        "rule_name": "FTL Travel Takes Time",
        "rule_description": "Faster-than-light travel is not instantaneous - it takes measurable time",
        "validation_keywords": ["jump", "hyperspace", "warp", "FTL", "light-speed"],
        "exception_keywords": ["days later", "hours later", "journey", "travel time"],
        "violation_message": "FTL travel appears instantaneous. Consider showing the passage of time.",
        "valid_examples": [
            "Three days in hyperspace gave her time to plan.",
            "The jump to Andromeda would take two weeks."
        ],
        "violation_examples": [
            "He jumped to the distant system and immediately engaged the enemy.",
            "In an instant, they were across the galaxy."
        ]
    },
    "werewolf_full_moon": {
        "rule_type": RuleType.BIOLOGICAL.value,
        "rule_name": "Werewolves Transform on Full Moon",
        "rule_description": "Werewolves can only transform during the full moon (unless otherwise noted)",
        "validation_keywords": ["transform", "shift", "wolf form", "werewolf", "change"],
        "exception_keywords": ["full moon", "lunar", "moon was full", "moonlight"],
        "violation_message": "Werewolf transformation occurred without full moon. Verify moon phase in your timeline.",
        "valid_examples": [
            "As the full moon rose, his transformation began.",
            "She dreaded the coming full moon and the change it would bring."
        ],
        "violation_examples": [
            "He transformed in broad daylight to chase the thief.",
            "Three nights before the full moon, she shifted involuntarily."
        ]
    },
    "telepathy_range": {
        "rule_type": RuleType.MAGIC.value,
        "rule_name": "Telepathy Has Limited Range",
        "rule_description": "Telepathic communication requires proximity (define your own limit)",
        "validation_keywords": ["telepathy", "mind", "mental", "thought", "psychic"],
        "exception_keywords": ["nearby", "close", "within range", "distance"],
        "violation_message": "Telepathic communication occurred over undefined distance. Consider establishing range limits.",
        "valid_examples": [
            "She reached out mentally to her companion nearby.",
            "At this distance, their telepathic link was strained."
        ],
        "violation_examples": [
            "From across the planet, she sent a mental message.",
            "He contacted his ally on the other side of the world with a thought."
        ]
    }
}
