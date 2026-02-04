"""
Emotional Beat Service - Track emotional beats through the story.

Analyzes:
- Emotional beat types per scene
- Emotional rhythm and variation
- Genre-appropriate emotional patterns
- Character-specific emotional arcs
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import re

from app.models.manuscript import Manuscript, Chapter


# ==================== Emotional Beat Types ====================

class EmotionalBeat:
    """Types of emotional beats"""
    JOY_TRIUMPH = "joy_triumph"
    FEAR_TENSION = "fear_tension"
    SADNESS_LOSS = "sadness_loss"
    ANGER_CONFLICT = "anger_conflict"
    LOVE_CONNECTION = "love_connection"
    SURPRISE_REVELATION = "surprise_revelation"
    HOPE_ANTICIPATION = "hope_anticipation"
    DESPAIR_DEFEAT = "despair_defeat"
    HUMOR_LEVITY = "humor_levity"
    WONDER_AWE = "wonder_awe"
    NEUTRAL = "neutral"


# Emotional beat indicators
BEAT_PATTERNS = {
    EmotionalBeat.JOY_TRIUMPH: [
        r'joy(?:ful)?', r'happy|happiness', r'triumph(?:ant)?',
        r'celebrat', r'victory', r'succeed', r'won\b',
        r'elat(?:ed|ion)', r'delight', r'ecstat'
    ],
    EmotionalBeat.FEAR_TENSION: [
        r'fear(?:ful)?', r'afraid', r'terrif(?:ied|ying)',
        r'dread', r'anxiety', r'nervous', r'tense|tension',
        r'panic', r'horror', r'danger', r'threat'
    ],
    EmotionalBeat.SADNESS_LOSS: [
        r'sad(?:ness)?', r'grief', r'mourn', r'loss',
        r'tears?|cried|crying', r'heartbreak', r'sorrow',
        r'depress', r'melan', r'devastat'
    ],
    EmotionalBeat.ANGER_CONFLICT: [
        r'anger|angry', r'rage|raging', r'fury|furious',
        r'frustrat', r'annoy', r'resent', r'bitter',
        r'fight(?:ing)?', r'argument|argued', r'conflict'
    ],
    EmotionalBeat.LOVE_CONNECTION: [
        r'love(?:d)?', r'affection', r'tender', r'intimat',
        r'connect(?:ion)?', r'bond(?:ed)?', r'close(?:ness)?',
        r'warm(?:th)?', r'caring', r'embrace'
    ],
    EmotionalBeat.SURPRISE_REVELATION: [
        r'surpris', r'shock(?:ed)?', r'astonish', r'stun',
        r'reveal', r'discover', r'realiz', r'truth',
        r'unexpected', r'twist'
    ],
    EmotionalBeat.HOPE_ANTICIPATION: [
        r'hope(?:ful)?', r'anticipat', r'expect(?:ation)?',
        r'optimis', r'excited|excitement', r'eager',
        r'looking forward', r'possibility', r'dream(?:ed)?'
    ],
    EmotionalBeat.DESPAIR_DEFEAT: [
        r'despair', r'defeat(?:ed)?', r'hopeless', r'doom',
        r'overwhelm', r'giving up', r'surrender', r'broken',
        r'lost\s+(?:all|everything)', r'nothing\s+left'
    ],
    EmotionalBeat.HUMOR_LEVITY: [
        r'laugh(?:ed|ing)?', r'joke', r'humor', r'funny',
        r'smile(?:d)?', r'grin(?:ned)?', r'chuckl', r'amused',
        r'witty', r'playful'
    ],
    EmotionalBeat.WONDER_AWE: [
        r'wonder(?:ful)?', r'awe(?:d)?', r'amaz(?:ed|ing)',
        r'marvel', r'magnificent', r'breathtaking',
        r'spectacular', r'incredible'
    ],
}

# Genre emotional expectations
GENRE_EMOTIONAL_PATTERNS = {
    "romance": {
        "primary": [EmotionalBeat.LOVE_CONNECTION, EmotionalBeat.HOPE_ANTICIPATION],
        "required": [EmotionalBeat.SADNESS_LOSS, EmotionalBeat.JOY_TRIUMPH],
        "emphasis": EmotionalBeat.LOVE_CONNECTION
    },
    "thriller": {
        "primary": [EmotionalBeat.FEAR_TENSION, EmotionalBeat.SURPRISE_REVELATION],
        "required": [EmotionalBeat.DESPAIR_DEFEAT, EmotionalBeat.HOPE_ANTICIPATION],
        "emphasis": EmotionalBeat.FEAR_TENSION
    },
    "mystery": {
        "primary": [EmotionalBeat.SURPRISE_REVELATION, EmotionalBeat.FEAR_TENSION],
        "required": [EmotionalBeat.HOPE_ANTICIPATION],
        "emphasis": EmotionalBeat.SURPRISE_REVELATION
    },
    "fantasy": {
        "primary": [EmotionalBeat.WONDER_AWE, EmotionalBeat.FEAR_TENSION],
        "required": [EmotionalBeat.JOY_TRIUMPH, EmotionalBeat.HOPE_ANTICIPATION],
        "emphasis": EmotionalBeat.WONDER_AWE
    },
    "literary": {
        "primary": [EmotionalBeat.SADNESS_LOSS, EmotionalBeat.LOVE_CONNECTION],
        "required": [EmotionalBeat.HOPE_ANTICIPATION, EmotionalBeat.SURPRISE_REVELATION],
        "emphasis": None
    },
    "horror": {
        "primary": [EmotionalBeat.FEAR_TENSION, EmotionalBeat.DESPAIR_DEFEAT],
        "required": [EmotionalBeat.SURPRISE_REVELATION],
        "emphasis": EmotionalBeat.FEAR_TENSION
    },
    "comedy": {
        "primary": [EmotionalBeat.HUMOR_LEVITY, EmotionalBeat.JOY_TRIUMPH],
        "required": [EmotionalBeat.LOVE_CONNECTION],
        "emphasis": EmotionalBeat.HUMOR_LEVITY
    },
}


class EmotionalBeatService:
    """Analyzes emotional beats throughout a manuscript"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Beat Detection ====================

    def detect_emotional_beats(self, text: str) -> Dict[str, Any]:
        """
        Detect emotional beats in a text passage.

        Returns:
        {
            "primary_beat": str,
            "secondary_beats": List[str],
            "beat_scores": Dict[str, float],
            "emotional_intensity": float,
            "is_neutral": bool
        }
        """
        if not text or len(text.strip()) < 50:
            return {
                "primary_beat": EmotionalBeat.NEUTRAL,
                "secondary_beats": [],
                "beat_scores": {},
                "emotional_intensity": 0.0,
                "is_neutral": True
            }

        text_lower = text.lower()
        beat_scores = {}

        # Score each beat type
        for beat, patterns in BEAT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                score += len(matches)

            if score > 0:
                beat_scores[beat] = score

        if not beat_scores:
            return {
                "primary_beat": EmotionalBeat.NEUTRAL,
                "secondary_beats": [],
                "beat_scores": {},
                "emotional_intensity": 0.0,
                "is_neutral": True
            }

        # Normalize and calculate intensity
        total = sum(beat_scores.values())
        word_count = len(text.split())
        intensity = min(1.0, total / (word_count / 100))  # Normalize by text length

        # Sort by score
        sorted_beats = sorted(beat_scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_beats[0]
        secondary = [b[0] for b in sorted_beats[1:3] if b[1] > total * 0.2]

        return {
            "primary_beat": primary[0],
            "secondary_beats": secondary,
            "beat_scores": {k: round(v / total, 2) for k, v in beat_scores.items()},
            "emotional_intensity": round(intensity, 2),
            "is_neutral": False
        }

    # ==================== Chapter Analysis ====================

    def analyze_chapter(self, chapter_id: str) -> Dict[str, Any]:
        """Analyze emotional beats in a chapter"""
        chapter = self.db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            return {"error": "Chapter not found"}

        if not chapter.content:
            return {"error": "No content to analyze"}

        # Split into scenes or paragraphs
        scene_break_pattern = r'\n\s*(?:\*\s*\*\s*\*|\#\s*\#\s*\#|~~~)\s*\n'
        scenes = re.split(scene_break_pattern, chapter.content)

        if len(scenes) == 1:
            # No scene breaks, analyze by paragraph groups
            paragraphs = [p for p in chapter.content.split('\n\n') if p.strip()]
            # Group paragraphs into chunks of ~500 words
            scenes = self._group_paragraphs(paragraphs, target_words=500)

        scene_beats = []
        beat_counts = {}

        for i, scene in enumerate(scenes):
            if len(scene.strip()) < 100:
                continue

            beat_info = self.detect_emotional_beats(scene)
            scene_beats.append({
                "scene_index": i,
                "primary_beat": beat_info["primary_beat"],
                "secondary_beats": beat_info["secondary_beats"],
                "intensity": beat_info["emotional_intensity"]
            })

            # Count beats
            primary = beat_info["primary_beat"]
            beat_counts[primary] = beat_counts.get(primary, 0) + 1

        # Analyze rhythm
        rhythm_analysis = self._analyze_emotional_rhythm(scene_beats)

        return {
            "chapter_id": chapter_id,
            "chapter_title": chapter.title,
            "total_scenes": len(scene_beats),
            "beat_distribution": beat_counts,
            "scene_beats": scene_beats,
            "rhythm_analysis": rhythm_analysis,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _group_paragraphs(self, paragraphs: List[str], target_words: int = 500) -> List[str]:
        """Group paragraphs into chunks of approximately target word count"""
        groups = []
        current_group = []
        current_words = 0

        for para in paragraphs:
            word_count = len(para.split())
            if current_words + word_count > target_words and current_group:
                groups.append('\n\n'.join(current_group))
                current_group = [para]
                current_words = word_count
            else:
                current_group.append(para)
                current_words += word_count

        if current_group:
            groups.append('\n\n'.join(current_group))

        return groups

    def _analyze_emotional_rhythm(self, scene_beats: List[Dict]) -> Dict[str, Any]:
        """Analyze the emotional rhythm across scenes"""
        if len(scene_beats) < 2:
            return {"varied": False, "pattern": "insufficient_data"}

        beats = [s["primary_beat"] for s in scene_beats]
        intensities = [s["intensity"] for s in scene_beats]

        # Check for monotony (same beat repeated)
        consecutive_same = 0
        max_consecutive = 0
        prev_beat = None

        for beat in beats:
            if beat == prev_beat:
                consecutive_same += 1
                max_consecutive = max(max_consecutive, consecutive_same)
            else:
                consecutive_same = 0
            prev_beat = beat

        # Check intensity variation
        if len(intensities) > 1:
            intensity_variation = max(intensities) - min(intensities)
        else:
            intensity_variation = 0

        # Determine pattern
        unique_beats = len(set(beats))
        total_beats = len(beats)

        if max_consecutive > 2:
            pattern = "monotonous"
        elif unique_beats < total_beats * 0.4:
            pattern = "repetitive"
        elif intensity_variation < 0.2:
            pattern = "flat"
        else:
            pattern = "varied"

        return {
            "pattern": pattern,
            "unique_beats": unique_beats,
            "max_consecutive_same": max_consecutive + 1,
            "intensity_variation": round(intensity_variation, 2),
            "average_intensity": round(sum(intensities) / len(intensities), 2) if intensities else 0,
            "is_healthy": pattern == "varied"
        }

    # ==================== Manuscript Analysis ====================

    def analyze_manuscript(
        self,
        manuscript_id: str,
        genre: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze emotional beats across entire manuscript"""
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
        all_beats = {}
        intensity_by_chapter = []

        for chapter in chapters:
            analysis = self.analyze_chapter(chapter.id)
            if "error" not in analysis:
                chapter_analyses.append(analysis)

                # Aggregate beat counts
                for beat, count in analysis.get("beat_distribution", {}).items():
                    all_beats[beat] = all_beats.get(beat, 0) + count

                # Track intensity
                avg_intensity = analysis.get("rhythm_analysis", {}).get("average_intensity", 0)
                intensity_by_chapter.append({
                    "chapter_index": chapter.order_index,
                    "chapter_title": chapter.title,
                    "average_intensity": avg_intensity
                })

        # Genre analysis
        genre_analysis = None
        if genre and genre in GENRE_EMOTIONAL_PATTERNS:
            genre_analysis = self._analyze_genre_fit(all_beats, genre)

        # Find missing beats
        present_beats = set(all_beats.keys())
        all_beat_types = {getattr(EmotionalBeat, attr) for attr in dir(EmotionalBeat)
                         if not attr.startswith('_') and attr != 'NEUTRAL'}
        missing_beats = all_beat_types - present_beats - {EmotionalBeat.NEUTRAL}

        return {
            "manuscript_id": manuscript_id,
            "genre": genre,
            "chapters_analyzed": len(chapter_analyses),
            "beat_distribution": all_beats,
            "missing_beats": list(missing_beats),
            "intensity_by_chapter": intensity_by_chapter,
            "genre_analysis": genre_analysis,
            "chapter_analyses": chapter_analyses,
            "analyzed_at": datetime.utcnow().isoformat()
        }

    def _analyze_genre_fit(self, beat_counts: Dict[str, int], genre: str) -> Dict[str, Any]:
        """Analyze how well emotional beats fit the genre"""
        expectations = GENRE_EMOTIONAL_PATTERNS.get(genre, {})

        primary = expectations.get("primary", [])
        required = expectations.get("required", [])
        emphasis = expectations.get("emphasis")

        # Check primary beats
        primary_present = [b for b in primary if b in beat_counts]
        primary_missing = [b for b in primary if b not in beat_counts]

        # Check required beats
        required_present = [b for b in required if b in beat_counts]
        required_missing = [b for b in required if b not in beat_counts]

        # Check emphasis
        emphasis_score = 0
        if emphasis and beat_counts:
            total = sum(beat_counts.values())
            emphasis_count = beat_counts.get(emphasis, 0)
            emphasis_score = round(emphasis_count / total, 2) if total > 0 else 0

        # Calculate fit score
        fit_score = 0
        fit_score += len(primary_present) / len(primary) * 40 if primary else 40
        fit_score += len(required_present) / len(required) * 30 if required else 30
        fit_score += emphasis_score * 30 if emphasis else 30

        return {
            "genre": genre,
            "fit_score": round(fit_score),
            "primary_beats_present": primary_present,
            "primary_beats_missing": primary_missing,
            "required_beats_present": required_present,
            "required_beats_missing": required_missing,
            "emphasis_beat": emphasis,
            "emphasis_score": emphasis_score
        }

    # ==================== Suggestions ====================

    def get_emotional_suggestions(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate suggestions for emotional variety"""
        suggestions = []

        # Missing beats
        missing = analysis.get("missing_beats", [])
        if missing:
            suggestions.append({
                "type": "missing_beats",
                "severity": "medium",
                "title": f"Missing Emotional Beats",
                "description": f"No scenes with: {', '.join(self._beat_label(b) for b in missing[:3])}",
                "fix": "Consider adding scenes that evoke these emotions for fuller emotional range"
            })

        # Genre fit
        genre_analysis = analysis.get("genre_analysis")
        if genre_analysis and genre_analysis.get("fit_score", 100) < 60:
            suggestions.append({
                "type": "genre_fit",
                "severity": "low",
                "title": f"Low Genre Emotional Fit ({genre_analysis.get('fit_score')}%)",
                "description": f"Missing primary {genre_analysis.get('genre')} beats: {', '.join(self._beat_label(b) for b in genre_analysis.get('primary_beats_missing', []))}",
                "fix": f"This genre typically emphasizes {self._beat_label(genre_analysis.get('emphasis_beat', 'varied'))} emotions"
            })

        # Rhythm issues from chapters
        for ch in analysis.get("chapter_analyses", []):
            rhythm = ch.get("rhythm_analysis", {})
            if rhythm.get("pattern") == "monotonous":
                suggestions.append({
                    "type": "monotonous_chapter",
                    "severity": "medium",
                    "title": f"Emotional Monotony in '{ch.get('chapter_title')}'",
                    "description": f"Same emotional beat repeated {rhythm.get('max_consecutive_same')}+ times",
                    "fix": "Vary the emotional beats to create rhythm and keep readers engaged"
                })

        return suggestions

    def _beat_label(self, beat: str) -> str:
        """Get human-readable beat label"""
        labels = {
            EmotionalBeat.JOY_TRIUMPH: "Joy/Triumph",
            EmotionalBeat.FEAR_TENSION: "Fear/Tension",
            EmotionalBeat.SADNESS_LOSS: "Sadness/Loss",
            EmotionalBeat.ANGER_CONFLICT: "Anger/Conflict",
            EmotionalBeat.LOVE_CONNECTION: "Love/Connection",
            EmotionalBeat.SURPRISE_REVELATION: "Surprise/Revelation",
            EmotionalBeat.HOPE_ANTICIPATION: "Hope/Anticipation",
            EmotionalBeat.DESPAIR_DEFEAT: "Despair/Defeat",
            EmotionalBeat.HUMOR_LEVITY: "Humor/Levity",
            EmotionalBeat.WONDER_AWE: "Wonder/Awe",
            EmotionalBeat.NEUTRAL: "Neutral",
        }
        return labels.get(beat, beat.replace('_', ' ').title())
