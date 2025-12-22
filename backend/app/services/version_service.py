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
        content: str,
        trigger_type: str,
        label: str = "",
        description: str = "",
        word_count: int = 0
    ) -> Snapshot:
        """
        Create a snapshot (Git commit) of the manuscript

        Args:
            manuscript_id: ID of the manuscript
            content: Current manuscript content (Lexical JSON string)
            trigger_type: MANUAL, AUTO, CHAPTER_COMPLETE, PRE_GENERATION, SESSION_END
            label: Optional user-provided label
            description: Optional description
            word_count: Word count at time of snapshot

        Returns:
            Snapshot model instance
        """
        repo = self.init_repository(manuscript_id)
        repo_path = self.get_repo_path(manuscript_id)

        # Write content to file (Lexical JSON state)
        content_path = repo_path / "manuscript.json"
        content_path.write_text(content, encoding="utf-8")

        # Extract and write plain text version for readable diffs
        plain_text = self._extract_text_from_lexical_json(content)
        text_path = repo_path / "manuscript.txt"
        text_path.write_text(plain_text, encoding="utf-8")

        # Write metadata
        metadata = {
            "manuscript_id": manuscript_id,
            "trigger_type": trigger_type,
            "label": label,
            "description": description,
            "word_count": word_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        metadata_path = repo_path / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        # Stage files
        index = repo.index
        index.read()
        index.add("manuscript.json")
        index.add("manuscript.txt")
        index.add("metadata.json")
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
            snapshot = Snapshot(
                manuscript_id=manuscript_id,
                commit_hash=str(commit_id),
                label=label,
                description=description,
                trigger_type=trigger_type,
                word_count=word_count
            )
            db.add(snapshot)
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
    ) -> str:
        """
        Restore manuscript to a specific snapshot

        Args:
            manuscript_id: ID of the manuscript
            snapshot_id: ID of the snapshot to restore
            create_backup: Whether to create a backup snapshot first

        Returns:
            Content of the restored snapshot
        """
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
                content_path = repo_path / "manuscript.json"
                if content_path.exists():
                    current_content = content_path.read_text(encoding="utf-8")
                    self.create_snapshot(
                        manuscript_id=manuscript_id,
                        content=current_content,
                        trigger_type="AUTO",
                        label="Pre-restore backup",
                        description=f"Automatic backup before restoring to {snapshot.label or snapshot.commit_hash[:8]}"
                    )

            # Checkout the commit
            commit = repo.get(snapshot.commit_hash)
            repo.checkout_tree(commit.tree)

            # Read restored content
            content_path = repo_path / "manuscript.json"
            if content_path.exists():
                return content_path.read_text(encoding="utf-8")
            else:
                raise ValueError("manuscript.json not found in snapshot")

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
