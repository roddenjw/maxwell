"""
Wiki Service - Core CRUD operations for World Wiki.

Provides:
- WikiEntry management (create, read, update, delete)
- WikiChange approval queue management
- WikiCrossReference management
- Search and filtering
- WikiConsistencyEngine for validators and agents
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import uuid
import re

from app.models.wiki import (
    WikiEntry, WikiChange, WikiCrossReference,
    WikiEntryType, WikiEntryStatus, WikiChangeType, WikiChangeStatus, WikiReferenceType
)
from app.models.world_rule import WorldRule, RuleViolation, RuleType, RuleSeverity


def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title"""
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug[:100]  # Limit length


class WikiService:
    """Core CRUD service for World Wiki entries"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== WikiEntry CRUD ====================

    def create_entry(
        self,
        world_id: str,
        entry_type: str,
        title: str,
        content: Optional[str] = None,
        structured_data: Optional[Dict] = None,
        summary: Optional[str] = None,
        parent_id: Optional[str] = None,
        linked_entity_id: Optional[str] = None,
        source_manuscripts: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None,
        created_by: str = "author"
    ) -> WikiEntry:
        """Create a new wiki entry"""
        entry = WikiEntry(
            id=str(uuid.uuid4()),
            world_id=world_id,
            entry_type=entry_type,
            title=title,
            slug=generate_slug(title),
            content=content,
            structured_data=structured_data or {},
            summary=summary,
            parent_id=parent_id,
            linked_entity_id=linked_entity_id,
            source_manuscripts=source_manuscripts or [],
            source_chapters=[],
            tags=tags or [],
            aliases=aliases or [],
            status=WikiEntryStatus.DRAFT.value,
            confidence_score=1.0 if created_by == "author" else 0.8,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_entry(self, entry_id: str) -> Optional[WikiEntry]:
        """Get a wiki entry by ID"""
        return self.db.query(WikiEntry).filter(WikiEntry.id == entry_id).first()

    def get_entry_by_slug(self, world_id: str, slug: str) -> Optional[WikiEntry]:
        """Get a wiki entry by slug within a world"""
        return self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.slug == slug
        ).first()

    def get_entries_by_world(
        self,
        world_id: str,
        entry_type: Optional[str] = None,
        status: Optional[str] = None,
        parent_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WikiEntry]:
        """Get wiki entries for a world with optional filtering"""
        query = self.db.query(WikiEntry).filter(WikiEntry.world_id == world_id)

        if entry_type:
            query = query.filter(WikiEntry.entry_type == entry_type)
        if status:
            query = query.filter(WikiEntry.status == status)
        if parent_id is not None:
            query = query.filter(WikiEntry.parent_id == parent_id)

        return query.order_by(WikiEntry.title).offset(offset).limit(limit).all()

    def search_entries(
        self,
        world_id: str,
        query: str,
        entry_types: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[WikiEntry]:
        """Search wiki entries by title, content, or aliases"""
        search_query = self.db.query(WikiEntry).filter(WikiEntry.world_id == world_id)

        # Search in title, content, and summary
        search_pattern = f"%{query}%"
        search_query = search_query.filter(
            or_(
                WikiEntry.title.ilike(search_pattern),
                WikiEntry.content.ilike(search_pattern),
                WikiEntry.summary.ilike(search_pattern)
            )
        )

        if entry_types:
            search_query = search_query.filter(WikiEntry.entry_type.in_(entry_types))

        return search_query.order_by(WikiEntry.title).limit(limit).all()

    def update_entry(
        self,
        entry_id: str,
        updates: Dict[str, Any]
    ) -> Optional[WikiEntry]:
        """Update a wiki entry"""
        entry = self.get_entry(entry_id)
        if not entry:
            return None

        allowed_fields = [
            'title', 'content', 'structured_data', 'summary', 'status',
            'parent_id', 'tags', 'aliases', 'image_url', 'source_manuscripts',
            'source_chapters', 'confidence_score', 'last_verified_at'
        ]

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(entry, field, value)

        # Update slug if title changed
        if 'title' in updates:
            entry.slug = generate_slug(updates['title'])

        entry.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete_entry(self, entry_id: str) -> bool:
        """Delete a wiki entry"""
        entry = self.get_entry(entry_id)
        if not entry:
            return False

        self.db.delete(entry)
        self.db.commit()
        return True

    # ==================== WikiChange Queue ====================

    def create_change(
        self,
        world_id: str,
        change_type: str,
        new_value: Dict,
        wiki_entry_id: Optional[str] = None,
        field_changed: Optional[str] = None,
        old_value: Optional[Dict] = None,
        reason: Optional[str] = None,
        source_text: Optional[str] = None,
        source_chapter_id: Optional[str] = None,
        source_manuscript_id: Optional[str] = None,
        confidence: float = 0.8,
        proposed_entry: Optional[Dict] = None
    ) -> WikiChange:
        """Create a pending change in the approval queue"""
        change = WikiChange(
            id=str(uuid.uuid4()),
            wiki_entry_id=wiki_entry_id,
            world_id=world_id,
            change_type=change_type,
            field_changed=field_changed,
            old_value=old_value,
            new_value=new_value,
            proposed_entry=proposed_entry,
            reason=reason,
            source_text=source_text,
            source_chapter_id=source_chapter_id,
            source_manuscript_id=source_manuscript_id,
            confidence=confidence,
            status=WikiChangeStatus.PENDING.value,
            created_at=datetime.utcnow()
        )
        self.db.add(change)
        self.db.commit()
        self.db.refresh(change)
        return change

    def get_pending_changes(
        self,
        world_id: str,
        wiki_entry_id: Optional[str] = None,
        limit: int = 50
    ) -> List[WikiChange]:
        """Get pending changes for a world"""
        query = self.db.query(WikiChange).filter(
            WikiChange.world_id == world_id,
            WikiChange.status == WikiChangeStatus.PENDING.value
        )

        if wiki_entry_id:
            query = query.filter(WikiChange.wiki_entry_id == wiki_entry_id)

        return query.order_by(WikiChange.priority.desc(), WikiChange.created_at).limit(limit).all()

    def approve_change(self, change_id: str, reviewer_note: Optional[str] = None) -> Optional[WikiEntry]:
        """Approve a pending change and apply it"""
        change = self.db.query(WikiChange).filter(WikiChange.id == change_id).first()
        if not change or change.status != WikiChangeStatus.PENDING.value:
            return None

        # Apply the change based on type
        if change.change_type == WikiChangeType.CREATE.value:
            # Create new entry from proposed_entry
            proposed = change.proposed_entry or change.new_value
            entry = self.create_entry(
                world_id=change.world_id,
                entry_type=proposed.get('entry_type'),
                title=proposed.get('title'),
                content=proposed.get('content'),
                structured_data=proposed.get('structured_data', {}),
                summary=proposed.get('summary'),
                created_by="ai"
            )
        elif change.change_type == WikiChangeType.UPDATE.value:
            # Update existing entry
            if change.field_changed:
                entry = self.update_entry(change.wiki_entry_id, {
                    change.field_changed: change.new_value
                })
            else:
                entry = self.update_entry(change.wiki_entry_id, change.new_value)
        elif change.change_type == WikiChangeType.DELETE.value:
            self.delete_entry(change.wiki_entry_id)
            entry = None
        else:
            entry = None

        # Update change status
        change.status = WikiChangeStatus.APPROVED.value
        change.reviewed_at = datetime.utcnow()
        change.reviewer_note = reviewer_note
        self.db.commit()

        return entry

    def reject_change(self, change_id: str, reviewer_note: Optional[str] = None) -> bool:
        """Reject a pending change"""
        change = self.db.query(WikiChange).filter(WikiChange.id == change_id).first()
        if not change or change.status != WikiChangeStatus.PENDING.value:
            return False

        change.status = WikiChangeStatus.REJECTED.value
        change.reviewed_at = datetime.utcnow()
        change.reviewer_note = reviewer_note
        self.db.commit()
        return True

    # ==================== WikiCrossReference ====================

    def create_reference(
        self,
        source_entry_id: str,
        target_entry_id: str,
        reference_type: str,
        context: Optional[str] = None,
        bidirectional: bool = True,
        created_by: str = "author"
    ) -> WikiCrossReference:
        """Create a cross-reference between wiki entries"""
        ref = WikiCrossReference(
            id=str(uuid.uuid4()),
            source_entry_id=source_entry_id,
            target_entry_id=target_entry_id,
            reference_type=reference_type,
            context=context,
            bidirectional=1 if bidirectional else 0,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        self.db.add(ref)
        self.db.commit()
        self.db.refresh(ref)
        return ref

    def get_entry_references(self, entry_id: str) -> Dict[str, List[WikiCrossReference]]:
        """Get all references for an entry (outgoing and incoming)"""
        outgoing = self.db.query(WikiCrossReference).filter(
            WikiCrossReference.source_entry_id == entry_id
        ).all()

        incoming = self.db.query(WikiCrossReference).filter(
            WikiCrossReference.target_entry_id == entry_id,
            WikiCrossReference.bidirectional == 1
        ).all()

        return {
            "outgoing": outgoing,
            "incoming": incoming
        }

    def delete_reference(self, reference_id: str) -> bool:
        """Delete a cross-reference"""
        ref = self.db.query(WikiCrossReference).filter(
            WikiCrossReference.id == reference_id
        ).first()
        if not ref:
            return False

        self.db.delete(ref)
        self.db.commit()
        return True


class WikiConsistencyEngine:
    """
    Central consistency engine for all analyzers and agents.

    Provides unified access to world facts for:
    - Voice analysis
    - Timeline validation
    - World rule checking
    - Relationship tracking
    """

    def __init__(self, db: Session):
        self.db = db
        self.wiki_service = WikiService(db)

    def get_character_facts(self, character_name: str, world_id: str) -> Dict[str, Any]:
        """Get all known facts about a character from the wiki"""
        # Search for character by name or alias
        entries = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.CHARACTER.value,
            or_(
                WikiEntry.title.ilike(f"%{character_name}%"),
                WikiEntry.aliases.contains([character_name])
            )
        ).all()

        if not entries:
            return {"found": False, "character_name": character_name}

        entry = entries[0]  # Take the best match
        facts = {
            "found": True,
            "wiki_entry_id": entry.id,
            "character_name": entry.title,
            "aliases": entry.aliases or [],
            "summary": entry.summary,
            "structured_data": entry.structured_data or {},
            "content": entry.content,
            "source_manuscripts": entry.source_manuscripts or []
        }

        # Get relationships
        refs = self.wiki_service.get_entry_references(entry.id)
        facts["relationships"] = [
            {
                "type": ref.reference_type,
                "target_id": ref.target_entry_id,
                "context": ref.context
            }
            for ref in refs["outgoing"]
        ]

        # Get character arcs
        from app.models.character_arc import CharacterArc
        arcs = self.db.query(CharacterArc).filter(
            CharacterArc.wiki_entry_id == entry.id
        ).all()
        facts["arcs"] = [
            {
                "arc_id": arc.id,
                "template": arc.arc_template,
                "planned_arc": arc.planned_arc,
                "detected_arc": arc.detected_arc,
                "completion": arc.arc_completion
            }
            for arc in arcs
        ]

        return facts

    def get_world_rules(
        self,
        world_id: str,
        rule_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[WorldRule]:
        """Get world rules for validation"""
        query = self.db.query(WorldRule).filter(WorldRule.world_id == world_id)

        if rule_type:
            query = query.filter(WorldRule.rule_type == rule_type)
        if active_only:
            query = query.filter(WorldRule.is_active == 1)

        return query.all()

    def get_relationship_state(
        self,
        char_a: str,
        char_b: str,
        world_id: str,
        at_chapter_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get relationship state between two characters"""
        # Find character entries
        char_a_entry = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.CHARACTER.value,
            WikiEntry.title.ilike(f"%{char_a}%")
        ).first()

        char_b_entry = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.CHARACTER.value,
            WikiEntry.title.ilike(f"%{char_b}%")
        ).first()

        if not char_a_entry or not char_b_entry:
            return {
                "found": False,
                "char_a": char_a,
                "char_b": char_b
            }

        # Find relationship reference
        ref = self.db.query(WikiCrossReference).filter(
            or_(
                and_(
                    WikiCrossReference.source_entry_id == char_a_entry.id,
                    WikiCrossReference.target_entry_id == char_b_entry.id
                ),
                and_(
                    WikiCrossReference.source_entry_id == char_b_entry.id,
                    WikiCrossReference.target_entry_id == char_a_entry.id,
                    WikiCrossReference.bidirectional == 1
                )
            )
        ).first()

        if not ref:
            return {
                "found": True,
                "has_relationship": False,
                "char_a": char_a_entry.title,
                "char_b": char_b_entry.title
            }

        return {
            "found": True,
            "has_relationship": True,
            "char_a": char_a_entry.title,
            "char_b": char_b_entry.title,
            "relationship_type": ref.reference_type,
            "context": ref.context
        }

    def get_location_facts(self, location_name: str, world_id: str) -> Dict[str, Any]:
        """Get location details for consistency checking"""
        entries = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.LOCATION.value,
            or_(
                WikiEntry.title.ilike(f"%{location_name}%"),
                WikiEntry.aliases.contains([location_name])
            )
        ).all()

        if not entries:
            return {"found": False, "location_name": location_name}

        entry = entries[0]
        return {
            "found": True,
            "wiki_entry_id": entry.id,
            "location_name": entry.title,
            "aliases": entry.aliases or [],
            "summary": entry.summary,
            "structured_data": entry.structured_data or {},
            "content": entry.content
        }

    def validate_against_rules(
        self,
        text: str,
        world_id: str,
        rule_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Check text against all world rules"""
        rules = self.get_world_rules(world_id)
        violations = []

        for rule in rules:
            if rule_types and rule.rule_type not in rule_types:
                continue

            # Check if any validation keywords are present
            keywords = rule.validation_keywords or []
            text_lower = text.lower()

            keyword_found = any(kw.lower() in text_lower for kw in keywords)
            if not keyword_found:
                continue

            # Check if exception keywords exempt this text
            exception_keywords = rule.exception_keywords or []
            exception_found = any(ex.lower() in text_lower for ex in exception_keywords)
            if exception_found:
                continue

            # Check validation pattern if present
            if rule.validation_pattern:
                try:
                    if not re.search(rule.validation_pattern, text, re.IGNORECASE):
                        violations.append({
                            "rule_id": rule.id,
                            "rule_name": rule.rule_name,
                            "rule_type": rule.rule_type,
                            "severity": rule.severity,
                            "message": rule.violation_message or f"Possible violation of: {rule.rule_name}",
                            "text_excerpt": text[:200]
                        })
                except re.error:
                    pass  # Skip invalid regex
            else:
                # Simple keyword match without exception = potential violation
                violations.append({
                    "rule_id": rule.id,
                    "rule_name": rule.rule_name,
                    "rule_type": rule.rule_type,
                    "severity": rule.severity,
                    "message": rule.violation_message or f"Check world rule: {rule.rule_name}",
                    "text_excerpt": text[:200]
                })

        return violations

    def get_all_characters(self, world_id: str) -> List[Dict[str, Any]]:
        """Get all characters in a world"""
        entries = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.CHARACTER.value
        ).all()

        return [
            {
                "id": e.id,
                "name": e.title,
                "aliases": e.aliases or [],
                "summary": e.summary
            }
            for e in entries
        ]

    def get_all_locations(self, world_id: str) -> List[Dict[str, Any]]:
        """Get all locations in a world"""
        entries = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.LOCATION.value
        ).all()

        return [
            {
                "id": e.id,
                "name": e.title,
                "aliases": e.aliases or [],
                "summary": e.summary
            }
            for e in entries
        ]
