2sa# Codex IDE: Implementation Plan

## Table of Contents
1. [Project Setup](#project-setup)
2. [Epic 1: Living Manuscript](#epic-1-living-manuscript)
3. [Epic 2: The Codex](#epic-2-the-codex)
4. [Epic 3: The Muse](#epic-3-the-muse)
5. [Epic 4: Structural Analysis](#epic-4-structural-analysis)
6. [Testing & Quality Assurance](#testing--quality-assurance)
7. [Deployment & Distribution](#deployment--distribution)
8. [Task Estimation](#task-estimation)

---

## Project Setup

### Setup-1: Initialize Project Structure
**Priority**: Critical | **Estimated Effort**: 1 day

#### Tasks:
1. **Create monorepo structure**
   ```bash
   mkdir -p codex-ide/{frontend,backend,docs,scripts}
   ```

2. **Initialize frontend (React + TypeScript)**
   ```bash
   cd frontend
   npm create vite@latest . -- --template react-ts
   npm install
   ```
   - Install dependencies:
     - `@lexical/react @lexical/headless`
     - `@tanstack/react-query zustand`
     - `tailwindcss @shadcn/ui`
     - `react-force-graph`
   - Configure Tailwind CSS
   - Set up Shadcn/UI components

3. **Initialize backend (Python + FastAPI)**
   ```bash
   cd backend
   python -m venv venv
   ```
   - Create `requirements.txt`:
     ```
     fastapi==0.104.1
     uvicorn[standard]==0.24.0
     sqlalchemy==2.0.23
     pydantic==2.5.0
     spacy==3.7.2
     chromadb==0.4.18
     kuzu==0.1.0
     pygit2==1.13.3
     python-multipart==0.0.6
     ```
   - Create project structure:
     ```python
     app/
     ├── __init__.py
     ├── main.py
     ├── api/
     ├── services/
     ├── models/
     └── repositories/
     ```

4. **Set up development environment**
   - Create `.env.example` for API keys
   - Configure VS Code workspace settings
   - Set up ESLint + Prettier (frontend)
   - Set up Black + Ruff (backend)
   - Initialize Git repository

5. **Create Docker development environment**
   ```yaml
   # docker-compose.yml
   version: '3.8'
   services:
     backend:
       build: ./backend
       ports: ["8000:8000"]
       volumes: ["./backend:/app"]
     frontend:
       build: ./frontend
       ports: ["5173:5173"]
       volumes: ["./frontend:/app"]
   ```

**Acceptance Criteria**:
- `npm run dev` starts frontend on port 5173
- `uvicorn app.main:app --reload` starts backend on port 8000
- Both services communicate successfully
- Git repository initialized with `.gitignore`

---

### Setup-2: Database Setup
**Priority**: Critical | **Estimated Effort**: 0.5 days

#### Tasks:
1. **Initialize SQLite database**
   - Create `backend/app/database.py` with SQLAlchemy engine
   - Set up Alembic for migrations:
     ```bash
     alembic init migrations
     ```
   - Create initial migration with base tables

2. **Set up ChromaDB**
   ```python
   import chromadb
   client = chromadb.PersistentClient(path="./data/chroma")
   scenes_collection = client.create_collection("scene_embeddings")
   entities_collection = client.create_collection("entity_embeddings")
   ```

3. **Set up KuzuDB**
   ```python
   import kuzu
   db = kuzu.Database("./data/graph")
   conn = kuzu.Connection(db)
   # Create schema (see ARCHITECTURE.md)
   ```

4. **Create database initialization script**
   ```bash
   python scripts/init_db.py
   ```

**Acceptance Criteria**:
- SQLite database created at `./data/codex.db`
- ChromaDB collections initialized
- KuzuDB graph schema created
- Migration system functional

---

### Setup-3: Configure Git-Based Versioning
**Priority**: High | **Estimated Effort**: 1 day

#### Tasks:
1. **Create `.codex/` repository structure**
   ```python
   import pygit2

   def init_manuscript_repo(manuscript_id: str):
       repo_path = f"./data/manuscripts/{manuscript_id}/.codex"
       pygit2.init_repository(repo_path)
       return repo_path
   ```

2. **Implement version service foundation**
   - `backend/app/services/version_service.py`
   - Methods:
     - `create_snapshot(manuscript_id, label, trigger_type)`
     - `get_history(manuscript_id)`
     - `restore_snapshot(snapshot_id)`
     - `create_branch(scene_id, variant_label)`

3. **Test Git operations**
   - Unit tests for snapshot creation
   - Test restore functionality
   - Verify file permissions

**Acceptance Criteria**:
- Can create Git commits programmatically
- Can retrieve commit history
- Can checkout previous commits
- Metadata stored in `snapshots` table

---

## Epic 1: Living Manuscript

### Epic 1.1: Implement Lexical Editor Wrapper
**Priority**: Critical | **Estimated Effort**: 3 days

#### Task 1.1.1: Create Base Editor Component
**Effort**: 1 day

1. **Create `ManuscriptEditor.tsx`**
   ```typescript
   import { LexicalComposer } from '@lexical/react/LexicalComposer';
   import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
   import { ContentEditable } from '@lexical/react/LexicalContentEditable';

   export function ManuscriptEditor() {
     const initialConfig = {
       namespace: 'CodexEditor',
       theme: editorTheme,
       onError: (error) => console.error(error),
       nodes: [
         // Custom nodes will be added here
       ]
     };

     return (
       <LexicalComposer initialConfig={initialConfig}>
         <RichTextPlugin
           contentEditable={<ContentEditable />}
           placeholder={<div>Start writing...</div>}
         />
       </LexicalComposer>
     );
   }
   ```

2. **Implement basic toolbar**
   - Bold, italic, underline buttons
   - Heading levels (H1, H2, H3)
   - Quote, list formatting

3. **Add keyboard shortcuts**
   - Ctrl+B for bold
   - Ctrl+I for italic
   - Ctrl+S for save (intercept)

**Acceptance Criteria**:
- Editor renders and accepts text input
- Basic formatting works
- Lexical state can be serialized to JSON

---

#### Task 1.1.2: Implement Custom Lexical Nodes
**Effort**: 1.5 days

1. **Create `SceneBreakNode`**
   ```typescript
   import { DecoratorNode } from 'lexical';

   export class SceneBreakNode extends DecoratorNode<JSX.Element> {
     static getType(): string {
       return 'scene-break';
     }

     createDOM(config: EditorConfig): HTMLElement {
       const div = document.createElement('div');
       div.className = 'scene-break';
       return div;
     }

     decorate(): JSX.Element {
       return <SceneBreakComponent nodeKey={this.getKey()} />;
     }
   }
   ```

2. **Create `EntityMentionNode`**
   - Detect entity names from Codex
   - Make clickable/hoverable
   - Show mini-card on hover with entity details

3. **Create `DialogueNode`** (optional enhancement)
   - Auto-detect dialogue (text in quotes)
   - Apply special styling
   - Track speaker attribution

**Acceptance Criteria**:
- Scene breaks render as visual dividers
- Entity mentions are clickable
- Hover shows entity preview card
- Custom nodes serialize/deserialize correctly

---

#### Task 1.1.3: Implement Editor Modes
**Effort**: 0.5 days

1. **Focus Mode**
   ```typescript
   const [isFocusMode, setIsFocusMode] = useState(false);

   // Hide sidebar, toolbar when active
   // Keyboard shortcut: F11 or Ctrl+Shift+F
   ```

2. **Architect Mode**
   - Show metadata sidebar
   - Display inline scene beats
   - Show word count per scene

**Acceptance Criteria**:
- Toggle between modes with keyboard shortcut
- UI adapts appropriately
- State persists in user preferences

---

### Epic 1.2: "Time Machine" Versioning
**Priority**: Critical | **Estimated Effort**: 4 days

#### Task 1.2.1: Implement Auto-Save Strategy
**Effort**: 1 day

1. **Create `AutoSavePlugin.tsx`**
   ```typescript
   import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
   import { debounce } from 'lodash';

   export function AutoSavePlugin() {
     const [editor] = useLexicalComposerContext();

     useEffect(() => {
       const saveContent = debounce(() => {
         const editorState = editor.getEditorState();
         const json = editorState.toJSON();
         // Send to backend
         saveManuscript(json);
       }, 5000); // 5 second debounce

       return editor.registerUpdateListener(({ editorState }) => {
         saveContent();
       });
     }, [editor]);

     return null;
   }
   ```

2. **Implement backend save endpoint**
   ```python
   @router.put("/api/manuscripts/{manuscript_id}")
   async def save_manuscript(
       manuscript_id: str,
       content: dict,
       db: Session = Depends(get_db)
   ):
       # Save to SQLite
       manuscript = db.query(Manuscript).filter_by(id=manuscript_id).first()
       manuscript.lexical_state = json.dumps(content)
       manuscript.updated_at = datetime.utcnow()
       db.commit()

       return {"success": True}
   ```

3. **Trigger snapshot creation on**:
   - Session close (window.onbeforeunload)
   - Chapter completion (detect heading node)
   - Manual save (Ctrl+Shift+S)
   - Pre-generation (before AI writes)

**Acceptance Criteria**:
- Content saves 5 seconds after typing stops
- No data loss on browser crash
- Snapshots created at appropriate times
- Loading indicator shows save status

---

#### Task 1.2.2: Build History Slider UI
**Effort**: 2 days

1. **Create `HistorySlider.tsx`**
   ```typescript
   export function HistorySlider({ manuscriptId }: Props) {
     const { data: snapshots } = useQuery({
       queryKey: ['history', manuscriptId],
       queryFn: () => fetchHistory(manuscriptId)
     });

     return (
       <div className="history-timeline">
         {snapshots.map(snapshot => (
           <SnapshotCard
             key={snapshot.id}
             snapshot={snapshot}
             onRestore={() => restoreSnapshot(snapshot.id)}
           />
         ))}
       </div>
     );
   }
   ```

2. **Design visual timeline**
   - Vertical timeline with date markers
   - Icons for different trigger types:
     - 💾 Manual save
     - 📝 Chapter completion
     - 🤖 Pre-generation
     - ⏱️ Auto-save
   - Show label/description for each snapshot

3. **Implement snapshot preview**
   - Click snapshot → show modal with metadata
   - Word count at that point
   - Changes since previous snapshot

**Acceptance Criteria**:
- Timeline displays all snapshots chronologically
- Visual icons differentiate snapshot types
- Preview shows accurate historical state

---

#### Task 1.2.3: Implement Diff Viewer
**Effort**: 1 day

1. **Create `DiffViewer.tsx`**
   ```typescript
   import { diffWords } from 'diff';

   export function DiffViewer({ oldText, newText }: Props) {
     const changes = diffWords(oldText, newText);

     return (
       <div className="diff-container">
         {changes.map((part, index) => (
           <span
             key={index}
             className={part.added ? 'bg-green-200' : part.removed ? 'bg-red-200' : ''}
           >
             {part.value}
           </span>
         ))}
       </div>
     );
   }
   ```

2. **Add "Restore this Version" button**
   - Confirm dialog before restoring
   - Creates new snapshot before restore (safety)
   - Shows success message

**Acceptance Criteria**:
- Added text highlighted in green
- Removed text highlighted in red
- Restore function works without data loss
- Confirmation dialog prevents accidents

---

### Epic 1.3: Scoped Branching ("Multiverse")
**Priority**: Medium | **Estimated Effort**: 2 days

#### Task 1.3.1: Implement Variant Manager
**Effort**: 1 day

1. **Create database operations**
   ```python
   # backend/app/services/variant_service.py

   def create_variant(scene_id: str, label: str, content: str):
       variant = Variant(
           id=str(uuid.uuid4()),
           scene_id=scene_id,
           label=label,
           content=content,
           is_main=False
       )
       db.add(variant)
       db.commit()
       return variant

   def get_variants(scene_id: str):
       return db.query(Variant).filter_by(scene_id=scene_id).all()

   def merge_to_main(variant_id: str):
       variant = db.query(Variant).get(variant_id)
       main_scene = db.query(Scene).get(variant.scene_id)
       main_scene.content = variant.content
       variant.is_main = True
       db.commit()
   ```

2. **Create API endpoints**
   ```python
   @router.get("/api/scenes/{scene_id}/variants")
   async def list_variants(scene_id: str):
       variants = get_variants(scene_id)
       return {"data": variants}

   @router.post("/api/scenes/{scene_id}/variants")
   async def create_scene_variant(scene_id: str, label: str, content: str):
       variant = create_variant(scene_id, label, content)
       return {"data": variant}

   @router.put("/api/variants/{variant_id}/merge")
   async def merge_variant(variant_id: str):
       merge_to_main(variant_id)
       return {"success": True}
   ```

**Acceptance Criteria**:
- Can create multiple variants per scene
- Variants stored independently
- Merge operation updates main scene

---

#### Task 1.3.2: Build Variant Switcher UI
**Effort**: 1 day

1. **Create `MultiverseTab.tsx`**
   ```typescript
   export function MultiverseTab({ sceneId }: Props) {
     const { data: variants } = useQuery({
       queryKey: ['variants', sceneId],
       queryFn: () => fetchVariants(sceneId)
     });

     return (
       <div className="variant-tabs">
         <button>Main Draft</button>
         {variants.map(variant => (
           <button key={variant.id}>
             {variant.label}
           </button>
         ))}
         <button onClick={createNewVariant}>+ New Alt</button>
       </div>
     );
   }
   ```

2. **Implement variant creation dialog**
   - Input field for variant label
   - Option to copy from main or start blank
   - Create button

3. **Add "Merge to Main" confirmation**
   - Warning dialog
   - Option to keep variant after merge
   - Create snapshot before merge

**Acceptance Criteria**:
- Tab switcher shows all variants
- Clicking tab loads variant content in editor
- Merge dialog works correctly
- Main draft updates on merge

---

## Epic 2: The Codex

### Epic 2.1: Define Codex Schema
**Priority**: Critical | **Estimated Effort**: 1 day

#### Task 2.1.1: Create TypeScript Types
**Effort**: 0.5 days

```typescript
// frontend/src/types/codex.ts

export enum EntityType {
  CHARACTER = 'CHARACTER',
  LOCATION = 'LOCATION',
  ITEM = 'ITEM',
  LORE = 'LORE'
}

export interface Entity {
  id: string;
  type: EntityType;
  name: string;
  aliases: string[];
  attributes: Record<string, any>;
  appearance_history: AppearanceRecord[];
  image_seed?: number;
  created_at: string;
  updated_at: string;
}

export interface Character extends Entity {
  type: EntityType.CHARACTER;
  attributes: {
    age?: number;
    appearance?: string;
    voice?: string;
    personality?: string;
    backstory?: string;
  };
  relationships: Relationship[];
}

export interface Location extends Entity {
  type: EntityType.LOCATION;
  attributes: {
    description?: string;
    atmosphere?: string;
    geography?: string;
  };
}

export interface Relationship {
  id: string;
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: string;
  strength: number;
  context: SceneContext[];
}

export interface SceneContext {
  scene_id: string;
  description: string;
}

export interface AppearanceRecord {
  scene_id: string;
  description: string;
  timestamp: string;
}
```

---

#### Task 2.1.2: Create Python Pydantic Models
**Effort**: 0.5 days

```python
# backend/app/models/entity.py

from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class EntityType(str, Enum):
    CHARACTER = "CHARACTER"
    LOCATION = "LOCATION"
    ITEM = "ITEM"
    LORE = "LORE"

class AppearanceRecord(BaseModel):
    scene_id: str
    description: str
    timestamp: datetime

class Entity(BaseModel):
    id: str
    type: EntityType
    name: str
    aliases: List[str] = []
    attributes: Dict[str, Any] = {}
    appearance_history: List[AppearanceRecord] = []
    image_seed: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class Character(Entity):
    type: EntityType = EntityType.CHARACTER
    relationships: List[str] = []  # Relationship IDs

class Relationship(BaseModel):
    id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    strength: int = 1
    context: List[Dict[str, str]] = []
```

**Acceptance Criteria**:
- TypeScript types compile without errors
- Pydantic models validate correctly
- API can serialize/deserialize entities
- Types match between frontend/backend

---

### Epic 2.2: The "Digital Archivist"
**Priority**: High | **Estimated Effort**: 5 days

#### Task 2.2.1: Set Up spaCy NLP Pipeline
**Effort**: 1 day

1. **Install and configure spaCy**
   ```bash
   python -m spacy download en_core_web_lg
   ```

2. **Create NLP service**
   ```python
   # backend/app/services/nlp_service.py

   import spacy
   from typing import List, Tuple

   nlp = spacy.load("en_core_web_lg")

   def extract_entities(text: str) -> List[Tuple[str, str]]:
       """Extract named entities from text"""
       doc = nlp(text)
       entities = []

       for ent in doc.ents:
           if ent.label_ in ["PERSON", "GPE", "LOC", "ORG", "FAC"]:
               entities.append((ent.text, ent.label_))

       return entities

   def extract_proper_nouns(text: str) -> List[str]:
       """Extract proper nouns using POS tagging"""
       doc = nlp(text)
       return [token.text for token in doc if token.pos_ == "PROPN"]
   ```

3. **Add neuralcoref for pronoun resolution**
   ```python
   import neuralcoref

   # Add to spaCy pipeline
   neuralcoref.add_to_pipe(nlp)

   def resolve_coreferences(text: str) -> str:
       """Resolve pronouns to their referents"""
       doc = nlp(text)
       return doc._.coref_resolved
   ```

4. **Create unit tests**
   ```python
   def test_extract_entities():
       text = "John walked into the Castle of Doom."
       entities = extract_entities(text)
       assert ("John", "PERSON") in entities
       assert any("Castle" in e[0] for e in entities)
   ```

**Acceptance Criteria**:
- spaCy pipeline loads successfully
- Entity extraction works on sample texts
- Pronoun resolution functional
- Unit tests pass

---

#### Task 2.2.2: Implement Asynchronous Entity Detection
**Effort**: 2 days

1. **Create background task system**
   ```python
   # backend/app/services/analysis_worker.py

   from fastapi import BackgroundTasks
   from app.services.nlp_service import extract_entities
   from app.services.codex_service import suggest_new_entity

   async def analyze_manuscript_async(
       manuscript_id: str,
       text: str,
       background_tasks: BackgroundTasks
   ):
       background_tasks.add_task(
           process_text_for_entities,
           manuscript_id,
           text
       )

   def process_text_for_entities(manuscript_id: str, text: str):
       # Extract entities
       entities = extract_entities(text)

       # Compare with existing Codex
       for entity_text, entity_type in entities:
           if not entity_exists(entity_text, manuscript_id):
               # Add to suggestions queue
               suggest_new_entity(
                   manuscript_id=manuscript_id,
                   name=entity_text,
                   type=map_spacy_to_entity_type(entity_type),
                   context=extract_context(text, entity_text)
               )
   ```

2. **Create suggestions queue table**
   ```python
   class EntitySuggestion(Base):
       __tablename__ = "entity_suggestions"

       id = Column(String, primary_key=True)
       manuscript_id = Column(String, ForeignKey("manuscripts.id"))
       name = Column(String)
       type = Column(String)
       context = Column(Text)  # JSON
       status = Column(String, default="PENDING")  # PENDING, APPROVED, REJECTED
       created_at = Column(DateTime, default=datetime.utcnow)
   ```

3. **Create API endpoint**
   ```python
   @router.post("/api/analyze/extract-entities")
   async def trigger_entity_extraction(
       manuscript_id: str,
       text: str,
       background_tasks: BackgroundTasks
   ):
       await analyze_manuscript_async(manuscript_id, text, background_tasks)
       return {"message": "Analysis started"}
   ```

4. **Add frontend polling/WebSocket**
   ```typescript
   // Option 1: Polling
   const { data } = useQuery({
     queryKey: ['suggestions', manuscriptId],
     queryFn: fetchSuggestions,
     refetchInterval: 10000 // Poll every 10 seconds
   });

   // Option 2: WebSocket (preferred)
   useEffect(() => {
     const ws = new WebSocket('ws://localhost:8000/ws/analysis');
     ws.onmessage = (event) => {
       const suggestion = JSON.parse(event.data);
       // Add to UI notification
     };
   }, []);
   ```

**Acceptance Criteria**:
- Text analysis triggers asynchronously
- Suggestions appear in queue within 10 seconds
- No blocking on main thread
- WebSocket updates work in real-time

---

#### Task 2.2.3: Build Suggestion Queue UI
**Effort**: 2 days

1. **Create `SuggestionQueue.tsx`**
   ```typescript
   export function SuggestionQueue({ manuscriptId }: Props) {
     const { data: suggestions } = useQuery({
       queryKey: ['suggestions', manuscriptId],
       queryFn: () => fetchSuggestions(manuscriptId)
     });

     const approveMutation = useMutation({
       mutationFn: (id: string) => approveSuggestion(id),
       onSuccess: () => {
         queryClient.invalidateQueries(['suggestions', manuscriptId]);
         queryClient.invalidateQueries(['entities', manuscriptId]);
       }
     });

     return (
       <div className="suggestion-queue">
         <h3>New Intel ({suggestions?.length})</h3>
         {suggestions?.map(suggestion => (
           <SuggestionCard
             key={suggestion.id}
             suggestion={suggestion}
             onApprove={() => approveMutation.mutate(suggestion.id)}
             onReject={() => rejectSuggestion(suggestion.id)}
           />
         ))}
       </div>
     );
   }
   ```

2. **Create `SuggestionCard.tsx`**
   ```typescript
   export function SuggestionCard({ suggestion, onApprove, onReject }: Props) {
     return (
       <div className="suggestion-card">
         <div className="flex items-center justify-between">
           <div>
             <EntityIcon type={suggestion.type} />
             <strong>{suggestion.name}</strong>
             <span className="text-gray-500">{suggestion.type}</span>
           </div>
           <div className="actions">
             <button onClick={onApprove}>✓ Add</button>
             <button onClick={onReject}>✗ Ignore</button>
           </div>
         </div>
         <p className="context">{suggestion.context}</p>
       </div>
     );
   }
   ```

3. **Add notification indicator**
   - Badge on Codex sidebar: "New Intel (3)"
   - Optional: Toast notification when new suggestion arrives
   - Sound notification (user preference)

**Acceptance Criteria**:
- Suggestions display in sidebar
- Approve button creates entity in Codex
- Reject button removes suggestion
- Notification badge shows count

---

### Epic 2.3: Relationship Tracking
**Priority**: Medium | **Estimated Effort**: 4 days

#### Task 2.3.1: Implement Relationship Detection
**Effort**: 2 days

1. **Create relationship extraction logic**
   ```python
   # backend/app/services/relationship_service.py

   import spacy
   from typing import List, Tuple

   # Action verbs that indicate relationships
   RELATIONSHIP_VERBS = {
       "kissed": "ROMANTIC",
       "married": "ROMANTIC",
       "fought": "CONFLICT",
       "killed": "CONFLICT",
       "helped": "ALLIANCE",
       "betrayed": "CONFLICT",
       "met": "ACQUAINTANCE"
   }

   def extract_relationships(text: str, entities: List[str]) -> List[Tuple[str, str, str]]:
       """
       Returns: [(entity1, entity2, relationship_type)]
       """
       doc = nlp(text)
       relationships = []

       # Find sentences with multiple entities
       for sent in doc.sents:
           sent_entities = [e for e in entities if e in sent.text]

           if len(sent_entities) >= 2:
               # Check for relationship verbs
               for token in sent:
                   if token.lemma_ in RELATIONSHIP_VERBS:
                       rel_type = RELATIONSHIP_VERBS[token.lemma_]
                       # Find subject and object
                       subj = [child for child in token.children if child.dep_ == "nsubj"]
                       obj = [child for child in token.children if child.dep_ == "dobj"]

                       if subj and obj:
                           relationships.append((subj[0].text, obj[0].text, rel_type))

       return relationships
   ```

2. **Create relationship storage**
   ```python
   def create_or_update_relationship(
       source_id: str,
       target_id: str,
       rel_type: str,
       scene_id: str,
       description: str
   ):
       # Check if relationship exists
       rel = db.query(Relationship).filter_by(
           source_entity_id=source_id,
           target_entity_id=target_id
       ).first()

       if rel:
           # Update strength and add context
           rel.strength += 1
           context = json.loads(rel.context)
           context.append({"scene_id": scene_id, "description": description})
           rel.context = json.dumps(context)
       else:
           # Create new relationship
           rel = Relationship(
               id=str(uuid.uuid4()),
               source_entity_id=source_id,
               target_entity_id=target_id,
               relationship_type=rel_type,
               strength=1,
               context=json.dumps([{"scene_id": scene_id, "description": description}])
           )
           db.add(rel)

       db.commit()
   ```

**Acceptance Criteria**:
- Relationships detected from text
- Multiple mentions increase strength
- Context stored for each interaction
- Bidirectional relationships tracked

---

#### Task 2.3.2: Build Relationship Graph Visualizer
**Effort**: 2 days

1. **Create `RelationshipGraph.tsx`**
   ```typescript
   import { ForceGraph2D } from 'react-force-graph';

   export function RelationshipGraph({ manuscriptId }: Props) {
     const { data: graphData } = useQuery({
       queryKey: ['codex-graph', manuscriptId],
       queryFn: () => fetchGraphData(manuscriptId)
     });

     // Transform data for react-force-graph
     const nodes = graphData.entities.map(e => ({
       id: e.id,
       name: e.name,
       type: e.type,
       color: getColorByType(e.type)
     }));

     const links = graphData.relationships.map(r => ({
       source: r.source_entity_id,
       target: r.target_entity_id,
       value: r.strength, // Line thickness
       type: r.relationship_type
     }));

     return (
       <ForceGraph2D
         graphData={{ nodes, links }}
         nodeLabel="name"
         nodeAutoColorBy="type"
         linkWidth={link => link.value}
         onNodeClick={handleNodeClick}
         linkDirectionalParticles={2}
       />
     );
   }
   ```

2. **Add interactive features**
   - Click node → Show entity card
   - Hover link → Show relationship type + context
   - Filter by entity type (checkboxes)
   - Search/highlight entity

3. **Add layout options**
   - Force-directed (default)
   - Hierarchical
   - Circular

**Acceptance Criteria**:
- Graph renders all entities and relationships
- Line thickness represents interaction count
- Clicking node shows entity details
- Graph updates when entities change

---

## Epic 3: The Muse (LangChain-Powered Generation)

### Epic 3.1: LangChain Agent Foundation
**Priority**: High | **Estimated Effort**: 4 days

#### Task 3.1.1: Install and Configure LangChain
**Effort**: 0.5 days

1. **Update backend dependencies**
   ```bash
   # backend/requirements.txt
   langchain==0.1.0
   langchain-anthropic==0.1.0
   langchain-community==0.0.13
   langchain-openai==0.0.5
   llama-cpp-python==0.2.0  # For local models
   ```

2. **Configure environment variables**
   ```bash
   # .env
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...
   LOCAL_MODEL_PATH=./models/llama-3-8b-instruct.gguf
   USE_LOCAL_MODEL=true  # Fallback preference
   ```

**Acceptance Criteria**:
- Dependencies installed without conflicts
- API keys loaded from environment
- Local model path configured

---

#### Task 3.1.2: Implement LangChain LLM Wrappers
**Effort**: 1.5 days

1. **Create base LLM factory**
   ```python
   # backend/app/services/llm/llm_factory.py

   from langchain_anthropic import ChatAnthropic
   from langchain_openai import ChatOpenAI
   from langchain_community.llms import LlamaCpp
   from typing import Union

   class LLMFactory:
       """Factory for creating LangChain LLM instances"""

       @staticmethod
       def create_cloud_llm(
           provider: str = "anthropic",
           model: str = None,
           temperature: float = 0.7
       ) -> Union[ChatAnthropic, ChatOpenAI]:
           """Create cloud-based LLM"""
           if provider == "anthropic":
               return ChatAnthropic(
                   model=model or "claude-3-5-sonnet-20241022",
                   temperature=temperature,
                   max_tokens=4096
               )
           elif provider == "openai":
               return ChatOpenAI(
                   model=model or "gpt-4-turbo-preview",
                   temperature=temperature
               )
           else:
               raise ValueError(f"Unknown provider: {provider}")

       @staticmethod
       def create_local_llm(
           model_path: str = None,
           temperature: float = 0.7
       ) -> LlamaCpp:
           """Create local LLM"""
           path = model_path or os.getenv("LOCAL_MODEL_PATH")
           return LlamaCpp(
               model_path=path,
               temperature=temperature,
               n_ctx=4096,
               n_gpu_layers=-1,  # Use GPU if available
               streaming=True,
               verbose=False
           )

       @staticmethod
       def create_smart_llm(user_preference: str = "auto") -> Union[ChatAnthropic, LlamaCpp]:
           """Smart selection based on availability and preferences"""
           if user_preference == "local_only":
               return LLMFactory.create_local_llm()

           if user_preference == "cloud_only":
               return LLMFactory.create_cloud_llm()

           # Auto mode: try cloud, fallback to local
           try:
               if os.getenv("ANTHROPIC_API_KEY"):
                   return LLMFactory.create_cloud_llm()
           except Exception:
               pass

           return LLMFactory.create_local_llm()
   ```

2. **Create streaming response handler**
   ```python
   # backend/app/services/llm/streaming.py

   from typing import AsyncIterator
   import json

   async def stream_llm_response(
       llm_chain,
       prompt: str
   ) -> AsyncIterator[str]:
       """Stream LLM responses as SSE"""
       async for chunk in llm_chain.astream(prompt):
           if isinstance(chunk, dict):
               text = chunk.get("content", chunk.get("text", ""))
           else:
               text = str(chunk)

           yield f"data: {json.dumps({'text': text})}\n\n"
   ```

**Acceptance Criteria**:
- Factory creates Claude, GPT, and local LLMs
- Smart fallback works when API keys missing
- Streaming works for all LLM types

---

#### Task 3.1.3: Build LangChain Tools for Story Context
**Effort**: 2 days

1. **Create Codex retrieval tools**
   ```python
   # backend/app/services/llm/tools.py

   from langchain.tools import Tool
   from langchain.pydantic_v1 import BaseModel, Field

   class EntityLookupInput(BaseModel):
       """Input for entity lookup tool"""
       entity_name: str = Field(description="Name of character, location, or item to look up")

   class CodexTools:
       """LangChain tools for accessing story knowledge"""

       def __init__(self, manuscript_id: str, db_session):
           self.manuscript_id = manuscript_id
           self.db = db_session

       def get_entity_info(self, entity_name: str) -> str:
           """Retrieve entity details from Codex"""
           entity = self.db.query(Entity).filter(
               Entity.manuscript_id == self.manuscript_id,
               or_(
                   Entity.name.ilike(f"%{entity_name}%"),
                   Entity.aliases.contains(entity_name)
               )
           ).first()

           if not entity:
               return f"No entity found named '{entity_name}'"

           # Format entity info for LLM
           info = f"{entity.name} ({entity.type}):\n"
           for key, value in entity.attributes.items():
               info += f"  - {key}: {value}\n"

           if entity.appearance_history:
               info += f"  - First appeared: Scene {entity.appearance_history[0]['scene_id']}\n"
               info += f"  - Total appearances: {len(entity.appearance_history)}\n"

           return info

       def get_recent_scenes(self, count: int = 3) -> str:
           """Get summaries of recent scenes for context"""
           scenes = self.db.query(Scene).filter(
               Scene.manuscript_id == self.manuscript_id
           ).order_by(Scene.position.desc()).limit(count).all()

           summaries = []
           for scene in scenes:
               # Extract first 200 chars as summary
               summary = scene.content[:200] + "..." if len(scene.content) > 200 else scene.content
               summaries.append(f"Scene {scene.position}: {summary}")

           return "\n\n".join(summaries)

       def search_similar_scenes(self, query: str, k: int = 3) -> str:
           """Vector search for similar scenes"""
           from app.services.embedding_service import EmbeddingService

           embedding_service = EmbeddingService()
           similar_scenes = embedding_service.find_similar_scenes(
               query=query,
               manuscript_id=self.manuscript_id,
               top_k=k
           )

           return "\n\n".join([f"Similar scene {i+1}:\n{scene}" for i, scene in enumerate(similar_scenes)])

       def build_tools(self) -> list[Tool]:
           """Build LangChain Tool objects"""
           return [
               Tool(
                   name="GetEntityInfo",
                   func=self.get_entity_info,
                   description="Look up detailed information about a character, location, or item from the story's Codex. Use this to ensure consistency."
               ),
               Tool(
                   name="GetRecentScenes",
                   func=self.get_recent_scenes,
                   description="Retrieve the most recent scenes written. Use this to maintain narrative continuity."
               ),
               Tool(
                   name="SearchSimilarScenes",
                   func=self.search_similar_scenes,
                   description="Find similar scenes from the manuscript using semantic search. Use this to match writing style and tone."
               )
           ]
   ```

**Acceptance Criteria**:
- Tools can access Codex entities
- Tools can retrieve recent scenes
- Vector search works for style matching
- Tools return formatted strings suitable for LLM consumption

---

### Epic 3.2: Graph-Augmented Generation (GraphRAG)
**Priority**: High | **Estimated Effort**: 4 days

#### Task 3.2.1: Implement Entity Context Retrieval
**Effort**: 2 days

1. **Create entity lookup service**
   ```python
   # backend/app/services/rag_service.py

   def get_entity_context(entity_names: List[str], manuscript_id: str) -> str:
       """Retrieve entity information from Codex"""
       context_parts = []

       for name in entity_names:
           entity = db.query(Entity).filter(
               Entity.manuscript_id == manuscript_id,
               or_(
                   Entity.name == name,
                   Entity.aliases.contains(name)
               )
           ).first()

           if entity:
               context = f"{entity.name} ({entity.type}):\n"
               for key, value in entity.attributes.items():
                   context += f"- {key}: {value}\n"
               context_parts.append(context)

       return "\n".join(context_parts)
   ```

2. **Create scene context retrieval**
   ```python
   def get_scene_context(location_name: str, manuscript_id: str) -> str:
       """Get previous scenes at this location"""
       location = get_entity_by_name(location_name, EntityType.LOCATION, manuscript_id)

       if not location:
           return ""

       # Find scenes at this location
       scenes = db.query(Scene).filter(
           Scene.manuscript_id == manuscript_id,
           Scene.setting_id == location.id
       ).order_by(Scene.position.desc()).limit(3).all()

       context = f"Previous events at {location_name}:\n"
       for scene in scenes:
           # Extract summary (first 100 words)
           summary = extract_summary(scene.content)
           context += f"- {summary}\n"

       return context
   ```

**Acceptance Criteria**:
- Entity context retrieval works
- Scene history retrieval works
- Context formatted for LLM consumption

---

#### Task 3.2.2: Implement Vector-Based Similarity Search
**Effort**: 1 day

```python
# backend/app/services/embedding_service.py

from sentence_transformers import SentenceTransformer
import chromadb

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.PersistentClient(path="./data/chroma")
        self.scenes_collection = self.chroma_client.get_collection("scene_embeddings")

    def embed_text(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()

    def find_similar_scenes(self, query: str, manuscript_id: str, top_k: int = 3):
        query_embedding = self.embed_text(query)

        results = self.scenes_collection.query(
            query_embeddings=[query_embedding],
            where={"manuscript_id": manuscript_id},
            n_results=top_k
        )

        return results["documents"][0]  # Similar scene texts
```

**Acceptance Criteria**:
- Embeddings generated for scenes
- Similarity search returns relevant scenes
- ChromaDB queries execute quickly (<100ms)

---

#### Task 3.2.3: Build RAG Prompt Engineering
**Effort**: 1 day

```python
def build_rag_prompt(
    user_request: str,
    manuscript_id: str,
    entity_names: List[str],
    location_name: str = None
) -> Tuple[str, str]:
    """Build system + user prompt with RAG context"""

    # Gather context
    entity_context = get_entity_context(entity_names, manuscript_id)
    location_context = get_scene_context(location_name, manuscript_id) if location_name else ""
    similar_scenes = find_similar_scenes(user_request, manuscript_id)

    # Build system prompt
    system_prompt = f"""You are a creative writing assistant for a fiction manuscript.

**Entity Information:**
{entity_context}

**Location Context:**
{location_context}

**Similar Scenes for Style Reference:**
{similar_scenes[0][:500]}...

Maintain consistency with the established facts above. Match the writing style of similar scenes."""

    # Build user prompt
    user_prompt = f"""Write a scene based on this request:

{user_request}

Incorporate the character traits and setting details provided in your context."""

    return system_prompt, user_prompt
```

**Acceptance Criteria**:
- RAG prompts include relevant context
- Entity facts correctly injected
- Generated text maintains consistency

---

### Epic 3.3: Beat Expansion Engine
**Priority**: Medium | **Estimated Effort**: 3 days

#### Task 3.3.1: Create Beat-to-Prose UI
**Effort**: 1.5 days

```typescript
// frontend/src/components/Muse/BeatExpander.tsx

export function BeatExpander() {
  const [beats, setBeats] = useState<string[]>(['']);
  const [expandedScenes, setExpandedScenes] = useState<Map<number, string>>(new Map());

  const expandBeat = async (beatIndex: number) => {
    const beat = beats[beatIndex];

    // Stream response
    const response = await fetch('/api/generate/beat-expansion', {
      method: 'POST',
      body: JSON.stringify({ beat, manuscriptId }),
    });

    const reader = response.body?.getReader();
    let text = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = new TextDecoder().decode(value);
      text += chunk;
      setExpandedScenes(new Map(expandedScenes.set(beatIndex, text)));
    }
  };

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="beats-column">
        <h3>Outline Beats</h3>
        {beats.map((beat, idx) => (
          <div key={idx}>
            <textarea
              value={beat}
              onChange={(e) => updateBeat(idx, e.target.value)}
              placeholder="• Hero discovers secret"
            />
            <button onClick={() => expandBeat(idx)}>Expand ✨</button>
          </div>
        ))}
        <button onClick={addBeat}>+ Add Beat</button>
      </div>

      <div className="prose-column">
        <h3>Generated Prose</h3>
        {Array.from(expandedScenes.entries()).map(([idx, prose]) => (
          <div key={idx} className="prose-block">
            <h4>Beat {idx + 1}</h4>
            <div className="typewriter-text">{prose}</div>
            <button onClick={() => insertToManuscript(prose)}>
              Insert to Manuscript
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Acceptance Criteria**:
- Split-pane interface works
- Beats editable as bullet points
- Expand button generates prose
- Prose displayed with typewriter effect

---

#### Task 3.3.2: Implement Style Matching Analysis
**Effort**: 1.5 days

```python
# backend/app/services/style_analyzer.py

import textstat
import numpy as np

def analyze_writing_style(text: str) -> dict:
    """Calculate style metrics"""
    sentences = text.split('.')

    # Sentence length variance (burstiness)
    sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
    burstiness = np.std(sentence_lengths) if sentence_lengths else 0

    # Readability (perplexity proxy)
    flesch_score = textstat.flesch_reading_ease(text)

    # Lexical diversity
    words = text.lower().split()
    unique_words = set(words)
    lexical_diversity = len(unique_words) / len(words) if words else 0

    return {
        "avg_sentence_length": np.mean(sentence_lengths) if sentence_lengths else 0,
        "burstiness": burstiness,
        "flesch_score": flesch_score,
        "lexical_diversity": lexical_diversity
    }

def build_style_matching_prompt(previous_text: str) -> str:
    """Generate instructions to match style"""
    style = analyze_writing_style(previous_text)

    return f"""Match this writing style:
- Average sentence length: {style['avg_sentence_length']:.1f} words
- Sentence variety: {'High' if style['burstiness'] > 5 else 'Medium' if style['burstiness'] > 2 else 'Low'}
- Reading level: {'Simple' if style['flesch_score'] > 70 else 'Moderate' if style['flesch_score'] > 50 else 'Complex'}
- Vocabulary: {'Diverse' if style['lexical_diversity'] > 0.6 else 'Moderate'}"""
```

**Acceptance Criteria**:
- Style analysis calculates metrics
- Generated prose matches source style
- User can toggle style matching on/off

---

### Epic 3.4: "The Coach" - Personalized Learning Agent
**Priority**: High | **Estimated Effort**: 5 days

> **NEW:** This epic implements a stateful LangChain agent that learns the writer's patterns, preferences, and weaknesses over time, providing increasingly personalized feedback.

#### Task 3.4.1: Database Schema for Learning & Memory
**Effort**: 1 day

1. **Create coaching history table**
   ```sql
   -- backend/migrations/versions/003_add_coaching_tables.py

   CREATE TABLE coaching_history (
       id TEXT PRIMARY KEY,
       user_id TEXT NOT NULL,
       manuscript_id TEXT,
       scene_text TEXT,
       agent_feedback JSON,
       user_reaction TEXT,  -- 'accepted', 'rejected', 'modified', 'ignored'
       feedback_type TEXT,  -- 'suggestion', 'warning', 'praise', 'critique'
       created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (manuscript_id) REFERENCES manuscripts(id)
   );

   CREATE INDEX idx_coaching_user ON coaching_history(user_id);
   CREATE INDEX idx_coaching_manuscript ON coaching_history(manuscript_id);
   ```

2. **Create writing profile table**
   ```sql
   CREATE TABLE writing_profile (
       user_id TEXT PRIMARY KEY,
       profile_data JSON,  -- Stores learned patterns
       created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
       updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
   );

   -- Profile data structure (JSON):
   {
       "style_metrics": {
           "avg_sentence_length": 15.2,
           "sentence_length_variance": 8.5,
           "avg_paragraph_length": 4.2,
           "lexical_diversity": 0.68,
           "flesch_reading_ease": 72.3
       },
       "strengths": [
           "vivid_descriptions",
           "natural_dialogue",
           "strong_openings"
       ],
       "weaknesses": [
           "info_dumping",
           "passive_voice_overuse",
           "telling_not_showing"
       ],
       "preferences": {
           "pov": "third_person_limited",
           "tense": "past",
           "dialogue_style": "minimal_tags"
       },
       "overused_words": {
           "just": 142,
           "really": 89,
           "very": 76
       },
       "favorite_techniques": [
           "sensory_details",
           "metaphor",
           "short_punchy_sentences_for_action"
       ]
   }
   ```

3. **Create feedback patterns table**
   ```sql
   CREATE TABLE feedback_patterns (
       id TEXT PRIMARY KEY,
       user_id TEXT NOT NULL,
       pattern_type TEXT,  -- 'overused_word', 'pacing_issue', 'consistency_error'
       pattern_description TEXT,
       frequency INTEGER DEFAULT 1,
       last_occurred DATETIME,
       FOREIGN KEY (user_id) REFERENCES writing_profile(user_id)
   );
   ```

**Acceptance Criteria**:
- Migration creates all tables
- Profile data stores as structured JSON
- Indices optimize user queries
- Sample profile can be inserted and retrieved

---

#### Task 3.4.2: Implement Learning Coach Agent
**Effort**: 2.5 days

1. **Create WritingCoach class**
   ```python
   # backend/app/services/coach/writing_coach.py

   from langchain.agents import AgentExecutor, create_openai_tools_agent
   from langchain.memory import ConversationBufferMemory
   from langchain_community.vectorstores import Chroma
   from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
   from langchain_anthropic import ChatAnthropic

   class WritingCoach:
       """Stateful agent that learns writer's patterns over time"""

       def __init__(self, user_id: str, manuscript_id: str, db_session):
           self.user_id = user_id
           self.manuscript_id = manuscript_id
           self.db = db_session

           # Load or create writing profile
           self.profile = self._load_profile()

           # Conversation memory (short-term)
           self.conversation_memory = ConversationBufferMemory(
               memory_key="chat_history",
               return_messages=True,
               output_key="output"
           )

           # Long-term memory (ChromaDB for semantic search)
           self.long_term_memory = self._init_long_term_memory()

           # LLM
           self.llm = ChatAnthropic(
               model="claude-3-5-sonnet-20241022",
               temperature=0.7
           )

           # Tools
           self.tools = self._build_tools()

           # Create agent
           self.agent = self._create_agent()

           self.executor = AgentExecutor(
               agent=self.agent,
               tools=self.tools,
               memory=self.conversation_memory,
               verbose=True,
               handle_parsing_errors=True
           )

       def _load_profile(self) -> dict:
           """Load user's writing profile from database"""
           profile_row = self.db.query(WritingProfile).filter_by(
               user_id=self.user_id
           ).first()

           if profile_row:
               return json.loads(profile_row.profile_data)
           else:
               # Initialize default profile
               return {
                   "style_metrics": {},
                   "strengths": [],
                   "weaknesses": [],
                   "preferences": {},
                   "overused_words": {},
                   "favorite_techniques": []
               }

       def _init_long_term_memory(self):
           """Initialize ChromaDB for long-term semantic memory"""
           collection_name = f"coach_memory_{self.user_id}"
           return Chroma(
               collection_name=collection_name,
               embedding_function=get_embeddings(),
               persist_directory=f"./data/coach_memory/{self.user_id}"
           )

       def _build_tools(self) -> list:
           """Build tools the agent can use"""
           from app.services.llm.tools import CodexTools
           from app.services.pacing_analyzer import analyze_pacing
           from app.services.consistency_checker import check_consistency

           codex_tools = CodexTools(self.manuscript_id, self.db)

           return codex_tools.build_tools() + [
               Tool(
                   name="GetWriterProfile",
                   func=lambda _: json.dumps(self.profile, indent=2),
                   description="Retrieve the writer's learned patterns, strengths, weaknesses, and preferences. Use this to personalize all feedback."
               ),
               Tool(
                   name="AnalyzePacing",
                   func=lambda text: json.dumps(analyze_pacing(text)),
                   description="Analyze pacing and tension in a text passage"
               ),
               Tool(
                   name="CheckConsistency",
                   func=lambda text: check_consistency(text, self.manuscript_id),
                   description="Check for plot holes and contradictions"
               ),
               Tool(
                   name="RecordObservation",
                   func=self._record_observation,
                   description="Store a new observation about the writer's patterns (e.g., 'tends to rush dialogue', 'overuses word X')"
               ),
               Tool(
                   name="SearchPastFeedback",
                   func=self._search_past_feedback,
                   description="Search past coaching interactions for similar situations"
               )
           ]

       def _create_agent(self):
           """Create the LangChain agent with dynamic system prompt"""
           prompt = ChatPromptTemplate.from_messages([
               ("system", self._build_system_prompt()),
               MessagesPlaceholder(variable_name="chat_history"),
               ("human", "{input}"),
               MessagesPlaceholder(variable_name="agent_scratchpad")
           ])

           return create_openai_tools_agent(
               llm=self.llm,
               tools=self.tools,
               prompt=prompt
           )

       def _build_system_prompt(self) -> str:
           """Dynamic system prompt based on learned profile"""
           strengths_str = ", ".join(self.profile.get("strengths", [])) or "still learning"
           weaknesses_str = ", ".join(self.profile.get("weaknesses", [])) or "still learning"

           return f"""You are a personalized writing coach for User {self.user_id}.

**Their Writing Profile:**
- Known strengths: {strengths_str}
- Areas to watch: {weaknesses_str}
- Style preferences: {json.dumps(self.profile.get('preferences', {}), indent=2)}
- Common overused words: {json.dumps(self.profile.get('overused_words', {}), indent=2)}

**Your Role:**
1. Provide PERSONALIZED feedback based on their specific patterns
2. Catch their recurring mistakes (you have their history)
3. Encourage their strengths when you see them
4. Adapt suggestions to their preferred style
5. Learn from their reactions (do they accept or reject your advice?)

**How to Give Feedback:**
- Be specific and constructive
- Reference their past patterns when relevant ("I notice you tend to...")
- Offer concrete examples, not generic advice
- Balance criticism with encouragement
- Use your tools to check facts and consistency

Use GetWriterProfile to see their complete profile, then tailor all advice accordingly."""

       async def analyze_scene(
           self,
           scene_text: str,
           context: dict = None
       ) -> dict:
           """Main method: Analyze a scene and provide personalized feedback"""

           # Build rich context
           prompt = f"""Analyze this scene the writer just wrote:

```
{scene_text}
```

**Context:**
{json.dumps(context or {}, indent=2)}

Provide personalized feedback considering:
1. Their known patterns and tendencies (check GetWriterProfile)
2. Consistency with story's Codex (use GetEntityInfo)
3. Pacing compared to recent scenes (use GetRecentScenes)
4. Any overused phrases or patterns you've noticed
5. Whether this shows their strengths or weaknesses

Be specific and actionable. If you notice a new pattern, record it with RecordObservation."""

           # Execute agent
           response = await self.executor.ainvoke({"input": prompt})

           # Store interaction for learning
           await self._store_coaching_session(scene_text, response)

           return response

       def _record_observation(self, observation: str) -> str:
           """Tool function: Record new observation about writer"""
           # Parse observation and update profile
           # This would use NLP to extract pattern type

           self.db.execute("""
               INSERT INTO feedback_patterns
               (id, user_id, pattern_type, pattern_description, last_occurred)
               VALUES (?, ?, ?, ?, ?)
           """, (str(uuid.uuid4()), self.user_id, "observation",
                 observation, datetime.now()))
           self.db.commit()

           return f"Recorded: {observation}"

       def _search_past_feedback(self, query: str, k: int = 3) -> str:
           """Tool function: Search past coaching sessions"""
           results = self.long_term_memory.similarity_search(query, k=k)
           return "\n\n".join([doc.page_content for doc in results])

       async def _store_coaching_session(self, scene_text: str, response: dict):
           """Store this session for future learning"""
           feedback_text = response.get("output", "")

           # Store in database
           self.db.execute("""
               INSERT INTO coaching_history
               (id, user_id, manuscript_id, scene_text, agent_feedback, created_at)
               VALUES (?, ?, ?, ?, ?, ?)
           """, (str(uuid.uuid4()), self.user_id, self.manuscript_id,
                 scene_text[:1000],  # Store excerpt
                 json.dumps(response),
                 datetime.now()))
           self.db.commit()

           # Store in vector DB for semantic search
           self.long_term_memory.add_texts(
               texts=[f"Scene: {scene_text[:500]}\n\nFeedback: {feedback_text}"],
               metadatas=[{"timestamp": datetime.now().isoformat()}]
           )

       async def update_profile_from_analysis(self, analysis_results: dict):
           """Update profile based on automated analysis"""
           # Update style metrics
           self.profile["style_metrics"].update(analysis_results.get("metrics", {}))

           # Update overused words
           for word, count in analysis_results.get("overused_words", {}).items():
               self.profile["overused_words"][word] = \
                   self.profile["overused_words"].get(word, 0) + count

           # Save to database
           self.db.execute("""
               UPDATE writing_profile
               SET profile_data = ?, updated_at = ?
               WHERE user_id = ?
           """, (json.dumps(self.profile), datetime.now(), self.user_id))
           self.db.commit()
   ```

**Acceptance Criteria**:
- Agent initializes with user profile
- Uses tools to access story context
- Provides personalized feedback
- Stores interactions for learning
- Profile updates over time

---

#### Task 3.4.3: Build Feedback UI Components
**Effort**: 1.5 days

1. **Create CoachPanel component**
   ```typescript
   // frontend/src/components/Coach/CoachPanel.tsx

   import { useState } from 'react';
   import { useMutation } from '@tanstack/react-query';

   export function CoachPanel({ manuscriptId, selectedText }: Props) {
     const [feedback, setFeedback] = useState<CoachFeedback | null>(null);

     const analyzeMutation = useMutation({
       mutationFn: async (text: string) => {
         const response = await fetch('/api/coach/analyze', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({
             manuscript_id: manuscriptId,
             scene_text: text
           })
         });
         return response.json();
       },
       onSuccess: (data) => {
         setFeedback(data);
       }
     });

     const recordReaction = async (reaction: 'accepted' | 'rejected' | 'modified') => {
       await fetch('/api/coach/feedback', {
         method: 'POST',
         body: JSON.stringify({
           feedback_id: feedback.id,
           reaction
         })
       });
     };

     return (
       <div className="coach-panel bg-white border-l border-slate-ui p-6">
         <h2 className="text-xl font-serif font-bold text-midnight mb-4">
           Your Writing Coach
         </h2>

         {feedback && (
           <div className="feedback-card mb-6">
             <div className="mb-4">
               <h3 className="font-sans font-semibold text-midnight mb-2">
                 Analysis
               </h3>
               <div className="prose prose-sm">
                 {feedback.analysis}
               </div>
             </div>

             {feedback.suggestions.length > 0 && (
               <div className="mb-4">
                 <h3 className="font-sans font-semibold text-midnight mb-2">
                   Suggestions
                 </h3>
                 <ul className="space-y-2">
                   {feedback.suggestions.map((suggestion, idx) => (
                     <li key={idx} className="flex items-start gap-2">
                       <span className="text-bronze">•</span>
                       <span className="text-sm text-faded-ink">{suggestion}</span>
                     </li>
                   ))}
                 </ul>
               </div>
             )}

             <div className="flex gap-2">
               <button
                 onClick={() => recordReaction('accepted')}
                 className="px-3 py-1 bg-bronze text-white text-sm font-sans"
                 style={{ borderRadius: '2px' }}
               >
                 Helpful
               </button>
               <button
                 onClick={() => recordReaction('rejected')}
                 className="px-3 py-1 bg-slate-ui text-midnight text-sm font-sans"
                 style={{ borderRadius: '2px' }}
               >
                 Not Helpful
               </button>
             </div>
           </div>
         )}

         <button
           onClick={() => analyzeMutation.mutate(selectedText)}
           disabled={!selectedText || analyzeMutation.isPending}
           className="w-full px-4 py-2 bg-bronze text-white font-sans font-medium disabled:opacity-50"
           style={{ borderRadius: '2px' }}
         >
           {analyzeMutation.isPending ? 'Analyzing...' : 'Get Feedback on Selected Text'}
         </button>
       </div>
     );
   }
   ```

2. **Create API endpoints**
   ```python
   # backend/app/api/routes/coach.py

   @router.post("/api/coach/analyze")
   async def analyze_with_coach(
       request: CoachAnalysisRequest,
       db: Session = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       """Get personalized feedback from writing coach"""
       coach = WritingCoach(
           user_id=current_user.id,
           manuscript_id=request.manuscript_id,
           db_session=db
       )

       feedback = await coach.analyze_scene(
           scene_text=request.scene_text,
           context=request.context
       )

       return {
           "id": str(uuid.uuid4()),
           "analysis": feedback["output"],
           "suggestions": extract_suggestions(feedback["output"]),
           "timestamp": datetime.now().isoformat()
       }

   @router.post("/api/coach/feedback")
   async def record_feedback_reaction(
       request: FeedbackReactionRequest,
       db: Session = Depends(get_db)
   ):
       """Record user's reaction to coach feedback"""
       db.execute("""
           UPDATE coaching_history
           SET user_reaction = ?
           WHERE id = ?
       """, (request.reaction, request.feedback_id))
       db.commit()

       return {"success": True}
   ```

**Acceptance Criteria**:
- Coach panel renders in sidebar
- Can analyze selected text
- Feedback displays clearly
- User can rate helpfulness
- Reactions stored for learning

---

### Epic 3.5: Sensory "Paint" Tools
**Priority**: Low | **Estimated Effort**: 2 days

#### Task 3.4.1: Create Floating Toolbar
**Effort**: 1 day

```typescript
// frontend/src/components/Editor/FloatingToolbar.tsx

export function FloatingToolbar() {
  const [editor] = useLexicalComposerContext();
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    return editor.registerUpdateListener(() => {
      const selection = window.getSelection();

      if (selection && selection.toString().length > 0) {
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        setPosition({ x: rect.left, y: rect.top - 60 });
        setIsVisible(true);
      } else {
        setIsVisible(false);
      }
    });
  }, [editor]);

  const applyTransformation = async (type: string) => {
    const selectedText = window.getSelection()?.toString();

    const prompts = {
      sight: "Add vivid visual descriptions to this text:",
      smell: "Add olfactory descriptions to this text:",
      sound: "Add auditory details to this text:",
      intense: "Make this text more intense and dramatic:",
      show: "Rewrite this to 'show, don't tell':"
    };

    const result = await generateText(prompts[type], selectedText);
    replaceSelection(result);
  };

  if (!isVisible) return null;

  return (
    <div
      className="floating-toolbar"
      style={{ position: 'absolute', left: position.x, top: position.y }}
    >
      <button onClick={() => applyTransformation('sight')}>👁️ Sight</button>
      <button onClick={() => applyTransformation('smell')}>👃 Smell</button>
      <button onClick={() => applyTransformation('sound')}>👂 Sound</button>
      <button onClick={() => applyTransformation('intense')}>⚡ Intensify</button>
      <button onClick={() => applyTransformation('show')}>🎭 Show</button>
    </div>
  );
}
```

**Acceptance Criteria**:
- Toolbar appears on text selection
- Each button triggers appropriate transformation
- Original text replaced with enhanced version
- Undo works correctly

---

## Epic 4: Structural Analysis

### Epic 4.1: Pacing Graph ("Vonnegut")
**Priority**: Medium | **Estimated Effort**: 3 days

#### Task 4.1.1: Implement Sentiment/Tension Analysis
**Effort**: 1.5 days

```python
# backend/app/services/pacing_analyzer.py

from textblob import TextBlob
import spacy

nlp = spacy.load("en_core_web_lg")

def analyze_pacing(text: str, chunk_size: int = 500) -> List[dict]:
    """Analyze pacing in chunks"""
    words = text.split()
    chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

    results = []
    for idx, chunk in enumerate(chunks):
        doc = nlp(chunk)

        # Sentiment analysis
        sentiment = TextBlob(chunk).sentiment.polarity

        # Tension analysis
        sentences = list(doc.sents)
        avg_sent_length = np.mean([len(list(sent)) for sent in sentences])

        # Active verb density
        verbs = [token for token in doc if token.pos_ == "VERB"]
        active_verbs = [v for v in verbs if "Pass" not in v.morph.get("Voice", [])]
        tension = len(active_verbs) / len(doc) if len(doc) > 0 else 0

        results.append({
            "chunk_index": idx,
            "word_position": idx * chunk_size,
            "sentiment": sentiment,  # -1 to 1
            "tension": tension,      # 0 to 1
            "sentence_length": avg_sent_length
        })

    return results
```

---

#### Task 4.1.2: Create Pacing Visualization
**Effort**: 1.5 days

```typescript
// frontend/src/components/Coach/PacingGraph.tsx

import { Line } from 'react-chartjs-2';

export function PacingGraph({ manuscriptId }: Props) {
  const { data: pacingData } = useQuery({
    queryKey: ['pacing', manuscriptId],
    queryFn: () => fetchPacingAnalysis(manuscriptId)
  });

  const chartData = {
    labels: pacingData.map(d => `Word ${d.word_position}`),
    datasets: [
      {
        label: 'Emotional Tone',
        data: pacingData.map(d => d.sentiment),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
      },
      {
        label: 'Tension',
        data: pacingData.map(d => d.tension),
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
      }
    ]
  };

  return (
    <div className="pacing-graph">
      <h3>Story Pacing</h3>
      <Line
        data={chartData}
        options={{
          responsive: true,
          scales: {
            y: {
              min: -1,
              max: 1
            }
          },
          plugins: {
            tooltip: {
              callbacks: {
                label: (context) => {
                  const value = context.parsed.y;
                  if (context.dataset.label === 'Emotional Tone') {
                    return value > 0 ? `Positive (${value.toFixed(2)})` : `Negative (${value.toFixed(2)})`;
                  }
                  return `Tension: ${value.toFixed(2)}`;
                }
              }
            }
          }
        }}
      />
      <div className="insights">
        {detectFlatSections(pacingData).map(section => (
          <div className="warning">
            ⚠️ Flat pacing detected around word {section.position}
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Acceptance Criteria**:
- Graph displays sentiment and tension
- X-axis shows word position
- Flat sections highlighted
- Tooltip shows details on hover

---

### Epic 4.2: Consistency Linter
**Priority**: High | **Estimated Effort**: 3 days

#### Task 4.2.1: Implement Fact-Checking Logic
**Effort**: 2 days

```python
# backend/app/services/consistency_checker.py

def check_consistency(text: str, manuscript_id: str) -> List[dict]:
    """Find contradictions between text and Codex"""
    doc = nlp(text)
    errors = []

    # Extract entity mentions
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # Look up in Codex
            entity = get_entity_by_name(ent.text, EntityType.CHARACTER, manuscript_id)

            if entity:
                # Check for attribute contradictions
                attributes_in_text = extract_attributes_from_context(ent, doc)

                for attr, value in attributes_in_text.items():
                    codex_value = entity.attributes.get(attr)

                    if codex_value and codex_value != value:
                        errors.append({
                            "entity": ent.text,
                            "attribute": attr,
                            "text_value": value,
                            "codex_value": codex_value,
                            "position": ent.start_char,
                            "context": ent.sent.text
                        })

    return errors

def extract_attributes_from_context(entity_mention, doc):
    """Extract attributes mentioned near an entity"""
    attributes = {}

    # Get sentence containing entity
    sent = entity_mention.sent

    # Look for patterns like "John's blue eyes" or "her red hair"
    for token in sent:
        if token.dep_ == "poss" and token.head.text in ["eyes", "hair", "voice"]:
            # Found possessive describing attribute
            attr_name = token.head.text
            # Find adjective describing it
            for child in token.head.children:
                if child.dep_ == "amod":
                    attributes[attr_name] = child.text

    return attributes
```

---

#### Task 4.2.2: Create Linter UI Integration
**Effort**: 1 day

```typescript
// frontend/src/components/Editor/plugins/ConsistencyLinterPlugin.tsx

export function ConsistencyLinterPlugin() {
  const [editor] = useLexicalComposerContext();
  const { data: errors } = useQuery({
    queryKey: ['consistency', manuscriptId],
    queryFn: checkConsistency,
    refetchInterval: 30000 // Check every 30 seconds
  });

  useEffect(() => {
    if (!errors) return;

    editor.update(() => {
      const root = $getRoot();

      errors.forEach(error => {
        // Find text node at error position
        // Apply custom error decoration
        const node = findNodeAtPosition(error.position);
        if (node) {
          node.setFormat('consistency-error');
        }
      });
    });
  }, [errors, editor]);

  return null;
}

// CSS
.consistency-error {
  border-bottom: 2px wavy purple;
  cursor: help;
}
```

**Acceptance Criteria**:
- Errors underlined in purple
- Tooltip shows contradiction details
- Clicking opens Codex entry to fix
- Re-check after edits

---

## Testing & Quality Assurance

### Test-1: Unit Testing Setup
**Priority**: High | **Estimated Effort**: 1 day

#### Backend Tests
```python
# backend/tests/test_nlp_service.py

def test_entity_extraction():
    text = "Elara walked into the Crystal Cavern."
    entities = extract_entities(text)
    assert len(entities) > 0
    assert any(e[1] == "PERSON" for e in entities)

def test_relationship_extraction():
    text = "John kissed Mary in the garden."
    relationships = extract_relationships(text, ["John", "Mary"])
    assert len(relationships) == 1
    assert relationships[0][2] == "ROMANTIC"
```

#### Frontend Tests
```typescript
// frontend/src/components/Editor/__tests__/ManuscriptEditor.test.tsx

import { render, screen } from '@testing-library/react';
import { ManuscriptEditor } from '../ManuscriptEditor';

test('renders editor with placeholder', () => {
  render(<ManuscriptEditor />);
  expect(screen.getByText(/Start writing/i)).toBeInTheDocument();
});

test('can type text into editor', async () => {
  const { container } = render(<ManuscriptEditor />);
  const editor = container.querySelector('[contenteditable="true"]');

  fireEvent.input(editor, { target: { textContent: 'Once upon a time' } });
  expect(editor.textContent).toBe('Once upon a time');
});
```

---

### Test-2: Integration Testing
**Priority**: High | **Estimated Effort**: 2 days

```python
# backend/tests/test_api_integration.py

@pytest.mark.asyncio
async def test_full_workflow(client):
    # Create manuscript
    response = await client.post("/api/manuscripts", json={"title": "Test Novel"})
    manuscript_id = response.json()["data"]["id"]

    # Add scene
    response = await client.post(f"/api/manuscripts/{manuscript_id}/scenes", json={
        "content": "John entered the castle.",
        "position": 0
    })
    scene_id = response.json()["data"]["id"]

    # Trigger entity extraction
    response = await client.post("/api/analyze/extract-entities", json={
        "manuscript_id": manuscript_id,
        "text": "John entered the castle."
    })

    # Wait for processing
    await asyncio.sleep(2)

    # Check suggestions
    response = await client.get(f"/api/codex/suggestions?manuscript_id={manuscript_id}")
    suggestions = response.json()["data"]
    assert len(suggestions) > 0
    assert any(s["name"] == "John" for s in suggestions)
```

---

### Test-3: E2E Testing
**Priority**: Medium | **Estimated Effort**: 2 days

```typescript
// e2e/tests/writing-workflow.spec.ts

import { test, expect } from '@playwright/test';

test('complete writing workflow', async ({ page }) => {
  // Create new manuscript
  await page.goto('/');
  await page.click('[data-testid="new-manuscript"]');
  await page.fill('input[name="title"]', 'My Test Novel');
  await page.click('button[type="submit"]');

  // Write content
  const editor = page.locator('[data-lexical-editor="true"]');
  await editor.type('Elara walked through the misty forest. She had never seen such beauty.');

  // Wait for auto-save
  await page.waitForSelector('[data-testid="save-indicator"][data-saved="true"]');

  // Check for entity suggestions
  await page.click('[data-testid="codex-sidebar"]');
  await expect(page.locator('[data-testid="suggestion-queue"]')).toContainText('Elara');

  // Approve suggestion
  await page.click('[data-testid="approve-suggestion-elara"]');

  // Verify entity created
  await expect(page.locator('[data-testid="entity-list"]')).toContainText('Elara');

  // Create snapshot
  await page.click('[data-testid="create-snapshot"]');
  await page.fill('input[name="snapshot-label"]', 'Chapter 1 draft');
  await page.click('button[data-testid="save-snapshot"]');

  // Verify in history
  await page.click('[data-testid="time-machine"]');
  await expect(page.locator('[data-testid="snapshot-list"]')).toContainText('Chapter 1 draft');
});
```

---

## Deployment & Distribution

### Deploy-1: Electron Packaging
**Priority**: High | **Estimated Effort**: 2 days

```javascript
// electron/main.js

const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let backendProcess;
let mainWindow;

function startBackend() {
  const pythonPath = path.join(__dirname, 'python', 'codex-backend');
  backendProcess = spawn(pythonPath, {
    cwd: __dirname
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  mainWindow.loadFile('dist/index.html');
}

app.whenReady().then(() => {
  startBackend();
  setTimeout(createWindow, 2000); // Wait for backend to start
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});
```

---

### Deploy-2: Build Pipeline
**Priority**: High | **Estimated Effort**: 1 day

```yaml
# .github/workflows/build.yml

name: Build & Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - uses: actions/setup-python@v4

      - name: Install dependencies
        run: |
          cd frontend && npm install
          cd ../backend && pip install -r requirements.txt pyinstaller

      - name: Build frontend
        run: cd frontend && npm run build

      - name: Build backend executable
        run: cd backend && pyinstaller --onefile app/main.py -n codex-backend

      - name: Package Electron app
        run: npm run electron:build

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: codex-ide-windows
          path: dist/Codex-IDE-Setup.exe

  build-mac:
    runs-on: macos-latest
    # Similar steps for macOS

  build-linux:
    runs-on: ubuntu-latest
    # Similar steps for Linux
```

---

## Task Estimation

### Summary by Epic

| Epic | Total Effort (Days) | Priority | Dependencies |
|------|---------------------|----------|--------------|
| Project Setup | 3.5 | Critical | None |
| Epic 1: Living Manuscript | 9 | Critical | Setup |
| Epic 2: The Codex | 10 | High | Setup, Epic 1 |
| **Epic 3: The Muse (LangChain)** | **17** | High | Setup, Epic 2 |
| &nbsp;&nbsp;3.1: LangChain Foundation | 4 | High | Epic 2 |
| &nbsp;&nbsp;3.2: GraphRAG | 4 | High | Epic 3.1 |
| &nbsp;&nbsp;3.3: Beat Expansion | 3 | Medium | Epic 3.1 |
| &nbsp;&nbsp;3.4: The Coach (Learning Agent) | 5 | High | Epic 3.1, 3.2 |
| &nbsp;&nbsp;3.5: Sensory Paint Tools | 1 | Low | Epic 3.1 |
| Epic 4: Structural Analysis | 6 | Medium | Epic 1, Epic 2 |
| Testing & QA | 5 | High | All Epics |
| Deployment | 3 | High | All Epics |
| **Total** | **53.5 days** | | |

> **Updated for LangChain:** Epic 3 has been enhanced with stateful agent architecture, adding 5 days for personalized learning coach.

### Team Allocation (1-2 Developers)

**Phase 1 (Weeks 1-3): Core Experience**
- Week 1: Project setup + Lexical editor ✅ (COMPLETE)
- Week 2: Auto-save + versioning backend
- Week 3: Time Machine UI + variant system

**Phase 2 (Weeks 4-6): Knowledge Layer**
- Week 4: spaCy setup + entity extraction
- Week 5: Codex UI + suggestion queue
- Week 6: Relationship graph + visualizer

**Phase 3 (Weeks 7-11): Generative Layer with LangChain**
- Week 7: LangChain setup + LLM wrappers + Codex tools
- Week 8: GraphRAG implementation + embedding system
- Week 9: Beat expansion + style matching
- Week 10: The Coach - Database schema + agent implementation
- Week 11: The Coach UI + feedback learning loop

**Phase 4 (Weeks 12-13): Polish & Distribution**
- Week 12: Pacing graph + consistency linter + testing
- Week 13: Electron packaging + deployment pipeline

**Total: 13 weeks (~3 months) for MVP with Learning Coach**

### LangChain Integration Benefits

**What This Adds:**
1. **Stateful Memory**: Agent remembers past interactions and learns patterns
2. **Tool Use**: Agent can query Codex, check consistency, analyze pacing autonomously
3. **Personalization**: Feedback gets better over time as it learns your style
4. **Reasoning**: Agent chains tools together to provide deeper analysis

**Dependencies Added:**
```bash
# New Python packages
langchain==0.1.0
langchain-anthropic==0.1.0
langchain-community==0.0.13
langchain-openai==0.0.5
llama-cpp-python==0.2.0
```

**Database Additions:**
- `coaching_history` - Stores all coaching interactions
- `writing_profile` - Stores learned user patterns (JSON)
- `feedback_patterns` - Tracks recurring issues
- ChromaDB collections per user for long-term semantic memory

---

## Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Local LLM too slow | High | Medium | Optimize with quantization, GPU acceleration |
| spaCy entity extraction inaccurate | Medium | High | Add user review/correction flow (already planned) |
| Git performance issues with large manuscripts | Medium | Low | Implement Git LFS, pagination |
| Lexical learning curve | Low | Medium | Extensive documentation, examples |
| ChromaDB/KuzuDB stability | Medium | Low | Plan migration path to mature alternatives |
| **LangChain agent reliability** | **High** | **Medium** | **Implement error handling, fallback to simpler prompts if tools fail, verbose logging** |
| **Agent token costs (cloud LLM)** | **Medium** | **High** | **Smart routing to local models, cache common queries, user spending limits** |
| **Long-term memory degradation** | **Low** | **Medium** | **Periodic profile validation, allow manual correction of learned patterns** |
| **Privacy concerns (cloud API)** | **High** | **Low** | **Offer local-only mode, transparent data handling, opt-in cloud features** |

---

## Success Criteria

### MVP (Version 1.0)
- [ ] Write and edit manuscripts with rich text formatting
- [ ] Automatic versioning with time travel
- [ ] Entity extraction and Codex management
- [ ] Basic AI generation (beat expansion, continuation)
- [ ] Consistency checking
- [ ] Desktop app for Windows/Mac/Linux

### Post-MVP Enhancements
- [ ] Collaboration features (real-time editing)
- [ ] Cloud sync
- [ ] Mobile companion app
- [ ] Advanced plotting tools (Save the Cat wizard)
- [ ] Custom AI model fine-tuning
- [ ] Export to EPUB, PDF, manuscript format

---

## Next Steps

1. **Review this plan with stakeholders**
2. **Set up development environment** (see Setup-1)
3. **Create GitHub project board** with all tasks
4. **Begin Phase 1: Core Experience**
5. **Weekly demos** to gather feedback
6. **Iterate based on user testing**

---

**Document Version**: 1.0
**Last Updated**: 2025-11-23
**Maintained By**: Development Team
