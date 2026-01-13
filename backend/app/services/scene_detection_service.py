"""
Scene Detection Service
Detects which scene a cursor position falls into based on ChapterScene boundaries
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.scene import ChapterScene
from app.models.manuscript import Chapter


class SceneDetectionService:
    """Service for detecting current scene based on cursor position in a chapter"""

    @staticmethod
    def get_scene_at_position(
        db: Session,
        chapter_id: str,
        cursor_position: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get scene metadata for the scene containing the cursor position.

        Args:
            db: Database session
            chapter_id: Chapter ID
            cursor_position: Character offset in chapter content (0-indexed)

        Returns:
            Scene metadata dict with:
            - scene_id: Scene UUID
            - sequence_order: 0-indexed scene number within chapter
            - start_position: Character offset where scene starts
            - end_position: Character offset where scene ends
            - word_count: Scene word count
            - summary: Scene summary (if available)
            - total_scenes_in_chapter: Total number of scenes in this chapter
            Or None if no scenes exist in the chapter
        """
        # Query all scenes for the chapter, ordered by sequence
        scenes = (
            db.query(ChapterScene)
            .filter(ChapterScene.chapter_id == chapter_id)
            .order_by(ChapterScene.sequence_order)
            .all()
        )

        # If no scenes exist, return None
        if not scenes:
            return None

        # Find the scene containing the cursor position
        current_scene = None

        for scene in scenes:
            # Scene boundaries: start_position <= cursor_position <= end_position
            # Note: We use <= for end_position to include the character at that position
            if scene.start_position <= cursor_position <= scene.end_position:
                current_scene = scene
                break

        # If cursor is before the first scene, return the first scene
        if current_scene is None and scenes:
            if cursor_position < scenes[0].start_position:
                current_scene = scenes[0]
            # If cursor is after the last scene, return the last scene
            elif cursor_position > scenes[-1].end_position:
                current_scene = scenes[-1]

        # Build response dictionary
        if current_scene:
            return {
                "scene_id": current_scene.id,
                "sequence_order": current_scene.sequence_order,
                "start_position": current_scene.start_position,
                "end_position": current_scene.end_position,
                "word_count": current_scene.word_count,
                "summary": current_scene.summary,
                "title": current_scene.title,
                "total_scenes_in_chapter": len(scenes),
            }

        return None


# Global instance
scene_detection_service = SceneDetectionService()
