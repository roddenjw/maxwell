"""
Scene Purpose Service - Analyze and classify scene purposes.

Identifies:
- Primary purpose of each scene
- Scenes lacking clear purpose
- Missing scene types for genre
- Multi-purpose scenes
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import re
import uuid

from app.models.manuscript import Chapter, Scene
from app.services.nlp_service import nlp_service


# ==================== Scene Purpose Types ====================

class ScenePurpose:
    CHARACTER_INTRO = "character_introduction"
    RELATIONSHIP_DEV = "relationship_development"
    PLOT_ADVANCE = "plot_advancement"
    WORLD_EXPO = "world_exposition"
    TENSION_BUILD = "tension_building"
    CONFLICT_RESOLUTION = "conflict_resolution"
    REVELATION = "revelation_twist"
    EMOTIONAL_BEAT = "emotional_beat"
    ACTION_SEQUENCE = "action_sequence"
    DIALOGUE_HEAVY = "dialogue_exchange"
    TRANSITION = "transition"
    CLIMAX = "climax"
    SETUP = "setup_payoff"
    BACKSTORY = "backstory"


# Scene purpose indicators (patterns that suggest purpose)
PURPOSE_PATTERNS = {
    ScenePurpose.CHARACTER_INTRO: [
        r'first\s+(?:met|saw|encountered)',
        r'introduced\s+(?:himself|herself|themselves)',
        r'this\s+was\s+[A-Z][a-z]+',
        r'new\s+(?:face|arrival|stranger)',
        r'stepped\s+(?:into|through)\s+(?:the\s+)?(?:room|door|entrance)',
    ],
    ScenePurpose.RELATIONSHIP_DEV: [
        r'(?:smiled|laughed)\s+(?:at|with)\s+(?:each|one)\s+other',
        r'held\s+(?:hands|her|his)',
        r'trust(?:ed)?',
        r'forgive|forgave',
        r'embrace[d]?',
        r'kiss(?:ed)?',
        r'confess(?:ed)?',
        r'bond(?:ed)?',
        r'friend(?:ship)?',
    ],
    ScenePurpose.PLOT_ADVANCE: [
        r'discover(?:ed)?',
        r'learn(?:ed|ing)?\s+that',
        r'found\s+(?:out|the)',
        r'reveal(?:ed)?',
        r'mission|quest|goal',
        r'plan(?:ned)?',
        r'decided',
        r'must\s+(?:go|find|stop)',
    ],
    ScenePurpose.WORLD_EXPO: [
        r'(?:this|the)\s+(?:world|land|kingdom|realm)',
        r'(?:laws?|rules?)\s+(?:of|that)',
        r'history\s+(?:of|showed)',
        r'tradition',
        r'ancient',
        r'legend',
        r'customs?',
        r'society',
    ],
    ScenePurpose.TENSION_BUILD: [
        r'danger',
        r'threat(?:en)?',
        r'worried|worry',
        r'fear(?:ed)?',
        r'dark(?:ness)?',
        r'something\s+(?:was|felt)\s+wrong',
        r'watch(?:ed|ing)',
        r'wait(?:ed|ing)',
        r'nervous',
        r'approaching',
    ],
    ScenePurpose.CONFLICT_RESOLUTION: [
        r'finally',
        r'at\s+last',
        r'resolved',
        r'peace',
        r'agreed',
        r'settled',
        r'over\s+(?:now|at\s+last)',
        r'forgave',
        r'reconcil',
    ],
    ScenePurpose.REVELATION: [
        r'the\s+truth',
        r'secret',
        r'all\s+along',
        r'real(?:ized|ly)',
        r'(?:was|were)\s+actually',
        r'never\s+(?:knew|expected)',
        r'shock(?:ed)?',
        r'couldn\'t\s+believe',
        r'twist(?:ed)?',
    ],
    ScenePurpose.EMOTIONAL_BEAT: [
        r'tears?',
        r'cried|cry',
        r'sobbed?',
        r'heart\s+(?:broke|ached|sank)',
        r'overwhelm(?:ed)?',
        r'grief',
        r'joy(?:ful)?',
        r'happiness',
        r'loved?',
        r'mourn(?:ed|ing)?',
    ],
    ScenePurpose.ACTION_SEQUENCE: [
        r'fight(?:ing)?',
        r'battle',
        r'sword|blade|weapon',
        r'attack(?:ed)?',
        r'dodg(?:ed|ing)',
        r'struck|strike',
        r'ran|run',
        r'chase[d]?',
        r'explod(?:ed|ing)',
    ],
    ScenePurpose.DIALOGUE_HEAVY: [
        r'\"[^\"]+\"\s+(?:he|she|they)\s+(?:said|asked|replied)',
        r'discussion',
        r'argued?',
        r'talk(?:ed|ing)',
        r'conversation',
    ],
    ScenePurpose.CLIMAX: [
        r'final\s+(?:battle|confrontation|moment)',
        r'everything\s+(?:came|led)\s+to\s+this',
        r'now\s+or\s+never',
        r'last\s+chance',
        r'showdown',
        r'face(?:d)?\s+(?:off|each\s+other)',
    ],
    ScenePurpose.BACKSTORY: [
        r'years?\s+ago',
        r'back\s+(?:then|when)',
        r'remember(?:ed)?',
        r'memory|memories',
        r'used\s+to',
        r'once\s+(?:was|were|upon)',
        r'childhood',
        r'before\s+(?:all|this|everything)',
    ],
}

# Genre-expected scene types
GENRE_SCENE_EXPECTATIONS = {
    "romance": [
        ScenePurpose.RELATIONSHIP_DEV,
        ScenePurpose.EMOTIONAL_BEAT,
        ScenePurpose.CONFLICT_RESOLUTION,
        ScenePurpose.REVELATION,
    ],
    "mystery": [
        ScenePurpose.REVELATION,
        ScenePurpose.TENSION_BUILD,
        ScenePurpose.PLOT_ADVANCE,
        ScenePurpose.DIALOGUE_HEAVY,
    ],
    "fantasy": [
        ScenePurpose.WORLD_EXPO,
        ScenePurpose.ACTION_SEQUENCE,
        ScenePurpose.PLOT_ADVANCE,
        ScenePurpose.CHARACTER_INTRO,
    ],
    "thriller": [
        ScenePurpose.TENSION_BUILD,
        ScenePurpose.ACTION_SEQUENCE,
        ScenePurpose.REVELATION,
        ScenePurpose.CLIMAX,
    ],
    "literary": [
        ScenePurpose.EMOTIONAL_BEAT,
        ScenePurpose.CHARACTER_INTRO,
        ScenePurpose.RELATIONSHIP_DEV,
        ScenePurpose.BACKSTORY,
    ],
}


class ScenePurposeService:
    """Analyzes and classifies scene purposes"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Purpose Detection ====================

    def detect_scene_purpose(self, text: str) -> Dict[str, Any]:
        """
        Detect the primary purpose(s) of a scene.

        Returns:
        {
            "primary_purpose": str,
            "secondary_purposes": List[str],
            "purpose_scores": Dict[str, float],
            "confidence": float,
            "is_purposeless": bool
        }
        """
        if not text or len(text.strip()) < 50:
            return {
                "primary_purpose": None,
                "secondary_purposes": [],
                "purpose_scores": {},
                "confidence": 0.0,
                "is_purposeless": True
            }

        text_lower = text.lower()
        purpose_scores = {}

        # Score each purpose type
        for purpose, patterns in PURPOSE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                score += len(matches)

            if score > 0:
                purpose_scores[purpose] = score

        if not purpose_scores:
            return {
                "primary_purpose": None,
                "secondary_purposes": [],
                "purpose_scores": {},
                "confidence": 0.0,
                "is_purposeless": True,
                "suggestion": "Consider adding clearer purpose markers to this scene"
            }

        # Normalize scores
        total = sum(purpose_scores.values())
        normalized = {k: round(v / total, 2) for k, v in purpose_scores.items()}

        # Sort by score
        sorted_purposes = sorted(normalized.items(), key=lambda x: x[1], reverse=True)

        primary = sorted_purposes[0]
        secondary = [p[0] for p in sorted_purposes[1:4] if p[1] > 0.15]

        return {
            "primary_purpose": primary[0],
            "primary_confidence": primary[1],
            "secondary_purposes": secondary,
            "purpose_scores": normalized,
            "confidence": primary[1],
            "is_purposeless": primary[1] < 0.2
        }

    # ==================== Scene Analysis ====================

    def analyze_scene(self, scene_text: str, scene_title: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a single scene for purpose and quality"""
        purpose_info = self.detect_scene_purpose(scene_text)

        # Calculate word count
        word_count = len(scene_text.split())

        # Detect if scene is too short or too long
        length_issue = None
        if word_count < 200:
            length_issue = "Scene is very short - may lack development"
        elif word_count > 5000:
            length_issue = "Scene is very long - consider splitting"

        # Check for dialogue balance
        dialogue_lines = len(re.findall(r'\"[^\"]+\"', scene_text))
        total_lines = max(1, len([l for l in scene_text.split('\n') if l.strip()]))
        dialogue_ratio = dialogue_lines / total_lines

        dialogue_note = None
        if dialogue_ratio < 0.1 and purpose_info.get('primary_purpose') != ScenePurpose.ACTION_SEQUENCE:
            dialogue_note = "Scene has minimal dialogue - consider adding character interaction"
        elif dialogue_ratio > 0.8:
            dialogue_note = "Scene is dialogue-heavy - consider adding action beats"

        return {
            "title": scene_title,
            "word_count": word_count,
            "purpose": purpose_info,
            "length_issue": length_issue,
            "dialogue_ratio": round(dialogue_ratio, 2),
            "dialogue_note": dialogue_note,
            "is_purposeless": purpose_info.get('is_purposeless', False)
        }

    def analyze_chapter(self, chapter_id: str) -> Dict[str, Any]:
        """Analyze a chapter by splitting into scenes"""
        chapter = self.db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return {"error": "Chapter not found"}

        if not chapter.content:
            return {"error": "No content to analyze"}

        # Split into scenes (using common scene break patterns)
        scene_break_pattern = r'\n\s*(?:\*\s*\*\s*\*|\#\s*\#\s*\#|~~~)\s*\n'
        scenes = re.split(scene_break_pattern, chapter.content)

        # If no scene breaks, treat entire chapter as one scene
        if len(scenes) == 1:
            scenes = [chapter.content]

        scene_analyses = []
        purposes_found = {}
        purposeless_count = 0

        for i, scene_text in enumerate(scenes):
            if len(scene_text.strip()) < 50:
                continue

            analysis = self.analyze_scene(scene_text, f"Scene {i + 1}")
            scene_analyses.append(analysis)

            # Track purposes
            primary = analysis['purpose'].get('primary_purpose')
            if primary:
                purposes_found[primary] = purposes_found.get(primary, 0) + 1

            if analysis.get('is_purposeless'):
                purposeless_count += 1

        return {
            "chapter_id": chapter_id,
            "chapter_title": chapter.title,
            "total_scenes": len(scene_analyses),
            "purposes_found": purposes_found,
            "purposeless_scenes": purposeless_count,
            "scene_analyses": scene_analyses,
            "has_issues": purposeless_count > 0,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def analyze_manuscript(
        self,
        manuscript_id: str,
        genre: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze entire manuscript for scene purposes"""
        # Get manuscript genre if not provided
        from app.models.manuscript import Manuscript
        manuscript = self.db.query(Manuscript).filter(Manuscript.id == manuscript_id).first()

        if not manuscript:
            return {"error": "Manuscript not found"}

        if not genre:
            genre = manuscript.genre.lower() if manuscript.genre else None

        chapters = self.db.query(Chapter).filter(
            Chapter.manuscript_id == manuscript_id,
            Chapter.document_type == "CHAPTER"
        ).order_by(Chapter.order_index).all()

        if not chapters:
            return {"error": "No chapters found"}

        chapter_analyses = []
        all_purposes = {}
        total_purposeless = 0
        total_scenes = 0

        for chapter in chapters:
            analysis = self.analyze_chapter(chapter.id)
            if 'error' not in analysis:
                chapter_analyses.append(analysis)
                total_scenes += analysis.get('total_scenes', 0)
                total_purposeless += analysis.get('purposeless_scenes', 0)

                for purpose, count in analysis.get('purposes_found', {}).items():
                    all_purposes[purpose] = all_purposes.get(purpose, 0) + count

        # Check for missing genre-expected purposes
        missing_purposes = []
        if genre and genre in GENRE_SCENE_EXPECTATIONS:
            expected = GENRE_SCENE_EXPECTATIONS[genre]
            for purpose in expected:
                if purpose not in all_purposes or all_purposes[purpose] < 2:
                    missing_purposes.append({
                        "purpose": purpose,
                        "label": self._get_purpose_label(purpose),
                        "suggestion": f"Consider adding more {self._get_purpose_label(purpose).lower()} scenes"
                    })

        # Calculate purpose distribution
        total_counted = sum(all_purposes.values())
        purpose_distribution = {
            k: round(v / total_counted * 100, 1)
            for k, v in all_purposes.items()
        } if total_counted > 0 else {}

        return {
            "manuscript_id": manuscript_id,
            "genre": genre,
            "chapters_analyzed": len(chapter_analyses),
            "total_scenes": total_scenes,
            "purposeless_scenes": total_purposeless,
            "purposeless_percentage": round(total_purposeless / total_scenes * 100, 1) if total_scenes > 0 else 0,
            "purpose_distribution": purpose_distribution,
            "missing_genre_purposes": missing_purposes,
            "chapter_analyses": chapter_analyses,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _get_purpose_label(self, purpose: str) -> str:
        """Get human-readable label for purpose"""
        labels = {
            ScenePurpose.CHARACTER_INTRO: "Character Introduction",
            ScenePurpose.RELATIONSHIP_DEV: "Relationship Development",
            ScenePurpose.PLOT_ADVANCE: "Plot Advancement",
            ScenePurpose.WORLD_EXPO: "World Exposition",
            ScenePurpose.TENSION_BUILD: "Tension Building",
            ScenePurpose.CONFLICT_RESOLUTION: "Conflict Resolution",
            ScenePurpose.REVELATION: "Revelation/Twist",
            ScenePurpose.EMOTIONAL_BEAT: "Emotional Beat",
            ScenePurpose.ACTION_SEQUENCE: "Action Sequence",
            ScenePurpose.DIALOGUE_HEAVY: "Dialogue Exchange",
            ScenePurpose.TRANSITION: "Transition",
            ScenePurpose.CLIMAX: "Climax",
            ScenePurpose.SETUP: "Setup/Payoff",
            ScenePurpose.BACKSTORY: "Backstory",
        }
        return labels.get(purpose, purpose.replace('_', ' ').title())

    # ==================== Suggestions ====================

    def get_purpose_suggestions(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate suggestions based on scene purpose analysis"""
        suggestions = []

        # Purposeless scenes
        purposeless = analysis.get('purposeless_scenes', 0)
        if purposeless > 0:
            suggestions.append({
                "type": "purposeless_scenes",
                "severity": "high" if purposeless > 3 else "medium",
                "title": f"{purposeless} Scene(s) Lack Clear Purpose",
                "description": "These scenes don't have a clear narrative function",
                "fix": "Each scene should advance plot, develop character, or build world. Consider cutting or revising scenes without clear purpose."
            })

        # Missing genre purposes
        for missing in analysis.get('missing_genre_purposes', []):
            suggestions.append({
                "type": "missing_purpose",
                "severity": "low",
                "title": f"Missing: {missing['label']} Scenes",
                "description": f"This genre typically includes {missing['label'].lower()} scenes",
                "fix": missing['suggestion']
            })

        # Purpose imbalance
        distribution = analysis.get('purpose_distribution', {})
        if distribution:
            # Check for over-reliance on one purpose
            max_purpose = max(distribution.items(), key=lambda x: x[1])
            if max_purpose[1] > 40:
                suggestions.append({
                    "type": "purpose_imbalance",
                    "severity": "low",
                    "title": f"Heavy Focus on {self._get_purpose_label(max_purpose[0])}",
                    "description": f"{max_purpose[1]}% of scenes serve this purpose",
                    "fix": "Consider varying scene purposes for better narrative rhythm"
                })

        return suggestions
