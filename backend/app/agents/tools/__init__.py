"""
LangChain Tools for Maxwell Agents

Tools for querying:
- Codex (entities, relationships)
- Timeline (events, locations)
- Outline (beats, structure)
- Manuscript (chapters, content)
- World (settings, rules)
- Series (cross-book context)
- Author (profile, preferences)
"""

from app.agents.tools.codex_tools import (
    QueryEntities,
    QueryCharacterProfile,
    QueryRelationships,
    SearchEntities,
    query_entities,
    query_character_profile,
    query_relationships,
    search_entities,
)

from app.agents.tools.timeline_tools import (
    QueryTimeline,
    QueryCharacterLocations,
    query_timeline,
    query_character_locations,
)

from app.agents.tools.outline_tools import (
    QueryOutline,
    QueryPlotBeats,
    query_outline,
    query_plot_beats,
)

from app.agents.tools.manuscript_tools import (
    QueryChapters,
    QueryChapterContent,
    SearchManuscript,
    query_chapters,
    query_chapter_content,
    search_manuscript,
)

from app.agents.tools.world_tools import (
    QueryWorldSettings,
    QueryWorldRules,
    query_world_settings,
    query_world_rules,
)

from app.agents.tools.series_tools import (
    QuerySeriesContext,
    QueryCrossBookEntities,
    query_series_context,
    query_cross_book_entities,
)

from app.agents.tools.author_tools import (
    QueryAuthorProfile,
    QueryFeedbackHistory,
    query_author_profile,
    query_feedback_history,
)

from app.agents.tools.outline_guide_tools import (
    AnalyzeOutlineCompleteness,
    GetBeatGuidance,
    SuggestScenesBetweenBeats,
    AnalyzeChapterBeatAlignment,
    GetNextOutlineStep,
    analyze_outline_completeness,
    get_beat_guidance,
    suggest_scenes_between_beats,
    analyze_chapter_beat_alignment,
    get_next_outline_step,
)

# All tools list for easy import
ALL_TOOLS = [
    query_entities,
    query_character_profile,
    query_relationships,
    search_entities,
    query_timeline,
    query_character_locations,
    query_outline,
    query_plot_beats,
    query_chapters,
    query_chapter_content,
    search_manuscript,
    query_world_settings,
    query_world_rules,
    query_series_context,
    query_cross_book_entities,
    query_author_profile,
    query_feedback_history,
    # Outline guide tools
    analyze_outline_completeness,
    get_beat_guidance,
    suggest_scenes_between_beats,
    analyze_chapter_beat_alignment,
    get_next_outline_step,
]

__all__ = [
    # Codex tools
    "QueryEntities",
    "QueryCharacterProfile",
    "QueryRelationships",
    "SearchEntities",
    "query_entities",
    "query_character_profile",
    "query_relationships",
    "search_entities",
    # Timeline tools
    "QueryTimeline",
    "QueryCharacterLocations",
    "query_timeline",
    "query_character_locations",
    # Outline tools
    "QueryOutline",
    "QueryPlotBeats",
    "query_outline",
    "query_plot_beats",
    # Manuscript tools
    "QueryChapters",
    "QueryChapterContent",
    "SearchManuscript",
    "query_chapters",
    "query_chapter_content",
    "search_manuscript",
    # World tools
    "QueryWorldSettings",
    "QueryWorldRules",
    "query_world_settings",
    "query_world_rules",
    # Series tools
    "QuerySeriesContext",
    "QueryCrossBookEntities",
    "query_series_context",
    "query_cross_book_entities",
    # Author tools
    "QueryAuthorProfile",
    "QueryFeedbackHistory",
    "query_author_profile",
    "query_feedback_history",
    # Outline guide tools
    "AnalyzeOutlineCompleteness",
    "GetBeatGuidance",
    "SuggestScenesBetweenBeats",
    "AnalyzeChapterBeatAlignment",
    "GetNextOutlineStep",
    "analyze_outline_completeness",
    "get_beat_guidance",
    "suggest_scenes_between_beats",
    "analyze_chapter_beat_alignment",
    "get_next_outline_step",
    # All tools
    "ALL_TOOLS",
]
