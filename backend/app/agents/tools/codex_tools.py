"""
Codex Tools for Maxwell Agents

Tools for querying entities and relationships from the Codex.
Supports all entity scopes: MANUSCRIPT, SERIES, WORLD.
"""

from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool

from app.database import SessionLocal
from app.models.entity import Entity, Relationship, ENTITY_SCOPE_MANUSCRIPT, ENTITY_SCOPE_SERIES, ENTITY_SCOPE_WORLD
from app.models.world import World, Series
from app.models.manuscript import Manuscript


class QueryEntitiesInput(BaseModel):
    """Input for querying entities"""
    manuscript_id: str = Field(description="The manuscript ID to query entities for")
    entity_type: Optional[str] = Field(
        default=None,
        description="Optional type filter: CHARACTER, LOCATION, ITEM, or LORE"
    )
    include_world_entities: bool = Field(
        default=True,
        description="Whether to include world-scoped entities"
    )
    include_series_entities: bool = Field(
        default=True,
        description="Whether to include series-scoped entities"
    )


class QueryEntities(BaseTool):
    """Query entities from the Codex"""

    name: str = "query_entities"
    description: str = """Query entities (characters, locations, items, lore) from the Codex.
    Returns entity names, types, and key attributes.
    Use this to understand what characters and world elements exist."""
    args_schema: Type[BaseModel] = QueryEntitiesInput

    def _run(
        self,
        manuscript_id: str,
        entity_type: Optional[str] = None,
        include_world_entities: bool = True,
        include_series_entities: bool = True
    ) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Get manuscript to find series/world
            manuscript = db.query(Manuscript).filter(
                Manuscript.id == manuscript_id
            ).first()

            results = []

            # Query manuscript-scoped entities
            query = db.query(Entity).filter(
                Entity.manuscript_id == manuscript_id
            )
            if entity_type:
                query = query.filter(Entity.type == entity_type)
            entities = query.all()
            results.extend(entities)

            # Query series-scoped entities
            if include_series_entities and manuscript and manuscript.series_id:
                series = db.query(Series).filter(
                    Series.id == manuscript.series_id
                ).first()
                if series:
                    query = db.query(Entity).filter(
                        Entity.world_id == series.world_id,
                        Entity.scope == ENTITY_SCOPE_SERIES
                    )
                    if entity_type:
                        query = query.filter(Entity.type == entity_type)
                    results.extend(query.all())

            # Query world-scoped entities
            if include_world_entities and manuscript and manuscript.series_id:
                series = db.query(Series).filter(
                    Series.id == manuscript.series_id
                ).first()
                if series:
                    query = db.query(Entity).filter(
                        Entity.world_id == series.world_id,
                        Entity.scope == ENTITY_SCOPE_WORLD
                    )
                    if entity_type:
                        query = query.filter(Entity.type == entity_type)
                    results.extend(query.all())

            # Format results
            if not results:
                return f"No entities found for manuscript {manuscript_id}"

            output_lines = [f"Found {len(results)} entities:"]
            for entity in results:
                scope_badge = f"[{entity.scope}]" if entity.scope != ENTITY_SCOPE_MANUSCRIPT else ""
                aliases_str = f" (aka: {', '.join(entity.aliases)})" if entity.aliases else ""
                output_lines.append(
                    f"- {entity.name}{aliases_str} [{entity.type}] {scope_badge}"
                )
                # Add key attributes if available
                if entity.attributes:
                    for key in ["description", "role", "age"]:
                        if key in entity.attributes:
                            val = str(entity.attributes[key])[:100]
                            output_lines.append(f"  {key}: {val}")

            return "\n".join(output_lines)

        finally:
            db.close()


class QueryCharacterProfileInput(BaseModel):
    """Input for querying a character profile"""
    manuscript_id: str = Field(description="The manuscript ID")
    character_name: str = Field(description="The character name to look up")


class QueryCharacterProfile(BaseTool):
    """Query detailed character profile"""

    name: str = "query_character_profile"
    description: str = """Get detailed profile for a specific character.
    Returns physical description, personality, backstory, motivations, and relationships.
    Use this when you need deep information about a character."""
    args_schema: Type[BaseModel] = QueryCharacterProfileInput

    def _run(self, manuscript_id: str, character_name: str) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Search for character by name or alias
            name_lower = character_name.lower()

            entities = db.query(Entity).filter(
                Entity.manuscript_id == manuscript_id,
                Entity.type == "CHARACTER"
            ).all()

            # Find matching character
            character = None
            for entity in entities:
                if entity.name.lower() == name_lower:
                    character = entity
                    break
                if any(alias.lower() == name_lower for alias in (entity.aliases or [])):
                    character = entity
                    break

            if not character:
                return f"Character '{character_name}' not found"

            # Build detailed profile
            lines = [f"## {character.name}"]

            if character.aliases:
                lines.append(f"Aliases: {', '.join(character.aliases)}")

            # Template data (structured)
            if character.template_data:
                td = character.template_data

                if td.get("role"):
                    lines.append(f"\n### Role: {td['role']}")

                if td.get("physical"):
                    lines.append("\n### Physical Description")
                    for key, val in td["physical"].items():
                        if val:
                            lines.append(f"- {key}: {val}")

                if td.get("personality"):
                    lines.append("\n### Personality")
                    for key, val in td["personality"].items():
                        if val:
                            if isinstance(val, list):
                                lines.append(f"- {key}: {', '.join(val)}")
                            else:
                                lines.append(f"- {key}: {val}")

                if td.get("backstory"):
                    lines.append("\n### Backstory")
                    for key, val in td["backstory"].items():
                        if val:
                            lines.append(f"- {key}: {val}")

                if td.get("motivation"):
                    lines.append("\n### Motivation")
                    for key, val in td["motivation"].items():
                        if val:
                            lines.append(f"- {key}: {val}")

            # Legacy attributes
            elif character.attributes:
                attrs = character.attributes

                if attrs.get("description"):
                    lines.append(f"\n### Description\n{attrs['description']}")

                if attrs.get("appearance"):
                    lines.append("\n### Appearance")
                    if isinstance(attrs["appearance"], list):
                        for item in attrs["appearance"]:
                            lines.append(f"- {item}")
                    else:
                        lines.append(attrs["appearance"])

                if attrs.get("personality"):
                    lines.append("\n### Personality")
                    if isinstance(attrs["personality"], list):
                        for item in attrs["personality"]:
                            lines.append(f"- {item}")
                    else:
                        lines.append(attrs["personality"])

            # Get relationships
            relationships = db.query(Relationship).filter(
                (Relationship.source_entity_id == character.id) |
                (Relationship.target_entity_id == character.id)
            ).all()

            if relationships:
                lines.append("\n### Relationships")
                for rel in relationships:
                    if rel.source_entity_id == character.id:
                        other_id = rel.target_entity_id
                        direction = "→"
                    else:
                        other_id = rel.source_entity_id
                        direction = "←"

                    other = db.query(Entity).filter(Entity.id == other_id).first()
                    if other:
                        lines.append(
                            f"- {direction} {other.name}: {rel.relationship_type}"
                        )

            return "\n".join(lines)

        finally:
            db.close()


class QueryRelationshipsInput(BaseModel):
    """Input for querying relationships"""
    manuscript_id: str = Field(description="The manuscript ID")
    entity_name: Optional[str] = Field(
        default=None,
        description="Optional: filter to relationships involving this entity"
    )


class QueryRelationships(BaseTool):
    """Query relationships between entities"""

    name: str = "query_relationships"
    description: str = """Query relationships between entities in the manuscript.
    Returns relationship types (ROMANTIC, CONFLICT, ALLIANCE, FAMILY, etc.) and context.
    Use this to understand character dynamics and connections."""
    args_schema: Type[BaseModel] = QueryRelationshipsInput

    def _run(
        self,
        manuscript_id: str,
        entity_name: Optional[str] = None
    ) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Get entities for this manuscript
            entities = db.query(Entity).filter(
                Entity.manuscript_id == manuscript_id
            ).all()

            entity_ids = {e.id for e in entities}
            entity_names = {e.id: e.name for e in entities}

            # Build query
            query = db.query(Relationship).filter(
                Relationship.source_entity_id.in_(entity_ids)
            )

            # Filter by entity name if provided
            if entity_name:
                target_entity = next(
                    (e for e in entities if e.name.lower() == entity_name.lower()),
                    None
                )
                if not target_entity:
                    return f"Entity '{entity_name}' not found"

                query = query.filter(
                    (Relationship.source_entity_id == target_entity.id) |
                    (Relationship.target_entity_id == target_entity.id)
                )

            relationships = query.all()

            if not relationships:
                return "No relationships found"

            lines = [f"Found {len(relationships)} relationships:"]
            for rel in relationships:
                source_name = entity_names.get(rel.source_entity_id, "Unknown")
                target_name = entity_names.get(rel.target_entity_id, "Unknown")
                lines.append(
                    f"- {source_name} → {target_name}: {rel.relationship_type} "
                    f"(strength: {rel.strength})"
                )

            return "\n".join(lines)

        finally:
            db.close()


class SearchEntitiesInput(BaseModel):
    """Input for searching entities"""
    manuscript_id: str = Field(description="The manuscript ID")
    query: str = Field(description="Search query (name, alias, or attribute)")


class SearchEntities(BaseTool):
    """Search entities by name, alias, or attributes"""

    name: str = "search_entities"
    description: str = """Search for entities by name, alias, or attribute content.
    Use this when you need to find an entity but don't know the exact name."""
    args_schema: Type[BaseModel] = SearchEntitiesInput

    def _run(self, manuscript_id: str, query: str) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            query_lower = query.lower()

            entities = db.query(Entity).filter(
                Entity.manuscript_id == manuscript_id
            ).all()

            matches = []
            for entity in entities:
                # Check name
                if query_lower in entity.name.lower():
                    matches.append((entity, "name match"))
                    continue

                # Check aliases
                if any(query_lower in alias.lower() for alias in (entity.aliases or [])):
                    matches.append((entity, "alias match"))
                    continue

                # Check attributes
                if entity.attributes:
                    attr_str = str(entity.attributes).lower()
                    if query_lower in attr_str:
                        matches.append((entity, "attribute match"))

            if not matches:
                return f"No entities matching '{query}' found"

            lines = [f"Found {len(matches)} matches for '{query}':"]
            for entity, match_type in matches:
                lines.append(f"- {entity.name} [{entity.type}] ({match_type})")

            return "\n".join(lines)

        finally:
            db.close()


# Create tool instances
query_entities = QueryEntities()
query_character_profile = QueryCharacterProfile()
query_relationships = QueryRelationships()
search_entities = SearchEntities()
