"""
Manuscript Aggregation Service
Handles word count aggregation and synchronization between manuscripts, chapters, and plot beats
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import logging

from app.models.manuscript import Manuscript, Chapter
from app.models.outline import PlotBeat

logger = logging.getLogger(__name__)


class ManuscriptAggregationService:
    """Service for aggregating manuscript-level metrics from chapters"""

    @staticmethod
    def update_manuscript_word_count(db: Session, manuscript_id: str) -> int:
        """
        Recalculate and update manuscript total word count from all chapters

        Sums word_count from all non-folder chapters in the manuscript.
        Updates Manuscript.word_count in database.

        Args:
            db: Database session
            manuscript_id: UUID of manuscript to update

        Returns:
            New total word count

        Raises:
            ValueError: If manuscript not found
        """
        # Get manuscript
        manuscript = db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()
        if not manuscript:
            raise ValueError(f"Manuscript not found: {manuscript_id}")

        # Sum word counts from all non-folder chapters
        # Use SQL aggregate for efficiency (single query)
        total_word_count = db.query(func.sum(Chapter.word_count)).filter(
            Chapter.manuscript_id == manuscript_id,
            Chapter.is_folder == 0  # Exclude folders
        ).scalar() or 0

        # Update manuscript
        manuscript.word_count = total_word_count
        db.commit()

        logger.info(f"Updated manuscript {manuscript_id} word count: {total_word_count}")
        return total_word_count

    @staticmethod
    def sync_plot_beat_word_count(db: Session, chapter_id: str) -> None:
        """
        Sync PlotBeat.actual_word_count for any beat linked to this chapter

        When a chapter's content changes, update any plot beat that references it.
        A chapter can be linked to at most one plot beat via PlotBeat.chapter_id.

        Args:
            db: Database session
            chapter_id: UUID of chapter that was updated
        """
        # Get chapter
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            logger.warning(f"Chapter not found for beat sync: {chapter_id}")
            return

        # Find any plot beat linked to this chapter
        plot_beats = db.query(PlotBeat).filter(PlotBeat.chapter_id == chapter_id).all()

        if not plot_beats:
            # No beats linked - this is normal, not all chapters are linked to beats
            return

        # Update actual_word_count for each linked beat
        for beat in plot_beats:
            old_count = beat.actual_word_count
            beat.actual_word_count = chapter.word_count

            logger.info(
                f"Synced beat {beat.id} ({beat.beat_name}) word count: "
                f"{old_count} → {chapter.word_count}"
            )

        db.commit()

    @staticmethod
    def sync_plot_beat_on_link_change(
        db: Session,
        beat_id: str,
        old_chapter_id: Optional[str],
        new_chapter_id: Optional[str]
    ) -> None:
        """
        Sync PlotBeat.actual_word_count when chapter link changes

        Handles three cases:
        1. Linking to new chapter: Set actual_word_count from chapter
        2. Unlinking from chapter: Reset actual_word_count to 0
        3. Changing chapter link: Update from new chapter

        Args:
            db: Database session
            beat_id: UUID of plot beat being updated
            old_chapter_id: Previous chapter_id (None if newly linking)
            new_chapter_id: New chapter_id (None if unlinking)
        """
        beat = db.query(PlotBeat).filter(PlotBeat.id == beat_id).first()
        if not beat:
            logger.warning(f"Beat not found for link sync: {beat_id}")
            return

        if new_chapter_id:
            # Linking to a chapter - get its word count
            chapter = db.query(Chapter).filter(Chapter.id == new_chapter_id).first()
            if chapter:
                beat.actual_word_count = chapter.word_count
                logger.info(
                    f"Linked beat {beat_id} to chapter {new_chapter_id}, "
                    f"set word count to {chapter.word_count}"
                )
            else:
                logger.warning(f"Chapter not found for linking: {new_chapter_id}")
                beat.actual_word_count = 0
        else:
            # Unlinking from chapter - reset to 0
            beat.actual_word_count = 0
            logger.info(f"Unlinked beat {beat_id} from chapter, reset word count to 0")

        db.commit()


# Singleton instance
manuscript_aggregation_service = ManuscriptAggregationService()
