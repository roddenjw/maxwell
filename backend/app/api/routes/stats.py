"""
Writing Statistics API Routes
Provides endpoints for generating writing recaps and analytics
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.services.writing_stats_service import WritingStatsService
from app.models.manuscript import Chapter
from app.models.versioning import Snapshot
from sqlalchemy import and_, func

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


@router.get("/analytics/{manuscript_id}")
async def get_analytics_dashboard(
    manuscript_id: str,
    days: Optional[int] = 30,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics data for dashboard

    Args:
        manuscript_id: ID of the manuscript
        days: Number of days to include (default 30)

    Returns:
        Analytics data including daily stats, streaks, and trends
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get all chapters
        chapters = db.query(Chapter).filter(
            and_(
                Chapter.manuscript_id == manuscript_id,
                Chapter.is_folder == False
            )
        ).all()

        # Get snapshots in timeframe
        snapshots = db.query(Snapshot).filter(
            and_(
                Snapshot.manuscript_id == manuscript_id,
                Snapshot.created_at >= start_date,
                Snapshot.created_at <= end_date
            )
        ).order_by(Snapshot.created_at.asc()).all()

        # Calculate daily word counts
        daily_stats = {}
        for snapshot in snapshots:
            date_key = snapshot.created_at.date().isoformat()
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'date': date_key,
                    'word_count': 0,
                    'sessions': 0,
                    'snapshots': []
                }
            daily_stats[date_key]['word_count'] = snapshot.word_count or 0
            daily_stats[date_key]['sessions'] += 1
            daily_stats[date_key]['snapshots'].append({
                'id': snapshot.id,
                'created_at': snapshot.created_at.isoformat(),
                'word_count': snapshot.word_count or 0,
                'label': snapshot.label
            })

        # Convert to list and sort
        daily_data = sorted(daily_stats.values(), key=lambda x: x['date'])

        # Calculate current streak
        current_streak = _calculate_current_streak(snapshots, end_date)

        # Calculate longest streak (last 90 days)
        service = WritingStatsService(db)
        longest_streak = service._calculate_longest_streak(manuscript_id, end_date)

        # Total stats
        total_words = sum(chapter.word_count or 0 for chapter in chapters)
        total_chapters = len(chapters)

        # Calculate words written in timeframe
        words_in_period = 0
        if daily_data:
            # Get earliest snapshot word count in period
            earliest_count = daily_data[0]['word_count'] if daily_data else 0
            latest_count = daily_data[-1]['word_count'] if daily_data else 0
            words_in_period = max(0, latest_count - earliest_count)

        # Recent sessions (last 10)
        recent_sessions = []
        for snapshot in snapshots[-10:]:
            recent_sessions.append({
                'id': snapshot.id,
                'date': snapshot.created_at.isoformat(),
                'word_count': snapshot.word_count or 0,
                'label': snapshot.label,
                'trigger_type': snapshot.trigger_type
            })

        return {
            "success": True,
            "data": {
                "overview": {
                    "total_words": total_words,
                    "total_chapters": total_chapters,
                    "words_this_period": words_in_period,
                    "current_streak": current_streak,
                    "longest_streak": longest_streak,
                    "days_active": len(daily_stats),
                    "total_sessions": len(snapshots)
                },
                "daily_stats": daily_data,
                "recent_sessions": recent_sessions,
                "timeframe": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days
                }
            }
        }

    except Exception as e:
        print(f"Analytics error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


def _calculate_current_streak(snapshots, end_date):
    """Calculate current consecutive writing streak"""
    if not snapshots:
        return 0

    # Get unique writing days
    writing_days = set()
    for snapshot in snapshots:
        writing_days.add(snapshot.created_at.date())

    days_list = sorted(list(writing_days), reverse=True)

    if not days_list:
        return 0

    # Check if most recent day is today or yesterday
    today = end_date.date()
    if days_list[0] < today - timedelta(days=1):
        return 0  # Streak broken

    # Count consecutive days backwards from most recent
    streak = 1
    for i in range(1, len(days_list)):
        if (days_list[i-1] - days_list[i]).days == 1:
            streak += 1
        else:
            break

    return streak
