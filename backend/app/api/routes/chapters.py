"""
Chapter CRUD API Routes
Handles hierarchical chapter/folder structure (Scrivener-like navigation)
"""

import json
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.manuscript import Chapter
from app.services.manuscript_aggregation_service import manuscript_aggregation_service


router = APIRouter(prefix="/api/chapters", tags=["chapters"])


def extract_text_from_lexical(lexical_state_str: str) -> str:
    """
    Extract plain text from Lexical editor state JSON
    Recursively walks the node tree and concatenates text content
    """
    try:
        if not lexical_state_str or lexical_state_str.strip() == "":
            return ""

        state = json.loads(lexical_state_str)

        def walk_nodes(node):
            """Recursively extract text from Lexical nodes"""
            text_parts = []

            # Handle root node
            if isinstance(node, dict):
                # Direct text content
                if node.get("type") == "text" and "text" in node:
                    text_parts.append(node["text"])

                # Paragraph nodes add newlines
                if node.get("type") == "paragraph" and node != state.get("root"):
                    # Will add newline after processing children
                    pass

                # Process children
                if "children" in node:
                    for child in node["children"]:
                        text_parts.append(walk_nodes(child))

                    # Add newline after paragraph
                    if node.get("type") == "paragraph":
                        text_parts.append("\n")

            return "".join(text_parts)

        # Start from root
        root = state.get("root", {})
        text = walk_nodes(root)

        # Clean up extra newlines
        text = text.strip()

        return text
    except Exception as e:
        print(f"⚠️  Failed to extract text from lexical state: {e}")
        return ""


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

    # If lexical state exists but no explicit content, extract it
    if lexical_state and not content and not chapter.is_folder:
        extracted_text = extract_text_from_lexical(lexical_state)
        if extracted_text:
            content = extracted_text

    word_count = 0 if chapter.is_folder else len(content.split()) if content else 0

    db_chapter = Chapter(
        id=str(uuid.uuid4()),
        manuscript_id=chapter.manuscript_id,
        parent_id=chapter.parent_id,
        title=chapter.title,
        is_folder=1 if chapter.is_folder else 0,
        order_index=chapter.order_index,
        lexical_state=lexical_state,
        content=content,
        word_count=word_count
    )
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)

    # Update manuscript word count if this is a document (not folder)
    if not chapter.is_folder:
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
        "data": serialize_chapter(chapter)
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
    if 'lexical_state' in update_data:
        chapter.lexical_state = update_data['lexical_state']
        # Auto-extract plain text from lexical state for search/analysis
        if chapter.lexical_state and not chapter.is_folder:
            extracted_text = extract_text_from_lexical(chapter.lexical_state)
            if extracted_text:
                chapter.content = extracted_text
                chapter.word_count = len(extracted_text.split())
    if 'content' in update_data:
        chapter.content = update_data['content']
        # Auto-calculate word count from content
        if chapter.content and not chapter.is_folder:
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
