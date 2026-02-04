"""
Wiki Agent Tools - LangChain tools for Wiki queries.

Provides tools for agents to:
- Query wiki entries
- Get character facts
- Get world rules
- Check rule violations
- Suggest wiki updates
"""

from typing import List, Optional, Dict, Any
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.database import get_db


# ==================== Wiki Query Tools ====================

@tool
def query_wiki(
    world_id: str,
    query: str,
    entry_types: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search wiki entries by title, content, or aliases.

    Args:
        world_id: The world ID to search in
        query: Search query string
        entry_types: Comma-separated list of entry types to filter (optional)
        limit: Maximum results to return (default 10)

    Returns:
        List of matching wiki entries with id, title, type, and summary
    """
    from app.services.wiki_service import WikiService

    db = next(get_db())
    try:
        service = WikiService(db)
        types_list = entry_types.split(",") if entry_types else None

        entries = service.search_entries(
            world_id=world_id,
            query=query,
            entry_types=types_list,
            limit=limit
        )

        return {
            "found": len(entries),
            "entries": [
                {
                    "id": e.id,
                    "title": e.title,
                    "entry_type": e.entry_type,
                    "summary": e.summary,
                    "aliases": e.aliases or []
                }
                for e in entries
            ]
        }
    finally:
        db.close()


@tool
def get_character_facts(
    character_name: str,
    world_id: str
) -> Dict[str, Any]:
    """
    Get all known facts about a character from the wiki.

    Args:
        character_name: Name of the character to look up
        world_id: The world ID to search in

    Returns:
        Dictionary with character facts including attributes, relationships, arcs
    """
    from app.services.wiki_service import WikiConsistencyEngine

    db = next(get_db())
    try:
        engine = WikiConsistencyEngine(db)
        return engine.get_character_facts(character_name, world_id)
    finally:
        db.close()


@tool
def get_location_facts(
    location_name: str,
    world_id: str
) -> Dict[str, Any]:
    """
    Get all known facts about a location from the wiki.

    Args:
        location_name: Name of the location to look up
        world_id: The world ID to search in

    Returns:
        Dictionary with location facts including description, history, culture
    """
    from app.services.wiki_service import WikiConsistencyEngine

    db = next(get_db())
    try:
        engine = WikiConsistencyEngine(db)
        return engine.get_location_facts(location_name, world_id)
    finally:
        db.close()


@tool
def get_world_rules(
    world_id: str,
    rule_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get world rules for consistency validation.

    Args:
        world_id: The world ID to get rules for
        rule_type: Optional filter by rule type (magic_system, physical_law, social_rule, cultural, temporal)

    Returns:
        List of world rules with name, description, and validation patterns
    """
    from app.services.wiki_service import WikiConsistencyEngine

    db = next(get_db())
    try:
        engine = WikiConsistencyEngine(db)
        rules = engine.get_world_rules(world_id, rule_type)

        return {
            "count": len(rules),
            "rules": [
                {
                    "id": r.id,
                    "rule_name": r.rule_name,
                    "rule_type": r.rule_type,
                    "rule_description": r.rule_description,
                    "severity": r.severity,
                    "validation_keywords": r.validation_keywords or []
                }
                for r in rules
            ]
        }
    finally:
        db.close()


@tool
def check_rule_violations(
    text: str,
    world_id: str,
    rule_types: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check text against world rules for violations.

    Args:
        text: The text to check for rule violations
        world_id: The world ID with rules to check against
        rule_types: Optional comma-separated list of rule types to check

    Returns:
        List of potential violations with rule name, severity, and message
    """
    from app.services.wiki_service import WikiConsistencyEngine

    db = next(get_db())
    try:
        engine = WikiConsistencyEngine(db)
        types_list = rule_types.split(",") if rule_types else None

        violations = engine.validate_against_rules(
            text=text,
            world_id=world_id,
            rule_types=types_list
        )

        return {
            "violations_found": len(violations),
            "violations": violations
        }
    finally:
        db.close()


@tool
def get_relationship_state(
    char_a: str,
    char_b: str,
    world_id: str
) -> Dict[str, Any]:
    """
    Get the relationship state between two characters.

    Args:
        char_a: First character name
        char_b: Second character name
        world_id: The world ID to search in

    Returns:
        Relationship information including type, context, and history
    """
    from app.services.wiki_service import WikiConsistencyEngine

    db = next(get_db())
    try:
        engine = WikiConsistencyEngine(db)
        return engine.get_relationship_state(char_a, char_b, world_id)
    finally:
        db.close()


@tool
def get_all_characters(
    world_id: str
) -> Dict[str, Any]:
    """
    Get all characters in a world.

    Args:
        world_id: The world ID to get characters for

    Returns:
        List of all characters with their names, aliases, and summaries
    """
    from app.services.wiki_service import WikiConsistencyEngine

    db = next(get_db())
    try:
        engine = WikiConsistencyEngine(db)
        characters = engine.get_all_characters(world_id)

        return {
            "count": len(characters),
            "characters": characters
        }
    finally:
        db.close()


@tool
def get_all_locations(
    world_id: str
) -> Dict[str, Any]:
    """
    Get all locations in a world.

    Args:
        world_id: The world ID to get locations for

    Returns:
        List of all locations with their names, aliases, and summaries
    """
    from app.services.wiki_service import WikiConsistencyEngine

    db = next(get_db())
    try:
        engine = WikiConsistencyEngine(db)
        locations = engine.get_all_locations(world_id)

        return {
            "count": len(locations),
            "locations": locations
        }
    finally:
        db.close()


# ==================== Wiki Update Tools ====================

@tool
def suggest_wiki_update(
    world_id: str,
    change_type: str,
    entry_type: str,
    title: str,
    content: Optional[str] = None,
    summary: Optional[str] = None,
    reason: str = "Suggested by AI agent",
    source_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Suggest a wiki update for author approval.

    Args:
        world_id: The world ID to add entry to
        change_type: Type of change ('create', 'update', 'delete')
        entry_type: Type of wiki entry ('character', 'location', 'item', etc.)
        title: Title/name of the entry
        content: Full content for the entry (optional)
        summary: Short summary (optional)
        reason: Why this change is suggested
        source_text: Source text that prompted this suggestion (optional)

    Returns:
        Change request ID and status
    """
    from app.services.wiki_service import WikiService
    from app.models.wiki import WikiChangeType

    db = next(get_db())
    try:
        service = WikiService(db)

        # Build proposed entry
        proposed_entry = {
            "entry_type": entry_type,
            "title": title,
            "content": content,
            "summary": summary
        }

        change = service.create_change(
            world_id=world_id,
            change_type=change_type,
            new_value=proposed_entry,
            proposed_entry=proposed_entry,
            reason=reason,
            source_text=source_text[:500] if source_text else None,
            confidence=0.7  # Agent suggestions have moderate confidence
        )

        return {
            "status": "queued",
            "change_id": change.id,
            "message": f"Wiki update suggestion for '{title}' has been queued for author approval"
        }
    finally:
        db.close()


@tool
def suggest_character_update(
    world_id: str,
    character_name: str,
    update_field: str,
    update_value: str,
    reason: str,
    source_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Suggest an update to an existing character in the wiki.

    Args:
        world_id: The world ID
        character_name: Name of the character to update
        update_field: Field to update (e.g., 'summary', 'personality', 'backstory')
        update_value: New value for the field
        reason: Why this update is suggested
        source_text: Source text that prompted this suggestion (optional)

    Returns:
        Change request ID and status
    """
    from app.services.wiki_service import WikiService
    from app.models.wiki import WikiEntry, WikiEntryType, WikiChangeType

    db = next(get_db())
    try:
        service = WikiService(db)

        # Find existing character
        entry = db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.CHARACTER.value,
            WikiEntry.title.ilike(f"%{character_name}%")
        ).first()

        if not entry:
            return {
                "status": "not_found",
                "message": f"Character '{character_name}' not found in wiki"
            }

        # Build update
        if update_field == "summary":
            old_value = entry.summary
            new_value = update_value
            field_changed = "summary"
        else:
            # Store in structured_data
            current_data = entry.structured_data or {}
            old_value = current_data.get(update_field)
            new_data = {**current_data, update_field: update_value}
            new_value = new_data
            field_changed = "structured_data"

        change = service.create_change(
            world_id=world_id,
            change_type=WikiChangeType.UPDATE.value,
            wiki_entry_id=entry.id,
            field_changed=field_changed,
            old_value={field_changed: old_value} if old_value else None,
            new_value={field_changed: new_value},
            reason=reason,
            source_text=source_text[:500] if source_text else None,
            confidence=0.65
        )

        return {
            "status": "queued",
            "change_id": change.id,
            "character_id": entry.id,
            "message": f"Update to {character_name}'s {update_field} queued for author approval"
        }
    finally:
        db.close()


@tool
def get_wiki_entry_detail(
    entry_id: str
) -> Dict[str, Any]:
    """
    Get full details of a specific wiki entry.

    Args:
        entry_id: The wiki entry ID

    Returns:
        Complete wiki entry with all fields
    """
    from app.services.wiki_service import WikiService

    db = next(get_db())
    try:
        service = WikiService(db)
        entry = service.get_entry(entry_id)

        if not entry:
            return {"found": False, "error": "Entry not found"}

        return {
            "found": True,
            "entry": {
                "id": entry.id,
                "world_id": entry.world_id,
                "entry_type": entry.entry_type,
                "title": entry.title,
                "slug": entry.slug,
                "content": entry.content,
                "summary": entry.summary,
                "structured_data": entry.structured_data or {},
                "aliases": entry.aliases or [],
                "tags": entry.tags or [],
                "status": entry.status,
                "confidence_score": entry.confidence_score,
                "created_by": entry.created_by
            }
        }
    finally:
        db.close()


# ==================== Consistency Check Tools ====================

@tool
def check_character_consistency(
    character_name: str,
    text_to_check: str,
    world_id: str
) -> Dict[str, Any]:
    """
    Check if text is consistent with known character facts.

    Args:
        character_name: Name of the character to check against
        text_to_check: Text that mentions this character
        world_id: The world ID

    Returns:
        Consistency check results with any detected issues
    """
    from app.services.wiki_service import WikiConsistencyEngine

    db = next(get_db())
    try:
        engine = WikiConsistencyEngine(db)
        facts = engine.get_character_facts(character_name, world_id)

        if not facts.get("found"):
            return {
                "character_found": False,
                "message": f"No wiki entry for {character_name} - cannot verify consistency"
            }

        # Basic consistency checks
        issues = []

        # Check for physical description contradictions
        structured_data = facts.get("structured_data", {})
        physical = structured_data.get("physical", [])
        for trait in physical:
            trait_lower = trait.lower()
            # Look for contradicting terms
            if "blue eyes" in trait_lower and "brown eyes" in text_to_check.lower():
                issues.append(f"Eye color contradiction: wiki says '{trait}' but text mentions brown eyes")
            if "blonde" in trait_lower and "dark hair" in text_to_check.lower():
                issues.append(f"Hair color contradiction: wiki says '{trait}' but text mentions dark hair")

        # Check for role/title contradictions
        roles = structured_data.get("role", [])
        for role in roles:
            role_lower = role.lower()
            text_lower = text_to_check.lower()
            # Check for contradicting titles
            if "king" in role_lower and "peasant" in text_lower:
                issues.append(f"Social status contradiction: wiki says '{role}'")

        return {
            "character_found": True,
            "character_name": facts.get("character_name"),
            "known_facts": {
                "summary": facts.get("summary"),
                "aliases": facts.get("aliases", []),
                "relationships": len(facts.get("relationships", [])),
                "arcs": len(facts.get("arcs", []))
            },
            "issues_found": len(issues),
            "issues": issues,
            "is_consistent": len(issues) == 0
        }
    finally:
        db.close()


# ==================== Analysis Tools ====================

@tool
def get_character_arc_status(
    character_name: str,
    world_id: str,
    manuscript_id: str
) -> Dict[str, Any]:
    """
    Get the status of a character's arc.

    Args:
        character_name: Name of the character
        world_id: The world ID
        manuscript_id: The manuscript ID

    Returns:
        Character arc information including template, stages, and completion
    """
    from app.services.wiki_service import WikiConsistencyEngine
    from app.models.character_arc import CharacterArc
    from app.models.wiki import WikiEntry, WikiEntryType

    db = next(get_db())
    try:
        # Find character wiki entry
        entry = db.query(WikiEntry).filter(
            WikiEntry.world_id == world_id,
            WikiEntry.entry_type == WikiEntryType.CHARACTER.value,
            WikiEntry.title.ilike(f"%{character_name}%")
        ).first()

        if not entry:
            return {
                "found": False,
                "message": f"No wiki entry for {character_name}"
            }

        # Find character arc
        arc = db.query(CharacterArc).filter(
            CharacterArc.wiki_entry_id == entry.id,
            CharacterArc.manuscript_id == manuscript_id
        ).first()

        if not arc:
            return {
                "found": True,
                "has_arc": False,
                "character_name": entry.title,
                "message": "No arc defined for this character in this manuscript"
            }

        return {
            "found": True,
            "has_arc": True,
            "character_name": entry.title,
            "arc": {
                "id": arc.id,
                "template": arc.arc_template,
                "planned_arc": arc.planned_arc,
                "detected_arc": arc.detected_arc,
                "completion": arc.arc_completion,
                "health": arc.arc_health,
                "beats_mapped": len(arc.arc_beats or [])
            }
        }
    finally:
        db.close()


# ==================== Tool Collections ====================

def get_wiki_tools():
    """Get all wiki tools for agent use"""
    return [
        query_wiki,
        get_character_facts,
        get_location_facts,
        get_world_rules,
        check_rule_violations,
        get_relationship_state,
        get_all_characters,
        get_all_locations,
        suggest_wiki_update,
        suggest_character_update,
        get_wiki_entry_detail,
        check_character_consistency,
        get_character_arc_status
    ]


def get_wiki_query_tools():
    """Get read-only wiki query tools"""
    return [
        query_wiki,
        get_character_facts,
        get_location_facts,
        get_world_rules,
        get_relationship_state,
        get_all_characters,
        get_all_locations,
        get_wiki_entry_detail,
        get_character_arc_status
    ]


def get_wiki_consistency_tools():
    """Get tools for consistency checking"""
    return [
        get_character_facts,
        get_world_rules,
        check_rule_violations,
        check_character_consistency,
        get_relationship_state
    ]


def get_wiki_update_tools():
    """Get tools that can suggest wiki updates"""
    return [
        suggest_wiki_update,
        suggest_character_update
    ]
