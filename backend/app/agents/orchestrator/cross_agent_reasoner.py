"""
Cross-Agent Reasoner

Handles conflicts between agents and provides unified assessments.
When agents disagree, Maxwell mediates and provides bridge suggestions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class ConflictType(Enum):
    """Types of conflicts that can occur between agents."""
    CHARACTER_VS_PLOT = "character_vs_plot"  # Character actions don't fit plot needs
    STYLE_VS_VOICE = "style_vs_voice"  # Style suggestions conflict with character voice
    PACING_VS_STRUCTURE = "pacing_vs_structure"  # Pacing issues vs structural requirements
    CONSISTENCY_VS_CREATIVITY = "consistency_vs_creativity"  # Facts vs artistic license
    DIALOGUE_VS_PROSE = "dialogue_vs_prose"  # Dialogue style vs narrative style
    NONE = "none"  # No conflict detected


class ConflictSeverity(Enum):
    """How serious the conflict is."""
    MINOR = "minor"  # Easy to resolve, both can coexist
    MODERATE = "moderate"  # Requires attention but manageable
    SIGNIFICANT = "significant"  # Needs author decision
    CRITICAL = "critical"  # Fundamental story issue


@dataclass
class AgentConflict:
    """A conflict between two agent perspectives."""
    conflict_type: ConflictType
    severity: ConflictSeverity
    agent_a: str
    agent_b: str
    feedback_a: str  # What agent A said
    feedback_b: str  # What agent B said
    conflict_description: str  # What's conflicting
    bridge_suggestion: str  # How to resolve
    author_question: Optional[str] = None  # Question to help author decide


@dataclass
class StoryHealthAssessment:
    """Unified assessment of story health from all agent perspectives."""
    overall_score: float  # 0-100
    overall_status: str  # "healthy", "needs_attention", "concerning"

    # Individual health areas
    character_health: float
    plot_health: float
    prose_health: float
    pacing_health: float
    consistency_health: float

    # Key insights
    top_strengths: List[str] = field(default_factory=list)
    top_concerns: List[str] = field(default_factory=list)

    # Conflicts detected
    conflicts: List[AgentConflict] = field(default_factory=list)

    # Unified recommendation
    primary_focus: str = ""  # What author should focus on
    unified_message: str = ""  # Maxwell's unified assessment


class CrossAgentReasoner:
    """
    Analyzes feedback from multiple agents to:
    1. Detect conflicts and contradictions
    2. Provide mediation and bridge suggestions
    3. Generate unified story health assessments
    """

    # Keywords that indicate specific agent domains
    DOMAIN_KEYWORDS = {
        "character": ["character", "motivation", "arc", "protagonist", "antagonist", "behavior", "personality"],
        "plot": ["plot", "story", "conflict", "tension", "stakes", "climax", "resolution", "structure"],
        "style": ["style", "prose", "writing", "sentence", "word choice", "description", "metaphor"],
        "pacing": ["pacing", "pace", "slow", "fast", "momentum", "drag", "rushed", "flow"],
        "consistency": ["consistency", "continuity", "contradiction", "fact", "timeline", "rules"],
        "voice": ["voice", "dialogue", "speech", "speak", "conversation", "tone"],
    }

    # Known conflict patterns
    CONFLICT_PATTERNS = [
        {
            "type": ConflictType.CHARACTER_VS_PLOT,
            "keywords_a": ["out of character", "wouldn't do", "motivation", "unbelievable"],
            "keywords_b": ["plot requires", "story needs", "dramatic", "conflict"],
            "bridge_template": "This action serves the plot but feels out of character. Consider: {bridge}",
        },
        {
            "type": ConflictType.STYLE_VS_VOICE,
            "keywords_a": ["prose", "style", "simpler", "clearer", "flowery"],
            "keywords_b": ["character voice", "dialect", "speech pattern", "authentic"],
            "bridge_template": "The prose style conflicts with the character's voice. Try: {bridge}",
        },
        {
            "type": ConflictType.PACING_VS_STRUCTURE,
            "keywords_a": ["rushing", "slow", "drag", "momentum"],
            "keywords_b": ["beat", "structure", "required", "necessary"],
            "bridge_template": "The pacing feels off but serves structural needs. Balance with: {bridge}",
        },
        {
            "type": ConflictType.CONSISTENCY_VS_CREATIVITY,
            "keywords_a": ["inconsistent", "contradiction", "established", "earlier"],
            "keywords_b": ["creative", "interesting", "fresh", "surprise"],
            "bridge_template": "This contradicts earlier content but adds interest. Resolve by: {bridge}",
        },
    ]

    def analyze_conflicts(
        self,
        agent_results: Dict[str, Any],
    ) -> List[AgentConflict]:
        """
        Analyze agent results for conflicts.

        Args:
            agent_results: Results from multiple agents

        Returns:
            List of detected conflicts
        """
        conflicts = []

        # Extract feedback from each agent
        agent_feedback = {}
        for agent_type, result in agent_results.items():
            if isinstance(result, dict):
                feedback_texts = []

                # Extract feedback from various formats
                for key in ["recommendations", "issues", "feedback", "suggestions"]:
                    if key in result:
                        items = result[key]
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict):
                                    text = item.get("text", "") or item.get("description", "") or str(item)
                                else:
                                    text = str(item)
                                feedback_texts.append(text)
                        elif isinstance(items, str):
                            feedback_texts.append(items)

                agent_feedback[agent_type] = " ".join(feedback_texts)

        # Check each pair of agents for conflicts
        agent_types = list(agent_feedback.keys())
        for i, agent_a in enumerate(agent_types):
            for agent_b in agent_types[i + 1:]:
                feedback_a = agent_feedback[agent_a]
                feedback_b = agent_feedback[agent_b]

                conflict = self._detect_conflict(
                    agent_a, feedback_a,
                    agent_b, feedback_b
                )

                if conflict:
                    conflicts.append(conflict)

        return conflicts

    def _detect_conflict(
        self,
        agent_a: str,
        feedback_a: str,
        agent_b: str,
        feedback_b: str,
    ) -> Optional[AgentConflict]:
        """Detect if two pieces of feedback conflict."""
        feedback_a_lower = feedback_a.lower()
        feedback_b_lower = feedback_b.lower()

        for pattern in self.CONFLICT_PATTERNS:
            # Check if keywords from both patterns are present
            has_keywords_a = any(
                kw in feedback_a_lower or kw in feedback_b_lower
                for kw in pattern["keywords_a"]
            )
            has_keywords_b = any(
                kw in feedback_a_lower or kw in feedback_b_lower
                for kw in pattern["keywords_b"]
            )

            if has_keywords_a and has_keywords_b:
                # Conflict detected
                bridge = self._generate_bridge_suggestion(
                    pattern["type"], feedback_a, feedback_b
                )

                return AgentConflict(
                    conflict_type=pattern["type"],
                    severity=self._assess_severity(feedback_a, feedback_b),
                    agent_a=agent_a,
                    agent_b=agent_b,
                    feedback_a=feedback_a[:200],
                    feedback_b=feedback_b[:200],
                    conflict_description=self._describe_conflict(pattern["type"]),
                    bridge_suggestion=pattern["bridge_template"].format(bridge=bridge),
                    author_question=self._generate_author_question(pattern["type"]),
                )

        return None

    def _generate_bridge_suggestion(
        self,
        conflict_type: ConflictType,
        feedback_a: str,
        feedback_b: str,
    ) -> str:
        """Generate a suggestion to bridge the conflict."""
        bridges = {
            ConflictType.CHARACTER_VS_PLOT: (
                "Add a brief moment showing what pushes the character past their limits, "
                "or a line of internal conflict acknowledging this isn't typical for them."
            ),
            ConflictType.STYLE_VS_VOICE: (
                "Keep the character's voice in dialogue but let the narrative voice "
                "provide contrast and clarity around their speech."
            ),
            ConflictType.PACING_VS_STRUCTURE: (
                "Compress the necessary beats while adding tension or subtext "
                "to maintain reader engagement during slower sections."
            ),
            ConflictType.CONSISTENCY_VS_CREATIVITY: (
                "Add a brief acknowledgment of the change, or plant earlier seeds "
                "that make the deviation feel like character growth."
            ),
            ConflictType.DIALOGUE_VS_PROSE: (
                "Use dialogue tags and action beats to bridge the style gap, "
                "letting narrative prose frame the dialogue naturally."
            ),
        }
        return bridges.get(conflict_type, "Consider both perspectives and find a middle ground.")

    def _assess_severity(self, feedback_a: str, feedback_b: str) -> ConflictSeverity:
        """Assess how severe the conflict is."""
        combined = (feedback_a + " " + feedback_b).lower()

        critical_words = ["fundamental", "breaks", "fails", "completely", "impossible"]
        significant_words = ["serious", "major", "significant", "important"]
        moderate_words = ["consider", "might", "could", "should"]

        if any(word in combined for word in critical_words):
            return ConflictSeverity.CRITICAL
        elif any(word in combined for word in significant_words):
            return ConflictSeverity.SIGNIFICANT
        elif any(word in combined for word in moderate_words):
            return ConflictSeverity.MODERATE
        return ConflictSeverity.MINOR

    def _describe_conflict(self, conflict_type: ConflictType) -> str:
        """Get a human-readable description of the conflict type."""
        descriptions = {
            ConflictType.CHARACTER_VS_PLOT: (
                "Character behavior conflicts with plot requirements"
            ),
            ConflictType.STYLE_VS_VOICE: (
                "Writing style suggestions conflict with character voice"
            ),
            ConflictType.PACING_VS_STRUCTURE: (
                "Pacing preferences conflict with structural needs"
            ),
            ConflictType.CONSISTENCY_VS_CREATIVITY: (
                "Consistency rules conflict with creative choices"
            ),
            ConflictType.DIALOGUE_VS_PROSE: (
                "Dialogue style conflicts with narrative prose"
            ),
        }
        return descriptions.get(conflict_type, "Agents have different perspectives")

    def _generate_author_question(self, conflict_type: ConflictType) -> str:
        """Generate a question to help the author decide."""
        questions = {
            ConflictType.CHARACTER_VS_PLOT: (
                "What matters more here: maintaining character consistency "
                "or advancing the plot? Is there a way to earn this moment?"
            ),
            ConflictType.STYLE_VS_VOICE: (
                "Should the character's voice dominate, or does this scene "
                "need clearer prose for reader comprehension?"
            ),
            ConflictType.PACING_VS_STRUCTURE: (
                "Can you afford to slow down here, or will readers lose interest? "
                "What makes this beat essential?"
            ),
            ConflictType.CONSISTENCY_VS_CREATIVITY: (
                "Is this change worth the continuity break? Can you foreshadow it "
                "earlier to make it feel earned?"
            ),
            ConflictType.DIALOGUE_VS_PROSE: (
                "Should the character speak authentically even if it's harder to read, "
                "or should clarity win here?"
            ),
        }
        return questions.get(conflict_type, "Which perspective feels right for your story?")

    def generate_story_health(
        self,
        agent_results: Dict[str, Any],
        conflicts: Optional[List[AgentConflict]] = None,
    ) -> StoryHealthAssessment:
        """
        Generate a unified story health assessment.

        Args:
            agent_results: Results from all agents
            conflicts: Pre-computed conflicts (if available)

        Returns:
            Unified story health assessment
        """
        if conflicts is None:
            conflicts = self.analyze_conflicts(agent_results)

        # Calculate health scores from agent results
        scores = {
            "character": 70.0,
            "plot": 70.0,
            "prose": 70.0,
            "pacing": 70.0,
            "consistency": 70.0,
        }

        strengths = []
        concerns = []

        # Analyze each agent's results
        for agent_type, result in agent_results.items():
            if not isinstance(result, dict):
                continue

            # Extract issues and praise
            issues = result.get("issues", []) or result.get("recommendations", [])
            praise = result.get("praise", []) or result.get("strengths", [])

            # Map agent to health category
            category = self._map_agent_to_category(agent_type)
            if category in scores:
                # Reduce score based on issues
                issue_penalty = len(issues) * 5 if isinstance(issues, list) else 0
                scores[category] = max(40, scores[category] - issue_penalty)

                # Boost score based on praise
                praise_boost = len(praise) * 3 if isinstance(praise, list) else 0
                scores[category] = min(100, scores[category] + praise_boost)

            # Extract top items
            if isinstance(praise, list):
                for item in praise[:2]:
                    text = item.get("text", str(item)) if isinstance(item, dict) else str(item)
                    strengths.append(text[:100])

            if isinstance(issues, list):
                for item in issues[:2]:
                    text = item.get("text", str(item)) if isinstance(item, dict) else str(item)
                    concerns.append(text[:100])

        # Reduce scores based on conflicts
        for conflict in conflicts:
            if conflict.severity == ConflictSeverity.CRITICAL:
                for key in scores:
                    scores[key] = max(30, scores[key] - 15)
            elif conflict.severity == ConflictSeverity.SIGNIFICANT:
                for key in scores:
                    scores[key] = max(40, scores[key] - 8)

        # Calculate overall score
        overall = sum(scores.values()) / len(scores)

        # Determine status
        if overall >= 80:
            status = "healthy"
        elif overall >= 60:
            status = "needs_attention"
        else:
            status = "concerning"

        # Determine primary focus
        lowest_category = min(scores, key=scores.get)
        primary_focus = f"Focus on improving {lowest_category}"

        # Generate unified message
        unified_message = self._generate_unified_message(
            overall, status, strengths, concerns, conflicts
        )

        return StoryHealthAssessment(
            overall_score=overall,
            overall_status=status,
            character_health=scores["character"],
            plot_health=scores["plot"],
            prose_health=scores["prose"],
            pacing_health=scores["pacing"],
            consistency_health=scores["consistency"],
            top_strengths=strengths[:3],
            top_concerns=concerns[:3],
            conflicts=conflicts,
            primary_focus=primary_focus,
            unified_message=unified_message,
        )

    def _map_agent_to_category(self, agent_type: str) -> str:
        """Map agent type to health category."""
        mapping = {
            "style": "prose",
            "continuity": "consistency",
            "structure": "plot",
            "voice": "character",
            "consistency": "consistency",
            "pacing": "pacing",
        }
        return mapping.get(agent_type.lower(), "prose")

    def _generate_unified_message(
        self,
        overall: float,
        status: str,
        strengths: List[str],
        concerns: List[str],
        conflicts: List[AgentConflict],
    ) -> str:
        """Generate Maxwell's unified assessment message."""
        # Opening based on status
        if status == "healthy":
            opening = "Your writing is in great shape overall."
        elif status == "needs_attention":
            opening = "Your writing shows promise with some areas to polish."
        else:
            opening = "There are a few areas that could use your attention."

        # Highlight strengths
        strength_text = ""
        if strengths:
            strength_text = f" I particularly liked {strengths[0][:50]}..."

        # Note concerns
        concern_text = ""
        if concerns:
            concern_text = f" My main suggestion would be to address {concerns[0][:50]}..."

        # Note conflicts
        conflict_text = ""
        if conflicts:
            critical = [c for c in conflicts if c.severity in [ConflictSeverity.CRITICAL, ConflictSeverity.SIGNIFICANT]]
            if critical:
                conflict_text = (
                    f" I noticed some tensions between different aspects of your writing that "
                    f"might need your attention - {critical[0].conflict_description.lower()}."
                )

        return f"{opening}{strength_text}{concern_text}{conflict_text}"


def create_cross_agent_reasoner() -> CrossAgentReasoner:
    """Factory function to create a CrossAgentReasoner instance."""
    return CrossAgentReasoner()
