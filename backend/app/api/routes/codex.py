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

        # Analyze text
        results = nlp_service.analyze_manuscript(text, manuscript_id, existing_dicts)

        # Create suggestions for detected entities
        for entity in results["entities"]:
            codex_service.create_suggestion(
                manuscript_id=manuscript_id,
                name=entity["name"],
                entity_type=entity["type"],
                context=entity["context"]
            )

        # Create relationships for known entities
        # Build entity name -> id mapping
        entity_id_map = {entity.name: entity.id for entity in existing_entities}

        for rel in results["relationships"]:
            source_id = entity_id_map.get(rel["source_name"])
            target_id = entity_id_map.get(rel["target_name"])

            if source_id and target_id:
                codex_service.create_relationship(
                    source_entity_id=source_id,
                    target_entity_id=target_id,
                    relationship_type=rel["type"],
                    strength=rel["strength"],
                    context=[{"description": rel["context"]}]
                )

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
