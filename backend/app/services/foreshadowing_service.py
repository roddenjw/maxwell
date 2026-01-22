"""
Foreshadowing Service

Manages foreshadowing setup/payoff pairs for narrative tracking.
Includes:
- CRUD operations for foreshadowing pairs
- Chekhov's gun violation detection (unresolved setups)
- Potential payoff suggestions
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database import SessionLocal
from app.models.foreshadowing import ForeshadowingPair, ForeshadowingType
from app.models.timeline import TimelineEvent


class ForeshadowingService:
    """Service for managing foreshadowing pairs"""

    def create_foreshadowing_pair(
        self,
        manuscript_id: str,
        foreshadowing_event_id: str,
        foreshadowing_type: str,
        foreshadowing_text: str,
        payoff_event_id: Optional[str] = None,
        payoff_text: Optional[str] = None,
        confidence: int = 5,
        notes: Optional[str] = None,
    ) -> ForeshadowingPair:
        """
        Create a new foreshadowing setup/payoff pair.

        Args:
            manuscript_id: ID of the manuscript
            foreshadowing_event_id: ID of the event where setup occurs
            foreshadowing_type: Type (CHEKHOV_GUN, PROPHECY, SYMBOL, HINT, PARALLEL)
            foreshadowing_text: Description of the setup
            payoff_event_id: Optional ID of the event where payoff occurs
            payoff_text: Optional description of the payoff
            confidence: 1-10 scale of how obvious the connection is
            notes: Author's notes

        Returns:
            Created ForeshadowingPair
        """
        db = SessionLocal()
        try:
            pair = ForeshadowingPair(
                manuscript_id=manuscript_id,
                foreshadowing_event_id=foreshadowing_event_id,
                foreshadowing_type=foreshadowing_type,
                foreshadowing_text=foreshadowing_text,
                payoff_event_id=payoff_event_id,
                payoff_text=payoff_text,
                is_resolved=1 if payoff_event_id else 0,
                confidence=confidence,
                notes=notes,
            )
            db.add(pair)
            db.commit()
            db.refresh(pair)
            return pair
        finally:
            db.close()

    def get_foreshadowing_pairs(
        self,
        manuscript_id: str,
        include_resolved: bool = True,
        foreshadowing_type: Optional[str] = None,
    ) -> List[ForeshadowingPair]:
        """
        Get all foreshadowing pairs for a manuscript.

        Args:
            manuscript_id: ID of the manuscript
            include_resolved: Whether to include resolved pairs
            foreshadowing_type: Optional filter by type

        Returns:
            List of ForeshadowingPair objects
        """
        db = SessionLocal()
        try:
            query = db.query(ForeshadowingPair).filter(
                ForeshadowingPair.manuscript_id == manuscript_id
            )

            if not include_resolved:
                query = query.filter(ForeshadowingPair.is_resolved == 0)

            if foreshadowing_type:
                query = query.filter(ForeshadowingPair.foreshadowing_type == foreshadowing_type)

            return query.order_by(ForeshadowingPair.created_at.desc()).all()
        finally:
            db.close()

    def get_foreshadowing_pair(self, pair_id: str) -> Optional[ForeshadowingPair]:
        """Get a single foreshadowing pair by ID"""
        db = SessionLocal()
        try:
            return db.query(ForeshadowingPair).filter(
                ForeshadowingPair.id == pair_id
            ).first()
        finally:
            db.close()

    def update_foreshadowing_pair(
        self,
        pair_id: str,
        foreshadowing_type: Optional[str] = None,
        foreshadowing_text: Optional[str] = None,
        payoff_event_id: Optional[str] = None,
        payoff_text: Optional[str] = None,
        confidence: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Optional[ForeshadowingPair]:
        """Update an existing foreshadowing pair"""
        db = SessionLocal()
        try:
            pair = db.query(ForeshadowingPair).filter(
                ForeshadowingPair.id == pair_id
            ).first()

            if not pair:
                return None

            if foreshadowing_type is not None:
                pair.foreshadowing_type = foreshadowing_type
            if foreshadowing_text is not None:
                pair.foreshadowing_text = foreshadowing_text
            if payoff_event_id is not None:
                pair.payoff_event_id = payoff_event_id
                pair.is_resolved = 1 if payoff_event_id else pair.is_resolved
            if payoff_text is not None:
                pair.payoff_text = payoff_text
            if confidence is not None:
                pair.confidence = confidence
            if notes is not None:
                pair.notes = notes

            pair.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(pair)
            return pair
        finally:
            db.close()

    def delete_foreshadowing_pair(self, pair_id: str) -> bool:
        """Delete a foreshadowing pair"""
        db = SessionLocal()
        try:
            pair = db.query(ForeshadowingPair).filter(
                ForeshadowingPair.id == pair_id
            ).first()

            if not pair:
                return False

            db.delete(pair)
            db.commit()
            return True
        finally:
            db.close()

    def link_payoff(
        self,
        pair_id: str,
        payoff_event_id: str,
        payoff_text: str,
    ) -> Optional[ForeshadowingPair]:
        """
        Link a payoff event to an existing foreshadowing setup.

        This marks the pair as resolved.
        """
        db = SessionLocal()
        try:
            pair = db.query(ForeshadowingPair).filter(
                ForeshadowingPair.id == pair_id
            ).first()

            if not pair:
                return None

            pair.payoff_event_id = payoff_event_id
            pair.payoff_text = payoff_text
            pair.is_resolved = 1
            pair.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(pair)
            return pair
        finally:
            db.close()

    def unlink_payoff(self, pair_id: str) -> Optional[ForeshadowingPair]:
        """
        Remove the payoff from a foreshadowing pair.

        This marks the pair as unresolved.
        """
        db = SessionLocal()
        try:
            pair = db.query(ForeshadowingPair).filter(
                ForeshadowingPair.id == pair_id
            ).first()

            if not pair:
                return None

            pair.payoff_event_id = None
            pair.payoff_text = None
            pair.is_resolved = 0
            pair.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(pair)
            return pair
        finally:
            db.close()

    def get_unresolved_foreshadowing(
        self,
        manuscript_id: str
    ) -> List[ForeshadowingPair]:
        """
        Get all unresolved foreshadowing setups (Chekhov violations).

        These are setups that haven't been linked to a payoff event.
        Writers should review these to ensure all setups have payoffs.
        """
        return self.get_foreshadowing_pairs(
            manuscript_id=manuscript_id,
            include_resolved=False
        )

    def get_foreshadowing_for_event(
        self,
        event_id: str
    ) -> Dict[str, List[ForeshadowingPair]]:
        """
        Get all foreshadowing pairs involving a specific event.

        Returns:
            Dict with 'setups' (pairs where event is the setup)
            and 'payoffs' (pairs where event is the payoff)
        """
        db = SessionLocal()
        try:
            setups = db.query(ForeshadowingPair).filter(
                ForeshadowingPair.foreshadowing_event_id == event_id
            ).all()

            payoffs = db.query(ForeshadowingPair).filter(
                ForeshadowingPair.payoff_event_id == event_id
            ).all()

            return {
                "setups": setups,
                "payoffs": payoffs,
            }
        finally:
            db.close()

    def get_foreshadowing_stats(
        self,
        manuscript_id: str
    ) -> Dict[str, Any]:
        """
        Get foreshadowing statistics for a manuscript.

        Returns counts by type, resolution status, and confidence distribution.
        """
        db = SessionLocal()
        try:
            pairs = db.query(ForeshadowingPair).filter(
                ForeshadowingPair.manuscript_id == manuscript_id
            ).all()

            total = len(pairs)
            resolved = sum(1 for p in pairs if p.is_resolved)
            unresolved = total - resolved

            # Count by type
            by_type = {}
            for p in pairs:
                by_type[p.foreshadowing_type] = by_type.get(p.foreshadowing_type, 0) + 1

            # Confidence distribution
            confidence_sum = sum(p.confidence for p in pairs)
            avg_confidence = confidence_sum / total if total > 0 else 0

            return {
                "total": total,
                "resolved": resolved,
                "unresolved": unresolved,
                "by_type": by_type,
                "average_confidence": round(avg_confidence, 1),
            }
        finally:
            db.close()

    def suggest_potential_payoffs(
        self,
        pair_id: str
    ) -> List[Dict[str, Any]]:
        """
        Suggest potential payoff events for an unresolved foreshadowing setup.

        Uses keyword matching and event proximity to find candidates.
        This is a simple heuristic - AI-powered suggestions would be better.
        """
        db = SessionLocal()
        try:
            pair = db.query(ForeshadowingPair).filter(
                ForeshadowingPair.id == pair_id
            ).first()

            if not pair:
                return []

            # Get the setup event
            setup_event = db.query(TimelineEvent).filter(
                TimelineEvent.id == pair.foreshadowing_event_id
            ).first()

            if not setup_event:
                return []

            # Get all events after the setup event
            later_events = db.query(TimelineEvent).filter(
                TimelineEvent.manuscript_id == pair.manuscript_id,
                TimelineEvent.order_index > setup_event.order_index
            ).order_by(TimelineEvent.order_index).all()

            # Simple keyword matching from foreshadowing text
            keywords = set(
                word.lower()
                for word in pair.foreshadowing_text.split()
                if len(word) > 3
            )

            suggestions = []
            for event in later_events:
                # Score based on keyword overlap
                event_words = set(
                    word.lower()
                    for word in event.description.split()
                    if len(word) > 3
                )
                overlap = len(keywords & event_words)

                if overlap > 0:
                    suggestions.append({
                        "event_id": event.id,
                        "description": event.description[:150],
                        "order_index": event.order_index,
                        "keyword_matches": overlap,
                        "score": overlap,  # Simple scoring
                    })

            # Sort by score and return top 5
            suggestions.sort(key=lambda x: x["score"], reverse=True)
            return suggestions[:5]

        finally:
            db.close()


# Singleton instance
foreshadowing_service = ForeshadowingService()
