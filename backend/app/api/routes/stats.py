"""
Writing Statistics API Routes
Provides endpoints for generating writing recaps
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.writing_stats_service import WritingStatsService

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/recap/{manuscript_id}")
async def get_writing_recap(
    manuscript_id: str,
    timeframe: Optional[str] = 'week',
    db: Session = Depends(get_db)
):
    """
    Generate writing statistics recap for a manuscript

    Args:
        manuscript_id: ID of the manuscript
        timeframe: Time period - 'session', 'day', 'week', 'month', 'all_time'

    Returns:
        Writing statistics for generating recap cards
    """
    try:
        service = WritingStatsService(db)
        stats = await service.generate_session_recap(manuscript_id, timeframe)

        return {
            "success": True,
            "data": stats
        }
    except ValueError as e:
        print(f"ValueError in stats endpoint: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"Exception in stats endpoint: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate stats: {str(e)}")
