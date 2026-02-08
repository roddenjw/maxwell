"""
World and Series Service
Handles business logic for world/series management and entity scoping
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
import logging
from datetime import datetime

from app.models import World, Series, Manuscript, Entity, ENTITY_SCOPE_MANUSCRIPT, ENTITY_SCOPE_SERIES, ENTITY_SCOPE_WORLD

logger = logging.getLogger(__name__)


class WorldService:
    """Service for managing worlds and series"""

    # ========================
    # World CRUD Operations
    # ========================

    def create_world(
        self,
        db: Session,
        name: str,
        description: str = "",
        settings: dict = None
    ) -> World:
        """Create a new world"""
        world = World(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            settings=settings or {}
        )
        db.add(world)
        db.commit()
        db.refresh(world)
        return world

    def get_world(self, db: Session, world_id: str) -> Optional[World]:
        """Get a world by ID"""
        return db.query(World).filter(World.id == world_id).first()

    def list_worlds(self, db: Session, skip: int = 0, limit: int = 100) -> List[World]:
        """List all worlds"""
        return db.query(World).offset(skip).limit(limit).all()

    def update_world(
        self,
        db: Session,
        world_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[dict] = None
    ) -> Optional[World]:
        """Update a world"""
        world = self.get_world(db, world_id)
        if not world:
            return None

        if name is not None:
            world.name = name
        if description is not None:
            world.description = description
        if settings is not None:
            world.settings = settings

        world.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(world)
        return world

    def delete_world(self, db: Session, world_id: str) -> bool:
        """Delete a world and all its series/manuscripts/entities"""
        world = self.get_world(db, world_id)
        if not world:
            return False

        db.delete(world)
        db.commit()
        return True

    # ========================
    # Series CRUD Operations
    # ========================

    def create_series(
        self,
        db: Session,
        world_id: str,
        name: str,
        description: str = "",
        order_index: int = 0
    ) -> Optional[Series]:
        """Create a new series in a world"""
        # Verify world exists
        world = self.get_world(db, world_id)
        if not world:
            return None

        series = Series(
            id=str(uuid.uuid4()),
            world_id=world_id,
            name=name,
            description=description,
            order_index=order_index
        )
        db.add(series)
        db.commit()
        db.refresh(series)
        return series

    def get_series(self, db: Session, series_id: str) -> Optional[Series]:
        """Get a series by ID"""
        return db.query(Series).filter(Series.id == series_id).first()

    def list_series_in_world(
        self,
        db: Session,
        world_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Series]:
        """List all series in a world"""
        return (
            db.query(Series)
            .filter(Series.world_id == world_id)
            .order_by(Series.order_index)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_series(
        self,
        db: Session,
        series_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        order_index: Optional[int] = None
    ) -> Optional[Series]:
        """Update a series"""
        series = self.get_series(db, series_id)
        if not series:
            return None

        if name is not None:
            series.name = name
        if description is not None:
            series.description = description
        if order_index is not None:
            series.order_index = order_index

        series.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(series)
        return series

    def delete_series(self, db: Session, series_id: str) -> bool:
        """Delete a series (manuscripts become orphaned)"""
        series = self.get_series(db, series_id)
        if not series:
            return False

        # Orphan manuscripts instead of deleting them
        for manuscript in series.manuscripts:
            manuscript.series_id = None

        db.delete(series)
        db.commit()
        return True

    # ========================
    # Manuscript Assignment
    # ========================

    def assign_manuscript_to_series(
        self,
        db: Session,
        manuscript_id: str,
        series_id: str,
        order_index: Optional[int] = None
    ) -> Optional[Manuscript]:
        """Assign a manuscript to a series and auto-populate codex from world wiki"""
        manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
        series = self.get_series(db, series_id)

        if not manuscript or not series:
            return None

        manuscript.series_id = series_id
        if order_index is not None:
            manuscript.order_index = order_index

        manuscript.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(manuscript)

        # Auto-populate codex from world wiki
        try:
            from app.services.wiki_codex_bridge import WikiCodexBridge
            bridge = WikiCodexBridge(db)
            bridge.bulk_sync_wiki_to_manuscript(series.world_id, manuscript_id)
        except Exception as e:
            logger.warning(f"Failed to auto-populate codex from wiki: {e}")

        return manuscript

    def remove_manuscript_from_series(
        self,
        db: Session,
        manuscript_id: str
    ) -> Optional[Manuscript]:
        """Remove a manuscript from its series (make standalone)"""
        manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
        if not manuscript:
            return None

        manuscript.series_id = None
        manuscript.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(manuscript)
        return manuscript

    def list_manuscripts_in_series(
        self,
        db: Session,
        series_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Manuscript]:
        """List all manuscripts in a series"""
        return (
            db.query(Manuscript)
            .filter(Manuscript.series_id == series_id)
            .order_by(Manuscript.order_index)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_manuscripts_in_world(
        self,
        db: Session,
        world_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Manuscript]:
        """List all manuscripts in a world (across all series)"""
        series_ids = [s.id for s in self.list_series_in_world(db, world_id)]
        return (
            db.query(Manuscript)
            .filter(Manuscript.series_id.in_(series_ids))
            .order_by(Manuscript.order_index)
            .offset(skip)
            .limit(limit)
            .all()
        )

    # ========================
    # Entity Scoping
    # ========================

    def create_world_entity(
        self,
        db: Session,
        world_id: str,
        entity_type: str,
        name: str,
        aliases: List[str] = None,
        attributes: dict = None
    ) -> Optional[Entity]:
        """Create an entity at the world scope (shared across all manuscripts)"""
        world = self.get_world(db, world_id)
        if not world:
            return None

        entity = Entity(
            id=str(uuid.uuid4()),
            world_id=world_id,
            manuscript_id=None,  # World entities don't belong to a manuscript
            scope=ENTITY_SCOPE_WORLD,
            type=entity_type,
            name=name,
            aliases=aliases or [],
            attributes=attributes or {}
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    def list_world_entities(
        self,
        db: Session,
        world_id: str,
        entity_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Entity]:
        """List all world-scoped entities"""
        query = db.query(Entity).filter(
            and_(
                Entity.world_id == world_id,
                Entity.scope == ENTITY_SCOPE_WORLD
            )
        )

        if entity_type:
            query = query.filter(Entity.type == entity_type)

        return query.order_by(Entity.name).offset(skip).limit(limit).all()

    def get_entities_for_manuscript(
        self,
        db: Session,
        manuscript_id: str,
        include_world_entities: bool = True,
        entity_type: Optional[str] = None
    ) -> List[Entity]:
        """
        Get all entities visible to a manuscript.
        Includes manuscript-local entities and optionally world-scoped entities.
        """
        # Get manuscript to find its world
        manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
        if not manuscript:
            return []

        # Get manuscript-local entities
        query = db.query(Entity).filter(Entity.manuscript_id == manuscript_id)
        if entity_type:
            query = query.filter(Entity.type == entity_type)

        entities = query.all()

        # Optionally include world entities
        if include_world_entities and manuscript.series_id:
            series = self.get_series(db, manuscript.series_id)
            if series:
                world_entities = self.list_world_entities(
                    db, series.world_id, entity_type
                )
                entities.extend(world_entities)

        return entities

    def change_entity_scope(
        self,
        db: Session,
        entity_id: str,
        new_scope: str,
        world_id: Optional[str] = None
    ) -> Optional[Entity]:
        """
        Change an entity's scope.
        - To MANUSCRIPT: entity stays with its manuscript
        - To WORLD: entity moves to the world level (requires world_id)
        """
        entity = db.query(Entity).filter(Entity.id == entity_id).first()
        if not entity:
            return None

        if new_scope == ENTITY_SCOPE_WORLD:
            if not world_id:
                return None
            entity.scope = ENTITY_SCOPE_WORLD
            entity.world_id = world_id
            # Keep manuscript_id to track origin, or set to None
            # Keeping it allows us to know where the entity came from
        elif new_scope == ENTITY_SCOPE_MANUSCRIPT:
            entity.scope = ENTITY_SCOPE_MANUSCRIPT
            entity.world_id = None

        entity.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(entity)
        return entity

    def copy_entity_to_manuscript(
        self,
        db: Session,
        entity_id: str,
        manuscript_id: str
    ) -> Optional[Entity]:
        """
        Copy a world entity to a manuscript as a local entity.
        Useful when writers want to customize a shared entity for a specific book.
        """
        source_entity = db.query(Entity).filter(Entity.id == entity_id).first()
        manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()

        if not source_entity or not manuscript:
            return None

        # Create a copy with manuscript scope
        new_entity = Entity(
            id=str(uuid.uuid4()),
            manuscript_id=manuscript_id,
            world_id=None,
            scope=ENTITY_SCOPE_MANUSCRIPT,
            type=source_entity.type,
            name=source_entity.name,
            aliases=source_entity.aliases.copy() if source_entity.aliases else [],
            attributes=source_entity.attributes.copy() if source_entity.attributes else {}
        )
        db.add(new_entity)
        db.commit()
        db.refresh(new_entity)
        return new_entity

    # ========================
    # Helper Methods
    # ========================

    def get_world_for_manuscript(
        self,
        db: Session,
        manuscript_id: str
    ) -> Optional[World]:
        """Get the world that a manuscript belongs to"""
        manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
        if not manuscript or not manuscript.series_id:
            return None

        series = self.get_series(db, manuscript.series_id)
        if not series:
            return None

        return self.get_world(db, series.world_id)

    def ensure_manuscript_has_world(
        self,
        db: Session,
        manuscript_id: str
    ) -> Optional[World]:
        """
        Ensure a manuscript belongs to a world. If standalone, auto-create one.

        Creates a world named after the manuscript, a "Standalone" series,
        assigns the manuscript, and syncs existing codex entities to wiki.
        """
        # Check if manuscript already has a world
        existing_world = self.get_world_for_manuscript(db, manuscript_id)
        if existing_world:
            return existing_world

        manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
        if not manuscript:
            return None

        # Create world named after manuscript
        world = self.create_world(
            db=db,
            name=f"{manuscript.title} World",
            description=f"Auto-created world for \"{manuscript.title}\"",
        )

        # Create a standalone series
        series = self.create_series(
            db=db,
            world_id=world.id,
            name="Standalone",
            description="Default series for standalone manuscripts",
            order_index=0,
        )

        # Assign manuscript to the series
        self.assign_manuscript_to_series(
            db=db,
            manuscript_id=manuscript_id,
            series_id=series.id,
            order_index=0,
        )

        # Sync existing codex entities to the new wiki
        try:
            from app.services.wiki_codex_bridge import WikiCodexBridge
            bridge = WikiCodexBridge(db)
            bridge.bulk_sync_manuscript_to_wiki(manuscript_id, world.id)
        except Exception as e:
            logger.warning(f"Failed to sync codex to wiki during world creation: {e}")

        return world

    def move_manuscript_to_world(
        self,
        db: Session,
        manuscript_id: str,
        target_series_id: str,
        order_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Move a manuscript to a different series (possibly in a different world).

        For same-world moves, just updates series_id.
        For cross-world moves, transfers wiki data and re-populates codex.
        """
        from app.models.wiki import WikiEntry, WikiChange, WikiCrossReference
        from app.models.character_arc import CharacterArc
        from app.services.wiki_codex_bridge import WikiCodexBridge
        from app.services.wiki_service import generate_slug

        manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
        target_series = self.get_series(db, target_series_id)

        if not manuscript or not target_series:
            return {"error": "Manuscript or target series not found"}

        target_world_id = target_series.world_id
        source_world = self.get_world_for_manuscript(db, manuscript_id)
        source_world_id = source_world.id if source_world else None

        stats = {
            "entries_copied": 0,
            "entries_merged": 0,
            "changes_copied": 0,
            "arcs_updated": 0,
            "cross_world": source_world_id != target_world_id,
        }

        # Same world — just move series
        if source_world_id == target_world_id:
            manuscript.series_id = target_series_id
            if order_index is not None:
                manuscript.order_index = order_index
            manuscript.updated_at = datetime.utcnow()
            db.commit()
            return stats

        # Cross-world move: transfer wiki data
        # 1. Find wiki entries where this manuscript is a source
        source_entries = db.query(WikiEntry).filter(
            WikiEntry.world_id == source_world_id
        ).all()

        entry_id_map = {}  # old_id -> new_id (for cross-references and arcs)

        for entry in source_entries:
            sources = entry.source_manuscripts or []
            if manuscript_id not in sources:
                continue

            # Check for duplicate in target world by slug
            existing = db.query(WikiEntry).filter(
                WikiEntry.world_id == target_world_id,
                WikiEntry.slug == entry.slug,
            ).first()

            if existing:
                # Merge: add manuscript to existing entry's sources
                target_sources = existing.source_manuscripts or []
                if manuscript_id not in target_sources:
                    target_sources.append(manuscript_id)
                    existing.source_manuscripts = target_sources
                    existing.updated_at = datetime.utcnow()
                entry_id_map[entry.id] = existing.id
                stats["entries_merged"] += 1
            else:
                # Copy entry to target world
                new_entry = WikiEntry(
                    id=str(uuid.uuid4()),
                    world_id=target_world_id,
                    entry_type=entry.entry_type,
                    title=entry.title,
                    slug=entry.slug,
                    structured_data=entry.structured_data,
                    content=entry.content,
                    summary=entry.summary,
                    image_url=entry.image_url,
                    image_seed=entry.image_seed,
                    parent_id=None,
                    source_manuscripts=[manuscript_id],
                    source_chapters=entry.source_chapters,
                    status=entry.status,
                    confidence_score=entry.confidence_score,
                    tags=entry.tags,
                    aliases=entry.aliases,
                )
                db.add(new_entry)
                db.flush()
                entry_id_map[entry.id] = new_entry.id
                stats["entries_copied"] += 1

            # Remove manuscript from source entry's sources
            sources = [s for s in sources if s != manuscript_id]
            entry.source_manuscripts = sources
            entry.updated_at = datetime.utcnow()

        # 2. Copy WikiChange rows for this manuscript
        source_changes = db.query(WikiChange).filter(
            WikiChange.source_manuscript_id == manuscript_id,
            WikiChange.world_id == source_world_id,
        ).all()

        for change in source_changes:
            new_entry_id = entry_id_map.get(change.wiki_entry_id)
            new_change = WikiChange(
                id=str(uuid.uuid4()),
                wiki_entry_id=new_entry_id,
                world_id=target_world_id,
                change_type=change.change_type,
                field_changed=change.field_changed,
                old_value=change.old_value,
                new_value=change.new_value,
                proposed_entry=change.proposed_entry,
                reason=change.reason,
                source_text=change.source_text,
                source_chapter_id=change.source_chapter_id,
                source_manuscript_id=manuscript_id,
                confidence=change.confidence,
                status=change.status,
                priority=change.priority,
            )
            db.add(new_change)
            stats["changes_copied"] += 1

        # 3. Update CharacterArc wiki entry references
        for old_id, new_id in entry_id_map.items():
            arcs = db.query(CharacterArc).filter(
                CharacterArc.wiki_entry_id == old_id,
                CharacterArc.manuscript_id == manuscript_id,
            ).all()
            for arc in arcs:
                arc.wiki_entry_id = new_id
                stats["arcs_updated"] += 1

        # 4. Copy cross-references between transferred entries
        old_ids = set(entry_id_map.keys())
        for old_id in old_ids:
            cross_refs = db.query(WikiCrossReference).filter(
                WikiCrossReference.source_entry_id == old_id
            ).all()
            for ref in cross_refs:
                if ref.target_entry_id in old_ids:
                    new_ref = WikiCrossReference(
                        id=str(uuid.uuid4()),
                        source_entry_id=entry_id_map[ref.source_entry_id],
                        target_entry_id=entry_id_map[ref.target_entry_id],
                        reference_type=ref.reference_type,
                        context=ref.context,
                        context_chapter_id=ref.context_chapter_id,
                        bidirectional=ref.bidirectional,
                        display_label=ref.display_label,
                    )
                    db.add(new_ref)

        # 5. Move manuscript to target series
        manuscript.series_id = target_series_id
        if order_index is not None:
            manuscript.order_index = order_index
        manuscript.updated_at = datetime.utcnow()

        db.commit()

        # 6. Re-populate codex from new world's wiki
        try:
            bridge = WikiCodexBridge(db)
            bridge.bulk_sync_wiki_to_manuscript(target_world_id, manuscript_id)
        except Exception as e:
            logger.warning(f"Failed to re-populate codex after move: {e}")

        return stats


# Global service instance
world_service = WorldService()
