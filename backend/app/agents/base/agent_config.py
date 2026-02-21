"""
Agent Configuration Management

Handles configuration for Maxwell's LangChain agents including
model selection, temperature settings, and capability detection.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


class AgentType(str, Enum):
    """Types of specialized agents available"""
    CONTINUITY = "continuity"      # Character facts, timeline consistency
    STYLE = "style"                # Prose quality, show vs tell
    STRUCTURE = "structure"        # Beat alignment, story progression
    VOICE = "voice"                # Dialogue authenticity
    CONSISTENCY = "consistency"    # Full consistency checking
    RESEARCH = "research"          # Worldbuilding and research
    COACH = "coach"                # Smart conversational coach
    STORY_STRUCTURE_GUIDE = "story_structure_guide"  # Outline guidance and beat mapping


class ModelProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    LOCAL = "local"


class ModelCapability(str, Enum):
    """Model capability tiers"""
    MINIMAL = "minimal"      # Basic responses, limited reasoning
    STANDARD = "standard"    # Good reasoning, moderate context
    ADVANCED = "advanced"    # Full reasoning, large context


@dataclass
class ModelConfig:
    """Configuration for a specific LLM model"""
    provider: ModelProvider
    model_name: str
    max_tokens: int = 4096
    temperature: float = 0.7
    capability: ModelCapability = ModelCapability.STANDARD

    # Local model specific
    model_path: Optional[str] = None
    n_ctx: int = 4096
    n_gpu_layers: int = -1  # -1 = auto-detect, 0 = CPU only

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "provider": self.provider.value,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "capability": self.capability.value,
            "model_path": self.model_path,
            "n_ctx": self.n_ctx,
            "n_gpu_layers": self.n_gpu_layers,
        }


# Default model configurations
DEFAULT_MODELS = {
    ModelProvider.OPENAI: ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4o-mini",
        max_tokens=4096,
        temperature=0.7,
        capability=ModelCapability.STANDARD,
    ),
    ModelProvider.ANTHROPIC: ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-3-haiku-20240307",
        max_tokens=4096,
        temperature=0.7,
        capability=ModelCapability.STANDARD,
    ),
    ModelProvider.OPENROUTER: ModelConfig(
        provider=ModelProvider.OPENROUTER,
        model_name="anthropic/claude-3-haiku",
        max_tokens=4096,
        temperature=0.7,
        capability=ModelCapability.STANDARD,
    ),
}


@dataclass
class AgentConfig:
    """
    Configuration for a Maxwell agent

    Handles model selection, context weights, and agent-specific settings.
    """
    agent_type: AgentType
    model_config: ModelConfig

    # Context weights (0.0 to 1.0) - how much to weight each context level
    author_context_weight: float = 0.5
    world_context_weight: float = 0.5
    series_context_weight: float = 0.5
    manuscript_context_weight: float = 1.0

    # Agent-specific settings
    max_context_tokens: int = 8000
    include_teaching: bool = True  # Include teaching explanations
    response_format: str = "json"  # "json" or "text"

    # Cost tracking
    track_costs: bool = True

    # Custom prompt additions
    custom_system_prompt: Optional[str] = None

    # Tool configuration
    enabled_tools: List[str] = field(default_factory=list)
    max_tool_iterations: int = 3  # Max tool-call rounds per LLM invocation

    @classmethod
    def for_agent_type(
        cls,
        agent_type: AgentType,
        model_config: Optional[ModelConfig] = None,
        **kwargs
    ) -> "AgentConfig":
        """
        Create config with appropriate defaults for each agent type

        Different agents weight context differently:
        - Style: Heavily weights Author context (personal style)
        - Continuity: Weights World + Series context (cross-book facts)
        - Voice: Author style + World character profiles
        - Structure: Manuscript outline + Series arc
        """
        # Default model if not provided
        if model_config is None:
            model_config = DEFAULT_MODELS[ModelProvider.ANTHROPIC]

        # Agent-specific defaults
        if agent_type == AgentType.STYLE:
            return cls(
                agent_type=agent_type,
                model_config=model_config,
                author_context_weight=1.0,
                world_context_weight=0.2,
                series_context_weight=0.2,
                manuscript_context_weight=0.8,
                enabled_tools=["query_author_profile", "query_manuscript_stats"],
                **kwargs
            )
        elif agent_type == AgentType.CONTINUITY:
            return cls(
                agent_type=agent_type,
                model_config=model_config,
                author_context_weight=0.2,
                world_context_weight=1.0,
                series_context_weight=1.0,
                manuscript_context_weight=0.8,
                enabled_tools=[
                    "query_entities", "query_timeline", "query_world_rules",
                    "query_series_context"
                ],
                **kwargs
            )
        elif agent_type == AgentType.VOICE:
            return cls(
                agent_type=agent_type,
                model_config=model_config,
                author_context_weight=0.7,
                world_context_weight=0.5,
                series_context_weight=0.6,
                manuscript_context_weight=0.8,
                enabled_tools=[
                    "query_character_profile", "query_dialogue_patterns",
                    "query_author_style"
                ],
                **kwargs
            )
        elif agent_type == AgentType.STRUCTURE:
            return cls(
                agent_type=agent_type,
                model_config=model_config,
                author_context_weight=0.3,
                world_context_weight=0.3,
                series_context_weight=0.8,
                manuscript_context_weight=1.0,
                enabled_tools=[
                    "query_outline", "query_plot_beats", "query_series_arc"
                ],
                **kwargs
            )
        elif agent_type == AgentType.CONSISTENCY:
            return cls(
                agent_type=agent_type,
                model_config=model_config,
                author_context_weight=0.3,
                world_context_weight=1.0,
                series_context_weight=1.0,
                manuscript_context_weight=1.0,
                enabled_tools=[
                    "query_entities", "query_timeline", "query_world_rules",
                    "query_relationships", "query_character_states"
                ],
                **kwargs
            )
        elif agent_type == AgentType.RESEARCH:
            return cls(
                agent_type=agent_type,
                model_config=model_config,
                author_context_weight=0.2,
                world_context_weight=1.0,
                series_context_weight=0.3,
                manuscript_context_weight=0.5,
                enabled_tools=[
                    "query_entities", "query_world_settings", "web_search",
                    "create_codex_draft"
                ],
                **kwargs
            )
        elif agent_type == AgentType.COACH:
            return cls(
                agent_type=agent_type,
                model_config=model_config,
                author_context_weight=0.8,
                world_context_weight=0.6,
                series_context_weight=0.6,
                manuscript_context_weight=1.0,
                response_format="text",
                enabled_tools=[
                    "query_entities", "query_timeline", "query_outline",
                    "query_chapters", "query_author_profile", "search_memory"
                ],
                **kwargs
            )
        elif agent_type == AgentType.STORY_STRUCTURE_GUIDE:
            return cls(
                agent_type=agent_type,
                model_config=model_config,
                author_context_weight=0.4,   # Some - to understand author's voice
                world_context_weight=0.6,    # Medium - story needs world context
                series_context_weight=0.8,   # High - series arc matters for structure
                manuscript_context_weight=1.0,  # Highest - current outline is primary
                response_format="text",      # Conversational guidance
                enabled_tools=[
                    "query_outline", "query_plot_beats", "query_chapters",
                    "query_entities", "query_brainstorm", "analyze_outline_completeness",
                    "get_beat_guidance", "suggest_scenes_between_beats"
                ],
                **kwargs
            )
        else:
            return cls(
                agent_type=agent_type,
                model_config=model_config,
                **kwargs
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "agent_type": self.agent_type.value,
            "model_config": self.model_config.to_dict(),
            "author_context_weight": self.author_context_weight,
            "world_context_weight": self.world_context_weight,
            "series_context_weight": self.series_context_weight,
            "manuscript_context_weight": self.manuscript_context_weight,
            "max_context_tokens": self.max_context_tokens,
            "include_teaching": self.include_teaching,
            "response_format": self.response_format,
            "track_costs": self.track_costs,
            "custom_system_prompt": self.custom_system_prompt,
            "enabled_tools": self.enabled_tools,
        }
