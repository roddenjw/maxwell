"""
API routes for versioning (Time Machine)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import version_service

router = APIRouter(prefix="/api/versioning", tags=["versioning"])


# Request/Response Models
class CreateSnapshotRequest(BaseModel):
    manuscript_id: str
    trigger_type: str  # MANUAL, AUTO, CHAPTER_COMPLETE, PRE_GENERATION, SESSION_END
    label: Optional[str] = ""
    description: Optional[str] = ""
    word_count: int = 0


class RestoreSnapshotRequest(BaseModel):
    manuscript_id: str
    snapshot_id: str
    create_backup: bool = True


class GetDiffRequest(BaseModel):
    manuscript_id: str
    snapshot_id_old: str
    snapshot_id_new: str


class CreateVariantRequest(BaseModel):
    manuscript_id: str
    scene_id: str
    variant_label: str
    base_snapshot_id: Optional[str] = None


class MergeVariantRequest(BaseModel):
    manuscript_id: str
    variant_branch: str


# Routes
@router.post("/snapshots")
async def create_snapshot(request: CreateSnapshotRequest):
    """
    Create a snapshot (version) of ALL chapters in the manuscript

    Args:
        request: Snapshot creation details

    Returns:
        Created snapshot metadata
    """
    try:
        snapshot = version_service.create_snapshot(
            manuscript_id=request.manuscript_id,
            trigger_type=request.trigger_type,
            label=request.label,
            description=request.description,
            word_count=request.word_count
        )

        return {
            "success": True,
            "data": {
                "id": snapshot.id,
                "commit_hash": snapshot.commit_hash,
                "label": snapshot.label,
                "description": snapshot.description,
                "auto_summary": snapshot.auto_summary or "",
                "trigger_type": snapshot.trigger_type,
                "word_count": snapshot.word_count,
                "created_at": snapshot.created_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/snapshots/{manuscript_id}")
async def get_history(manuscript_id: str):
    """
    Get version history for a manuscript

    Args:
        manuscript_id: ID of the manuscript

    Returns:
        List of snapshots
    """
    try:
        history = version_service.get_history(manuscript_id)
        return {
            "success": True,
            "data": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore")
async def restore_snapshot(request: RestoreSnapshotRequest):
    """
    Restore ALL chapters to a specific snapshot state

    Args:
        request: Restore details

    Returns:
        Restoration info including number of chapters restored
    """
    try:
        result = version_service.restore_snapshot(
            manuscript_id=request.manuscript_id,
            snapshot_id=request.snapshot_id,
            create_backup=request.create_backup
        )

        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/diff")
async def get_diff(request: GetDiffRequest):
    """
    Get diff between two snapshots

    Args:
        request: Diff request details

    Returns:
        Diff information
    """
    try:
        diff = version_service.get_diff(
            manuscript_id=request.manuscript_id,
            snapshot_id_old=request.snapshot_id_old,
            snapshot_id_new=request.snapshot_id_new
        )

        return {
            "success": True,
            "data": diff
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/variants/create")
async def create_variant(request: CreateVariantRequest):
    """
    Create a variant branch for multiverse exploration

    Args:
        request: Variant creation details

    Returns:
        Branch name created
    """
    try:
        branch_name = version_service.create_variant_branch(
            manuscript_id=request.manuscript_id,
            scene_id=request.scene_id,
            variant_label=request.variant_label,
            base_snapshot_id=request.base_snapshot_id
        )

        return {
            "success": True,
            "data": {
                "branch_name": branch_name
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/variants/merge")
async def merge_variant(request: MergeVariantRequest):
    """
    Merge a variant branch back to main

    Args:
        request: Merge details

    Returns:
        Success status
    """
    try:
        success = version_service.merge_variant(
            manuscript_id=request.manuscript_id,
            variant_branch=request.variant_branch
        )

        if not success:
            raise HTTPException(
                status_code=409,
                detail="Merge conflict detected. Please resolve manually."
            )

        return {
            "success": True,
            "message": "Variant merged successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/snapshots/{snapshot_id}")
async def delete_snapshot(snapshot_id: str):
    """
    Delete a snapshot from database (Git commit remains)

    Args:
        snapshot_id: ID of the snapshot to delete

    Returns:
        Success status
    """
    try:
        version_service.delete_snapshot(snapshot_id)
        return {
            "success": True,
            "message": "Snapshot deleted"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
