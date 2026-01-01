# Phase 2: Real-Time Entity Extraction

## Overview

Maxwell's **real-time entity extraction** automatically detects characters, locations, items, and lore as you write—no manual "Analyze" button needed. This creates a magical writing experience where the Codex builds itself.

## Architecture

### Backend (Python)

**RealtimeNLPService** (`backend/app/services/realtime_nlp_service.py`):
- **Debouncing**: Waits 2 seconds after typing stops before analyzing
- **Text buffering**: Accumulates text deltas to reduce API calls
- **spaCy NER**: Extracts named entities using `en_core_web_lg` model
- **Smart filtering**: Excludes common false positives (pronouns, verbs, etc.)
- **Concurrency control**: One analysis per manuscript at a time
- **Backpressure**: Limits buffer to 10,000 characters

**WebSocket Endpoint** (`backend/app/api/routes/realtime.py`):
- Endpoint: `ws://localhost:8000/api/realtime/nlp/{manuscript_id}`
- Client sends: `{"text_delta": "newly typed text"}`
- Server sends: `{"new_entities": [...], "timestamp": "..."}`
- Keep-alive pings every 30 seconds
- Auto-reconnect on disconnect

### Frontend (React + TypeScript)

**useRealtimeNLP Hook** (`frontend/src/hooks/useRealtimeNLP.ts`):
- Manages WebSocket connection lifecycle
- Sends text deltas to backend
- Receives entity suggestions
- Shows toast notifications with "Add to Codex" action
- Tracks analytics (entity detected, entity approved)

**RealtimeNLPPlugin** (`frontend/src/components/Editor/plugins/RealtimeNLPPlugin.tsx`):
- Lexical editor plugin
- Detects text changes in real-time
- Calculates deltas (new text since last update)
- Sends deltas via WebSocket

## Entity Detection Logic

### Entity Types Mapped

| spaCy Label | Maxwell Type | Example |
|-------------|--------------|---------|
| PERSON      | CHARACTER    | "Sarah Chen" |
| GPE, LOC, FAC | LOCATION   | "The Obsidian Tower" |
| WORK_OF_ART, PRODUCT | ITEM | "The Crimson Blade" |
| ORG, EVENT  | LORE         | "Council of Shadows" |

### Capitalization Heuristics

The service also detects entities using capitalization patterns:

- **Single capitalized proper noun** → CHARACTER
  - "Marcus stood up"

- **Two-word capitalized phrase** → ITEM or CHARACTER
  - "Sir Galahad" (CHARACTER - has title)
  - "Crystal Amulet" (ITEM - no title)

- **3+ word capitalized phrase** → LOCATION
  - "Tower of the Forgotten"

### Exclusion List

Common words excluded to reduce false positives:
- Pronouns: "I", "he", "she", "they"
- Common verbs: "made", "found", "went", "said"
- Generic nouns: "man", "woman", "person", "place"
- Colors/adjectives: "dark", "light", "old", "young"

## User Experience

### Writing Flow

1. User types: "Sarah pushed through the heavy oak door..."
2. **After 2 seconds of no typing:**
   - Plugin sends text delta to WebSocket
   - Backend analyzes with spaCy
   - Detects "Sarah" as CHARACTER
3. **Toast notification appears:**
   - "✨ Detected character: "Sarah""
   - Button: "Add to Codex" (10-second duration)
4. User clicks "Add to Codex"
5. Entity saved to database
6. Success toast: "✅ Added "Sarah" to Codex"

### Performance Characteristics

- **Debounce delay**: 2 seconds (configurable)
- **Max text size**: 5,000 characters per analysis
- **Max buffer**: 10,000 characters
- **Entities per notification**: Max 5 at once
- **Toast duration**: 10 seconds
- **Keep-alive interval**: 30 seconds

## Analytics Tracked

Via PostHog (if configured):

- `entity_analyzed`: Every time an entity is detected
  - Properties: `manuscript_id`, `entity_type`

- `entity_approved`: User clicks "Add to Codex"
  - Properties: `manuscript_id`, `entity_type`

This helps measure:
- **Detection accuracy**: How many detected entities are approved?
- **Feature engagement**: Are users using real-time extraction?
- **Entity distribution**: Which types are most common (CHARACTER, LOCATION, etc.)?

## Testing Guide

### Manual Testing

1. **Start both servers:**
   ```bash
   # Terminal 1: Backend
   cd backend && source venv/bin/activate && uvicorn app.main:app --reload

   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

2. **Open Maxwell** at http://localhost:5173

3. **Create or open a manuscript**

4. **Start typing a story** with character names:
   ```
   Sarah Chen walked into the Obsidian Tower. Marcus greeted her at the entrance,
   holding the Crystal Amulet in his hands.
   ```

5. **Wait 2 seconds after stopping**

6. **Expect toast notifications:**
   - ✨ Detected character: "Sarah Chen"
   - ✨ Detected location: "Obsidian Tower"
   - ✨ Detected character: "Marcus"
   - ✨ Detected item: "Crystal Amulet"

7. **Click "Add to Codex"** on any notification

8. **Verify in Codex sidebar:**
   - Open Codex (📖 button in left sidebar)
   - Check "Intel" tab
   - Confirm entity appears in list

### Check Browser Console

Expected logs:
```
✅ Real-time NLP WebSocket connected
📤 Received 4 entity suggestions
```

### Check Backend Logs

Expected logs:
```
✨ WebSocket connected for manuscript: {id} (1 active)
📤 Sent 4 entity suggestions
```

### Troubleshooting

**Issue**: No WebSocket connection
- **Fix**: Ensure backend is running on port 8000
- **Check**: Browser console for WebSocket errors

**Issue**: No entities detected
- **Fix**: Ensure spaCy is initialized (check backend startup logs)
- **Expected**: `🧠 NLP service available (spaCy en_core_web_lg)`

**Issue**: Too many false positives
- **Fix**: Add words to `EXCLUDE_WORDS` in `realtime_nlp_service.py`

**Issue**: WebSocket disconnects
- **Fix**: Check for firewall/proxy blocking WebSocket connections
- **Note**: Auto-reconnect after 5 seconds

## Comparison: Manual vs Real-Time

### Before (Manual Analysis)

1. Write entire chapter
2. Click "Analyze" button
3. Wait for full text processing
4. Review all suggestions at once (overwhelming)
5. Approve/reject one by one

### After (Real-Time Extraction)

1. Write naturally
2. Entities appear as you type (after 2-second delay)
3. Approve instantly with one click
4. No interruption to flow
5. Codex builds organically

## Future Enhancements (Phase 2+)

### Visual Feedback
- Underline detected entities in editor (like spell check)
- Hover to see entity type
- Click to add without toast

### Smart Deduplication
- Track rejected entities (don't suggest again)
- Learn from user preferences

### Context-Aware Detection
- Relationship extraction ("Sarah's sister Emma")
- Event detection ("The Battle of Crimson Fields")
- Emotional arc tracking

### Performance Optimization
- Only analyze current paragraph (not full buffer)
- Client-side pre-filtering before sending to server

---

## Files Modified

### Backend
- `app/services/realtime_nlp_service.py` - Core NLP logic
- `app/api/routes/realtime.py` - WebSocket endpoint

### Frontend
- `frontend/src/hooks/useRealtimeNLP.ts` - WebSocket hook + analytics
- `frontend/src/components/Editor/plugins/RealtimeNLPPlugin.tsx` - Lexical plugin
- `frontend/src/components/Editor/ManuscriptEditor.tsx` - Plugin integration

### Analytics
- Added `entityAnalyzed` event
- Added `entityApproved` event

---

## Success Metrics

Track these in PostHog to measure Phase 2 success:

1. **Adoption**: % of users who approve at least 1 entity via real-time
2. **Accuracy**: Approval rate (approved / detected)
3. **Engagement**: Avg entities detected per 1000 words
4. **Preference**: Real-time approvals vs manual "Analyze" button
5. **Performance**: WebSocket uptime and reconnection rate

---

**Last Updated**: January 1, 2026
**Status**: ✅ Complete - Real-time extraction fully functional
**Next**: Phase 2 Week 3 - Visual Timeline Enhancements
