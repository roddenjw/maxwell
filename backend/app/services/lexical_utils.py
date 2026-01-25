"""
Lexical Editor Utilities
Shared utilities for converting between Lexical editor JSON and other formats.
Used by import/export services and chapter management.
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional


# Lexical format bitmask constants
FORMAT_BOLD = 1
FORMAT_ITALIC = 2
FORMAT_STRIKETHROUGH = 4
FORMAT_UNDERLINE = 8


@dataclass
class TextRun:
    """A run of text with consistent formatting."""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False

    def to_format_bitmask(self) -> int:
        """Convert formatting flags to Lexical format bitmask."""
        mask = 0
        if self.bold:
            mask |= FORMAT_BOLD
        if self.italic:
            mask |= FORMAT_ITALIC
        if self.strikethrough:
            mask |= FORMAT_STRIKETHROUGH
        if self.underline:
            mask |= FORMAT_UNDERLINE
        return mask

    @classmethod
    def from_format_bitmask(cls, text: str, format_mask: int) -> 'TextRun':
        """Create a TextRun from text and Lexical format bitmask."""
        return cls(
            text=text,
            bold=bool(format_mask & FORMAT_BOLD),
            italic=bool(format_mask & FORMAT_ITALIC),
            strikethrough=bool(format_mask & FORMAT_STRIKETHROUGH),
            underline=bool(format_mask & FORMAT_UNDERLINE),
        )


@dataclass
class RichParagraph:
    """A paragraph containing formatted text runs."""
    runs: List[TextRun] = field(default_factory=list)
    heading_level: int = 0  # 0 = normal paragraph, 1-6 = heading levels

    def get_plain_text(self) -> str:
        """Get plain text content of the paragraph."""
        return ''.join(run.text for run in self.runs)

    def is_empty(self) -> bool:
        """Check if paragraph has no content."""
        return not self.runs or all(not run.text.strip() for run in self.runs)


def extract_text_from_lexical(lexical_state_str: str) -> str:
    """
    Extract plain text from Lexical editor state JSON.
    Recursively walks the node tree and concatenates text content.

    Args:
        lexical_state_str: JSON string containing Lexical editor state

    Returns:
        Plain text extracted from the editor state
    """
    try:
        if not lexical_state_str or lexical_state_str.strip() == "":
            return ""

        state = json.loads(lexical_state_str)

        def walk_nodes(node):
            """Recursively extract text from Lexical nodes"""
            text_parts = []

            if isinstance(node, dict):
                # Direct text content
                if node.get("type") == "text" and "text" in node:
                    text_parts.append(node["text"])

                # Process children
                if "children" in node:
                    for child in node["children"]:
                        text_parts.append(walk_nodes(child))

                    # Add newline after paragraph
                    if node.get("type") == "paragraph":
                        text_parts.append("\n")

            return "".join(text_parts)

        # Start from root
        root = state.get("root", {})
        text = walk_nodes(root)

        # Clean up extra newlines
        text = text.strip()

        return text
    except Exception as e:
        print(f"Failed to extract text from lexical state: {e}")
        return ""


def plain_text_to_lexical(text: str) -> dict:
    """
    Convert plain text to Lexical editor state format.

    Args:
        text: Plain text string, with paragraphs separated by newlines

    Returns:
        Dictionary representing Lexical editor state
    """
    # Split text into paragraphs
    paragraphs = text.split('\n') if text else []

    # Create Lexical nodes for each paragraph
    children = []
    for para_text in paragraphs:
        # Include empty paragraphs to preserve document structure
        if para_text.strip():
            children.append({
                "children": [
                    {
                        "detail": 0,
                        "format": 0,
                        "mode": "normal",
                        "style": "",
                        "text": para_text,
                        "type": "text",
                        "version": 1
                    }
                ],
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "paragraph",
                "version": 1
            })
        else:
            # Empty paragraph
            children.append({
                "children": [],
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "paragraph",
                "version": 1
            })

    # Create root Lexical state
    return {
        "root": {
            "children": children,
            "direction": "ltr",
            "format": "",
            "indent": 0,
            "type": "root",
            "version": 1
        }
    }


def rich_paragraphs_to_lexical(paragraphs: List[RichParagraph]) -> dict:
    """
    Convert formatted paragraphs to Lexical editor state format.

    Args:
        paragraphs: List of RichParagraph objects with formatted text runs

    Returns:
        Dictionary representing Lexical editor state with formatting preserved
    """
    children = []

    for para in paragraphs:
        # Create text nodes for each run
        text_nodes = []
        for run in para.runs:
            if run.text:  # Only add non-empty runs
                text_nodes.append({
                    "detail": 0,
                    "format": run.to_format_bitmask(),
                    "mode": "normal",
                    "style": "",
                    "text": run.text,
                    "type": "text",
                    "version": 1
                })

        # Determine node type based on heading level
        if para.heading_level > 0:
            # Heading node
            children.append({
                "children": text_nodes,
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "heading",
                "tag": f"h{min(para.heading_level, 6)}",
                "version": 1
            })
        else:
            # Regular paragraph
            children.append({
                "children": text_nodes,
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "paragraph",
                "version": 1
            })

    return {
        "root": {
            "children": children,
            "direction": "ltr",
            "format": "",
            "indent": 0,
            "type": "root",
            "version": 1
        }
    }


def lexical_to_rich_paragraphs(lexical_state: str | dict) -> List[RichParagraph]:
    """
    Convert Lexical editor state to a list of RichParagraph objects.
    Extracts formatting information from the Lexical JSON tree.

    Args:
        lexical_state: Lexical editor state as JSON string or dict

    Returns:
        List of RichParagraph objects with formatting preserved
    """
    try:
        if isinstance(lexical_state, str):
            if not lexical_state or lexical_state.strip() == "":
                return []
            state = json.loads(lexical_state)
        else:
            state = lexical_state

        paragraphs = []
        root = state.get("root", {})

        def extract_runs_from_node(node) -> List[TextRun]:
            """Extract text runs from a node and its children."""
            runs = []

            if isinstance(node, dict):
                node_type = node.get("type", "")

                if node_type == "text":
                    text = node.get("text", "")
                    format_mask = node.get("format", 0)
                    if text:
                        runs.append(TextRun.from_format_bitmask(text, format_mask))

                elif node_type == "linebreak":
                    # Line breaks within a paragraph - could add as special run if needed
                    pass

                # Process children recursively
                if "children" in node:
                    for child in node["children"]:
                        runs.extend(extract_runs_from_node(child))

            return runs

        # Process root children (paragraphs, headings, etc.)
        for child in root.get("children", []):
            child_type = child.get("type", "")

            if child_type in ("paragraph", "heading"):
                runs = extract_runs_from_node(child)

                # Determine heading level
                heading_level = 0
                if child_type == "heading":
                    tag = child.get("tag", "h1")
                    if tag.startswith("h") and len(tag) == 2:
                        try:
                            heading_level = int(tag[1])
                        except ValueError:
                            heading_level = 1

                paragraphs.append(RichParagraph(runs=runs, heading_level=heading_level))

            elif child_type == "root":
                # Nested root - process recursively
                for nested_child in child.get("children", []):
                    if nested_child.get("type") in ("paragraph", "heading"):
                        runs = extract_runs_from_node(nested_child)
                        heading_level = 0
                        if nested_child.get("type") == "heading":
                            tag = nested_child.get("tag", "h1")
                            if tag.startswith("h") and len(tag) == 2:
                                try:
                                    heading_level = int(tag[1])
                                except ValueError:
                                    heading_level = 1
                        paragraphs.append(RichParagraph(runs=runs, heading_level=heading_level))

        return paragraphs

    except Exception as e:
        print(f"Failed to convert lexical state to rich paragraphs: {e}")
        return []


def plain_text_to_lexical_json(text: str) -> str:
    """
    Convert plain text to Lexical editor state JSON string.
    Convenience wrapper around plain_text_to_lexical().

    Args:
        text: Plain text string

    Returns:
        JSON string representing Lexical editor state
    """
    return json.dumps(plain_text_to_lexical(text))


def rich_paragraphs_to_lexical_json(paragraphs: List[RichParagraph]) -> str:
    """
    Convert formatted paragraphs to Lexical editor state JSON string.
    Convenience wrapper around rich_paragraphs_to_lexical().

    Args:
        paragraphs: List of RichParagraph objects

    Returns:
        JSON string representing Lexical editor state
    """
    return json.dumps(rich_paragraphs_to_lexical(paragraphs))
