"""
Character Arc models - tracking character growth through the story.

Links wiki entries to outline beats for arc progression tracking.
Supports arc templates (redemption, fall, coming of age, etc.)
"""

from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum

from app.database import Base


class ArcTemplate(str, Enum):
    """Pre-defined character arc templates based on storytelling best practices"""
    REDEMPTION = "redemption"
    FALL = "fall"
    COMING_OF_AGE = "coming_of_age"
    POSITIVE_CHANGE = "positive_change"
    FLAT_ARC = "flat_arc"
    NEGATIVE_CHANGE = "negative_change"
    DISILLUSIONMENT = "disillusionment"
    CORRUPTION = "corruption"
    TRANSFORMATION = "transformation"
    CUSTOM = "custom"


# Arc template definitions with stages and beat mappings
ARC_TEMPLATE_DEFINITIONS = {
    ArcTemplate.REDEMPTION.value: {
        "name": "Redemption Arc",
        "description": "Character moves from moral failing to redemption through growth",
        "stages": [
            {"id": "flawed_state", "name": "Flawed State", "description": "Character begins in a morally compromised position"},
            {"id": "catalyst", "name": "Catalyst", "description": "Event that begins the journey toward change"},
            {"id": "struggle", "name": "Struggle", "description": "Character wrestles with old habits and new path"},
            {"id": "dark_moment", "name": "Dark Moment", "description": "Character nearly falls back to old ways"},
            {"id": "transformation", "name": "Transformation", "description": "Character makes a defining choice for good"},
            {"id": "redeemed_state", "name": "Redeemed State", "description": "Character has achieved moral redemption"},
        ],
        "beat_mapping": {
            "three_act": {
                "flawed_state": "setup",
                "catalyst": "inciting_incident",
                "struggle": "rising_action",
                "dark_moment": "crisis",
                "transformation": "climax",
                "redeemed_state": "resolution"
            },
            "heros_journey": {
                "flawed_state": "ordinary_world",
                "catalyst": "call_to_adventure",
                "struggle": "tests_allies_enemies",
                "dark_moment": "ordeal",
                "transformation": "resurrection",
                "redeemed_state": "return_with_elixir"
            },
            "save_the_cat": {
                "flawed_state": "opening_image",
                "catalyst": "catalyst",
                "struggle": "fun_and_games",
                "dark_moment": "all_is_lost",
                "transformation": "finale",
                "redeemed_state": "final_image"
            }
        }
    },
    ArcTemplate.FALL.value: {
        "name": "Tragic Fall",
        "description": "Character descends from a noble state to destruction",
        "stages": [
            {"id": "noble_state", "name": "Noble State", "description": "Character begins in a position of virtue or power"},
            {"id": "temptation", "name": "Temptation", "description": "Something tempts the character to compromise"},
            {"id": "compromise", "name": "Compromise", "description": "Character makes a morally questionable choice"},
            {"id": "corruption", "name": "Corruption", "description": "Compromises compound, character loses moral footing"},
            {"id": "downfall", "name": "Downfall", "description": "Character faces consequences and falls"},
        ],
        "beat_mapping": {
            "three_act": {
                "noble_state": "setup",
                "temptation": "inciting_incident",
                "compromise": "rising_action",
                "corruption": "crisis",
                "downfall": "climax"
            }
        }
    },
    ArcTemplate.COMING_OF_AGE.value: {
        "name": "Coming of Age",
        "description": "Character matures from innocence through experience",
        "stages": [
            {"id": "innocence", "name": "Innocence", "description": "Character begins naive or sheltered"},
            {"id": "challenge", "name": "Challenge", "description": "First real test of character's worldview"},
            {"id": "mentor", "name": "Mentor", "description": "Guide appears to help navigate challenges"},
            {"id": "trial", "name": "Trial", "description": "Character must face challenge alone"},
            {"id": "growth", "name": "Growth", "description": "Character gains wisdom from experience"},
            {"id": "maturity", "name": "Maturity", "description": "Character emerges as a mature individual"},
        ],
        "beat_mapping": {
            "three_act": {
                "innocence": "setup",
                "challenge": "inciting_incident",
                "mentor": "rising_action",
                "trial": "crisis",
                "growth": "climax",
                "maturity": "resolution"
            },
            "heros_journey": {
                "innocence": "ordinary_world",
                "challenge": "call_to_adventure",
                "mentor": "meeting_the_mentor",
                "trial": "ordeal",
                "growth": "resurrection",
                "maturity": "return_with_elixir"
            }
        }
    },
    ArcTemplate.POSITIVE_CHANGE.value: {
        "name": "Positive Change Arc",
        "description": "Character overcomes a lie they believe to embrace truth",
        "stages": [
            {"id": "lie_believed", "name": "Lie Believed", "description": "Character operates under a false belief"},
            {"id": "desire", "name": "Desire", "description": "Character pursues a want based on the lie"},
            {"id": "conflict", "name": "Conflict", "description": "Reality clashes with the character's lie"},
            {"id": "truth_glimpsed", "name": "Truth Glimpsed", "description": "Character begins to see the truth"},
            {"id": "truth_embraced", "name": "Truth Embraced", "description": "Character fully accepts the truth"},
        ],
        "beat_mapping": {
            "three_act": {
                "lie_believed": "setup",
                "desire": "inciting_incident",
                "conflict": "rising_action",
                "truth_glimpsed": "crisis",
                "truth_embraced": "climax"
            }
        }
    },
    ArcTemplate.FLAT_ARC.value: {
        "name": "Flat Arc (Testing)",
        "description": "Character holds a truth and changes the world around them",
        "stages": [
            {"id": "truth_known", "name": "Truth Known", "description": "Character begins with a core truth"},
            {"id": "world_challenges", "name": "World Challenges", "description": "The world tests the character's truth"},
            {"id": "truth_tested", "name": "Truth Tested", "description": "Truth is severely challenged"},
            {"id": "world_changed", "name": "World Changed", "description": "Character's truth transforms the world"},
        ],
        "beat_mapping": {
            "three_act": {
                "truth_known": "setup",
                "world_challenges": "rising_action",
                "truth_tested": "crisis",
                "world_changed": "resolution"
            }
        }
    },
    ArcTemplate.NEGATIVE_CHANGE.value: {
        "name": "Negative Change Arc",
        "description": "Character rejects truth and embraces a lie",
        "stages": [
            {"id": "truth_known", "name": "Truth Known", "description": "Character begins aware of a truth"},
            {"id": "temptation", "name": "Temptation", "description": "A lie offers easier path"},
            {"id": "compromise", "name": "Compromise", "description": "Character begins to justify the lie"},
            {"id": "lie_embraced", "name": "Lie Embraced", "description": "Character fully accepts the lie"},
            {"id": "destruction", "name": "Destruction", "description": "Consequences of embracing the lie"},
        ],
        "beat_mapping": {
            "three_act": {
                "truth_known": "setup",
                "temptation": "inciting_incident",
                "compromise": "rising_action",
                "lie_embraced": "crisis",
                "destruction": "climax"
            }
        }
    },
    ArcTemplate.DISILLUSIONMENT.value: {
        "name": "Disillusionment Arc",
        "description": "Character moves from naive optimism to realistic worldview",
        "stages": [
            {"id": "optimism", "name": "Optimism", "description": "Character has idealistic worldview"},
            {"id": "first_crack", "name": "First Crack", "description": "Reality begins to challenge idealism"},
            {"id": "denial", "name": "Denial", "description": "Character resists accepting harsh truths"},
            {"id": "acceptance", "name": "Acceptance", "description": "Character accepts the world as it is"},
            {"id": "wisdom", "name": "Wisdom", "description": "Character finds balance between hope and reality"},
        ],
        "beat_mapping": {
            "three_act": {
                "optimism": "setup",
                "first_crack": "inciting_incident",
                "denial": "rising_action",
                "acceptance": "crisis",
                "wisdom": "resolution"
            }
        }
    },
    ArcTemplate.CORRUPTION.value: {
        "name": "Corruption Arc",
        "description": "Character is gradually corrupted by power or circumstances",
        "stages": [
            {"id": "pure_intent", "name": "Pure Intent", "description": "Character begins with good intentions"},
            {"id": "power_gained", "name": "Power Gained", "description": "Character acquires power or influence"},
            {"id": "small_compromise", "name": "Small Compromise", "description": "First ethical compromise for greater good"},
            {"id": "escalation", "name": "Escalation", "description": "Compromises grow larger and more frequent"},
            {"id": "corrupted", "name": "Corrupted", "description": "Character has become what they once opposed"},
        ],
        "beat_mapping": {
            "three_act": {
                "pure_intent": "setup",
                "power_gained": "inciting_incident",
                "small_compromise": "rising_action",
                "escalation": "crisis",
                "corrupted": "climax"
            }
        }
    },
    ArcTemplate.TRANSFORMATION.value: {
        "name": "Transformation Arc",
        "description": "Character undergoes fundamental identity change",
        "stages": [
            {"id": "old_identity", "name": "Old Identity", "description": "Character's established sense of self"},
            {"id": "identity_crisis", "name": "Identity Crisis", "description": "Events challenge who character believes they are"},
            {"id": "exploration", "name": "Exploration", "description": "Character experiments with new identity"},
            {"id": "integration", "name": "Integration", "description": "Old and new aspects combine"},
            {"id": "new_identity", "name": "New Identity", "description": "Character emerges with transformed self"},
        ],
        "beat_mapping": {
            "three_act": {
                "old_identity": "setup",
                "identity_crisis": "inciting_incident",
                "exploration": "rising_action",
                "integration": "crisis",
                "new_identity": "resolution"
            }
        }
    }
}


class CharacterArc(Base):
    """
    Character arc tracking - links wiki entry to outline for arc progression.

    Tracks both planned arc (author's intention) and detected arc
    (from manuscript analysis) for comparison.
    """
    __tablename__ = "character_arcs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    wiki_entry_id = Column(String, ForeignKey("wiki_entries.id"), nullable=False)
    manuscript_id = Column(String, ForeignKey("manuscripts.id"), nullable=False)

    # Arc template
    arc_template = Column(String, default=ArcTemplate.CUSTOM.value)

    # Custom arc name (for CUSTOM template or overriding template name)
    arc_name = Column(String, nullable=True)

    # Planned arc (author's intention)
    # Structure follows template stages:
    # {
    #   "starting_state": "Selfish loner",
    #   "catalyst": "Meets orphan who needs help",
    #   "midpoint_shift": "Begins caring about others",
    #   "dark_moment": "Betrays new friends for old habits",
    #   "resolution": "Sacrifices self for community",
    #   "ending_state": "Selfless hero"
    # }
    planned_arc = Column(JSON, default=dict)

    # Detected arc (from manuscript analysis)
    # Same structure, populated by AI analysis
    detected_arc = Column(JSON, default=dict)

    # Arc beats linked to outline
    # [
    #   {
    #     "beat_id": "...",
    #     "outline_id": "...",
    #     "arc_stage": "catalyst",
    #     "chapter_id": "...",
    #     "description": "John meets the orphan",
    #     "is_planned": true,
    #     "is_detected": true
    #   },
    #   ...
    # ]
    arc_beats = Column(JSON, default=list)

    # Custom stages (for CUSTOM template)
    # [
    #   {"id": "stage_1", "name": "Beginning", "description": "..."},
    #   ...
    # ]
    custom_stages = Column(JSON, default=list)

    # Tracking
    arc_completion = Column(Float, default=0.0)  # 0-1 based on beats hit
    arc_health = Column(String, default="healthy")  # healthy, at_risk, broken
    arc_deviation_notes = Column(Text, nullable=True)  # Where actual differs from planned

    # Analysis metadata
    last_analyzed_at = Column(DateTime, nullable=True)
    analysis_confidence = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    wiki_entry = relationship("WikiEntry", backref="character_arcs")
    manuscript = relationship("Manuscript", backref="character_arcs")

    def __repr__(self):
        return f"<CharacterArc(id={self.id}, template={self.arc_template}, completion={self.arc_completion})>"

    def get_template_definition(self) -> dict:
        """Get the template definition for this arc"""
        if self.arc_template == ArcTemplate.CUSTOM.value:
            return {
                "name": self.arc_name or "Custom Arc",
                "description": "Custom character arc",
                "stages": self.custom_stages or [],
                "beat_mapping": {}
            }
        return ARC_TEMPLATE_DEFINITIONS.get(self.arc_template, {})

    def get_stages(self) -> list:
        """Get the stages for this arc"""
        if self.arc_template == ArcTemplate.CUSTOM.value:
            return self.custom_stages or []
        template = ARC_TEMPLATE_DEFINITIONS.get(self.arc_template, {})
        return template.get("stages", [])

    def calculate_completion(self) -> float:
        """Calculate arc completion based on beats hit"""
        stages = self.get_stages()
        if not stages:
            return 0.0

        total_stages = len(stages)
        completed_stages = set()

        for beat in (self.arc_beats or []):
            if beat.get("is_detected") or beat.get("is_planned"):
                completed_stages.add(beat.get("arc_stage"))

        return len(completed_stages) / total_stages if total_stages > 0 else 0.0
