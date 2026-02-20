"""
Wiki API Routes - CRUD operations for World Wiki.

Endpoints for:
- Wiki entry management
- Cross-reference management
- Change approval queue
- Wiki-Codex synchronization
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.services.wiki_service import WikiService, WikiConsistencyEngine
from app.services.wiki_codex_bridge import WikiCodexBridge
from app.services.wiki_auto_populator import WikiAutoPopulator
from app.services.culture_service import CultureService
from app.models.wiki import WikiEntry, WikiEntryType, WikiEntryStatus, WikiChangeType, WikiReferenceType


router = APIRouter(prefix="/wiki", tags=["wiki"])


# ==================== Pydantic Models ====================

class WikiEntryCreate(BaseModel):
    world_id: str
    entry_type: str
    title: str
    content: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    parent_id: Optional[str] = None
    linked_entity_id: Optional[str] = None
    tags: Optional[List[str]] = None
    aliases: Optional[List[str]] = None


class WikiEntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    parent_id: Optional[str] = None
    tags: Optional[List[str]] = None
    aliases: Optional[List[str]] = None
    image_url: Optional[str] = None


class WikiEntryResponse(BaseModel):
    id: str
    world_id: str
    entry_type: str
    title: str
    slug: str
    content: Optional[str] = None
    structured_data: Dict[str, Any] = {}
    summary: Optional[str] = None
    parent_id: Optional[str] = None
    linked_entity_id: Optional[str] = None
    source_manuscripts: List[str] = []
    status: str
    confidence_score: float
    tags: List[str] = []
    aliases: List[str] = []
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WikiCrossReferenceCreate(BaseModel):
    source_entry_id: str
    target_entry_id: str
    reference_type: str
    context: Optional[str] = None
    bidirectional: bool = True


class WikiCrossReferenceResponse(BaseModel):
    id: str
    source_entry_id: str
    target_entry_id: str
    reference_type: str
    context: Optional[str] = None
    bidirectional: int
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class WikiChangeResponse(BaseModel):
    id: str
    wiki_entry_id: Optional[str] = None
    world_id: str
    change_type: str
    field_changed: Optional[str] = None
    old_value: Optional[Dict] = None
    new_value: Dict
    proposed_entry: Optional[Dict] = None
    reason: Optional[str] = None
    source_text: Optional[str] = None
    confidence: float
    status: str
    created_at: datetime
    # Resolved fields for display
    entry_title: Optional[str] = None
    entry_type: Optional[str] = None

    class Config:
        from_attributes = True


class ChangeReviewRequest(BaseModel):
    reviewer_note: Optional[str] = None


class SyncRequest(BaseModel):
    manuscript_id: str
    world_id: str
    entry_types: Optional[List[str]] = None


# ==================== Wiki Entry Endpoints ====================

@router.post("/entries", response_model=WikiEntryResponse)
def create_wiki_entry(
    entry: WikiEntryCreate,
    db: Session = Depends(get_db)
):
    """Create a new wiki entry"""
    service = WikiService(db)

    created = service.create_entry(
        world_id=entry.world_id,
        entry_type=entry.entry_type,
        title=entry.title,
        content=entry.content,
        structured_data=entry.structured_data,
        summary=entry.summary,
        parent_id=entry.parent_id,
        linked_entity_id=entry.linked_entity_id,
        tags=entry.tags,
        aliases=entry.aliases,
        created_by="author"
    )

    return created


@router.get("/entries/{entry_id}", response_model=WikiEntryResponse)
def get_wiki_entry(
    entry_id: str,
    db: Session = Depends(get_db)
):
    """Get a wiki entry by ID"""
    service = WikiService(db)
    entry = service.get_entry(entry_id)

    if not entry:
        raise HTTPException(status_code=404, detail="Wiki entry not found")

    return entry


@router.get("/worlds/{world_id}/entries", response_model=List[WikiEntryResponse])
def get_world_entries(
    world_id: str,
    entry_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    parent_id: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get wiki entries for a world"""
    service = WikiService(db)

    entries = service.get_entries_by_world(
        world_id=world_id,
        entry_type=entry_type,
        status=status,
        parent_id=parent_id,
        limit=limit,
        offset=offset
    )

    return entries


@router.get("/worlds/{world_id}/search")
def search_wiki_entries(
    world_id: str,
    q: str = Query(..., min_length=1),
    entry_types: Optional[str] = Query(None, description="Comma-separated list of entry types"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """Search wiki entries by title, content, or aliases"""
    service = WikiService(db)

    types_list = entry_types.split(",") if entry_types else None

    entries = service.search_entries(
        world_id=world_id,
        query=q,
        entry_types=types_list,
        limit=limit
    )

    return [WikiEntryResponse.model_validate(e) for e in entries]


@router.put("/entries/{entry_id}", response_model=WikiEntryResponse)
def update_wiki_entry(
    entry_id: str,
    updates: WikiEntryUpdate,
    db: Session = Depends(get_db)
):
    """Update a wiki entry"""
    service = WikiService(db)

    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    updated = service.update_entry(entry_id, update_dict)

    if not updated:
        raise HTTPException(status_code=404, detail="Wiki entry not found")

    return updated


@router.delete("/entries/{entry_id}")
def delete_wiki_entry(
    entry_id: str,
    db: Session = Depends(get_db)
):
    """Delete a wiki entry"""
    service = WikiService(db)

    if not service.delete_entry(entry_id):
        raise HTTPException(status_code=404, detail="Wiki entry not found")

    return {"status": "deleted", "id": entry_id}


# ==================== Cross-Reference Endpoints ====================

@router.post("/references", response_model=WikiCrossReferenceResponse)
def create_cross_reference(
    ref: WikiCrossReferenceCreate,
    db: Session = Depends(get_db)
):
    """Create a cross-reference between wiki entries"""
    service = WikiService(db)

    created = service.create_reference(
        source_entry_id=ref.source_entry_id,
        target_entry_id=ref.target_entry_id,
        reference_type=ref.reference_type,
        context=ref.context,
        bidirectional=ref.bidirectional,
        created_by="author"
    )

    return created


@router.get("/entries/{entry_id}/references")
def get_entry_references(
    entry_id: str,
    db: Session = Depends(get_db)
):
    """Get all references for a wiki entry"""
    service = WikiService(db)

    refs = service.get_entry_references(entry_id)

    return {
        "outgoing": [WikiCrossReferenceResponse.model_validate(r) for r in refs["outgoing"]],
        "incoming": [WikiCrossReferenceResponse.model_validate(r) for r in refs["incoming"]]
    }


@router.delete("/references/{reference_id}")
def delete_cross_reference(
    reference_id: str,
    db: Session = Depends(get_db)
):
    """Delete a cross-reference"""
    service = WikiService(db)

    if not service.delete_reference(reference_id):
        raise HTTPException(status_code=404, detail="Reference not found")

    return {"status": "deleted", "id": reference_id}


# ==================== Change Queue Endpoints ====================

@router.get("/worlds/{world_id}/changes", response_model=List[WikiChangeResponse])
def get_pending_changes(
    world_id: str,
    wiki_entry_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """Get pending changes in the approval queue"""
    service = WikiService(db)

    changes = service.get_pending_changes(
        world_id=world_id,
        wiki_entry_id=wiki_entry_id,
        limit=limit
    )

    # Resolve entry titles for display
    result = []
    for change in changes:
        resp = WikiChangeResponse.model_validate(change)
        if change.change_type == "create" and change.proposed_entry:
            resp.entry_title = change.proposed_entry.get("title")
            resp.entry_type = change.proposed_entry.get("entry_type")
        elif change.wiki_entry_id:
            entry = db.query(WikiEntry).filter(WikiEntry.id == change.wiki_entry_id).first()
            if entry:
                resp.entry_title = entry.title
                resp.entry_type = entry.entry_type
        result.append(resp)

    return result


@router.post("/changes/{change_id}/approve")
def approve_change(
    change_id: str,
    review: ChangeReviewRequest,
    db: Session = Depends(get_db)
):
    """Approve a pending change"""
    service = WikiService(db)

    result = service.approve_change(change_id, review.reviewer_note)

    if result is None:
        # Check if the change existed at all
        from app.models.wiki import WikiChange as WikiChangeModel
        change = db.query(WikiChangeModel).filter(WikiChangeModel.id == change_id).first()
        if change is None:
            raise HTTPException(status_code=404, detail="Change not found")
        # Change existed but was already processed or was a delete (no entry returned)

    return {
        "status": "approved",
        "change_id": change_id,
        "wiki_entry_id": result.id if result else None
    }


@router.post("/changes/{change_id}/reject")
def reject_change(
    change_id: str,
    review: ChangeReviewRequest,
    db: Session = Depends(get_db)
):
    """Reject a pending change"""
    service = WikiService(db)

    if not service.reject_change(change_id, review.reviewer_note):
        raise HTTPException(status_code=404, detail="Change not found or already processed")

    return {"status": "rejected", "change_id": change_id}


# ==================== Sync Endpoints ====================

@router.post("/sync/manuscript-to-wiki")
def sync_manuscript_to_wiki(
    request: SyncRequest,
    db: Session = Depends(get_db)
):
    """Sync all entities from a manuscript to the world wiki"""
    bridge = WikiCodexBridge(db)

    stats = bridge.bulk_sync_manuscript_to_wiki(
        manuscript_id=request.manuscript_id,
        world_id=request.world_id
    )

    return stats


@router.post("/sync/wiki-to-manuscript")
def sync_wiki_to_manuscript(
    request: SyncRequest,
    db: Session = Depends(get_db)
):
    """Sync wiki entries to a manuscript's codex"""
    bridge = WikiCodexBridge(db)

    stats = bridge.bulk_sync_wiki_to_manuscript(
        world_id=request.world_id,
        manuscript_id=request.manuscript_id,
        entry_types=request.entry_types
    )

    return stats


# ==================== Consistency Engine Endpoints ====================

@router.get("/worlds/{world_id}/characters")
def get_world_characters(
    world_id: str,
    db: Session = Depends(get_db)
):
    """Get all characters in a world"""
    engine = WikiConsistencyEngine(db)
    return engine.get_all_characters(world_id)


@router.get("/worlds/{world_id}/locations")
def get_world_locations(
    world_id: str,
    db: Session = Depends(get_db)
):
    """Get all locations in a world"""
    engine = WikiConsistencyEngine(db)
    return engine.get_all_locations(world_id)


@router.get("/worlds/{world_id}/character/{character_name}")
def get_character_facts(
    world_id: str,
    character_name: str,
    db: Session = Depends(get_db)
):
    """Get all facts about a character"""
    engine = WikiConsistencyEngine(db)
    return engine.get_character_facts(character_name, world_id)


@router.get("/worlds/{world_id}/location/{location_name}")
def get_location_facts(
    world_id: str,
    location_name: str,
    db: Session = Depends(get_db)
):
    """Get all facts about a location"""
    engine = WikiConsistencyEngine(db)
    return engine.get_location_facts(location_name, world_id)


@router.post("/worlds/{world_id}/validate-rules")
def validate_against_world_rules(
    world_id: str,
    text: str = Query(..., description="Text to validate"),
    rule_types: Optional[str] = Query(None, description="Comma-separated list of rule types"),
    db: Session = Depends(get_db)
):
    """Validate text against world rules"""
    engine = WikiConsistencyEngine(db)

    types_list = rule_types.split(",") if rule_types else None

    violations = engine.validate_against_rules(
        text=text,
        world_id=world_id,
        rule_types=types_list
    )

    return {
        "violations": violations,
        "count": len(violations)
    }


# ==================== Culture Endpoints ====================

class CultureLinkCreate(BaseModel):
    entity_entry_id: str
    culture_entry_id: str
    reference_type: str
    context: Optional[str] = None


@router.post("/cultures/link", response_model=WikiCrossReferenceResponse)
def link_entity_to_culture(
    data: CultureLinkCreate,
    db: Session = Depends(get_db)
):
    """Link an entity to a culture with a relationship type"""
    service = CultureService(db)
    ref = service.link_entity_to_culture(
        entity_entry_id=data.entity_entry_id,
        culture_entry_id=data.culture_entry_id,
        reference_type=data.reference_type,
        context=data.context,
    )
    return ref


@router.delete("/cultures/link/{reference_id}")
def unlink_entity_from_culture(
    reference_id: str,
    db: Session = Depends(get_db)
):
    """Remove a culture link"""
    service = CultureService(db)
    if not service.unlink_entity_from_culture(reference_id):
        raise HTTPException(status_code=404, detail="Culture link not found")
    return {"status": "deleted", "id": reference_id}


@router.get("/entries/{entry_id}/cultures")
def get_entity_cultures(
    entry_id: str,
    db: Session = Depends(get_db)
):
    """Get all cultures linked to an entity"""
    service = CultureService(db)
    return service.get_entity_cultures(entry_id)


@router.get("/cultures/{culture_id}/members")
def get_culture_members(
    culture_id: str,
    member_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all members of a culture, optionally filtered by type"""
    service = CultureService(db)
    return service.get_culture_members(culture_id, member_type)


@router.get("/cultures/{culture_id}/children")
def get_culture_children(
    culture_id: str,
    db: Session = Depends(get_db)
):
    """Get hierarchical children of a culture"""
    service = CultureService(db)
    return service.get_culture_children(culture_id)


@router.get("/worlds/{world_id}/cultures")
def get_world_cultures(
    world_id: str,
    db: Session = Depends(get_db)
):
    """Get all cultures in a world with member counts"""
    service = CultureService(db)
    return service.get_world_cultures(world_id)


@router.get("/worlds/{world_id}/characters/{character_name}/cultural-context")
def get_character_cultural_context(
    world_id: str,
    character_name: str,
    db: Session = Depends(get_db)
):
    """Get full cultural context for a character"""
    service = CultureService(db)
    return service.get_character_cultural_context(character_name, world_id)


# ==================== Entry Type Metadata ====================

@router.get("/entry-types")
def get_entry_types():
    """Get available wiki entry types"""
    return [
        {"value": t.value, "label": t.value.replace("_", " ").title()}
        for t in WikiEntryType
    ]


@router.get("/reference-types")
def get_reference_types():
    """Get available cross-reference types"""
    return [
        {"value": t.value, "label": t.value.replace("_", " ").title()}
        for t in WikiReferenceType
    ]


# ==================== Auto-Population Endpoints ====================

class AnalyzeManuscriptRequest(BaseModel):
    manuscript_id: str
    world_id: Optional[str] = None


class AnalyzeChapterRequest(BaseModel):
    chapter_id: str
    world_id: Optional[str] = None


class AutoApproveRequest(BaseModel):
    threshold: float = 0.95


@router.post("/auto-populate/manuscript")
def analyze_manuscript_for_wiki(
    request: AnalyzeManuscriptRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a manuscript for wiki updates.
    Creates proposed changes in the approval queue.
    """
    populator = WikiAutoPopulator(db)

    result = populator.analyze_manuscript(
        manuscript_id=request.manuscript_id,
        world_id=request.world_id
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/auto-populate/chapter")
def analyze_chapter_for_wiki(
    request: AnalyzeChapterRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a single chapter for wiki updates.
    Lightweight analysis for incremental updates.
    """
    populator = WikiAutoPopulator(db)

    result = populator.analyze_chapter(
        chapter_id=request.chapter_id,
        world_id=request.world_id
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/worlds/{world_id}/auto-approve")
def auto_approve_high_confidence(
    world_id: str,
    request: AutoApproveRequest,
    db: Session = Depends(get_db)
):
    """
    Auto-approve changes above the confidence threshold.
    Returns count of approved changes.
    """
    populator = WikiAutoPopulator(db)

    approved_count = populator.auto_approve_high_confidence(
        world_id=world_id,
        threshold=request.threshold
    )

    return {
        "world_id": world_id,
        "threshold": request.threshold,
        "approved_count": approved_count
    }


@router.get("/worlds/{world_id}/pending-summary")
def get_pending_changes_summary(
    world_id: str,
    db: Session = Depends(get_db)
):
    """Get summary of pending changes for a world"""
    populator = WikiAutoPopulator(db)
    return populator.get_pending_changes_summary(world_id)


@router.post("/changes/bulk-approve")
def bulk_approve_changes(
    change_ids: List[str],
    review: ChangeReviewRequest,
    db: Session = Depends(get_db)
):
    """Approve multiple changes at once"""
    service = WikiService(db)
    approved = []
    failed = []

    for change_id in change_ids:
        result = service.approve_change(change_id, review.reviewer_note)
        if result is not None:
            approved.append(change_id)
        else:
            failed.append(change_id)

    return {
        "approved": approved,
        "failed": failed,
        "approved_count": len(approved),
        "failed_count": len(failed)
    }


@router.post("/changes/bulk-reject")
def bulk_reject_changes(
    change_ids: List[str],
    review: ChangeReviewRequest,
    db: Session = Depends(get_db)
):
    """Reject multiple changes at once"""
    service = WikiService(db)
    rejected = []
    failed = []

    for change_id in change_ids:
        if service.reject_change(change_id, review.reviewer_note):
            rejected.append(change_id)
        else:
            failed.append(change_id)

    return {
        "rejected": rejected,
        "failed": failed,
        "rejected_count": len(rejected),
        "failed_count": len(failed)
    }
