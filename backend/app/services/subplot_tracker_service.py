"""
Subplot Tracker Service - Track narrative threads through the story.

Analyzes:
- Subplot identification and tracking
- Subplot presence across chapters
- Abandoned and unresolved subplots
- Subplot resolution verification
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import re
import uuid

from app.models.manuscript import Manuscript, Chapter
from app.models.wiki import WikiEntry, WikiEntryType


# ==================== Subplot Types ====================

class SubplotType:
    """Types of subplots"""
    MAIN_PLOT = "main_plot"
    ROMANCE = "romance"
    RIVALRY = "rivalry"
    MYSTERY = "mystery"
    GROWTH = "character_growth"
    FAMILY = "family"
    FRIENDSHIP = "friendship"
    REVENGE = "revenge"
    REDEMPTION = "redemption"
    QUEST = "quest"
    POLITICAL = "political"
    SURVIVAL = "survival"
    THEME = "thematic"
    CUSTOM = "custom"


# Subplot indicators
SUBPLOT_PATTERNS = {
    SubplotType.ROMANCE: [
        r'(?:attracted|attraction)', r'(?:love|loved|loving)',
        r'(?:kiss|kissed)', r'(?:relationship)', r'(?:heart)',
        r'(?:date|dating)', r'(?:boyfriend|girlfriend)'
    ],
    SubplotType.RIVALRY: [
        r'(?:rival|rivalry)', r'(?:compete|competition)',
        r'(?:better\s+than)', r'(?:defeat|beat)\s+(?:him|her|them)',
        r'(?:one-up)', r'(?:prove\s+(?:himself|herself))'
    ],
    SubplotType.MYSTERY: [
        r'(?:secret|secrets)', r'(?:clue|clues)',
        r'(?:hidden)', r'(?:discover)', r'(?:truth)',
        r'(?:investigation|investigate)', r'(?:mystery)'
    ],
    SubplotType.GROWTH: [
        r'(?:learn|learned|learning)', r'(?:grow|growth)',
        r'(?:change|changed|changing)', r'(?:overcome)',
        r'(?:realize|realized)', r'(?:confidence)'
    ],
    SubplotType.FAMILY: [
        r'(?:family|families)', r'(?:father|mother|parent)',
        r'(?:brother|sister|sibling)', r'(?:son|daughter)',
        r'(?:inheritance)', r'(?:legacy)'
    ],
    SubplotType.FRIENDSHIP: [
        r'(?:friend|friends|friendship)', r'(?:trust|trusted)',
        r'(?:loyal|loyalty)', r'(?:together)',
        r'(?:support)', r'(?:betray|betrayal)'
    ],
    SubplotType.REVENGE: [
        r'(?:revenge)', r'(?:avenge|vengeance)',
        r'(?:pay\s+for)', r'(?:payback)', r'(?:get\s+back\s+at)'
    ],
    SubplotType.REDEMPTION: [
        r'(?:redemption|redeem)', r'(?:forgive|forgiveness)',
        r'(?:atone|atonement)', r'(?:make\s+(?:up|amends))',
        r'(?:second\s+chance)'
    ],
    SubplotType.QUEST: [
        r'(?:quest)', r'(?:mission)', r'(?:journey)',
        r'(?:find|search)', r'(?:retrieve)', r'(?:artifact)'
    ],
    SubplotType.POLITICAL: [
        r'(?:power)', r'(?:throne)', r'(?:kingdom)',
        r'(?:alliance)', r'(?:war)', r'(?:politics|political)',
        r'(?:council)', r'(?:treaty)'
    ],
    SubplotType.SURVIVAL: [
        r'(?:survive|survival)', r'(?:escape)',
        r'(?:hunt(?:ed)?)', r'(?:danger)', r'(?:threat)'
    ],
}


class SubplotTrackerService:
    """Tracks subplot threads through a manuscript"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Subplot Detection ====================

    def detect_subplots_in_text(
        self,
        text: str,
        characters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect potential subplot threads in a text passage.

        Returns:
        {
            "detected_types": List[str],
            "type_scores": Dict[str, float],
            "character_associations": Dict[str, List[str]]
        }
        """
        if not text or len(text.strip()) < 100:
            return {
                "detected_types": [],
                "type_scores": {},
                "character_associations": {}
            }

        text_lower = text.lower()
        type_scores = {}
        char_associations = {}

        # Score each subplot type
        for subplot_type, patterns in SUBPLOT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                score += len(matches)

            if score > 0:
                type_scores[subplot_type] = score

        if not type_scores:
            return {
                "detected_types": [],
                "type_scores": {},
                "character_associations": {}
            }

        # Normalize scores
        total = sum(type_scores.values())
        normalized = {k: round(v / total, 2) for k, v in type_scores.items()}

        # Get significant types (> 15% of signals)
        detected = [t for t, s in normalized.items() if s > 0.15]

        # Associate with characters if provided
        if characters:
            for char in characters:
                char_lower = char.lower()
                if char_lower in text_lower:
                    char_associations[char] = []
                    # Find which subplots mention this character nearby
                    for subplot_type, patterns in SUBPLOT_PATTERNS.items():
                        if subplot_type not in detected:
                            continue
                        for pattern in patterns:
                            # Look for character name within 100 chars of pattern
                            for match in re.finditer(pattern, text_lower):
                                start = max(0, match.start() - 100)
                                end = min(len(text_lower), match.end() + 100)
                                if char_lower in text_lower[start:end]:
                                    if subplot_type not in char_associations[char]:
                                        char_associations[char].append(subplot_type)

        return {
            "detected_types": detected,
            "type_scores": normalized,
            "character_associations": char_associations
        }

    # ==================== Chapter Analysis ====================

    def analyze_chapter(
        self,
        chapter_id: str,
        characters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze subplot presence in a chapter"""
        chapter = self.db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return {"error": "Chapter not found"}

        if not chapter.content:
            return {"error": "No content to analyze"}

        # Get characters if not provided
        if not characters:
            from app.models.entity import Entity
            entities = self.db.query(Entity).filter(
                Entity.manuscript_id == chapter.manuscript_id,
                Entity.entity_type == "CHARACTER"
            ).all()
            characters = [e.name for e in entities]

        detection = self.detect_subplots_in_text(chapter.content, characters)

        return {
            "chapter_id": chapter_id,
            "chapter_title": chapter.title,
            "chapter_index": chapter.order_index,
            "subplots_present": detection["detected_types"],
            "subplot_scores": detection["type_scores"],
            "character_associations": detection["character_associations"],
            "analyzed_at": datetime.utcnow().isoformat()
        }

    # ==================== Manuscript Analysis ====================

    def analyze_manuscript(
        self,
        manuscript_id: str
    ) -> Dict[str, Any]:
        """
        Analyze subplot threads across entire manuscript.

        Tracks:
        - Which subplots appear in which chapters
        - Abandoned subplots (disappear mid-story)
        - Unresolved subplots (still active at end)
        """
        chapters = self.db.query(Chapter).filter(
            Chapter.manuscript_id == manuscript_id,
            Chapter.document_type == "CHAPTER"
        ).order_by(Chapter.order_index).all()

        if not chapters:
            return {"error": "No chapters found"}

        # Get characters for association tracking
        from app.models.entity import Entity
        entities = self.db.query(Entity).filter(
            Entity.manuscript_id == manuscript_id,
            Entity.entity_type == "CHARACTER"
        ).all()
        characters = [e.name for e in entities]

        chapter_analyses = []
        subplot_timeline = {}  # subplot_type -> list of chapter indices
        subplot_characters = {}  # subplot_type -> set of characters

        for chapter in chapters:
            analysis = self.analyze_chapter(chapter.id, characters)
            if "error" not in analysis:
                chapter_analyses.append(analysis)

                # Track subplot presence
                for subplot in analysis.get("subplots_present", []):
                    if subplot not in subplot_timeline:
                        subplot_timeline[subplot] = []
                        subplot_characters[subplot] = set()

                    subplot_timeline[subplot].append(chapter.order_index)

                    # Track character associations
                    for char, assoc_subplots in analysis.get("character_associations", {}).items():
                        if subplot in assoc_subplots:
                            subplot_characters[subplot].add(char)

        # Analyze subplot health
        total_chapters = len(chapters)
        subplot_health = {}

        for subplot, chapter_indices in subplot_timeline.items():
            health = self._analyze_subplot_health(
                chapter_indices,
                total_chapters,
                subplot
            )
            subplot_health[subplot] = {
                **health,
                "characters": list(subplot_characters.get(subplot, [])),
                "first_chapter": min(chapter_indices) if chapter_indices else None,
                "last_chapter": max(chapter_indices) if chapter_indices else None,
                "appearance_count": len(chapter_indices)
            }

        # Identify issues
        abandoned = [s for s, h in subplot_health.items() if h["status"] == "abandoned"]
        unresolved = [s for s, h in subplot_health.items() if h["status"] == "unresolved"]

        return {
            "manuscript_id": manuscript_id,
            "total_chapters": total_chapters,
            "subplots_found": len(subplot_timeline),
            "subplot_health": subplot_health,
            "abandoned_subplots": abandoned,
            "unresolved_subplots": unresolved,
            "chapter_analyses": chapter_analyses,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _analyze_subplot_health(
        self,
        chapter_indices: List[int],
        total_chapters: int,
        subplot_type: str
    ) -> Dict[str, Any]:
        """Analyze the health of a subplot thread"""
        if not chapter_indices:
            return {"status": "not_found", "issues": []}

        first = min(chapter_indices)
        last = max(chapter_indices)
        appearances = len(chapter_indices)

        issues = []

        # Check for abandonment (doesn't appear in final third)
        final_third_start = total_chapters * 2 // 3
        if last < final_third_start and first < total_chapters // 2:
            # Started in first half, disappeared before final third
            status = "abandoned"
            issues.append(f"Last appears in chapter {last + 1}, missing from final third")
        # Check for unresolved (still very active at end but no resolution signal)
        elif last >= total_chapters - 2 and appearances > 3:
            # Active at the end with many appearances
            status = "unresolved"
            issues.append("Still active at story end - may need resolution")
        # Check for sporadic appearance
        elif appearances < (last - first + 1) * 0.3:
            status = "sporadic"
            issues.append(f"Only appears in {appearances} of {last - first + 1} chapters it spans")
        else:
            status = "healthy"

        # Calculate presence percentage
        presence_pct = round(appearances / total_chapters * 100, 1)

        return {
            "status": status,
            "presence_percentage": presence_pct,
            "issues": issues,
            "chapter_spread": last - first + 1
        }

    # ==================== Subplot Suggestions ====================

    def get_subplot_suggestions(
        self,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate suggestions for subplot management"""
        suggestions = []

        # Abandoned subplots
        for subplot in analysis.get("abandoned_subplots", []):
            health = analysis.get("subplot_health", {}).get(subplot, {})
            suggestions.append({
                "type": "abandoned_subplot",
                "severity": "high",
                "title": f"Abandoned Subplot: {self._subplot_label(subplot)}",
                "description": f"This subplot last appears in chapter {health.get('last_chapter', 'unknown') + 1}",
                "fix": "Either resolve this subplot before it disappears, or remove early references if it's not needed"
            })

        # Unresolved subplots
        for subplot in analysis.get("unresolved_subplots", []):
            health = analysis.get("subplot_health", {}).get(subplot, {})
            suggestions.append({
                "type": "unresolved_subplot",
                "severity": "medium",
                "title": f"Unresolved Subplot: {self._subplot_label(subplot)}",
                "description": f"Active through {health.get('appearance_count', '?')} chapters but may need resolution",
                "fix": "Consider adding a resolution scene, or clarify that this thread intentionally continues"
            })

        # Sporadic subplots
        for subplot, health in analysis.get("subplot_health", {}).items():
            if health.get("status") == "sporadic":
                suggestions.append({
                    "type": "sporadic_subplot",
                    "severity": "low",
                    "title": f"Sporadic Subplot: {self._subplot_label(subplot)}",
                    "description": f"Only {health.get('presence_percentage', '?')}% presence across chapters it spans",
                    "fix": "Consider weaving this subplot more consistently through the narrative"
                })

        return suggestions

    def _subplot_label(self, subplot_type: str) -> str:
        """Get human-readable subplot label"""
        labels = {
            SubplotType.MAIN_PLOT: "Main Plot",
            SubplotType.ROMANCE: "Romance",
            SubplotType.RIVALRY: "Rivalry",
            SubplotType.MYSTERY: "Mystery",
            SubplotType.GROWTH: "Character Growth",
            SubplotType.FAMILY: "Family",
            SubplotType.FRIENDSHIP: "Friendship",
            SubplotType.REVENGE: "Revenge",
            SubplotType.REDEMPTION: "Redemption",
            SubplotType.QUEST: "Quest",
            SubplotType.POLITICAL: "Political",
            SubplotType.SURVIVAL: "Survival",
            SubplotType.THEME: "Thematic",
            SubplotType.CUSTOM: "Custom",
        }
        return labels.get(subplot_type, subplot_type.replace('_', ' ').title())

    # ==================== Wiki Integration ====================

    def sync_subplots_to_wiki(
        self,
        manuscript_id: str,
        world_id: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create wiki entries for identified subplots"""
        from app.services.wiki_service import WikiService

        wiki_service = WikiService(self.db)
        created = []
        skipped = []

        for subplot_type, health in analysis.get("subplot_health", {}).items():
            if health.get("status") == "abandoned":
                continue  # Don't create wiki entries for abandoned subplots

            # Check if entry already exists
            existing = self.db.query(WikiEntry).filter(
                WikiEntry.world_id == world_id,
                WikiEntry.entry_type == "subplot",
                WikiEntry.title.ilike(f"%{self._subplot_label(subplot_type)}%")
            ).first()

            if existing:
                skipped.append(subplot_type)
                continue

            # Create wiki entry
            entry = wiki_service.create_entry(
                world_id=world_id,
                entry_type="subplot",
                title=f"{self._subplot_label(subplot_type)} Subplot",
                summary=f"A {self._subplot_label(subplot_type).lower()} subplot thread spanning {health.get('chapter_spread', '?')} chapters",
                structured_data={
                    "subplot_type": subplot_type,
                    "status": health.get("status"),
                    "characters": health.get("characters", []),
                    "first_chapter": health.get("first_chapter"),
                    "last_chapter": health.get("last_chapter"),
                    "presence_percentage": health.get("presence_percentage")
                },
                created_by="ai"
            )
            created.append({
                "subplot_type": subplot_type,
                "wiki_entry_id": entry.id
            })

        return {
            "created": created,
            "skipped": skipped,
            "total_created": len(created)
        }
