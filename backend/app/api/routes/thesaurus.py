"""
Thesaurus API Routes
Provides synonym and related word lookups for the inline thesaurus feature
"""

from fastapi import APIRouter, Query
from typing import Dict, Any, List
from pydantic import BaseModel

from app.services.thesaurus_service import thesaurus_service


router = APIRouter(prefix="/api/thesaurus", tags=["thesaurus"])


class SynonymGroup(BaseModel):
    """A group of synonyms for a part of speech"""
    part_of_speech: str
    definition: str
    words: List[str]


class SynonymsResponse(BaseModel):
    """Response with synonyms for a word"""
    word: str
    found: bool
    groups: List[SynonymGroup] = []
    antonyms: List[str] = []
    fallback: bool = False
    error: str | None = None


class RelatedWordsResponse(BaseModel):
    """Response with related words"""
    word: str
    found: bool
    definition: str | None = None
    broader_terms: List[str] = []
    narrower_terms: List[str] = []
    parts: List[str] = []
    part_of: List[str] = []
    error: str | None = None


@router.get("/synonyms/{word}", response_model=SynonymsResponse)
async def get_synonyms(
    word: str,
    max_results: int = Query(default=20, le=50, ge=1)
) -> SynonymsResponse:
    """
    Get synonyms for a word, organized by part of speech

    Args:
        word: The word to look up
        max_results: Maximum synonyms per category (1-50)

    Returns:
        Synonyms grouped by part of speech with definitions
    """
    result = thesaurus_service.get_synonyms(word, max_results=max_results)
    return SynonymsResponse(**result)


@router.get("/related/{word}", response_model=RelatedWordsResponse)
async def get_related_words(
    word: str,
    max_results: int = Query(default=10, le=30, ge=1)
) -> RelatedWordsResponse:
    """
    Get related words including broader/narrower terms

    Args:
        word: The word to look up
        max_results: Maximum results per category (1-30)

    Returns:
        Related words by relationship type
    """
    result = thesaurus_service.get_related_words(word, max_results=max_results)
    return RelatedWordsResponse(**result)


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for thesaurus service"""
    return {
        "success": True,
        "data": {
            "status": "ok",
            "service": "thesaurus",
            "wordnet_available": thesaurus_service.is_available()
        }
    }
