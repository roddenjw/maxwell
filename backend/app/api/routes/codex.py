"""
Codex API routes for entity and relationship management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.codex_service import codex_service
from app.services.nlp_service import nlp_service


router = APIRouter(prefix="/api/codex", tags=["codex"])


# Request/Response Models

class CreateEntityRequest(BaseModel):
    manuscript_id: str
    type: str  # CHARACTER, LOCATION, ITEM, LORE
    name: str
    aliases: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None


class UpdateEntityRequest(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    aliases: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None


class AddAppearanceRequest(BaseModel):
    entity_id: str
    scene_id: Optional[str] = None
    description: str


class CreateRelationshipRequest(BaseModel):
    source_entity_id: str
    target_entity_id: str
    relationship_type: str  # ROMANTIC, CONFLICT, ALLIANCE, FAMILY, PROFESSIONAL, ACQUAINTANCE
    strength: Optional[int] = 1
    context: Optional[List[Dict[str, Any]]] = None


class ApproveSuggestionRequest(BaseModel):
    suggestion_id: str
    aliases: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None


class RejectSuggestionRequest(BaseModel):
    suggestion_id: str


class AnalyzeTextRequest(BaseModel):
    manuscript_id: str
    text: str


# Entity Endpoints

@router.post("/entities")
async def create_entity(request: CreateEntityRequest):
    """Create a new entity"""
    try:
        entity = codex_service.create_entity(
            manuscript_id=request.manuscript_id,
            entity_type=request.type,
            name=request.name,
            aliases=request.aliases,
            attributes=request.attributes
        )

        return {
            "success": True,
            "data": {
                "id": entity.id,
                "manuscript_id": entity.manuscript_id,
                "type": entity.type,
                "name": entity.name,
                "aliases": entity.aliases,
                "attributes": entity.attributes,
                "appearance_history": entity.appearance_history,
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{manuscript_id}")
async def list_entities(manuscript_id: str, type: Optional[str] = None):
    """List entities for a manuscript"""
    try:
        entities = codex_service.get_entities(manuscript_id, entity_type=type)

        return {
            "success": True,
            "data": [
                {
                    "id": entity.id,
                    "manuscript_id": entity.manuscript_id,
                    "type": entity.type,
                    "name": entity.name,
                    "aliases": entity.aliases,
                    "attributes": entity.attributes,
                    "appearance_history": entity.appearance_history,
                    "created_at": entity.created_at.isoformat(),
                    "updated_at": entity.updated_at.isoformat()
                }
                for entity in entities
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/entities/{entity_id}")
async def update_entity(entity_id: str, request: UpdateEntityRequest):
    """Update entity"""
    try:
        entity = codex_service.update_entity(
            entity_id=entity_id,
            name=request.name,
            entity_type=request.type,
            aliases=request.aliases,
            attributes=request.attributes
        )

        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

        return {
            "success": True,
            "data": {
                "id": entity.id,
                "manuscript_id": entity.manuscript_id,
                "type": entity.type,
                "name": entity.name,
                "aliases": entity.aliases,
                "attributes": entity.attributes,
                "appearance_history": entity.appearance_history,
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/entities/{entity_id}")
async def delete_entity(entity_id: str):
    """Delete entity"""
    try:
        success = codex_service.delete_entity(entity_id)

        if not success:
            raise HTTPException(status_code=404, detail="Entity not found")

        return {
            "success": True,
            "message": "Entity deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entities/appearance")
async def add_appearance(request: AddAppearanceRequest):
    """Add appearance record to entity"""
    try:
        entity = codex_service.add_appearance(
            entity_id=request.entity_id,
            scene_id=request.scene_id,
            description=request.description
        )

        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

        return {
            "success": True,
            "data": {
                "id": entity.id,
                "appearance_history": entity.appearance_history
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Relationship Endpoints

@router.post("/relationships")
async def create_relationship(request: CreateRelationshipRequest):
    """Create relationship between entities"""
    try:
        relationship = codex_service.create_relationship(
            source_entity_id=request.source_entity_id,
            target_entity_id=request.target_entity_id,
            relationship_type=request.relationship_type,
            strength=request.strength or 1,
            context=request.context
        )

        return {
            "success": True,
            "data": {
                "id": relationship.id,
                "source_entity_id": relationship.source_entity_id,
                "target_entity_id": relationship.target_entity_id,
                "relationship_type": relationship.relationship_type,
                "strength": relationship.strength,
                "context": relationship.context,
                "created_at": relationship.created_at.isoformat(),
                "updated_at": relationship.updated_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relationships/{manuscript_id}")
async def list_relationships(manuscript_id: str, entity_id: Optional[str] = None):
    """List relationships for a manuscript"""
    try:
        relationships = codex_service.get_relationships(manuscript_id, entity_id)

        return {
            "success": True,
            "data": [
                {
                    "id": rel.id,
                    "source_entity_id": rel.source_entity_id,
                    "target_entity_id": rel.target_entity_id,
                    "relationship_type": rel.relationship_type,
                    "strength": rel.strength,
                    "context": rel.context,
                    "created_at": rel.created_at.isoformat(),
                    "updated_at": rel.updated_at.isoformat()
                }
                for rel in relationships
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/relationships/{relationship_id}")
async def delete_relationship(relationship_id: str):
    """Delete relationship"""
    try:
        success = codex_service.delete_relationship(relationship_id)

        if not success:
            raise HTTPException(status_code=404, detail="Relationship not found")

        return {
            "success": True,
            "message": "Relationship deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Suggestion Endpoints

@router.get("/suggestions/{manuscript_id}")
async def list_suggestions(manuscript_id: str, status: Optional[str] = None):
    """List entity suggestions"""
    try:
        suggestions = codex_service.get_suggestions(manuscript_id, status)

        return {
            "success": True,
            "data": [
                {
                    "id": suggestion.id,
                    "manuscript_id": suggestion.manuscript_id,
                    "name": suggestion.name,
                    "type": suggestion.type,
                    "context": suggestion.context,
                    "status": suggestion.status,
                    "created_at": suggestion.created_at.isoformat()
                }
                for suggestion in suggestions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/approve")
async def approve_suggestion(request: ApproveSuggestionRequest):
    """Approve suggestion and create entity"""
    try:
        entity = codex_service.approve_suggestion(
            suggestion_id=request.suggestion_id,
            aliases=request.aliases,
            attributes=request.attributes
        )

        return {
            "success": True,
            "data": {
                "id": entity.id,
                "manuscript_id": entity.manuscript_id,
                "type": entity.type,
                "name": entity.name,
                "aliases": entity.aliases,
                "attributes": entity.attributes,
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/reject")
async def reject_suggestion(request: RejectSuggestionRequest):
    """Reject suggestion"""
    try:
        success = codex_service.reject_suggestion(request.suggestion_id)

        if not success:
            raise HTTPException(status_code=404, detail="Suggestion not found")

        return {
            "success": True,
            "message": "Suggestion rejected"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analysis Endpoints

@router.post("/analyze")
async def analyze_text(request: AnalyzeTextRequest, background_tasks: BackgroundTasks):
    """
    Analyze text for entities and relationships using NLP

    This endpoint triggers background processing and returns immediately.
    Results are stored as suggestions that can be approved/rejected.
    """
    try:
        # Check if NLP is available
        if not nlp_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="NLP service not available. Install spaCy and download en_core_web_lg model."
            )

        # Add analysis task to background
        background_tasks.add_task(
            _process_analysis,
            manuscript_id=request.manuscript_id,
            text=request.text
        )

        return {
            "success": True,
            "message": "Analysis started. Results will appear in suggestions.",
            "manuscript_id": request.manuscript_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _process_analysis(manuscript_id: str, text: str):
    """
    Background task to process NLP analysis

    Args:
        manuscript_id: Manuscript ID
        text: Text to analyze
    """
    try:
        # Get existing entities
        existing_entities = codex_service.get_entities(manuscript_id)
        existing_dicts = [
            {
                "name": entity.name,
                "type": entity.type,
                "aliases": entity.aliases
            }
            for entity in existing_entities
        ]

        # Get previously rejected suggestions to avoid re-suggesting
        rejected_suggestions = codex_service.get_suggestions(manuscript_id, status="REJECTED")
        rejected_names = {sug.name.lower() for sug in rejected_suggestions}

        # Analyze text
        results = nlp_service.analyze_manuscript(text, manuscript_id, existing_dicts)

        # Create suggestions for detected entities
        for entity in results["entities"]:
            # Skip if this name was previously rejected
            if entity["name"].lower() in rejected_names:
                print(f"Skipping previously rejected entity: {entity['name']}")
                continue
            try:
                codex_service.create_suggestion(
                    manuscript_id=manuscript_id,
                    name=entity["name"],
                    entity_type=entity["type"],
                    context=entity["context"]
                )
            except Exception as e:
                # Skip duplicate suggestions
                print(f"Skipping suggestion for {entity['name']}: {e}")
                continue

        # Create relationships for known entities
        # Build entity name -> id mapping (include aliases)
        entity_id_map = {}
        for entity in existing_entities:
            entity_id_map[entity.name.lower()] = entity.id
            for alias in entity.aliases:
                entity_id_map[alias.lower()] = entity.id

        # Get existing relationships to avoid duplicates
        existing_relationships = codex_service.get_relationships(manuscript_id)
        existing_rel_set = set()
        for rel in existing_relationships:
            # Store both directions to handle bidirectional relationships
            existing_rel_set.add((rel.source_entity_id, rel.target_entity_id, rel.relationship_type))
            existing_rel_set.add((rel.target_entity_id, rel.source_entity_id, rel.relationship_type))

        # Create new relationships
        for rel in results["relationships"]:
            source_id = entity_id_map.get(rel["source_name"].lower())
            target_id = entity_id_map.get(rel["target_name"].lower())

            if source_id and target_id and source_id != target_id:
                # Check if relationship already exists
                rel_key = (source_id, target_id, rel["type"])
                if rel_key not in existing_rel_set:
                    try:
                        codex_service.create_relationship(
                            source_entity_id=source_id,
                            target_entity_id=target_id,
                            relationship_type=rel["type"],
                            strength=rel["strength"],
                            context=[{"description": rel["context"]}]
                        )
                        # Add to set to avoid duplicates within this analysis
                        existing_rel_set.add(rel_key)
                        existing_rel_set.add((target_id, source_id, rel["type"]))
                    except Exception as e:
                        # Skip duplicate relationships
                        print(f"Skipping relationship {rel['source_name']} -> {rel['target_name']}: {e}")
                        continue

        # Update entity attributes with extracted descriptions
        descriptions = results.get("descriptions", {})
        if descriptions:
            for entity_name, desc_data in descriptions.items():
                # Find the entity
                entity = next((e for e in existing_entities if e.name == entity_name), None)
                if not entity:
                    continue

                # Merge descriptions with existing attributes
                current_attrs = entity.attributes or {}

                # Append new information to existing data
                for category, items in desc_data.items():
                    if category not in current_attrs:
                        current_attrs[category] = []

                    # Add new items that aren't already present
                    existing_items = set(current_attrs[category]) if isinstance(current_attrs[category], list) else set()
                    for item in items:
                        if item not in existing_items:
                            if not isinstance(current_attrs[category], list):
                                current_attrs[category] = []
                            current_attrs[category].append(item)
                            existing_items.add(item)

                # Update entity with merged attributes
                try:
                    codex_service.update_entity(
                        entity_id=entity.id,
                        attributes=current_attrs
                    )
                    print(f"Updated descriptions for {entity_name}")
                except Exception as e:
                    print(f"Failed to update descriptions for {entity_name}: {e}")

    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Analysis error: {e}")


@router.get("/nlp/status")
async def nlp_status():
    """Check if NLP service is available"""
    return {
        "success": True,
        "data": {
            "available": nlp_service.is_available(),
            "model": "en_core_web_lg" if nlp_service.is_available() else None
        }
    }


@router.get("/export/{manuscript_id}")
async def export_codex(manuscript_id: str, format: str = "markdown"):
    """
    Export Codex data as Markdown or JSON

    Args:
        manuscript_id: Manuscript ID
        format: Export format (markdown or json)

    Returns:
        Exported data
    """
    try:
        # Get all entities and relationships
        entities = codex_service.get_entities(manuscript_id)
        relationships = codex_service.get_relationships(manuscript_id)

        if format == "json":
            # Return as JSON
            return {
                "success": True,
                "data": {
                    "entities": [
                        {
                            "id": entity.id,
                            "type": entity.type,
                            "name": entity.name,
                            "aliases": entity.aliases,
                            "attributes": entity.attributes,
                            "created_at": entity.created_at.isoformat()
                        }
                        for entity in entities
                    ],
                    "relationships": [
                        {
                            "source_entity_id": rel.source_entity_id,
                            "target_entity_id": rel.target_entity_id,
                            "relationship_type": rel.relationship_type,
                            "strength": rel.strength,
                            "context": rel.context
                        }
                        for rel in relationships
                    ],
                    "stats": {
                        "total_entities": len(entities),
                        "total_relationships": len(relationships),
                        "entity_breakdown": _count_by_type(entities)
                    }
                }
            }
        else:
            # Generate Markdown
            markdown = _generate_markdown_export(entities, relationships, manuscript_id)

            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(
                content=markdown,
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename=codex-{manuscript_id}.md"
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _count_by_type(entities):
    """Count entities by type"""
    from collections import defaultdict
    counts = defaultdict(int)
    for entity in entities:
        counts[entity.type] += 1
    return dict(counts)


def _generate_markdown_export(entities, relationships, manuscript_id: str) -> str:
    """Generate Markdown export of Codex data"""
    from datetime import datetime

    md = f"# The Codex - {manuscript_id}\n\n"
    md += f"*Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*\n\n"
    md += "---\n\n"

    # Statistics
    md += "## 📊 Statistics\n\n"
    md += f"- **Total Entities**: {len(entities)}\n"
    md += f"- **Total Relationships**: {len(relationships)}\n\n"

    # Breakdown by type
    type_counts = _count_by_type(entities)
    if type_counts:
        md += "### By Type\n\n"
        for entity_type, count in sorted(type_counts.items()):
            md += f"- **{entity_type}**: {count}\n"
        md += "\n"

    md += "---\n\n"

    # Entities grouped by type
    for entity_type in ["CHARACTER", "LOCATION", "ITEM", "LORE"]:
        typed_entities = [e for e in entities if e.type == entity_type]
        if not typed_entities:
            continue

        icon = {"CHARACTER": "👤", "LOCATION": "📍", "ITEM": "🔷", "LORE": "📚"}.get(entity_type, "")
        md += f"## {icon} {entity_type}S\n\n"

        for entity in sorted(typed_entities, key=lambda e: e.name):
            md += f"### {entity.name}\n\n"

            if entity.aliases:
                md += f"**Aliases**: {', '.join(entity.aliases)}\n\n"

            # Attributes
            if entity.attributes:
                if entity.attributes.get("appearance"):
                    md += "#### 👁️ Appearance\n\n"
                    for item in entity.attributes["appearance"]:
                        md += f"- {item}\n"
                    md += "\n"

                if entity.attributes.get("personality"):
                    md += "#### 💭 Personality\n\n"
                    for item in entity.attributes["personality"]:
                        md += f"- {item}\n"
                    md += "\n"

                if entity.attributes.get("background"):
                    md += "#### 📜 Background\n\n"
                    for item in entity.attributes["background"]:
                        md += f"- {item}\n"
                    md += "\n"

                if entity.attributes.get("actions"):
                    md += "#### ⚡ Actions\n\n"
                    for item in entity.attributes["actions"]:
                        md += f"- {item}\n"
                    md += "\n"

                if entity.attributes.get("description"):
                    md += "#### 📝 Description\n\n"
                    md += f"{entity.attributes['description']}\n\n"

                if entity.attributes.get("notes"):
                    md += "#### 📌 Notes\n\n"
                    md += f"{entity.attributes['notes']}\n\n"

            md += "---\n\n"

    # Relationships
    if relationships:
        md += "## 🔗 Relationships\n\n"

        # Build entity lookup
        entity_lookup = {e.id: e.name for e in entities}

        for rel in relationships:
            source_name = entity_lookup.get(rel.source_entity_id, "Unknown")
            target_name = entity_lookup.get(rel.target_entity_id, "Unknown")

            md += f"- **{source_name}** → **{target_name}** ({rel.relationship_type})\n"

            if rel.context:
                for ctx in rel.context[:2]:  # Show first 2 contexts
                    if isinstance(ctx, dict) and "description" in ctx:
                        md += f"  - _{ctx['description']}_\n"

        md += "\n"

    md += "---\n\n"
    md += "*Generated with Maxwell - The Codex IDE*\n"

    return md
