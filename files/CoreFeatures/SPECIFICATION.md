Codex IDE: Master Design Document & Technical Specification

1. System Overview & Architectural Philosophy
   Product Vision: An Integrated Development Environment (IDE) for fiction authors that unifies the flexibility of a word processor, the rigor of a knowledge graph, and the creativity of generative AI. Core Design Philosophy: "Invisible Engineering."

Complex Backend: Uses Git-like versioning, GraphRAG, and NLP pipelines.

Simple Frontend: Uses metaphors like "Time Machine," "Story Bible," and "Magic Assist." The user should never see a commit hash, a node edge, or a JSON object.

1.1 Tech Stack Definition
Frontend: React 18 (TypeScript), Vite, Tailwind CSS, Shadcn/UI (components).

Editor Framework: Lexical (by Meta). Selected for its headless architecture and ability to treat text as structured nodes (essential for inline AI).

Backend/Local Server: Python 3.11 + FastAPI. (Python is required for the NLP/spaCy and local LLM inference layers).

Database (Local): SQLite (Application Data) + ChromaDB (Vector Store for RAG) + KuzuDB or NetworkX (Knowledge Graph).

State Management: TanStack Query (server state) + Zustand (client state).

2. Feature Implementation Plan (Epics)
   Epic 1: The "Living Manuscript" (Editor & Versioning)
   Goal: Create a writing experience that feels safe and fluid, handling versioning automatically.

Task 1.1: Implement Lexical Editor Wrapper

Create a ManuscriptEditor component.

Implement custom nodes for SceneBreak, Dialogue (auto-detected), and EntityMention (clickable names).

Constraint: Editor must support "Focus Mode" (hiding UI) and "Architect Mode" (showing margin comments/metadata).

Task 1.2: "Time Machine" Versioning (Invisible Git)

Backend: Implement a local Git repository pattern hidden from the user.

Auto-Save Strategy: Trigger a "Snapshot" (commit) on:

Session close.

Chapter completion.

Pre-generation (before AI writes text).

UI Layer: Instead of a Git log, build a "History Slider."

Visuals: A vertical timeline showing "moments" (e.g., "Chapter 3 Revised," "Added Character Elara").

Interaction: Clicking a moment shows a diff view (Green = Added, Red = Removed) and a "Restore this Version" button.

Task 1.3: Scoped Branching ("Multiverse" Feature)

Concept: Allow users to write alternative versions of a scene without duplicating the file.

Implementation: Create a VariantManager in the database.

UI: A tab switcher above the Scene Editor: [ Alt: Hero Escapes ].

Action: "Merge to Main" button replaces the content of the Main Draft with the selected Variant.

Epic 2: The Codex (Dynamic Knowledge Graph)
Goal: A "Story Bible" that updates itself as the user writes, preventing contradictions.

Task 2.1: Define the Codex Schema

Create strict JSON types for Character, Location, Item, Lore. (See Data Structure section below).

Task 2.2: The "Digital Archivist" (Implicit Entity Extraction)

Pipeline: Integrate spaCy with neuralcoref in the Python backend.

Trigger: Run analysis asynchronously 5 seconds after the user stops typing.

Logic:

Identify Proper Nouns (NER).

Resolve Pronouns ("He" -> "John").

Compare against existing Codex DB.

If new entity found -> Add to "Suggestions Queue."

UI: A subtle "New Intel" indicator in the sidebar. User clicks to approve: "We noticed you mentioned 'The Obsidian Dagger.' Create entry?"

Task 2.3: Relationship Tracking

Logic: If Entity A and Entity B appear in the same paragraph with specific verbs (e.g., "kissed," "stabbed"), create a provisional edge in the graph.

Visualizer: Use react-force-graph to show a "Character Web" where line thickness = number of interactions.

Epic 3: The "Muse" (Generative AI Layer)
Goal: Sudowrite-style generative features grounded in the Codex data.

Task 3.1: Hybrid LLM Router

Implement a router that selects the model based on task:

Simple (Spellcheck/Phrasing): Local Llama 3 (8B) or Mistral.

Complex (Plotting/Prose): Claude 3.5 Sonnet / GPT-4o (via API).

Uncensored: Router option to send to OpenRouter (e.g., Dolphin-Mixtral) for adult/dark content.

Task 3.2: Graph-Augmented Generation (GraphRAG)

Workflow: When user asks "Write a scene where John enters the castle":

Lookup: Query Codex for "John" (Traits: Brave, Inventory: Sword) and "Castle" (Traits: Ruined, Haunted).

Inject: Prepend these facts to the System Prompt.

Generate: Output prose that is contextually accurate (e.g., John uses his sword, notices the ruins).

Task 3.3: The "Beat Expansion" Engine

UI: Split screen. Left = Bullet points (Beats). Right = Prose.

Action: "Expand" button converts 1 beat into ~300 words of prose.

Style Matching: Analyze the previous 2,000 words of the manuscript to calculate "Perplexity" and "Burstiness" (sentence length variance) and instruct the LLM to match this style.

Task 3.4: Sensory "Paint" Tools

UI: A floating toolbar when text is highlighted.

Options: "Describe (Sight)," "Describe (Smell)," "Make Intense," "Show, Don't Tell."

Epic 4: Structural Analysis (The Coach)
Goal: Educational scaffolding and pacing checks.

Task 4.1: The "Vonnegut" Pacing Graph

Logic: Tokenize manuscript into 500-word chunks. Score each chunk for "Sentiment" (Positive/Negative) and "Tension" (Sentence length + Active Verb density).

Visualization: A line graph running parallel to the scrollbar.

Usage: User sees a flat line in Act 2 -> Realizes the pacing is dragging.

Task 4.2: Consistency Linter

Logic: Background job checks text against Codex facts.

Example: Codex says "John's eyes: Blue." Text says "John's brown eyes."

UI: Underline the error in Purple (distinct from Spellcheck Red). Tooltip: "Contradiction: Codex lists John's eyes as Blue."

3. Data Structures (JSON Schemas)
   3.1 The Entity Model (Character)

JSON

{
"id": "uuid-1234",
"type": "CHARACTER",
"name": "Elara Vance",
"aliases":,
"attributes": {
"age": 24,
"appearance": "Scar on left cheek, cybernetic eye",
"voice": "Sarcastic, uses short sentences"
},
"relationships":,
"appearance_history":,
"image_seed": 4829104 // For consistent image generation
}
3.2 The Manuscript Node (Lexical)

JSON

{
"type": "scene",
"id": "sc-001",
"metadata": {
"pov_character": "uuid-1234",
"setting": "uuid-9999",
"time_of_day": "Dusk",
"beat_type": "Inciting Incident", // Save the Cat tag
"word_count": 1450,
"completion_status": "DRAFT"
},
"content": "..." // Lexical serialized state
} 4. Implementation Directives for Claude Code
Instruction: When creating the plan.md file, organize the development phases as follows to ensure the "Invisible Engineering" requirement is met.

Phase 1: The Core Experience

Build the Lexical editor with Markdown support.

Set up SQLite.

Implement the "Time Machine" UI (mocked backend initially).

User Value: A distraction-free editor that "never loses work."

Phase 2: The Knowledge Layer

Implement the Python backend with spaCy.

Build the "Sidebar" that updates based on the cursor position.

User Value: The tool "knows" who the characters are.

Phase 3: The Generative Layer

Integrate LLM APIs.

Implement "Beat Expansion" and "Rewrite" tools.

User Value: The tool helps write the story when stuck.

Phase 4: The Polish & Teacher

Implement Pacing Graphs and Consistency Linters.

Add the "Genesis Wizard" (Save the Cat outlining templates).

User Value: The tool teaches structure and editing.

Critical Coding Rule:

Abstraction: Never expose raw JSON or graph query languages to the frontend. All interactions must be through semantic API endpoints (e.g., add_character_to_scene, not update_graph_node).

Latency: Generative features must show a "Streaming" UI (typing effect) to maintain immersion. Do not use full-page loaders.
