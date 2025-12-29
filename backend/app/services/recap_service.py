"""
Recap Service - Generate aesthetic chapter and arc summaries using Claude API
"""

import os
import json
import hashlib
from typing import Dict, List, Optional
from anthropic import Anthropic


class RecapService:
    """Generate beautiful recaps for chapters and story arcs"""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def generate_chapter_recap(self, chapter_title: str, chapter_content: str) -> Dict:
        """
        Generate a beautiful recap for a single chapter

        Args:
            chapter_title: Title of the chapter
            chapter_content: Full text content of the chapter

        Returns:
            Structured recap dictionary with key events, themes, etc.
        """
        prompt = f"""Analyze this chapter from a fiction manuscript and create an aesthetic recap summary.

Chapter Title: {chapter_title}

Chapter Content:
{chapter_content[:8000]}  # Limit to ~8000 chars to stay within context

Please provide a structured recap in JSON format with these elements:

1. **summary**: A concise 2-3 sentence overview of what happens in this chapter
2. **key_events**: List of 3-5 major events or plot points (bullet format)
3. **character_developments**: Array of objects with "character" and "development" describing how characters change or reveal themselves
4. **themes**: List of 2-4 thematic elements or motifs present in this chapter
5. **emotional_tone**: A brief description of the chapter's emotional atmosphere (e.g., "tense and foreboding", "hopeful but uncertain")
6. **narrative_arc**: Where this chapter sits in the story (e.g., "rising action", "climax", "denouement")
7. **memorable_moments**: 1-2 standout scenes or lines that define this chapter

Format your response as valid JSON. Be specific, vivid, and useful for a writer reviewing before writing the next chapter."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract JSON from response
            content = response.content[0].text

            # Try to parse JSON (claude might wrap it in markdown code blocks)
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            recap_data = json.loads(json_str)

            return recap_data

        except Exception as e:
            print(f"Error generating chapter recap: {e}")
            # Return a minimal recap on error
            return {
                "summary": "Unable to generate recap at this time.",
                "key_events": [],
                "character_developments": [],
                "themes": [],
                "emotional_tone": "Unknown",
                "narrative_arc": "Unknown",
                "memorable_moments": []
            }

    def generate_arc_recap(
        self,
        arc_title: str,
        chapters: List[Dict[str, str]]
    ) -> Dict:
        """
        Generate a recap for a multi-chapter story arc

        Args:
            arc_title: Name/description of this arc
            chapters: List of dicts with 'title' and 'content' keys

        Returns:
            Structured recap dictionary for the entire arc
        """
        # Combine chapter summaries (limit total length)
        chapters_text = "\n\n".join([
            f"**{ch['title']}**\n{ch['content'][:2000]}"
            for ch in chapters[:10]  # Max 10 chapters
        ])

        prompt = f"""Analyze this story arc from a fiction manuscript and create an aesthetic recap summary.

Arc: {arc_title}
Number of Chapters: {len(chapters)}

Chapters:
{chapters_text}

Please provide a structured recap in JSON format with these elements:

1. **summary**: A 3-4 sentence overview of the entire arc's narrative journey
2. **major_plot_points**: List of 5-7 critical events across the arc
3. **character_arcs**: Array of objects with "character" and "arc" describing character transformations across these chapters
4. **central_themes**: List of 3-5 major themes that define this arc
5. **emotional_journey**: Description of how the emotional tone evolves across the arc
6. **arc_structure**: Brief analysis of the arc's pacing and structure
7. **climactic_moment**: The most dramatic or pivotal scene in the arc
8. **unresolved_threads**: Any plot threads or questions left open

Format your response as valid JSON. Be insightful and helpful for a writer planning what comes next."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            content = response.content[0].text

            # Extract JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            recap_data = json.loads(json_str)

            # Add chapter IDs for reference
            recap_data["chapter_ids"] = [ch.get("id") for ch in chapters if ch.get("id")]

            return recap_data

        except Exception as e:
            print(f"Error generating arc recap: {e}")
            return {
                "summary": "Unable to generate arc recap at this time.",
                "major_plot_points": [],
                "character_arcs": [],
                "central_themes": [],
                "emotional_journey": "Unknown",
                "arc_structure": "Unknown",
                "climactic_moment": "",
                "unresolved_threads": [],
                "chapter_ids": [ch.get("id") for ch in chapters if ch.get("id")]
            }

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute a hash of content for cache invalidation"""
        return hashlib.md5(content.encode()).hexdigest()


# Singleton instance
recap_service = RecapService()
