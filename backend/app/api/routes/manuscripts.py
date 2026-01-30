"""
Manuscript CRUD API Routes
Handles manuscript creation, reading, updating, and deletion
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from app.database import get_db
from app.models.manuscript import Manuscript, Scene, SceneVariant


router = APIRouter(prefix="/api/manuscripts", tags=["manuscripts"])


# Pydantic schemas for request/response
class SceneCreate(BaseModel):
    content: str
    position: int
    beats: Optional[List[dict]] = []


class SceneResponse(BaseModel):
    id: str
    content: str
    position: int
    beats: List[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ManuscriptCreate(BaseModel):
    title: str
    lexical_state: Optional[str] = ""


class ManuscriptUpdate(BaseModel):
    title: Optional[str] = None
    lexical_state: Optional[str] = None
    word_count: Optional[int] = None
    # Story metadata
    premise: Optional[str] = None
    premise_source: Optional[str] = None  # 'ai_generated' or 'user_written'
    genre: Optional[str] = None


class ManuscriptResponse(BaseModel):
    id: str
    title: str
    lexical_state: str
    word_count: int
    # Story metadata
    premise: Optional[str] = ""
    premise_source: Optional[str] = ""
    genre: Optional[str] = ""
    created_at: datetime
    updated_at: datetime
    scenes: List[SceneResponse] = []

    class Config:
        from_attributes = True


class ManuscriptListResponse(BaseModel):
    id: str
    title: str
    word_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# CRUD Endpoints

@router.post("", response_model=ManuscriptResponse)
async def create_manuscript(
    manuscript: ManuscriptCreate,
    db: Session = Depends(get_db)
):
    """Create a new manuscript"""
    db_manuscript = Manuscript(
        id=str(uuid.uuid4()),
        title=manuscript.title,
        lexical_state=manuscript.lexical_state or "",
        word_count=0
    )
    db.add(db_manuscript)
    db.commit()
    db.refresh(db_manuscript)

    return db_manuscript


@router.get("", response_model=List[ManuscriptListResponse])
async def list_manuscripts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all manuscripts"""
    manuscripts = db.query(Manuscript).offset(skip).limit(limit).all()
    return manuscripts


@router.get("/{manuscript_id}", response_model=ManuscriptResponse)
async def get_manuscript(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific manuscript by ID"""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    return manuscript


@router.put("/{manuscript_id}", response_model=ManuscriptResponse)
async def update_manuscript(
    manuscript_id: str,
    manuscript_update: ManuscriptUpdate,
    db: Session = Depends(get_db)
):
    """Update a manuscript"""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    # Update fields if provided
    if manuscript_update.title is not None:
        manuscript.title = manuscript_update.title
    if manuscript_update.lexical_state is not None:
        manuscript.lexical_state = manuscript_update.lexical_state
    if manuscript_update.word_count is not None:
        manuscript.word_count = manuscript_update.word_count
    # Story metadata
    if manuscript_update.premise is not None:
        manuscript.premise = manuscript_update.premise
    if manuscript_update.premise_source is not None:
        manuscript.premise_source = manuscript_update.premise_source
    if manuscript_update.genre is not None:
        manuscript.genre = manuscript_update.genre

    manuscript.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(manuscript)

    return manuscript


@router.delete("/{manuscript_id}")
async def delete_manuscript(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """Delete a manuscript"""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    db.delete(manuscript)
    db.commit()

    return {
        "success": True,
        "message": f"Manuscript {manuscript_id} deleted successfully"
    }


# Scene endpoints

@router.post("/{manuscript_id}/scenes", response_model=SceneResponse)
async def create_scene(
    manuscript_id: str,
    scene: SceneCreate,
    db: Session = Depends(get_db)
):
    """Create a new scene in a manuscript"""
    # Verify manuscript exists
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    db_scene = Scene(
        id=str(uuid.uuid4()),
        manuscript_id=manuscript_id,
        content=scene.content,
        position=scene.position,
        beats=scene.beats or []
    )
    db.add(db_scene)
    db.commit()
    db.refresh(db_scene)

    return db_scene


@router.get("/{manuscript_id}/scenes", response_model=List[SceneResponse])
async def list_scenes(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """List all scenes for a manuscript"""
    # Verify manuscript exists
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    scenes = db.query(Scene).filter(
        Scene.manuscript_id == manuscript_id
    ).order_by(Scene.position).all()

    return scenes


@router.get("/{manuscript_id}/scenes/{scene_id}", response_model=SceneResponse)
async def get_scene(
    manuscript_id: str,
    scene_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific scene"""
    scene = db.query(Scene).filter(
        Scene.id == scene_id,
        Scene.manuscript_id == manuscript_id
    ).first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    return scene


@router.put("/{manuscript_id}/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(
    manuscript_id: str,
    scene_id: str,
    scene_update: SceneCreate,
    db: Session = Depends(get_db)
):
    """Update a scene"""
    scene = db.query(Scene).filter(
        Scene.id == scene_id,
        Scene.manuscript_id == manuscript_id
    ).first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    scene.content = scene_update.content
    scene.position = scene_update.position
    scene.beats = scene_update.beats or []
    scene.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(scene)

    return scene


@router.delete("/{manuscript_id}/scenes/{scene_id}")
async def delete_scene(
    manuscript_id: str,
    scene_id: str,
    db: Session = Depends(get_db)
):
    """Delete a scene"""
    scene = db.query(Scene).filter(
        Scene.id == scene_id,
        Scene.manuscript_id == manuscript_id
    ).first()

    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    db.delete(scene)
    db.commit()

    return {
        "success": True,
        "message": f"Scene {scene_id} deleted successfully"
    }
