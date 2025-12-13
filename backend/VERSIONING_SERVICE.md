# Git-Based Versioning Service (Time Machine)

**Status**: ✅ Complete
**Date**: 2025-12-13

---

## Overview

The versioning service provides Git-based version control for manuscripts, enabling:
- **Automatic snapshots** on key events
- **Manual snapshots** by user request
- **Time travel** to restore previous versions
- **Diff viewing** between versions
- **Multiverse branching** for exploring alternate scenes

---

## Architecture

### Git Repository Per Manuscript

Each manuscript gets its own Git repository:
```
data/manuscripts/
└── {manuscript_id}/
    └── .codex/                    # Git repository
        ├── .git/                  # Git internals
        ├── manuscript.json        # Lexical editor state
        └── metadata.json          # Snapshot metadata
```

### Database + Git Hybrid

- **Git**: Stores actual file history (immutable, full fidelity)
- **SQLite**: Stores snapshot metadata for fast queries

**Snapshots Table:**
```sql
CREATE TABLE snapshots (
    id TEXT PRIMARY KEY,
    manuscript_id TEXT,
    commit_hash TEXT,              -- Links to Git commit
    label TEXT,                    -- User-provided label
    description TEXT,
    trigger_type TEXT,             -- MANUAL, AUTO, CHAPTER_COMPLETE, etc.
    word_count INTEGER,
    created_at DATETIME
);
```

---

## Service API

### `VersionService` Class

**Location:** `app/services/version_service.py`

#### Methods

**1. `init_repository(manuscript_id: str)`**
```python
# Initialize Git repo for a manuscript
repo = version_service.init_repository("ms-123")
```

**2. `create_snapshot(...)`**
```python
snapshot = version_service.create_snapshot(
    manuscript_id="ms-123",
    content='{"root": {...}}',  # Lexical JSON
    trigger_type="MANUAL",
    label="Chapter 3 complete",
    description="Finished the confrontation scene",
    word_count=15234
)
# Returns: Snapshot model with commit_hash
```

**Trigger Types:**
- `MANUAL` - User clicked "Create Snapshot"
- `AUTO` - Periodic auto-save
- `CHAPTER_COMPLETE` - Detected heading node
- `PRE_GENERATION` - Before AI writes
- `SESSION_END` - User closes editor

**3. `get_history(manuscript_id: str)`**
```python
history = version_service.get_history("ms-123")
# Returns: List of snapshots with Git metadata
[
    {
        "id": "snap-001",
        "commit_hash": "a1b2c3d4...",
        "label": "Chapter 3 complete",
        "trigger_type": "MANUAL",
        "word_count": 15234,
        "created_at": "2025-12-13T19:30:00",
        "author": "Maxwell IDE",
        "message": "[MANUAL] Chapter 3 complete\n\nFinished the confrontation scene"
    },
    ...
]
```

**4. `restore_snapshot(manuscript_id, snapshot_id, create_backup=True)`**
```python
content = version_service.restore_snapshot(
    manuscript_id="ms-123",
    snapshot_id="snap-001",
    create_backup=True  # Creates backup before restore
)
# Returns: Restored Lexical JSON content
```

**5. `get_diff(manuscript_id, snapshot_id_old, snapshot_id_new)`**
```python
diff = version_service.get_diff(
    manuscript_id="ms-123",
    snapshot_id_old="snap-001",
    snapshot_id_new="snap-002"
)
# Returns: {
#   "files_changed": 1,
#   "insertions": 42,
#   "deletions": 15,
#   "patches": [...]
# }
```

**6. `create_variant_branch(manuscript_id, scene_id, variant_label)`**
```python
branch = version_service.create_variant_branch(
    manuscript_id="ms-123",
    scene_id="scene-456",
    variant_label="darker ending"
)
# Returns: "variant/scene-456/darker-ending"
```

**7. `merge_variant(manuscript_id, variant_branch)`**
```python
success = version_service.merge_variant(
    manuscript_id="ms-123",
    variant_branch="variant/scene-456/darker-ending"
)
# Returns: True if merged, False if conflicts
```

---

## REST API Endpoints

**Base Path:** `/api/versioning`

### POST `/snapshots`
Create a new snapshot

**Request:**
```json
{
  "manuscript_id": "ms-123",
  "content": "{\"root\": {...}}",
  "trigger_type": "MANUAL",
  "label": "Chapter 3 complete",
  "description": "Finished confrontation scene",
  "word_count": 15234
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "snap-001",
    "commit_hash": "a1b2c3d4...",
    "label": "Chapter 3 complete",
    "trigger_type": "MANUAL",
    "word_count": 15234,
    "created_at": "2025-12-13T19:30:00"
  }
}
```

### GET `/snapshots/{manuscript_id}`
Get version history

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "snap-001",
      "commit_hash": "a1b2c3d4...",
      "label": "Chapter 3 complete",
      "trigger_type": "MANUAL",
      "word_count": 15234,
      "created_at": "2025-12-13T19:30:00"
    }
  ]
}
```

### POST `/restore`
Restore to a snapshot

**Request:**
```json
{
  "manuscript_id": "ms-123",
  "snapshot_id": "snap-001",
  "create_backup": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "content": "{\"root\": {...}}"
  }
}
```

### POST `/diff`
Get diff between snapshots

**Request:**
```json
{
  "manuscript_id": "ms-123",
  "snapshot_id_old": "snap-001",
  "snapshot_id_new": "snap-002"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "files_changed": 1,
    "insertions": 42,
    "deletions": 15,
    "patches": [...]
  }
}
```

### POST `/variants/create`
Create a variant branch

**Request:**
```json
{
  "manuscript_id": "ms-123",
  "scene_id": "scene-456",
  "variant_label": "darker ending",
  "base_snapshot_id": "snap-001"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "branch_name": "variant/scene-456/darker-ending"
  }
}
```

### POST `/variants/merge`
Merge a variant back to main

**Request:**
```json
{
  "manuscript_id": "ms-123",
  "variant_branch": "variant/scene-456/darker-ending"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Variant merged successfully"
}
```

### DELETE `/snapshots/{snapshot_id}`
Delete a snapshot

**Response:**
```json
{
  "success": true,
  "message": "Snapshot deleted"
}
```

---

## Usage Examples

### Frontend Integration

**Auto-save with snapshot creation:**
```typescript
// In AutoSavePlugin.tsx
const saveContent = debounce(async () => {
  const editorState = editor.getEditorState();
  const json = JSON.stringify(editorState.toJSON());

  // Save to backend + create snapshot
  const response = await fetch('/api/versioning/snapshots', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      manuscript_id: manuscriptId,
      content: json,
      trigger_type: 'AUTO',
      label: '',
      word_count: getWordCount()
    })
  });

  const { data } = await response.json();
  console.log('Snapshot created:', data.commit_hash);
}, 5000);
```

**Load version history:**
```typescript
const { data: history } = useQuery({
  queryKey: ['history', manuscriptId],
  queryFn: async () => {
    const response = await fetch(`/api/versioning/snapshots/${manuscriptId}`);
    const { data } = await response.json();
    return data;
  }
});
```

**Restore a version:**
```typescript
const restoreMutation = useMutation({
  mutationFn: async (snapshotId: string) => {
    const response = await fetch('/api/versioning/restore', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        manuscript_id: manuscriptId,
        snapshot_id: snapshotId,
        create_backup: true
      })
    });
    const { data } = await response.json();
    return data.content;
  },
  onSuccess: (content) => {
    // Load content into editor
    const editorState = editor.parseEditorState(content);
    editor.setEditorState(editorState);
  }
});
```

---

## Features

### ✅ Implemented

1. **Git-backed storage** - Every snapshot is a real Git commit
2. **Metadata database** - Fast queries without parsing Git
3. **Automatic snapshotting** - Configurable triggers
4. **Manual snapshots** - User can save named versions
5. **Restore functionality** - Time travel to any snapshot
6. **Auto-backup on restore** - Never lose current work
7. **Diff generation** - Compare any two snapshots
8. **Variant branching** - Create alternate versions
9. **Variant merging** - Merge variants back to main
10. **REST API** - Complete HTTP interface

### 🔜 Pending (UI/Frontend)

1. **History Slider UI** - Visual timeline component
2. **Diff Viewer UI** - Side-by-side comparison
3. **Variant Switcher** - Tab-based multiverse navigation
4. **Snapshot labeling UI** - Add labels/descriptions
5. **Auto-snapshot triggers** - Detect chapter completion

---

## Data Flow

```
USER EDITS TEXT
      ↓
Auto-save (5s debounce)
      ↓
POST /api/versioning/snapshots
      ↓
VersionService.create_snapshot()
      ├─→ Write manuscript.json
      ├─→ Write metadata.json
      ├─→ Git add + commit
      └─→ Store in database
      ↓
Snapshot created with commit hash
```

```
USER CLICKS "RESTORE"
      ↓
POST /api/versioning/restore
      ↓
VersionService.restore_snapshot()
      ├─→ Create backup snapshot (current state)
      ├─→ Git checkout target commit
      └─→ Read manuscript.json
      ↓
Return restored content
      ↓
Load into Lexical editor
```

---

## Performance Considerations

### Git Repository Size

- **Lexical JSON** is text-based, compresses well
- Git stores diffs efficiently
- Average manuscript (100K words) ≈ 500KB JSON
- 100 snapshots ≈ 5-10MB total (with compression)

### Query Performance

- History queries hit database (fast)
- Content retrieval hits Git (fast for recent commits)
- Diff generation requires Git traversal (slower, but cached)

### Optimization

- Git uses pack files for compression
- Database indices on `manuscript_id` and `created_at`
- Lazy loading of commit content
- Pagination for history (if > 100 snapshots)

---

## Testing

**Test Script:** `backend/tests/test_version_service.py`

```python
def test_create_snapshot():
    content = '{"root": {"children": [{"text": "Hello"}]}}'

    snapshot = version_service.create_snapshot(
        manuscript_id="test-ms",
        content=content,
        trigger_type="MANUAL",
        label="Test snapshot"
    )

    assert snapshot.commit_hash
    assert len(snapshot.commit_hash) == 40  # Git SHA-1

def test_restore_snapshot():
    # Create two snapshots
    snap1 = version_service.create_snapshot(...)
    snap2 = version_service.create_snapshot(...)

    # Restore to snap1
    content = version_service.restore_snapshot(
        manuscript_id="test-ms",
        snapshot_id=snap1.id
    )

    assert content == snap1_content

def test_diff():
    diff = version_service.get_diff(
        manuscript_id="test-ms",
        snapshot_id_old=snap1.id,
        snapshot_id_new=snap2.id
    )

    assert diff["files_changed"] > 0
```

---

## Summary

**Total Implementation:**
- `version_service.py` - 350 LOC
- `versioning.py` (routes) - 220 LOC
- **Total**: ~570 LOC

**Capabilities:**
- ✅ Full Git version control
- ✅ Snapshot creation with metadata
- ✅ Restore with auto-backup
- ✅ Diff generation
- ✅ Variant branching & merging
- ✅ Complete REST API

**Next Steps:**
1. Frontend UI components (Week 2-3)
2. Auto-snapshot triggers (Week 3)
3. History visualization (Week 3)

**Status**: Core service complete, ready for frontend integration
