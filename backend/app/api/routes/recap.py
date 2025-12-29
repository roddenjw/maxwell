"""
Recap API Routes
Generate aesthetic summaries for chapters and story arcs
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Recap, Chapter
from app.services.recap_service import recap_service

router = APIRouter(prefix="/api/recap", tags=["recap"])


class GenerateChapterRecapRequest(BaseModel):
    """Request to generate a chapter recap"""
    force_regenerate: bool = False  # Bypass cache


class GenerateArcRecapRequest(BaseModel):
    """Request to generate an arc recap"""
    arc_title: str
    chapter_ids: List[str]


class RecapResponse(BaseModel):
    """Response with recap data"""
    recap_id: str
    recap_type: str
    content: dict
    created_at: str
    is_cached: bool = False


@router.post("/chapter/{chapter_id}", response_model=RecapResponse)
async def generate_chapter_recap(
    chapter_id: str,
    request: GenerateChapterRecapRequest,
    db: Session = Depends(get_db)
):
    """
    Generate or retrieve a recap for a specific chapter

    Args:
        chapter_id: ID of the chapter to recap
        request: Generation options
        db: Database session

    Returns:
        Recap data
    """
    # Get the chapter
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Compute content hash for cache validation
    content_hash = recap_service.compute_content_hash(chapter.content)

    # Check for existing recap
    existing_recap = db.query(Recap).filter(
        Recap.chapter_id == chapter_id,
        Recap.recap_type == "chapter"
    ).first()

    # Use cached recap if available and content hasn't changed
    if existing_recap and not request.force_regenerate:
        if existing_recap.source_hash == content_hash:
            return RecapResponse(
                recap_id=existing_recap.id,
                recap_type=existing_recap.recap_type,
                content=existing_recap.content,
                created_at=existing_recap.created_at.isoformat(),
                is_cached=True
            )

    # Generate new recap
    recap_content = recap_service.generate_chapter_recap(
        chapter_title=chapter.title,
        chapter_content=chapter.content
    )

    # Save or update recap
    if existing_recap:
        existing_recap.content = recap_content
        existing_recap.source_hash = content_hash
        recap = existing_recap
    else:
        recap = Recap(
            manuscript_id=chapter.manuscript_id,
            chapter_id=chapter_id,
            recap_type="chapter",
            content=recap_content,
            source_hash=content_hash
        )
        db.add(recap)

    db.commit()
    db.refresh(recap)

    return RecapResponse(
        recap_id=recap.id,
        recap_type=recap.recap_type,
        content=recap.content,
        created_at=recap.created_at.isoformat(),
        is_cached=False
    )


@router.post("/arc", response_model=RecapResponse)
async def generate_arc_recap(
    request: GenerateArcRecapRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a recap for a multi-chapter story arc

    Args:
        request: Arc recap request with chapter IDs
        db: Database session

    Returns:
        Arc recap data
    """
    if not request.chapter_ids:
        raise HTTPException(status_code=400, detail="At least one chapter ID required")

    # Get all chapters
    chapters = db.query(Chapter).filter(Chapter.id.in_(request.chapter_ids)).all()

    if not chapters:
        raise HTTPException(status_code=404, detail="No chapters found")

    # Prepare chapter data
    chapter_data = [
        {
            "id": ch.id,
            "title": ch.title,
            "content": ch.content
        }
        for ch in chapters
    ]

    # Generate arc recap
    recap_content = recap_service.generate_arc_recap(
        arc_title=request.arc_title,
        chapters=chapter_data
    )

    # Save arc recap (use first chapter's manuscript_id)
    recap = Recap(
        manuscript_id=chapters[0].manuscript_id,
        chapter_id=None,  # Arc recaps don't have a single chapter
        recap_type="arc",
        content=recap_content,
        source_hash=None  # Arc recaps are not cached by content hash
    )
    db.add(recap)
    db.commit()
    db.refresh(recap)

    return RecapResponse(
        recap_id=recap.id,
        recap_type=recap.recap_type,
        content=recap.content,
        created_at=recap.created_at.isoformat(),
        is_cached=False
    )


@router.get("/chapter/{chapter_id}", response_model=RecapResponse)
async def get_chapter_recap(
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the cached recap for a chapter (if it exists)

    Args:
        chapter_id: ID of the chapter
        db: Database session

    Returns:
        Cached recap or 404
    """
    recap = db.query(Recap).filter(
        Recap.chapter_id == chapter_id,
        Recap.recap_type == "chapter"
    ).first()

    if not recap:
        raise HTTPException(status_code=404, detail="No recap found for this chapter")

    return RecapResponse(
        recap_id=recap.id,
        recap_type=recap.recap_type,
        content=recap.content,
        created_at=recap.created_at.isoformat(),
        is_cached=True
    )


@router.delete("/chapter/{chapter_id}")
async def delete_chapter_recap(
    chapter_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete the cached recap for a chapter

    Args:
        chapter_id: ID of the chapter
        db: Database session

    Returns:
        Success message
    """
    recap = db.query(Recap).filter(
        Recap.chapter_id == chapter_id,
        Recap.recap_type == "chapter"
    ).first()

    if recap:
        db.delete(recap)
        db.commit()
        return {"message": "Recap deleted successfully"}

    raise HTTPException(status_code=404, detail="No recap found for this chapter")


@router.get("/manuscript/{manuscript_id}/recaps")
async def get_manuscript_recaps(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all recaps for a manuscript

    Args:
        manuscript_id: ID of the manuscript
        db: Database session

    Returns:
        List of recaps
    """
    recaps = db.query(Recap).filter(
        Recap.manuscript_id == manuscript_id
    ).order_by(Recap.created_at.desc()).all()

    return {
        "recaps": [
            {
                "recap_id": r.id,
                "recap_type": r.recap_type,
                "chapter_id": r.chapter_id,
                "created_at": r.created_at.isoformat(),
                "content": r.content
            }
            for r in recaps
        ]
    }
