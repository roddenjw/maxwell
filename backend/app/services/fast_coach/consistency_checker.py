"""
Consistency Checker - Check against Codex for contradictions
Detects inconsistencies in character attributes, timeline, locations
"""

import re
from typing import List, Optional
from sqlalchemy.orm import Session

from .types import Suggestion, SuggestionType, SeverityLevel
from app.models.entity import Entity


class ConsistencyChecker:
    """Check writing against Codex for consistency"""

    def __init__(self, db_session: Session, nlp_service):
        """
        Initialize consistency checker

        Args:
            db_session: Database session for Codex queries
            nlp_service: NLP service for entity extraction
        """
        self.db = db_session
        self.nlp = nlp_service.nlp

    def check(self, text: str, manuscript_id: str) -> List[Suggestion]:
        """
        Check text for consistency issues against Codex

        Args:
            text: The text to check
            manuscript_id: ID of the manuscript

        Returns:
            List of consistency suggestions
        """
        if not text or len(text.strip()) < 20:
            return []

        suggestions = []

        # Extract entities mentioned in text
        doc = self.nlp(text)
        entities_mentioned = []

        for ent in doc.ents:
            if ent.label_ in ["PERSON", "GPE", "LOC", "ORG"]:
                entities_mentioned.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })

        # Check each mentioned entity against Codex
        for entity_mention in entities_mentioned:
            entity_name = entity_mention["text"]

            # Look up in Codex
            codex_entity = self.db.query(Entity).filter(
                Entity.manuscript_id == manuscript_id,
                Entity.name.ilike(f"%{entity_name}%")
            ).first()

            if codex_entity:
                # Check for attribute conflicts
                conflicts = self._check_attribute_conflicts(
                    text,
                    entity_mention,
                    codex_entity
                )
                suggestions.extend(conflicts)

        return suggestions

    def _check_attribute_conflicts(
        self,
        text: str,
        entity_mention: dict,
        codex_entity: Entity
    ) -> List[Suggestion]:
        """Check for contradicting descriptions"""
        conflicts = []

        entity_name = entity_mention["text"]
        entity_type = codex_entity.type

        # Character attribute checks
        if entity_type == "CHARACTER":
            conflicts.extend(self._check_character_attributes(
                text, entity_name, codex_entity
            ))

        # Location attribute checks
        elif entity_type == "LOCATION":
            conflicts.extend(self._check_location_attributes(
                text, entity_name, codex_entity
            ))

        return conflicts

    def _check_character_attributes(
        self,
        text: str,
        char_name: str,
        codex_entity: Entity
    ) -> List[Suggestion]:
        """Check character physical attributes"""
        conflicts = []

        attributes = codex_entity.attributes or {}

        # Eye color check
        if "eye_color" in attributes or "eyes" in attributes:
            codex_color = attributes.get("eye_color") or attributes.get("eyes")
            conflicts.extend(self._check_color_attribute(
                text, char_name, "eyes", codex_color
            ))

        # Hair color check
        if "hair_color" in attributes or "hair" in attributes:
            codex_color = attributes.get("hair_color") or attributes.get("hair")
            conflicts.extend(self._check_color_attribute(
                text, char_name, "hair", codex_color
            ))

        # Age check
        if "age" in attributes:
            codex_age = attributes["age"]
            conflicts.extend(self._check_age_attribute(
                text, char_name, codex_age
            ))

        return conflicts

    def _check_color_attribute(
        self,
        text: str,
        char_name: str,
        attribute: str,
        codex_value: str
    ) -> List[Suggestion]:
        """Check for color conflicts (eyes, hair)"""
        conflicts = []

        # Pattern: "his/her/their <color> <attribute>"
        # or "<name>'s <color> <attribute>"
        patterns = [
            rf"(his|her|their)\s+(\w+)\s+{attribute}",
            rf"{re.escape(char_name)}'?s?\s+(\w+)\s+{attribute}"
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract color from match
                color_group = 2 if len(match.groups()) == 2 else 1
                text_color = match.group(color_group)

                # Check if it contradicts Codex
                if text_color.lower() != codex_value.lower():
                    conflicts.append(Suggestion(
                        type=SuggestionType.CONSISTENCY,
                        severity=SeverityLevel.WARNING,
                        message=f"Inconsistency: {char_name}'s {attribute} are {codex_value} in Codex, but described as {text_color} here",
                        suggestion=f"Update to '{codex_value}' or revise the Codex entry if this is correct.",
                        start_char=match.start(),
                        end_char=match.end(),
                        metadata={
                            "character": char_name,
                            "attribute": attribute,
                            "codex_value": codex_value,
                            "text_value": text_color
                        }
                    ))

        return conflicts

    def _check_age_attribute(
        self,
        text: str,
        char_name: str,
        codex_age: str
    ) -> List[Suggestion]:
        """Check for age conflicts"""
        conflicts = []

        # Pattern: "<name> was <number> years old"
        pattern = rf"{re.escape(char_name)}\s+(?:was|is)\s+(\d+)\s+years?\s+old"
        matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in matches:
            text_age = match.group(1)

            # Check if it contradicts Codex (allow some tolerance)
            try:
                codex_age_num = int(codex_age)
                text_age_num = int(text_age)

                if abs(codex_age_num - text_age_num) > 2:  # More than 2 years difference
                    conflicts.append(Suggestion(
                        type=SuggestionType.CONSISTENCY,
                        severity=SeverityLevel.WARNING,
                        message=f"Age inconsistency: {char_name} is {codex_age} in Codex, but {text_age} here",
                        suggestion=f"Verify age is correct. Update Codex or text to match.",
                        start_char=match.start(),
                        end_char=match.end(),
                        metadata={
                            "character": char_name,
                            "codex_age": codex_age,
                            "text_age": text_age
                        }
                    ))
            except ValueError:
                pass  # Not a numeric age

        return conflicts

    def _check_location_attributes(
        self,
        text: str,
        location_name: str,
        codex_entity: Entity
    ) -> List[Suggestion]:
        """Check location descriptions"""
        conflicts = []

        # Could check for geographical contradictions
        # For now, just a placeholder for future expansion
        # Example: "north of X" when Codex says "south of X"

        return conflicts
