"""
Story Structure Templates
Defines beat templates for different story structures
Based on: KM Weiland, Save the Cat, Hero's Journey, and traditional 3-Act structure
"""

from typing import List, Dict, Any


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


# KM Weiland's Story Structure (Structuring Your Novel)
# 9 key beats at specific percentages
KM_WEILAND_STRUCTURE = [
    PlotBeatTemplate(
        beat_name="hook",
        beat_label="Hook",
        description="Grab the reader's attention and establish the normal world. Introduce your protagonist and their everyday life.",
        position_percent=0.00,
        order_index=0,
        tips="Start with action, intrigue, or a compelling character moment. Show what's at stake."
    ),
    PlotBeatTemplate(
        beat_name="inciting-event",
        beat_label="Inciting Event",
        description="The event that disrupts the protagonist's normal world and sets the story in motion.",
        position_percent=0.12,
        order_index=1,
        tips="This is the 'call to adventure' that changes everything. It should be impossible to ignore."
    ),
    PlotBeatTemplate(
        beat_name="first-plot-point",
        beat_label="First Plot Point",
        description="The protagonist makes a decision that commits them to the journey. No turning back. Moves from Act 1 to Act 2.",
        position_percent=0.25,
        order_index=2,
        tips="This is a point of no return. The protagonist crosses a threshold into a new world or situation."
    ),
    PlotBeatTemplate(
        beat_name="first-pinch-point",
        beat_label="First Pinch Point",
        description="A reminder of the antagonistic force's power. Shows what the protagonist is up against.",
        position_percent=0.375,
        order_index=3,
        tips="Raise the stakes. Show the antagonist's strength. Make the challenge feel real and dangerous."
    ),
    PlotBeatTemplate(
        beat_name="midpoint",
        beat_label="Midpoint",
        description="A major shift in the story. New information is revealed that changes the protagonist's understanding or approach.",
        position_percent=0.50,
        order_index=4,
        tips="This is the moment of truth or false victory. The protagonist shifts from reaction to action."
    ),
    PlotBeatTemplate(
        beat_name="second-pinch-point",
        beat_label="Second Pinch Point",
        description="Another reminder of the antagonistic force, often worse than the first. Pressure increases.",
        position_percent=0.625,
        order_index=5,
        tips="The darkest moment is approaching. Show how formidable the challenge truly is."
    ),
    PlotBeatTemplate(
        beat_name="third-plot-point",
        beat_label="Third Plot Point",
        description="The low point. Everything seems lost. The protagonist faces their darkest moment. Moves from Act 2 to Act 3.",
        position_percent=0.75,
        order_index=6,
        tips="This is the 'all is lost' moment. The protagonist must face their deepest fear or greatest loss."
    ),
    PlotBeatTemplate(
        beat_name="climax",
        beat_label="Climax",
        description="The final confrontation. The protagonist faces the antagonistic force with everything they've learned.",
        position_percent=0.90,
        order_index=7,
        tips="This is the moment the entire story has been building toward. High stakes, maximum tension."
    ),
    PlotBeatTemplate(
        beat_name="resolution",
        beat_label="Resolution",
        description="The aftermath. Show how the protagonist and their world have changed. Tie up loose ends.",
        position_percent=0.98,
        order_index=8,
        tips="Give readers closure. Show the new normal. Demonstrate growth and transformation."
    ),
]


# Save the Cat (Blake Snyder's 15-beat structure)
SAVE_THE_CAT_STRUCTURE = [
    PlotBeatTemplate(
        beat_name="opening-image",
        beat_label="Opening Image",
        description="A snapshot of the protagonist's life before the adventure begins. Shows the 'before' picture.",
        position_percent=0.00,
        order_index=0,
        tips="Create a vivid image that will contrast with the closing image."
    ),
    PlotBeatTemplate(
        beat_name="theme-stated",
        beat_label="Theme Stated",
        description="Someone (often not the protagonist) states the theme of the story, usually in the form of advice.",
        position_percent=0.05,
        order_index=1,
        tips="This is subtle. The protagonist usually doesn't understand it yet."
    ),
    PlotBeatTemplate(
        beat_name="setup",
        beat_label="Setup",
        description="Introduce the protagonist's world, supporting characters, and the flaws that need fixing.",
        position_percent=0.01,
        order_index=2,
        tips="Show the protagonist's everyday life and what's missing or broken in it."
    ),
    PlotBeatTemplate(
        beat_name="catalyst",
        beat_label="Catalyst",
        description="The inciting incident. Something happens that disrupts the status quo.",
        position_percent=0.10,
        order_index=3,
        tips="This changes everything but the protagonist doesn't accept the challenge yet."
    ),
    PlotBeatTemplate(
        beat_name="debate",
        beat_label="Debate",
        description="The protagonist hesitates, questions whether to take action. Should they go on this journey?",
        position_percent=0.12,
        order_index=4,
        tips="Show internal conflict. Make the stakes clear. Why is this decision hard?"
    ),
    PlotBeatTemplate(
        beat_name="break-into-two",
        beat_label="Break Into Two",
        description="The protagonist makes a choice and enters Act Two. They commit to the journey.",
        position_percent=0.20,
        order_index=5,
        tips="This is a choice, not something forced on them. They step into a new world."
    ),
    PlotBeatTemplate(
        beat_name="b-story",
        beat_label="B Story",
        description="Introduction of a new character or relationship that will help the protagonist learn the theme.",
        position_percent=0.22,
        order_index=6,
        tips="This is often the love interest or mentor. They represent the theme."
    ),
    PlotBeatTemplate(
        beat_name="fun-and-games",
        beat_label="Fun and Games",
        description="The promise of the premise. The fun part of the adventure. Explore the new world.",
        position_percent=0.30,
        order_index=7,
        tips="This is what the trailer would show. Deliver on the premise's promise."
    ),
    PlotBeatTemplate(
        beat_name="midpoint",
        beat_label="Midpoint",
        description="Either a false victory or false defeat. Stakes are raised. Time clock starts ticking.",
        position_percent=0.50,
        order_index=8,
        tips="Everything changes here. The protagonist gets what they want... or loses everything."
    ),
    PlotBeatTemplate(
        beat_name="bad-guys-close-in",
        beat_label="Bad Guys Close In",
        description="The antagonistic forces regroup and press harder. Things get worse. Internal and external pressure builds.",
        position_percent=0.55,
        order_index=9,
        tips="Show the opposition getting stronger. The protagonist's flaws cause problems."
    ),
    PlotBeatTemplate(
        beat_name="all-is-lost",
        beat_label="All Is Lost",
        description="The lowest point. The opposite of the midpoint. Something or someone dies (literally or figuratively).",
        position_percent=0.75,
        order_index=10,
        tips="This is the 'whiff of death' moment. Hope seems gone. Make it devastating."
    ),
    PlotBeatTemplate(
        beat_name="dark-night-of-soul",
        beat_label="Dark Night of the Soul",
        description="The protagonist wallows in defeat. Processes the loss. Reflects on what went wrong.",
        position_percent=0.80,
        order_index=11,
        tips="This is a quiet, introspective moment before the final push."
    ),
    PlotBeatTemplate(
        beat_name="break-into-three",
        beat_label="Break Into Three",
        description="The protagonist has an 'aha!' moment. Discovers the solution by applying the theme. Act Three begins.",
        position_percent=0.85,
        order_index=12,
        tips="The A story and B story converge. The protagonist finally understands the theme."
    ),
    PlotBeatTemplate(
        beat_name="finale",
        beat_label="Finale",
        description="The climax. The protagonist confronts the antagonist using what they've learned. Resolve all storylines.",
        position_percent=0.90,
        order_index=13,
        tips="Synthesize the old world (Act 1) and new world (Act 2). Show growth."
    ),
    PlotBeatTemplate(
        beat_name="final-image",
        beat_label="Final Image",
        description="A snapshot showing the protagonist's new life. Contrasts with the opening image. The 'after' picture.",
        position_percent=0.99,
        order_index=14,
        tips="Mirror the opening image to show transformation. Leave readers satisfied."
    ),
]


# Hero's Journey (Joseph Campbell / Christopher Vogler)
# 12 stages
HEROS_JOURNEY_STRUCTURE = [
    PlotBeatTemplate(
        beat_name="ordinary-world",
        beat_label="Ordinary World",
        description="The hero's normal life before the adventure begins. Establish the status quo.",
        position_percent=0.00,
        order_index=0,
        tips="Show what the hero will leave behind. Make us care about their world."
    ),
    PlotBeatTemplate(
        beat_name="call-to-adventure",
        beat_label="Call to Adventure",
        description="The hero is presented with a challenge or quest. The inciting incident.",
        position_percent=0.10,
        order_index=1,
        tips="This disrupts the ordinary world. Present a problem that can't be ignored."
    ),
    PlotBeatTemplate(
        beat_name="refusal-of-call",
        beat_label="Refusal of the Call",
        description="The hero hesitates or refuses the adventure. Shows their fears and doubts.",
        position_percent=0.15,
        order_index=2,
        tips="Make the stakes clear. Show why the hero is reluctant or afraid."
    ),
    PlotBeatTemplate(
        beat_name="meeting-mentor",
        beat_label="Meeting the Mentor",
        description="The hero encounters a guide who provides advice, training, or magical gifts.",
        position_percent=0.20,
        order_index=3,
        tips="The mentor prepares the hero and gives them what they need to begin."
    ),
    PlotBeatTemplate(
        beat_name="crossing-threshold",
        beat_label="Crossing the Threshold",
        description="The hero commits to the adventure and enters the special world. No turning back.",
        position_percent=0.25,
        order_index=4,
        tips="This is the point of no return. The hero leaves the familiar behind."
    ),
    PlotBeatTemplate(
        beat_name="tests-allies-enemies",
        beat_label="Tests, Allies, and Enemies",
        description="The hero faces tests, makes allies, and confronts enemies. Learning the rules of the special world.",
        position_percent=0.30,
        order_index=5,
        tips="Show the hero adapting to the new world. Introduce key supporting characters."
    ),
    PlotBeatTemplate(
        beat_name="approach-innermost-cave",
        beat_label="Approach to the Inmost Cave",
        description="The hero prepares for the major challenge. Approaches the most dangerous place.",
        position_percent=0.45,
        order_index=6,
        tips="Build tension. The hero prepares for the greatest ordeal."
    ),
    PlotBeatTemplate(
        beat_name="ordeal",
        beat_label="Ordeal",
        description="The hero faces their greatest fear or challenge. A life-or-death crisis. The midpoint.",
        position_percent=0.50,
        order_index=7,
        tips="This is a major turning point. The hero faces death (literally or figuratively)."
    ),
    PlotBeatTemplate(
        beat_name="reward",
        beat_label="Reward (Seizing the Sword)",
        description="The hero survives the ordeal and gains the reward: knowledge, treasure, reconciliation.",
        position_percent=0.60,
        order_index=8,
        tips="Show what the hero has won. This sets up the final confrontation."
    ),
    PlotBeatTemplate(
        beat_name="road-back",
        beat_label="The Road Back",
        description="The hero must return to the ordinary world. New obstacles arise. The chase begins.",
        position_percent=0.70,
        order_index=9,
        tips="The adventure isn't over. Complications arise. Pursuit or urgency increases."
    ),
    PlotBeatTemplate(
        beat_name="resurrection",
        beat_label="Resurrection",
        description="The final test. The hero is purified through a last sacrifice or ordeal. Climax.",
        position_percent=0.90,
        order_index=10,
        tips="This is the climactic final battle. The hero is transformed by the experience."
    ),
    PlotBeatTemplate(
        beat_name="return-with-elixir",
        beat_label="Return with the Elixir",
        description="The hero returns to the ordinary world with knowledge, treasure, or wisdom to share.",
        position_percent=0.98,
        order_index=11,
        tips="Show how the hero and their world have changed. The journey was worthwhile."
    ),
]


# Traditional 3-Act Structure (Simple)
THREE_ACT_STRUCTURE = [
    PlotBeatTemplate(
        beat_name="setup",
        beat_label="Setup",
        description="Introduce characters, setting, and the normal world. Establish what the story is about.",
        position_percent=0.00,
        order_index=0,
        tips="Hook the reader. Make them care about the characters and world."
    ),
    PlotBeatTemplate(
        beat_name="inciting-incident",
        beat_label="Inciting Incident",
        description="The event that disrupts the status quo and kicks off the main plot.",
        position_percent=0.10,
        order_index=1,
        tips="Something happens that changes everything. The story truly begins here."
    ),
    PlotBeatTemplate(
        beat_name="plot-point-one",
        beat_label="Plot Point One",
        description="The protagonist commits to the journey. End of Act One. They cross into a new situation.",
        position_percent=0.25,
        order_index=2,
        tips="This is a major decision or event. No going back to the old normal."
    ),
    PlotBeatTemplate(
        beat_name="rising-action",
        beat_label="Rising Action",
        description="The protagonist faces escalating obstacles and challenges. Learning and adapting.",
        position_percent=0.35,
        order_index=3,
        tips="Build tension progressively. Each obstacle should be harder than the last."
    ),
    PlotBeatTemplate(
        beat_name="midpoint",
        beat_label="Midpoint",
        description="A major revelation or reversal. The story takes a new direction. Stakes increase.",
        position_percent=0.50,
        order_index=4,
        tips="This changes the game. New information or a major event shifts the trajectory."
    ),
    PlotBeatTemplate(
        beat_name="complications",
        beat_label="Complications",
        description="Things get harder. The antagonist fights back. Pressure builds on the protagonist.",
        position_percent=0.60,
        order_index=5,
        tips="Turn the screws. Make success seem increasingly impossible."
    ),
    PlotBeatTemplate(
        beat_name="plot-point-two",
        beat_label="Plot Point Two",
        description="The low point. All seems lost. End of Act Two. The darkest moment before the dawn.",
        position_percent=0.75,
        order_index=6,
        tips="This is rock bottom. The protagonist must dig deep to find the will to continue."
    ),
    PlotBeatTemplate(
        beat_name="climax",
        beat_label="Climax",
        description="The final confrontation. The protagonist faces the antagonist with everything they've learned.",
        position_percent=0.90,
        order_index=7,
        tips="This is the payoff. Maximum tension. Everything the story has built toward."
    ),
    PlotBeatTemplate(
        beat_name="resolution",
        beat_label="Resolution",
        description="The aftermath. Show the new normal. Tie up loose ends. Demonstrate growth.",
        position_percent=0.98,
        order_index=8,
        tips="Give readers closure. Show how the journey changed the protagonist and their world."
    ),
]


# Structure registry
STORY_STRUCTURES = {
    "km-weiland": {
        "name": "KM Weiland's Structure",
        "description": "9-beat structure based on KM Weiland's 'Structuring Your Novel'. Focuses on key turning points at specific percentages.",
        "beats": KM_WEILAND_STRUCTURE,
        "recommended_for": ["all genres", "literary fiction", "character-driven"],
        "word_count_range": (50000, 120000),
    },
    "save-the-cat": {
        "name": "Save the Cat",
        "description": "Blake Snyder's 15-beat structure. Originally for screenwriting but works brilliantly for novels.",
        "beats": SAVE_THE_CAT_STRUCTURE,
        "recommended_for": ["thriller", "action", "romance", "commercial fiction"],
        "word_count_range": (60000, 100000),
    },
    "heros-journey": {
        "name": "The Hero's Journey",
        "description": "Joseph Campbell's monomyth structure. 12 stages of the archetypal hero's adventure.",
        "beats": HEROS_JOURNEY_STRUCTURE,
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


def get_structure_template(structure_type: str) -> Dict[str, Any]:
    """Get a story structure template by type"""
    if structure_type not in STORY_STRUCTURES:
        raise ValueError(f"Unknown structure type: {structure_type}. Available: {list(STORY_STRUCTURES.keys())}")

    return STORY_STRUCTURES[structure_type]


def get_available_structures() -> List[Dict[str, Any]]:
    """Get list of all available structure templates"""
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
        structure_type: The structure template to use
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
