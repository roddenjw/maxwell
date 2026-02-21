"""
Wiki Auto-Populator Service - AI-powered wiki population.

Analyzes manuscripts and suggests Wiki updates.
All changes go to approval queue for author review.
"""

from typing import List, Optional, Dict, Any, Tuple, Callable
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import re

from app.models.wiki import (
    WikiEntry, WikiChange, WikiEntryType, WikiChangeType, WikiChangeStatus
)
from app.models.world_rule import WorldRule, RuleType, RuleSeverity
from app.models.manuscript import Manuscript, Chapter
from app.models.entity import Entity
from app.models.world import World, Series
from app.services.wiki_service import WikiService
from app.services.nlp_service import nlp_service


# ==================== Extraction Patterns ====================

# World rule patterns (what triggers rule extraction)
WORLD_RULE_PATTERNS = [
    # Explicit rules
    (r"(?:In this world|Here),?\s+(.+)", "explicit"),
    (r"(?:The|Our) (?:laws?|rules?) (?:of .+? )?(?:states?|says?|dictates?|requires?) that\s+(.+)", "law"),
    (r"(?:Magic|Power|Energy) (?:requires?|needs?|demands?)\s+(.+)", "magic_system"),
    (r"(?:No one|Nobody|None) (?:can|may|could)\s+([^.]+)\s+without\s+([^.]+)", "limitation"),
    (r"(?:It is|It's) (?:impossible|forbidden|prohibited) to\s+(.+)", "prohibition"),
    (r"(?:Only|Just) (?:the|those who|people with)\s+(.+?)\s+can\s+(.+)", "requirement"),
    (r"(?:All|Every) (\w+) (?:must|have to|need to)\s+(.+)", "universal_rule"),
    # Implicit rules from exposition
    (r"(?:has always been|have always been|was always|were always)\s+(.+)", "tradition"),
    (r"(?:is known for|are known for|was known for|were known for)\s+(.+)", "cultural"),
]

# Relationship patterns
RELATIONSHIP_PATTERNS = [
    # Family
    (r"(\w+(?:\s+\w+)?)'s (?:father|mother|parent)", "parent"),
    (r"(\w+(?:\s+\w+)?) (?:is|was) (?:the )?(?:father|mother|parent) of (\w+(?:\s+\w+)?)", "parent"),
    (r"(\w+(?:\s+\w+)?)'s (?:son|daughter|child)", "child"),
    (r"(\w+(?:\s+\w+)?)'s (?:brother|sister|sibling)", "sibling"),
    (r"(\w+(?:\s+\w+)?) (?:is|was) (?:married to|the (?:husband|wife) of) (\w+(?:\s+\w+)?)", "spouse"),
    # Professional
    (r"(\w+(?:\s+\w+)?)'s (?:boss|employer|master|lord)", "superior"),
    (r"(\w+(?:\s+\w+)?) (?:works for|serves|reports to) (\w+(?:\s+\w+)?)", "subordinate"),
    (r"(\w+(?:\s+\w+)?)'s (?:apprentice|student|protege)", "mentor"),
    # Social
    (r"(\w+(?:\s+\w+)?)'s (?:friend|ally|companion)", "friend"),
    (r"(\w+(?:\s+\w+)?)'s (?:enemy|rival|nemesis)", "enemy"),
    (r"(\w+(?:\s+\w+)?) (?:loves|is in love with) (\w+(?:\s+\w+)?)", "romantic"),
]

# Location detail patterns
LOCATION_DETAIL_PATTERNS = [
    (r"(\w+(?:\s+\w+)?) (?:is|was) (?:a |an )?(?:city|town|village|kingdom|realm|country|region|land|world) (?:of|known for|famous for)\s+(.+)", "description"),
    (r"(?:In|At|Near) (\w+(?:\s+\w+)?),?\s+(?:the|there)\s+(.+)", "feature"),
    (r"(\w+(?:\s+\w+)?) (?:has|had|contains|holds)\s+(.+)", "contents"),
    (r"The (?:people|inhabitants|residents|citizens) of (\w+(?:\s+\w+)?)\s+(.+)", "culture"),
    (r"(\w+(?:\s+\w+)?) (?:was founded|was built|was established)\s+(.+)", "history"),
]

# Character trait patterns
CHARACTER_TRAIT_PATTERNS = [
    (r"(\w+(?:\s+\w+)?) (?:is|was) (?:a |an )?(\w+(?:\s+\w+)?(?:\s+\w+)?)\s*(?:who|that|,)", "role"),
    (r"(\w+(?:\s+\w+)?) (?:has|had) (\w+(?:\s+\w+)?(?:\s+\w+)?)\s+(?:eyes|hair|skin)", "physical"),
    (r"(\w+(?:\s+\w+)?) (?:is|was) known (?:for|as)\s+(.+)", "reputation"),
    (r"(\w+(?:\s+\w+)?) (?:always|never|often|usually)\s+(.+)", "habit"),
]


class WikiAutoPopulator:
    """
    Analyzes manuscripts and suggests Wiki updates.
    All changes go to approval queue for author review.
    """

    def __init__(self, db: Session):
        self.db = db
        self.wiki_service = WikiService(db)

    def get_world_for_manuscript(self, manuscript_id: str) -> Optional[str]:
        """Get world_id for a manuscript through its series"""
        manuscript = self.db.query(Manuscript).filter(
            Manuscript.id == manuscript_id
        ).first()

        if not manuscript:
            return None

        if not manuscript.series_id:
            return None

        series = self.db.query(Series).filter(
            Series.id == manuscript.series_id
        ).first()

        return series.world_id if series else None

    # ==================== Main Analysis Methods ====================

    def analyze_manuscript(
        self,
        manuscript_id: str,
        world_id: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Full manuscript analysis for wiki updates.
        Returns summary of proposed changes.

        Args:
            progress_callback: Optional callback(stage_name, stage_index) called before each extraction stage.
        """
        # Get world_id if not provided
        if not world_id:
            world_id = self.get_world_for_manuscript(manuscript_id)

        if not world_id:
            return {"error": "No world found for manuscript"}

        # Get all chapters for this manuscript
        chapters = self.db.query(Chapter).filter(
            Chapter.manuscript_id == manuscript_id,
            Chapter.document_type == "CHAPTER"
        ).order_by(Chapter.order_index).all()

        if not chapters:
            return {"error": "No chapters found", "changes": []}

        # Combine all chapter content
        full_text = "\n\n".join(
            chapter.content or "" for chapter in chapters if chapter.content
        )

        if not full_text.strip():
            return {"error": "No content to analyze", "changes": []}

        # Run all extraction pipelines
        results = {
            "manuscript_id": manuscript_id,
            "world_id": world_id,
            "chapters_analyzed": len(chapters),
            "extractions": {}
        }

        # 1. Extract entities
        if progress_callback:
            progress_callback("Extracting entities", 0)
        entity_changes = self.extract_entities_for_wiki(
            full_text, world_id, manuscript_id
        )
        results["extractions"]["entities"] = len(entity_changes)

        # 2. Extract world rules
        if progress_callback:
            progress_callback("Extracting world rules", 1)
        rule_changes = self.extract_world_rules(
            full_text, world_id, manuscript_id
        )
        results["extractions"]["world_rules"] = len(rule_changes)

        # 3. Extract relationships
        if progress_callback:
            progress_callback("Extracting relationships", 2)
        relationship_changes = self.extract_relationships(
            full_text, world_id, manuscript_id
        )
        results["extractions"]["relationships"] = len(relationship_changes)

        # 4. Extract location details
        if progress_callback:
            progress_callback("Extracting locations", 3)
        location_changes = self.extract_location_details(
            full_text, world_id, manuscript_id
        )
        results["extractions"]["locations"] = len(location_changes)

        # 5. Extract character traits
        if progress_callback:
            progress_callback("Extracting character traits", 4)
        trait_changes = self.extract_character_traits(
            full_text, world_id, manuscript_id
        )
        results["extractions"]["character_traits"] = len(trait_changes)

        # Count total changes created
        total_changes = sum(results["extractions"].values())
        results["total_changes"] = total_changes

        return results

    def analyze_chapter(
        self,
        chapter_id: str,
        world_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a single chapter for wiki updates.
        Lightweight version for incremental updates.
        """
        chapter = self.db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return {"error": "Chapter not found"}

        if not chapter.content or not chapter.content.strip():
            return {"error": "No content to analyze", "changes": []}

        # Get world_id if not provided
        if not world_id:
            world_id = self.get_world_for_manuscript(chapter.manuscript_id)

        if not world_id:
            return {"error": "No world found for manuscript"}

        text = chapter.content
        manuscript_id = chapter.manuscript_id

        results = {
            "chapter_id": chapter_id,
            "world_id": world_id,
            "extractions": {}
        }

        # Run lightweight extraction (fewer patterns)
        entity_changes = self.extract_entities_for_wiki(
            text, world_id, manuscript_id, chapter_id
        )
        results["extractions"]["entities"] = len(entity_changes)

        rule_changes = self.extract_world_rules(
            text, world_id, manuscript_id, chapter_id
        )
        results["extractions"]["world_rules"] = len(rule_changes)

        results["total_changes"] = sum(results["extractions"].values())

        return results

    # ==================== Entity Extraction ====================

    def extract_entities_for_wiki(
        self,
        text: str,
        world_id: str,
        manuscript_id: str,
        chapter_id: Optional[str] = None
    ) -> List[WikiChange]:
        """Extract entities and create wiki change proposals"""
        changes = []

        # Use NLP service if available
        if not nlp_service.is_available():
            return changes

        # Get existing wiki entries to avoid duplicates
        existing_entries = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id
        ).all()

        existing_titles = {e.title.lower() for e in existing_entries}
        existing_aliases = set()
        for e in existing_entries:
            if e.aliases:
                for alias in e.aliases:
                    existing_aliases.add(alias.lower())

        # Get existing codex entities
        existing_entities = self.db.query(Entity).filter(
            Entity.manuscript_id == manuscript_id
        ).all()

        existing_entity_names = [
            {"name": e.name, "aliases": e.aliases or []}
            for e in existing_entities
        ]

        # Extract entities using NLP
        try:
            detected = nlp_service.extract_entities(text, existing_entity_names)
        except Exception:
            return changes

        for entity_data in detected:
            name = entity_data["name"]

            # Skip if already in wiki
            if name.lower() in existing_titles or name.lower() in existing_aliases:
                continue

            # Skip low confidence
            if entity_data.get("confidence", 0) < 0.6:
                continue

            # Map entity type to wiki entry type
            wiki_type = self._map_entity_type_to_wiki(entity_data["type"])
            if not wiki_type:
                continue

            # Check for duplicates in pending changes
            pending = self.db.query(WikiChange).filter(
                WikiChange.world_id == world_id,
                WikiChange.status == WikiChangeStatus.PENDING.value,
                WikiChange.proposed_entry.contains({"title": name})
            ).first()

            if pending:
                continue

            # Create change proposal
            proposed_entry = {
                "entry_type": wiki_type,
                "title": name,
                "summary": entity_data.get("description", ""),
                "content": f"Detected in manuscript. Context: {entity_data.get('context', '')}",
                "structured_data": entity_data.get("extracted_attributes", {}),
            }

            change = self.wiki_service.create_change(
                world_id=world_id,
                change_type=WikiChangeType.CREATE.value,
                new_value=proposed_entry,
                proposed_entry=proposed_entry,
                reason=f"New {wiki_type} detected in manuscript text",
                source_text=entity_data.get("context", "")[:500],
                source_chapter_id=chapter_id,
                source_manuscript_id=manuscript_id,
                confidence=entity_data.get("confidence", 0.7)
            )
            changes.append(change)

        return changes

    def _map_entity_type_to_wiki(self, entity_type: str) -> Optional[str]:
        """Map Codex entity type to Wiki entry type"""
        mapping = {
            "CHARACTER": WikiEntryType.CHARACTER.value,
            "LOCATION": WikiEntryType.LOCATION.value,
            "ITEM": WikiEntryType.ARTIFACT.value,
            "LORE": WikiEntryType.WORLD_RULE.value,
            "ORGANIZATION": WikiEntryType.FACTION.value,
            "EVENT": WikiEntryType.EVENT.value,
            "CULTURE": WikiEntryType.CULTURE.value,
            "CREATURE": WikiEntryType.CREATURE.value,
            "RACE": WikiEntryType.CREATURE.value,
        }
        return mapping.get(entity_type)

    # ==================== World Rule Extraction ====================

    def extract_world_rules(
        self,
        text: str,
        world_id: str,
        manuscript_id: str,
        chapter_id: Optional[str] = None
    ) -> List[WikiChange]:
        """Extract world rules from text and create proposals"""
        changes = []

        # Get existing rules to avoid duplicates (check both WorldRule and WikiEntry tables)
        existing_rules = self.db.query(WorldRule).filter(
            WorldRule.world_id == world_id
        ).all()
        existing_rule_names = {r.rule_name.lower() for r in existing_rules}

        existing_wiki_rules = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.WORLD_RULE.value
        ).all()
        for wr in existing_wiki_rules:
            existing_rule_names.add(wr.title.lower())

        for pattern, rule_category in WORLD_RULE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                # Get the matched rule content
                if match.groups():
                    rule_content = " ".join(g for g in match.groups() if g)
                else:
                    continue

                # Skip very short or very long matches
                if len(rule_content) < 10 or len(rule_content) > 500:
                    continue

                # Generate rule name
                rule_name = self._generate_rule_name(rule_content, rule_category)

                # Skip if similar rule exists
                if rule_name.lower() in existing_rule_names:
                    continue

                # Skip duplicates in current batch
                if any(
                    c.new_value.get("title", "").lower() == rule_name.lower()
                    for c in changes
                ):
                    continue

                # Get surrounding context
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]

                # Create proposed entry (must have title/entry_type for approval flow)
                proposed_entry = {
                    "entry_type": WikiEntryType.WORLD_RULE.value,
                    "title": rule_name,
                    "summary": rule_content[:300],
                    "content": rule_content,
                    "structured_data": {
                        "rule_type": self._map_rule_category(rule_category),
                        "condition": rule_content[:200] if len(rule_content) > 200 else rule_content,
                        "validation_keywords": self._extract_keywords(rule_content),
                    },
                }

                # Create change proposal
                change = self.wiki_service.create_change(
                    world_id=world_id,
                    change_type=WikiChangeType.CREATE.value,
                    new_value=proposed_entry,
                    proposed_entry=proposed_entry,
                    reason=f"World rule detected ({rule_category})",
                    source_text=context,
                    source_chapter_id=chapter_id,
                    source_manuscript_id=manuscript_id,
                    confidence=0.65  # Lower confidence for rules
                )
                changes.append(change)

        return changes

    def _generate_rule_name(self, content: str, category: str) -> str:
        """Generate a concise rule name from content"""
        # Take first few words
        words = content.split()[:6]
        name = " ".join(words)

        # Capitalize and add category prefix
        category_prefixes = {
            "explicit": "",
            "law": "Law: ",
            "magic_system": "Magic: ",
            "limitation": "Limit: ",
            "prohibition": "Forbidden: ",
            "requirement": "Requires: ",
            "universal_rule": "Rule: ",
            "tradition": "Tradition: ",
            "cultural": "Culture: ",
        }

        prefix = category_prefixes.get(category, "")
        return f"{prefix}{name.capitalize()}"[:100]

    def _map_rule_category(self, category: str) -> str:
        """Map rule category to RuleType"""
        mapping = {
            "magic_system": RuleType.MAGIC.value,
            "law": RuleType.SOCIAL.value,
            "prohibition": RuleType.PHYSICS.value,
            "limitation": RuleType.PHYSICS.value,
            "cultural": RuleType.CULTURAL.value,
            "tradition": RuleType.CULTURAL.value,
        }
        return mapping.get(category, RuleType.CUSTOM.value)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key terms for validation"""
        # Simple approach: extract capitalized words and key nouns
        words = set()

        # Find capitalized words (likely proper nouns)
        for word in re.findall(r'\b[A-Z][a-z]+\b', text):
            if len(word) > 2:
                words.add(word.lower())

        # Find key terms
        key_terms = ["magic", "power", "law", "rule", "forbidden", "must", "cannot", "never"]
        for term in key_terms:
            if term in text.lower():
                words.add(term)

        return list(words)[:10]  # Limit to 10 keywords

    # ==================== Relationship Extraction ====================

    def extract_relationships(
        self,
        text: str,
        world_id: str,
        manuscript_id: str,
        chapter_id: Optional[str] = None
    ) -> List[WikiChange]:
        """Extract character relationships from text"""
        changes = []

        # Get existing wiki entries for characters
        character_entries = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.CHARACTER.value
        ).all()

        character_names = {e.title.lower(): e for e in character_entries}

        for pattern, rel_type in RELATIONSHIP_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                groups = match.groups()
                if len(groups) < 1:
                    continue

                # Get character names from match
                char_a = groups[0].strip() if groups[0] else None
                char_b = groups[1].strip() if len(groups) > 1 and groups[1] else None

                if not char_a:
                    continue

                # Check if character A exists in wiki
                char_a_entry = character_names.get(char_a.lower())

                if not char_a_entry:
                    continue

                # Get context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                # Create update to add relationship info
                relationship_data = {
                    "relationship_type": rel_type,
                    "related_to": char_b if char_b else "mentioned",
                    "context": context[:200]
                }

                # Update structured_data with relationship
                current_data = char_a_entry.structured_data or {}
                relationships = current_data.get("relationships", [])

                # Skip if relationship already exists
                existing = any(
                    r.get("relationship_type") == rel_type and r.get("related_to") == char_b
                    for r in relationships
                )
                if existing:
                    continue

                relationships.append(relationship_data)
                new_data = {**current_data, "relationships": relationships}

                change = self.wiki_service.create_change(
                    world_id=world_id,
                    change_type=WikiChangeType.UPDATE.value,
                    wiki_entry_id=char_a_entry.id,
                    field_changed="structured_data",
                    old_value=current_data,
                    new_value=new_data,
                    reason=f"Relationship detected: {rel_type}",
                    source_text=context,
                    source_chapter_id=chapter_id,
                    source_manuscript_id=manuscript_id,
                    confidence=0.7
                )
                changes.append(change)

        return changes

    # ==================== Location Detail Extraction ====================

    def extract_location_details(
        self,
        text: str,
        world_id: str,
        manuscript_id: str,
        chapter_id: Optional[str] = None
    ) -> List[WikiChange]:
        """Extract location details from text"""
        changes = []

        # Get existing location entries
        location_entries = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.LOCATION.value
        ).all()

        location_names = {e.title.lower(): e for e in location_entries}

        for pattern, detail_type in LOCATION_DETAIL_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                groups = match.groups()
                if len(groups) < 2:
                    continue

                location_name = groups[0].strip()
                detail = groups[1].strip()

                # Check if location exists
                location_entry = location_names.get(location_name.lower())

                if not location_entry:
                    continue

                # Get context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                # Update structured_data with detail
                current_data = location_entry.structured_data or {}
                details = current_data.get(detail_type, [])

                # Skip if detail already exists
                if detail in details:
                    continue

                details.append(detail)
                new_data = {**current_data, detail_type: details}

                change = self.wiki_service.create_change(
                    world_id=world_id,
                    change_type=WikiChangeType.UPDATE.value,
                    wiki_entry_id=location_entry.id,
                    field_changed="structured_data",
                    old_value=current_data,
                    new_value=new_data,
                    reason=f"Location detail detected: {detail_type}",
                    source_text=context,
                    source_chapter_id=chapter_id,
                    source_manuscript_id=manuscript_id,
                    confidence=0.65
                )
                changes.append(change)

        return changes

    # ==================== Character Trait Extraction ====================

    def extract_character_traits(
        self,
        text: str,
        world_id: str,
        manuscript_id: str,
        chapter_id: Optional[str] = None
    ) -> List[WikiChange]:
        """Extract character traits from text"""
        changes = []

        # Get existing character entries
        character_entries = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.CHARACTER.value
        ).all()

        character_names = {e.title.lower(): e for e in character_entries}

        for pattern, trait_type in CHARACTER_TRAIT_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                groups = match.groups()
                if len(groups) < 2:
                    continue

                char_name = groups[0].strip()
                trait = groups[1].strip()

                # Check if character exists
                char_entry = character_names.get(char_name.lower())

                if not char_entry:
                    continue

                # Get context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                # Update structured_data with trait
                current_data = char_entry.structured_data or {}
                traits = current_data.get(trait_type, [])

                # Skip if trait already exists
                if trait in traits:
                    continue

                traits.append(trait)
                new_data = {**current_data, trait_type: traits}

                change = self.wiki_service.create_change(
                    world_id=world_id,
                    change_type=WikiChangeType.UPDATE.value,
                    wiki_entry_id=char_entry.id,
                    field_changed="structured_data",
                    old_value=current_data,
                    new_value=new_data,
                    reason=f"Character trait detected: {trait_type}",
                    source_text=context,
                    source_chapter_id=chapter_id,
                    source_manuscript_id=manuscript_id,
                    confidence=0.6
                )
                changes.append(change)

        return changes

    # ==================== Incremental Update Methods ====================

    def on_chapter_save(
        self,
        chapter_id: str,
        world_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Called when a chapter is saved.
        Runs lightweight analysis and queues changes.
        """
        return self.analyze_chapter(chapter_id, world_id)

    def on_entity_created(
        self,
        entity: Entity,
        world_id: str
    ) -> Optional[WikiChange]:
        """
        Called when a new Codex entity is created.
        Creates wiki entry proposal if entity is world-scoped.
        """
        # Only create wiki entries for world-scoped entities
        if entity.scope != "WORLD" and entity.scope != "SERIES":
            return None

        # Check if wiki entry already exists
        existing = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.linked_entity_id == entity.id
        ).first()

        if existing:
            return None

        wiki_type = self._map_entity_type_to_wiki(entity.entity_type)
        if not wiki_type:
            return None

        proposed_entry = {
            "entry_type": wiki_type,
            "title": entity.name,
            "summary": entity.description or "",
            "structured_data": entity.attributes or {},
            "linked_entity_id": entity.id
        }

        return self.wiki_service.create_change(
            world_id=world_id,
            change_type=WikiChangeType.CREATE.value,
            new_value=proposed_entry,
            proposed_entry=proposed_entry,
            reason="New Codex entity created",
            source_manuscript_id=entity.manuscript_id,
            confidence=1.0  # High confidence since author created it
        )

    def on_entity_updated(
        self,
        entity: Entity,
        world_id: str
    ) -> Optional[WikiChange]:
        """
        Called when a Codex entity is updated.
        Propagates changes to linked wiki entry if exists.
        """
        # Find linked wiki entry
        wiki_entry = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.linked_entity_id == entity.id
        ).first()

        if not wiki_entry:
            return None

        # Build update from entity changes
        updates = {}

        if entity.name != wiki_entry.title:
            updates["title"] = entity.name

        if entity.description and entity.description != wiki_entry.summary:
            updates["summary"] = entity.description

        if entity.attributes and entity.attributes != wiki_entry.structured_data:
            updates["structured_data"] = entity.attributes

        if not updates:
            return None

        return self.wiki_service.create_change(
            world_id=world_id,
            change_type=WikiChangeType.UPDATE.value,
            wiki_entry_id=wiki_entry.id,
            new_value=updates,
            old_value={k: getattr(wiki_entry, k) for k in updates.keys()},
            reason="Codex entity updated",
            source_manuscript_id=entity.manuscript_id,
            confidence=1.0
        )

    # ==================== Auto-Approve High Confidence ====================

    def auto_approve_high_confidence(
        self,
        world_id: str,
        threshold: float = 0.95
    ) -> int:
        """
        Automatically approve changes above confidence threshold.
        Returns count of approved changes.
        """
        pending = self.db.query(WikiChange).filter(
            WikiChange.world_id == world_id,
            WikiChange.status == WikiChangeStatus.PENDING.value,
            WikiChange.confidence >= threshold
        ).all()

        approved_count = 0
        for change in pending:
            self.wiki_service.approve_change(
                change.id,
                reviewer_note="Auto-approved (high confidence)"
            )
            approved_count += 1

        return approved_count

    # ==================== Stats ====================

    def get_pending_changes_summary(self, world_id: str) -> Dict[str, Any]:
        """Get summary of pending changes for a world"""
        pending = self.db.query(WikiChange).filter(
            WikiChange.world_id == world_id,
            WikiChange.status == WikiChangeStatus.PENDING.value
        ).all()

        by_type = {}
        for change in pending:
            change_type = change.change_type
            by_type[change_type] = by_type.get(change_type, 0) + 1

        avg_confidence = (
            sum(c.confidence for c in pending) / len(pending)
            if pending else 0
        )

        return {
            "total_pending": len(pending),
            "by_type": by_type,
            "average_confidence": round(avg_confidence, 2),
            "high_confidence_count": sum(1 for c in pending if c.confidence >= 0.95)
        }
