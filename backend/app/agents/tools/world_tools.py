"""
World Tools for Maxwell Agents

Tools for querying world settings, rules, and world-scoped data.
"""

from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool

from app.database import SessionLocal
from app.models.world import World, Series
from app.models.manuscript import Manuscript
from app.models.entity import Entity, ENTITY_SCOPE_WORLD


class QueryWorldSettingsInput(BaseModel):
    """Input for querying world settings"""
    manuscript_id: str = Field(description="The manuscript ID (used to find the world)")


class QueryWorldSettings(BaseTool):
    """Query world settings"""

    name: str = "query_world_settings"
    description: str = """Get the world settings including genre, magic system, technology level, and themes.
    Use this to understand the rules and constraints of the fictional world."""
    args_schema: Type[BaseModel] = QueryWorldSettingsInput

    def _run(self, manuscript_id: str) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Get manuscript -> series -> world
            manuscript = db.query(Manuscript).filter(
                Manuscript.id == manuscript_id
            ).first()

            if not manuscript or not manuscript.series_id:
                return "No world associated with this manuscript"

            series = db.query(Series).filter(
                Series.id == manuscript.series_id
            ).first()

            if not series:
                return "Series not found"

            world = db.query(World).filter(World.id == series.world_id).first()

            if not world:
                return "World not found"

            # Format output
            lines = [
                f"## World: {world.name}",
            ]

            if world.description:
                lines.append(f"\n{world.description}")

            settings = world.settings or {}

            if settings:
                lines.append("\n### Settings")

                # Genre
                if settings.get("genre"):
                    lines.append(f"\n**Genre:** {settings['genre']}")

                # Time period
                if settings.get("time_period"):
                    lines.append(f"**Time Period:** {settings['time_period']}")

                # Technology level
                if settings.get("technology_level"):
                    lines.append(f"**Technology Level:** {settings['technology_level']}")

                # Magic system
                if settings.get("magic_system"):
                    magic = settings["magic_system"]
                    lines.append("\n#### Magic System")
                    if isinstance(magic, dict):
                        for key, value in magic.items():
                            if isinstance(value, list):
                                lines.append(f"- {key}: {', '.join(str(v) for v in value)}")
                            else:
                                lines.append(f"- {key}: {value}")
                    else:
                        lines.append(f"  {magic}")

                # Themes
                if settings.get("themes"):
                    themes = settings["themes"]
                    if isinstance(themes, list):
                        lines.append(f"\n**Themes:** {', '.join(themes)}")
                    else:
                        lines.append(f"\n**Themes:** {themes}")

                # Tone
                if settings.get("tone"):
                    lines.append(f"**Tone:** {settings['tone']}")

                # Custom settings
                for key, value in settings.items():
                    if key not in ["genre", "time_period", "technology_level",
                                   "magic_system", "themes", "tone", "world_rules"]:
                        if isinstance(value, dict):
                            lines.append(f"\n#### {key.title()}")
                            for k, v in value.items():
                                lines.append(f"- {k}: {v}")
                        elif isinstance(value, list):
                            lines.append(f"\n**{key.title()}:** {', '.join(str(v) for v in value)}")
                        else:
                            lines.append(f"**{key.title()}:** {value}")

            # Count world entities
            world_entity_count = db.query(Entity).filter(
                Entity.world_id == world.id,
                Entity.scope == ENTITY_SCOPE_WORLD
            ).count()

            lines.append(f"\n### Statistics")
            lines.append(f"World-scoped entities: {world_entity_count}")

            # Count series in world
            series_count = db.query(Series).filter(
                Series.world_id == world.id
            ).count()
            lines.append(f"Series in world: {series_count}")

            return "\n".join(lines)

        finally:
            db.close()


class QueryWorldRulesInput(BaseModel):
    """Input for querying world rules"""
    manuscript_id: str = Field(description="The manuscript ID")


class QueryWorldRules(BaseTool):
    """Query world rules and constraints"""

    name: str = "query_world_rules"
    description: str = """Get the established rules and constraints of the world.
    This includes magic system rules, laws of physics, social rules, etc.
    Use this to check if new content violates established world logic."""
    args_schema: Type[BaseModel] = QueryWorldRulesInput

    def _run(self, manuscript_id: str) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Get manuscript -> series -> world
            manuscript = db.query(Manuscript).filter(
                Manuscript.id == manuscript_id
            ).first()

            if not manuscript or not manuscript.series_id:
                return "No world associated with this manuscript"

            series = db.query(Series).filter(
                Series.id == manuscript.series_id
            ).first()

            if not series:
                return "Series not found"

            world = db.query(World).filter(World.id == series.world_id).first()

            if not world:
                return "World not found"

            settings = world.settings or {}

            lines = [f"## World Rules: {world.name}"]

            # Explicit world rules
            if settings.get("world_rules"):
                lines.append("\n### Established Rules")
                rules = settings["world_rules"]
                if isinstance(rules, list):
                    for i, rule in enumerate(rules, 1):
                        lines.append(f"{i}. {rule}")
                elif isinstance(rules, dict):
                    for category, rule_list in rules.items():
                        lines.append(f"\n#### {category}")
                        if isinstance(rule_list, list):
                            for rule in rule_list:
                                lines.append(f"- {rule}")
                        else:
                            lines.append(f"- {rule_list}")
                else:
                    lines.append(rules)

            # Magic system rules
            if settings.get("magic_system"):
                magic = settings["magic_system"]
                lines.append("\n### Magic System Rules")

                if isinstance(magic, dict):
                    if magic.get("rules"):
                        for rule in magic["rules"]:
                            lines.append(f"- {rule}")

                    if magic.get("limitations"):
                        lines.append("\n**Limitations:**")
                        for lim in magic["limitations"]:
                            lines.append(f"- {lim}")

                    if magic.get("costs"):
                        lines.append("\n**Costs:**")
                        for cost in magic["costs"]:
                            lines.append(f"- {cost}")
                else:
                    lines.append(magic)

            # Technology constraints
            if settings.get("technology_level"):
                lines.append(f"\n### Technology Constraints")
                lines.append(f"Level: {settings['technology_level']}")

                if settings.get("technology_rules"):
                    for rule in settings["technology_rules"]:
                        lines.append(f"- {rule}")

            # Social rules
            if settings.get("social_rules"):
                lines.append("\n### Social Rules")
                for rule in settings["social_rules"]:
                    lines.append(f"- {rule}")

            # If no explicit rules found
            if len(lines) == 1:
                lines.append("\nNo explicit world rules have been defined.")
                lines.append("Consider adding rules in World Settings to enable consistency checking.")

            return "\n".join(lines)

        finally:
            db.close()


# Create tool instances
query_world_settings = QueryWorldSettings()
query_world_rules = QueryWorldRules()
