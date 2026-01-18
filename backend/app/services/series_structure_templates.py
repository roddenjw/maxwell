"""
Series Structure Templates
Defines beat templates for multi-book narrative structures (trilogies, sagas, etc.)
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SeriesBeatTemplate:
    """Template for a single series-level plot beat"""
    def __init__(
        self,
        beat_name: str,
        beat_label: str,
        description: str,
        position_percent: float,
        order_index: int,
        target_book_index: int,
        tips: str = ""
    ):
        self.beat_name = beat_name
        self.beat_label = beat_label
        self.description = description
        self.position_percent = position_percent  # 0.0 to 1.0 across entire series
        self.order_index = order_index
        self.target_book_index = target_book_index  # Which book (1, 2, 3...)
        self.tips = tips

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API responses"""
        return {
            "beat_name": self.beat_name,
            "beat_label": self.beat_label,
            "beat_description": self.description,
            "target_position_percent": self.position_percent,
            "order_index": self.order_index,
            "target_book_index": self.target_book_index,
            "tips": self.tips
        }

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dict for database insertion"""
        return {
            "beat_name": self.beat_name,
            "beat_label": self.beat_label,
            "beat_description": self.description,
            "target_position_percent": self.position_percent,
            "order_index": self.order_index,
            "target_book_index": self.target_book_index,
        }


# Trilogy Arc (3-book structure)
# Classic three-act structure expanded across three books
TRILOGY_ARC_STRUCTURE = [
    # Book 1: Setup & Discovery
    SeriesBeatTemplate(
        beat_name="series-hook",
        beat_label="Series Hook",
        description="Introduce the protagonist and their world. Establish the status quo that will be disrupted by the series-spanning conflict.",
        position_percent=0.00,
        order_index=0,
        target_book_index=1,
        tips="Plant seeds for the larger conflict while focusing on the immediate story."
    ),
    SeriesBeatTemplate(
        beat_name="series-catalyst",
        beat_label="Series Catalyst",
        description="The event that launches the protagonist into the series arc. Something changes irrevocably, hinting at a much larger conflict.",
        position_percent=0.08,
        order_index=1,
        target_book_index=1,
        tips="This catalyst should feel complete for Book 1 while suggesting more to come."
    ),
    SeriesBeatTemplate(
        beat_name="book1-climax",
        beat_label="Book 1 Climax",
        description="The protagonist achieves a significant victory or revelation, but realizes the conflict is much larger than expected.",
        position_percent=0.30,
        order_index=2,
        target_book_index=1,
        tips="Resolve the immediate conflict while opening doors to the larger series arc."
    ),

    # Book 2: Escalation & Testing
    SeriesBeatTemplate(
        beat_name="series-midpoint-setup",
        beat_label="Series Midpoint Setup",
        description="The protagonist faces the full scope of the antagonist's power. Previous victories prove insufficient.",
        position_percent=0.35,
        order_index=3,
        target_book_index=2,
        tips="Book 2 often features the protagonist at their lowest point in the series."
    ),
    SeriesBeatTemplate(
        beat_name="dark-night",
        beat_label="The Dark Night",
        description="The protagonist suffers a major setback or loss. Everything they've built seems to crumble.",
        position_percent=0.50,
        order_index=4,
        target_book_index=2,
        tips="This is the 'Empire Strikes Back' moment—things get worse before they get better."
    ),
    SeriesBeatTemplate(
        beat_name="book2-climax",
        beat_label="Book 2 Climax",
        description="A pyrrhic victory or revelation that fundamentally changes the protagonist's understanding. The true stakes become clear.",
        position_percent=0.65,
        order_index=5,
        target_book_index=2,
        tips="End with a cliffhanger or major shift that demands resolution in Book 3."
    ),

    # Book 3: Resolution & Transformation
    SeriesBeatTemplate(
        beat_name="final-act-setup",
        beat_label="Final Act Setup",
        description="The protagonist regroups and prepares for the final confrontation. Allies gather, plans are made.",
        position_percent=0.70,
        order_index=6,
        target_book_index=3,
        tips="This is the calm before the storm—characters reflect on their journey."
    ),
    SeriesBeatTemplate(
        beat_name="series-climax",
        beat_label="Series Climax",
        description="The ultimate confrontation. Everything the protagonist has learned and gained is tested.",
        position_percent=0.90,
        order_index=7,
        target_book_index=3,
        tips="All major plot threads should converge here."
    ),
    SeriesBeatTemplate(
        beat_name="series-resolution",
        beat_label="Series Resolution",
        description="The aftermath. Show how the world and characters have changed. Tie up remaining threads.",
        position_percent=1.00,
        order_index=8,
        target_book_index=3,
        tips="Give readers emotional closure while honoring the journey."
    ),
]


# Duology Arc (2-book structure)
DUOLOGY_ARC_STRUCTURE = [
    # Book 1: Setup & Revelation
    SeriesBeatTemplate(
        beat_name="duology-hook",
        beat_label="Story Hook",
        description="Establish the protagonist and the conflict they'll face across both books.",
        position_percent=0.00,
        order_index=0,
        target_book_index=1,
        tips="With only two books, you need to establish stakes quickly."
    ),
    SeriesBeatTemplate(
        beat_name="book1-midpoint",
        beat_label="Book 1 Midpoint",
        description="A major revelation or turn that reframes everything. The true scope of the conflict emerges.",
        position_percent=0.25,
        order_index=1,
        target_book_index=1,
        tips="This midpoint should work for Book 1 while hinting at Book 2's challenges."
    ),
    SeriesBeatTemplate(
        beat_name="book1-climax",
        beat_label="Book 1 Climax",
        description="Resolve the immediate threat while revealing a larger challenge. End with a compelling hook for Book 2.",
        position_percent=0.45,
        order_index=2,
        target_book_index=1,
        tips="The protagonist should be fundamentally changed by Book 1's events."
    ),

    # Book 2: Confrontation & Resolution
    SeriesBeatTemplate(
        beat_name="book2-escalation",
        beat_label="Book 2 Escalation",
        description="The stakes rise. The antagonist or conflict proves more dangerous than expected.",
        position_percent=0.55,
        order_index=3,
        target_book_index=2,
        tips="Book 2 should feel like a natural continuation, not a rehash."
    ),
    SeriesBeatTemplate(
        beat_name="all-is-lost",
        beat_label="All Is Lost",
        description="The protagonist faces their greatest challenge. Defeat seems inevitable.",
        position_percent=0.75,
        order_index=4,
        target_book_index=2,
        tips="This moment should feel earned by everything that came before."
    ),
    SeriesBeatTemplate(
        beat_name="duology-climax",
        beat_label="Series Climax",
        description="The final confrontation. Everything comes together for the ultimate resolution.",
        position_percent=0.90,
        order_index=5,
        target_book_index=2,
        tips="Honor both books' buildup in this climax."
    ),
    SeriesBeatTemplate(
        beat_name="duology-resolution",
        beat_label="Series Resolution",
        description="Show the new status quo. How have the characters and world changed?",
        position_percent=1.00,
        order_index=6,
        target_book_index=2,
        tips="Provide satisfying closure for the duology."
    ),
]


# Ongoing Series Arc (open-ended with seasonal arcs)
# Each "season" is roughly 3-4 books
ONGOING_SERIES_STRUCTURE = [
    # Season Arc Structure (repeatable)
    SeriesBeatTemplate(
        beat_name="season-hook",
        beat_label="Season Hook",
        description="Introduce a new threat or mystery that will span this set of books. Reestablish characters and relationships.",
        position_percent=0.00,
        order_index=0,
        target_book_index=1,
        tips="New readers should be able to join here while rewarding returning readers."
    ),
    SeriesBeatTemplate(
        beat_name="season-escalation",
        beat_label="Season Escalation",
        description="The season's main conflict intensifies. Subplots develop and interweave.",
        position_percent=0.25,
        order_index=1,
        target_book_index=1,
        tips="Build connections between the seasonal arc and any overarching series threads."
    ),
    SeriesBeatTemplate(
        beat_name="season-midpoint",
        beat_label="Season Midpoint",
        description="A major reveal or shift that recontextualizes the season's conflict. Alliances may shift.",
        position_percent=0.50,
        order_index=2,
        target_book_index=2,
        tips="This is often where the season's theme crystallizes."
    ),
    SeriesBeatTemplate(
        beat_name="season-crisis",
        beat_label="Season Crisis",
        description="Everything comes to a head. The protagonist must make critical decisions with lasting consequences.",
        position_percent=0.75,
        order_index=3,
        target_book_index=3,
        tips="Leave threads for future seasons while resolving this season's main conflict."
    ),
    SeriesBeatTemplate(
        beat_name="season-resolution",
        beat_label="Season Resolution",
        description="Resolve the season's main conflict. Set up hooks for the next season or arc.",
        position_percent=1.00,
        order_index=4,
        target_book_index=3,
        tips="Balance closure with anticipation for what comes next."
    ),
]


# Saga Arc (5+ book epic structure)
SAGA_ARC_STRUCTURE = [
    # Phase 1: Foundation (Books 1-2)
    SeriesBeatTemplate(
        beat_name="saga-beginning",
        beat_label="The Beginning",
        description="Introduce the vast world and the protagonist's humble origins. Plant seeds for the epic conflict.",
        position_percent=0.00,
        order_index=0,
        target_book_index=1,
        tips="In a saga, take time to build the world richly."
    ),
    SeriesBeatTemplate(
        beat_name="first-journey",
        beat_label="The First Journey",
        description="The protagonist leaves their comfort zone. Early adventures establish their character.",
        position_percent=0.10,
        order_index=1,
        target_book_index=1,
        tips="Each early book should be satisfying alone while building the larger tapestry."
    ),
    SeriesBeatTemplate(
        beat_name="awakening",
        beat_label="The Awakening",
        description="The protagonist discovers their larger role in the world's fate. The true scope of the saga emerges.",
        position_percent=0.20,
        order_index=2,
        target_book_index=2,
        tips="This is where the saga truly begins."
    ),

    # Phase 2: Growth (Books 2-3)
    SeriesBeatTemplate(
        beat_name="trials-begin",
        beat_label="Trials Begin",
        description="The protagonist faces escalating challenges that test and develop their abilities.",
        position_percent=0.30,
        order_index=3,
        target_book_index=2,
        tips="Introduce key allies and enemies who will matter throughout the saga."
    ),
    SeriesBeatTemplate(
        beat_name="saga-midpoint",
        beat_label="Saga Midpoint",
        description="A major turning point that forever changes the protagonist and the world. Nothing will be the same.",
        position_percent=0.50,
        order_index=4,
        target_book_index=3,
        tips="This should be a memorable, series-defining moment."
    ),

    # Phase 3: Darkening (Books 3-4)
    SeriesBeatTemplate(
        beat_name="gathering-shadows",
        beat_label="Gathering Shadows",
        description="The antagonistic forces grow stronger. The cost of the conflict becomes clear.",
        position_percent=0.60,
        order_index=5,
        target_book_index=4,
        tips="Losses here should be permanent and meaningful."
    ),
    SeriesBeatTemplate(
        beat_name="the-fall",
        beat_label="The Fall",
        description="The protagonist's darkest hour. Everything they've worked for seems lost.",
        position_percent=0.70,
        order_index=6,
        target_book_index=4,
        tips="This is the emotional low point of the entire saga."
    ),

    # Phase 4: Resolution (Book 5+)
    SeriesBeatTemplate(
        beat_name="the-return",
        beat_label="The Return",
        description="The protagonist rises from defeat, transformed. The final phase begins.",
        position_percent=0.80,
        order_index=7,
        target_book_index=5,
        tips="Show how the protagonist has grown through everything."
    ),
    SeriesBeatTemplate(
        beat_name="final-battle",
        beat_label="The Final Battle",
        description="The ultimate confrontation between the protagonist and the antagonistic forces.",
        position_percent=0.90,
        order_index=8,
        target_book_index=5,
        tips="All major characters should have their moment."
    ),
    SeriesBeatTemplate(
        beat_name="saga-ending",
        beat_label="The Ending",
        description="The conclusion of the saga. Show the new world that has emerged from the conflict.",
        position_percent=1.00,
        order_index=9,
        target_book_index=5,
        tips="Honor the full journey with an ending that resonates."
    ),
]


# Template registry
SERIES_STRUCTURES = {
    "trilogy-arc": {
        "name": "Trilogy Arc",
        "description": "Classic three-book structure with escalating stakes and a satisfying conclusion.",
        "book_count": 3,
        "arc_type": "trilogy",
        "beats": TRILOGY_ARC_STRUCTURE
    },
    "duology-arc": {
        "name": "Duology Arc",
        "description": "Two-book structure for stories that need more than one book but less than three.",
        "book_count": 2,
        "arc_type": "duology",
        "beats": DUOLOGY_ARC_STRUCTURE
    },
    "ongoing-series": {
        "name": "Ongoing Series",
        "description": "Open-ended structure with seasonal arcs. Good for episodic or long-running series.",
        "book_count": None,  # Open-ended
        "arc_type": "ongoing",
        "beats": ONGOING_SERIES_STRUCTURE
    },
    "saga-arc": {
        "name": "Epic Saga",
        "description": "Five+ book epic structure for grand, sweeping narratives.",
        "book_count": 5,
        "arc_type": "saga",
        "beats": SAGA_ARC_STRUCTURE
    }
}


def get_series_structure(structure_type: str) -> Dict[str, Any]:
    """
    Get series structure definition by type.

    Args:
        structure_type: One of 'trilogy-arc', 'duology-arc', 'ongoing-series', 'saga-arc'

    Returns:
        Structure definition with beats

    Raises:
        ValueError: If structure type is unknown
    """
    if structure_type not in SERIES_STRUCTURES:
        raise ValueError(f"Unknown series structure: {structure_type}")

    structure = SERIES_STRUCTURES[structure_type]
    return {
        "name": structure["name"],
        "description": structure["description"],
        "book_count": structure["book_count"],
        "arc_type": structure["arc_type"],
        "beats": [beat.to_dict() for beat in structure["beats"]]
    }


def get_series_structure_for_db(structure_type: str) -> Dict[str, Any]:
    """
    Get series structure definition for database insertion.

    Args:
        structure_type: One of 'trilogy-arc', 'duology-arc', 'ongoing-series', 'saga-arc'

    Returns:
        Structure definition with beats for DB insertion
    """
    if structure_type not in SERIES_STRUCTURES:
        raise ValueError(f"Unknown series structure: {structure_type}")

    structure = SERIES_STRUCTURES[structure_type]
    return {
        "name": structure["name"],
        "description": structure["description"],
        "book_count": structure["book_count"],
        "arc_type": structure["arc_type"],
        "beats": [beat.to_db_dict() for beat in structure["beats"]]
    }


def list_series_structures() -> List[Dict[str, Any]]:
    """
    List all available series structures.

    Returns:
        List of structure summaries (without full beat details)
    """
    return [
        {
            "type": key,
            "name": structure["name"],
            "description": structure["description"],
            "book_count": structure["book_count"],
            "arc_type": structure["arc_type"],
            "beat_count": len(structure["beats"])
        }
        for key, structure in SERIES_STRUCTURES.items()
    ]
