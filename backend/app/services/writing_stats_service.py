"""
Writing Statistics Service
Generates stats for "Wrapped"-style recap cards
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter
import re
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.manuscript import Manuscript
from app.models.versioning import Snapshot


class WritingStatsService:
    """Calculate writing statistics for recap cards"""

    # Sensory words categorized by sense
    SENSORY_WORDS = {
        'sight': ['crimson', 'glowing', 'shadowy', 'brilliant', 'gleaming', 'dark', 'bright', 'shimmering',
                  'golden', 'silver', 'azure', 'emerald', 'scarlet', 'ivory', 'obsidian'],
        'sound': ['whispered', 'echoed', 'silence', 'roared', 'murmured', 'screamed', 'rustled',
                  'thundered', 'hummed', 'chimed', 'crackled', 'boomed'],
        'touch': ['rough', 'smooth', 'cold', 'warm', 'soft', 'hard', 'silky', 'coarse',
                  'sharp', 'gentle', 'tender', 'harsh'],
        'smell': ['fragrant', 'acrid', 'sweet', 'musty', 'pungent', 'fresh', 'rotten', 'floral'],
        'taste': ['bitter', 'savory', 'sour', 'sweet', 'tangy', 'spicy', 'bland', 'rich']
    }

    # Emotional tone indicators
    TONE_KEYWORDS = {
        'triumphant': ['victory', 'triumph', 'success', 'glory', 'conquest', 'achieved', 'won'],
        'hopeful': ['hope', 'dream', 'wish', 'aspire', 'believe', 'faith', 'optimism'],
        'contemplative': ['wonder', 'ponder', 'consider', 'reflect', 'think', 'muse'],
        'melancholic': ['sorrow', 'sadness', 'grief', 'loss', 'tears', 'mourning', 'regret'],
        'dramatic': ['suddenly', 'crashed', 'exploded', 'shattered', 'blazing', 'fierce']
    }

    def __init__(self, db: Session):
        self.db = db

    async def generate_session_recap(
        self,
        manuscript_id: str,
        timeframe: str = 'week'  # 'session', 'day', 'week', 'month', 'all_time'
    ) -> Dict:
        """Generate comprehensive stats for recap card"""

        # Get all text from chapters (where the actual content lives)
        from app.models.manuscript import Chapter
        chapters = self.db.query(Chapter).filter(
            and_(
                Chapter.manuscript_id == manuscript_id,
                Chapter.is_folder == 0  # Only chapters, not folders
            )
        ).all()

        # Check if manuscript has any content at all
        if not chapters:
            # Check if manuscript exists in manuscripts table
            manuscript = self.db.query(Manuscript).filter_by(id=manuscript_id).first()
            if not manuscript and not chapters:
                raise ValueError(f"Manuscript {manuscript_id} not found")

        # Calculate time range
        end_time = datetime.utcnow()
        start_time = self._get_start_time(timeframe, end_time)

        # Get snapshots in timeframe
        snapshots = self.db.query(Snapshot).filter(
            and_(
                Snapshot.manuscript_id == manuscript_id,
                Snapshot.created_at >= start_time,
                Snapshot.created_at <= end_time
            )
        ).order_by(Snapshot.created_at.asc()).all()

        # Combine all chapter content
        all_text = ' '.join([chapter.content or '' for chapter in chapters])
        text_written = all_text

        # Calculate total word count from all chapters
        total_words = sum(chapter.word_count or 0 for chapter in chapters)

        # Calculate metrics
        stats = {
            'timeframe': timeframe,
            'timeframe_label': self._get_timeframe_label(timeframe),

            # Basic metrics
            'word_count': self._count_words(text_written),
            'character_count': len(text_written),
            'paragraph_count': text_written.count('\n\n'),
            'session_count': len(snapshots),

            # Advanced metrics
            'sensory_words': self._extract_sensory_words(text_written),
            'most_used_word': self._get_most_common_word(text_written),
            'writing_vibe': self._analyze_emotional_tone(text_written),
            'avg_words_per_session': self._count_words(text_written) // max(len(snapshots), 1),

            # Streak data
            'writing_days': len(self._get_writing_days(snapshots)),
            'longest_streak': self._calculate_longest_streak(manuscript_id, end_time),

            # Total manuscript stats
            'total_words': total_words,
            'total_chapters': len(chapters),
        }

        return stats

    def _get_start_time(self, timeframe: str, end_time: datetime) -> datetime:
        """Calculate start time based on timeframe"""
        if timeframe == 'day':
            return end_time - timedelta(days=1)
        elif timeframe == 'week':
            return end_time - timedelta(days=7)
        elif timeframe == 'month':
            return end_time - timedelta(days=30)
        elif timeframe == 'all_time':
            return datetime(2000, 1, 1)  # Far in past
        else:  # session (last snapshot)
            return end_time - timedelta(hours=24)

    def _get_timeframe_label(self, timeframe: str) -> str:
        """Get human-readable timeframe label"""
        labels = {
            'day': 'Today',
            'week': 'This Week',
            'month': 'This Month',
            'all_time': 'All Time',
            'session': 'This Session'
        }
        return labels.get(timeframe, timeframe.title())

    def _calculate_text_delta(self, snapshots: List[Snapshot], current_content: str) -> str:
        """Calculate text added between first and last snapshot"""
        if not snapshots:
            return current_content

        # Get first snapshot content
        first_snapshot = snapshots[0]
        first_content = first_snapshot.content or ''

        # Compare with current content
        # For simplicity, we'll use the current content
        # In production, you'd do a proper diff
        return current_content

    def _count_words(self, text: str) -> int:
        """Count words in text"""
        if not text:
            return 0
        words = re.findall(r'\b\w+\b', text)
        return len(words)

    def _extract_sensory_words(self, text: str) -> Dict[str, List[tuple]]:
        """Find sensory words used in text"""
        if not text:
            return {}

        words = re.findall(r'\b\w+\b', text.lower())
        found = {}

        for sense, word_list in self.SENSORY_WORDS.items():
            matches = [w for w in words if w in word_list]
            if matches:
                # Count and get top 3
                counter = Counter(matches)
                found[sense] = counter.most_common(3)

        return found

    def _get_most_common_word(self, text: str, min_length: int = 5) -> Optional[str]:
        """Get most commonly used word (excluding common words)"""
        if not text:
            return None

        # Common words to exclude
        STOP_WORDS = {'the', 'and', 'was', 'were', 'have', 'been', 'that', 'this',
                      'with', 'from', 'they', 'would', 'there', 'their', 'what'}

        words = re.findall(r'\b\w+\b', text.lower())
        words = [w for w in words if len(w) >= min_length and w not in STOP_WORDS]

        if not words:
            return None

        counter = Counter(words)
        most_common = counter.most_common(1)
        return most_common[0][0] if most_common else None

    def _analyze_emotional_tone(self, text: str) -> str:
        """Classify overall writing vibe using spaCy sentiment analysis"""
        if not text:
            return "Contemplative"

        try:
            # Use spaCy for sophisticated NLP analysis
            from app.services.nlp_service import nlp_service

            if not nlp_service.is_available():
                # Fallback to keyword-based analysis
                return self._keyword_based_tone(text)

            # Analyze a sample of the text (first 5000 chars for performance)
            sample = text[:5000] if len(text) > 5000 else text
            doc = nlp_service.nlp(sample)

            # Count emotional keywords with context
            tone_scores = {}
            for sent in doc.sents:
                sent_text = sent.text.lower()
                for tone, keywords in self.TONE_KEYWORDS.items():
                    matches = sum(1 for keyword in keywords if keyword in sent_text)
                    tone_scores[tone] = tone_scores.get(tone, 0) + matches

            # Analyze sentence structure for dramatic vs contemplative
            avg_sent_length = sum(len(sent) for sent in doc.sents) / max(len(list(doc.sents)), 1)
            short_sentence_ratio = sum(1 for sent in doc.sents if len(sent) < 10) / max(len(list(doc.sents)), 1)

            # Short sentences suggest dramatic/action-oriented
            if short_sentence_ratio > 0.4 or avg_sent_length < 15:
                tone_scores['dramatic'] = tone_scores.get('dramatic', 0) + 2

            # Get the dominant tone
            if tone_scores:
                max_tone = max(tone_scores, key=tone_scores.get)
                if tone_scores[max_tone] > 0:
                    return max_tone.title()

            return "Contemplative"

        except Exception as e:
            # Fallback to keyword-based if spaCy fails
            return self._keyword_based_tone(text)

    def _keyword_based_tone(self, text: str) -> str:
        """Fallback keyword-based tone analysis"""
        text_lower = text.lower()
        scores = {}

        for tone, keywords in self.TONE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[tone] = score

        if scores:
            max_tone = max(scores, key=scores.get)
            if scores[max_tone] > 0:
                return max_tone.title()

        return "Contemplative"

    def _get_writing_days(self, snapshots: List[Snapshot]) -> set:
        """Get unique days when writing occurred"""
        days = set()
        for snapshot in snapshots:
            day = snapshot.created_at.date()
            days.add(day)
        return days

    def _calculate_longest_streak(self, manuscript_id: str, end_time: datetime) -> int:
        """Calculate longest consecutive writing streak"""
        # Get all snapshots for this manuscript (last 90 days for performance)
        start = end_time - timedelta(days=90)
        snapshots = self.db.query(Snapshot).filter(
            and_(
                Snapshot.manuscript_id == manuscript_id,
                Snapshot.created_at >= start,
                Snapshot.created_at <= end_time
            )
        ).order_by(Snapshot.created_at.asc()).all()

        if not snapshots:
            return 0

        # Get unique days
        days = sorted(list(self._get_writing_days(snapshots)))

        # Calculate longest streak
        max_streak = 1
        current_streak = 1

        for i in range(1, len(days)):
            if (days[i] - days[i-1]).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        return max_streak

    def _count_chapters(self, manuscript_id: str) -> int:
        """Count chapters in manuscript"""
        from app.models.manuscript import Chapter

        count = self.db.query(Chapter).filter(
            and_(
                Chapter.manuscript_id == manuscript_id,
                Chapter.is_folder == False
            )
        ).count()

        return count
