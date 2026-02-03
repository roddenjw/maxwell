"""
Import API Routes
Handles manuscript import from various document formats.
"""

import os
import uuid as uuid_lib
import tempfile
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.import_service import import_service, SUPPORTED_FORMATS
from app.services.scrivener_import_service import scrivener_import_service
from app.models.manuscript import Manuscript, Chapter
from app.models.entity import Entity


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


# --- Scrivener Import Models ---

class ScrivenerPreviewResponse(BaseModel):
    """Preview of what will be imported from Scrivener"""
    title: str
    author: Optional[str]
    draft_found: bool
    draft_documents: int
    draft_word_count: int
    characters_found: bool
    characters_count: int
    locations_found: bool
    locations_count: int
    research_found: bool
    research_count: int


class ScrivenerImportResponse(BaseModel):
    """Result of Scrivener import operation"""
    success: bool
    manuscript_id: str
    title: str
    chapters_imported: int
    entities_imported: int
    word_count: int
    message: str


# --- Scrivener Import Endpoints ---

@router.post("/scrivener/preview")
async def preview_scrivener_import(
    file: UploadFile = File(..., description="Zipped .scriv project folder"),
    db: Session = Depends(get_db)
) -> dict:
    """
    Preview what will be imported from a Scrivener project.

    Upload a .zip file containing the .scriv folder.
    Returns a summary of what will be imported without creating anything.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Validate file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="Please upload a .zip file containing your .scriv project folder"
        )

    # Save uploaded file temporarily
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Parse Scrivener project
        project = await scrivener_import_service.parse_scrivener_project(temp_path)

        # Get preview
        preview = scrivener_import_service.get_preview(project)

        return {
            "success": True,
            "title": preview["title"],
            "author": preview["author"],
            "draft_found": preview["draft"]["found"],
            "draft_documents": preview["draft"]["documents"],
            "draft_word_count": preview["draft"]["word_count"],
            "characters_found": preview["characters"]["found"],
            "characters_count": preview["characters"]["count"],
            "locations_found": preview["locations"]["found"],
            "locations_count": preview["locations"]["count"],
            "research_found": preview["research"]["found"],
            "research_count": preview["research"]["count"],
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing Scrivener project: {str(e)}"
        )
    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/scrivener")
async def import_scrivener_project(
    file: UploadFile = File(..., description="Zipped .scriv project folder"),
    import_research: bool = Query(
        False,
        description="Import research folder as notes"
    ),
    import_characters: bool = Query(
        True,
        description="Import character sheets as Codex entities"
    ),
    import_locations: bool = Query(
        True,
        description="Import location documents as Codex entities"
    ),
    db: Session = Depends(get_db)
) -> dict:
    """
    Import a Scrivener project into Maxwell.

    Upload a .zip file containing your .scriv folder.
    The project will be converted to a Maxwell manuscript with:
    - Draft documents becoming chapters
    - Character sheets becoming Codex entities
    - Location documents becoming Codex entities
    - Optionally, research folder becoming notes
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    # Validate file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="Please upload a .zip file containing your .scriv project folder"
        )

    # Save uploaded file temporarily
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Parse Scrivener project
        project = await scrivener_import_service.parse_scrivener_project(temp_path)

        # Convert to Maxwell format
        maxwell_data = scrivener_import_service.convert_to_maxwell(
            project,
            import_research=import_research,
            import_characters=import_characters,
            import_locations=import_locations
        )

        # Create manuscript
        manuscript_id = str(uuid_lib.uuid4())
        manuscript = Manuscript(
            id=manuscript_id,
            title=maxwell_data["title"],
            settings={
                "imported_from": "scrivener",
                "original_author": maxwell_data.get("author"),
                "import_stats": maxwell_data.get("import_stats", {})
            }
        )
        db.add(manuscript)

        # Track totals
        total_chapters = 0
        total_word_count = 0

        # Create chapters recursively
        def create_chapters(chapter_list, parent_id=None):
            nonlocal total_chapters, total_word_count

            for idx, chapter_data in enumerate(chapter_list):
                chapter_id = str(uuid_lib.uuid4())

                chapter = Chapter(
                    id=chapter_id,
                    manuscript_id=manuscript_id,
                    title=chapter_data["title"],
                    content=chapter_data.get("content", ""),
                    document_type=chapter_data.get("document_type", "CHAPTER"),
                    order=idx,
                    parent_id=parent_id
                )
                db.add(chapter)
                total_chapters += 1
                total_word_count += chapter_data.get("word_count", 0)

                # Handle nested children
                if chapter_data.get("children"):
                    create_chapters(chapter_data["children"], chapter_id)

        create_chapters(maxwell_data["chapters"])

        # Create entities
        total_entities = 0
        for entity_data in maxwell_data["entities"]:
            entity = Entity(
                id=str(uuid_lib.uuid4()),
                manuscript_id=manuscript_id,
                name=entity_data["name"],
                type=entity_data["type"],
                description=entity_data.get("description", ""),
                aliases=[],
                attributes={
                    "notes": entity_data.get("notes", ""),
                    "imported_from": "scrivener",
                    "scrivener_metadata": entity_data.get("metadata", {})
                }
            )
            db.add(entity)
            total_entities += 1

        db.commit()

        return {
            "success": True,
            "manuscript_id": manuscript_id,
            "title": maxwell_data["title"],
            "chapters_imported": total_chapters,
            "entities_imported": total_entities,
            "word_count": total_word_count,
            "message": f"Successfully imported '{maxwell_data['title']}' from Scrivener"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error importing Scrivener project: {str(e)}"
        )
    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
