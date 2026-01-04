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

---

## EXTENDED ROADMAP: THE CREATION ENGINE
**Vision:** Transform Maxwell from writing tool → complete creative development platform
**Based on:** User feedback January 2026
**Timeline:** Phases 4-6+ (Q2 2026 onwards)

---

## Phase 4: Story Structure & Outline Engine
**Timeline:** Months 10-13 (April - July 2026)
**Goal:** AI-powered story structure guidance and outline generation
**Key Feature:** Manuscript Creation Wizard with genre-specific templates

### 4.1 Outline Engine Foundation (Weeks 1-2)
**Database Schema:**
```sql
CREATE TABLE outlines (
    id TEXT PRIMARY KEY,
    manuscript_id TEXT NOT NULL REFERENCES manuscripts(id),
    structure_type TEXT NOT NULL,  -- '3-act', 'save-the-cat', 'km-weiland', etc.
    genre TEXT,  -- 'fantasy', 'thriller', 'romance', etc.
    target_word_count INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE plot_beats (
    id TEXT PRIMARY KEY,
    outline_id TEXT NOT NULL REFERENCES outlines(id),
    beat_name TEXT NOT NULL,  -- 'hook', 'inciting-event', 'midpoint', etc.
    beat_description TEXT,
    target_position_percent REAL,  -- 0.0 to 1.0 (12% = 0.12)
    target_word_count INTEGER,
    actual_word_count INTEGER,
    chapter_id TEXT REFERENCES chapters(id),
    is_completed BOOLEAN DEFAULT FALSE,
    notes TEXT,
    order_index INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**API Endpoints:**
```
POST   /api/outlines                  - Create outline
GET    /api/outlines/:id              - Get outline with beats
PUT    /api/outlines/:id              - Update outline
DELETE /api/outlines/:id              - Delete outline
POST   /api/outlines/:id/beats        - Add plot beat
PUT    /api/outlines/:id/beats/:beatId - Update beat
```

**UI Components:**
- OutlineSidebar (similar to CodexSidebar)
- PlotBeatCard (shows beat, target %, actual %, status)
- StructureTimeline (visual progress bar with beats)
- OutlineEditor (freeform outline editing)

**Estimate:** 2 weeks

---

### 4.2 Story Structure Templates (Weeks 3-4)
**Research & Implement:**

**1. KM Weiland's Structure:**
```typescript
const KM_WEILAND_STRUCTURE = {
  name: "KM Weiland's Story Structure",
  beats: [
    { name: "Hook", position: 0.01, description: "Open with action, intrigue, or character voice that grabs readers" },
    { name: "Inciting Event", position: 0.12, description: "Call to adventure - protagonist's world changes" },
    { name: "First Plot Point", position: 0.25, description: "No turning back - protagonist commits to journey" },
    { name: "First Pinch Point", position: 0.375, description: "Antagonistic force applies pressure" },
    { name: "Midpoint", position: 0.50, description: "Major revelation - protagonist moves from reaction to action" },
    { name: "Second Pinch Point", position: 0.625, description: "Antagonist strikes again - stakes raised" },
    { name: "Third Plot Point", position: 0.75, description: "All is lost - protagonist's lowest point" },
    { name: "Climax", position: 0.88, description: "Final confrontation - protagonist faces antagonist" },
    { name: "Resolution", position: 0.99, description: "New normal - show how world has changed" },
  ]
};
```

**2. Save the Cat:**
```typescript
const SAVE_THE_CAT_STRUCTURE = {
  name: "Save the Cat",
  beats: [
    { name: "Opening Image", position: 0.01, description: "Snapshot of protagonist's flawed life" },
    { name: "Theme Stated", position: 0.05, description: "Lesson protagonist will learn stated by another character" },
    { name: "Setup", position: 0.01-0.10, description: "Introduce protagonist, stakes, and goals" },
    { name: "Catalyst", position: 0.10, description: "Inciting incident - life-changing event" },
    { name: "Debate", position: 0.10-0.20, description: "Protagonist hesitates - should they go?" },
    { name: "Break into Two", position: 0.20, description: "Protagonist leaves old world, enters new" },
    { name: "B Story", position: 0.22, description: "Love story or relationship that will teach theme" },
    { name: "Fun and Games", position: 0.20-0.50, description: "Promise of the premise - story delivers" },
    { name: "Midpoint", position: 0.50, description: "False victory or false defeat" },
    { name: "Bad Guys Close In", position: 0.50-0.75, description: "Complications and obstacles multiply" },
    { name: "All Is Lost", position: 0.75, description: "Lowest point - opposite of midpoint" },
    { name: "Dark Night of the Soul", position: 0.75-0.80, description: "Protagonist processes loss" },
    { name: "Break into Three", position: 0.80, description: "Protagonist finds solution - combines A and B stories" },
    { name: "Finale", position: 0.80-0.99, description: "Protagonist executes plan, faces antagonist" },
    { name: "Final Image", position: 0.99, description: "Opposite of opening image - show transformation" },
  ]
};
```

**3. Hero's Journey:**
```typescript
const HEROS_JOURNEY_STRUCTURE = {
  name: "Hero's Journey (Campbell/Vogler)",
  beats: [
    { name: "Ordinary World", position: 0.01-0.10, description: "Hero's normal life before adventure" },
    { name: "Call to Adventure", position: 0.10, description: "Problem/challenge presented" },
    { name: "Refusal of Call", position: 0.12, description: "Hero hesitates, afraid" },
    { name: "Meeting the Mentor", position: 0.15, description: "Wise figure gives advice/gift" },
    { name: "Crossing Threshold", position: 0.20, description: "Hero commits, enters special world" },
    { name: "Tests, Allies, Enemies", position: 0.20-0.50, description: "Hero faces challenges, builds team" },
    { name: "Approach Inmost Cave", position: 0.50, description: "Hero prepares for major challenge" },
    { name: "Ordeal", position: 0.60, description: "Hero faces greatest fear/death" },
    { name: "Reward", position: 0.65, description: "Hero seizes treasure/knowledge" },
    { name: "Road Back", position: 0.75, description: "Hero must return to ordinary world" },
    { name: "Resurrection", position: 0.85, description: "Final test - hero transformed" },
    { name: "Return with Elixir", position: 0.95, description: "Hero returns home changed, with gift for world" },
  ]
};
```

**Genre-Specific Templates:**
```typescript
const GENRE_DEFAULTS = {
  fantasy: {
    wordCount: 90000,
    recommendedStructures: ['hero-journey', 'km-weiland'],
    specificBeats: ['magic-system-reveal', 'world-rules-established']
  },
  thriller: {
    wordCount: 75000,
    recommendedStructures: ['save-the-cat', 'km-weiland'],
    specificBeats: ['ticking-clock', 'false-lead']
  },
  romance: {
    wordCount: 70000,
    recommendedStructures: ['save-the-cat', 'romance-arc'],
    specificBeats: ['meet-cute', 'first-kiss', 'black-moment', 'grand-gesture']
  },
  scifi: {
    wordCount: 85000,
    recommendedStructures: ['hero-journey', 'km-weiland'],
    specificBeats: ['tech-reveal', 'world-building-info-dump']
  },
  mystery: {
    wordCount: 70000,
    recommendedStructures: ['save-the-cat', 'mystery-structure'],
    specificBeats: ['crime-discovered', 'red-herring', 'true-villain-revealed']
  }
};
```

**Estimate:** 2 weeks

---

### 4.3 Manuscript Creation Wizard (Weeks 5-6)
**User Flow:**

**Step 1: Genre Selection**
```
What type of story are you writing?
[ ] Fantasy
[ ] Science Fiction
[ ] Thriller/Suspense
[ ] Romance
[ ] Mystery/Detective
[ ] Historical Fiction
[ ] Literary Fiction
[ ] Horror
[ ] Young Adult
[ ] Other

<Info box>
Genre helps Maxwell suggest appropriate story structures,
pacing, and word count targets.
</Info box>
```

**Step 2: Structure Selection**
```
Choose a story structure template:

⭐ Recommended for Fantasy:

○ Hero's Journey (Classic Adventure)
  12 stages | Perfect for epic quests
  Examples: Lord of the Rings, Star Wars

○ KM Weiland's Structure (Detailed Blueprint)
  9 major beats | Precise percentages
  Examples: Most bestsellers

[ ] I'll create my own structure
[ ] Skip - I prefer to freewrite

<Preview button> See template details
```

**Step 3: AI Outline Generation**
```
Let's build your story outline!

Maxwell will ask you questions about your story and
generate plot beat suggestions.

Ready to begin? [Start Outline Wizard]
```

**Step 4: AI-Powered Q&A** (uses OpenRouter)
```
Question 1/5: What's your protagonist's goal?

<textarea>
Example: "Destroy the One Ring to save Middle-earth"
Example: "Solve her sister's murder before the killer strikes again"
</textarea>

[🤖 AI Suggestions] Based on your genre (Fantasy), here are
common protagonist goals:
- Defeat an ancient evil threatening the kingdom
- Master forbidden magic to save loved ones
- Unite warring factions against common enemy
- Discover true identity/heritage

[Next Question]
```

**Step 5: Generate Outline**
```
Creating your outline...

✓ Analyzing your inputs
✓ Applying Hero's Journey structure
✓ Generating plot beat suggestions

Your outline is ready! [View Outline] [Start Writing]
```

**Implementation:**
```typescript
// OutlineWizard.tsx
const OutlineWizard = ({ onComplete }) => {
  const [step, setStep] = useState(1);
  const [genre, setGenre] = useState('');
  const [structure, setStructure] = useState('');
  const [answers, setAnswers] = useState({});

  const questions = [
    {
      id: 'protagonist-goal',
      text: "What's your protagonist's main goal?",
      aiPrompt: `Based on ${genre} genre, suggest 4 common protagonist goals`
    },
    {
      id: 'antagonist',
      text: "Who or what opposes your protagonist?",
      aiPrompt: `Based on ${genre} and protagonist goal "${answers['protagonist-goal']}", suggest antagonist types`
    },
    {
      id: 'stakes',
      text: "What happens if your protagonist fails?",
      aiPrompt: `Suggest high-stakes consequences for ${genre} story`
    },
    {
      id: 'setting',
      text: "Where and when does your story take place?",
      aiPrompt: `Suggest interesting ${genre} settings`
    },
    {
      id: 'unique-element',
      text: "What makes your story unique?",
      aiPrompt: `Suggest unique twists for ${genre} with these elements: ${JSON.stringify(answers)}`
    }
  ];

  const generateOutline = async () => {
    const apiKey = localStorage.getItem('openrouter_api_key');
    const model = localStorage.getItem('openrouter_model') || 'anthropic/claude-3.5-sonnet';

    // Call AI to generate plot beats
    const response = await fetch('/api/outlines/generate', {
      method: 'POST',
      body: JSON.stringify({
        genre,
        structure,
        answers,
        apiKey,
        model
      })
    });

    const outline = await response.json();
    onComplete(outline);
  };
};
```

**Backend Outline Generation:**
```python
# /backend/app/api/routes/outlines.py
@router.post("/generate")
async def generate_outline(request: GenerateOutlineRequest):
    """Use AI to generate plot beat suggestions"""

    openrouter = OpenRouterService(request.api_key)

    system_prompt = f"""You are a story structure expert helping a writer
create an outline for their {request.genre} novel using the
{request.structure} structure.

Based on their answers, generate specific, creative suggestions for
each plot beat."""

    user_prompt = f"""
Story Details:
- Genre: {request.genre}
- Structure: {request.structure}
- Protagonist Goal: {request.answers['protagonist-goal']}
- Antagonist: {request.answers['antagonist']}
- Stakes: {request.answers['stakes']}
- Setting: {request.answers['setting']}
- Unique Element: {request.answers['unique-element']}

Generate specific plot beat suggestions for this story using the
{request.structure} structure. For each beat, provide:
1. Beat name
2. Suggested scene/event
3. How it relates to protagonist's goal

Format as JSON with this structure:
{{
  "beats": [
    {{
      "name": "Hook",
      "suggestion": "Open with protagonist in middle of...",
      "position": 0.01
    }},
    ...
  ]
}}
"""

    result = await openrouter.get_writing_suggestion(
        text=user_prompt,
        context=system_prompt,
        suggestion_type='outline',
        max_tokens=2000
    )

    if result['success']:
        # Parse AI response and create outline
        beats_data = json.loads(result['suggestion'])

        # Create outline in database
        outline = create_outline(
            manuscript_id=request.manuscript_id,
            genre=request.genre,
            structure=request.structure,
            beats=beats_data['beats']
        )

        return outline
```

**Estimate:** 2 weeks

---

### 4.4 Story Structure Checkpoints (Weeks 7-8)
**Real-time guidance based on word count**

**Progress Dashboard:**
```
┌─────────────────────────────────────────────────────────────┐
│ Your Progress: "The Shadow Kingdom"                        │
│ Genre: Fantasy | Structure: Hero's Journey                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Words: 32,450 / 90,000 (36%)                              │
│ ████████████░░░░░░░░░░░░░░░░░░░░░░░░                      │
│                                                             │
│ ✓ Hook (1%)           - Completed                          │
│ ✓ Ordinary World (10%) - Completed                         │
│ ✓ Call to Adventure (12%) - Completed                      │
│ ⚠ Crossing Threshold (20%) - Approaching (18,000 words)   │
│ ○ Approach Inmost Cave (50%) - Upcoming                    │
│ ○ Ordeal (60%) - Upcoming                                  │
│ ○ Resurrection (85%) - Upcoming                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘

[View Full Outline] [Mark Beat Complete] [Get AI Suggestions]
```

**Checkpoint Notifications:**
```typescript
// CheckpointNotifier.tsx
const CheckpointNotifier = ({ outline, currentWordCount }) => {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    const targetWordCount = outline.target_word_count;
    const currentPercent = currentWordCount / targetWordCount;

    // Find upcoming checkpoint
    const nextBeat = outline.beats.find(beat =>
      !beat.is_completed &&
      beat.target_position_percent > currentPercent &&
      beat.target_position_percent - currentPercent < 0.05 // Within 5%
    );

    if (nextBeat) {
      showNotification({
        title: `Approaching: ${nextBeat.beat_name}`,
        message: `You're at ${(currentPercent * 100).toFixed(0)}%, approaching ${nextBeat.beat_name} (${(nextBeat.target_position_percent * 100).toFixed(0)}%). Expected around ${nextBeat.target_word_count} words.`,
        description: nextBeat.beat_description,
        action: 'Get AI Suggestions'
      });
    }

    // Check for missed checkpoints
    const missedBeats = outline.beats.filter(beat =>
      !beat.is_completed &&
      currentPercent > beat.target_position_percent + 0.10 // 10% past
    );

    if (missedBeats.length > 0) {
      showWarning({
        title: 'Checkpoint Missed',
        message: `You may have missed the "${missedBeats[0].beat_name}" beat (expected at ${(missedBeats[0].target_position_percent * 100).toFixed(0)}%, you're at ${(currentPercent * 100).toFixed(0)}%).`,
        suggestion: 'Consider adding a flashback or scene to include this story beat, or mark it as intentionally skipped.'
      });
    }
  }, [currentWordCount, outline]);
};
```

**AI Beat Analysis:**
```
[User clicks "Get AI Suggestions" at 36% mark]

🤖 AI Analysis

Based on your story so far (32,450 words), you're approaching the
"Crossing the Threshold" beat (expected ~18,000 words / 20%).

Your protagonist should:
✓ Make an irrevocable decision
✓ Enter the "special world" of the adventure
✓ Leave behind the ordinary world

Suggestions for your story:
1. Have [Protagonist] cross the magical barrier into the Shadow Realm
2. Show the moment they accept the quest from the Council
3. Create a scene where burning bridges with [home/family] is final

Would you like me to:
[ ] Generate a detailed scene outline
[ ] Suggest dialogue for this moment
[ ] Analyze if you've already included this beat

[Generate Ideas]
```

**Estimate:** 2 weeks

---

### 4.5 Outline-to-Chapters Generator (Week 9)
**Auto-generate chapter structure from outline**

**UI:**
```
Your outline has 12 plot beats. Would you like Maxwell to
suggest a chapter structure?

Target: 90,000 words / 30 chapters = ~3,000 words per chapter

Suggested Structure:

Act 1 (25% / 22,500 words)
  Chapter 1-2: Hook + Ordinary World (6,000 words)
  Chapter 3-4: Call to Adventure + Refusal (6,000 words)
  Chapter 5-7: Meeting Mentor + Crossing Threshold (10,500 words)

Act 2A (25% / 22,500 words)
  Chapter 8-12: Tests, Allies, Enemies (15,000 words)
  Chapter 13-14: Approach Inmost Cave (7,500 words)

Act 2B (25% / 22,500 words)
  Chapter 15-16: Ordeal (6,000 words)
  Chapter 17-19: Reward + Road Back (10,500 words)
  Chapter 20-21: All Is Lost (6,000 words)

Act 3 (25% / 22,500 words)
  Chapter 22-25: Resurrection (12,000 words)
  Chapter 26-30: Return with Elixir + Resolution (10,500 words)

[Generate Chapters] [Customize] [Skip]
```

**Implementation:**
```typescript
const generateChapterStructure = async (outline: Outline) => {
  const totalWords = outline.target_word_count;
  const avgChapterWords = 3000;
  const estimatedChapters = Math.round(totalWords / avgChapterWords);

  // Distribute chapters across beats
  const beats = outline.beats;
  const chaptersPerBeat = estimatedChapters / beats.length;

  for (let beat of beats) {
    const beatWords = totalWords * (beat.target_position_percent);
    const beatChapters = Math.round(chaptersPerBeat);

    for (let i = 0; i < beatChapters; i++) {
      await chaptersApi.create({
        manuscript_id: outline.manuscript_id,
        title: `Chapter ${chapterCount} - ${beat.beat_name}`,
        is_folder: false,
        plot_beat_id: beat.id,
        order_index: chapterCount++
      });
    }
  }
};
```

**Estimate:** 1 week

---

### Phase 4 Success Metrics
- [ ] 70% of new users complete outline wizard
- [ ] Average outline completion time < 15 minutes
- [ ] 50% of outlines generate chapter structures
- [ ] Checkpoint notifications increase daily writing by 20%
- [ ] Users with outlines have 2x higher manuscript completion rate

**Total Phase 4 Estimate:** 9 weeks

---

## Phase 5: Brainstorming & Ideation Tools
**Timeline:** Months 14-17 (August - November 2026)
**Goal:** Help writers generate ideas, develop characters, and overcome creative blocks
**Research Foundation:** Brandon Sanderson lectures, KM Weiland resources

### 5.1 Idea Generator (Weeks 1-2)
**Prompt Library:**
```typescript
const IDEA_PROMPTS = {
  character: [
    "What if your protagonist had the opposite flaw you'd expect?",
    "Combine two character archetypes that never go together",
    "Give your villain a sympathetic motivation",
    "What secret would destroy your protagonist if revealed?"
  ],
  plot: [
    "What's the worst thing that could happen to your protagonist?",
    "Flip your ending - what if the antagonist won?",
    "Add a ticking clock element",
    "What if the mentor betrays the protagonist?"
  ],
  world: [
    "What if magic had a physical cost?",
    "Invert one law of physics in your world",
    "What if a modern technology existed in a historical setting?",
    "Create a society with an unusual taboo"
  ],
  conflict: [
    "Force your protagonist to choose between two good options",
    "Create a moral dilemma with no right answer",
    "What external conflict reflects internal conflict?",
    "Add a deadline that forces immediate action"
  ]
};
```

**AI Idea Generation:**
```
💡 Brainstorming: Character Ideas

[User clicks "Generate Ideas"]

🤖 Based on your fantasy setting:

1. **The Guilt-Ridden Healer**
   A medic who can heal any wound but absorbs the pain
   themselves. Struggles with addiction to pain-numbing potions.

2. **The Literal-Minded Fae**
   An ancient creature who interprets human speech exactly as
   spoken, leading to dangerous misunderstandings.

3. **The Exiled Royal Inventor**
   Banished for creating dangerous technology, now forced to
   help rebels overthrow their own family.

4. **The Amnesiac Oracle**
   Can see everyone's future except their own past.

[Save to Codex] [Combine Ideas] [Generate More] [Customize]

Which character interests you most?
I can develop their backstory, relationships, and arc.
```

**Estimate:** 2 weeks

---

### 5.2 Mind Mapping Tool (Weeks 3-4)
**Visual idea connections**

```
[Brainstorming Mind Map]

                     [Main Character]
                           |
            +--------------+---------------+
            |              |               |
        [Goal]       [Flaw]           [Strength]
            |              |               |
      "Save Sister"  "Too Trusting"   "Clever"
            |
            +--[Obstacle]
                    |
              "Villain Lies"
                    |
              [How villain uses flaw]
```

**Features:**
- Drag-and-drop nodes
- Connect related ideas
- Export to Codex entities
- AI suggestion for missing connections
- Collaborative brainstorming (future)

**Estimate:** 2 weeks

---

### 5.3 Character Development Worksheets (Week 5)
**Brandon Sanderson-inspired exercises**

```
Character Profile: [Character Name]

## Core Attributes
What they Want: ___________________________________
What they Need: ___________________________________
Their Flaw: ______________________________________
Their Strength: __________________________________

## Brandon Sanderson's Triangle
     Goal
      /\
     /  \
    /    \
   /      \
  / Flaw  Strength \
 /__________________\

Conflict: How flaw prevents achieving goal
Arc: How strength + lessons learned = achievement

## Quick Questions
- What do they lie about?
- What makes them laugh?
- What's their greatest fear?
- What would they die for?
- What's their secret shame?

[🤖 AI Analysis]
Based on your answers, this character is a:
[Reluctant Hero] archetype with [Trust Issues] as primary obstacle.

Suggested arc: Learns to accept help → allies prove trustworthy →
               overcomes final challenge with team
```

**Estimate:** 1 week

---

### 5.4 World-Building Templates (Weeks 6-8)
**Structured world development**

```
🗺️ World Builder: Fantasy Kingdoms

## Geography
Climate: [Temperate / Tropical / Arctic / Desert]
Terrain: [Mountains / Plains / Islands / Underground]
Key Locations:
  - Capital City: ___________________________
  - Forbidden Zone: _________________________
  - Sacred Site: ____________________________

## Society
Government: [Monarchy / Republic / Theocracy / Anarchy]
Social Classes: ______________________________
Currency: ___________________________________
Major Conflicts: ____________________________

## Magic System (Sanderson's Laws)
Source of Power: ____________________________
Limitations: ________________________________
Cost/Price: _________________________________
Who can use it: _____________________________
Societal Impact: ____________________________

## Culture
Religion: ___________________________________
Taboos: _____________________________________
Holidays: ___________________________________
Coming-of-age ritual: _______________________

[🤖 AI Assistant]
Need help filling in gaps? I can:
- Suggest magic system limitations
- Generate cultural details
- Create naming conventions for your world
- Identify potential plot conflicts from world rules
```

**Estimate:** 3 weeks

---

### Phase 5 Success Metrics
- [ ] 60% of users use Idea Generator
- [ ] Mind maps created: 500+/month
- [ ] Character worksheets completed: 1,000+/month
- [ ] Users report "less writer's block" (survey)

**Total Phase 5 Estimate:** 8 weeks

---

## Phase 6: The Full Creation Engine
**Timeline:** Months 18+ (December 2026 onwards)
**Goal:** Comprehensive creative platform from idea → finished novel
**This is the NORTH STAR - continuous development**

### 6.1 Advanced World Builder (Months 18-20)
- Interactive maps (drag-and-drop locations)
- Timeline of historical events
- Political relationship graphs
- Economic systems modeling
- Culture generators

### 6.2 Magic System Designer (Months 21-22)
- Sanderson's Laws compliance checker
- Power scaling calculator
- Visual effect descriptions
- Cultural integration analyzer
- Limitation/cost tracker

### 6.3 Character Relationship Network (Month 23)
- Dynamic relationship graph (like Codex, but advanced)
- Relationship evolution over time
- Conflict tracker between characters
- Automatic relationship consistency checking

### 6.4 Advanced AI Creative Assistant (Months 24-30)
- Context-aware gap filling
- "What if?" scenario generator
- Character voice consistency checker
- Plot hole detector
- Foreshadowing tracker
- Theme consistency analyzer

### 6.5 Scene-Level Guidance (Months 31-36)
- Real-time scene structure feedback
- Pacing analysis (MRUs - Motivation-Reaction Units)
- Dialogue attribution best practices
- Show vs. tell detector
- Sensory details suggester

### 6.6 Integration & Polish (Ongoing)
- **Inline Reference Panel:** Show relevant outline sections while writing
- **Quick Access Codex:** Character/world details in sidebar
- **Contextual AI Suggestions:** Based on outline + world rules + character voices
- **Automatic Continuity Checking:** Flag inconsistencies with established lore

---

## Updated Timeline Overview

| Phase | Timeline | Key Deliverable | Status |
|-------|----------|----------------|--------|
| Phase 1 | Months 1-3 (Q1 2026) | MVP Launch | ✅ Complete |
| Phase 2 | Months 4-6 (Q1-Q2) | PLG Growth | ✅ Complete |
| Phase 3 | Months 7-9 (Q2-Q3) | AI Integration (BYOK) | ✅ Complete |
| **Phase 4** | **Months 10-13 (Q3)** | **Story Structure Engine** | 🔄 Planned |
| **Phase 5** | **Months 14-17 (Q4)** | **Brainstorming Tools** | 📋 Planned |
| **Phase 6+** | **Months 18+ (2027)** | **Full Creation Engine** | 🎯 Vision |

---

## Success Criteria: The Full Creation Engine

**When Maxwell becomes indispensable:**
1. ✅ Writers can brainstorm ideas → AI helps generate options
2. ✅ Writers can outline → AI suggests plot beats
3. ✅ Writers can draft → Real-time structure guidance
4. ✅ Writers can revise → Consistency checking across entire manuscript
5. ✅ Writers can finish → Export, publish, share

**Metrics:**
- Time from idea → first draft: 30% faster
- Manuscript completion rate: 3x industry average
- User retention: 80%+ after 6 months
- NPS Score: 70+

---

## Research Resources (Must Study)

### Story Structure
- [ ] KM Weiland: "Structuring Your Novel"
- [ ] Blake Snyder: "Save the Cat"
- [ ] Christopher Vogler: "The Writer's Journey"
- [ ] Shawn Coyne: "The Story Grid"

### Brainstorming & Craft
- [ ] Brandon Sanderson: BYU Creative Writing Lectures (YouTube)
- [ ] Brandon Sanderson: "Sanderson's Laws of Magic"
- [ ] James Scott Bell: "Plot & Structure"
- [ ] Donald Maass: "The Emotional Craft of Fiction"

### Worldbuilding
- [ ] Brandon Sanderson: Worldbuilding Lectures
- [ ] Timothy Hickson: "On Writing and Worldbuilding"
- [ ] r/worldbuilding community resources

### Competitor Analysis
- [ ] Sudowrite - AI creative assistant patterns
- [ ] NovelAI - AI storytelling UX
- [ ] Plottr - Outline/timeline visualization
- [ ] Campfire - World-building tools

---

## Open Questions for Phase 4-6

1. **Outline Ownership:** Should outlines be mandatory or optional?
   - **Recommendation:** Optional. Some writers are discovery writers (pantsers).
   - **Solution:** Offer "Guided" vs "Freeform" manuscript creation paths.

2. **AI Cost Management:** Complex outline generation uses many tokens
   - **Recommendation:** Budget estimates in wizard ("This will cost ~$0.10-0.50")
   - **Alternative:** Offer pre-generated templates for free, custom AI generation paid

3. **Template Licensing:** Can we include copyrighted story structures?
   - **Recommendation:** Use public domain structures (Hero's Journey, 3-Act)
   - **Solution:** Paraphrase commercial structures (Save the Cat, KM Weiland) without copying text

4. **Integration Complexity:** How do outline, codex, timeline, brainstorming all connect?
   - **Recommendation:** Unified "Project" view showing all creative documents
   - **Solution:** Phase 6+ unification layer

---

**Last Updated:** January 3, 2026
**Next Review:** End of Phase 3 (March 2026)
**Document Owner:** Implementation Team

**Changes from v2.0:**
- Added Phases 4-6+ (Creation Engine roadmap)
- Incorporated user feedback (Story structure, brainstorming, world-building)
- Research resources identified
- Timeline extended through 2027+
