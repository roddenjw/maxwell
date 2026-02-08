"""
Culture Service - Culture-specific queries and context resolution.

Delegates to WikiService for CRUD and adds culture-specific logic:
- Linking entities to cultures with relationship types
- Resolving cultural context for characters (values, taboos, norms)
- Formatting culture data for LLM prompts
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.wiki import (
    WikiEntry, WikiCrossReference, WikiEntryType, WikiReferenceType
)
from app.models.world_rule import WorldRule
from app.services.wiki_service import WikiService


# Reference types that indicate culture relationships
CULTURE_REFERENCE_TYPES = {
    WikiReferenceType.BORN_IN.value,
    WikiReferenceType.EXILED_FROM.value,
    WikiReferenceType.ADOPTED_INTO.value,
    WikiReferenceType.LEADER_OF.value,
    WikiReferenceType.REBEL_AGAINST.value,
    WikiReferenceType.WORSHIPS.value,
    WikiReferenceType.TRADES_WITH.value,
    WikiReferenceType.ORIGINATED_IN.value,
    WikiReferenceType.SACRED_TO.value,
    WikiReferenceType.RESENTS.value,
    WikiReferenceType.MEMBER_OF.value,
    WikiReferenceType.PART_OF.value,
    WikiReferenceType.LOCATED_IN.value,
}

# Relationship types that imply tension or conflict with the culture
TENSION_TYPES = {
    WikiReferenceType.EXILED_FROM.value,
    WikiReferenceType.REBEL_AGAINST.value,
    WikiReferenceType.RESENTS.value,
}

# Relationship types that imply belonging or allegiance
BELONGING_TYPES = {
    WikiReferenceType.BORN_IN.value,
    WikiReferenceType.ADOPTED_INTO.value,
    WikiReferenceType.MEMBER_OF.value,
    WikiReferenceType.LEADER_OF.value,
    WikiReferenceType.WORSHIPS.value,
}


class CultureService:
    """Culture-specific queries layered on top of WikiService"""

    def __init__(self, db: Session):
        self.db = db
        self.wiki_service = WikiService(db)

    def link_entity_to_culture(
        self,
        entity_entry_id: str,
        culture_entry_id: str,
        reference_type: str,
        context: Optional[str] = None,
        created_by: str = "author"
    ) -> WikiCrossReference:
        """Create a culture link between an entity and a culture wiki entry."""
        return self.wiki_service.create_reference(
            source_entry_id=entity_entry_id,
            target_entry_id=culture_entry_id,
            reference_type=reference_type,
            context=context,
            bidirectional=True,
            created_by=created_by
        )

    def unlink_entity_from_culture(self, reference_id: str) -> bool:
        """Remove a culture link."""
        return self.wiki_service.delete_reference(reference_id)

    def get_entity_cultures(self, entry_id: str) -> List[Dict[str, Any]]:
        """Get all cultures an entity is linked to, with relationship details."""
        # Outgoing refs where target is a culture
        outgoing = self.db.query(WikiCrossReference, WikiEntry).join(
            WikiEntry, WikiCrossReference.target_entry_id == WikiEntry.id
        ).filter(
            WikiCrossReference.source_entry_id == entry_id,
            WikiEntry.entry_type == WikiEntryType.CULTURE.value,
            WikiCrossReference.reference_type.in_(CULTURE_REFERENCE_TYPES)
        ).all()

        # Incoming refs where source is a culture (bidirectional)
        incoming = self.db.query(WikiCrossReference, WikiEntry).join(
            WikiEntry, WikiCrossReference.source_entry_id == WikiEntry.id
        ).filter(
            WikiCrossReference.target_entry_id == entry_id,
            WikiEntry.entry_type == WikiEntryType.CULTURE.value,
            WikiCrossReference.bidirectional == 1,
            WikiCrossReference.reference_type.in_(CULTURE_REFERENCE_TYPES)
        ).all()

        results = []
        seen_ids = set()

        for ref, culture in outgoing:
            if ref.id not in seen_ids:
                seen_ids.add(ref.id)
                results.append({
                    "reference_id": ref.id,
                    "culture_id": culture.id,
                    "culture_title": culture.title,
                    "reference_type": ref.reference_type,
                    "context": ref.context,
                    "direction": "outgoing",
                    "structured_data": culture.structured_data or {},
                })

        for ref, culture in incoming:
            if ref.id not in seen_ids:
                seen_ids.add(ref.id)
                results.append({
                    "reference_id": ref.id,
                    "culture_id": culture.id,
                    "culture_title": culture.title,
                    "reference_type": ref.reference_type,
                    "context": ref.context,
                    "direction": "incoming",
                    "structured_data": culture.structured_data or {},
                })

        return results

    def get_culture_members(
        self,
        culture_id: str,
        member_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all entities linked to a culture, optionally filtered by type."""
        # Incoming refs where source entity links TO this culture
        incoming = self.db.query(WikiCrossReference, WikiEntry).join(
            WikiEntry, WikiCrossReference.source_entry_id == WikiEntry.id
        ).filter(
            WikiCrossReference.target_entry_id == culture_id,
            WikiCrossReference.reference_type.in_(CULTURE_REFERENCE_TYPES)
        )

        # Outgoing refs FROM this culture (bidirectional)
        outgoing = self.db.query(WikiCrossReference, WikiEntry).join(
            WikiEntry, WikiCrossReference.target_entry_id == WikiEntry.id
        ).filter(
            WikiCrossReference.source_entry_id == culture_id,
            WikiCrossReference.bidirectional == 1,
            WikiCrossReference.reference_type.in_(CULTURE_REFERENCE_TYPES)
        )

        if member_type:
            incoming = incoming.filter(WikiEntry.entry_type == member_type)
            outgoing = outgoing.filter(WikiEntry.entry_type == member_type)

        results = []
        seen_ids = set()

        for ref, entity in incoming.all():
            if entity.id not in seen_ids:
                seen_ids.add(entity.id)
                results.append({
                    "reference_id": ref.id,
                    "entity_id": entity.id,
                    "entity_title": entity.title,
                    "entity_type": entity.entry_type,
                    "reference_type": ref.reference_type,
                    "context": ref.context,
                })

        for ref, entity in outgoing.all():
            if entity.id not in seen_ids:
                seen_ids.add(entity.id)
                results.append({
                    "reference_id": ref.id,
                    "entity_id": entity.id,
                    "entity_title": entity.title,
                    "entity_type": entity.entry_type,
                    "reference_type": ref.reference_type,
                    "context": ref.context,
                })

        return results

    def get_culture_children(self, culture_id: str) -> List[Dict[str, Any]]:
        """Get wiki entries with parent_id set to this culture."""
        children = self.db.query(WikiEntry).filter(
            WikiEntry.parent_id == culture_id
        ).order_by(WikiEntry.title).all()

        return [
            {
                "id": child.id,
                "title": child.title,
                "entry_type": child.entry_type,
                "summary": child.summary,
            }
            for child in children
        ]

    def get_character_cultural_context(
        self,
        character_name: str,
        world_id: str
    ) -> Dict[str, Any]:
        """
        Resolve full cultural context for a character.

        Returns cultures, values, taboos, behavioral norms, speech patterns,
        and cultural tensions derived from relationship types.
        """
        # Find character entry
        entry = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.CHARACTER.value,
            or_(
                WikiEntry.title.ilike(f"%{character_name}%"),
            )
        ).first()

        if not entry:
            return {"found": False, "character_name": character_name}

        # Get culture links
        cultures = self.get_entity_cultures(entry.id)

        if not cultures:
            return {
                "found": True,
                "character_name": entry.title,
                "has_cultures": False,
                "cultures": [],
                "cultural_tensions": [],
            }

        # Analyze tensions
        belonging_cultures = []
        tension_cultures = []
        cultural_tensions = []

        for c in cultures:
            ref_type = c["reference_type"]
            if ref_type in TENSION_TYPES:
                tension_cultures.append(c)
            if ref_type in BELONGING_TYPES:
                belonging_cultures.append(c)

        # Detect cross-cultural tensions
        for tc in tension_cultures:
            for bc in belonging_cultures:
                if tc["culture_id"] == bc["culture_id"]:
                    cultural_tensions.append(
                        f"{ref_type_label(bc['reference_type'])} {bc['culture_title']} "
                        f"but {ref_type_label(tc['reference_type'])} — "
                        f"may resent traditions while unconsciously following them"
                    )
                else:
                    cultural_tensions.append(
                        f"Belongs to {bc['culture_title']} but "
                        f"{ref_type_label(tc['reference_type'])} {tc['culture_title']} — "
                        f"potential divided loyalties"
                    )

        # Gather cultural facts from structured_data
        all_values = []
        all_taboos = []
        all_norms = []
        all_speech = []

        for c in cultures:
            sd = c.get("structured_data", {})
            all_values.extend(sd.get("values", []))
            all_taboos.extend(sd.get("taboos", []))
            all_norms.extend(sd.get("behavioral_norms", sd.get("customs", [])))
            all_speech.extend(sd.get("speech_patterns", sd.get("language", [])))

        return {
            "found": True,
            "character_name": entry.title,
            "character_id": entry.id,
            "has_cultures": True,
            "cultures": [
                {
                    "culture_id": c["culture_id"],
                    "culture_title": c["culture_title"],
                    "reference_type": c["reference_type"],
                    "context": c["context"],
                }
                for c in cultures
            ],
            "values": all_values,
            "taboos": all_taboos,
            "behavioral_norms": all_norms,
            "speech_patterns": all_speech,
            "cultural_tensions": cultural_tensions,
        }

    def get_culture_facts(self, culture_id: str) -> Dict[str, Any]:
        """Get all facts about a culture — members, children, rules, relationships."""
        culture = self.wiki_service.get_entry(culture_id)
        if not culture:
            return {"found": False}

        members = self.get_culture_members(culture_id)
        children = self.get_culture_children(culture_id)

        # Get cultural rules
        rules = self.db.query(WorldRule).filter(
            WorldRule.wiki_entry_id == culture_id,
            WorldRule.is_active == 1
        ).all()

        return {
            "found": True,
            "culture_id": culture.id,
            "title": culture.title,
            "summary": culture.summary,
            "content": culture.content,
            "structured_data": culture.structured_data or {},
            "members": members,
            "children": children,
            "rules": [
                {
                    "id": r.id,
                    "rule_name": r.rule_name,
                    "rule_description": r.rule_description,
                    "severity": r.severity,
                }
                for r in rules
            ],
            "member_count": len(members),
            "children_count": len(children),
        }

    def get_world_cultures(self, world_id: str) -> List[Dict[str, Any]]:
        """Get all cultures in a world with member counts."""
        cultures = self.db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.CULTURE.value
        ).order_by(WikiEntry.title).all()

        results = []
        for culture in cultures:
            members = self.get_culture_members(culture.id)
            results.append({
                "id": culture.id,
                "title": culture.title,
                "summary": culture.summary,
                "structured_data": culture.structured_data or {},
                "member_count": len(members),
            })

        return results

    def format_culture_for_prompt(self, culture_id: str) -> str:
        """Format a culture's data as readable text for LLM prompts."""
        facts = self.get_culture_facts(culture_id)
        if not facts.get("found"):
            return ""

        parts = [f"### Culture: {facts['title']}"]

        if facts.get("summary"):
            parts.append(facts["summary"])

        sd = facts.get("structured_data", {})

        if sd.get("values"):
            parts.append(f"\nValues: {', '.join(sd['values'])}")
        if sd.get("taboos"):
            parts.append(f"Taboos: {', '.join(sd['taboos'])}")
        if sd.get("customs"):
            parts.append(f"Customs: {', '.join(sd['customs'])}")
        if sd.get("social_structure"):
            val = sd["social_structure"]
            if isinstance(val, list):
                parts.append(f"Social Structure: {', '.join(val)}")
            else:
                parts.append(f"Social Structure: {val}")
        if sd.get("speech_patterns"):
            parts.append(f"Speech Patterns: {', '.join(sd['speech_patterns'])}")

        if facts.get("rules"):
            parts.append("\nCultural Rules:")
            for r in facts["rules"]:
                parts.append(f"  - {r['rule_name']}: {r.get('rule_description', '')}")

        if facts.get("members"):
            # Group by type
            by_type: Dict[str, List[str]] = {}
            for m in facts["members"]:
                t = m["entity_type"]
                if t not in by_type:
                    by_type[t] = []
                by_type[t].append(f"{m['entity_title']} ({ref_type_label(m['reference_type'])})")

            parts.append(f"\nMembers ({facts['member_count']}):")
            for etype, names in by_type.items():
                parts.append(f"  {etype}: {', '.join(names[:10])}")

        return "\n".join(parts)

    def format_character_culture_summary(
        self,
        character_name: str,
        world_id: str
    ) -> str:
        """Compact character cultural context for agent prompts."""
        ctx = self.get_character_cultural_context(character_name, world_id)

        if not ctx.get("found") or not ctx.get("has_cultures"):
            return ""

        parts = [f"Cultural Background for {ctx['character_name']}:"]

        for c in ctx["cultures"]:
            label = ref_type_label(c["reference_type"])
            parts.append(f"  - {label} {c['culture_title']}")
            if c.get("context"):
                parts.append(f"    ({c['context']})")

        if ctx.get("values"):
            parts.append(f"  Values: {', '.join(ctx['values'][:5])}")
        if ctx.get("taboos"):
            parts.append(f"  Taboos: {', '.join(ctx['taboos'][:5])}")
        if ctx.get("behavioral_norms"):
            parts.append(f"  Norms: {', '.join(ctx['behavioral_norms'][:5])}")
        if ctx.get("speech_patterns"):
            parts.append(f"  Speech: {', '.join(ctx['speech_patterns'][:5])}")
        if ctx.get("cultural_tensions"):
            parts.append("  Tensions:")
            for t in ctx["cultural_tensions"]:
                parts.append(f"    - {t}")

        return "\n".join(parts)


def ref_type_label(ref_type: str) -> str:
    """Human-readable label for a reference type."""
    labels = {
        "born_in": "Born in",
        "exiled_from": "Exiled from",
        "adopted_into": "Adopted into",
        "leader_of": "Leader of",
        "rebel_against": "Rebel against",
        "worships": "Worships",
        "trades_with": "Trades with",
        "originated_in": "Originated in",
        "sacred_to": "Sacred to",
        "resents": "Resents",
        "member_of": "Member of",
        "part_of": "Part of",
        "located_in": "Located in",
    }
    return labels.get(ref_type, ref_type.replace("_", " ").title())
