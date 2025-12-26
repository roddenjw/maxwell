"""
Chapter CRUD API Routes
Handles hierarchical chapter/folder structure (Scrivener-like navigation)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from app.database import get_db
from app.models.manuscript import Chapter


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


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    is_folder: Optional[bool] = None
    parent_id: Optional[str] = None
    order_index: Optional[int] = None
    lexical_state: Optional[str] = None
    content: Optional[str] = None
    word_count: Optional[int] = None


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
    children: List['ChapterTreeResponse'] = []

    class Config:
        from_attributes = True


ChapterTreeResponse.model_rebuild()


class ReorderRequest(BaseModel):
    chapter_ids: List[str]


# CRUD Endpoints

@router.post("")
async def create_chapter(
    chapter: ChapterCreate,
    db: Session = Depends(get_db)
):
    """Create a new chapter or folder"""
    db_chapter = Chapter(
        id=str(uuid.uuid4()),
        manuscript_id=chapter.manuscript_id,
        parent_id=chapter.parent_id,
        title=chapter.title,
        is_folder=1 if chapter.is_folder else 0,
        order_index=chapter.order_index,
        lexical_state=chapter.lexical_state or "",
        content=chapter.content or "",
        word_count=0
    )
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)

    return {
        "success": True,
        "data": {
            **db_chapter.__dict__,
            "is_folder": bool(db_chapter.is_folder),
            "children": []
        }
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
        "data": [
            {
                **chapter.__dict__,
                "is_folder": bool(chapter.is_folder),
                "children": []
            }
            for chapter in chapters
        ]
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
            children = build_tree(chapter.id) if chapter.is_folder else []
            result.append({
                "id": chapter.id,
                "title": chapter.title,
                "is_folder": bool(chapter.is_folder),
                "order_index": chapter.order_index,
                "word_count": chapter.word_count,
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
        "data": {
            **chapter.__dict__,
            "is_folder": bool(chapter.is_folder),
            "children": []
        }
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
    if 'lexical_state' in update_data:
        chapter.lexical_state = update_data['lexical_state']
    if 'content' in update_data:
        chapter.content = update_data['content']
    if 'word_count' in update_data:
        chapter.word_count = update_data['word_count']

    chapter.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(chapter)

    return {
        "success": True,
        "data": {
            **chapter.__dict__,
            "is_folder": bool(chapter.is_folder),
            "children": []
        }
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
