"""
Voice Analysis Service

Analyzes character dialogue to build voice profiles and detect inconsistencies.
Helps writers maintain consistent, distinct character voices.
"""

import re
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter
from dataclasses import dataclass, field
import logging

from sqlalchemy.orm import Session

from app.models.entity import Entity
from app.models.manuscript import Manuscript, Chapter
from app.models.voice_profile import (
    CharacterVoiceProfile,
    VoiceInconsistency,
    VoiceComparison
)

logger = logging.getLogger(__name__)


@dataclass
class DialogueSample:
    """A single piece of dialogue attributed to a character"""
    text: str
    chapter_id: str
    start_offset: int
    end_offset: int
    context: str = ""  # Surrounding text for context


@dataclass
class VoiceMetrics:
    """Computed metrics for a character's voice"""
    avg_sentence_length: float = 0.0
    sentence_length_variance: float = 0.0
    vocabulary_complexity: float = 0.0
    vocabulary_richness: float = 0.0
    contraction_rate: float = 0.0
    question_rate: float = 0.0
    exclamation_rate: float = 0.0
    common_phrases: List[Tuple[str, int]] = field(default_factory=list)
    signature_words: List[str] = field(default_factory=list)
    filler_words: Dict[str, int] = field(default_factory=dict)
    formality_score: float = 0.5
    emotion_markers: Dict[str, float] = field(default_factory=dict)
    dialogue_samples: int = 0
    total_words: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "avg_sentence_length": round(self.avg_sentence_length, 2),
            "sentence_length_variance": round(self.sentence_length_variance, 2),
            "vocabulary_complexity": round(self.vocabulary_complexity, 2),
            "vocabulary_richness": round(self.vocabulary_richness, 3),
            "contraction_rate": round(self.contraction_rate, 3),
            "question_rate": round(self.question_rate, 3),
            "exclamation_rate": round(self.exclamation_rate, 3),
            "common_phrases": self.common_phrases[:10],
            "signature_words": self.signature_words[:15],
            "filler_words": dict(sorted(
                self.filler_words.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            "formality_score": round(self.formality_score, 2),
            "emotion_markers": {k: round(v, 3) for k, v in self.emotion_markers.items()},
            "dialogue_samples": self.dialogue_samples,
            "total_words": self.total_words,
        }


class VoiceAnalysisService:
    """
    Service for analyzing character voices and detecting inconsistencies.

    Voice Profile Philosophy:
    - Each character should have a distinct 'sound'
    - Consistency doesn't mean sameness - characters can evolve
    - Minor variations are natural; major deviations warrant attention
    - Context matters: emotional scenes may have different patterns
    """

    # Common contractions for contraction rate analysis
    CONTRACTIONS = {
        "don't", "doesn't", "didn't", "won't", "wouldn't", "can't", "couldn't",
        "shouldn't", "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't",
        "hadn't", "I'm", "I've", "I'll", "I'd", "you're", "you've", "you'll",
        "you'd", "he's", "she's", "it's", "we're", "we've", "we'll", "we'd",
        "they're", "they've", "they'll", "they'd", "that's", "there's", "here's",
        "what's", "who's", "let's", "ain't", "gonna", "wanna", "gotta",
    }

    # Filler words that characterize informal speech
    FILLER_WORDS = {
        "um", "uh", "er", "ah", "like", "you know", "i mean", "basically",
        "actually", "literally", "honestly", "well", "so", "anyway", "right",
        "okay", "ok", "yeah", "yep", "nope", "huh", "hmm",
    }

    # Formal vocabulary indicators
    FORMAL_INDICATORS = {
        "therefore", "however", "furthermore", "moreover", "nevertheless",
        "consequently", "subsequently", "accordingly", "indeed", "certainly",
        "precisely", "absolutely", "undoubtedly", "perhaps", "indeed",
        "regarding", "concerning", "approximately", "primarily", "essentially",
    }

    # Informal vocabulary indicators
    INFORMAL_INDICATORS = {
        "gonna", "wanna", "gotta", "kinda", "sorta", "yeah", "yep", "nope",
        "cool", "awesome", "totally", "super", "stuff", "things", "guy",
        "guys", "kids", "okay", "ok", "hey", "hi", "bye", "wow", "oops",
    }

    # Emotion markers
    POSITIVE_EMOTIONS = {
        "happy", "glad", "joy", "love", "wonderful", "great", "amazing",
        "fantastic", "beautiful", "excited", "delighted", "pleased", "thrilled",
    }

    NEGATIVE_EMOTIONS = {
        "sad", "angry", "hate", "terrible", "awful", "horrible", "disgusting",
        "furious", "miserable", "depressed", "frustrated", "annoyed", "upset",
    }

    def __init__(self, db: Session):
        self.db = db

    def extract_character_dialogue(
        self,
        manuscript_id: str,
        character_id: str
    ) -> List[DialogueSample]:
        """
        Extract all dialogue attributed to a specific character.

        Uses entity mentions and dialogue attribution patterns to find
        dialogue that belongs to this character.
        """
        dialogue_samples = []

        # Get character entity
        character = self.db.query(Entity).filter(
            Entity.id == character_id
        ).first()

        if not character:
            return []

        # Get all chapters
        chapters = self.db.query(Chapter).filter(
            Chapter.manuscript_id == manuscript_id,
            Chapter.document_type == "CHAPTER"
        ).all()

        # Character name variants for attribution detection
        name_variants = [character.name.lower()]
        if character.aliases:
            name_variants.extend([a.lower() for a in character.aliases])

        # Also add first name if full name
        name_parts = character.name.split()
        if len(name_parts) > 1:
            name_variants.append(name_parts[0].lower())

        for chapter in chapters:
            if not chapter.content:
                continue

            # Find dialogue with attribution
            samples = self._extract_attributed_dialogue(
                chapter.content,
                chapter.id,
                name_variants
            )
            dialogue_samples.extend(samples)

        return dialogue_samples

    def _extract_attributed_dialogue(
        self,
        text: str,
        chapter_id: str,
        name_variants: List[str]
    ) -> List[DialogueSample]:
        """
        Extract dialogue attributed to a character by name.

        Looks for patterns like:
        - "Hello," said John.
        - John said, "Hello."
        - "Hello." John smiled.
        - "Hello," John replied.
        """
        samples = []

        # Pattern for dialogue with attribution after
        # "dialogue," name verb  OR  "dialogue." Name verb
        pattern_after = r'["""]([^"""]+)["""][,.]?\s*(' + '|'.join(
            re.escape(n) for n in name_variants
        ) + r')\s+\w+'

        # Pattern for attribution before dialogue
        # name verb, "dialogue"
        pattern_before = r'(' + '|'.join(
            re.escape(n) for n in name_variants
        ) + r')\s+\w+[,]?\s*["""]([^"""]+)["""]'

        # Find dialogue with attribution after
        for match in re.finditer(pattern_after, text, re.IGNORECASE):
            dialogue = match.group(1).strip()
            if len(dialogue) > 5:  # Skip very short dialogue
                samples.append(DialogueSample(
                    text=dialogue,
                    chapter_id=chapter_id,
                    start_offset=match.start(),
                    end_offset=match.end(),
                    context=text[max(0, match.start()-50):match.end()+50]
                ))

        # Find dialogue with attribution before
        for match in re.finditer(pattern_before, text, re.IGNORECASE):
            dialogue = match.group(2).strip()
            if len(dialogue) > 5:
                samples.append(DialogueSample(
                    text=dialogue,
                    chapter_id=chapter_id,
                    start_offset=match.start(),
                    end_offset=match.end(),
                    context=text[max(0, match.start()-50):match.end()+50]
                ))

        return samples

    def compute_voice_metrics(
        self,
        dialogue_samples: List[DialogueSample]
    ) -> VoiceMetrics:
        """
        Compute voice metrics from dialogue samples.

        Analyzes vocabulary, sentence structure, formality, and speech patterns.
        """
        if not dialogue_samples:
            return VoiceMetrics()

        metrics = VoiceMetrics()
        metrics.dialogue_samples = len(dialogue_samples)

        all_text = " ".join(s.text for s in dialogue_samples)
        all_words = re.findall(r'\b\w+\b', all_text.lower())
        metrics.total_words = len(all_words)

        if not all_words:
            return metrics

        # Sentence analysis
        sentences = []
        for sample in dialogue_samples:
            sample_sentences = re.split(r'[.!?]+', sample.text)
            sentences.extend([s.strip() for s in sample_sentences if s.strip()])

        if sentences:
            sentence_lengths = [len(s.split()) for s in sentences]
            metrics.avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)

            # Variance
            mean = metrics.avg_sentence_length
            variance = sum((x - mean) ** 2 for x in sentence_lengths) / len(sentence_lengths)
            metrics.sentence_length_variance = variance ** 0.5

            # Question rate
            questions = sum(1 for s in sentences if '?' in s)
            metrics.question_rate = questions / len(sentences)

            # Exclamation rate
            exclamations = sum(1 for sample in dialogue_samples if '!' in sample.text)
            metrics.exclamation_rate = exclamations / len(dialogue_samples)

        # Vocabulary complexity (syllables per word)
        total_syllables = sum(self._count_syllables(w) for w in all_words)
        metrics.vocabulary_complexity = total_syllables / len(all_words)

        # Vocabulary richness (type-token ratio)
        unique_words = set(all_words)
        metrics.vocabulary_richness = len(unique_words) / len(all_words)

        # Contraction rate
        contractions_used = sum(1 for w in all_words if w in self.CONTRACTIONS)
        metrics.contraction_rate = contractions_used / len(all_words)

        # Filler words
        for filler in self.FILLER_WORDS:
            count = all_text.lower().count(filler)
            if count > 0:
                metrics.filler_words[filler] = count

        # Formality score
        formal_count = sum(1 for w in all_words if w in self.FORMAL_INDICATORS)
        informal_count = sum(1 for w in all_words if w in self.INFORMAL_INDICATORS)
        informal_count += contractions_used
        informal_count += sum(metrics.filler_words.values())

        total_markers = formal_count + informal_count
        if total_markers > 0:
            metrics.formality_score = formal_count / total_markers
        else:
            metrics.formality_score = 0.5  # Neutral

        # Common phrases (2-4 word sequences that appear multiple times)
        metrics.common_phrases = self._find_common_phrases(all_text)

        # Signature words (words used more than average)
        word_counts = Counter(all_words)
        avg_count = len(all_words) / len(unique_words)
        signature = [
            word for word, count in word_counts.most_common(30)
            if count > avg_count * 2 and len(word) > 3
            and word not in {'that', 'this', 'with', 'have', 'from', 'they', 'been', 'were', 'said'}
        ]
        metrics.signature_words = signature[:15]

        # Emotion markers
        positive = sum(1 for w in all_words if w in self.POSITIVE_EMOTIONS)
        negative = sum(1 for w in all_words if w in self.NEGATIVE_EMOTIONS)
        total_emotion = positive + negative
        if total_emotion > 0:
            metrics.emotion_markers = {
                "positive": positive / total_emotion,
                "negative": negative / total_emotion,
                "neutral": 1 - (positive + negative) / len(all_words)
            }
        else:
            metrics.emotion_markers = {"positive": 0, "negative": 0, "neutral": 1}

        return metrics

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
        if len(word) <= 3:
            return 1

        count = len(re.findall(r'[aeiouy]+', word))
        if word.endswith('e'):
            count -= 1
        return max(1, count)

    def _find_common_phrases(self, text: str) -> List[Tuple[str, int]]:
        """Find repeated phrases (2-4 words)"""
        words = text.lower().split()
        phrases = Counter()

        for n in [2, 3, 4]:
            for i in range(len(words) - n + 1):
                phrase = ' '.join(words[i:i+n])
                # Skip phrases with only common words
                if any(w not in {'the', 'a', 'an', 'is', 'was', 'to', 'and', 'of', 'in', 'it', 'i'}
                       for w in words[i:i+n]):
                    phrases[phrase] += 1

        # Return phrases that appear more than once
        return [(p, c) for p, c in phrases.most_common(20) if c > 1]

    def build_voice_profile(
        self,
        manuscript_id: str,
        character_id: str,
        force_rebuild: bool = False
    ) -> CharacterVoiceProfile:
        """
        Build or update a voice profile for a character.

        Returns the profile with computed metrics from all dialogue.
        """
        # Check for existing profile
        existing = self.db.query(CharacterVoiceProfile).filter(
            CharacterVoiceProfile.manuscript_id == manuscript_id,
            CharacterVoiceProfile.character_id == character_id
        ).first()

        if existing and not force_rebuild:
            # Profile exists and not forcing rebuild
            return existing

        # Extract dialogue
        dialogue_samples = self.extract_character_dialogue(
            manuscript_id, character_id
        )

        # Compute metrics
        metrics = self.compute_voice_metrics(dialogue_samples)

        # Calculate confidence based on sample size
        # More samples = higher confidence
        confidence = min(1.0, metrics.dialogue_samples / 20)

        if existing:
            # Update existing profile
            existing.profile_data = metrics.to_dict()
            existing.confidence_score = confidence
            existing.calculated_at = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            return existing
        else:
            # Create new profile
            profile = CharacterVoiceProfile(
                id=str(uuid.uuid4()),
                character_id=character_id,
                manuscript_id=manuscript_id,
                profile_data=metrics.to_dict(),
                confidence_score=confidence,
                calculated_at=datetime.utcnow()
            )
            self.db.add(profile)
            self.db.commit()
            return profile

    def detect_inconsistencies(
        self,
        manuscript_id: str,
        character_id: str,
        chapter_id: Optional[str] = None
    ) -> List[VoiceInconsistency]:
        """
        Detect voice inconsistencies for a character.

        Compares dialogue in the specified chapter (or all chapters)
        against the established voice profile.
        """
        # Get or build profile
        profile = self.build_voice_profile(manuscript_id, character_id)

        if not profile.profile_data or profile.confidence_score < 0.3:
            # Not enough data for reliable detection
            return []

        profile_metrics = profile.profile_data
        inconsistencies = []

        # Get character for name variants
        character = self.db.query(Entity).filter(
            Entity.id == character_id
        ).first()

        if not character:
            return []

        name_variants = [character.name.lower()]
        if character.aliases:
            name_variants.extend([a.lower() for a in character.aliases])

        # Get chapters to analyze
        chapter_query = self.db.query(Chapter).filter(
            Chapter.manuscript_id == manuscript_id,
            Chapter.document_type == "CHAPTER"
        )
        if chapter_id:
            chapter_query = chapter_query.filter(Chapter.id == chapter_id)

        chapters = chapter_query.all()

        for chapter in chapters:
            if not chapter.content:
                continue

            # Extract dialogue from this chapter
            samples = self._extract_attributed_dialogue(
                chapter.content, chapter.id, name_variants
            )

            for sample in samples:
                # Analyze this sample against profile
                sample_issues = self._check_sample_consistency(
                    sample, profile_metrics, character, chapter.id
                )
                inconsistencies.extend(sample_issues)

        # Save inconsistencies to database
        for issue in inconsistencies:
            self.db.add(issue)

        if inconsistencies:
            self.db.commit()

        return inconsistencies

    def _check_sample_consistency(
        self,
        sample: DialogueSample,
        profile: Dict[str, Any],
        character: Entity,
        chapter_id: str
    ) -> List[VoiceInconsistency]:
        """
        Check a single dialogue sample against the voice profile.
        """
        issues = []

        # Compute metrics for this sample
        sample_metrics = self.compute_voice_metrics([sample])

        # Check sentence length (if significantly different)
        if profile.get("avg_sentence_length", 0) > 0:
            expected_len = profile["avg_sentence_length"]
            actual_len = sample_metrics.avg_sentence_length

            # Flag if more than 2x different
            if actual_len > expected_len * 2 or actual_len < expected_len * 0.5:
                if actual_len > 0:
                    issues.append(VoiceInconsistency(
                        id=str(uuid.uuid4()),
                        manuscript_id=character.manuscript_id,
                        character_id=character.id,
                        chapter_id=chapter_id,
                        inconsistency_type="SENTENCE_LENGTH",
                        severity="medium" if abs(actual_len - expected_len) > expected_len else "low",
                        description=(
                            f"{character.name}'s dialogue has unusual sentence length. "
                            f"They typically use {expected_len:.1f} words per sentence, "
                            f"but this passage averages {actual_len:.1f}."
                        ),
                        dialogue_excerpt=sample.text[:200],
                        start_offset=sample.start_offset,
                        end_offset=sample.end_offset,
                        expected_value=f"{expected_len:.1f} words/sentence",
                        actual_value=f"{actual_len:.1f} words/sentence",
                        suggestion=(
                            "Consider adjusting sentence length to match this character's "
                            "established speech pattern, unless the change is intentional "
                            "(e.g., emotional state, formal situation)."
                        ),
                        teaching_point=(
                            "Sentence length is a key voice marker. Short, punchy sentences "
                            "suggest urgency or simplicity. Longer sentences can indicate "
                            "thoughtfulness or verbosity. Consistency helps readers 'hear' "
                            "the character's voice."
                        )
                    ))

        # Check formality (if significantly different)
        if "formality_score" in profile:
            expected_formality = profile["formality_score"]
            actual_formality = sample_metrics.formality_score

            # Flag if formality shifts significantly
            if abs(expected_formality - actual_formality) > 0.4:
                direction = "more formal" if actual_formality > expected_formality else "less formal"
                issues.append(VoiceInconsistency(
                    id=str(uuid.uuid4()),
                    manuscript_id=character.manuscript_id,
                    character_id=character.id,
                    chapter_id=chapter_id,
                    inconsistency_type="FORMALITY",
                    severity="medium",
                    description=(
                        f"{character.name}'s dialogue sounds {direction} than usual. "
                        f"Their typical formality is {expected_formality:.0%}, "
                        f"but this passage is {actual_formality:.0%}."
                    ),
                    dialogue_excerpt=sample.text[:200],
                    start_offset=sample.start_offset,
                    end_offset=sample.end_offset,
                    expected_value=f"{expected_formality:.0%} formal",
                    actual_value=f"{actual_formality:.0%} formal",
                    suggestion=(
                        f"Review whether this formality shift is intentional. "
                        f"If not, consider {'adding contractions and casual language' if actual_formality > expected_formality else 'using more complete sentences'}."
                    ),
                    teaching_point=(
                        "Formality level - use of contractions, slang, versus proper grammar "
                        "- creates character voice. A character who normally says 'gonna' "
                        "suddenly saying 'going to' can feel off unless motivated by context."
                    )
                ))

        # Check vocabulary complexity
        if profile.get("vocabulary_complexity", 0) > 0:
            expected_complexity = profile["vocabulary_complexity"]
            actual_complexity = sample_metrics.vocabulary_complexity

            if abs(expected_complexity - actual_complexity) > 0.5:
                direction = "simpler" if actual_complexity < expected_complexity else "more complex"
                issues.append(VoiceInconsistency(
                    id=str(uuid.uuid4()),
                    manuscript_id=character.manuscript_id,
                    character_id=character.id,
                    chapter_id=chapter_id,
                    inconsistency_type="VOCABULARY",
                    severity="low",
                    description=(
                        f"{character.name}'s vocabulary seems {direction} than usual."
                    ),
                    dialogue_excerpt=sample.text[:200],
                    start_offset=sample.start_offset,
                    end_offset=sample.end_offset,
                    expected_value=f"~{expected_complexity:.1f} syllables/word",
                    actual_value=f"~{actual_complexity:.1f} syllables/word",
                    suggestion=(
                        "Consider whether the vocabulary matches this character's "
                        "education level and typical speech patterns."
                    ),
                    teaching_point=(
                        "Vocabulary complexity reflects character background. A scholar "
                        "uses different words than a street kid. Maintaining this "
                        "distinction keeps characters authentic."
                    )
                ))

        return issues

    def compare_voices(
        self,
        manuscript_id: str,
        character_a_id: str,
        character_b_id: str
    ) -> VoiceComparison:
        """
        Compare two character voices for distinctiveness.

        Returns a comparison showing how similar/different their voices are.
        """
        # Build profiles for both characters
        profile_a = self.build_voice_profile(manuscript_id, character_a_id)
        profile_b = self.build_voice_profile(manuscript_id, character_b_id)

        # Get character names
        char_a = self.db.query(Entity).filter(Entity.id == character_a_id).first()
        char_b = self.db.query(Entity).filter(Entity.id == character_b_id).first()

        metrics_a = profile_a.profile_data or {}
        metrics_b = profile_b.profile_data or {}

        # Calculate similarities
        vocab_sim = self._similarity(
            metrics_a.get("vocabulary_complexity", 0),
            metrics_b.get("vocabulary_complexity", 0),
            max_diff=1.0
        )

        structure_sim = self._similarity(
            metrics_a.get("avg_sentence_length", 0),
            metrics_b.get("avg_sentence_length", 0),
            max_diff=10.0
        )

        formality_sim = self._similarity(
            metrics_a.get("formality_score", 0.5),
            metrics_b.get("formality_score", 0.5),
            max_diff=1.0
        )

        overall_sim = (vocab_sim + structure_sim + formality_sim) / 3

        # Find distinguishing features
        features_a = []
        features_b = []
        shared = []

        # Sentence length
        len_a = metrics_a.get("avg_sentence_length", 0)
        len_b = metrics_b.get("avg_sentence_length", 0)
        if len_a > len_b + 3:
            features_a.append("longer sentences")
            features_b.append("shorter sentences")
        elif len_b > len_a + 3:
            features_b.append("longer sentences")
            features_a.append("shorter sentences")
        else:
            shared.append("similar sentence length")

        # Formality
        form_a = metrics_a.get("formality_score", 0.5)
        form_b = metrics_b.get("formality_score", 0.5)
        if form_a > form_b + 0.2:
            features_a.append("more formal speech")
            features_b.append("more casual speech")
        elif form_b > form_a + 0.2:
            features_b.append("more formal speech")
            features_a.append("more casual speech")

        # Contractions
        contr_a = metrics_a.get("contraction_rate", 0)
        contr_b = metrics_b.get("contraction_rate", 0)
        if contr_a > contr_b + 0.05:
            features_a.append("uses more contractions")
        elif contr_b > contr_a + 0.05:
            features_b.append("uses more contractions")

        # Questions
        q_a = metrics_a.get("question_rate", 0)
        q_b = metrics_b.get("question_rate", 0)
        if q_a > q_b + 0.1:
            features_a.append("asks more questions")
        elif q_b > q_a + 0.1:
            features_b.append("asks more questions")

        # Signature words
        sig_a = set(metrics_a.get("signature_words", []))
        sig_b = set(metrics_b.get("signature_words", []))
        unique_a = sig_a - sig_b
        unique_b = sig_b - sig_a
        if unique_a:
            features_a.append(f"distinctive words: {', '.join(list(unique_a)[:3])}")
        if unique_b:
            features_b.append(f"distinctive words: {', '.join(list(unique_b)[:3])}")

        # Generate recommendations
        recommendations = []
        if overall_sim > 0.8:
            recommendations.append(
                f"Consider differentiating {char_a.name} and {char_b.name}'s voices more. "
                "They currently sound quite similar."
            )
            if form_a == form_b:
                recommendations.append(
                    "Try giving one character more formal speech patterns."
                )
            if len_a == len_b:
                recommendations.append(
                    "Vary sentence length - one could be more terse, the other more verbose."
                )

        comparison = VoiceComparison(
            id=str(uuid.uuid4()),
            manuscript_id=manuscript_id,
            character_a_id=character_a_id,
            character_b_id=character_b_id,
            overall_similarity=overall_sim,
            vocabulary_similarity=vocab_sim,
            structure_similarity=structure_sim,
            formality_similarity=formality_sim,
            comparison_data={
                "distinguishing_features_a": features_a,
                "distinguishing_features_b": features_b,
                "shared_traits": shared,
                "recommendations": recommendations,
                "character_a_name": char_a.name if char_a else "Unknown",
                "character_b_name": char_b.name if char_b else "Unknown",
            }
        )

        self.db.add(comparison)
        self.db.commit()

        return comparison

    def _similarity(self, a: float, b: float, max_diff: float) -> float:
        """Calculate similarity score (0-1) between two values"""
        diff = abs(a - b)
        return max(0, 1 - (diff / max_diff))

    def get_manuscript_voice_summary(
        self,
        manuscript_id: str
    ) -> Dict[str, Any]:
        """
        Get a summary of all character voices in a manuscript.

        Useful for an overview dashboard.
        """
        # Get all character entities
        characters = self.db.query(Entity).filter(
            Entity.manuscript_id == manuscript_id,
            Entity.type == "CHARACTER"
        ).all()

        profiles = []
        for char in characters:
            profile = self.db.query(CharacterVoiceProfile).filter(
                CharacterVoiceProfile.manuscript_id == manuscript_id,
                CharacterVoiceProfile.character_id == char.id
            ).first()

            profiles.append({
                "character_id": char.id,
                "character_name": char.name,
                "has_profile": profile is not None,
                "confidence": profile.confidence_score if profile else 0,
                "dialogue_samples": profile.profile_data.get("dialogue_samples", 0) if profile and profile.profile_data else 0,
            })

        # Get open inconsistencies
        open_issues = self.db.query(VoiceInconsistency).filter(
            VoiceInconsistency.manuscript_id == manuscript_id,
            VoiceInconsistency.is_resolved == 0
        ).count()

        return {
            "characters": profiles,
            "total_characters": len(characters),
            "characters_with_profiles": sum(1 for p in profiles if p["has_profile"]),
            "open_inconsistencies": open_issues,
        }
