"""
Maxwell Synthesizer - Unified Persona for Agent Feedback

Transforms raw multi-agent output into cohesive, conversational feedback
that speaks with Maxwell's unified voice.

The synthesizer takes disparate agent findings and creates a narrative that:
1. Speaks as Maxwell (not "The Style Agent found...")
2. Prioritizes by impact (plot-breaking > continuity > style)
3. Connects related issues across agents
4. Celebrates what's working before critiquing
5. Maintains teaching-first philosophy

Usage:
    synthesizer = MaxwellSynthesizer(api_key="sk-...")
    unified = await synthesizer.synthesize(orchestrator_result, tone="encouraging")
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from app.services.llm_service import llm_service, LLMConfig, LLMProvider
from app.agents.base.agent_config import ModelConfig, ModelProvider


class SynthesisTone(Enum):
    """Tone options for Maxwell's synthesis"""
    ENCOURAGING = "encouraging"  # Default - warm and supportive
    DIRECT = "direct"            # More concise, professional
    TEACHING = "teaching"        # Extra educational context
    CELEBRATORY = "celebratory"  # Focus on what's working


@dataclass
class SynthesizedFeedback:
    """Unified feedback from Maxwell"""
    # The main conversational response
    narrative: str

    # Structured data for UI rendering
    highlights: List[Dict[str, Any]] = field(default_factory=list)  # What's working well
    priorities: List[Dict[str, Any]] = field(default_factory=list)  # Ordered by impact
    teaching_moments: List[str] = field(default_factory=list)        # Craft education

    # Summary for quick display
    summary: str = ""

    # Metrics
    total_issues: int = 0
    total_praise: int = 0
    cost: float = 0.0
    tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "narrative": self.narrative,
            "highlights": self.highlights,
            "priorities": self.priorities,
            "teaching_moments": self.teaching_moments,
            "summary": self.summary,
            "total_issues": self.total_issues,
            "total_praise": self.total_praise,
            "cost": self.cost,
            "tokens": self.tokens
        }


SYNTHESIS_SYSTEM_PROMPT = """You are Maxwell, a warm and knowledgeable writing coach. You've just analyzed a piece of writing using your internal expertise in style, continuity, structure, and voice.

Your task is to synthesize the analysis into ONE cohesive, conversational response.

## Your Voice
- Speak as yourself ("I noticed..." not "The analysis found...")
- Be warm, encouraging, and supportive
- Direct but tactful when pointing out issues
- Teaching-focused: explain the "why" behind observations
- Celebrate what's working - writers need encouragement

## Synthesis Rules
1. **Prioritize by impact**: Plot/continuity issues > structure > style/voice
2. **Connect related findings**: If style issues stem from structure problems, say so
3. **Lead with praise**: Start with what's working well
4. **Group related feedback**: Don't list items mechanically
5. **Limit scope**: Focus on top 3-5 actionable items, don't overwhelm
6. **Be specific**: Reference the actual text when possible

## Tone: {tone}
{tone_guidance}

## Analysis Results to Synthesize

### Style Analysis
{style_findings}

### Continuity Analysis
{continuity_findings}

### Structure Analysis
{structure_findings}

### Voice Analysis
{voice_findings}

### Praise/Highlights
{praise}

## Response Format
Respond with valid JSON:
{{
  "narrative": "Your conversational feedback as Maxwell (2-4 paragraphs)",
  "summary": "One sentence summary of the key takeaway",
  "highlights": [
    {{"aspect": "string", "text": "What Maxwell noticed working well"}}
  ],
  "priorities": [
    {{
      "type": "string",
      "severity": "high|medium|low",
      "text": "The issue or suggestion",
      "why_it_matters": "Teaching explanation",
      "suggestion": "Concrete action"
    }}
  ],
  "teaching_moments": ["Brief craft principle worth knowing"]
}}"""

TONE_GUIDANCE = {
    SynthesisTone.ENCOURAGING: """Be extra warm and supportive. Emphasize growth mindset -
every draft is progress. Frame issues as opportunities. Use phrases like "I see what you're
going for here" and "One thing that could elevate this...".""",

    SynthesisTone.DIRECT: """Be professional and concise. Get to the point quickly while
remaining respectful. Focus on actionable feedback without excessive preamble. Writers
appreciate efficiency.""",

    SynthesisTone.TEACHING: """Take extra time to explain craft principles. Connect feedback
to established writing techniques. Include examples from literature if relevant. This is
a learning opportunity.""",

    SynthesisTone.CELEBRATORY: """Focus heavily on what's working. This might be after a
major revision or when the writer needs encouragement. Still mention key issues but frame
them as "polish" items."""
}


class MaxwellSynthesizer:
    """
    Synthesizes multi-agent feedback into Maxwell's unified voice.

    Takes raw orchestrator output and transforms it into cohesive,
    conversational feedback that feels like talking to one expert editor.
    """

    def __init__(
        self,
        api_key: str,
        model_config: Optional[ModelConfig] = None
    ):
        """
        Initialize the synthesizer.

        Args:
            api_key: API key for LLM provider
            model_config: Optional model config (defaults to Claude Haiku for speed)
        """
        self.api_key = api_key
        self.model_config = model_config or ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-haiku-20240307",
            temperature=0.7,
            max_tokens=2048
        )

    async def synthesize(
        self,
        orchestrator_result: Dict[str, Any],
        tone: SynthesisTone = SynthesisTone.ENCOURAGING,
        author_context: Optional[Dict[str, Any]] = None
    ) -> SynthesizedFeedback:
        """
        Synthesize multi-agent results into unified Maxwell feedback.

        Args:
            orchestrator_result: Raw result from WritingAssistantOrchestrator
            tone: Desired tone for the feedback
            author_context: Optional author learning context for personalization

        Returns:
            SynthesizedFeedback with unified narrative and structured data
        """
        # Extract findings by agent type
        style_findings = self._extract_agent_findings(orchestrator_result, "style")
        continuity_findings = self._extract_agent_findings(orchestrator_result, "continuity")
        structure_findings = self._extract_agent_findings(orchestrator_result, "structure")
        voice_findings = self._extract_agent_findings(orchestrator_result, "voice")
        praise = self._extract_praise(orchestrator_result)

        # Build the synthesis prompt
        prompt = SYNTHESIS_SYSTEM_PROMPT.format(
            tone=tone.value,
            tone_guidance=TONE_GUIDANCE[tone],
            style_findings=style_findings or "No specific style issues noted.",
            continuity_findings=continuity_findings or "No continuity concerns found.",
            structure_findings=structure_findings or "Structure appears solid.",
            voice_findings=voice_findings or "Voice and dialogue are working well.",
            praise=praise or "No specific praise captured."
        )

        # Add author context if available
        if author_context:
            prompt += f"\n\n## Author Context\n{self._format_author_context(author_context)}"

        # Call LLM for synthesis
        llm_config = LLMConfig(
            provider=LLMProvider(self.model_config.provider.value),
            model=self.model_config.model_name,
            temperature=self.model_config.temperature,
            max_tokens=self.model_config.max_tokens,
            response_format="json",
            api_key=self.api_key
        )

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Please synthesize the analysis into unified feedback."}
        ]

        response = await llm_service.generate(llm_config, messages)

        # Parse response
        return self._parse_synthesis(
            response.content,
            orchestrator_result,
            response.cost,
            response.usage.get("total_tokens", 0)
        )

    def _extract_agent_findings(
        self,
        result: Dict[str, Any],
        agent_type: str
    ) -> str:
        """Extract and format findings from a specific agent."""
        findings = []

        # Check recommendations
        for rec in result.get("recommendations", []):
            if rec.get("source_agent") == agent_type:
                text = rec.get("text", rec.get("description", ""))
                severity = rec.get("severity", "medium")
                findings.append(f"- [{severity.upper()}] {text}")

        # Check issues
        for issue in result.get("issues", []):
            if issue.get("source_agent") == agent_type:
                desc = issue.get("description", "")
                severity = issue.get("severity", "medium")
                findings.append(f"- [{severity.upper()}] {desc}")

        return "\n".join(findings) if findings else ""

    def _extract_praise(self, result: Dict[str, Any]) -> str:
        """Extract praise items from all agents."""
        praise_items = []

        for rec in result.get("recommendations", []):
            if rec.get("type") == "praise" or rec.get("severity") == "positive":
                text = rec.get("text", "")
                aspect = rec.get("aspect", "")
                if aspect:
                    praise_items.append(f"- {aspect}: {text}")
                else:
                    praise_items.append(f"- {text}")

        # Also check explicit praise list
        for praise in result.get("praise", []):
            text = praise.get("text", "")
            aspect = praise.get("aspect", "")
            if aspect:
                praise_items.append(f"- {aspect}: {text}")
            else:
                praise_items.append(f"- {text}")

        return "\n".join(praise_items) if praise_items else ""

    def _format_author_context(self, author_context: Dict[str, Any]) -> str:
        """Format author context for the prompt."""
        parts = []

        if author_context.get("strengths"):
            parts.append(f"Author strengths: {', '.join(author_context['strengths'])}")

        if author_context.get("common_issues"):
            parts.append(f"Recurring patterns: {', '.join(author_context['common_issues'][:3])}")

        if author_context.get("preferred_feedback_style"):
            parts.append(f"Prefers: {author_context['preferred_feedback_style']} feedback")

        return "\n".join(parts)

    def _parse_synthesis(
        self,
        content: str,
        original_result: Dict[str, Any],
        cost: float,
        tokens: int
    ) -> SynthesizedFeedback:
        """Parse the LLM synthesis response."""
        import json

        try:
            data = json.loads(content)

            return SynthesizedFeedback(
                narrative=data.get("narrative", content),
                summary=data.get("summary", ""),
                highlights=data.get("highlights", []),
                priorities=data.get("priorities", []),
                teaching_moments=data.get("teaching_moments", []),
                total_issues=len(original_result.get("issues", [])),
                total_praise=len(original_result.get("praise", [])),
                cost=cost + original_result.get("total_cost", 0),
                tokens=tokens + original_result.get("total_tokens", 0)
            )
        except json.JSONDecodeError:
            # Fallback: use raw content as narrative
            return SynthesizedFeedback(
                narrative=content,
                summary="Analysis complete.",
                total_issues=len(original_result.get("issues", [])),
                total_praise=len(original_result.get("praise", [])),
                cost=cost + original_result.get("total_cost", 0),
                tokens=tokens + original_result.get("total_tokens", 0)
            )

    async def quick_synthesis(
        self,
        findings: List[Dict[str, Any]],
        tone: SynthesisTone = SynthesisTone.DIRECT
    ) -> str:
        """
        Quick synthesis for single-agent or fast feedback.

        Returns just the narrative without full structured output.
        """
        if not findings:
            return "I reviewed your writing and it looks solid! No major concerns to flag."

        # For quick synthesis, we can do template-based without LLM
        high_priority = [f for f in findings if f.get("severity") == "high"]
        medium_priority = [f for f in findings if f.get("severity") == "medium"]
        praise = [f for f in findings if f.get("severity") == "positive" or f.get("type") == "praise"]

        parts = []

        if praise:
            parts.append(f"I noticed some strong moments in your writing - {praise[0].get('text', 'nice work')}.")

        if high_priority:
            parts.append(f"One thing I'd prioritize: {high_priority[0].get('text', high_priority[0].get('description', ''))}.")

        if medium_priority and len(parts) < 3:
            parts.append(f"You might also consider: {medium_priority[0].get('text', medium_priority[0].get('description', ''))}.")

        if not parts:
            parts.append("Your writing is looking good! Keep up the momentum.")

        return " ".join(parts)


def create_maxwell_synthesizer(
    api_key: str,
    model_config: Optional[ModelConfig] = None
) -> MaxwellSynthesizer:
    """Factory function to create a Maxwell Synthesizer."""
    return MaxwellSynthesizer(api_key=api_key, model_config=model_config)
