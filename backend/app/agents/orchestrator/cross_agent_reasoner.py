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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_type": self.conflict_type.value,
            "severity": self.severity.value,
            "agent_a": self.agent_a,
            "agent_b": self.agent_b,
            "feedback_a": self.feedback_a,
            "feedback_b": self.feedback_b,
            "conflict_description": self.conflict_description,
            "bridge_suggestion": self.bridge_suggestion,
            "author_question": self.author_question,
        }


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "overall_status": self.overall_status,
            "character_health": self.character_health,
            "plot_health": self.plot_health,
            "prose_health": self.prose_health,
            "pacing_health": self.pacing_health,
            "consistency_health": self.consistency_health,
            "top_strengths": self.top_strengths,
            "top_concerns": self.top_concerns,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "primary_focus": self.primary_focus,
            "unified_message": self.unified_message,
        }


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

    # Bridge suggestions for different conflict types
    BRIDGE_SUGGESTIONS = {
        ConflictType.CHARACTER_VS_PLOT: [
            "have the character acknowledge this is unusual for them",
            "add internal conflict showing their struggle with this choice",
            "foreshadow this behavior change earlier in the story",
            "give the character a compelling reason that fits their personality",
        ],
        ConflictType.STYLE_VS_VOICE: [
            "use the ornate style in narration but simpler prose in dialogue",
            "let the character's voice shine through internal monologue",
            "distinguish between the narrator's voice and character speech",
            "create contrast that highlights the character's unique perspective",
        ],
        ConflictType.PACING_VS_STRUCTURE: [
            "compress the necessary beats into more dynamic scenes",
            "add subplot tension during slower structural moments",
            "use scene breaks to skip less essential transitions",
            "layer character development into plot-heavy sections",
        ],
        ConflictType.CONSISTENCY_VS_CREATIVITY: [
            "acknowledge the change in-universe as character growth",
            "add a brief callback to reconcile with earlier content",
            "frame the inconsistency as an intentional reveal",
            "revise earlier sections to set up this change",
        ],
    }

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
                    feedback_a=feedback_a[:200],  # Truncate for readability
                    feedback_b=feedback_b[:200],
                    conflict_description=self._describe_conflict(pattern["type"]),
                    bridge_suggestion=bridge,
                    author_question=self._generate_author_question(pattern["type"]),
                )

        return None

    def _generate_bridge_suggestion(
        self,
        conflict_type: ConflictType,
        feedback_a: str,
        feedback_b: str,
    ) -> str:
        """Generate a bridge suggestion for resolving the conflict."""
        suggestions = self.BRIDGE_SUGGESTIONS.get(conflict_type, [])
        if suggestions:
            # For now, return the first suggestion
            # In future, could use LLM to pick the most relevant
            return suggestions[0]
        return "Consider how both perspectives can inform your revision."

    def _assess_severity(self, feedback_a: str, feedback_b: str) -> ConflictSeverity:
        """Assess how severe a conflict is."""
        combined = (feedback_a + " " + feedback_b).lower()

        if any(word in combined for word in ["critical", "major", "fundamental", "breaks"]):
            return ConflictSeverity.CRITICAL
        elif any(word in combined for word in ["significant", "important", "notable"]):
            return ConflictSeverity.SIGNIFICANT
        elif any(word in combined for word in ["minor", "small", "slight"]):
            return ConflictSeverity.MINOR
        else:
            return ConflictSeverity.MODERATE

    def _describe_conflict(self, conflict_type: ConflictType) -> str:
        """Get a human-readable description of the conflict type."""
        descriptions = {
            ConflictType.CHARACTER_VS_PLOT: "Character behavior conflicts with plot requirements",
            ConflictType.STYLE_VS_VOICE: "Prose style conflicts with character voice",
            ConflictType.PACING_VS_STRUCTURE: "Pacing concerns conflict with structural needs",
            ConflictType.CONSISTENCY_VS_CREATIVITY: "Consistency concerns conflict with creative choices",
            ConflictType.DIALOGUE_VS_PROSE: "Dialogue style conflicts with narrative prose",
        }
        return descriptions.get(conflict_type, "Agents have conflicting perspectives")

    def _generate_author_question(self, conflict_type: ConflictType) -> str:
        """Generate a question to help the author decide."""
        questions = {
            ConflictType.CHARACTER_VS_PLOT: "Which matters more here: staying true to your character or serving the plot?",
            ConflictType.STYLE_VS_VOICE: "Should the prose adapt to the character, or should the character's voice stand out against it?",
            ConflictType.PACING_VS_STRUCTURE: "Is this moment worth slowing down for, or should you find a way to compress it?",
            ConflictType.CONSISTENCY_VS_CREATIVITY: "Is this inconsistency worth keeping for creative reasons, or should you revise for coherence?",
            ConflictType.DIALOGUE_VS_PROSE: "Should dialogue feel integrated with the narrative or deliberately distinct?",
        }
        return questions.get(conflict_type, "How would you like to balance these competing concerns?")

    def assess_story_health(
        self,
        agent_results: Dict[str, Any],
    ) -> StoryHealthAssessment:
        """
        Generate a unified story health assessment from all agent results.

        Args:
            agent_results: Results from multiple agents

        Returns:
            Unified StoryHealthAssessment
        """
        # Calculate health scores per domain
        character_health = self._calculate_domain_health(agent_results, "continuity", "character")
        plot_health = self._calculate_domain_health(agent_results, "structure", "plot")
        prose_health = self._calculate_domain_health(agent_results, "style", "prose")
        pacing_health = self._calculate_domain_health(agent_results, "style", "pacing")
        consistency_health = self._calculate_domain_health(agent_results, "continuity", "consistency")

        # Overall score is weighted average
        overall_score = (
            character_health * 0.25 +
            plot_health * 0.25 +
            prose_health * 0.2 +
            pacing_health * 0.15 +
            consistency_health * 0.15
        )

        # Determine status
        if overall_score >= 80:
            status = "healthy"
        elif overall_score >= 60:
            status = "needs_attention"
        else:
            status = "concerning"

        # Extract strengths and concerns
        strengths = self._extract_strengths(agent_results)
        concerns = self._extract_concerns(agent_results)

        # Detect conflicts
        conflicts = self.analyze_conflicts(agent_results)

        # Determine primary focus
        primary_focus = self._determine_primary_focus(
            character_health, plot_health, prose_health, pacing_health, consistency_health
        )

        # Generate unified message
        unified_message = self._generate_unified_message(
            overall_score, status, primary_focus, len(conflicts)
        )

        return StoryHealthAssessment(
            overall_score=overall_score,
            overall_status=status,
            character_health=character_health,
            plot_health=plot_health,
            prose_health=prose_health,
            pacing_health=pacing_health,
            consistency_health=consistency_health,
            top_strengths=strengths[:3],
            top_concerns=concerns[:3],
            conflicts=conflicts,
            primary_focus=primary_focus,
            unified_message=unified_message,
        )

    def _calculate_domain_health(
        self,
        agent_results: Dict[str, Any],
        agent_type: str,
        domain: str,
    ) -> float:
        """Calculate health score for a specific domain."""
        result = agent_results.get(agent_type, {})
        if not result:
            return 75.0  # Default to moderate health if no data

        issues = result.get("issues", [])
        recommendations = result.get("recommendations", [])

        # Count severity
        high_issues = sum(1 for i in issues if i.get("severity") == "high")
        medium_issues = sum(1 for i in issues if i.get("severity") == "medium")
        low_issues = sum(1 for i in issues if i.get("severity") == "low")

        # Calculate penalty
        penalty = high_issues * 15 + medium_issues * 8 + low_issues * 3

        # Start at 100 and subtract penalties, minimum 20
        return max(20.0, 100.0 - penalty)

    def _extract_strengths(self, agent_results: Dict[str, Any]) -> List[str]:
        """Extract top strengths from agent results."""
        strengths = []
        for agent_type, result in agent_results.items():
            if isinstance(result, dict):
                for rec in result.get("recommendations", []):
                    if rec.get("type") == "praise" or rec.get("severity") == "positive":
                        strengths.append(rec.get("text", "")[:100])
                for praise in result.get("praise", []):
                    strengths.append(praise.get("text", "")[:100])
        return strengths

    def _extract_concerns(self, agent_results: Dict[str, Any]) -> List[str]:
        """Extract top concerns from agent results."""
        concerns = []
        for agent_type, result in agent_results.items():
            if isinstance(result, dict):
                for issue in result.get("issues", []):
                    if issue.get("severity") in ["high", "medium"]:
                        concerns.append(issue.get("description", issue.get("text", ""))[:100])
        return concerns

    def _determine_primary_focus(
        self,
        character: float,
        plot: float,
        prose: float,
        pacing: float,
        consistency: float,
    ) -> str:
        """Determine what the author should focus on."""
        scores = {
            "character development": character,
            "plot structure": plot,
            "prose quality": prose,
            "pacing": pacing,
            "consistency": consistency,
        }
        # Return the lowest scoring area
        return min(scores, key=scores.get)

    def _generate_unified_message(
        self,
        score: float,
        status: str,
        focus: str,
        conflict_count: int,
    ) -> str:
        """Generate Maxwell's unified assessment message."""
        if status == "healthy":
            base = "Your story is in good shape overall."
        elif status == "needs_attention":
            base = "Your story shows promise but has some areas that need work."
        else:
            base = "Your story has several areas that would benefit from focused revision."

        focus_msg = f" I'd suggest focusing on {focus} in your next revision."

        if conflict_count > 0:
            conflict_msg = f" I noticed {conflict_count} area{'s' if conflict_count > 1 else ''} where my feedback might seem contradictory - I've included suggestions for how to balance those competing concerns."
        else:
            conflict_msg = ""

        return base + focus_msg + conflict_msg


def create_cross_agent_reasoner() -> CrossAgentReasoner:
    """Factory function to create a CrossAgentReasoner."""
    return CrossAgentReasoner()
