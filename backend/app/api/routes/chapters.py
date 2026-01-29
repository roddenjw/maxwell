"""
Chapter CRUD API Routes
Handles hierarchical chapter/folder structure (Scrivener-like navigation)
"""

import uuid
from datetime import datetime
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.manuscript import (
    Chapter,
    DOCUMENT_TYPE_CHAPTER,
    DOCUMENT_TYPE_FOLDER,
    DOCUMENT_TYPE_CHARACTER_SHEET,
    DOCUMENT_TYPE_NOTES,
    DOCUMENT_TYPE_TITLE_PAGE,
)
from app.models.entity import Entity
from app.models.outline import PlotBeat
from app.services.manuscript_aggregation_service import manuscript_aggregation_service
from app.services.scene_detection_service import scene_detection_service
from app.services.lexical_utils import extract_text_from_lexical


# Type alias for document types
DocumentType = Literal["CHAPTER", "FOLDER", "CHARACTER_SHEET", "NOTES", "TITLE_PAGE"]


router = APIRouter(prefix="/api/chapters", tags=["chapters"])


# Pydantic schemas for request/response

class ChapterCreate(BaseModel):
    manuscript_id: str
    title: str
    is_folder: bool = False
    parent_id: Optional[str] = None
    order_index: int = 0
    lexical_state: Optional[str] = ""
    content: Optional[str] = ""
    document_type: Optional[DocumentType] = None
    linked_entity_id: Optional[str] = None
    document_metadata: Optional[dict] = None


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    is_folder: Optional[bool] = None
    parent_id: Optional[str] = None
    order_index: Optional[int] = None
    lexical_state: Optional[str] = None
    content: Optional[str] = None
    word_count: Optional[int] = None
    document_type: Optional[DocumentType] = None
    linked_entity_id: Optional[str] = None
    document_metadata: Optional[dict] = None


class ChapterResponse(BaseModel):
    id: str
    manuscript_id: str
    parent_id: Optional[str]
    title: str
    is_folder: bool
    order_index: int
    lexical_state: str
    content: str
    word_count: int
    document_type: str
    linked_entity_id: Optional[str]
    document_metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime
    children: List['ChapterResponse'] = []

    class Config:
        from_attributes = True


# Allow forward reference for recursive model
ChapterResponse.model_rebuild()


class ChapterTreeResponse(BaseModel):
    id: str
    title: str
    is_folder: bool
    order_index: int
    document_type: str
    linked_entity_id: Optional[str]
    children: List['ChapterTreeResponse'] = []

    class Config:
        from_attributes = True


ChapterTreeResponse.model_rebuild()


class ChapterFromEntityCreate(BaseModel):
    """Create a character sheet document from an existing Codex entity"""
    manuscript_id: str
    entity_id: str
    parent_id: Optional[str] = None
    order_index: int = 0


def serialize_chapter(chapter: Chapter) -> dict:
    """
    Serialize a Chapter SQLAlchemy object to a clean dict

    This function prevents SQLAlchemy metadata (_sa_instance_state) from
    leaking into API responses, which was causing text disappearance in the frontend.

    Uses explicit field mapping to ensure only expected fields are included.
    """
    return {
        "id": chapter.id,
        "manuscript_id": chapter.manuscript_id,
        "parent_id": chapter.parent_id,
        "title": chapter.title,
        "is_folder": bool(chapter.is_folder),
        "order_index": chapter.order_index,
        "lexical_state": chapter.lexical_state or "",
        "content": chapter.content or "",
        "word_count": chapter.word_count,
        "document_type": chapter.document_type or DOCUMENT_TYPE_CHAPTER,
        "linked_entity_id": chapter.linked_entity_id,
        "document_metadata": chapter.document_metadata or {},
        "created_at": chapter.created_at.isoformat() if chapter.created_at else None,
        "updated_at": chapter.updated_at.isoformat() if chapter.updated_at else None,
        "children": []
    }


class ReorderRequest(BaseModel):
    chapter_ids: List[str]


# CRUD Endpoints

@router.post("")
async def create_chapter(
    chapter: ChapterCreate,
    db: Session = Depends(get_db)
):
    """Create a new chapter or folder"""
    # Extract content from lexical state if provided
    lexical_state = chapter.lexical_state or ""
    content = chapter.content or ""

    # Determine document_type
    # If explicit document_type provided, use it
    # Otherwise infer from is_folder
    if chapter.document_type:
        document_type = chapter.document_type
    elif chapter.is_folder:
        document_type = DOCUMENT_TYPE_FOLDER
    else:
        document_type = DOCUMENT_TYPE_CHAPTER

    # Is this a folder-like document type?
    is_folder_type = document_type == DOCUMENT_TYPE_FOLDER

    # If lexical state exists but no explicit content, extract it
    if lexical_state and not content and not is_folder_type:
        extracted_text = extract_text_from_lexical(lexical_state)
        if extracted_text:
            content = extracted_text

    word_count = 0 if is_folder_type else len(content.split()) if content else 0

    db_chapter = Chapter(
        id=str(uuid.uuid4()),
        manuscript_id=chapter.manuscript_id,
        parent_id=chapter.parent_id,
        title=chapter.title,
        is_folder=1 if chapter.is_folder or is_folder_type else 0,
        order_index=chapter.order_index,
        lexical_state=lexical_state,
        content=content,
        word_count=word_count,
        document_type=document_type,
        linked_entity_id=chapter.linked_entity_id,
        document_metadata=chapter.document_metadata or {}
    )
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)

    # Update manuscript word count if this is a document (not folder)
    if not is_folder_type:
        manuscript_aggregation_service.update_manuscript_word_count(
            db,
            chapter.manuscript_id
        )

    return {
        "success": True,
        "data": serialize_chapter(db_chapter)
    }


@router.get("/manuscript/{manuscript_id}")
async def list_chapters(
    manuscript_id: str,
    parent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all chapters for a manuscript, optionally filtered by parent"""
    query = db.query(Chapter).filter(Chapter.manuscript_id == manuscript_id)

    if parent_id:
        query = query.filter(Chapter.parent_id == parent_id)
    else:
        # If no parent_id specified, return root-level chapters
        query = query.filter(Chapter.parent_id.is_(None))

    chapters = query.order_by(Chapter.order_index).all()

    return {
        "success": True,
        "data": [serialize_chapter(chapter) for chapter in chapters]
    }


@router.get("/manuscript/{manuscript_id}/tree")
async def get_chapter_tree(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """Get the full chapter tree structure for a manuscript"""

    def build_tree(parent_id: Optional[str] = None):
        """Recursively build chapter tree"""
        query = db.query(Chapter).filter(
            Chapter.manuscript_id == manuscript_id
        )

        if parent_id:
            query = query.filter(Chapter.parent_id == parent_id)
        else:
            query = query.filter(Chapter.parent_id.is_(None))

        chapters = query.order_by(Chapter.order_index).all()

        result = []
        for chapter in chapters:
            # Folders can have children
            is_folder = chapter.is_folder or chapter.document_type == DOCUMENT_TYPE_FOLDER
            children = build_tree(chapter.id) if is_folder else []
            result.append({
                "id": chapter.id,
                "title": chapter.title,
                "is_folder": bool(chapter.is_folder),
                "order_index": chapter.order_index,
                "word_count": chapter.word_count,
                "document_type": chapter.document_type or DOCUMENT_TYPE_CHAPTER,
                "linked_entity_id": chapter.linked_entity_id,
                "children": children
            })

        return result

    return {
        "success": True,
        "data": build_tree()
    }


@router.get("/{chapter_id}")
async def get_chapter(
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific chapter by ID"""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    return {
        "success": True,
        "data": serialize_chapter(chapter)
    }


@router.get("/{chapter_id}/scene-context")
async def get_scene_context(
    chapter_id: str,
    cursor_position: int,
    db: Session = Depends(get_db)
):
    """
    Get scene context for the scene containing the cursor position.

    This endpoint is used by the SceneDetectionPlugin to provide real-time
    scene context in the BeatContextPanel while the writer is working.

    Args:
        chapter_id: Chapter ID
        cursor_position: Character offset in chapter content (0-indexed)

    Returns:
        {
            "success": True,
            "scene": {
                "scene_id": "uuid",
                "sequence_order": 2,
                "start_position": 4500,
                "end_position": 7800,
                "word_count": 1200,
                "summary": "Hero confronts villain",
                "title": "The Confrontation",
                "total_scenes_in_chapter": 5
            } or null if no scenes exist
        }
    """
    # Verify chapter exists
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Get scene context from scene detection service
    scene_info = scene_detection_service.get_scene_at_position(
        db=db,
        chapter_id=chapter_id,
        cursor_position=cursor_position
    )

    return {
        "success": True,
        "scene": scene_info  # Will be null if no scenes exist
    }


@router.put("/{chapter_id}")
async def update_chapter(
    chapter_id: str,
    chapter_update: ChapterUpdate,
    db: Session = Depends(get_db)
):
    """Update a chapter"""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Track if word count changed
    original_word_count = chapter.word_count

    # Get dict of provided fields (excluding None values from fields not set)
    update_data = chapter_update.model_dump(exclude_unset=True)

    # Update fields if provided
    if 'title' in update_data:
        chapter.title = update_data['title']
    if 'is_folder' in update_data:
        chapter.is_folder = 1 if update_data['is_folder'] else 0
    if 'parent_id' in update_data:
        # Allow setting parent_id to None (moving to root)
        chapter.parent_id = update_data['parent_id']
    if 'order_index' in update_data:
        chapter.order_index = update_data['order_index']
    if 'document_type' in update_data:
        chapter.document_type = update_data['document_type']
    if 'linked_entity_id' in update_data:
        chapter.linked_entity_id = update_data['linked_entity_id']
    if 'document_metadata' in update_data:
        chapter.document_metadata = update_data['document_metadata']
    if 'lexical_state' in update_data:
        chapter.lexical_state = update_data['lexical_state']
        # Auto-extract plain text from lexical state for search/analysis
        is_folder_type = chapter.is_folder or chapter.document_type == DOCUMENT_TYPE_FOLDER
        if chapter.lexical_state and not is_folder_type:
            extracted_text = extract_text_from_lexical(chapter.lexical_state)
            if extracted_text:
                chapter.content = extracted_text
                chapter.word_count = len(extracted_text.split())
    if 'content' in update_data:
        chapter.content = update_data['content']
        # Auto-calculate word count from content
        is_folder_type = chapter.is_folder or chapter.document_type == DOCUMENT_TYPE_FOLDER
        if chapter.content and not is_folder_type:
            chapter.word_count = len(chapter.content.split())
    if 'word_count' in update_data:
        chapter.word_count = update_data['word_count']

    chapter.updated_at = datetime.utcnow()

    # Check if word count changed
    word_count_changed = (chapter.word_count != original_word_count)

    db.commit()
    db.refresh(chapter)

    # Update aggregations if word count changed
    if word_count_changed and not chapter.is_folder:
        # Update manuscript total
        manuscript_aggregation_service.update_manuscript_word_count(
            db,
            chapter.manuscript_id
        )

        # Sync any plot beat linked to this chapter
        manuscript_aggregation_service.sync_plot_beat_word_count(
            db,
            chapter.id
        )

        # Auto-complete beat if chapter reached target word count
        beat = db.query(PlotBeat).filter(
            PlotBeat.chapter_id == chapter_id
        ).first()

        if beat and not beat.is_completed:
            # Auto-complete if chapter reached target
            if chapter.word_count >= beat.target_word_count:
                beat.is_completed = True
                beat.completed_at = datetime.utcnow()
                db.commit()
                print(f"✅ Auto-completed beat {beat.id} ({beat.beat_name})")

    return {
        "success": True,
        "data": serialize_chapter(chapter)
    }


@router.delete("/{chapter_id}")
async def delete_chapter(
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """Delete a chapter (and all its children if it's a folder)"""
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Store manuscript_id and folder status before deletion
    manuscript_id = chapter.manuscript_id
    was_folder = chapter.is_folder

    # If it's a folder, recursively delete children
    if chapter.is_folder:
        def delete_children(parent_id: str):
            children = db.query(Chapter).filter(Chapter.parent_id == parent_id).all()
            for child in children:
                if child.is_folder:
                    delete_children(child.id)
                db.delete(child)

        delete_children(chapter_id)

    db.delete(chapter)
    db.commit()

    # Update manuscript word count if we deleted a document
    if not was_folder:
        manuscript_aggregation_service.update_manuscript_word_count(
            db,
            manuscript_id
        )

    return {
        "success": True,
        "data": {
            "message": f"Chapter {chapter_id} deleted successfully"
        }
    }


@router.post("/reorder")
async def reorder_chapters(
    reorder_request: ReorderRequest,
    db: Session = Depends(get_db)
):
    """Reorder chapters based on provided IDs array"""
    chapter_ids = reorder_request.chapter_ids

    for index, chapter_id in enumerate(chapter_ids):
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if chapter:
            chapter.order_index = index

    db.commit()

    return {
        "success": True,
        "data": {
            "message": "Chapters reordered successfully",
            "count": len(chapter_ids)
        }
    }


@router.post("/from-entity")
async def create_chapter_from_entity(
    request: ChapterFromEntityCreate,
    db: Session = Depends(get_db)
):
    """
    Create a character sheet document from an existing Codex entity.
    The character sheet will be linked to the entity and pre-populated with its data.
    """
    # Verify entity exists
    entity = db.query(Entity).filter(Entity.id == request.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Only allow CHARACTER entities
    if entity.type != "CHARACTER":
        raise HTTPException(
            status_code=400,
            detail="Only CHARACTER entities can be converted to character sheets"
        )

    # Build document_metadata from entity data
    document_metadata = {
        "name": entity.name,
        "aliases": entity.aliases or [],
        "attributes": entity.attributes or {},
        "template_data": entity.template_data or {},
        "synced_at": datetime.utcnow().isoformat()
    }

    # Create the character sheet chapter
    db_chapter = Chapter(
        id=str(uuid.uuid4()),
        manuscript_id=request.manuscript_id,
        parent_id=request.parent_id,
        title=f"{entity.name} - Character Sheet",
        is_folder=0,
        order_index=request.order_index,
        lexical_state="",
        content="",
        word_count=0,
        document_type=DOCUMENT_TYPE_CHARACTER_SHEET,
        linked_entity_id=entity.id,
        document_metadata=document_metadata
    )
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)

    return {
        "success": True,
        "data": serialize_chapter(db_chapter)
    }


@router.put("/{chapter_id}/sync-entity")
async def sync_chapter_entity(
    chapter_id: str,
    direction: str = "from_entity",  # "from_entity" or "to_entity"
    db: Session = Depends(get_db)
):
    """
    Sync a character sheet with its linked Codex entity.

    direction:
    - "from_entity": Pull latest data from the entity into the character sheet
    - "to_entity": Push character sheet changes to the entity
    """
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if chapter.document_type != DOCUMENT_TYPE_CHARACTER_SHEET:
        raise HTTPException(
            status_code=400,
            detail="Only CHARACTER_SHEET documents can be synced with entities"
        )

    if not chapter.linked_entity_id:
        raise HTTPException(
            status_code=400,
            detail="This character sheet is not linked to an entity"
        )

    entity = db.query(Entity).filter(Entity.id == chapter.linked_entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Linked entity not found")

    if direction == "from_entity":
        # Pull from entity to character sheet
        chapter.document_metadata = {
            "name": entity.name,
            "aliases": entity.aliases or [],
            "attributes": entity.attributes or {},
            "template_data": entity.template_data or {},
            "synced_at": datetime.utcnow().isoformat()
        }
        chapter.title = f"{entity.name} - Character Sheet"
        chapter.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(chapter)

    elif direction == "to_entity":
        # Push from character sheet to entity
        metadata = chapter.document_metadata or {}
        if "name" in metadata:
            entity.name = metadata["name"]
        if "aliases" in metadata:
            entity.aliases = metadata["aliases"]
        if "attributes" in metadata:
            entity.attributes = metadata["attributes"]
        if "template_data" in metadata:
            entity.template_data = metadata["template_data"]

        entity.updated_at = datetime.utcnow()

        # Update synced_at in chapter
        chapter.document_metadata = {
            **metadata,
            "synced_at": datetime.utcnow().isoformat()
        }
        chapter.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(chapter)
        db.refresh(entity)

    else:
        raise HTTPException(
            status_code=400,
            detail="direction must be 'from_entity' or 'to_entity'"
        )

    return {
        "success": True,
        "data": serialize_chapter(chapter),
        "entity": {
            "id": entity.id,
            "name": entity.name,
            "type": entity.type
        }
    }
