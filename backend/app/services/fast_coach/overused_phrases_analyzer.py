"""
Overused Phrases Analyzer for Fast Coach.

Detects clichés, overused physical reactions, tired transitions,
and other phrases that have lost their impact through overuse.
"""

import re
from typing import List, Dict, Tuple, Optional
from .types import Suggestion, SuggestionType, SeverityLevel


class OverusedPhrasesAnalyzer:
    """
    Detects overused phrases beyond basic clichés.

    Categorizes phrases by type:
    - Physical reactions (most common in amateur fiction)
    - Emotional descriptions
    - Transitions and time markers
    - Descriptive clichés
    - Action clichés
    """

    # Comprehensive phrase database with alternatives
    # Format: "phrase": ("alternative suggestion", "category")
    OVERUSED_PHRASES: Dict[str, Tuple[str, str]] = {
        # Physical reactions - breath
        "let out a breath": ("Show the emotion causing the breath (relief, tension release)", "physical_reaction"),
        "let out the breath": ("Show the emotion causing the breath (relief, tension release)", "physical_reaction"),
        "released a breath": ("What emotion drives this? Show it through action or thought", "physical_reaction"),
        "released the breath": ("What emotion drives this? Show it through action or thought", "physical_reaction"),
        "took a deep breath": ("Why? Nervous, steeling themselves? Show the emotion directly", "physical_reaction"),
        "drew a deep breath": ("Why? Nervous, steeling themselves? Show the emotion directly", "physical_reaction"),
        "held her breath": ("Describe the anticipation or fear creating this tension", "physical_reaction"),
        "held his breath": ("Describe the anticipation or fear creating this tension", "physical_reaction"),
        "caught her breath": ("Show what caused the surprise or exertion", "physical_reaction"),
        "caught his breath": ("Show what caused the surprise or exertion", "physical_reaction"),
        "breath caught": ("Show what caused the surprise", "physical_reaction"),
        "breath hitched": ("Describe the emotion causing this physical response", "physical_reaction"),

        # Physical reactions - eyes
        "rolled her eyes": ("More specific: skyward glance, exasperated look, or show through dialogue", "physical_reaction"),
        "rolled his eyes": ("More specific: skyward glance, exasperated look, or show through dialogue", "physical_reaction"),
        "her eyes widened": ("Why? Show the surprise through her reaction or thoughts", "physical_reaction"),
        "his eyes widened": ("Why? Show the surprise through his reaction or thoughts", "physical_reaction"),
        "eyes went wide": ("Show what caused the surprise, not just the physical response", "physical_reaction"),
        "narrowed her eyes": ("Show the suspicion or anger through action or dialogue", "physical_reaction"),
        "narrowed his eyes": ("Show the suspicion or anger through action or dialogue", "physical_reaction"),
        "blinked in surprise": ("Show the surprise itself, not the blink", "physical_reaction"),

        # Physical reactions - jaw/teeth
        "clenched his jaw": ("What emotion? Show anger, determination, or frustration directly", "physical_reaction"),
        "clenched her jaw": ("What emotion? Show anger, determination, or frustration directly", "physical_reaction"),
        "jaw clenched": ("Show the underlying emotion through action or internal thought", "physical_reaction"),
        "gritted his teeth": ("Show the frustration or determination in another way", "physical_reaction"),
        "gritted her teeth": ("Show the frustration or determination in another way", "physical_reaction"),
        "ground his teeth": ("What's the emotion? Show it through action or thought", "physical_reaction"),
        "ground her teeth": ("What's the emotion? Show it through action or thought", "physical_reaction"),

        # Physical reactions - lips
        "bit her lip": ("Often signals nervousness—find a unique tell for this character", "physical_reaction"),
        "bit his lip": ("Often signals nervousness—find a unique tell for this character", "physical_reaction"),
        "pursed her lips": ("Show disapproval through action or dialogue instead", "physical_reaction"),
        "pursed his lips": ("Show disapproval through action or dialogue instead", "physical_reaction"),
        "lips thinned": ("Show the displeasure or anger more directly", "physical_reaction"),
        "licked her lips": ("Often nervousness—show through unique character-specific action", "physical_reaction"),
        "licked his lips": ("Often nervousness—show through unique character-specific action", "physical_reaction"),

        # Physical reactions - heart
        "heart pounded": ("Very common—try a more specific physical sensation", "physical_reaction"),
        "heart raced": ("Very common—describe the specific feeling instead", "physical_reaction"),
        "heart hammered": ("Try showing fear/excitement through action or thought", "physical_reaction"),
        "heart skipped a beat": ("Cliché for surprise—show the surprise itself", "physical_reaction"),
        "heart stopped": ("Hyperbole that's lost impact—show the shock differently", "physical_reaction"),
        "heart sank": ("Common—show disappointment through action or thought", "physical_reaction"),
        "heart leaped": ("Cliché for joy—show the happiness more specifically", "physical_reaction"),

        # Physical reactions - stomach
        "stomach dropped": ("Common—describe the specific sensation of dread", "physical_reaction"),
        "stomach churned": ("Show the anxiety or nausea more specifically", "physical_reaction"),
        "stomach knotted": ("Show the nervousness through action or thought", "physical_reaction"),
        "knot in her stomach": ("Describe the specific anxiety causing this", "physical_reaction"),
        "knot in his stomach": ("Describe the specific anxiety causing this", "physical_reaction"),
        "butterflies in her stomach": ("Cliché—find a fresh way to show nervousness", "physical_reaction"),
        "butterflies in his stomach": ("Cliché—find a fresh way to show nervousness", "physical_reaction"),

        # Physical reactions - temperature/chills
        "blood ran cold": ("Cliché for fear—show the fear more directly", "physical_reaction"),
        "blood froze": ("Cliché—show the terror through action or thought", "physical_reaction"),
        "shiver ran down": ("Very common—try a more specific physical reaction", "physical_reaction"),
        "chill ran down": ("Common—describe what causes this feeling", "physical_reaction"),
        "sent chills down": ("Overused—show the fear or unease differently", "physical_reaction"),
        "goosebumps": ("What specifically causes them? Show the stimulus", "physical_reaction"),
        "goose bumps": ("What specifically causes them? Show the stimulus", "physical_reaction"),

        # Physical reactions - other
        "let out a sigh": ("Show what emotion drives the sigh (relief, frustration, sadness)", "physical_reaction"),
        "heaved a sigh": ("What emotion? Relief, exhaustion? Show it directly", "physical_reaction"),
        "flinched": ("Why? Show what caused the reaction", "physical_reaction"),
        "winced": ("Show what caused the reaction and why", "physical_reaction"),
        "swallowed hard": ("Common for nervousness—find unique character-specific action", "physical_reaction"),
        "throat tightened": ("Show the emotion causing this physical response", "physical_reaction"),

        # Transitions
        "all of a sudden": ("Use 'suddenly' or show the suddenness through action", "transition"),
        "before she knew it": ("Often a POV break—stay in the moment", "transition"),
        "before he knew it": ("Often a POV break—stay in the moment", "transition"),
        "before long": ("Be more specific about the time that passed", "transition"),
        "in the blink of an eye": ("Cliché—show the speed through quick action", "transition"),
        "without warning": ("Show the surprise through character reaction", "transition"),
        "out of nowhere": ("Show where it came from or make the surprise vivid", "transition"),
        "the next thing she knew": ("Often a POV break—stay in the moment", "transition"),
        "the next thing he knew": ("Often a POV break—stay in the moment", "transition"),
        "suddenly realized": ("'Realized' is often telling—show the realization", "transition"),
        "in that moment": ("Usually unnecessary—just show the moment", "transition"),
        "at that moment": ("Often filler—just describe what happened", "transition"),

        # Descriptions
        "crystal clear": ("Be specific about what's clear and why it matters", "description"),
        "pitch black": ("Describe what the darkness feels like, how it affects the character", "description"),
        "pitch dark": ("Describe the darkness through sensory experience", "description"),
        "inky blackness": ("Cliché—describe how darkness affects the character", "description"),
        "blood red": ("Just 'red' or describe the specific shade meaningfully", "description"),
        "deafening silence": ("Oxymoron cliché—describe the silence's effect on character", "description"),
        "pregnant pause": ("Show the weight of the pause through character reaction", "description"),
        "piercing blue eyes": ("Very overused—find a fresh description or skip eye color", "description"),
        "emerald green eyes": ("Cliché—consider whether eye color needs mention", "description"),
        "sapphire eyes": ("Very overused eye description", "description"),
        "chiseled features": ("Vague and cliché—be more specific or skip", "description"),
        "ruggedly handsome": ("Cliché—describe specific features that create this impression", "description"),
        "stunningly beautiful": ("Telling rather than showing—describe specific features", "description"),
        "impossibly beautiful": ("'Impossibly' is weak—describe what makes them beautiful", "description"),

        # Actions
        "nodded in agreement": ("'Nodded' implies agreement—redundant. Just 'nodded' or show agreement otherwise", "action"),
        "nodded his head": ("'Nodded' means head-nodding—just 'nodded'", "action"),
        "nodded her head": ("'Nodded' means head-nodding—just 'nodded'", "action"),
        "shook his head in disbelief": ("Often 'shook his head' alone is enough", "action"),
        "shook her head in disbelief": ("Often 'shook her head' alone is enough", "action"),
        "shrugged his shoulders": ("'Shrugged' implies shoulders—just 'shrugged'", "action"),
        "shrugged her shoulders": ("'Shrugged' implies shoulders—just 'shrugged'", "action"),
        "turned on her heel": ("Cliché action—describe the departure uniquely", "action"),
        "turned on his heel": ("Cliché action—describe the departure uniquely", "action"),
        "spun around": ("Common—try a more specific action", "action"),
        "whipped around": ("Common—describe what prompts the quick turn", "action"),
        "leaned in close": ("What's the intent? Show it through context", "action"),
        "closed the distance": ("Common phrase—describe the movement specifically", "action"),

        # Emotions - telling
        "couldn't help but": ("Often unnecessary—just show the action", "emotion"),
        "couldn't believe": ("Show the disbelief through reaction, not statement", "emotion"),
        "didn't know what to say": ("Show the speechlessness through action/silence", "emotion"),
        "at a loss for words": ("Cliché—show the character's struggle to speak", "emotion"),
        "tears streamed down": ("Very common—find a fresh way to show crying", "emotion"),
        "tears welled up": ("Common—show the emotion causing the tears", "emotion"),
        "tears pricked": ("Show the emotion causing this physical response", "emotion"),
        "couldn't contain": ("Just show them not containing it", "emotion"),
        "felt a wave of": ("'Felt' is telling—show the emotion through action", "emotion"),
        "surge of emotion": ("Vague—name and show the specific emotion", "emotion"),
        "mixture of emotions": ("Too vague—be specific about what they feel", "emotion"),

        # Time/pacing
        "seemed like hours": ("Either be specific about time or show tedium differently", "time"),
        "felt like forever": ("Cliché—show the tedium or anticipation directly", "time"),
        "time stood still": ("Cliché—describe the moment's impact differently", "time"),
        "time seemed to slow": ("Overused in action scenes—show the heightened awareness differently", "time"),
        "everything happened so fast": ("Telling—show the rapid events instead", "time"),
    }

    # Category descriptions for teaching points
    CATEGORY_TEACHING = {
        "physical_reaction": (
            "Physical reactions like these are shortcuts for emotion. "
            "While occasionally useful, relying on them can feel like "
            "paint-by-numbers writing. Show the emotion through unique "
            "character-specific actions, internal thoughts, or dialogue."
        ),
        "transition": (
            "These transitional phrases often indicate skipped time or "
            "summarized action. Consider whether you can show the transition "
            "through scene structure instead of telling the reader."
        ),
        "description": (
            "Clichéd descriptions slide past readers without impact. "
            "Fresh, specific descriptions create vivid imagery that readers "
            "remember. When in doubt, describe how something affects your "
            "character rather than just what it looks like."
        ),
        "action": (
            "Many action clichés are redundant or generic. Strong verbs and "
            "specific details create more vivid prose than common phrases."
        ),
        "emotion": (
            "Emotional telling ('felt', 'couldn't help but') distances readers "
            "from the experience. Show emotions through physical sensation, "
            "action, dialogue, and internal thought."
        ),
        "time": (
            "These time-related phrases tell readers how to feel about pacing "
            "rather than letting the prose create that feeling. Trust your "
            "scene structure to convey the passage of time."
        ),
    }

    def analyze(self, text: str, max_issues: int = 20) -> List[Suggestion]:
        """
        Analyze text for overused phrases.

        Args:
            text: Text to analyze
            max_issues: Maximum number of issues to return (avoids overwhelming)

        Returns:
            List of suggestions about overused phrases
        """
        if not text or len(text.strip()) < 50:
            return []

        suggestions = []
        text_lower = text.lower()
        found_count: Dict[str, int] = {}

        for phrase, (alternative, category) in self.OVERUSED_PHRASES.items():
            # Find all occurrences
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)

            for match in pattern.finditer(text_lower):
                # Track how many times we've found this phrase
                found_count[phrase] = found_count.get(phrase, 0) + 1

                # Only report first 2 occurrences of any phrase
                if found_count[phrase] > 2:
                    continue

                # Get original case from source text
                original = text[match.start():match.end()]

                suggestions.append(Suggestion(
                    type=SuggestionType.OVERUSED_PHRASE,
                    severity=SeverityLevel.INFO,
                    message=f"Overused phrase: '{original}'",
                    suggestion=alternative,
                    start_char=match.start(),
                    end_char=match.end(),
                    highlight_word=original,
                    metadata={
                        "phrase": phrase,
                        "category": category,
                        "occurrence": found_count[phrase],
                        "teaching_point": self.CATEGORY_TEACHING.get(
                            category,
                            "Fresh language makes your prose more memorable than familiar phrases."
                        )
                    }
                ))

                if len(suggestions) >= max_issues:
                    break

            if len(suggestions) >= max_issues:
                break

        # Sort by position for better editor highlighting
        suggestions.sort(key=lambda s: s.start_char or 0)

        return suggestions

    def get_phrase_categories(self) -> Dict[str, int]:
        """Get count of phrases by category."""
        categories: Dict[str, int] = {}
        for phrase, (_, category) in self.OVERUSED_PHRASES.items():
            categories[category] = categories.get(category, 0) + 1
        return categories


# Singleton instance
overused_phrases_analyzer = OverusedPhrasesAnalyzer()
