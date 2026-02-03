"""
Writing Feedback API Routes.

Provides endpoints for real-time, paragraph, and chapter-level
writing analysis with inline highlighting support.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.manuscript import Manuscript, Chapter
from app.services.writing_feedback_service import (
    writing_feedback_service,
    FeedbackSettings,
    FeedbackResponse,
    WritingIssue
)
from app.services.languagetool_service import languagetool_service

router = APIRouter(prefix="/api/writing-feedback", tags=["writing-feedback"])


# Request/Response Models

class RealtimeAnalysisRequest(BaseModel):
    """Request for real-time analysis"""
    text: str = Field(..., description="Text to analyze")
    manuscript_id: Optional[str] = Field(None, description="Manuscript ID for custom dictionary")
    settings: Optional[dict] = Field(None, description="Feedback settings override")


class ChapterAnalysisRequest(BaseModel):
    """Request for chapter analysis"""
    settings: Optional[dict] = Field(None, description="Feedback settings override")


class ApplyFixRequest(BaseModel):
    """Request to apply a fix"""
    chapter_id: str = Field(..., description="Chapter to modify")
    start_offset: int = Field(..., description="Start position of text to replace")
    end_offset: int = Field(..., description="End position of text to replace")
    replacement: str = Field(..., description="Text to insert")


class AddToDictionaryRequest(BaseModel):
    """Request to add word to dictionary"""
    word: str = Field(..., description="Word to add")


class FeedbackSettingsUpdate(BaseModel):
    """Update feedback settings"""
    spelling: Optional[bool] = None
    grammar: Optional[bool] = None
    style: Optional[bool] = None
    word_choice: Optional[bool] = None
    dialogue: Optional[bool] = None
    show_info_level: Optional[bool] = None
    min_confidence: Optional[float] = None
    custom_dictionary: Optional[List[str]] = None
    ignored_rules: Optional[List[str]] = None
    language: Optional[str] = None


# Endpoints

@router.post("/realtime")
async def analyze_realtime(
    request: RealtimeAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Real-time analysis for typing feedback.

    Fast analysis (<500ms) that only checks spelling and basic grammar.
    Call this with debouncing (~1s) while the user types.

    Returns issues with positions for inline highlighting.
    """
    # Build settings from request and manuscript defaults
    settings = _build_settings(request.settings, request.manuscript_id, db)

    # Run real-time analysis
    response = writing_feedback_service.analyze_realtime(
        text=request.text,
        settings=settings,
        manuscript_id=request.manuscript_id,
        db=db
    )

    return response.to_dict()


@router.post("/paragraph")
async def analyze_paragraph(
    request: RealtimeAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Paragraph-level analysis.

    More thorough analysis (<2s) including style checks.
    Trigger on paragraph completion or brief pause.
    """
    settings = _build_settings(request.settings, request.manuscript_id, db)

    response = writing_feedback_service.analyze_paragraph(
        text=request.text,
        settings=settings,
        manuscript_id=request.manuscript_id,
        db=db
    )

    return response.to_dict()


@router.post("/chapter/{chapter_id}")
async def analyze_chapter(
    chapter_id: str,
    request: Optional[ChapterAnalysisRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Full chapter analysis.

    Complete analysis (<10s) including dialogue checks.
    Trigger manually or on save.
    """
    # Get chapter
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Get text from chapter content
    text = _extract_text_from_content(chapter.content)
    if not text:
        return {
            "issues": [],
            "stats": {"total": 0},
            "analysis_time_ms": 0,
            "text_length": 0
        }

    # Build settings
    settings_dict = request.settings if request else None
    settings = _build_settings(settings_dict, chapter.manuscript_id, db)

    response = writing_feedback_service.analyze_chapter(
        text=text,
        settings=settings,
        manuscript_id=chapter.manuscript_id,
        chapter_id=chapter_id,
        db=db
    )

    return response.to_dict()


@router.post("/manuscript/{manuscript_id}")
async def analyze_manuscript(
    manuscript_id: str,
    request: Optional[ChapterAnalysisRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Full manuscript analysis.

    Analyzes all chapters. May take longer for large manuscripts.
    Returns aggregated issues across all chapters.
    """
    # Get manuscript
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    # Get all chapters
    chapters = db.query(Chapter).filter(
        Chapter.manuscript_id == manuscript_id,
        Chapter.document_type == "CHAPTER"
    ).order_by(Chapter.order).all()

    if not chapters:
        return {
            "issues": [],
            "stats": {"total": 0},
            "analysis_time_ms": 0,
            "text_length": 0,
            "chapters_analyzed": 0
        }

    # Build settings
    settings_dict = request.settings if request else None
    settings = _build_settings(settings_dict, manuscript_id, db)

    # Analyze each chapter
    all_issues = []
    total_time = 0
    total_length = 0

    for chapter in chapters:
        text = _extract_text_from_content(chapter.content)
        if not text:
            continue

        response = writing_feedback_service.analyze_chapter(
            text=text,
            settings=settings,
            manuscript_id=manuscript_id,
            chapter_id=chapter.id,
            db=db
        )

        # Add chapter info to issues
        for issue in response.issues:
            issue_dict = issue.to_dict()
            issue_dict["chapter_id"] = chapter.id
            issue_dict["chapter_title"] = chapter.title
            all_issues.append(issue_dict)

        total_time += response.analysis_time_ms
        total_length += response.text_length

    # Calculate overall stats
    stats = {
        "total": len(all_issues),
        "spelling": sum(1 for i in all_issues if i["type"] == "spelling"),
        "grammar": sum(1 for i in all_issues if i["type"] == "grammar"),
        "style": sum(1 for i in all_issues if i["type"] == "style"),
        "word_choice": sum(1 for i in all_issues if i["type"] == "word_choice"),
        "dialogue": sum(1 for i in all_issues if i["type"] == "dialogue"),
    }

    return {
        "issues": all_issues,
        "stats": stats,
        "analysis_time_ms": total_time,
        "text_length": total_length,
        "chapters_analyzed": len(chapters)
    }


@router.post("/add-to-dictionary/{manuscript_id}")
async def add_to_dictionary(
    manuscript_id: str,
    request: AddToDictionaryRequest,
    db: Session = Depends(get_db)
):
    """
    Add a word to the manuscript's custom dictionary.

    Use for character names, made-up words, and other fiction-specific terms.
    """
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    word = request.word.strip()
    if not word:
        raise HTTPException(status_code=400, detail="Word cannot be empty")

    # Update manuscript settings
    settings = manuscript.settings or {}
    feedback_settings = settings.get("writing_feedback", {})
    custom_dict = feedback_settings.get("custom_dictionary", [])

    if word not in custom_dict:
        custom_dict.append(word)
        feedback_settings["custom_dictionary"] = custom_dict
        settings["writing_feedback"] = feedback_settings
        manuscript.settings = settings
        db.commit()

        # Also add to LanguageTool's runtime dictionary
        languagetool_service.add_to_dictionary(word)

    return {"status": "added", "word": word}


@router.delete("/dictionary/{manuscript_id}/{word}")
async def remove_from_dictionary(
    manuscript_id: str,
    word: str,
    db: Session = Depends(get_db)
):
    """Remove a word from the custom dictionary."""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    settings = manuscript.settings or {}
    feedback_settings = settings.get("writing_feedback", {})
    custom_dict = feedback_settings.get("custom_dictionary", [])

    if word in custom_dict:
        custom_dict.remove(word)
        feedback_settings["custom_dictionary"] = custom_dict
        settings["writing_feedback"] = feedback_settings
        manuscript.settings = settings
        db.commit()

    return {"status": "removed", "word": word}


@router.post("/ignore-rule/{manuscript_id}")
async def ignore_rule(
    manuscript_id: str,
    rule_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Add a rule to the ignore list for this manuscript.

    Use when a rule produces too many false positives for your writing style.
    """
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    settings = manuscript.settings or {}
    feedback_settings = settings.get("writing_feedback", {})
    ignored_rules = feedback_settings.get("ignored_rules", [])

    if rule_id not in ignored_rules:
        ignored_rules.append(rule_id)
        feedback_settings["ignored_rules"] = ignored_rules
        settings["writing_feedback"] = feedback_settings
        manuscript.settings = settings
        db.commit()

    return {"status": "ignored", "rule_id": rule_id}


@router.get("/settings/{manuscript_id}")
async def get_settings(
    manuscript_id: str,
    db: Session = Depends(get_db)
):
    """Get feedback settings for a manuscript."""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    settings = manuscript.settings or {}
    feedback_settings = settings.get("writing_feedback", {})

    # Return with defaults
    return {
        "spelling": feedback_settings.get("spelling", True),
        "grammar": feedback_settings.get("grammar", True),
        "style": feedback_settings.get("style", True),
        "word_choice": feedback_settings.get("word_choice", True),
        "dialogue": feedback_settings.get("dialogue", True),
        "show_info_level": feedback_settings.get("show_info_level", False),
        "min_confidence": feedback_settings.get("min_confidence", 0.5),
        "custom_dictionary": feedback_settings.get("custom_dictionary", []),
        "ignored_rules": feedback_settings.get("ignored_rules", []),
        "language": feedback_settings.get("language", "en-US")
    }


@router.put("/settings/{manuscript_id}")
async def update_settings(
    manuscript_id: str,
    updates: FeedbackSettingsUpdate,
    db: Session = Depends(get_db)
):
    """Update feedback settings for a manuscript."""
    manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
    if not manuscript:
        raise HTTPException(status_code=404, detail="Manuscript not found")

    settings = manuscript.settings or {}
    feedback_settings = settings.get("writing_feedback", {})

    # Apply updates
    update_dict = updates.dict(exclude_none=True)
    for key, value in update_dict.items():
        feedback_settings[key] = value

    settings["writing_feedback"] = feedback_settings
    manuscript.settings = settings
    db.commit()

    return {"status": "updated", "settings": feedback_settings}


@router.get("/status")
async def get_status():
    """Check if writing feedback services are available."""
    return {
        "languagetool_available": languagetool_service.is_available(),
        "supported_languages": languagetool_service.get_supported_languages()
    }


# Helper Functions

def _build_settings(
    request_settings: Optional[dict],
    manuscript_id: Optional[str],
    db: Session
) -> FeedbackSettings:
    """Build FeedbackSettings from request and manuscript defaults."""
    settings = FeedbackSettings()

    # Load manuscript defaults if available
    if manuscript_id:
        manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
        if manuscript and manuscript.settings:
            ms_settings = manuscript.settings.get("writing_feedback", {})
            settings.spelling = ms_settings.get("spelling", settings.spelling)
            settings.grammar = ms_settings.get("grammar", settings.grammar)
            settings.style = ms_settings.get("style", settings.style)
            settings.word_choice = ms_settings.get("word_choice", settings.word_choice)
            settings.dialogue = ms_settings.get("dialogue", settings.dialogue)
            settings.show_info_level = ms_settings.get("show_info_level", settings.show_info_level)
            settings.min_confidence = ms_settings.get("min_confidence", settings.min_confidence)
            settings.custom_dictionary = ms_settings.get("custom_dictionary", settings.custom_dictionary)
            settings.ignored_rules = ms_settings.get("ignored_rules", settings.ignored_rules)
            settings.language = ms_settings.get("language", settings.language)

    # Override with request settings
    if request_settings:
        if "spelling" in request_settings:
            settings.spelling = request_settings["spelling"]
        if "grammar" in request_settings:
            settings.grammar = request_settings["grammar"]
        if "style" in request_settings:
            settings.style = request_settings["style"]
        if "word_choice" in request_settings:
            settings.word_choice = request_settings["word_choice"]
        if "dialogue" in request_settings:
            settings.dialogue = request_settings["dialogue"]
        if "show_info_level" in request_settings:
            settings.show_info_level = request_settings["show_info_level"]
        if "min_confidence" in request_settings:
            settings.min_confidence = request_settings["min_confidence"]
        if "language" in request_settings:
            settings.language = request_settings["language"]

    return settings


def _extract_text_from_content(content: Optional[str]) -> str:
    """Extract plain text from Lexical JSON content."""
    if not content:
        return ""

    # If it's already plain text, return it
    if not content.strip().startswith("{"):
        return content

    # Parse Lexical JSON and extract text
    try:
        import json
        data = json.loads(content)
        return _extract_text_from_lexical(data)
    except (json.JSONDecodeError, KeyError):
        return content


def _extract_text_from_lexical(node: dict) -> str:
    """Recursively extract text from Lexical JSON nodes."""
    text_parts = []

    if node.get("type") == "text":
        text_parts.append(node.get("text", ""))
    elif "children" in node:
        for child in node["children"]:
            text_parts.append(_extract_text_from_lexical(child))
        # Add paragraph breaks between block-level elements
        if node.get("type") in ("paragraph", "heading"):
            text_parts.append("\n")

    return "".join(text_parts)
