"""
Import API Routes
Handles manuscript import from various document formats.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.import_service import import_service, SUPPORTED_FORMATS


router = APIRouter(prefix="/api/import", tags=["import"])


# --- Response Models ---

class FormatInfo(BaseModel):
    """Information about a supported import format."""
    extension: str
    name: str
    description: str
    formatting_support: str  # "full", "partial", "none"
    warning: Optional[str] = None


class ChapterPreview(BaseModel):
    """Preview of a detected chapter."""
    index: int
    title: str
    word_count: int
    preview_text: str
    included: bool = True


class ParseResponse(BaseModel):
    """Response from parsing a document."""
    success: bool
    parse_id: str
    title: str
    author: Optional[str]
    total_words: int
    detection_method: str
    format_warnings: List[str]
    chapters: List[ChapterPreview]
    source_format: str


class ChapterAdjustment(BaseModel):
    """Adjustment to a chapter during import."""
    index: int
    title: Optional[str] = None
    included: bool = True


class CreateRequest(BaseModel):
    """Request to create a manuscript from a parsed import."""
    parse_id: str
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    chapter_adjustments: Optional[List[ChapterAdjustment]] = None
    series_id: Optional[str] = None


class CreateResponse(BaseModel):
    """Response from creating a manuscript."""
    success: bool
    manuscript_id: str
    title: str
    chapter_count: int
    total_words: int


# --- Endpoints ---

@router.get("/formats")
async def get_supported_formats() -> dict:
    """
    Get list of supported import formats.

    Returns metadata about each format including:
    - Extension (.docx, .rtf, etc.)
    - Name and description
    - Level of formatting support (full, partial, none)
    - Any warnings about the format
    """
    formats = []
    for ext, info in SUPPORTED_FORMATS.items():
        formats.append(FormatInfo(
            extension=info["extension"],
            name=info["name"],
            description=info["description"],
            formatting_support=info["formatting_support"],
            warning=info.get("warning"),
        ))

    return {
        "success": True,
        "formats": [f.model_dump() for f in formats],
    }


@router.post("/parse")
async def parse_document(
    file: UploadFile = File(...),
    detection_mode: str = Query(
        "auto",
        description="Chapter detection mode: auto, headings, pattern, page_breaks, single"
    ),
) -> dict:
    """
    Parse an uploaded document and detect chapters.

    This is step 1 of the two-step import flow:
    1. Parse document -> returns preview with chapters
    2. Create manuscript -> uses parse_id to create the actual records

    Args:
        file: The document file to parse
        detection_mode: How to detect chapter boundaries
            - "auto": Try all methods in order (headings -> pattern -> page breaks -> single)
            - "headings": Split on H1/H2 heading styles
            - "pattern": Split on patterns like "Chapter 1", "CHAPTER ONE", etc.
            - "page_breaks": Split on explicit page breaks
            - "single": Treat entire document as one chapter

    Returns:
        ParseResponse with chapter previews and a parse_id for step 2
    """
    # Validate detection mode
    valid_modes = ["auto", "headings", "pattern", "page_breaks", "single"]
    if detection_mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid detection_mode. Must be one of: {', '.join(valid_modes)}"
        )

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    # Parse the document
    try:
        result = await import_service.parse_document(
            file_content=content,
            filename=file.filename or "unknown.txt",
            detection_mode=detection_mode,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {e}")

    # Build chapter previews
    chapter_previews = []
    for ch in result.chapters:
        # Generate preview text
        preview = ch.plain_content[:200].strip()
        if len(ch.plain_content) > 200:
            preview += "..."

        chapter_previews.append(ChapterPreview(
            index=ch.index,
            title=ch.title,
            word_count=ch.word_count,
            preview_text=preview,
            included=True,
        ))

    return {
        "success": True,
        "parse_id": result.parse_id,
        "title": result.title,
        "author": result.author,
        "total_words": result.total_words,
        "detection_method": result.detection_method,
        "format_warnings": result.format_warnings,
        "chapters": [cp.model_dump() for cp in chapter_previews],
        "source_format": result.source_format,
    }


@router.post("/create")
async def create_manuscript(
    request: CreateRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Create a manuscript from a previously parsed import.

    This is step 2 of the two-step import flow.
    Uses the parse_id from step 1 to retrieve the cached parse result
    and create the actual Manuscript and Chapter records.

    Args:
        request: CreateRequest with parse_id and optional overrides

    Returns:
        CreateResponse with the new manuscript ID
    """
    # Validate parse_id exists
    cached = import_service.get_cached_result(request.parse_id)
    if not cached:
        raise HTTPException(
            status_code=404,
            detail="Parse result not found or expired. Please re-upload the file."
        )

    try:
        # Convert chapter adjustments to dict format
        adjustments = None
        if request.chapter_adjustments:
            adjustments = [adj.model_dump() for adj in request.chapter_adjustments]

        # Create the manuscript
        manuscript = await import_service.create_manuscript_from_import(
            db=db,
            parse_id=request.parse_id,
            title=request.title,
            author=request.author,
            description=request.description,
            chapter_adjustments=adjustments,
            series_id=request.series_id,
        )

        # Count chapters that were created
        chapter_count = db.query(
            __import__('app.models.manuscript', fromlist=['Chapter']).Chapter
        ).filter_by(manuscript_id=manuscript.id).count()

        return {
            "success": True,
            "manuscript_id": manuscript.id,
            "title": manuscript.title,
            "chapter_count": chapter_count,
            "total_words": manuscript.word_count,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create manuscript: {e}")


@router.get("/preview/{parse_id}")
async def get_parse_preview(parse_id: str) -> dict:
    """
    Get the preview for a previously parsed document.

    Useful for refreshing the UI without re-uploading the file.
    """
    result = import_service.get_cached_result(parse_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Parse result not found or expired. Please re-upload the file."
        )

    # Build chapter previews
    chapter_previews = []
    for ch in result.chapters:
        preview = ch.plain_content[:200].strip()
        if len(ch.plain_content) > 200:
            preview += "..."

        chapter_previews.append(ChapterPreview(
            index=ch.index,
            title=ch.title,
            word_count=ch.word_count,
            preview_text=preview,
            included=True,
        ))

    return {
        "success": True,
        "parse_id": result.parse_id,
        "title": result.title,
        "author": result.author,
        "total_words": result.total_words,
        "detection_method": result.detection_method,
        "format_warnings": result.format_warnings,
        "chapters": [cp.model_dump() for cp in chapter_previews],
        "source_format": result.source_format,
    }
