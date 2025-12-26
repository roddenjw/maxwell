# Maxwell Implementation Plan v2.0
## Integrated Roadmap: MVP → PLG Growth Engine

**Last Updated:** December 24, 2025
**Vision:** The world's most intuitive fiction writing IDE with invisible engineering and viral growth mechanics

---

## Executive Summary

This plan integrates:
- **Phase 1-4 Market Launch** (Months 1-12)
- **PLG Growth Features** (Viral mechanics, real-time NLP, BYOK)
- **Critical Bug Fixes** (Chapter loading, drag-and-drop)

**Key Principle:** Each phase must ship a feature that drives the next phase's growth.

---

## Current State Audit (December 2025)

### ✅ Completed Features
- [x] Lexical-based rich text editor
- [x] Chapter/folder database schema (hierarchical)
- [x] Chapter API (CRUD endpoints)
- [x] DocumentNavigator component (tree view)
- [x] Basic entity extraction (spaCy NLP)
- [x] Suggestion queue (one-click approval)
- [x] Git-based versioning (snapshots)
- [x] Timeline orchestrator (events, emotional arc, heatmap)
- [x] Enhanced toolbar (fonts, sizes, alignment, lists)

### 🐛 Critical Bugs (Block Launch)
- [ ] Chapter clicking does nothing (no content loading)
- [ ] No drag-and-drop reordering for chapters
- [ ] Folder expand/collapse state not persisted

### 🚧 In Progress
- [ ] Real-time entity extraction (manual "Analyze" button exists)
- [ ] Multiverse branching UI (basic snapshots work, needs visual timeline)

---

## Phase 1: The MVP — "The Binder"
**Timeline:** Months 1-3 (January - March 2026)
**Goal:** Launch a fully functional Scrivener alternative with local-first storage
**Pricing:** Beta Lifetime Deal ($49)
**Target Audience:** Indie Hackers, r/writing, writing Twitter

### Critical Path Items (Must Ship)

#### 1.1 Fix Chapter Loading & Navigation (Week 1)
**Priority:** P0 (Blocking)

**Issue:** Clicking chapters doesn't load content into editor.

**Solution:**
```typescript
// App.tsx
const [currentChapterContent, setCurrentChapterContent] = useState('');

const handleChapterSelect = async (chapterId: string) => {
  setCurrentChapter(chapterId);

  // Fetch chapter content
  const chapter = await chaptersApi.getChapter(chapterId);

  // Load into editor
  setCurrentChapterContent(chapter.lexical_state || '');
  setEditorKey(prev => prev + 1); // Force re-mount with new content
};

// Pass to DocumentNavigator
<DocumentNavigator
  manuscriptId={currentManuscript.id}
  onChapterSelect={handleChapterSelect}
/>

// Update Editor to use chapter content
<ManuscriptEditor
  key={editorKey}
  chapterId={currentChapterId}
  initialContent={currentChapterContent}
  onSave={(lexicalState) => {
    // Auto-save to chapter
    chaptersApi.updateChapter(currentChapterId, { lexical_state: lexicalState });
  }}
/>
```

**Files to Edit:**
- `/frontend/src/App.tsx` - Implement handleChapterSelect
- `/frontend/src/components/Editor/ManuscriptEditor.tsx` - Accept chapterId prop
- `/frontend/src/components/Editor/plugins/AutoSavePlugin.tsx` - Save to chapter, not manuscript

**Estimate:** 4 hours

---

#### 1.2 Drag-and-Drop Chapter Reordering (Week 1-2)
**Priority:** P0 (Launch blocker)

**User Story:** "As a writer, I want to drag chapters to reorder them, just like Scrivener's binder."

**Technical Approach:**

Use `@dnd-kit` (already popular, accessible, works with React 18):

```bash
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities
```

**Implementation:**

```typescript
// /frontend/src/components/Document/DocumentNavigator.tsx
import { DndContext, closestCenter, DragEndEvent } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

export default function DocumentNavigator({ manuscriptId, onChapterSelect }) {
  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (active.id !== over?.id) {
      const oldIndex = chapterTree.findIndex(ch => ch.id === active.id);
      const newIndex = chapterTree.findIndex(ch => ch.id === over?.id);

      // Optimistic update
      const newTree = arrayMove(chapterTree, oldIndex, newIndex);
      setChapterTree(newTree);

      // Persist to backend
      const chapterIds = newTree.map(ch => ch.id);
      await chaptersApi.reorderChapters(chapterIds);
    }
  };

  return (
    <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={chapterTree.map(ch => ch.id)} strategy={verticalListSortingStrategy}>
        {chapterTree.map(node => (
          <SortableChapterNode key={node.id} node={node} onSelect={onChapterSelect} />
        ))}
      </SortableContext>
    </DndContext>
  );
}

// Sortable wrapper component
function SortableChapterNode({ node, onSelect }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: node.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style}>
      <button
        onClick={() => onSelect(node.id, node.is_folder)}
        className="w-full text-left px-3 py-2"
      >
        <div className="flex items-center gap-2">
          {/* Drag handle */}
          <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing">
            ⋮⋮
          </div>

          {/* Icon */}
          <span>{node.is_folder ? '📁' : '📄'}</span>

          {/* Title */}
          <span>{node.title}</span>
        </div>
      </button>

      {/* Nested children (if folder) */}
      {node.is_folder && node.children.length > 0 && (
        <div className="ml-4">
          {node.children.map(child => (
            <SortableChapterNode key={child.id} node={child} onSelect={onSelect} />
          ))}
        </div>
      )}
    </div>
  );
}
```

**Additional Features:**
- [ ] Visual drag preview (ghost element)
- [ ] Drop between items (not just replace)
- [ ] Drag chapters into/out of folders
- [ ] Keyboard shortcuts (Ctrl+Up/Down to reorder)

**Files to Create/Edit:**
- `/frontend/src/components/Document/DocumentNavigator.tsx` - Add DnD
- `/frontend/src/components/Document/SortableChapterNode.tsx` - New component

**Estimate:** 8 hours

---

#### 1.3 Binder File System UX Polish (Week 2)
**Priority:** P1 (Nice to have for beta)

**Features:**
- [ ] Inline rename (double-click title to edit)
- [ ] Right-click context menu (rename, delete, duplicate)
- [ ] Keyboard navigation (arrow keys, Enter to open)
- [ ] Visual folder expand/collapse animation
- [ ] Persist expanded state to localStorage

**Example: Inline Rename**
```typescript
function ChapterNode({ node }) {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(node.title);

  const handleDoubleClick = () => setIsEditing(true);

  const handleSave = async () => {
    await chaptersApi.updateChapter(node.id, { title });
    setIsEditing(false);
  };

  return (
    <div onDoubleClick={handleDoubleClick}>
      {isEditing ? (
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          onBlur={handleSave}
          onKeyDown={e => e.key === 'Enter' && handleSave()}
          autoFocus
        />
      ) : (
        <span>{node.title}</span>
      )}
    </div>
  );
}
```

**Estimate:** 6 hours

---

#### 1.4 Local-First Storage (Week 3)
**Priority:** P1 (Beta requirement)

**Goal:** All data stored locally in SQLite (backend), no cloud dependency.

**Current State:** Already using SQLite (`/backend/data/codex.db`)

**Enhancements Needed:**
- [ ] Backup/restore feature (export entire database)
- [ ] Import from Scrivener (.scriv files - optional)
- [ ] Data export to DOCX/PDF (for submission)

**Export Feature:**
```python
# /backend/app/api/routes/export.py
@router.get("/export/{manuscript_id}/docx")
async def export_to_docx(manuscript_id: str, db: Session = Depends(get_db)):
    """Export manuscript to DOCX format"""
    from docx import Document
    from docx.shared import Pt, Inches

    doc = Document()

    # Fetch all chapters in order
    chapters = db.query(Chapter).filter(
        Chapter.manuscript_id == manuscript_id,
        Chapter.is_folder == 0
    ).order_by(Chapter.order_index).all()

    for chapter in chapters:
        # Add chapter title as heading
        doc.add_heading(chapter.title, level=1)

        # Add content
        doc.add_paragraph(chapter.content)

        # Page break
        doc.add_page_break()

    # Return as file
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=manuscript.docx"}
    )
```

**Estimate:** 8 hours

---

#### 1.5 Beta Launch Checklist (Week 3-4)

**Must-Haves:**
- [x] Chapter creation/editing works
- [x] Drag-and-drop reordering
- [x] Export to DOCX
- [ ] Onboarding flow (welcome modal, sample manuscript)
- [ ] Basic analytics (Mixpanel/PostHog integration)
- [ ] Crash reporting (Sentry)

**Marketing Assets:**
- [ ] Landing page (highlight "Scrivener alternative, $49 lifetime")
- [ ] Demo video (2 minutes, show binder + export)
- [ ] Launch tweet thread
- [ ] Product Hunt launch plan

**Launch Platforms:**
- Indie Hackers
- r/writing
- r/selfpublish
- Writing Twitter (#WritingCommunity)

**Success Metrics:**
- 100 beta signups in first week
- 50 lifetime purchases ($2,450 revenue)

**Estimate:** 16 hours (marketing + polish)

---

### Phase 1 Total Timeline: 3 Weeks
**Total Development Hours:** ~50 hours
**Revenue Target:** $2,450 (50 sales @ $49)

---

## Phase 2: The Logic Layer — "The Codex"
**Timeline:** Months 4-6 (April - June 2026)
**Goal:** Auto-updating knowledge graph that feels "magical"
**Pricing:** Increase to $99 (grandfathered users stay at $49)
**Target Audience:** AuthorTube, writing coaches, Scrivener refugees

### 2.1 Real-Time Entity Extraction (Week 1-2)
**Priority:** P0 (Core differentiator)

**Current State:** Manual "Analyze" button in toolbar.

**Target State:** Background extraction while typing (debounced).

**Implementation:** (See PLG_STRATEGY.md Section 1 for full architecture)

**Quick Win Version (Week 1):**
```typescript
// Auto-trigger analysis after 3 seconds of no typing
const debouncedAnalyze = useMemo(
  () => debounce(async () => {
    const text = extractCurrentParagraph(); // Only analyze current paragraph
    const entities = await codexApi.analyzeText({
      manuscript_id: manuscriptId,
      text: text
    });

    // Show toast for new entities
    if (entities.suggestions.length > 0) {
      showToast(`✨ ${entities.suggestions.length} new entities detected`);
    }
  }, 3000),
  [manuscriptId]
);

// Trigger on every editor change
const handleEditorChange = (editorState) => {
  // ... existing code ...
  debouncedAnalyze();
};
```

**Full Version (Week 2):**
- WebSocket connection for true real-time
- Only analyze text deltas (new characters typed)
- Smart deduplication (don't re-suggest same entity)

**Files:**
- `/frontend/src/hooks/useRealtimeNLP.ts` - New WebSocket hook
- `/backend/app/api/routes/realtime.py` - New WebSocket endpoint
- `/frontend/src/components/EntityToast.tsx` - Toast notification

**Estimate:** 12 hours

---

#### 2.2 Visual Timeline Enhancements (Week 3)
**Priority:** P1 (Marketing differentiator)

**Current State:** Timeline sidebar exists with emotional arc, heatmap.

**Enhancements:**
- [ ] Character location tracker (map view - where is each character at each event?)
- [ ] Conflict tracker (which characters are in conflict?)
- [ ] Timeline export to PDF (for plotting on paper)

**Example: Character Location Tracker**
```typescript
// /frontend/src/components/Timeline/CharacterLocationMap.tsx
export function CharacterLocationMap({ manuscriptId, characterId }) {
  const [events, setEvents] = useState([]);

  // Fetch events where character appears
  useEffect(() => {
    timelineApi.listEvents(manuscriptId, { character_id: characterId })
      .then(data => setEvents(data));
  }, [characterId]);

  return (
    <div className="space-y-2">
      {events.map((event, i) => (
        <div key={event.id} className="flex items-center gap-3">
          <div className="w-8 h-8 bg-bronze text-white rounded-full flex items-center justify-center">
            {i + 1}
          </div>
          <div className="flex-1">
            <p className="font-semibold">{event.description}</p>
            <p className="text-sm text-faded-ink">
              Location: {getLocationName(event.location_id)}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
```

**Estimate:** 8 hours

---

#### 2.3 Codex Relationship Graph (Week 4)
**Priority:** P1 (Visual appeal for demos)

**Current State:** Basic relationship list.

**Enhancement:** Interactive force-directed graph (like Obsidian).

**Already Built:** `/frontend/src/components/Codex/RelationshipGraph.tsx` exists!

**Improvements Needed:**
- [ ] Click node to see details
- [ ] Different edge styles for relationship types (family, enemy, ally)
- [ ] Export graph as PNG (for social sharing!)

**Estimate:** 6 hours

---

#### 2.4 AuthorTube Outreach Campaign (Week 4-6)

**Strategy:** Send free lifetime licenses to writing YouTubers in exchange for honest reviews.

**Target Creators:**
- Abbie Emmons (580K subs)
- Jenna Moreci (600K subs)
- Shaelin Writes (280K subs)
- Ellen Brock (150K subs)

**Pitch Email Template:**
```
Subject: Free lifetime access to Maxwell (new Scrivener alternative)

Hi [Name],

I'm building Maxwell, a writing IDE designed for fiction authors. It combines:
- Scrivener's binder system
- Novelcrafter's timeline
- Auto-updating character database (no manual data entry)

I'd love to give you free lifetime access in exchange for an honest review. No strings attached—even if you hate it, I want real feedback.

Demo: [Loom video link]

Interested?

Best,
[Your Name]
```

**Success Metrics:**
- 3+ YouTuber reviews
- 1,000 new signups from YouTube traffic
- $50,000 revenue (500 sales @ $99)

---

### Phase 2 Total Timeline: 6 Weeks
**Total Development Hours:** ~40 hours
**Revenue Target:** $50,000

---

## Phase 3: The AI Integration — "Zero Mark-up AI"
**Timeline:** Months 7-9 (July - September 2026)
**Goal:** Guided BYOK with OpenRouter (no subscription anxiety)
**Pricing:** Keep at $99 base + pay-as-you-go AI
**Target Audience:** Sudowrite refugees, cost-conscious authors

### 3.1 Guided BYOK Setup (Week 1-2)
**Priority:** P0 (Core feature)

**Implementation:** (See PLG_STRATEGY.md Section 3 for full architecture)

**Key Components:**
1. **Wallet System** - Track user balance
2. **OpenRouter Integration** - Single API for 20+ models
3. **Stripe Integration** - $5/$10/$20 top-up amounts
4. **In-App Balance Widget** - Always visible

**User Flow:**
1. Click "Enable AI Features"
2. Add $5 with Stripe (one click, no API keys)
3. Start generating (costs deducted automatically)
4. Low balance warning at $1 remaining

**Files to Create:**
- `/backend/app/models/ai_wallet.py` - Database models
- `/backend/app/services/ai_wallet_service.py` - Business logic
- `/frontend/src/components/AI/WalletWidget.tsx` - UI widget
- `/frontend/src/components/AI/TopUpModal.tsx` - Stripe checkout

**Estimate:** 20 hours

---

#### 3.2 AI Writing Features (Week 3-4)
**Priority:** P0 (Justifies AI costs)

**Features to Ship:**
1. **Rewrite** - Select text, click "Rewrite" for alternate version
2. **Describe** - "Describe this character" (generates physical description)
3. **Brainstorm** - "What happens next?" (plot suggestions)

**Example: Rewrite Feature**
```typescript
// /frontend/src/components/Editor/AIToolbar.tsx
export function AIToolbar({ selectedText, onReplace }) {
  const [loading, setLoading] = useState(false);

  const handleRewrite = async () => {
    setLoading(true);

    const result = await aiApi.rewrite({
      text: selectedText,
      instruction: "Make this more descriptive",
      model: "anthropic/claude-3-haiku" // Cheapest for drafts
    });

    // Show result in modal with accept/reject
    showRewriteModal(result.text, () => {
      onReplace(result.text);
    });

    setLoading(false);
  };

  return (
    <button onClick={handleRewrite} disabled={!selectedText || loading}>
      {loading ? 'Rewriting...' : '✨ Rewrite'}
    </button>
  );
}
```

**Backend API:**
```python
# /backend/app/api/routes/ai.py
@router.post("/rewrite")
async def rewrite_text(
    request: RewriteRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rewrite text using AI"""

    # Call wallet service (checks balance, makes AI call, deducts cost)
    result = await ai_wallet_service.call_ai_model(
        user_id=user_id,
        model=request.model,
        messages=[
            {"role": "system", "content": "You are a creative writing assistant."},
            {"role": "user", "content": f"Rewrite this text: {request.text}\n\nInstruction: {request.instruction}"}
        ],
        max_tokens=500
    )

    return {
        "success": True,
        "data": {
            "text": result,
            "cost": ai_wallet_service.last_cost  # Show user how much it cost
        }
    }
```

**Estimate:** 16 hours

---

#### 3.3 Marketing: "Zero Mark-up AI" Campaign (Week 4)

**Angle:** "Stop paying $29/month for AI you don't use. Pay only for what you generate."

**Comparison Chart:**
| Feature | Sudowrite | Maxwell |
|---------|-----------|---------|
| Monthly Cost | $29 | $0 |
| AI Cost per 1000 words | Included | ~$0.02 |
| Credits Expire? | Yes (monthly) | Never |
| Setup | Email signup | One-click |

**Content:**
- Blog post: "Why I switched from Sudowrite to Maxwell"
- Reddit post in r/selfpublish
- Twitter thread with cost breakdown

**Success Metrics:**
- 500 new signups
- 200 users add AI funds ($2,000 in wallet deposits)

---

### Phase 3 Total Timeline: 4 Weeks
**Total Development Hours:** ~50 hours
**Revenue Target:** $25,000 (250 sales) + $2,000 (AI top-ups)

---

## Phase 4: The Community Layer — "Viral Stats Engine"
**Timeline:** Months 10-12 (October - December 2026)
**Goal:** Shareable writing stats that go viral (Spotify Wrapped for writers)
**Pricing:** Keep at $99
**Target Audience:** WritingTok, BookTok, #WritingCommunity

### 4.1 Writing Stats Tracking (Week 1)
**Priority:** P0 (Foundation for viral engine)

**Metrics to Track:**
- Words written per session/day/week/month
- Most used sensory words
- Writing "vibe" (tone analysis from timeline)
- Focus streak (minutes of continuous writing)
- Most productive day/time

**Database Schema:**
```python
# /backend/app/models/writing_stats.py
class WritingSession(Base):
    """Track individual writing sessions"""
    __tablename__ = "writing_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    manuscript_id = Column(String, ForeignKey("manuscripts.id"))

    started_at = Column(DateTime)
    ended_at = Column(DateTime)

    words_written = Column(Integer)
    characters_written = Column(Integer)

    # Derived metrics
    focus_time = Column(Integer)  # Seconds of active writing
    breaks_taken = Column(Integer)

class WritingStat(Base):
    """Aggregated stats for recap cards"""
    __tablename__ = "writing_stats"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    timeframe = Column(String)  # 'day', 'week', 'month'
    date = Column(Date)

    word_count = Column(Integer)
    sensory_words = Column(JSON)  # {"sight": ["crimson", "glowing"], ...}
    writing_vibe = Column(String)  # "Melancholic", "Triumphant", etc.
    focus_streak = Column(Integer)  # Longest uninterrupted writing time
```

**Estimate:** 8 hours

---

#### 4.2 Aesthetic Recap Card Generator (Week 2-3)
**Priority:** P0 (Viral engine)

**Implementation:** (See PLG_STRATEGY.md Section 2 for full architecture)

**Templates:**
1. **Dark** - Gradient (dark blue → purple), white text
2. **Vintage** - Parchment background, serif fonts
3. **Neon** - Vibrant gradients, bold colors

**Example Card Layout:**
```
┌─────────────────────────┐
│                         │
│   Your Writing Wrapped  │
│                         │
│       2,847             │
│   words written         │
│                         │
│  Most used word:        │
│      "Crimson"          │
│                         │
│  Writing Vibe:          │
│    Melancholic          │
│                         │
│  Focus Streak: 43 min   │
│                         │
│  Written in Maxwell     │
└─────────────────────────┘
```

**Key Feature: One-Click Share**
```typescript
const handleShare = async () => {
  const blob = await recapCardGenerator.generateCard(stats, template);

  if (navigator.share) {
    // Native share (mobile)
    await navigator.share({
      files: [new File([blob], 'maxwell-recap.png', { type: 'image/png' })],
      title: 'My Writing Progress',
      text: 'Check out my writing stats! #WritingCommunity #Maxwell'
    });
  } else {
    // Fallback: Download
    downloadBlob(blob, 'maxwell-recap.png');
  }
};
```

**Estimate:** 12 hours

---

#### 4.3 Sprint Rooms (Week 4)
**Priority:** P1 (Community building)

**Concept:** Live writing rooms where writers work together in real-time.

**Features:**
- [ ] Public/private rooms
- [ ] Live word count leaderboard
- [ ] Timer (25-min sprints)
- [ ] Chat (optional)

**Tech Stack:**
- WebSockets for real-time updates
- Redis for session management

**MVP Implementation:**
```python
# /backend/app/services/sprint_room_service.py
class SprintRoom:
    def __init__(self, room_id: str, duration: int = 25):
        self.room_id = room_id
        self.duration = duration  # minutes
        self.participants = {}  # user_id -> word_count
        self.started_at = None

    async def join(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.participants[user_id] = 0

        # Broadcast new participant
        await self.broadcast({
            "type": "user_joined",
            "user_id": user_id,
            "total_participants": len(self.participants)
        })

    async def update_progress(self, user_id: str, word_count: int):
        self.participants[user_id] = word_count

        # Broadcast leaderboard
        leaderboard = sorted(
            self.participants.items(),
            key=lambda x: x[1],
            reverse=True
        )

        await self.broadcast({
            "type": "leaderboard_update",
            "leaderboard": leaderboard
        })
```

**Frontend:**
```typescript
// /frontend/src/components/SprintRoom/SprintRoom.tsx
export function SprintRoom({ roomId }) {
  const [leaderboard, setLeaderboard] = useState([]);
  const [timeRemaining, setTimeRemaining] = useState(1500); // 25 minutes
  const ws = useRef<WebSocket>();

  useEffect(() => {
    ws.current = new WebSocket(`ws://localhost:8000/api/sprint/${roomId}`);

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'leaderboard_update') {
        setLeaderboard(data.leaderboard);
      }
    };
  }, [roomId]);

  return (
    <div className="sprint-room">
      <h2>Sprint in Progress</h2>
      <div className="timer">{formatTime(timeRemaining)}</div>

      <div className="leaderboard">
        {leaderboard.map(([userId, wordCount], i) => (
          <div key={userId} className="leaderboard-item">
            <span>#{i + 1}</span>
            <span>{getUserName(userId)}</span>
            <span>{wordCount} words</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Estimate:** 16 hours

---

#### 4.4 November Writing Challenge (Week 4-6)

**Concept:** Post-NaNoWriMo event to capture displaced writers.

**Features:**
- [ ] Goal setting (50K words in 30 days)
- [ ] Daily progress tracking
- [ ] Badges/achievements
- [ ] Public leaderboard (opt-in)
- [ ] Email reminders

**Marketing:**
- Launch October 15th (2 weeks before NaNoWriMo ends)
- Pitch as "NaNoWriMo alternative without the drama"
- Partner with writing Twitter influencers

**Success Metrics:**
- 5,000 challenge participants
- 1,000 new paid users ($99,000 revenue)
- 500 viral recap card shares

---

### Phase 4 Total Timeline: 6 Weeks
**Total Development Hours:** ~60 hours
**Revenue Target:** $100,000

---

## PLG Features Integration Timeline

### Background Entity Extraction
- **Phase 2, Week 1-2** (Already planned above)

### Aesthetic Recap Engine
- **Phase 4, Week 2-3** (Already planned above)

### Guided BYOK
- **Phase 3, Week 1-2** (Already planned above)

### Multiverse Branching UI
- **Phase 5** (Future enhancement - not critical for launch)

---

## Success Metrics by Phase

| Phase | Revenue Target | User Target | Key Metric |
|-------|---------------|-------------|------------|
| Phase 1 | $2,450 | 100 beta users | 50 lifetime purchases |
| Phase 2 | $50,000 | 1,000 users | 3 YouTuber reviews |
| Phase 3 | $27,000 | 1,500 users | 200 users add AI funds |
| Phase 4 | $100,000 | 6,000 users | 500 viral shares |
| **Total** | **$179,450** | **8,600 users** | **Product-market fit** |

---

## Critical Path Dependencies

```
Phase 1 ──> Phase 2 ──> Phase 3 ──> Phase 4
  (MVP)   (Codex/NLP)    (AI/BYOK)  (Community)
   ↓           ↓            ↓           ↓
 Launch    AuthorTube   Sudowrite   NaNoWriMo
  Beta      Outreach    Alternative   Event
```

**Blocking Issues:**
1. Phase 1 cannot launch until chapter loading + drag-and-drop work
2. Phase 2 needs Phase 1 revenue to fund development
3. Phase 4 needs Phase 2 user base to go viral

---

## Risk Mitigation

### Risk: Not enough beta signups
**Mitigation:** Pre-sell 50 lifetime licenses before launch (Product Hunt "coming soon" page)

### Risk: YouTubers don't respond
**Mitigation:** Offer paid sponsorships ($500 for dedicated video)

### Risk: Viral cards don't get shared
**Mitigation:** A/B test 10 different templates, incentivize sharing (unlock bonus features)

### Risk: AI costs too high for users
**Mitigation:** Offer "AI-free" tier at $49 (just the editor/codex)

---

## Immediate Next Steps (This Week)

### Week 1 Focus (December 25-31, 2025)
**Goal:** Fix critical bugs, prepare for Phase 1 launch

**Monday-Tuesday:**
- [ ] Fix chapter loading in editor (4 hours)
- [ ] Implement basic drag-and-drop (8 hours)

**Wednesday-Thursday:**
- [ ] Add inline rename functionality (4 hours)
- [ ] Add right-click context menu (4 hours)
- [ ] Persist folder expand state (2 hours)

**Friday:**
- [ ] Export to DOCX feature (8 hours)

**Weekend:**
- [ ] Create onboarding flow (4 hours)
- [ ] Write landing page copy (4 hours)
- [ ] Record demo video (4 hours)

**Total:** ~42 hours (manageable in 1 week)

---

## Technical Debt to Address

### High Priority (Before Phase 2)
- [ ] Add proper error boundaries (React)
- [ ] Implement retry logic for API calls
- [ ] Add loading states to all async operations
- [ ] Set up Sentry for crash reporting

### Medium Priority (Before Phase 3)
- [ ] Migrate to React Query for better caching
- [ ] Add proper TypeScript types for all API responses
- [ ] Implement optimistic updates everywhere
- [ ] Add unit tests for critical paths

### Low Priority (After Phase 4)
- [ ] Refactor stores (combine manuscript + chapter stores)
- [ ] Extract common components to design system
- [ ] Performance optimization (lazy loading, code splitting)

---

## Open Questions

1. **Authentication:** Phase 1 is local-only. When do we add user accounts?
   - **Answer:** Phase 3 (needed for AI wallet)

2. **Pricing:** Should we offer monthly subscription option?
   - **Answer:** No, lifetime only. Monthly dilutes the "affordable" positioning.

3. **Mobile:** Do we build iOS/Android apps?
   - **Answer:** Phase 5+. Focus on desktop first (Electron wrapper).

4. **Collaboration:** Multi-user editing (Google Docs style)?
   - **Answer:** Phase 6+. Not critical for solo authors.

---

**Last Updated:** December 24, 2025
**Next Review:** End of Phase 1 (March 2026)
**Document Owner:** Implementation Team
