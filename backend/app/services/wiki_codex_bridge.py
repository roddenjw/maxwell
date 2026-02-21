"""
Wiki-Codex Bridge Service - Syncs manuscript Codex entities with World Wiki entries.

The Codex is the manuscript-level view into the World Wiki:
- When an entity is created in Codex → Creates/links to Wiki entry
- When a Wiki entry is updated → Updates linked Codex entities
- Entities can override Wiki data for manuscript-specific needs
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import asyncio
import logging
import uuid

from app.models.entity import Entity, ENTITY_SCOPE_MANUSCRIPT, ENTITY_SCOPE_WORLD
from app.models.wiki import WikiEntry, WikiEntryType, WikiEntryStatus, WikiChange
from app.models.world import World
from app.models.manuscript import Manuscript
from app.services.wiki_service import WikiService, generate_slug

logger = logging.getLogger(__name__)


# Map Codex entity types to Wiki entry types
ENTITY_TO_WIKI_TYPE = {
    "CHARACTER": WikiEntryType.CHARACTER.value,
    "LOCATION": WikiEntryType.LOCATION.value,
    "ITEM": WikiEntryType.ARTIFACT.value,
    "LORE": WikiEntryType.WORLD_RULE.value,
    "CULTURE": WikiEntryType.CULTURE.value,
    "CREATURE": WikiEntryType.CREATURE.value,
    "RACE": WikiEntryType.CREATURE.value,
    "ORGANIZATION": WikiEntryType.FACTION.value,
    "EVENT": WikiEntryType.EVENT.value,
}

# Explicit reverse mapping (CREATURE wins over RACE since both map to creature)
WIKI_TO_ENTITY_TYPE = {
    WikiEntryType.CHARACTER.value: "CHARACTER",
    WikiEntryType.LOCATION.value: "LOCATION",
    WikiEntryType.ARTIFACT.value: "ITEM",
    WikiEntryType.WORLD_RULE.value: "LORE",
    WikiEntryType.CULTURE.value: "CULTURE",
    WikiEntryType.CREATURE.value: "CREATURE",
    WikiEntryType.FACTION.value: "ORGANIZATION",
    WikiEntryType.EVENT.value: "EVENT",
}


class WikiCodexBridge:
    """
    Bridges manuscript Codex entities to World Wiki entries.

    Maintains synchronization between:
    - Manuscript-level Codex entities
    - World-level Wiki entries
    """

    def __init__(self, db: Session):
        self.db = db
        self.wiki_service = WikiService(db)

    def sync_entity_to_wiki(
        self,
        entity: Entity,
        world_id: str,
        create_if_missing: bool = True
    ) -> Optional[WikiEntry]:
        """
        Create or update wiki entry from Codex entity.

        If entity is already linked to a wiki entry, updates it.
        If not, searches for matching entry or creates new one.
        """
        # If entity already has a wiki entry linked
        if entity.wiki_entry:
            return self._update_wiki_from_entity(entity, entity.wiki_entry)

        # Search for existing wiki entry by name
        wiki_type = ENTITY_TO_WIKI_TYPE.get(entity.type, WikiEntryType.CHARACTER.value)
        existing = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == wiki_type,
            WikiEntry.title.ilike(entity.name)
        ).first()

        if existing:
            # Link entity to existing wiki entry
            entity.linked_wiki_entry_id = existing.id
            self.db.commit()
            return existing

        if not create_if_missing:
            return None

        # Create new wiki entry
        structured_data = self._entity_to_structured_data(entity)

        wiki_entry = self.wiki_service.create_entry(
            world_id=world_id,
            entry_type=wiki_type,
            title=entity.name,
            content=self._entity_to_content(entity),
            structured_data=structured_data,
            summary=entity.attributes.get('description', ''),
            aliases=entity.aliases or [],
            source_manuscripts=[entity.manuscript_id] if entity.manuscript_id else [],
            created_by="codex_sync"
        )

        # Link entity to wiki entry
        entity.linked_wiki_entry_id = wiki_entry.id
        self.db.commit()

        return wiki_entry

    def sync_wiki_to_entity(
        self,
        wiki_entry: WikiEntry,
        manuscript_id: str,
        create_if_missing: bool = True
    ) -> Optional[Entity]:
        """
        Create or update Codex entity from Wiki entry.

        If a linked entity exists for this manuscript, updates it.
        If not, creates a new entity linked to the wiki entry.
        """
        # Find existing entity linked to this wiki entry in this manuscript
        existing = self.db.query(Entity).filter(
            Entity.linked_wiki_entry_id == wiki_entry.id,
            Entity.manuscript_id == manuscript_id
        ).first()

        if existing:
            return self._update_entity_from_wiki(wiki_entry, existing)

        if not create_if_missing:
            return None

        # Create new entity from wiki entry
        entity_type = WIKI_TO_ENTITY_TYPE.get(
            wiki_entry.entry_type,
            "CHARACTER"
        )

        entity = Entity(
            id=str(uuid.uuid4()),
            manuscript_id=manuscript_id,
            type=entity_type,
            name=wiki_entry.title,
            aliases=wiki_entry.aliases or [],
            attributes=self._wiki_to_attributes(wiki_entry),
            template_data=wiki_entry.structured_data or {},
            linked_wiki_entry_id=wiki_entry.id,
            scope=ENTITY_SCOPE_MANUSCRIPT,
            created_at=datetime.utcnow()
        )

        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

        return entity

    def get_manuscript_overrides(
        self,
        wiki_entry_id: str,
        manuscript_id: str
    ) -> Dict[str, Any]:
        """
        Get manuscript-specific overrides for a wiki entry.

        Returns the differences between the wiki entry and the
        linked entity in this manuscript.
        """
        wiki_entry = self.wiki_service.get_entry(wiki_entry_id)
        if not wiki_entry:
            return {}

        entity = self.db.query(Entity).filter(
            Entity.linked_wiki_entry_id == wiki_entry_id,
            Entity.manuscript_id == manuscript_id
        ).first()

        if not entity:
            return {}

        overrides = {}

        # Compare names
        if entity.name != wiki_entry.title:
            overrides['name'] = entity.name

        # Compare aliases
        if set(entity.aliases or []) != set(wiki_entry.aliases or []):
            overrides['aliases'] = entity.aliases

        # Compare attributes/structured_data
        wiki_data = wiki_entry.structured_data or {}
        entity_data = entity.attributes or {}

        for key, entity_value in entity_data.items():
            wiki_value = wiki_data.get(key)
            if entity_value != wiki_value:
                if 'attributes' not in overrides:
                    overrides['attributes'] = {}
                overrides['attributes'][key] = entity_value

        return overrides

    def bulk_sync_manuscript_to_wiki(
        self,
        manuscript_id: str,
        world_id: str
    ) -> Dict[str, Any]:
        """
        Sync all entities from a manuscript to the world wiki.

        Returns statistics about the sync operation.
        """
        entities = self.db.query(Entity).filter(
            Entity.manuscript_id == manuscript_id
        ).all()

        stats = {
            "total": len(entities),
            "created": 0,
            "updated": 0,
            "linked": 0,
            "errors": []
        }

        for entity in entities:
            try:
                # Check if already linked
                was_linked = entity.wiki_entry is not None

                wiki_entry = self.sync_entity_to_wiki(entity, world_id)

                if wiki_entry:
                    if was_linked:
                        stats["updated"] += 1
                    elif self.db.query(WikiEntry).filter(
                        WikiEntry.id == entity.linked_wiki_entry_id
                    ).first():
                        stats["linked"] += 1
                    else:
                        stats["created"] += 1
            except Exception as e:
                stats["errors"].append({
                    "entity_id": entity.id,
                    "entity_name": entity.name,
                    "error": str(e)
                })

        return stats

    def bulk_sync_wiki_to_manuscript(
        self,
        world_id: str,
        manuscript_id: str,
        entry_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sync wiki entries from a world to a manuscript's codex.

        Returns statistics about the sync operation.
        """
        query = self.db.query(WikiEntry).filter(WikiEntry.world_id == world_id)

        if entry_types:
            query = query.filter(WikiEntry.entry_type.in_(entry_types))

        wiki_entries = query.all()

        stats = {
            "total": len(wiki_entries),
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": []
        }

        for wiki_entry in wiki_entries:
            try:
                # Check if entity already exists
                existing = self.db.query(Entity).filter(
                    Entity.linked_wiki_entry_id == wiki_entry.id,
                    Entity.manuscript_id == manuscript_id
                ).first()

                if existing:
                    self._update_entity_from_wiki(wiki_entry, existing)
                    stats["updated"] += 1
                else:
                    entity = self.sync_wiki_to_entity(wiki_entry, manuscript_id)
                    if entity:
                        stats["created"] += 1
                    else:
                        stats["skipped"] += 1

            except Exception as e:
                stats["errors"].append({
                    "wiki_entry_id": wiki_entry.id,
                    "wiki_title": wiki_entry.title,
                    "error": str(e)
                })

        return stats

    def agent_merge_entity_to_wiki(
        self,
        entity: Entity,
        world_id: str,
        api_key: Optional[str] = None,
    ) -> Optional[WikiEntry]:
        """
        Sync a codex entity to wiki using AI merge agent when there's an
        existing entry to merge with. Falls back to simple sync when:
        - No API key available
        - Entry is new (no conflict to resolve)
        - Agent returns error

        For existing entries with changes, the agent produces a merged version.
        High confidence (>= 0.85) → auto-apply. Low confidence → queue WikiChange.
        """
        wiki_type = ENTITY_TO_WIKI_TYPE.get(entity.type, WikiEntryType.CHARACTER.value)

        # Find existing wiki entry by link or name match
        wiki_entry = None
        if entity.linked_wiki_entry_id:
            wiki_entry = self.db.query(WikiEntry).filter(
                WikiEntry.id == entity.linked_wiki_entry_id
            ).first()

        if not wiki_entry:
            wiki_entry = self.db.query(WikiEntry).filter(
                WikiEntry.world_id == world_id,
                WikiEntry.entry_type == wiki_type,
                WikiEntry.title.ilike(entity.name)
            ).first()

        # New entry — create directly, no merge needed
        if not wiki_entry:
            return self.sync_entity_to_wiki(entity, world_id, create_if_missing=True)

        # Link entity if not already linked
        if not entity.linked_wiki_entry_id:
            entity.linked_wiki_entry_id = wiki_entry.id
            self.db.commit()

        # No API key — fall back to simple merge
        if not api_key:
            return self._update_wiki_from_entity(entity, wiki_entry)

        # Use AI merge agent
        try:
            from app.agents.specialized.wiki_merge_agent import merge_entity_into_wiki

            existing_wiki = {
                "title": wiki_entry.title,
                "content": wiki_entry.content or "",
                "structured_data": wiki_entry.structured_data or {},
                "summary": wiki_entry.summary or "",
                "aliases": wiki_entry.aliases or [],
            }
            incoming_entity = {
                "name": entity.name,
                "type": entity.type,
                "attributes": entity.attributes or {},
                "aliases": entity.aliases or [],
            }

            # Run async merge in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(
                        asyncio.run,
                        merge_entity_into_wiki(
                            api_key=api_key,
                            existing_wiki=existing_wiki,
                            incoming_entity=incoming_entity,
                            entry_type=wiki_type,
                        )
                    ).result()
            else:
                result = asyncio.run(
                    merge_entity_into_wiki(
                        api_key=api_key,
                        existing_wiki=existing_wiki,
                        incoming_entity=incoming_entity,
                        entry_type=wiki_type,
                    )
                )

            # High confidence — auto-apply
            if result.confidence >= 0.85 and not result.needs_review:
                updates = {
                    "content": result.merged_content,
                    "structured_data": result.merged_structured_data,
                    "summary": result.merged_summary,
                    "aliases": result.merged_aliases,
                }

                # Add manuscript to sources
                sources = wiki_entry.source_manuscripts or []
                if entity.manuscript_id and entity.manuscript_id not in sources:
                    sources.append(entity.manuscript_id)
                    updates["source_manuscripts"] = sources

                return self.wiki_service.update_entry(wiki_entry.id, updates)

            # Low confidence — queue for review
            change = WikiChange(
                id=str(uuid.uuid4()),
                wiki_entry_id=wiki_entry.id,
                world_id=world_id,
                change_type="MERGE",
                field_changed=None,
                old_value={
                    "content": wiki_entry.content,
                    "structured_data": wiki_entry.structured_data,
                    "summary": wiki_entry.summary,
                    "aliases": wiki_entry.aliases,
                },
                new_value={
                    "content": result.merged_content,
                    "structured_data": result.merged_structured_data,
                    "summary": result.merged_summary,
                    "aliases": result.merged_aliases,
                },
                reason=result.reason,
                source_text=f"Codex entity '{entity.name}' updated in manuscript",
                source_manuscript_id=entity.manuscript_id,
                confidence=result.confidence,
                status="PENDING",
                priority=1,
            )
            self.db.add(change)
            self.db.commit()

            return wiki_entry

        except Exception as e:
            logger.warning(f"Agent merge failed, falling back to simple merge: {e}")
            return self._update_wiki_from_entity(entity, wiki_entry)

    def _update_wiki_from_entity(
        self,
        entity: Entity,
        wiki_entry: WikiEntry
    ) -> WikiEntry:
        """Update wiki entry from entity data"""
        updates = {}

        # Only update if entity has more recent data
        if entity.updated_at and wiki_entry.updated_at:
            if entity.updated_at <= wiki_entry.updated_at:
                return wiki_entry

        # Update structured data, merging with existing
        if entity.attributes:
            current_data = wiki_entry.structured_data or {}
            current_data.update(entity.attributes)
            updates['structured_data'] = current_data

        # Update aliases if entity has more
        if entity.aliases:
            current_aliases = set(wiki_entry.aliases or [])
            current_aliases.update(entity.aliases)
            updates['aliases'] = list(current_aliases)

        # Add manuscript to sources if not present
        if entity.manuscript_id:
            sources = wiki_entry.source_manuscripts or []
            if entity.manuscript_id not in sources:
                sources.append(entity.manuscript_id)
                updates['source_manuscripts'] = sources

        if updates:
            return self.wiki_service.update_entry(wiki_entry.id, updates)

        return wiki_entry

    def _update_entity_from_wiki(
        self,
        wiki_entry: WikiEntry,
        entity: Entity
    ) -> Entity:
        """Update entity from wiki data"""
        # Update basic fields
        entity.name = wiki_entry.title
        entity.aliases = wiki_entry.aliases or entity.aliases

        # Merge attributes with wiki data
        wiki_data = wiki_entry.structured_data or {}
        entity_attrs = entity.attributes or {}

        # Wiki data serves as base, entity data overrides
        merged = {**wiki_data, **entity_attrs}
        entity.attributes = merged

        entity.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(entity)

        return entity

    def _entity_to_structured_data(self, entity: Entity) -> Dict:
        """Convert entity attributes to wiki structured data"""
        data = {}

        if entity.type == "CHARACTER":
            attrs = entity.attributes or {}
            data = {
                "role": attrs.get("role", ""),
                "age": attrs.get("age", ""),
                "appearance": attrs.get("appearance", ""),
                "personality": attrs.get("personality", ""),
                "backstory": attrs.get("backstory", ""),
                "motivation": attrs.get("motivation", ""),
                "voice": attrs.get("voice", "")
            }
        elif entity.type == "LOCATION":
            attrs = entity.attributes or {}
            data = {
                "description": attrs.get("description", ""),
                "atmosphere": attrs.get("atmosphere", ""),
                "geography": attrs.get("geography", ""),
                "history": attrs.get("history", "")
            }
        elif entity.type == "ITEM":
            attrs = entity.attributes or {}
            data = {
                "description": attrs.get("description", ""),
                "significance": attrs.get("significance", ""),
                "history": attrs.get("history", ""),
                "powers": attrs.get("powers", "")
            }
        else:
            data = entity.attributes or {}

        # Include template data if present
        if entity.template_data:
            data.update(entity.template_data)

        return data

    def _entity_to_content(self, entity: Entity) -> str:
        """Convert entity to markdown content for wiki"""
        parts = []

        if entity.type == "CHARACTER":
            attrs = entity.attributes or {}

            if attrs.get("appearance"):
                parts.append(f"## Appearance\n{attrs['appearance']}")

            if attrs.get("personality"):
                parts.append(f"## Personality\n{attrs['personality']}")

            if attrs.get("backstory"):
                parts.append(f"## Backstory\n{attrs['backstory']}")

            if attrs.get("motivation"):
                parts.append(f"## Motivation\n{attrs['motivation']}")

        elif entity.type == "LOCATION":
            attrs = entity.attributes or {}

            if attrs.get("description"):
                parts.append(f"## Description\n{attrs['description']}")

            if attrs.get("atmosphere"):
                parts.append(f"## Atmosphere\n{attrs['atmosphere']}")

            if attrs.get("history"):
                parts.append(f"## History\n{attrs['history']}")

        else:
            # Generic content from attributes
            attrs = entity.attributes or {}
            if attrs.get("description"):
                parts.append(attrs["description"])

        return "\n\n".join(parts) if parts else ""

    def _wiki_to_attributes(self, wiki_entry: WikiEntry) -> Dict:
        """Convert wiki structured data to entity attributes"""
        return wiki_entry.structured_data or {}
