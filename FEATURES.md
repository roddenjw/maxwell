# Maxwell Features Guide

This document provides user guides and technical overviews for Maxwell's major features. For architecture details, see [CLAUDE.md](./CLAUDE.md). For implementation status, see [PROGRESS.md](./PROGRESS.md).

**Last Updated:** 2026-01-07

---

## Table of Contents

1. [Time Machine (Version Control)](#1-time-machine-version-control)
2. [Fast Coach (Writing Feedback)](#2-fast-coach-writing-feedback)
3. [AI Integration (OpenRouter BYOK)](#3-ai-integration-openrouter-byok)
4. [Recap Engine (Chapter Summaries)](#4-recap-engine-chapter-summaries)

---

## 1. Time Machine (Version Control)

**Status:** ✅ Complete (Phase 1)

Maxwell's Time Machine provides Git-backed version control with a visual interface designed for writers, not developers. No Git knowledge required.

### Features

**Snapshots:**
- Manual snapshots with custom labels
- Automatic snapshots every 5 minutes (configurable)
- Pre-restore backup snapshots (safety net)
- Snapshot metadata: timestamp, word count, trigger type

**Version History:**
- Timeline view of all snapshots
- Organized by date and trigger type
- Word count tracking across versions
- Quick navigation to any point in history

**Diff Viewer:**
- Visual comparison between any two versions
- Green highlights for additions
- Red highlights for deletions
- Side-by-side or unified diff views

**Restore:**
- One-click restoration to any previous version
- Automatic backup before restore
- Safe rollback: never lose work

### How to Use

**Creating Manual Snapshots:**

1. Open Time Machine (clock icon ⏰ in top-right header)
2. Click **"+ Create Snapshot"** button
3. Enter a descriptive label (e.g., "Chapter 3 - First Draft")
4. Click OK
5. Snapshot appears in timeline immediately

**Viewing Snapshot History:**

1. Open Time Machine
2. Scroll through timeline in left sidebar
3. Each snapshot shows:
   - Label/description
   - Date and time
   - Word count
   - Trigger type badge (Manual, Auto, Pre-restore)

**Comparing Versions (Diff Viewer):**

1. Select a snapshot in the timeline
2. Click **"View Changes"** button
3. Diff viewer shows changes:
   - `<ins>` tags (green) = additions
   - `<del>` tags (red) = deletions
4. Click "Close Diff" to return to timeline

**Restoring Previous Versions:**

1. Select the snapshot you want to restore
2. Click **"Restore"** button
3. Confirm restoration in dialog
4. Current work is automatically backed up as "Pre-restore backup"
5. Editor reloads with restored content

### Technical Details

**Architecture:**

Maxwell uses Git under the hood (via pygit2) with one repository per manuscript.

**Storage Location:**
```
/data/manuscripts/{manuscript_id}/.git
```

**Backend:**
- Service: `backend/app/services/version_service.py`
- Models: `backend/app/models/versioning.py` (Snapshot)
- Routes: `backend/app/api/routes/versioning.py`

**API Endpoints:**
```bash
# Create snapshot
POST /api/versioning/snapshots
{
  "manuscript_id": "string",
  "content": "string",
  "trigger_type": "MANUAL|AUTO|SAVE|RESTORE",
  "label": "string",
  "word_count": number
}

# List snapshots
GET /api/versioning/snapshots/{manuscript_id}

# Restore snapshot
POST /api/versioning/restore
{
  "manuscript_id": "string",
  "snapshot_id": "string",
  "create_backup": boolean
}

# Get diff between versions
POST /api/versioning/diff
{
  "manuscript_id": "string",
  "from_snapshot_id": "string",
  "to_snapshot_id": "string"
}
```

**Frontend:**
- Component: `frontend/src/components/TimeMachine/TimeMachineSidebar.tsx`
- Store: `frontend/src/stores/versionStore.ts`
- Plugin: `frontend/src/components/Editor/plugins/AutoSavePlugin.tsx` (auto-snapshots)

**Auto-Snapshot Behavior:**
- Triggered every 5 minutes after last edit
- Only creates snapshot if content changed
- Debounced to avoid excessive snapshots
- Configurable interval in editor settings

**Performance:**
- Snapshot creation: < 100ms (Git commit)
- Snapshot listing: < 50ms (SQLite query)
- Diff generation: < 200ms (Git diff)
- Restoration: < 150ms (Git checkout + DB update)

### Best Practices

**When to Create Manual Snapshots:**
- Before major revisions
- After completing a chapter/scene
- Before deleting large sections
- When reaching milestones

**Label Naming:**
- Use descriptive labels: "Chapter 3 - First Draft"
- Include version numbers: "v1.0", "v2.0 - after beta feedback"
- Note major changes: "Removed subplot A", "Added character backstory"

**Snapshot Management:**
- Review snapshots monthly and delete unnecessary auto-saves
- Keep major milestone snapshots
- Use labels to identify important versions

---

## 2. Fast Coach (Writing Feedback)

**Status:** ✅ Complete (Phase 3)

Fast Coach provides instant writing feedback without AI API calls. It's a Python-based real-time analyzer that detects common writing issues as you type.

### Features

**Style Analysis:**
- Sentence length variance (monotony detection)
- Passive voice detection (>30% threshold warning)
- Adverb density checking (-ly words)
- Paragraph length analysis (>200 words warning)

**Word Choice Analysis:**
- Weak intensifiers: just, really, very, quite, actually, basically, literally
- "Telling" verbs: felt, thought, knew, realized, wondered, seemed
- Filter words: started to, began to, seemed to, appeared to
- Word repetition detection (within 20-word proximity)
- Cliché pattern matching

**Consistency Checking:**
- Character attribute validation (eye color, hair color, age)
- Entity mention detection via spaCy NER
- Codex integration for entity data
- Age consistency (±2 year tolerance)

**Feedback Organization:**
- Grouped by severity: Errors → Warnings → Tips
- Expandable suggestion cards
- Dismiss functionality
- Active suggestion count

### How to Use

**Activating Fast Coach:**

1. Open any manuscript in the editor
2. Click **"✨ Coach"** toggle button in header
3. Fast Coach sidebar appears on the right
4. Start typing to receive real-time feedback

**Reading Suggestions:**

1. Suggestions appear automatically as you write
2. Grouped into three categories:
   - **🔴 Errors** - Critical issues (e.g., consistency errors)
   - **🟡 Warnings** - Style improvements (e.g., passive voice)
   - **🟢 Tips** - Best practices (e.g., word choice)
3. Click to expand suggestion for details
4. Read the explanation and suggested fix

**Dismissing Suggestions:**

1. Click the "×" button on any suggestion
2. Suggestion is removed from sidebar
3. Won't reappear for same text
4. Cleared on document reload

**Debounced Analysis:**

Fast Coach waits 1 second after you stop typing before analyzing. This prevents lag while typing.

### Technical Details

**Backend Architecture:**

**Services:**
- `backend/app/services/fast_coach/style_analyzer.py` - Style issues
- `backend/app/services/fast_coach/word_analyzer.py` - Word choice
- `backend/app/services/fast_coach/consistency_checker.py` - Entity consistency

**API Endpoints:**
```bash
# Analyze text
POST /api/fast-coach/analyze
{
  "text": "string",
  "manuscript_id": "string (optional)",
  "check_consistency": boolean
}

# Response
{
  "suggestions": [
    {
      "type": "WORD_CHOICE|STYLE|CONSISTENCY|...",
      "severity": "ERROR|WARNING|INFO",
      "message": "string",
      "suggestion": "string",
      "highlight_word": "string",
      "metadata": {}
    }
  ],
  "stats": {
    "total_suggestions": number,
    "by_type": {},
    "by_severity": {}
  }
}

# Health check
GET /api/fast-coach/health
```

**Frontend:**
- Plugin: `frontend/src/components/Editor/plugins/FastCoachPlugin.tsx`
- Sidebar: `frontend/src/components/FastCoach/FastCoachSidebar.tsx`
- Store: `frontend/src/stores/fastCoachStore.ts`

**Performance:**
- Analysis time: < 100ms for typical chapters (500-1000 words)
- Debounce: 1 second after typing stops
- Non-blocking: runs in background, doesn't freeze editor

**Dependencies:**
- NLTK (sentence tokenization)
- spaCy (entity recognition)
- Python standard library (regex)

**Installation (if needed):**
```bash
pip install nltk numpy

# Download NLTK data
python -m nltk.downloader punkt punkt_tab
```

### Example Analysis

**Input Text (165 words):**
```
The door was opened by the mysterious stranger who had been waiting
outside for hours. She really really really really thought the
situation was very interesting. He felt sad about leaving. She felt
angry at the betrayal. They felt confused about what happened next.
He began to walk away slowly. She started to follow him reluctantly.
```

**Detected Issues:**
1. **High adverb density** (9 -ly words in 165 total)
2. **Weak word: "really"** used 5 times
3. **Telling verb: "felt"** used 4 times
4. **Filter words** (began to, started to)
5. **Word repetition** ("really" within 1 word, "felt" within 6 words)
6. **Passive voice** ("was opened by")

**Total:** 6 suggestions across 4 analyzer types

---

## 3. AI Integration (OpenRouter BYOK)

**Status:** ✅ Complete (Phase 3)

Maxwell integrates with OpenRouter to provide AI-powered writing suggestions. BYOK (Bring Your Own Key) pattern gives users complete control over AI usage and costs.

### Features

**OpenRouter Integration:**
- Access to 100+ AI models (Claude, GPT-4, Llama, Gemini, etc.)
- Pay-as-you-go pricing (no subscription)
- User controls own API key and costs
- Privacy: API keys never sent to Maxwell servers
- Transparent usage tracking and cost calculation

**AI Suggestion Types:**
- **General:** Overall writing quality and engagement
- **Dialogue:** Character voice and conversation flow
- **Pacing:** Scene tension and narrative momentum
- **Description:** Sensory details and imagery
- **Character:** Consistency and development
- **Style:** Prose style and word choice
- **Consistency:** Plot logic and continuity

**Usage Tracking:**
- Token count per request (prompt + completion)
- Estimated cost calculation
- Running total in localStorage
- Per-model pricing (varies by model)

### How to Use

**Setting Up Your API Key:**

1. Get an OpenRouter API key:
   - Visit https://openrouter.ai/
   - Sign up for free account
   - Add credits ($5-$20 recommended)
   - Copy your API key from dashboard

2. Add key to Maxwell:
   - Open any manuscript
   - Click **⚙️ Settings** button in sidebar footer
   - Click **"OpenRouter Settings"** tab
   - Paste your API key
   - Click **"Test Key"** to validate
   - Click **"Save"** to store in browser

**Getting AI Suggestions:**

1. Open Fast Coach sidebar (**✨ Coach** button)
2. Write at least 50 characters in the editor
3. Scroll to **"AI Suggestions"** section
4. Select suggestion type (General, Dialogue, Pacing, etc.)
5. Click **"✨ Get AI Suggestion"**
6. Wait 3-10 seconds for analysis
7. Read AI-generated feedback
8. Usage and cost automatically tracked

**Viewing Usage Stats:**

1. Open Settings (⚙️)
2. Go to "OpenRouter Settings" tab
3. See usage statistics:
   - Total tokens used
   - Estimated total cost
   - Number of requests
4. Reset stats anytime with "Clear Usage"

**Removing Your API Key:**

1. Open Settings (⚙️)
2. Click **"Remove Key"** button
3. API key deleted from browser localStorage
4. Usage stats cleared

### Technical Details

**Backend Architecture:**

**Service:** `backend/app/services/openrouter_service.py`

```python
class OpenRouterService:
    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"

    async def validate_api_key(api_key: str) -> Dict[str, Any]
    async def get_writing_suggestion(
        text: str,
        context: str,
        suggestion_type: str,
        api_key: str,
        model: str = DEFAULT_MODEL
    ) -> Dict

    @staticmethod
    def calculate_cost(usage: Dict, model: str) -> float
```

**API Endpoints:**
```bash
# Get AI suggestion
POST /api/fast-coach/ai-analyze
{
  "text": "string (excerpt to analyze)",
  "api_key": "string (user's OpenRouter key)",
  "manuscript_id": "string (optional)",
  "context": "string (optional)",
  "suggestion_type": "general|dialogue|pacing|..."
}

# Response
{
  "success": true,
  "suggestion": "AI-generated suggestion text",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 300,
    "total_tokens": 450
  },
  "cost": 0.0045  # in USD
}

# Validate API key
POST /api/fast-coach/test-api-key
{
  "api_key": "string"
}

# Response
{
  "valid": true,
  "limit": 10.50,
  "usage": 2.35
}
```

**Frontend:**
- Settings: `frontend/src/components/Settings/SettingsModal.tsx`
- AI Panel: `frontend/src/components/FastCoach/AISuggestionsPanel.tsx`
- Store: `frontend/src/stores/fastCoachStore.ts`

**Security:**
- API keys stored in browser localStorage only
- Never sent to Maxwell backend except in request body
- Never logged or persisted on server
- User can remove key anytime

**Cost Estimation:**

OpenRouter pricing varies by model:
- Claude 3.5 Sonnet: ~$3 per 1M tokens
- GPT-4: ~$30 per 1M tokens (input) / $60 per 1M (output)
- Llama 3.1: ~$0.18 per 1M tokens (very cheap!)

**Example costs:**
- 500-word analysis: ~$0.002-0.005 (less than a penny)
- 100 analyses: ~$0.20-0.50
- Daily writing session (10 analyses): ~$0.02-0.05

**Error Handling:**
- Timeout protection (30s max)
- Graceful degradation (shows error, doesn't crash)
- Invalid key detection
- Network error handling
- Rate limit detection

### Privacy & Data Handling

**Your API Key:**
- Stored in browser localStorage only
- Never sent to Maxwell servers
- Never logged or tracked
- Removed when you click "Remove Key"

**Your Text:**
- Sent directly to OpenRouter (not Maxwell servers)
- Only the excerpt you analyze (not full manuscript)
- Not stored by OpenRouter (per their privacy policy)
- Not used to train models (Claude policy)

**Usage Data:**
- Token counts stored in browser localStorage
- Never sent to Maxwell servers
- You can reset anytime

**Maxwell's Approach:**
We believe writers should control their own AI usage. By using BYOK, you:
- Choose which model to use
- See exactly what it costs
- Keep your API key private
- Can stop anytime

---

## 4. Recap Engine (Chapter Summaries)

**Status:** ✅ Complete (Phase 3)

The Recap Engine uses Claude AI to generate structured chapter summaries. Perfect for reviewing what happened before continuing your story.

### Features

**Summary Components:**
- **Summary:** 2-3 sentence overview
- **Key Events:** 3-5 major plot points (numbered list)
- **Character Developments:** How characters change/reveal themselves
- **Themes:** Major thematic elements
- **Emotional Tone:** Chapter's emotional atmosphere
- **Narrative Arc:** Where chapter sits in story structure
- **Memorable Moments:** Standout scenes or lines

**Smart Caching:**
- First generation: 10-20 seconds (Claude API call)
- Cached retrieval: Instant (<0.1 seconds)
- Auto-invalidation: Regenerates if chapter content changes
- Cache indicator: Shows when recap was generated

### How to Use

**Generating a Recap:**

1. Open a chapter in the editor
2. Click **"📖 Recap"** button in toolbar
3. Wait 10-20 seconds for AI analysis (first time)
4. View structured recap in modal

**Regenerating a Recap:**

If you've edited your chapter and want fresh insights:

1. Open the Recap modal
2. Click **"Regenerate Recap"** at bottom
3. Wait for new analysis
4. See updated insights based on current content

**Viewing Cached Recaps:**

- Recaps are automatically cached after first generation
- Open Recap modal to instantly view cached version
- No API call needed for cached recaps
- Cache invalidates when chapter content changes

### Technical Details

**Backend:**

**API Endpoints:**
```bash
# Generate or retrieve recap
POST /api/recap/chapter/{chapter_id}
{
  "regenerate": boolean  # Force new generation
}

# Response
{
  "summary": "string",
  "key_events": ["event1", "event2", ...],
  "character_developments": ["dev1", "dev2", ...],
  "themes": ["theme1", "theme2", ...],
  "emotional_tone": "string",
  "narrative_arc": "string",
  "memorable_moments": ["moment1", "moment2", ...],
  "generated_at": "2026-01-07T12:00:00Z",
  "word_count": 1234
}

# Get cached recap
GET /api/recap/chapter/{chapter_id}

# Delete cached recap
DELETE /api/recap/chapter/{chapter_id}

# List all recaps for manuscript
GET /api/recap/manuscript/{manuscript_id}/recaps

# Generate arc recap (multiple chapters)
POST /api/recap/arc
{
  "manuscript_id": "string",
  "chapter_ids": ["id1", "id2", ...]
}
```

**Caching Strategy:**
- Content hash-based invalidation
- Stored in SQLite database
- JSON storage for structured data
- Automatic regeneration on content change

**Frontend:**
- Component: `frontend/src/components/Recap/RecapModal.tsx`
- Store: `frontend/src/stores/recapStore.ts`
- Integration: Editor toolbar button

**Performance:**
- **Cached:** <100ms retrieval from database
- **Fresh:** 10-20s (Claude Sonnet 4 API call)
- **Database:** SQLite with JSON column for recap data

**AI Model:**
- Default: Claude 3.5 Sonnet (via OpenRouter)
- Prompt: Structured analysis prompt with clear guidelines
- Token usage: ~500-1000 tokens per chapter recap

### Use Cases

**Before Writing Next Chapter:**
Generate a recap to refresh your memory of what happened and where the story is going.

**After Major Revisions:**
Regenerate recap to see how edits changed themes, tone, and character development.

**Story Planning:**
Use recaps to identify:
- Pacing issues
- Theme consistency
- Character arc development
- Plot holes

**Sharing Progress:**
Export recap insights to share with:
- Beta readers
- Writing partners
- Editors
- Critique groups

### UI Design

The Recap modal features:
- **Parchment aesthetic** matching Maxwell's vintage theme
- **Bronze accents** for headers and highlights
- **Gradient header** with sticky positioning
- **Responsive layout** for all screen sizes
- **Smooth animations** for polished feel
- **Accessible design** with ARIA labels

### Future Enhancements

Potential additions:
- **Arc Recaps:** Multi-chapter story arc summaries (backend ready!)
- **Export to PDF:** Download recaps as beautiful PDFs
- **Social Sharing:** Share recap cards on social media
- **Comparison View:** Compare recaps across revisions
- **Timeline Integration:** Link events to timeline entries

---

## Feature Comparison

| Feature | Fast Coach | AI Suggestions | Recap Engine | Time Machine |
|---------|------------|----------------|--------------|--------------|
| **Speed** | Instant | 3-10 sec | 10-20 sec (first) | < 1 sec |
| **Cost** | Free | Pay-per-use | Pay-per-use | Free |
| **Requires API Key** | No | Yes | Yes | No |
| **Real-time** | Yes | No | No | No |
| **Caching** | No | No | Yes | N/A |
| **Privacy** | Local | OpenRouter | OpenRouter | Local |

---

## Getting Help

**For feature questions:**
- Check this guide first
- See [CLAUDE.md](./CLAUDE.md) for technical details
- See [PROGRESS.md](./PROGRESS.md) for feature status

**For issues:**
- Report bugs via GitHub Issues (when public)
- Email: support@maxwell.app (coming soon)

**For feature requests:**
- See [IMPLEMENTATION_PLAN_v2.md](./IMPLEMENTATION_PLAN_v2.md) for roadmap
- Submit requests via feedback form (in-app, coming soon)

---

**Last Updated:** 2026-01-07
**Maintainer:** Maxwell Development Team
