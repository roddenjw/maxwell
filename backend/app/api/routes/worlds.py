"""
World and Series API Routes
Handles world/series CRUD and manuscript organization
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.services.world_service import world_service
from app.models import World, Series, Manuscript, Entity


router = APIRouter(prefix="/api/worlds", tags=["worlds"])


# ========================
# Pydantic Schemas
# ========================

class WorldCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    settings: Optional[dict] = None


class WorldUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = None


class WorldResponse(BaseModel):
    id: str
    name: str
    description: str
    settings: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SeriesCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    order_index: Optional[int] = 0


class SeriesUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None


class SeriesResponse(BaseModel):
    id: str
    world_id: str
    name: str
    description: str
    order_index: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ManuscriptBriefResponse(BaseModel):
    id: str
    title: str
    author: str
    description: str
    word_count: int
    order_index: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssignManuscriptRequest(BaseModel):
    manuscript_id: str
    order_index: Optional[int] = None


class WorldEntityCreate(BaseModel):
    type: str  # CHARACTER, LOCATION, ITEM, LORE
    name: str
    aliases: Optional[List[str]] = []
    attributes: Optional[dict] = {}


class EntityResponse(BaseModel):
    id: str
    world_id: Optional[str]
    manuscript_id: Optional[str]
    scope: str
    type: str
    name: str
    aliases: List[str]
    attributes: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChangeScopeRequest(BaseModel):
    new_scope: str  # MANUSCRIPT, WORLD
    world_id: Optional[str] = None


class CopyEntityRequest(BaseModel):
    manuscript_id: str


# ========================
# World Endpoints
# ========================

@router.post("", response_model=WorldResponse)
async def create_world(
    world_data: WorldCreate,
    db: Session = Depends(get_db)
):
    """Create a new world"""
    world = world_service.create_world(
        db=db,
        name=world_data.name,
        description=world_data.description,
        settings=world_data.settings
    )
    return world


@router.get("", response_model=List[WorldResponse])
async def list_worlds(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all worlds"""
    return world_service.list_worlds(db, skip=skip, limit=limit)


@router.get("/{world_id}", response_model=WorldResponse)
async def get_world(
    world_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific world"""
    world = world_service.get_world(db, world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world


@router.put("/{world_id}", response_model=WorldResponse)
async def update_world(
    world_id: str,
    world_data: WorldUpdate,
    db: Session = Depends(get_db)
):
    """Update a world"""
    world = world_service.update_world(
        db=db,
        world_id=world_id,
        name=world_data.name,
        description=world_data.description,
        settings=world_data.settings
    )
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world


@router.delete("/{world_id}")
async def delete_world(
    world_id: str,
    db: Session = Depends(get_db)
):
    """Delete a world and all its series/manuscripts/entities"""
    success = world_service.delete_world(db, world_id)
    if not success:
        raise HTTPException(status_code=404, detail="World not found")
    return {"success": True, "message": f"World {world_id} deleted successfully"}


# ========================
# Series Endpoints
# ========================

@router.post("/{world_id}/series", response_model=SeriesResponse)
async def create_series(
    world_id: str,
    series_data: SeriesCreate,
    db: Session = Depends(get_db)
):
    """Create a new series in a world"""
    series = world_service.create_series(
        db=db,
        world_id=world_id,
        name=series_data.name,
        description=series_data.description,
        order_index=series_data.order_index
    )
    if not series:
        raise HTTPException(status_code=404, detail="World not found")
    return series


@router.get("/{world_id}/series", response_model=List[SeriesResponse])
async def list_series(
    world_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all series in a world"""
    # Verify world exists
    world = world_service.get_world(db, world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    return world_service.list_series_in_world(db, world_id, skip=skip, limit=limit)


# ========================
# Series Management (by series ID)
# ========================

@router.get("/series/{series_id}", response_model=SeriesResponse)
async def get_series(
    series_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific series"""
    series = world_service.get_series(db, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@router.put("/series/{series_id}", response_model=SeriesResponse)
async def update_series(
    series_id: str,
    series_data: SeriesUpdate,
    db: Session = Depends(get_db)
):
    """Update a series"""
    series = world_service.update_series(
        db=db,
        series_id=series_id,
        name=series_data.name,
        description=series_data.description,
        order_index=series_data.order_index
    )
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@router.delete("/series/{series_id}")
async def delete_series(
    series_id: str,
    db: Session = Depends(get_db)
):
    """Delete a series (manuscripts become orphaned)"""
    success = world_service.delete_series(db, series_id)
    if not success:
        raise HTTPException(status_code=404, detail="Series not found")
    return {"success": True, "message": f"Series {series_id} deleted successfully"}


# ========================
# Manuscript Assignment Endpoints
# ========================

@router.get("/series/{series_id}/manuscripts", response_model=List[ManuscriptBriefResponse])
async def list_series_manuscripts(
    series_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all manuscripts in a series"""
    series = world_service.get_series(db, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    return world_service.list_manuscripts_in_series(db, series_id, skip=skip, limit=limit)


@router.post("/series/{series_id}/manuscripts", response_model=ManuscriptBriefResponse)
async def assign_manuscript_to_series(
    series_id: str,
    request: AssignManuscriptRequest,
    db: Session = Depends(get_db)
):
    """Assign a manuscript to a series"""
    manuscript = world_service.assign_manuscript_to_series(
        db=db,
        manuscript_id=request.manuscript_id,
        series_id=series_id,
        order_index=request.order_index
    )
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript or series not found")
    return manuscript


@router.delete("/series/{series_id}/manuscripts/{manuscript_id}")
async def remove_manuscript_from_series(
    series_id: str,
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """Remove a manuscript from a series (make standalone)"""
    manuscript = world_service.remove_manuscript_from_series(db, manuscript_id)
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")
    return {"success": True, "message": f"Manuscript removed from series"}


@router.get("/{world_id}/manuscripts", response_model=List[ManuscriptBriefResponse])
async def list_world_manuscripts(
    world_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all manuscripts in a world (across all series)"""
    world = world_service.get_world(db, world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    return world_service.list_manuscripts_in_world(db, world_id, skip=skip, limit=limit)


# ========================
# World Entity Endpoints
# ========================

@router.post("/{world_id}/entities", response_model=EntityResponse)
async def create_world_entity(
    world_id: str,
    entity_data: WorldEntityCreate,
    db: Session = Depends(get_db)
):
    """Create a world-scoped entity (shared across all manuscripts)"""
    entity = world_service.create_world_entity(
        db=db,
        world_id=world_id,
        entity_type=entity_data.type,
        name=entity_data.name,
        aliases=entity_data.aliases,
        attributes=entity_data.attributes
    )
    if not entity:
        raise HTTPException(status_code=404, detail="World not found")
    return entity


@router.get("/{world_id}/entities", response_model=List[EntityResponse])
async def list_world_entities(
    world_id: str,
    type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all world-scoped entities"""
    world = world_service.get_world(db, world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    return world_service.list_world_entities(
        db, world_id, entity_type=type, skip=skip, limit=limit
    )


@router.put("/entities/{entity_id}/scope", response_model=EntityResponse)
async def change_entity_scope(
    entity_id: str,
    request: ChangeScopeRequest,
    db: Session = Depends(get_db)
):
    """Change an entity's scope (MANUSCRIPT or WORLD)"""
    entity = world_service.change_entity_scope(
        db=db,
        entity_id=entity_id,
        new_scope=request.new_scope,
        world_id=request.world_id
    )
    if not entity:
        raise HTTPException(
            status_code=400,
            detail="Entity not found or invalid scope change (world_id required for WORLD scope)"
        )
    return entity


@router.post("/entities/{entity_id}/copy", response_model=EntityResponse)
async def copy_entity_to_manuscript(
    entity_id: str,
    request: CopyEntityRequest,
    db: Session = Depends(get_db)
):
    """Copy a world entity to a manuscript as a local entity"""
    entity = world_service.copy_entity_to_manuscript(
        db=db,
        entity_id=entity_id,
        manuscript_id=request.manuscript_id
    )
    if not entity:
        raise HTTPException(status_code=404, detail="Entity or manuscript not found")
    return entity
