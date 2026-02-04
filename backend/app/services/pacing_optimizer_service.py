"""
Pacing Optimizer Service - Analyze and suggest pacing improvements.

Analyzes:
- Scene/chapter length variation
- Dialogue-to-description ratio
- Action density
- Tension level changes
- Slow sections and dead spots
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import re

from app.models.manuscript import Manuscript, Chapter
from app.services.scene_purpose_service import ScenePurposeService


# ==================== Pacing Metrics ====================

class PacingIssue:
    """Types of pacing issues"""
    TOO_SLOW = "too_slow"
    TOO_FAST = "too_fast"
    NO_TENSION = "no_tension"
    MONOTONOUS = "monotonous"
    UNEVEN = "uneven"
    DESCRIPTION_HEAVY = "description_heavy"
    DIALOGUE_HEAVY = "dialogue_heavy"
    SHORT_CHAPTER = "short_chapter"
    LONG_CHAPTER = "long_chapter"


# Genre pacing norms
GENRE_PACING = {
    "thriller": {
        "ideal_chapter_length": (2500, 4000),
        "dialogue_ratio": (0.3, 0.5),
        "action_frequency": "high",
        "tension_gaps_max": 2,  # Max chapters without tension
    },
    "romance": {
        "ideal_chapter_length": (3000, 5000),
        "dialogue_ratio": (0.4, 0.6),
        "action_frequency": "low",
        "tension_gaps_max": 3,
    },
    "fantasy": {
        "ideal_chapter_length": (3500, 6000),
        "dialogue_ratio": (0.25, 0.45),
        "action_frequency": "medium",
        "tension_gaps_max": 3,
    },
    "mystery": {
        "ideal_chapter_length": (2500, 4500),
        "dialogue_ratio": (0.35, 0.55),
        "action_frequency": "medium",
        "tension_gaps_max": 2,
    },
    "literary": {
        "ideal_chapter_length": (3000, 6000),
        "dialogue_ratio": (0.2, 0.5),
        "action_frequency": "low",
        "tension_gaps_max": 5,
    },
}


class PacingOptimizerService:
    """Analyzes pacing and provides optimization suggestions"""

    def __init__(self, db: Session):
        self.db = db
        self.scene_service = ScenePurposeService(db)

    # ==================== Chapter Analysis ====================

    def analyze_chapter_pacing(self, chapter_id: str) -> Dict[str, Any]:
        """Analyze pacing metrics for a single chapter"""
        chapter = self.db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return {"error": "Chapter not found"}

        if not chapter.content:
            return {"error": "No content to analyze"}

        text = chapter.content
        word_count = len(text.split())

        # Calculate metrics
        dialogue_ratio = self._calculate_dialogue_ratio(text)
        action_density = self._calculate_action_density(text)
        description_density = self._calculate_description_density(text)
        tension_level = self._estimate_tension_level(text)
        sentence_variety = self._analyze_sentence_variety(text)

        # Identify issues
        issues = []

        if dialogue_ratio > 0.7:
            issues.append({
                "type": PacingIssue.DIALOGUE_HEAVY,
                "severity": "medium",
                "value": dialogue_ratio
            })
        elif dialogue_ratio < 0.15:
            issues.append({
                "type": PacingIssue.DESCRIPTION_HEAVY,
                "severity": "medium",
                "value": dialogue_ratio
            })

        if word_count < 1500:
            issues.append({
                "type": PacingIssue.SHORT_CHAPTER,
                "severity": "low",
                "value": word_count
            })
        elif word_count > 7000:
            issues.append({
                "type": PacingIssue.LONG_CHAPTER,
                "severity": "low",
                "value": word_count
            })

        if tension_level < 0.2 and action_density < 0.1:
            issues.append({
                "type": PacingIssue.TOO_SLOW,
                "severity": "medium",
                "value": tension_level
            })

        return {
            "chapter_id": chapter_id,
            "chapter_title": chapter.title,
            "chapter_index": chapter.order_index,
            "metrics": {
                "word_count": word_count,
                "dialogue_ratio": round(dialogue_ratio, 2),
                "action_density": round(action_density, 2),
                "description_density": round(description_density, 2),
                "tension_level": round(tension_level, 2),
                "sentence_variety": sentence_variety
            },
            "issues": issues,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _calculate_dialogue_ratio(self, text: str) -> float:
        """Calculate ratio of dialogue to total text"""
        # Count dialogue (text in quotes)
        dialogue_matches = re.findall(r'"[^"]*"', text)
        dialogue_words = sum(len(d.split()) for d in dialogue_matches)
        total_words = len(text.split())

        return dialogue_words / total_words if total_words > 0 else 0

    def _calculate_action_density(self, text: str) -> float:
        """Calculate density of action verbs and phrases"""
        action_patterns = [
            r'\b(?:ran|run|running)\b', r'\b(?:fought|fight|fighting)\b',
            r'\b(?:jumped|jump|jumping)\b', r'\b(?:grabbed|grab)\b',
            r'\b(?:threw|throw)\b', r'\b(?:hit|struck|strike)\b',
            r'\b(?:dodged|dodge)\b', r'\b(?:blocked|block)\b',
            r'\b(?:attacked|attack)\b', r'\b(?:escaped|escape)\b',
            r'\b(?:chased|chase)\b', r'\b(?:rushed|rush)\b',
            r'\b(?:shot|shoot)\b', r'\b(?:kicked|kick)\b'
        ]

        action_count = 0
        for pattern in action_patterns:
            action_count += len(re.findall(pattern, text, re.IGNORECASE))

        word_count = len(text.split())
        return action_count / (word_count / 100) if word_count > 0 else 0

    def _calculate_description_density(self, text: str) -> float:
        """Calculate density of descriptive passages"""
        # Count adjectives and descriptive phrases
        description_patterns = [
            r'\b(?:beautiful|gorgeous|stunning|lovely)\b',
            r'\b(?:vast|enormous|tiny|massive)\b',
            r'\b(?:ancient|old|weathered|worn)\b',
            r'\b(?:dark|bright|dim|glowing)\b',
            r'\bthe\s+\w+\s+was\s+\w+\b',  # "The X was Y" patterns
            r'\b(?:seemed|appeared|looked)\b'
        ]

        desc_count = 0
        for pattern in description_patterns:
            desc_count += len(re.findall(pattern, text, re.IGNORECASE))

        word_count = len(text.split())
        return desc_count / (word_count / 100) if word_count > 0 else 0

    def _estimate_tension_level(self, text: str) -> float:
        """Estimate tension level from text markers"""
        tension_patterns = [
            (r'\b(?:danger|dangerous)\b', 3),
            (r'\b(?:fear|afraid|terrified)\b', 3),
            (r'\b(?:threat|threatening)\b', 2),
            (r'\b(?:urgent|urgently|hurry)\b', 2),
            (r'\b(?:suddenly|abruptly)\b', 1),
            (r'\b(?:heart\s+(?:pounded|raced|hammered))\b', 2),
            (r'\b(?:couldn\'t\s+breathe)\b', 2),
            (r'[!?]{2,}', 1),  # Multiple exclamation/question marks
            (r'\b(?:dead|death|dying|die)\b', 2),
            (r'\b(?:blood|bleeding)\b', 2),
            (r'\b(?:scream|screamed|screaming)\b', 2),
        ]

        tension_score = 0
        for pattern, weight in tension_patterns:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            tension_score += matches * weight

        word_count = len(text.split())
        # Normalize to 0-1 scale
        normalized = tension_score / (word_count / 100) if word_count > 0 else 0
        return min(1.0, normalized / 10)  # Cap at 1.0

    def _analyze_sentence_variety(self, text: str) -> Dict[str, Any]:
        """Analyze sentence length variety"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return {"varied": False, "avg_length": 0}

        lengths = [len(s.split()) for s in sentences]
        avg_length = sum(lengths) / len(lengths)

        # Calculate standard deviation
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5

        # Short, medium, long sentence counts
        short = sum(1 for l in lengths if l < 10)
        medium = sum(1 for l in lengths if 10 <= l < 25)
        long = sum(1 for l in lengths if l >= 25)

        is_varied = std_dev > 5 and short > 0 and long > 0

        return {
            "varied": is_varied,
            "avg_length": round(avg_length, 1),
            "std_dev": round(std_dev, 1),
            "short_sentences": short,
            "medium_sentences": medium,
            "long_sentences": long
        }

    # ==================== Manuscript Analysis ====================

    def analyze_manuscript_pacing(
        self,
        manuscript_id: str,
        genre: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze pacing across entire manuscript"""
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
        word_counts = []
        dialogue_ratios = []
        tension_levels = []
        all_issues = []

        for chapter in chapters:
            analysis = self.analyze_chapter_pacing(chapter.id)
            if "error" not in analysis:
                chapter_analyses.append(analysis)
                metrics = analysis.get("metrics", {})

                word_counts.append(metrics.get("word_count", 0))
                dialogue_ratios.append(metrics.get("dialogue_ratio", 0))
                tension_levels.append(metrics.get("tension_level", 0))
                all_issues.extend(analysis.get("issues", []))

        # Calculate manuscript-level metrics
        manuscript_metrics = self._calculate_manuscript_metrics(
            word_counts, dialogue_ratios, tension_levels, chapters
        )

        # Detect tension valleys
        tension_valleys = self._detect_tension_valleys(tension_levels, chapters)

        # Detect slow sections
        slow_sections = self._detect_slow_sections(chapter_analyses)

        # Genre-specific analysis
        genre_analysis = None
        if genre and genre in GENRE_PACING:
            genre_analysis = self._analyze_genre_fit_pacing(
                manuscript_metrics, genre
            )

        return {
            "manuscript_id": manuscript_id,
            "genre": genre,
            "chapters_analyzed": len(chapter_analyses),
            "manuscript_metrics": manuscript_metrics,
            "tension_valleys": tension_valleys,
            "slow_sections": slow_sections,
            "genre_analysis": genre_analysis,
            "chapter_analyses": chapter_analyses,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _calculate_manuscript_metrics(
        self,
        word_counts: List[int],
        dialogue_ratios: List[float],
        tension_levels: List[float],
        chapters: List[Chapter]
    ) -> Dict[str, Any]:
        """Calculate aggregate manuscript metrics"""
        if not word_counts:
            return {}

        total_words = sum(word_counts)
        avg_chapter_length = total_words / len(word_counts)

        # Chapter length consistency
        if len(word_counts) > 1:
            variance = sum((w - avg_chapter_length) ** 2 for w in word_counts) / len(word_counts)
            length_std_dev = variance ** 0.5
            length_consistency = 1 - min(1.0, length_std_dev / avg_chapter_length)
        else:
            length_consistency = 1.0

        return {
            "total_word_count": total_words,
            "chapter_count": len(word_counts),
            "avg_chapter_length": round(avg_chapter_length),
            "min_chapter_length": min(word_counts),
            "max_chapter_length": max(word_counts),
            "length_consistency": round(length_consistency, 2),
            "avg_dialogue_ratio": round(sum(dialogue_ratios) / len(dialogue_ratios), 2),
            "avg_tension_level": round(sum(tension_levels) / len(tension_levels), 2),
            "max_tension_level": round(max(tension_levels), 2),
            "min_tension_level": round(min(tension_levels), 2)
        }

    def _detect_tension_valleys(
        self,
        tension_levels: List[float],
        chapters: List[Chapter]
    ) -> List[Dict[str, Any]]:
        """Detect sequences of low-tension chapters"""
        valleys = []
        valley_start = None
        valley_length = 0
        threshold = 0.2

        for i, level in enumerate(tension_levels):
            if level < threshold:
                if valley_start is None:
                    valley_start = i
                valley_length += 1
            else:
                if valley_length >= 3:  # 3+ chapters of low tension
                    valleys.append({
                        "start_chapter_index": valley_start,
                        "start_chapter_title": chapters[valley_start].title if valley_start < len(chapters) else "Unknown",
                        "length": valley_length,
                        "severity": "high" if valley_length >= 5 else "medium"
                    })
                valley_start = None
                valley_length = 0

        # Check final valley
        if valley_length >= 3:
            valleys.append({
                "start_chapter_index": valley_start,
                "start_chapter_title": chapters[valley_start].title if valley_start < len(chapters) else "Unknown",
                "length": valley_length,
                "severity": "high" if valley_length >= 5 else "medium"
            })

        return valleys

    def _detect_slow_sections(
        self,
        chapter_analyses: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Detect chapters that are pacing slow"""
        slow_sections = []

        for analysis in chapter_analyses:
            metrics = analysis.get("metrics", {})

            # Check for slow indicators
            is_slow = (
                metrics.get("dialogue_ratio", 1) < 0.15 and
                metrics.get("action_density", 1) < 0.1 and
                metrics.get("tension_level", 1) < 0.2
            )

            if is_slow:
                slow_sections.append({
                    "chapter_id": analysis.get("chapter_id"),
                    "chapter_title": analysis.get("chapter_title"),
                    "chapter_index": analysis.get("chapter_index"),
                    "dialogue_ratio": metrics.get("dialogue_ratio"),
                    "action_density": metrics.get("action_density"),
                    "tension_level": metrics.get("tension_level"),
                    "suggestion": "This chapter is description-heavy with little dialogue or action"
                })

        return slow_sections

    def _analyze_genre_fit_pacing(
        self,
        metrics: Dict[str, Any],
        genre: str
    ) -> Dict[str, Any]:
        """Analyze how well pacing fits the genre"""
        norms = GENRE_PACING.get(genre, {})

        issues = []

        # Check chapter length
        ideal_length = norms.get("ideal_chapter_length", (2500, 5000))
        avg_length = metrics.get("avg_chapter_length", 0)
        if avg_length < ideal_length[0]:
            issues.append(f"Chapters are shorter than typical for {genre} ({avg_length} vs {ideal_length[0]}-{ideal_length[1]})")
        elif avg_length > ideal_length[1]:
            issues.append(f"Chapters are longer than typical for {genre} ({avg_length} vs {ideal_length[0]}-{ideal_length[1]})")

        # Check dialogue ratio
        ideal_dialogue = norms.get("dialogue_ratio", (0.25, 0.5))
        avg_dialogue = metrics.get("avg_dialogue_ratio", 0)
        if avg_dialogue < ideal_dialogue[0]:
            issues.append(f"Less dialogue than typical for {genre} ({avg_dialogue:.0%} vs {ideal_dialogue[0]:.0%}-{ideal_dialogue[1]:.0%})")
        elif avg_dialogue > ideal_dialogue[1]:
            issues.append(f"More dialogue than typical for {genre} ({avg_dialogue:.0%} vs {ideal_dialogue[0]:.0%}-{ideal_dialogue[1]:.0%})")

        return {
            "genre": genre,
            "issues": issues,
            "is_fitting": len(issues) == 0,
            "norms": norms
        }

    # ==================== Suggestions ====================

    def get_pacing_suggestions(
        self,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate actionable pacing suggestions"""
        suggestions = []

        # Tension valleys
        for valley in analysis.get("tension_valleys", []):
            suggestions.append({
                "type": "tension_valley",
                "severity": valley.get("severity", "medium"),
                "title": f"Tension Valley: Chapters {valley['start_chapter_index'] + 1}-{valley['start_chapter_index'] + valley['length']}",
                "description": f"{valley['length']} consecutive chapters with low tension",
                "fix": "Consider adding a conflict beat, revelation, or deadline pressure in this stretch"
            })

        # Slow sections
        for slow in analysis.get("slow_sections", [])[:3]:  # Limit to top 3
            suggestions.append({
                "type": "slow_section",
                "severity": "medium",
                "title": f"Slow Section: '{slow['chapter_title']}'",
                "description": slow.get("suggestion", "Heavy description, low dialogue/action"),
                "fix": "Add dialogue exchanges, character reactions, or cut excess description"
            })

        # Genre fit
        genre_analysis = analysis.get("genre_analysis", {})
        for issue in genre_analysis.get("issues", []):
            suggestions.append({
                "type": "genre_pacing",
                "severity": "low",
                "title": "Genre Pacing Mismatch",
                "description": issue,
                "fix": f"Adjust pacing to match typical {genre_analysis.get('genre', 'genre')} expectations"
            })

        # Chapter length inconsistency
        metrics = analysis.get("manuscript_metrics", {})
        if metrics.get("length_consistency", 1) < 0.6:
            suggestions.append({
                "type": "inconsistent_length",
                "severity": "low",
                "title": "Inconsistent Chapter Lengths",
                "description": f"Chapters range from {metrics.get('min_chapter_length', '?')} to {metrics.get('max_chapter_length', '?')} words",
                "fix": "Consider evening out chapter lengths for better reading rhythm"
            })

        return suggestions
