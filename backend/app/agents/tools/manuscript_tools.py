"""
Manuscript Tools for Maxwell Agents

Tools for querying chapters, content, and manuscript structure.
"""

from typing import Optional, Type
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool

from app.database import SessionLocal
from app.models.manuscript import Manuscript, Chapter


class QueryChaptersInput(BaseModel):
    """Input for querying chapters"""
    manuscript_id: str = Field(description="The manuscript ID")
    include_folders: bool = Field(
        default=True,
        description="Whether to include folder items"
    )


class QueryChapters(BaseTool):
    """Query chapter structure"""

    name: str = "query_chapters"
    description: str = """Get the manuscript's chapter structure with titles and word counts.
    Use this to understand the document organization and find specific chapters."""
    args_schema: Type[BaseModel] = QueryChaptersInput

    def _run(self, manuscript_id: str, include_folders: bool = True) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Get manuscript
            manuscript = db.query(Manuscript).filter(
                Manuscript.id == manuscript_id
            ).first()

            if not manuscript:
                return f"Manuscript {manuscript_id} not found"

            # Get chapters
            query = db.query(Chapter).filter(
                Chapter.manuscript_id == manuscript_id
            )

            if not include_folders:
                query = query.filter(Chapter.is_folder == 0)

            chapters = query.order_by(Chapter.order_index).all()

            if not chapters:
                return "No chapters found"

            # Build tree structure
            def get_children(parent_id):
                return [c for c in chapters if c.parent_id == parent_id]

            def format_chapter(chapter, indent=0):
                prefix = "  " * indent
                type_icon = "[F]" if chapter.is_folder else "[D]"
                words = f"({chapter.word_count:,} words)" if not chapter.is_folder else ""
                return f"{prefix}{type_icon} {chapter.title} {words}"

            def format_tree(parent_id=None, indent=0):
                lines = []
                for chapter in get_children(parent_id):
                    lines.append(format_chapter(chapter, indent))
                    lines.extend(format_tree(chapter.id, indent + 1))
                return lines

            # Format output
            lines = [
                f"## {manuscript.title}",
                f"Total Word Count: {manuscript.word_count:,}",
                f"Chapters: {len([c for c in chapters if not c.is_folder])}",
                "\n### Structure:"
            ]
            lines.extend(format_tree())

            return "\n".join(lines)

        finally:
            db.close()


class QueryChapterContentInput(BaseModel):
    """Input for querying chapter content"""
    chapter_id: str = Field(description="The chapter ID")
    max_chars: int = Field(
        default=3000,
        description="Maximum characters to return"
    )


class QueryChapterContent(BaseTool):
    """Query chapter content"""

    name: str = "query_chapter_content"
    description: str = """Get the text content of a specific chapter.
    Use this when you need to read what's actually written in a chapter."""
    args_schema: Type[BaseModel] = QueryChapterContentInput

    def _run(self, chapter_id: str, max_chars: int = 3000) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            chapter = db.query(Chapter).filter(
                Chapter.id == chapter_id
            ).first()

            if not chapter:
                return f"Chapter {chapter_id} not found"

            if chapter.is_folder:
                return f"'{chapter.title}' is a folder, not a document"

            content = chapter.content or ""

            # Format output
            lines = [
                f"## {chapter.title}",
                f"Word Count: {chapter.word_count:,}",
                "\n### Content:"
            ]

            if len(content) > max_chars:
                lines.append(content[:max_chars])
                lines.append(f"\n...[truncated, {len(content) - max_chars:,} more chars]")
            else:
                lines.append(content)

            return "\n".join(lines)

        finally:
            db.close()


class SearchManuscriptInput(BaseModel):
    """Input for searching manuscript"""
    manuscript_id: str = Field(description="The manuscript ID")
    query: str = Field(description="Search query")
    max_results: int = Field(default=5, description="Maximum results to return")


class SearchManuscript(BaseTool):
    """Search manuscript content"""

    name: str = "search_manuscript"
    description: str = """Search for text across all chapters in the manuscript.
    Returns matching excerpts with chapter context.
    Use this to find where specific topics, characters, or phrases are mentioned."""
    args_schema: Type[BaseModel] = SearchManuscriptInput

    def _run(
        self,
        manuscript_id: str,
        query: str,
        max_results: int = 5
    ) -> str:
        """Execute the tool"""
        db = SessionLocal()
        try:
            # Get all document chapters
            chapters = db.query(Chapter).filter(
                Chapter.manuscript_id == manuscript_id,
                Chapter.is_folder == 0
            ).all()

            if not chapters:
                return "No chapters to search"

            query_lower = query.lower()
            results = []

            for chapter in chapters:
                content = (chapter.content or "").lower()
                if query_lower in content:
                    # Find position and extract context
                    pos = content.find(query_lower)
                    start = max(0, pos - 100)
                    end = min(len(content), pos + len(query) + 100)

                    # Get original case content
                    original = chapter.content or ""
                    excerpt = original[start:end]

                    # Count occurrences
                    count = content.count(query_lower)

                    results.append({
                        "chapter": chapter.title,
                        "chapter_id": chapter.id,
                        "count": count,
                        "excerpt": excerpt
                    })

                    if len(results) >= max_results:
                        break

            if not results:
                return f"No matches for '{query}' in manuscript"

            # Format output
            lines = [f"Found matches for '{query}':"]

            for result in results:
                lines.append(
                    f"\n### {result['chapter']} ({result['count']} matches)"
                )
                lines.append(f"Chapter ID: {result['chapter_id']}")
                lines.append(f"Excerpt: ...{result['excerpt']}...")

            return "\n".join(lines)

        finally:
            db.close()


# Create tool instances
query_chapters = QueryChapters()
query_chapter_content = QueryChapterContent()
search_manuscript = SearchManuscript()
