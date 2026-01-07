"""
Story Structure Templates
Defines beat templates for various narrative structures
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class PlotBeatTemplate:
    """Template for a single plot beat"""
    def __init__(
        self,
        beat_name: str,
        beat_label: str,
        description: str,
        position_percent: float,
        order_index: int,
        tips: str = ""
    ):
        self.beat_name = beat_name
        self.beat_label = beat_label
        self.description = description
        self.position_percent = position_percent
        self.order_index = order_index
        self.tips = tips

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API responses (includes tips for display)"""
        return {
            "beat_name": self.beat_name,
            "beat_label": self.beat_label,
            "beat_description": self.description,
            "target_position_percent": self.position_percent,
            "order_index": self.order_index,
            "tips": self.tips
        }

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dict for database insertion (excludes tips)"""
        return {
            "beat_name": self.beat_name,
            "beat_label": self.beat_label,
            "beat_description": self.description,
            "target_position_percent": self.position_percent,
            "order_index": self.order_index,
        }


# 9-Beat Story Arc
# A flexible nine-beat structure focusing on key turning points at specific story percentages
STORY_ARC_9_STRUCTURE = [
    PlotBeatTemplate(
        beat_name="hook",
        beat_label="Hook",
        description="Capture your reader's attention immediately. Present your protagonist in their normal environment, showing who they are and hinting at what matters to them.",
        position_percent=0.00,
        order_index=0,
        tips="Open with something compelling—an intriguing situation, a character in motion, or a glimpse of conflict to come."
    ),
    PlotBeatTemplate(
        beat_name="inciting-event",
        beat_label="Inciting Event",
        description="An unexpected occurrence shakes up your protagonist's ordinary life. This catalyst introduces the central conflict or opportunity that will drive the story forward.",
        position_percent=0.12,
        order_index=1,
        tips="Make this event significant enough that ignoring it becomes impossible for your protagonist."
    ),
    PlotBeatTemplate(
        beat_name="first-plot-point",
        beat_label="First Plot Point",
        description="Your protagonist makes a crucial choice that propels them into the main story conflict. This decision marks the transition into a new phase where returning to normalcy is no longer an option.",
        position_percent=0.25,
        order_index=2,
        tips="This should be an active choice by your protagonist, not something forced upon them, showing their commitment to face what lies ahead."
    ),
    PlotBeatTemplate(
        beat_name="first-pressure-point",
        beat_label="First Pressure Point",
        description="The opposing forces reveal their true strength. Your protagonist gets a clear demonstration of what they're up against, raising awareness of the challenge's magnitude.",
        position_percent=0.375,
        order_index=3,
        tips="Increase tension by showing the antagonist's capabilities or the severity of the obstacles ahead."
    ),
    PlotBeatTemplate(
        beat_name="midpoint",
        beat_label="Midpoint",
        description="A pivotal moment transforms the story's direction. New revelations emerge, forcing your protagonist to reassess their situation and change their strategy.",
        position_percent=0.50,
        order_index=4,
        tips="Create a shift from your protagonist reacting to circumstances toward actively pursuing their goal."
    ),
    PlotBeatTemplate(
        beat_name="second-pressure-point",
        beat_label="Second Pressure Point",
        description="Opposition intensifies as antagonistic forces push back harder. The challenges escalate beyond what came before, tightening the vise on your protagonist.",
        position_percent=0.625,
        order_index=5,
        tips="Demonstrate how the conflict has grown more complex and dangerous since the first pressure point."
    ),
    PlotBeatTemplate(
        beat_name="second-turning-point",
        beat_label="Second Turning Point",
        description="The story reaches its bleakest moment. Your protagonist experiences a devastating setback or loss that makes victory seem unreachable.",
        position_percent=0.75,
        order_index=6,
        tips="Strip away your protagonist's advantages or confidence, forcing them to find inner resources they didn't know they possessed."
    ),
    PlotBeatTemplate(
        beat_name="climax",
        beat_label="Climax",
        description="The decisive showdown arrives. Your protagonist confronts the central conflict armed with everything they've learned throughout their journey.",
        position_percent=0.90,
        order_index=7,
        tips="Deliver maximum tension and stakes in this culminating moment that determines the story's outcome."
    ),
    PlotBeatTemplate(
        beat_name="resolution",
        beat_label="Resolution",
        description="The story's aftermath unfolds. Show how your protagonist and their world have been transformed by the journey, wrapping up remaining story threads.",
        position_percent=0.98,
        order_index=8,
        tips="Provide satisfying closure while demonstrating the lasting changes your protagonist has undergone."
    ),
]


# 15-Beat Screenplay Structure
# A comprehensive structure emphasizing thematic development and emotional beats
SCREENPLAY_15_STRUCTURE = [
    PlotBeatTemplate(
        beat_name="story-opening",
        beat_label="Story Opening",
        description="Present a vivid picture of your protagonist's world before change arrives. This initial portrait establishes the baseline against which transformation will be measured.",
        position_percent=0.00,
        order_index=0,
        tips="Create a memorable opening that you can mirror later to showcase how far your protagonist has come."
    ),
    PlotBeatTemplate(
        beat_name="theme-stated",
        beat_label="Theme Stated",
        description="Introduce your story's central theme through dialogue or action, often voiced by a character other than the protagonist who doesn't yet recognize its significance.",
        position_percent=0.05,
        order_index=1,
        tips="Plant this thematic seed subtly—your protagonist typically won't grasp its meaning until much later in their journey."
    ),
    PlotBeatTemplate(
        beat_name="setup",
        beat_label="Setup",
        description="Establish the key elements of your story world. Introduce important characters, relationships, and the protagonist's current situation, including what's incomplete or broken in their life.",
        position_percent=0.01,
        order_index=2,
        tips="Show your protagonist's daily reality and hint at the void or flaw that the coming journey will address."
    ),
    PlotBeatTemplate(
        beat_name="catalyst",
        beat_label="Catalyst",
        description="An event disrupts the established order of your protagonist's life. This occurrence presents a problem or opportunity that cannot be ignored, though acceptance hasn't yet happened.",
        position_percent=0.10,
        order_index=3,
        tips="Distinguish this from commitment—the catalyst proposes change, but your protagonist hasn't agreed to pursue it yet."
    ),
    PlotBeatTemplate(
        beat_name="debate",
        beat_label="Debate",
        description="Your protagonist wrestles with uncertainty. They question whether to engage with the challenge presented by the catalyst, revealing their fears and the stakes involved.",
        position_percent=0.12,
        order_index=4,
        tips="Explore your protagonist's internal resistance to show why this decision carries weight and consequence."
    ),
    PlotBeatTemplate(
        beat_name="commitment-point",
        beat_label="Commitment Point",
        description="Your protagonist actively chooses to pursue the story's central challenge. This voluntary decision launches them into unfamiliar territory and new circumstances.",
        position_percent=0.20,
        order_index=5,
        tips="Emphasize that this is a conscious choice, not an accident or force—your protagonist must take ownership of this step forward."
    ),
    PlotBeatTemplate(
        beat_name="b-story",
        beat_label="B Story",
        description="A secondary character or relationship enters the narrative, often providing perspective that illuminates your story's theme. This subplot typically offers emotional contrast to the main action.",
        position_percent=0.22,
        order_index=6,
        tips="This relationship often serves as a mirror or teacher, helping your protagonist understand lessons they need to learn."
    ),
    PlotBeatTemplate(
        beat_name="fun-and-games",
        beat_label="Fun and Games",
        description="Explore the premise's most entertaining possibilities. Your protagonist navigates their new situation, providing the experiences that likely drew readers to your story concept.",
        position_percent=0.30,
        order_index=7,
        tips="Deliver on your premise's promise—if it's a romance, show them falling in love; if it's an adventure, show thrilling escapades."
    ),
    PlotBeatTemplate(
        beat_name="midpoint",
        beat_label="Midpoint",
        description="A significant win or loss occurs that raises the stakes considerably. Time pressure increases, and what seemed achievable becomes more complex or urgent.",
        position_percent=0.50,
        order_index=8,
        tips="Create a major reversal—apparent success that hides coming disaster, or apparent failure that plants seeds of eventual triumph."
    ),
    PlotBeatTemplate(
        beat_name="rising-opposition",
        beat_label="Rising Opposition",
        description="Antagonistic forces regroup and push back against your protagonist's progress. External pressures combine with internal doubts as complications multiply.",
        position_percent=0.55,
        order_index=9,
        tips="Show both external opposition strengthening and your protagonist's flaws creating additional problems."
    ),
    PlotBeatTemplate(
        beat_name="lowest-point",
        beat_label="Lowest Point",
        description="Everything collapses around your protagonist. A significant loss occurs—whether literal death or the death of hope, relationships, or dreams—creating the story's darkest moment.",
        position_percent=0.75,
        order_index=10,
        tips="Make this defeat feel genuine and devastating, leaving readers wondering how your protagonist can possibly recover."
    ),
    PlotBeatTemplate(
        beat_name="moment-of-despair",
        beat_label="Moment of Despair",
        description="Your protagonist processes the recent catastrophe. In this quiet, reflective interval, they examine what went wrong and face the weight of their losses.",
        position_percent=0.80,
        order_index=11,
        tips="Allow stillness after the storm—this introspective pause makes the coming resurgence more powerful."
    ),
    PlotBeatTemplate(
        beat_name="resolution-decision",
        beat_label="Resolution Decision",
        description="A breakthrough occurs as your protagonist grasps the key to solving their central problem. By integrating the story's thematic lesson, they discover a path forward.",
        position_percent=0.85,
        order_index=12,
        tips="Unite your main story with the B story as your protagonist finally understands what they've been learning all along."
    ),
    PlotBeatTemplate(
        beat_name="finale",
        beat_label="Finale",
        description="Your protagonist faces the final challenge, applying their newfound understanding to resolve the central conflict. All narrative threads converge toward conclusion.",
        position_percent=0.90,
        order_index=13,
        tips="Demonstrate how your protagonist has integrated lessons from their journey, showing growth through their actions."
    ),
    PlotBeatTemplate(
        beat_name="story-closing",
        beat_label="Story Closing",
        description="Present your protagonist's transformed reality. This final image contrasts with your opening to illustrate the complete arc of change they've experienced.",
        position_percent=0.99,
        order_index=14,
        tips="Echo elements from your opening to highlight the transformation, giving readers a satisfying sense of completion."
    ),
]


# Mythic Quest Structure
# A twelve-stage structure based on archetypal quest narratives
MYTHIC_QUEST_STRUCTURE = [
    PlotBeatTemplate(
        beat_name="ordinary-world",
        beat_label="Ordinary World",
        description="Show your protagonist's life before transformation begins. Establish their familiar environment, daily patterns, and the people who populate their normal existence.",
        position_percent=0.00,
        order_index=0,
        tips="Create investment in your protagonist's current world so readers understand what they're leaving behind when change comes."
    ),
    PlotBeatTemplate(
        beat_name="invitation-to-change",
        beat_label="Invitation to Change",
        description="Your protagonist encounters an opportunity or challenge that threatens to disrupt their familiar life. This presents the central quest or problem that will drive the narrative.",
        position_percent=0.10,
        order_index=1,
        tips="Introduce a problem compelling enough that your protagonist cannot simply ignore it and continue their previous existence."
    ),
    PlotBeatTemplate(
        beat_name="hesitation",
        beat_label="Hesitation",
        description="Your protagonist resists the invitation to embark on the journey. This reluctance reveals their doubts, fears, or attachments to their current situation.",
        position_percent=0.15,
        order_index=2,
        tips="Use this resistance to establish what's at stake and why leaving the familiar feels dangerous or costly."
    ),
    PlotBeatTemplate(
        beat_name="meeting-mentor",
        beat_label="Meeting the Mentor",
        description="A guide figure appears who offers wisdom, tools, or encouragement. This character helps prepare your protagonist for the challenges ahead.",
        position_percent=0.20,
        order_index=3,
        tips="The mentor equips your protagonist with what they need to begin—this might be knowledge, objects, or simply confidence."
    ),
    PlotBeatTemplate(
        beat_name="crossing-threshold",
        beat_label="Crossing the Threshold",
        description="Your protagonist commits to the quest and steps beyond the boundaries of their known world. They enter unfamiliar territory where old rules no longer apply.",
        position_percent=0.25,
        order_index=4,
        tips="Mark this as a definitive departure from the ordinary world—your protagonist passes through a one-way door."
    ),
    PlotBeatTemplate(
        beat_name="tests-allies-enemies",
        beat_label="Tests, Allies, and Enemies",
        description="Your protagonist encounters challenges that test their abilities while forming bonds with helpers and identifying adversaries. They learn how this new world operates.",
        position_percent=0.30,
        order_index=5,
        tips="Use these encounters to develop supporting characters who will matter later and show your protagonist adapting to new circumstances."
    ),
    PlotBeatTemplate(
        beat_name="preparation",
        beat_label="Preparation for Crisis",
        description="Your protagonist prepares to face the story's central challenge. They approach the most dangerous phase of their quest with growing awareness of what it will demand.",
        position_percent=0.45,
        order_index=6,
        tips="Build mounting tension as your protagonist steels themselves for the ordeal that awaits."
    ),
    PlotBeatTemplate(
        beat_name="ordeal",
        beat_label="Ordeal",
        description="Your protagonist confronts their greatest fear or challenge in a life-threatening crisis. This central trial tests them to their limits.",
        position_percent=0.50,
        order_index=7,
        tips="Create a genuine brush with failure or death that fundamentally alters your protagonist's journey."
    ),
    PlotBeatTemplate(
        beat_name="victory",
        beat_label="Victory and Gain",
        description="Having survived the ordeal, your protagonist claims their reward. This might be knowledge, an object of power, reconciliation, or deeper understanding.",
        position_percent=0.60,
        order_index=8,
        tips="Show what your protagonist has earned through their survival, establishing assets they'll need for the final confrontation."
    ),
    PlotBeatTemplate(
        beat_name="road-back",
        beat_label="The Road Back",
        description="Your protagonist must journey back toward their original world, but new complications arise. The consequences of their actions create fresh obstacles or pursuit.",
        position_percent=0.70,
        order_index=9,
        tips="Introduce urgency or pursuit—the quest isn't finished, and getting home presents its own challenges."
    ),
    PlotBeatTemplate(
        beat_name="resurrection",
        beat_label="Resurrection",
        description="Your protagonist faces one final, purifying test. This ultimate challenge serves as the climax, requiring them to demonstrate complete transformation.",
        position_percent=0.90,
        order_index=10,
        tips="Make this the most demanding trial yet, where your protagonist must prove they've truly changed through their journey."
    ),
    PlotBeatTemplate(
        beat_name="triumphant-return",
        beat_label="Triumphant Return",
        description="Your protagonist returns to the ordinary world bearing gifts—wisdom, treasures, or abilities that benefit others. They share what they've gained from their transformative journey.",
        position_percent=0.98,
        order_index=11,
        tips="Show both personal transformation and how your protagonist's journey creates value for their community or world."
    ),
]


# Traditional 3-Act Structure (Simple)
THREE_ACT_STRUCTURE = [
    PlotBeatTemplate(
        beat_name="setup",
        beat_label="Setup",
        description="Introduce your cast, environment, and the protagonist's current situation. Establish the foundation readers need to understand your story's stakes and possibilities.",
        position_percent=0.00,
        order_index=0,
        tips="Hook readers immediately while providing essential context about who your characters are and what world they inhabit."
    ),
    PlotBeatTemplate(
        beat_name="inciting-incident",
        beat_label="Inciting Incident",
        description="An event shatters the established status quo and initiates your main plot. This occurrence sets your story's conflict in motion.",
        position_percent=0.10,
        order_index=1,
        tips="Create a disruption significant enough to launch your entire narrative—the real story begins at this moment."
    ),
    PlotBeatTemplate(
        beat_name="plot-point-one",
        beat_label="Plot Point One",
        description="Your protagonist commits to addressing the story's central challenge. This decision or event propels them into new circumstances and marks the first act's conclusion.",
        position_percent=0.25,
        order_index=2,
        tips="Make this a significant threshold—returning to the previous normal becomes impossible from this point forward."
    ),
    PlotBeatTemplate(
        beat_name="rising-action",
        beat_label="Rising Action",
        description="Your protagonist faces increasingly difficult obstacles as they pursue their goal. Each challenge forces them to learn, adapt, and grow stronger.",
        position_percent=0.35,
        order_index=3,
        tips="Escalate difficulty progressively—ensure each new obstacle presents greater challenges than what came before."
    ),
    PlotBeatTemplate(
        beat_name="midpoint",
        beat_label="Midpoint",
        description="A major revelation or reversal shifts your story's trajectory. The stakes intensify and new information changes how your protagonist approaches their quest.",
        position_percent=0.50,
        order_index=4,
        tips="Create a pivot point that transforms the story's direction and raises urgency for everything that follows."
    ),
    PlotBeatTemplate(
        beat_name="complications",
        beat_label="Complications",
        description="Opposition strengthens as antagonistic forces counterattack. Mounting pressure makes your protagonist's success appear increasingly unlikely.",
        position_percent=0.60,
        order_index=5,
        tips="Intensify conflict by showing how opposition adapts and grows more formidable in response to your protagonist's actions."
    ),
    PlotBeatTemplate(
        beat_name="plot-point-two",
        beat_label="Plot Point Two",
        description="Your protagonist hits rock bottom in their darkest hour. This devastating low point concludes the second act and forces them to find reserves they didn't know existed.",
        position_percent=0.75,
        order_index=6,
        tips="Strip away everything that gave your protagonist confidence or advantage, creating genuine doubt about possible success."
    ),
    PlotBeatTemplate(
        beat_name="climax",
        beat_label="Climax",
        description="The ultimate confrontation arrives. Your protagonist applies everything they've learned to face the central conflict in this decisive showdown.",
        position_percent=0.90,
        order_index=7,
        tips="Deliver the culminating moment your entire story has built toward, with maximum stakes and tension."
    ),
    PlotBeatTemplate(
        beat_name="resolution",
        beat_label="Resolution",
        description="Show the consequences of your climax and how your protagonist's world has changed. Resolve remaining plot threads while demonstrating lasting transformation.",
        position_percent=0.98,
        order_index=8,
        tips="Provide closure that satisfies readers while clearly showing how your protagonist and their world have evolved through the journey."
    ),
]


# Structure registry
STORY_STRUCTURES = {
    "story-arc-9": {
        "name": "9-Beat Story Arc",
        "description": "A flexible nine-beat structure focusing on key turning points at specific story percentages. Works well for character-driven narratives and literary fiction.",
        "beats": STORY_ARC_9_STRUCTURE,
        "recommended_for": ["all genres", "literary fiction", "character-driven"],
        "word_count_range": (50000, 120000),
    },
    "screenplay-15": {
        "name": "15-Beat Screenplay Structure",
        "description": "A comprehensive fifteen-beat structure emphasizing thematic development and emotional beats. Originally developed for screenwriting but highly effective for novels.",
        "beats": SCREENPLAY_15_STRUCTURE,
        "recommended_for": ["thriller", "action", "romance", "commercial fiction"],
        "word_count_range": (60000, 100000),
    },
    "mythic-quest": {
        "name": "Mythic Quest Structure",
        "description": "A twelve-stage structure based on archetypal quest narratives. Ideal for adventure stories featuring transformation and discovery.",
        "beats": MYTHIC_QUEST_STRUCTURE,
        "recommended_for": ["fantasy", "sci-fi", "adventure", "epic"],
        "word_count_range": (80000, 150000),
    },
    "3-act": {
        "name": "Three-Act Structure",
        "description": "Traditional dramatic structure. Simple and flexible. Great starting point for new writers.",
        "beats": THREE_ACT_STRUCTURE,
        "recommended_for": ["all genres", "beginners", "short novels"],
        "word_count_range": (40000, 100000),
    },
}

# Legacy structure ID mapping for backward compatibility
LEGACY_STRUCTURE_IDS = {
    "km-weiland": "story-arc-9",
    "save-the-cat": "screenplay-15",
    "heros-journey": "mythic-quest",
}


def get_structure_template(structure_type: str) -> Dict[str, Any]:
    """Get a story structure template by type

    Args:
        structure_type: The structure ID (supports both current and legacy IDs)

    Returns:
        Dictionary containing structure metadata and beat templates

    Raises:
        ValueError: If structure_type is not recognized
    """
    # Map legacy IDs to current IDs for backward compatibility
    actual_type = LEGACY_STRUCTURE_IDS.get(structure_type, structure_type)

    if structure_type in LEGACY_STRUCTURE_IDS:
        logger.warning(
            f"Legacy structure ID '{structure_type}' used. "
            f"Please update to use '{actual_type}' instead. "
            f"Legacy IDs will be supported for backward compatibility."
        )

    if actual_type not in STORY_STRUCTURES:
        available = list(STORY_STRUCTURES.keys()) + list(LEGACY_STRUCTURE_IDS.keys())
        raise ValueError(f"Unknown structure type: {structure_type}. Available: {available}")

    return STORY_STRUCTURES[actual_type]


def get_available_structures() -> List[Dict[str, Any]]:
    """Get list of all available structure templates (current IDs only)

    Returns:
        List of dictionaries containing structure metadata
    """
    return [
        {
            "id": structure_id,
            "name": structure_data["name"],
            "description": structure_data["description"],
            "beat_count": len(structure_data["beats"]),
            "recommended_for": structure_data["recommended_for"],
            "word_count_range": structure_data["word_count_range"],
        }
        for structure_id, structure_data in STORY_STRUCTURES.items()
    ]


def create_plot_beats_from_template(structure_type: str, target_word_count: int = 80000) -> List[Dict[str, Any]]:
    """
    Create plot beats from a template with calculated word counts

    Args:
        structure_type: The structure template to use (supports legacy IDs)
        target_word_count: Target word count for the manuscript

    Returns:
        List of plot beat dictionaries ready for database insertion
    """
    template = get_structure_template(structure_type)
    beats = []

    for beat_template in template["beats"]:
        beat_dict = beat_template.to_db_dict()  # Use to_db_dict() for database insertion
        beat_dict["target_word_count"] = int(target_word_count * beat_template.position_percent)
        beat_dict["actual_word_count"] = 0
        beat_dict["is_completed"] = False
        beat_dict["user_notes"] = ""
        beat_dict["content_summary"] = ""
        beats.append(beat_dict)

    return beats
