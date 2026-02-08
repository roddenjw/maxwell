"""
Codex service for entity and relationship management
Handles CRUD operations for characters, locations, items, and lore
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import and_

from app.database import SessionLocal
from app.models.entity import Entity, Relationship, EntitySuggestion
from app.models.scene import EntityAppearance
from app.models.manuscript import Chapter

logger = logging.getLogger(__name__)


def _trigger_wiki_sync(entity_id: str, manuscript_id: str):
    """
    Trigger background wiki sync for an entity after create/update.
    Uses agent merge if API key is available, falls back to simple sync.
    Non-blocking — errors are logged but don't affect the codex operation.
    """
    try:
        db = SessionLocal()
        try:
            entity = db.query(Entity).filter(Entity.id == entity_id).first()
            if not entity:
                return

            # Find world for this manuscript
            from app.services.world_service import world_service
            world = world_service.get_world_for_manuscript(db, manuscript_id)
            if not world:
                return  # Standalone manuscript, no wiki to sync to

            from app.services.wiki_codex_bridge import WikiCodexBridge
            bridge = WikiCodexBridge(db)

            # Try to get API key for agent merge
            api_key = None
            try:
                import os
                api_key = os.environ.get("OPENROUTER_API_KEY")
            except Exception:
                pass

            bridge.agent_merge_entity_to_wiki(entity, world.id, api_key=api_key)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Wiki sync failed for entity {entity_id}: {e}")


class CodexService:
    """Service for managing Codex entities and relationships"""

    # Entity Management

    def create_entity(
        self,
        manuscript_id: str,
        entity_type: str,
        name: str,
        aliases: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        template_type: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None
    ) -> Entity:
        """
        Create a new entity

        Args:
            manuscript_id: ID of the manuscript
            entity_type: Type (CHARACTER, LOCATION, ITEM, LORE)
            name: Entity name
            aliases: Alternative names
            attributes: Type-specific attributes
            template_type: Template type (CHARACTER, LOCATION, ITEM, MAGIC_SYSTEM, etc.)
            template_data: Structured template data

        Returns:
            Created Entity
        """
        db = SessionLocal()
        try:
            entity = Entity(
                manuscript_id=manuscript_id,
                type=entity_type,
                name=name,
                aliases=aliases or [],
                attributes=attributes or {},
                template_type=template_type,
                template_data=template_data or {}
            )
            db.add(entity)
            db.commit()
            db.refresh(entity)
            db.expunge(entity)

            # Trigger wiki sync (non-blocking)
            _trigger_wiki_sync(entity.id, manuscript_id)

            return entity
        finally:
            db.close()

    def get_entities(
        self,
        manuscript_id: str,
        entity_type: Optional[str] = None
    ) -> List[Entity]:
        """
        Get entities for a manuscript

        Args:
            manuscript_id: ID of the manuscript
            entity_type: Optional type filter

        Returns:
            List of entities
        """
        db = SessionLocal()
        try:
            query = db.query(Entity).filter(Entity.manuscript_id == manuscript_id)

            if entity_type:
                query = query.filter(Entity.type == entity_type)

            entities = query.order_by(Entity.name).all()

            # Detach from session to avoid lazy loading issues
            result = []
            for entity in entities:
                db.expunge(entity)
                result.append(entity)

            return result
        finally:
            db.close()

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Get entity by ID

        Args:
            entity_id: Entity ID

        Returns:
            Entity or None
        """
        db = SessionLocal()
        try:
            entity = db.query(Entity).filter(Entity.id == entity_id).first()
            if entity:
                db.expunge(entity)
            return entity
        finally:
            db.close()

    def update_entity(
        self,
        entity_id: str,
        name: Optional[str] = None,
        entity_type: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        template_type: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Entity]:
        """
        Update entity

        Args:
            entity_id: Entity ID
            name: New name
            aliases: New aliases
            attributes: New attributes
            template_type: Template type
            template_data: Structured template data

        Returns:
            Updated Entity or None
        """
        db = SessionLocal()
        try:
            entity = db.query(Entity).filter(Entity.id == entity_id).first()

            if not entity:
                return None

            if name is not None:
                entity.name = name
            if entity_type is not None:
                entity.type = entity_type
            if aliases is not None:
                entity.aliases = aliases
            if attributes is not None:
                entity.attributes = attributes
            if template_type is not None:
                entity.template_type = template_type
            if template_data is not None:
                entity.template_data = template_data

            entity.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(entity)
            db.expunge(entity)

            # Trigger wiki sync (non-blocking)
            if entity.manuscript_id:
                _trigger_wiki_sync(entity.id, entity.manuscript_id)

            return entity
        finally:
            db.close()

    def delete_entity(self, entity_id: str) -> bool:
        """
        Delete entity. Clears wiki link but does NOT delete the wiki entry.

        Args:
            entity_id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        db = SessionLocal()
        try:
            entity = db.query(Entity).filter(Entity.id == entity_id).first()

            if not entity:
                return False

            # Clear wiki link but don't delete wiki entry
            if entity.linked_wiki_entry_id:
                entity.linked_wiki_entry_id = None

            db.delete(entity)
            db.commit()
            return True
        finally:
            db.close()

    def merge_entities(
        self,
        primary_entity_id: str,
        secondary_entity_ids: List[str],
        merge_strategy: Dict[str, str]
    ) -> Optional[Entity]:
        """
        Merge multiple entities into a primary entity.

        Args:
            primary_entity_id: The entity to keep (primary)
            secondary_entity_ids: Entities to merge into primary and then delete
            merge_strategy: How to handle conflicts (e.g., {"aliases": "combine", "attributes": "merge"})

        Returns:
            The merged primary entity, or None if not found
        """
        db = SessionLocal()
        try:
            # Get primary entity
            primary = db.query(Entity).filter(Entity.id == primary_entity_id).first()
            if not primary:
                return None

            # Get secondary entities
            secondaries = db.query(Entity).filter(Entity.id.in_(secondary_entity_ids)).all()

            # Merge aliases
            all_aliases = set(primary.aliases or [])
            for secondary in secondaries:
                # Add secondary's name as an alias (unless it's the same as primary)
                if secondary.name != primary.name:
                    all_aliases.add(secondary.name)
                # Add secondary's aliases
                all_aliases.update(secondary.aliases or [])

            primary.aliases = list(all_aliases)

            # Merge attributes based on strategy
            attributes_strategy = merge_strategy.get("attributes", "merge")
            merged_attributes = dict(primary.attributes or {})

            if attributes_strategy == "merge":
                for secondary in secondaries:
                    if secondary.attributes:
                        for key, value in secondary.attributes.items():
                            if key not in merged_attributes or not merged_attributes[key]:
                                merged_attributes[key] = value
                            elif isinstance(merged_attributes[key], list) and isinstance(value, list):
                                # Combine lists (e.g., appearance notes, personality traits)
                                merged_attributes[key] = list(set(merged_attributes[key] + value))
                            elif isinstance(merged_attributes[key], str) and isinstance(value, str):
                                # Append text content with separator
                                if value and value not in merged_attributes[key]:
                                    merged_attributes[key] = merged_attributes[key] + "\n\n" + value

            primary.attributes = merged_attributes

            # Merge appearance history
            all_appearances = list(primary.appearance_history or [])
            for secondary in secondaries:
                if secondary.appearance_history:
                    all_appearances.extend(secondary.appearance_history)
            primary.appearance_history = all_appearances

            # Merge template_data if present
            if primary.template_data or any(s.template_data for s in secondaries):
                merged_template = dict(primary.template_data or {})
                for secondary in secondaries:
                    if secondary.template_data:
                        for key, value in secondary.template_data.items():
                            if key not in merged_template or not merged_template[key]:
                                merged_template[key] = value
                primary.template_data = merged_template

            # Remap relationships from secondaries to primary
            from app.models.entity import Relationship
            for secondary in secondaries:
                # Update relationships where secondary is source
                db.query(Relationship).filter(
                    Relationship.source_entity_id == secondary.id
                ).update({Relationship.source_entity_id: primary.id})

                # Update relationships where secondary is target
                db.query(Relationship).filter(
                    Relationship.target_entity_id == secondary.id
                ).update({Relationship.target_entity_id: primary.id})

            # Remap EntityAppearance records
            from app.models.scene import EntityAppearance
            db.query(EntityAppearance).filter(
                EntityAppearance.entity_id.in_(secondary_entity_ids)
            ).update({EntityAppearance.entity_id: primary.id})

            # Remap character sheets (linked_entity_id in chapters table)
            from app.models.manuscript import Chapter
            db.query(Chapter).filter(
                Chapter.linked_entity_id.in_(secondary_entity_ids)
            ).update({Chapter.linked_entity_id: primary.id})

            # Delete duplicate self-referential relationships
            from sqlalchemy import and_
            db.query(Relationship).filter(
                and_(
                    Relationship.source_entity_id == primary.id,
                    Relationship.target_entity_id == primary.id
                )
            ).delete()

            # Delete secondary entities
            for secondary in secondaries:
                db.delete(secondary)

            db.commit()
            db.refresh(primary)
            return primary
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def add_appearance(
        self,
        entity_id: str,
        scene_id: Optional[str],
        description: str
    ) -> Optional[Entity]:
        """
        Add appearance record to entity

        Args:
            entity_id: Entity ID
            scene_id: Scene ID where entity appeared
            description: Description of appearance

        Returns:
            Updated Entity or None
        """
        db = SessionLocal()
        try:
            entity = db.query(Entity).filter(Entity.id == entity_id).first()

            if not entity:
                return None

            appearance = {
                "scene_id": scene_id,
                "description": description,
                "timestamp": datetime.utcnow().isoformat()
            }

            appearance_history = entity.appearance_history or []
            appearance_history.append(appearance)
            entity.appearance_history = appearance_history
            entity.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(entity)
            db.expunge(entity)
            return entity
        finally:
            db.close()

    # Relationship Management

    def create_relationship(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        strength: int = 1,
        context: Optional[List[Dict[str, Any]]] = None
    ) -> Relationship:
        """
        Create relationship between entities

        Args:
            source_entity_id: Source entity ID
            target_entity_id: Target entity ID
            relationship_type: Type (ROMANTIC, CONFLICT, ALLIANCE, etc.)
            strength: Interaction count
            context: List of {scene_id, description}

        Returns:
            Created Relationship
        """
        db = SessionLocal()
        try:
            # Check if relationship already exists
            existing = db.query(Relationship).filter(
                and_(
                    Relationship.source_entity_id == source_entity_id,
                    Relationship.target_entity_id == target_entity_id,
                    Relationship.relationship_type == relationship_type
                )
            ).first()

            if existing:
                # Update existing relationship
                existing.strength += strength
                if context:
                    existing_context = existing.context or []
                    existing_context.extend(context)
                    existing.context = existing_context
                existing.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing)
                db.expunge(existing)
                return existing

            # Create new relationship
            relationship = Relationship(
                source_entity_id=source_entity_id,
                target_entity_id=target_entity_id,
                relationship_type=relationship_type,
                strength=strength,
                context=context or []
            )
            db.add(relationship)
            db.commit()
            db.refresh(relationship)
            db.expunge(relationship)
            return relationship
        finally:
            db.close()

    def get_relationships(
        self,
        manuscript_id: str,
        entity_id: Optional[str] = None
    ) -> List[Relationship]:
        """
        Get relationships for a manuscript

        Args:
            manuscript_id: Manuscript ID
            entity_id: Optional entity ID filter

        Returns:
            List of relationships
        """
        db = SessionLocal()
        try:
            if entity_id:
                # Get relationships where entity is source or target
                relationships = db.query(Relationship).join(
                    Entity,
                    (Entity.id == Relationship.source_entity_id)
                ).filter(
                    Entity.manuscript_id == manuscript_id,
                    (Relationship.source_entity_id == entity_id) | (Relationship.target_entity_id == entity_id)
                ).all()
            else:
                # Get all relationships for the manuscript
                relationships = db.query(Relationship).join(
                    Entity,
                    (Entity.id == Relationship.source_entity_id)
                ).filter(
                    Entity.manuscript_id == manuscript_id
                ).all()

            # Detach from session
            result = []
            for rel in relationships:
                db.expunge(rel)
                result.append(rel)

            return result
        finally:
            db.close()

    def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete relationship

        Args:
            relationship_id: Relationship ID

        Returns:
            True if deleted, False if not found
        """
        db = SessionLocal()
        try:
            relationship = db.query(Relationship).filter(
                Relationship.id == relationship_id
            ).first()

            if not relationship:
                return False

            db.delete(relationship)
            db.commit()
            return True
        finally:
            db.close()

    # Suggestion Management

    def create_suggestion(
        self,
        manuscript_id: str,
        name: str,
        entity_type: str,
        context: str,
        extracted_description: Optional[str] = None,
        extracted_attributes: Optional[Dict[str, Any]] = None
    ) -> EntitySuggestion:
        """
        Create entity suggestion from NLP extraction

        Args:
            manuscript_id: Manuscript ID
            name: Suggested entity name
            entity_type: Suggested type
            context: Text where entity was found
            extracted_description: Description extracted from text patterns
            extracted_attributes: Categorized attributes (appearance, personality, etc.)

        Returns:
            Created suggestion
        """
        db = SessionLocal()
        try:
            # Check if suggestion already exists (any status)
            existing = db.query(EntitySuggestion).filter(
                and_(
                    EntitySuggestion.manuscript_id == manuscript_id,
                    EntitySuggestion.name == name,
                    EntitySuggestion.type == entity_type
                )
            ).first()

            if existing:
                # If already approved/rejected, don't create a new one
                # If pending, return the existing one
                return existing

            # Also check if an entity with this name already exists
            existing_entity = db.query(Entity).filter(
                and_(
                    Entity.manuscript_id == manuscript_id,
                    Entity.name == name
                )
            ).first()

            if existing_entity:
                # Entity already exists, no need for a suggestion
                return None

            suggestion = EntitySuggestion(
                manuscript_id=manuscript_id,
                name=name,
                type=entity_type,
                context=context,
                extracted_description=extracted_description,
                extracted_attributes=extracted_attributes,
                status="PENDING"
            )
            db.add(suggestion)
            db.commit()
            db.refresh(suggestion)
            db.expunge(suggestion)
            return suggestion
        finally:
            db.close()

    def get_suggestions(
        self,
        manuscript_id: str,
        status: Optional[str] = None
    ) -> List[EntitySuggestion]:
        """
        Get suggestions for a manuscript

        Args:
            manuscript_id: Manuscript ID
            status: Optional status filter (PENDING, APPROVED, REJECTED)

        Returns:
            List of suggestions
        """
        db = SessionLocal()
        try:
            query = db.query(EntitySuggestion).filter(
                EntitySuggestion.manuscript_id == manuscript_id
            )

            if status:
                query = query.filter(EntitySuggestion.status == status)

            suggestions = query.order_by(EntitySuggestion.created_at.desc()).all()

            # Detach from session
            result = []
            for suggestion in suggestions:
                db.expunge(suggestion)
                result.append(suggestion)

            return result
        finally:
            db.close()

    def approve_suggestion(
        self,
        suggestion_id: str,
        name_override: Optional[str] = None,
        type_override: Optional[str] = None,
        description: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Entity:
        """
        Approve suggestion and create entity with optional overrides

        Args:
            suggestion_id: Suggestion ID
            name_override: Override the suggested name
            type_override: Override the suggested type
            description: Description to add to entity attributes
            aliases: Optional aliases
            attributes: Optional attributes

        Returns:
            Created Entity

        Raises:
            ValueError: If suggestion not found or already processed
        """
        db = SessionLocal()
        try:
            suggestion = db.query(EntitySuggestion).filter(
                EntitySuggestion.id == suggestion_id
            ).first()

            if not suggestion:
                raise ValueError(f"Suggestion {suggestion_id} not found")

            if suggestion.status != "PENDING":
                raise ValueError(f"Suggestion already {suggestion.status}")

            # Use overrides if provided, otherwise use suggestion values
            final_name = name_override if name_override else suggestion.name
            final_type = type_override if type_override else suggestion.type

            # Build final attributes
            final_attributes = attributes or {}
            if description:
                final_attributes["description"] = description

            # Create entity
            entity = Entity(
                manuscript_id=suggestion.manuscript_id,
                type=final_type,
                name=final_name,
                aliases=aliases or [],
                attributes=final_attributes
            )
            db.add(entity)

            # Update suggestion status
            suggestion.status = "APPROVED"

            db.commit()
            db.refresh(entity)
            db.expunge(entity)
            return entity
        finally:
            db.close()

    def reject_suggestion(self, suggestion_id: str) -> bool:
        """
        Reject suggestion

        Args:
            suggestion_id: Suggestion ID

        Returns:
            True if rejected, False if not found

        Raises:
            ValueError: If suggestion already processed
        """
        db = SessionLocal()
        try:
            suggestion = db.query(EntitySuggestion).filter(
                EntitySuggestion.id == suggestion_id
            ).first()

            if not suggestion:
                return False

            if suggestion.status != "PENDING":
                raise ValueError(f"Suggestion already {suggestion.status}")

            suggestion.status = "REJECTED"
            db.commit()
            return True
        finally:
            db.close()

    def get_entity_appearance_summary(self, entity_id: str) -> Dict[str, Any]:
        """
        Get first and last appearance summary for an entity

        Args:
            entity_id: Entity ID

        Returns:
            Dict with first_appearance, last_appearance, total_appearances
        """
        db = SessionLocal()
        try:
            # Get all appearances for this entity, ordered by chapter order and sequence
            appearances = db.query(EntityAppearance).filter(
                EntityAppearance.entity_id == entity_id
            ).join(
                Chapter, EntityAppearance.chapter_id == Chapter.id
            ).order_by(
                Chapter.order.asc(),
                EntityAppearance.sequence_order.asc()
            ).all()

            if not appearances:
                return {
                    "first_appearance": None,
                    "last_appearance": None,
                    "total_appearances": 0
                }

            # Get first and last
            first = appearances[0]
            last = appearances[-1]

            # Get chapter info for each
            first_chapter = db.query(Chapter).filter(Chapter.id == first.chapter_id).first()
            last_chapter = db.query(Chapter).filter(Chapter.id == last.chapter_id).first()

            return {
                "first_appearance": {
                    "chapter_id": first.chapter_id,
                    "chapter_title": first_chapter.title if first_chapter else "Unknown",
                    "chapter_order": first_chapter.order if first_chapter else 0,
                    "summary": first.summary,
                    "created_at": first.created_at.isoformat() if first.created_at else None
                },
                "last_appearance": {
                    "chapter_id": last.chapter_id,
                    "chapter_title": last_chapter.title if last_chapter else "Unknown",
                    "chapter_order": last_chapter.order if last_chapter else 0,
                    "summary": last.summary,
                    "created_at": last.created_at.isoformat() if last.created_at else None
                },
                "total_appearances": len(appearances)
            }
        finally:
            db.close()

    def get_entity_appearance_contexts(self, entity_id: str) -> List[Dict[str, Any]]:
        """
        Get all appearance contexts for an entity (for AI analysis)

        Args:
            entity_id: Entity ID

        Returns:
            List of appearance context dicts
        """
        db = SessionLocal()
        try:
            appearances = db.query(EntityAppearance).filter(
                EntityAppearance.entity_id == entity_id
            ).join(
                Chapter, EntityAppearance.chapter_id == Chapter.id
            ).order_by(
                Chapter.order.asc(),
                EntityAppearance.sequence_order.asc()
            ).all()

            result = []
            for app in appearances:
                chapter = db.query(Chapter).filter(Chapter.id == app.chapter_id).first()
                result.append({
                    "chapter_title": chapter.title if chapter else "Unknown",
                    "summary": app.summary,
                    "context_text": app.context_text
                })

            return result
        finally:
            db.close()


# Global instance
codex_service = CodexService()
