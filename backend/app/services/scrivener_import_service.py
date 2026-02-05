"""
Scrivener project import service.

Handles parsing of .scriv project folders (Scrivener 3) and conversion to Maxwell format.
Supports importing:
- Draft/Manuscript folder as chapters
- Character sheets as Codex entities
- Location documents as Codex entities
- Research folder as notes (optional)
"""

import os
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import tempfile
import shutil
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScrivenerDocument:
    """Represents a document in the Scrivener binder"""
    uuid: str
    title: str
    doc_type: str  # "Text", "Folder", "Research", "Character", "Location"
    parent_uuid: Optional[str] = None
    children: List[str] = field(default_factory=list)
    synopsis: Optional[str] = None
    content_rtf: Optional[str] = None
    content_plain: Optional[str] = None
    order: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Scrivener status and label
    status: Optional[str] = None
    label: Optional[str] = None
    # Word count targets
    target_word_count: Optional[int] = None


@dataclass
class ScrivenerProject:
    """Parsed Scrivener project structure"""
    title: str
    author: Optional[str] = None
    draft_folder_uuid: Optional[str] = None
    research_folder_uuid: Optional[str] = None
    characters_folder_uuid: Optional[str] = None
    locations_folder_uuid: Optional[str] = None
    notes_folder_uuid: Optional[str] = None
    trash_folder_uuid: Optional[str] = None
    documents: Dict[str, ScrivenerDocument] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)


class ScrivenerImportService:
    """
    Service for importing Scrivener projects into Maxwell.

    Supports:
    - Scrivener 3 format (.scriv folders)
    - Zipped .scriv projects
    - RTF and plain text content extraction
    """

    def __init__(self):
        self.temp_dir = None

    async def parse_scrivener_project(
        self,
        file_path: str,
        is_zip: bool = True
    ) -> ScrivenerProject:
        """
        Parse Scrivener project from .zip or extracted folder.

        Args:
            file_path: Path to .zip file or .scriv folder
            is_zip: If True, extract from zip first

        Returns:
            ScrivenerProject with all documents parsed
        """
        if is_zip:
            # Extract to temp directory
            self.temp_dir = tempfile.mkdtemp()
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(self.temp_dir)
            except zipfile.BadZipFile:
                raise ValueError("Invalid zip file - file may be corrupted")

            # Find .scriv folder
            scriv_path = self._find_scriv_folder(self.temp_dir)
            if not scriv_path:
                raise ValueError("No .scriv folder found in zip file")
        else:
            scriv_path = file_path

        try:
            # Parse the project
            project = self._parse_scrivx(scriv_path)

            # Extract content for each document
            await self._extract_all_content(project, scriv_path)

            return project
        finally:
            # Cleanup temp directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None

    def _find_scriv_folder(self, base_path: str) -> Optional[str]:
        """Find .scriv folder in extracted zip"""
        for root, dirs, files in os.walk(base_path):
            # Check for .scriv directories
            for d in dirs:
                if d.endswith('.scriv'):
                    return os.path.join(root, d)

            # Also check if we're already inside the scriv folder
            # (has Files directory and a .scrivx file)
            if 'Files' in dirs and any(f.endswith('.scrivx') for f in files):
                return root

        return None

    def _parse_scrivx(self, scriv_path: str) -> ScrivenerProject:
        """
        Parse the .scrivx XML manifest file.

        This is the main index file for Scrivener projects.
        """
        # Find .scrivx file
        scrivx_file = None
        for f in os.listdir(scriv_path):
            if f.endswith('.scrivx'):
                scrivx_file = os.path.join(scriv_path, f)
                break

        if not scrivx_file:
            raise ValueError("No .scrivx file found in project folder")

        tree = ET.parse(scrivx_file)
        root = tree.getroot()

        # Get project title from filename or Title attribute
        title = root.get('Title')
        if not title:
            # Use the scrivx filename without extension
            title = os.path.splitext(os.path.basename(scrivx_file))[0]

        project = ScrivenerProject(title=title)

        # Parse project settings
        project_settings = root.find('.//ProjectProperties')
        if project_settings is not None:
            project.author = project_settings.get('Author', '')
            project.settings = {
                'author': project.author,
            }

        # Parse binder items
        binder = root.find('.//Binder')
        if binder is not None:
            self._parse_binder_items(binder, project, None)

        # Identify special folders (Draft, Research, Characters, etc.)
        self._identify_special_folders(project)

        return project

    def _parse_binder_items(
        self,
        parent_element: ET.Element,
        project: ScrivenerProject,
        parent_uuid: Optional[str]
    ):
        """Recursively parse binder items from XML"""
        for idx, item in enumerate(parent_element.findall('./BinderItem')):
            uuid = item.get('UUID')
            if not uuid:
                continue

            # Get title
            title_elem = item.find('Title')
            title_text = title_elem.text if title_elem is not None and title_elem.text else 'Untitled'

            # Get document type
            doc_type = item.get('Type', 'Text')

            # Create document
            doc = ScrivenerDocument(
                uuid=uuid,
                title=title_text,
                doc_type=doc_type,
                parent_uuid=parent_uuid,
                order=idx
            )

            # Parse metadata
            metadata = item.find('MetaData')
            if metadata is not None:
                status_elem = metadata.find('Status')
                if status_elem is not None and status_elem.text:
                    doc.status = status_elem.text

                label_elem = metadata.find('Label')
                if label_elem is not None and label_elem.text:
                    doc.label = label_elem.text

            # Parse target word count
            target_elem = item.find('.//Target')
            if target_elem is not None:
                count = target_elem.get('Count')
                if count:
                    try:
                        doc.target_word_count = int(count)
                    except ValueError:
                        pass

            # Parse children
            children_elem = item.find('Children')
            if children_elem is not None:
                for child in children_elem.findall('BinderItem'):
                    child_uuid = child.get('UUID')
                    if child_uuid:
                        doc.children.append(child_uuid)
                self._parse_binder_items(children_elem, project, uuid)

            project.documents[uuid] = doc

    def _identify_special_folders(self, project: ScrivenerProject):
        """
        Identify special folders based on Type attribute or title patterns.

        Scrivener uses special Type values for system folders:
        - DraftFolder: The main manuscript folder
        - TrashFolder: Deleted items
        - ResearchFolder: Research materials
        """
        for uuid, doc in project.documents.items():
            doc_type = doc.doc_type.lower()
            title_lower = doc.title.lower()

            # Check by Type attribute first (most reliable)
            if doc_type == 'draftfolder':
                project.draft_folder_uuid = uuid
            elif doc_type == 'trashfolder':
                project.trash_folder_uuid = uuid
            elif doc_type == 'researchfolder':
                project.research_folder_uuid = uuid
            # Then check by title patterns (for custom folders)
            elif doc.doc_type in ['Folder', 'Root']:
                if any(name in title_lower for name in ['draft', 'manuscript', 'novel', 'book']):
                    if not project.draft_folder_uuid:
                        project.draft_folder_uuid = uuid
                elif 'research' in title_lower:
                    if not project.research_folder_uuid:
                        project.research_folder_uuid = uuid
                elif any(name in title_lower for name in ['character', 'people', 'cast']):
                    project.characters_folder_uuid = uuid
                elif any(name in title_lower for name in ['location', 'place', 'setting', 'world']):
                    project.locations_folder_uuid = uuid
                elif any(name in title_lower for name in ['note', 'idea', 'scratch']):
                    project.notes_folder_uuid = uuid

    async def _extract_all_content(
        self,
        project: ScrivenerProject,
        scriv_path: str
    ):
        """Extract content for all documents from Files/Data directory"""
        # Scrivener 3 stores content in Files/Data/{UUID}/
        files_path = os.path.join(scriv_path, 'Files', 'Data')

        if not os.path.exists(files_path):
            # Try Scrivener 2 path
            files_path = os.path.join(scriv_path, 'Files', 'Docs')

        if not os.path.exists(files_path):
            logger.warning(f"Could not find content directory in {scriv_path}")
            return

        for uuid, doc in project.documents.items():
            # Skip folders
            if doc.doc_type in ['Folder', 'DraftFolder', 'ResearchFolder', 'TrashFolder', 'Root']:
                continue

            doc_path = os.path.join(files_path, uuid)
            if not os.path.exists(doc_path):
                continue

            # Try to read RTF content (Scrivener 3 default)
            rtf_path = os.path.join(doc_path, 'content.rtf')
            if os.path.exists(rtf_path):
                try:
                    with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as f:
                        doc.content_rtf = f.read()
                    # Convert to plain text
                    doc.content_plain = self._rtf_to_text(doc.content_rtf)
                except Exception as e:
                    logger.error(f"Error reading RTF for {uuid}: {e}")

            # Try plain text fallback
            if not doc.content_plain:
                txt_path = os.path.join(doc_path, 'content.txt')
                if os.path.exists(txt_path):
                    try:
                        with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                            doc.content_plain = f.read()
                    except Exception as e:
                        logger.error(f"Error reading text for {uuid}: {e}")

            # Try to read synopsis
            synopsis_path = os.path.join(doc_path, 'synopsis.txt')
            if os.path.exists(synopsis_path):
                try:
                    with open(synopsis_path, 'r', encoding='utf-8', errors='ignore') as f:
                        doc.synopsis = f.read().strip()
                except Exception as e:
                    logger.error(f"Error reading synopsis for {uuid}: {e}")

    def _rtf_to_text(self, rtf_content: str) -> str:
        """
        Convert RTF content to plain text.

        Uses striprtf if available, otherwise falls back to basic regex stripping.
        """
        try:
            # Try using striprtf library
            from striprtf.striprtf import rtf_to_text
            return rtf_to_text(rtf_content)
        except ImportError:
            # Fallback: basic RTF stripping
            logger.warning("striprtf not installed, using basic RTF conversion")
            return self._basic_rtf_strip(rtf_content)
        except Exception as e:
            logger.error(f"RTF conversion error: {e}")
            return self._basic_rtf_strip(rtf_content)

    def _basic_rtf_strip(self, rtf: str) -> str:
        """Basic RTF to text conversion using regex"""
        # Remove RTF control words
        text = re.sub(r'\\[a-z]+\d*\s?', '', rtf)
        # Remove braces
        text = re.sub(r'[{}]', '', text)
        # Remove escaped characters
        text = text.replace('\\\\', '\\')
        text = text.replace('\\{', '{')
        text = text.replace('\\}', '}')
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def convert_to_maxwell(
        self,
        project: ScrivenerProject,
        import_research: bool = False,
        import_characters: bool = True,
        import_locations: bool = True
    ) -> Dict[str, Any]:
        """
        Convert parsed Scrivener project to Maxwell format.

        Args:
            project: Parsed ScrivenerProject
            import_research: Import research folder as notes
            import_characters: Import character sheets as entities
            import_locations: Import locations as entities

        Returns:
            Dictionary with:
            - title: str
            - author: Optional[str]
            - chapters: List[dict] - For Manuscript chapters
            - entities: List[dict] - For Codex entities
        """
        result = {
            "title": project.title,
            "author": project.author,
            "chapters": [],
            "entities": [],
            "import_stats": {
                "documents_found": len(project.documents),
                "draft_documents": 0,
                "character_documents": 0,
                "location_documents": 0,
                "research_documents": 0,
            }
        }

        # Convert draft folder to chapters
        if project.draft_folder_uuid:
            draft_chapters = []
            self._convert_folder_to_chapters(
                project,
                project.draft_folder_uuid,
                draft_chapters,
                parent_id=None
            )
            result["chapters"].extend(draft_chapters)
            result["import_stats"]["draft_documents"] = self._count_documents(draft_chapters)

        # Convert character documents to entities
        if import_characters and project.characters_folder_uuid:
            char_entities = []
            self._convert_to_entities(
                project,
                project.characters_folder_uuid,
                char_entities,
                "CHARACTER"
            )
            result["entities"].extend(char_entities)
            result["import_stats"]["character_documents"] = len(char_entities)

        # Convert location documents to entities
        if import_locations and project.locations_folder_uuid:
            loc_entities = []
            self._convert_to_entities(
                project,
                project.locations_folder_uuid,
                loc_entities,
                "LOCATION"
            )
            result["entities"].extend(loc_entities)
            result["import_stats"]["location_documents"] = len(loc_entities)

        # Optionally convert research to notes
        if import_research and project.research_folder_uuid:
            research_chapters = []
            self._convert_folder_to_chapters(
                project,
                project.research_folder_uuid,
                research_chapters,
                parent_id=None,
                doc_type="NOTES"
            )
            result["chapters"].extend(research_chapters)
            result["import_stats"]["research_documents"] = self._count_documents(research_chapters)

        return result

    def _count_documents(self, chapters: List[dict]) -> int:
        """Recursively count documents in chapter list"""
        count = 0
        for ch in chapters:
            if ch.get("document_type") != "FOLDER":
                count += 1
            if ch.get("children"):
                count += self._count_documents(ch["children"])
        return count

    def _convert_folder_to_chapters(
        self,
        project: ScrivenerProject,
        folder_uuid: str,
        chapters: List[dict],
        parent_id: Optional[str],
        doc_type: str = "CHAPTER"
    ):
        """Recursively convert folder contents to Maxwell chapters"""
        folder = project.documents.get(folder_uuid)
        if not folder:
            return

        for child_uuid in folder.children:
            child = project.documents.get(child_uuid)
            if not child:
                continue

            # Skip trash
            if child.doc_type == 'TrashFolder':
                continue

            if child.doc_type in ['Folder', 'DraftFolder', 'ResearchFolder', 'Root']:
                # Create folder in Maxwell
                folder_data = {
                    "title": child.title,
                    "content": "",
                    "document_type": "FOLDER",
                    "order": child.order,
                    "synopsis": child.synopsis,
                    "metadata": {
                        "scrivener_uuid": child.uuid,
                        "scrivener_status": child.status,
                        "scrivener_label": child.label,
                    },
                    "children": []
                }
                chapters.append(folder_data)

                # Recurse into folder
                self._convert_folder_to_chapters(
                    project,
                    child_uuid,
                    folder_data["children"],
                    child_uuid,
                    doc_type
                )
            else:
                # Create chapter/document
                content = child.content_plain or ""

                chapters.append({
                    "title": child.title,
                    "content": content,
                    "synopsis": child.synopsis,
                    "document_type": doc_type,
                    "order": child.order,
                    "word_count": len(content.split()) if content else 0,
                    "target_word_count": child.target_word_count,
                    "metadata": {
                        "scrivener_uuid": child.uuid,
                        "scrivener_status": child.status,
                        "scrivener_label": child.label,
                    }
                })

    def _convert_to_entities(
        self,
        project: ScrivenerProject,
        folder_uuid: str,
        entities: List[dict],
        entity_type: str
    ):
        """Convert folder contents to Codex entities"""
        folder = project.documents.get(folder_uuid)
        if not folder:
            return

        for child_uuid in folder.children:
            child = project.documents.get(child_uuid)
            if not child:
                continue

            if child.doc_type not in ['Folder', 'DraftFolder', 'ResearchFolder', 'Root']:
                # Convert to entity
                description = child.synopsis or ""
                content = child.content_plain or ""

                # If no synopsis, try to extract first paragraph as description
                if not description and content:
                    paragraphs = content.split('\n\n')
                    if paragraphs:
                        description = paragraphs[0][:500]  # First 500 chars

                entities.append({
                    "name": child.title,
                    "type": entity_type,
                    "description": description,
                    "notes": content,
                    "metadata": {
                        "scrivener_uuid": child.uuid,
                        "scrivener_status": child.status,
                        "scrivener_label": child.label,
                        "imported_from": "scrivener"
                    }
                })
            else:
                # Recurse into subfolders (e.g., "Main Characters", "Side Characters")
                self._convert_to_entities(project, child_uuid, entities, entity_type)

    def get_preview(self, project: ScrivenerProject) -> Dict[str, Any]:
        """
        Get a preview of what will be imported.

        Returns summary without actually doing the conversion.
        """
        preview = {
            "title": project.title,
            "author": project.author,
            "draft": {
                "found": project.draft_folder_uuid is not None,
                "documents": 0,
                "word_count": 0
            },
            "characters": {
                "found": project.characters_folder_uuid is not None,
                "count": 0
            },
            "locations": {
                "found": project.locations_folder_uuid is not None,
                "count": 0
            },
            "research": {
                "found": project.research_folder_uuid is not None,
                "count": 0
            }
        }

        # Count draft documents
        if project.draft_folder_uuid:
            preview["draft"]["documents"], preview["draft"]["word_count"] = \
                self._count_folder_contents(project, project.draft_folder_uuid)

        # Count character documents
        if project.characters_folder_uuid:
            preview["characters"]["count"], _ = \
                self._count_folder_contents(project, project.characters_folder_uuid)

        # Count location documents
        if project.locations_folder_uuid:
            preview["locations"]["count"], _ = \
                self._count_folder_contents(project, project.locations_folder_uuid)

        # Count research documents
        if project.research_folder_uuid:
            preview["research"]["count"], _ = \
                self._count_folder_contents(project, project.research_folder_uuid)

        return preview

    def _count_folder_contents(
        self,
        project: ScrivenerProject,
        folder_uuid: str
    ) -> Tuple[int, int]:
        """
        Count documents and words in a folder recursively.

        Returns: (document_count, word_count)
        """
        folder = project.documents.get(folder_uuid)
        if not folder:
            return 0, 0

        doc_count = 0
        word_count = 0

        for child_uuid in folder.children:
            child = project.documents.get(child_uuid)
            if not child:
                continue

            if child.doc_type in ['Folder', 'DraftFolder', 'ResearchFolder', 'Root']:
                sub_docs, sub_words = self._count_folder_contents(project, child_uuid)
                doc_count += sub_docs
                word_count += sub_words
            else:
                doc_count += 1
                if child.content_plain:
                    word_count += len(child.content_plain.split())

        return doc_count, word_count


# Singleton instance
scrivener_import_service = ScrivenerImportService()
