"""
Git-based versioning service for Time Machine functionality
Uses pygit2 for version control of manuscripts
"""

import pygit2
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os

from app.models.versioning import Snapshot
from app.database import SessionLocal

# Data directory
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
MANUSCRIPTS_DIR = DATA_DIR / "manuscripts"
MANUSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)


class VersionService:
    """Service for Git-based manuscript versioning"""

    def __init__(self):
        # Git signature for commits
        self.signature = pygit2.Signature(
            "Maxwell IDE",
            "noreply@maxwell.local",
            int(datetime.utcnow().timestamp())
        )

    def get_repo_path(self, manuscript_id: str) -> Path:
        """Get path to manuscript's Git repository"""
        return MANUSCRIPTS_DIR / manuscript_id / ".codex"

    def init_repository(self, manuscript_id: str) -> pygit2.Repository:
        """Initialize Git repository for a manuscript"""
        repo_path = self.get_repo_path(manuscript_id)

        if repo_path.exists():
            # Repository already exists
            return pygit2.Repository(str(repo_path))

        # Create directory structure
        repo_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize Git repository
        repo = pygit2.init_repository(str(repo_path), bare=False)

        # Create initial .gitkeep file
        gitkeep_path = repo_path / ".gitkeep"
        gitkeep_path.write_text("")

        # Create initial commit
        index = repo.index
        index.read()
        index.add(".gitkeep")
        index.write()

        tree_id = index.write_tree()

        repo.create_commit(
            "HEAD",
            self.signature,
            self.signature,
            "Initialize manuscript repository",
            tree_id,
            []
        )

        return repo

    def _extract_text_from_lexical_json(self, content: str) -> str:
        """
        Extract plain text from Lexical editor state JSON

        Args:
            content: Lexical JSON string

        Returns:
            Plain text content
        """
        try:
            # Parse the Lexical JSON
            state = json.loads(content)

            def extract_text_recursive(node):
                """Recursively extract text from Lexical nodes"""
                text_parts = []

                # If this node has text, add it
                if isinstance(node, dict) and "text" in node:
                    text_parts.append(node["text"])

                # If this node has children, recurse
                if isinstance(node, dict) and "children" in node:
                    for child in node["children"]:
                        text_parts.append(extract_text_recursive(child))

                # Join with spaces, preserving paragraph breaks
                if isinstance(node, dict) and node.get("type") == "paragraph":
                    return "\n".join(text_parts) + "\n"

                return " ".join(text_parts)

            # Extract from root
            if "root" in state:
                return extract_text_recursive(state["root"]).strip()

            return content  # Fallback to raw content

        except (json.JSONDecodeError, KeyError, TypeError):
            # If parsing fails, return content as-is
            return content

    def create_snapshot(
        self,
        manuscript_id: str,
        trigger_type: str,
        label: str = "",
        description: str = "",
        word_count: int = 0,
        content: str = None  # Deprecated - kept for backward compatibility
    ) -> Snapshot:
        """
        Create a snapshot (Git commit) of ALL chapters in the manuscript

        Args:
            manuscript_id: ID of the manuscript
            trigger_type: MANUAL, AUTO, CHAPTER_COMPLETE, PRE_GENERATION, SESSION_END
            label: Optional user-provided label
            description: Optional description
            word_count: Total word count at time of snapshot
            content: DEPRECATED - snapshots now capture all chapters

        Returns:
            Snapshot model instance
        """
        from app.models.manuscript import Chapter

        repo = self.init_repository(manuscript_id)
        repo_path = self.get_repo_path(manuscript_id)

        # Create chapters directory
        chapters_dir = repo_path / "chapters"
        chapters_dir.mkdir(exist_ok=True)

        # Fetch all chapters from database
        db = SessionLocal()
        try:
            chapters = db.query(Chapter).filter(
                Chapter.manuscript_id == manuscript_id
            ).all()

            total_word_count = 0
            chapter_tree = []

            # Save each chapter as a separate file
            for chapter in chapters:
                chapter_data = {
                    "id": chapter.id,
                    "title": chapter.title,
                    "is_folder": chapter.is_folder,
                    "parent_id": chapter.parent_id,
                    "order_index": chapter.order_index,
                    "lexical_state": chapter.lexical_state,
                    "content": chapter.content,
                    "word_count": chapter.word_count,
                }

                # Save chapter JSON
                chapter_path = chapters_dir / f"{chapter.id}.json"
                chapter_path.write_text(json.dumps(chapter_data, indent=2), encoding="utf-8")

                # Also save plain text version for diffs
                if chapter.content and not chapter.is_folder:
                    text_path = chapters_dir / f"{chapter.id}.txt"
                    text_path.write_text(chapter.content, encoding="utf-8")

                total_word_count += chapter.word_count or 0

                # Build tree structure for metadata
                chapter_tree.append({
                    "id": chapter.id,
                    "title": chapter.title,
                    "parent_id": chapter.parent_id,
                    "order_index": chapter.order_index,
                    "is_folder": chapter.is_folder,
                    "word_count": chapter.word_count
                })

        finally:
            db.close()

        # Write metadata
        metadata = {
            "manuscript_id": manuscript_id,
            "trigger_type": trigger_type,
            "label": label,
            "description": description,
            "word_count": word_count or total_word_count,
            "chapter_count": len(chapters),
            "chapter_tree": chapter_tree,
            "timestamp": datetime.utcnow().isoformat()
        }
        metadata_path = repo_path / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        # Stage all files
        index = repo.index
        index.read()
        index.add("metadata.json")

        # Add all chapter files
        for chapter_file in chapters_dir.glob("*.json"):
            index.add(f"chapters/{chapter_file.name}")
        for text_file in chapters_dir.glob("*.txt"):
            index.add(f"chapters/{text_file.name}")

        index.write()

        # Create tree
        tree_id = index.write_tree()

        # Get parent commit
        try:
            parent = repo.head.peel()
            parents = [parent.id]
        except pygit2.GitError:
            parents = []

        # Create commit
        commit_message = self._build_commit_message(trigger_type, label, description)
        commit_id = repo.create_commit(
            "HEAD",
            self.signature,
            self.signature,
            commit_message,
            tree_id,
            parents
        )

        # Store snapshot metadata in database
        db = SessionLocal()
        try:
            # Create the new snapshot
            snapshot = Snapshot(
                manuscript_id=manuscript_id,
                commit_hash=str(commit_id),
                label=label,
                description=description,
                trigger_type=trigger_type,
                word_count=word_count or total_word_count,
                auto_summary=""
            )
            db.add(snapshot)
            db.commit()
            db.refresh(snapshot)

            # Generate auto-summary by comparing with previous snapshot
            previous_snapshot = db.query(Snapshot).filter(
                Snapshot.manuscript_id == manuscript_id,
                Snapshot.id != snapshot.id
            ).order_by(Snapshot.created_at.desc()).first()

            if previous_snapshot:
                auto_summary = self.generate_basic_summary(
                    manuscript_id, previous_snapshot, snapshot
                )
                if auto_summary:
                    snapshot.auto_summary = auto_summary
                    db.commit()
                    db.refresh(snapshot)

            return snapshot
        finally:
            db.close()

    def _build_commit_message(
        self,
        trigger_type: str,
        label: str,
        description: str
    ) -> str:
        """Build Git commit message"""
        if label:
            message = f"[{trigger_type}] {label}"
        else:
            message = f"[{trigger_type}] Snapshot"

        if description:
            message += f"\n\n{description}"

        return message

    def get_history(self, manuscript_id: str) -> List[Dict[str, Any]]:
        """
        Get commit history for a manuscript

        Returns list of snapshots from database with Git metadata
        """
        db = SessionLocal()
        try:
            snapshots = db.query(Snapshot).filter(
                Snapshot.manuscript_id == manuscript_id
            ).order_by(Snapshot.created_at.desc()).all()

            history = []
            repo = self.init_repository(manuscript_id)

            for snapshot in snapshots:
                try:
                    commit = repo.get(snapshot.commit_hash)
                    history.append({
                        "id": snapshot.id,
                        "commit_hash": snapshot.commit_hash,
                        "label": snapshot.label,
                        "description": snapshot.description,
                        "auto_summary": snapshot.auto_summary or "",
                        "trigger_type": snapshot.trigger_type,
                        "word_count": snapshot.word_count,
                        "created_at": snapshot.created_at.isoformat(),
                        "author": commit.author.name,
                        "message": commit.message
                    })
                except KeyError:
                    # Commit not found in repo
                    history.append({
                        "id": snapshot.id,
                        "commit_hash": snapshot.commit_hash,
                        "label": snapshot.label,
                        "description": snapshot.description,
                        "auto_summary": snapshot.auto_summary or "",
                        "trigger_type": snapshot.trigger_type,
                        "word_count": snapshot.word_count,
                        "created_at": snapshot.created_at.isoformat(),
                        "error": "Commit not found in repository"
                    })

            return history
        finally:
            db.close()

    def restore_snapshot(
        self,
        manuscript_id: str,
        snapshot_id: str,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Restore ALL chapters to a specific snapshot state

        Args:
            manuscript_id: ID of the manuscript
            snapshot_id: ID of the snapshot to restore
            create_backup: Whether to create a backup snapshot first

        Returns:
            Dictionary with restoration info including chapter count
        """
        from app.models.manuscript import Chapter

        db = SessionLocal()
        try:
            # Get snapshot from database
            snapshot = db.query(Snapshot).filter(
                Snapshot.id == snapshot_id,
                Snapshot.manuscript_id == manuscript_id
            ).first()

            if not snapshot:
                raise ValueError(f"Snapshot {snapshot_id} not found")

            repo = self.init_repository(manuscript_id)
            repo_path = self.get_repo_path(manuscript_id)

            # Create backup snapshot if requested
            if create_backup:
                self.create_snapshot(
                    manuscript_id=manuscript_id,
                    trigger_type="AUTO",
                    label="Pre-restore backup",
                    description=f"Automatic backup before restoring to {snapshot.label or snapshot.commit_hash[:8]}"
                )

            # Checkout the commit
            commit = repo.get(snapshot.commit_hash)
            repo.checkout_tree(commit.tree)

            # Reset HEAD to the commit to update working directory
            repo.set_head(commit.id)

            # Load chapters from snapshot
            chapters_dir = repo_path / "chapters"

            if not chapters_dir.exists():
                # Try legacy format (single manuscript.json)
                content_path = repo_path / "manuscript.json"
                if content_path.exists():
                    content = content_path.read_text(encoding="utf-8")
                    return {
                        "content": content,
                        "chapters_restored": 0,
                        "legacy_format": True
                    }
                else:
                    raise ValueError("No chapter data found in snapshot")

            # Restore all chapters
            restored_count = 0
            chapter_files = list(chapters_dir.glob("*.json"))

            for chapter_file in chapter_files:
                chapter_data = json.loads(chapter_file.read_text(encoding="utf-8"))

                # Check if chapter exists
                existing_chapter = db.query(Chapter).filter(
                    Chapter.id == chapter_data["id"]
                ).first()

                if existing_chapter:
                    # Update existing chapter
                    existing_chapter.title = chapter_data.get("title", "Untitled")
                    existing_chapter.is_folder = chapter_data.get("is_folder", 0)
                    existing_chapter.parent_id = chapter_data.get("parent_id")
                    existing_chapter.order_index = chapter_data.get("order_index", 0)
                    existing_chapter.lexical_state = chapter_data.get("lexical_state", "")
                    existing_chapter.content = chapter_data.get("content", "")
                    existing_chapter.word_count = chapter_data.get("word_count", 0)
                else:
                    # Create new chapter (it was deleted after snapshot)
                    new_chapter = Chapter(
                        id=chapter_data["id"],
                        manuscript_id=manuscript_id,
                        title=chapter_data.get("title", "Untitled"),
                        is_folder=chapter_data.get("is_folder", 0),
                        parent_id=chapter_data.get("parent_id"),
                        order_index=chapter_data.get("order_index", 0),
                        lexical_state=chapter_data.get("lexical_state", ""),
                        content=chapter_data.get("content", ""),
                        word_count=chapter_data.get("word_count", 0)
                    )
                    db.add(new_chapter)

                restored_count += 1

            # Delete chapters that don't exist in snapshot
            snapshot_chapter_ids = {f.stem for f in chapter_files}
            current_chapters = db.query(Chapter).filter(
                Chapter.manuscript_id == manuscript_id
            ).all()

            deleted_count = 0
            for chapter in current_chapters:
                if chapter.id not in snapshot_chapter_ids:
                    db.delete(chapter)
                    deleted_count += 1

            db.commit()

            return {
                "chapters_restored": restored_count,
                "chapters_deleted": deleted_count,
                "snapshot_label": snapshot.label or "Unnamed",
                "legacy_format": False
            }

        finally:
            db.close()

    def get_diff(
        self,
        manuscript_id: str,
        snapshot_id_old: str,
        snapshot_id_new: str
    ) -> Dict[str, Any]:
        """
        Get diff between two snapshots

        Returns:
            Dict with diff information
        """
        db = SessionLocal()
        try:
            old_snapshot = db.query(Snapshot).filter(
                Snapshot.id == snapshot_id_old
            ).first()
            new_snapshot = db.query(Snapshot).filter(
                Snapshot.id == snapshot_id_new
            ).first()

            if not old_snapshot or not new_snapshot:
                raise ValueError("One or both snapshots not found")

            repo = self.init_repository(manuscript_id)

            old_commit = repo.get(old_snapshot.commit_hash)
            new_commit = repo.get(new_snapshot.commit_hash)

            # Get diff between commits
            diff = repo.diff(old_commit.tree, new_commit.tree)

            # Extract text changes
            changes = {
                "files_changed": diff.stats.files_changed,
                "insertions": diff.stats.insertions,
                "deletions": diff.stats.deletions,
                "patches": [],
                "diff_html": ""
            }

            # Generate HTML diff
            html_lines = []
            txt_diff_found = False

            for patch in diff:
                changes["patches"].append({
                    "old_file": patch.delta.old_file.path,
                    "new_file": patch.delta.new_file.path,
                    "status": patch.delta.status_char(),
                    "patch": patch.text
                })

                # Convert patch to HTML - use manuscript.txt for readable diffs
                if patch.delta.new_file.path == "manuscript.txt":
                    txt_diff_found = True
                    for line in patch.text.split('\n'):
                        # Skip all git technical headers and markers
                        if (line.startswith('diff --git') or
                            line.startswith('index ') or
                            line.startswith('---') or
                            line.startswith('+++') or
                            line.startswith('@@') or
                            line.strip() == r'\ No newline at end of file'):
                            continue

                        # Process actual content lines
                        if line.startswith('+'):
                            html_lines.append(f'<ins>{line[1:]}</ins>')
                        elif line.startswith('-'):
                            html_lines.append(f'<del>{line[1:]}</del>')
                        elif line.strip():  # Unchanged lines
                            html_lines.append(line)

            # Fallback: If no .txt diff found, extract text from JSON diffs
            if not txt_diff_found:
                # Try to extract and compare text from manuscript.json
                try:
                    # Get the actual content from both commits
                    old_tree = old_commit.tree
                    new_tree = new_commit.tree

                    old_json_content = ""
                    new_json_content = ""

                    # Read old content
                    try:
                        old_entry = old_tree['manuscript.json']
                        old_blob = repo.get(old_entry.id)
                        old_json_content = old_blob.data.decode('utf-8')
                    except (KeyError, AttributeError):
                        pass

                    # Read new content
                    try:
                        new_entry = new_tree['manuscript.json']
                        new_blob = repo.get(new_entry.id)
                        new_json_content = new_blob.data.decode('utf-8')
                    except (KeyError, AttributeError):
                        pass

                    # Extract text from both
                    old_text = self._extract_text_from_lexical_json(old_json_content)
                    new_text = self._extract_text_from_lexical_json(new_json_content)

                    # Simple line-by-line comparison
                    if old_text != new_text:
                        html_lines.append(f'<del>{old_text}</del>')
                        html_lines.append(f'<ins>{new_text}</ins>')
                except Exception as e:
                    # If fallback fails, show a message
                    html_lines.append(f'<p>Unable to generate readable diff. Please create new snapshots to see text changes.</p>')

            changes["diff_html"] = '\n'.join(html_lines)
            return changes

        finally:
            db.close()

    def generate_basic_summary(
        self,
        manuscript_id: str,
        old_snapshot: Snapshot,
        new_snapshot: Snapshot
    ) -> str:
        """
        Generate a basic (non-AI) summary of changes between snapshots.
        This is synchronous and suitable for use in create_snapshot().

        Args:
            manuscript_id: ID of the manuscript
            old_snapshot: The older snapshot
            new_snapshot: The newer snapshot

        Returns:
            Human-readable summary string
        """
        try:
            changes = self._get_chapter_changes(manuscript_id, old_snapshot, new_snapshot)

            # Build summary parts
            summary_parts = []

            # Word count delta
            word_delta = changes['word_delta']
            if word_delta > 0:
                summary_parts.append(f"+{word_delta:,} words")
            elif word_delta < 0:
                summary_parts.append(f"{word_delta:,} words")
            else:
                summary_parts.append("No word count change")

            # Chapter counts
            chapter_details = []
            if changes['added']:
                count = len(changes['added'])
                chapter_details.append(f"{count} new chapter{'s' if count > 1 else ''}")
            if changes['removed']:
                count = len(changes['removed'])
                chapter_details.append(f"{count} removed")
            if changes['modified']:
                count = len(changes['modified'])
                chapter_details.append(f"{count} edited")

            if chapter_details:
                summary_parts.append(" | ".join(chapter_details))

            basic_line = " | ".join(summary_parts[:2]) if len(summary_parts) > 1 else summary_parts[0]

            # Add chapter details
            details = []
            for ch in changes['added'][:2]:  # Limit to 2 new chapters
                details.append(f"New: \"{ch['title']}\"")
            for ch in changes['removed'][:2]:
                details.append(f"Removed: \"{ch['title']}\"")
            for ch in changes['modified'][:2]:  # Limit to 2 most-changed
                delta = ch['word_delta']
                delta_str = f"+{delta}" if delta > 0 else str(delta)
                details.append(f"\"{ch['title']}\" ({delta_str})")

            # Count extras
            total_mentioned = min(2, len(changes['added'])) + min(2, len(changes['removed'])) + min(2, len(changes['modified']))
            total_changes = len(changes['added']) + len(changes['removed']) + len(changes['modified'])
            if total_changes > total_mentioned:
                details.append(f"+{total_changes - total_mentioned} more")

            if details:
                return f"{basic_line}\n{'; '.join(details)}"
            return basic_line

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to generate basic summary: {e}")
            return ""

    def _get_chapter_changes(
        self,
        manuscript_id: str,
        old_snapshot: Snapshot,
        new_snapshot: Snapshot
    ) -> Dict[str, Any]:
        """
        Analyze chapter-level changes between two snapshots.

        Returns:
            Dict with added, removed, modified chapters and word count delta
        """
        repo = self.init_repository(manuscript_id)
        repo_path = self.get_repo_path(manuscript_id)

        old_commit = repo.get(old_snapshot.commit_hash)
        new_commit = repo.get(new_snapshot.commit_hash)

        # Get chapter trees from metadata
        def get_chapter_tree(commit):
            """Extract chapter tree from commit's metadata.json"""
            try:
                tree = commit.tree
                metadata_entry = tree['metadata.json']
                metadata_blob = repo.get(metadata_entry.id)
                metadata = json.loads(metadata_blob.data.decode('utf-8'))
                return {c['id']: c for c in metadata.get('chapter_tree', [])}
            except (KeyError, json.JSONDecodeError):
                return {}

        old_chapters = get_chapter_tree(old_commit)
        new_chapters = get_chapter_tree(new_commit)

        # Calculate changes
        old_ids = set(old_chapters.keys())
        new_ids = set(new_chapters.keys())

        added_ids = new_ids - old_ids
        removed_ids = old_ids - new_ids
        common_ids = old_ids & new_ids

        # Find modified chapters (by comparing word counts or content)
        modified_chapters = []
        for cid in common_ids:
            old_ch = old_chapters[cid]
            new_ch = new_chapters[cid]
            if old_ch.get('word_count', 0) != new_ch.get('word_count', 0):
                word_delta = new_ch.get('word_count', 0) - old_ch.get('word_count', 0)
                modified_chapters.append({
                    'id': cid,
                    'title': new_ch.get('title', 'Untitled'),
                    'word_delta': word_delta
                })

        # Build result
        added = [
            {'id': cid, 'title': new_chapters[cid].get('title', 'Untitled'), 'is_folder': new_chapters[cid].get('is_folder', False)}
            for cid in added_ids if not new_chapters[cid].get('is_folder', False)
        ]
        removed = [
            {'id': cid, 'title': old_chapters[cid].get('title', 'Untitled')}
            for cid in removed_ids if not old_chapters[cid].get('is_folder', False)
        ]

        # Calculate total word delta
        word_delta = (new_snapshot.word_count or 0) - (old_snapshot.word_count or 0)

        return {
            'added': added,
            'removed': removed,
            'modified': modified_chapters,
            'word_delta': word_delta,
            'old_word_count': old_snapshot.word_count or 0,
            'new_word_count': new_snapshot.word_count or 0
        }

    async def generate_changeset_summary(
        self,
        manuscript_id: str,
        old_snapshot_id: str,
        new_snapshot_id: str,
        use_ai: bool = True,
        api_key: Optional[str] = None
    ) -> str:
        """
        Generate human-readable summary of changes between snapshots.

        Args:
            manuscript_id: ID of the manuscript
            old_snapshot_id: ID of the older snapshot
            new_snapshot_id: ID of the newer snapshot
            use_ai: Whether to use AI for narrative enhancement (requires api_key)
            api_key: OpenRouter API key for AI enhancement

        Returns:
            Human-readable summary string
        """
        db = SessionLocal()
        try:
            old_snapshot = db.query(Snapshot).filter(
                Snapshot.id == old_snapshot_id
            ).first()
            new_snapshot = db.query(Snapshot).filter(
                Snapshot.id == new_snapshot_id
            ).first()

            if not old_snapshot or not new_snapshot:
                return ""

            # Get chapter-level changes
            changes = self._get_chapter_changes(manuscript_id, old_snapshot, new_snapshot)

            # Build basic summary
            summary_parts = []

            # Word count delta
            word_delta = changes['word_delta']
            if word_delta > 0:
                summary_parts.append(f"+{word_delta:,} words")
            elif word_delta < 0:
                summary_parts.append(f"{word_delta:,} words")

            # Chapter counts
            if changes['added']:
                summary_parts.append(f"{len(changes['added'])} new chapter{'s' if len(changes['added']) > 1 else ''}")
            if changes['removed']:
                summary_parts.append(f"{len(changes['removed'])} removed")
            if changes['modified']:
                summary_parts.append(f"{len(changes['modified'])} edited")

            basic_summary = " | ".join(summary_parts) if summary_parts else "No significant changes"

            # Build detailed chapter info
            details = []
            for ch in changes['added']:
                details.append(f"New: \"{ch['title']}\"")
            for ch in changes['removed']:
                details.append(f"Removed: \"{ch['title']}\"")
            for ch in changes['modified'][:3]:  # Limit to 3 most-changed
                delta_str = f"+{ch['word_delta']}" if ch['word_delta'] > 0 else str(ch['word_delta'])
                details.append(f"Edited: \"{ch['title']}\" ({delta_str} words)")

            if len(changes['modified']) > 3:
                details.append(f"...and {len(changes['modified']) - 3} more edited")

            # Combine basic + details
            full_summary = basic_summary
            if details:
                full_summary += "\n" + "\n".join(details)

            # AI enhancement (optional)
            if use_ai and api_key and (changes['added'] or changes['modified']):
                try:
                    ai_narrative = await self._generate_ai_narrative(
                        changes, api_key, manuscript_id
                    )
                    if ai_narrative:
                        full_summary = ai_narrative
                except Exception as e:
                    # Fallback to basic summary on AI failure
                    import logging
                    logging.getLogger(__name__).warning(f"AI summary generation failed: {e}")

            return full_summary

        finally:
            db.close()

    async def _generate_ai_narrative(
        self,
        changes: Dict[str, Any],
        api_key: str,
        manuscript_id: str
    ) -> Optional[str]:
        """
        Generate an AI-enhanced narrative summary of changes.

        Args:
            changes: Chapter change data from _get_chapter_changes()
            api_key: OpenRouter API key
            manuscript_id: ID of the manuscript

        Returns:
            AI-generated narrative summary or None on failure
        """
        from app.services.openrouter_service import OpenRouterService

        # Build context for AI
        word_delta = changes['word_delta']
        word_str = f"+{word_delta:,}" if word_delta > 0 else f"{word_delta:,}"

        context = f"""You are summarizing changes made to a fiction manuscript between two snapshots (like a Git commit message).

Write a brief, engaging 1-2 sentence summary that describes what changed in a narrative way.
Focus on the creative work: new chapters added, content expanded, scenes edited.
Be concise and writer-friendly. Don't mention technical details like "snapshots" or "commits".

Format: Start with the word count change, then describe the creative changes.
Example outputs:
- "+1,250 words. Added climactic confrontation in Chapter 8 and expanded the tavern scene."
- "-340 words. Trimmed Chapter 5 dialogue and removed a redundant flashback."
- "+2,100 words across 3 chapters. New chapter introduces the mysterious stranger."""

        # Build the changes description
        changes_text = f"Word count change: {word_str}\n"

        if changes['added']:
            chapter_names = [f'"{ch["title"]}"' for ch in changes['added']]
            changes_text += f"New chapters: {', '.join(chapter_names)}\n"

        if changes['removed']:
            chapter_names = [f'"{ch["title"]}"' for ch in changes['removed']]
            changes_text += f"Removed chapters: {', '.join(chapter_names)}\n"

        if changes['modified']:
            modified_details = []
            for ch in changes['modified'][:5]:
                delta = ch['word_delta']
                delta_str = f"+{delta}" if delta > 0 else str(delta)
                modified_details.append(f'"{ch["title"]}" ({delta_str} words)')
            changes_text += f"Edited chapters: {', '.join(modified_details)}\n"

        prompt = f"Summarize these manuscript changes:\n\n{changes_text}"

        service = OpenRouterService(api_key)
        result = await service.get_writing_suggestion(
            text=prompt,
            context=context,
            suggestion_type="general",
            max_tokens=150,
            temperature=0.6
        )

        if result.get("success") and result.get("suggestion"):
            return result["suggestion"].strip()

        return None

    def create_variant_branch(
        self,
        manuscript_id: str,
        scene_id: str,
        variant_label: str,
        base_snapshot_id: Optional[str] = None
    ) -> str:
        """
        Create a Git branch for a scene variant (multiverse)

        Args:
            manuscript_id: ID of the manuscript
            scene_id: ID of the scene
            variant_label: Label for the variant
            base_snapshot_id: Optional snapshot to branch from (defaults to HEAD)

        Returns:
            Branch name created
        """
        repo = self.init_repository(manuscript_id)

        # Create branch name
        branch_name = f"variant/{scene_id}/{variant_label.replace(' ', '-')}"

        # Get base commit
        if base_snapshot_id:
            db = SessionLocal()
            try:
                snapshot = db.query(Snapshot).filter(
                    Snapshot.id == base_snapshot_id
                ).first()
                if snapshot:
                    base_commit = repo.get(snapshot.commit_hash)
                else:
                    base_commit = repo.head.peel()
            finally:
                db.close()
        else:
            base_commit = repo.head.peel()

        # Create branch
        repo.branches.local.create(branch_name, base_commit)

        return branch_name

    def merge_variant(
        self,
        manuscript_id: str,
        variant_branch: str
    ) -> bool:
        """
        Merge a variant branch back to main

        Args:
            manuscript_id: ID of the manuscript
            variant_branch: Name of the variant branch

        Returns:
            True if merge successful, False otherwise
        """
        repo = self.init_repository(manuscript_id)

        try:
            # Get branch reference
            branch = repo.branches.get(variant_branch)
            if not branch:
                raise ValueError(f"Branch {variant_branch} not found")

            # Merge into HEAD
            repo.merge(branch.target)

            # Check for conflicts
            if repo.index.conflicts:
                # Has conflicts - abort merge
                repo.state_cleanup()
                return False

            # Create merge commit
            tree_id = repo.index.write_tree()
            tree = repo.get(tree_id)

            parents = [repo.head.target, branch.target]

            repo.create_commit(
                "HEAD",
                self.signature,
                self.signature,
                f"Merge variant: {variant_branch}",
                tree,
                parents
            )

            # Cleanup
            repo.state_cleanup()

            return True

        except Exception as e:
            # Cleanup on error
            repo.state_cleanup()
            raise e

    def delete_snapshot(self, snapshot_id: str):
        """Delete a snapshot from database (Git commit remains)"""
        db = SessionLocal()
        try:
            snapshot = db.query(Snapshot).filter(
                Snapshot.id == snapshot_id
            ).first()

            if snapshot:
                db.delete(snapshot)
                db.commit()
        finally:
            db.close()


# Global instance
version_service = VersionService()
