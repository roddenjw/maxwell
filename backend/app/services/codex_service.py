"""
Codex service for entity and relationship management
Handles CRUD operations for characters, locations, items, and lore
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import and_

from app.database import SessionLocal
from app.models.entity import Entity, Relationship, EntitySuggestion


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
            return entity
        finally:
            db.close()

    def delete_entity(self, entity_id: str) -> bool:
        """
        Delete entity

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

            db.delete(entity)
            db.commit()
            return True
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
            # Check if suggestion already exists
            existing = db.query(EntitySuggestion).filter(
                and_(
                    EntitySuggestion.manuscript_id == manuscript_id,
                    EntitySuggestion.name == name,
                    EntitySuggestion.type == entity_type,
                    EntitySuggestion.status == "PENDING"
                )
            ).first()

            if existing:
                return existing

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


# Global instance
codex_service = CodexService()
