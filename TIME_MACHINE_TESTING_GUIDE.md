# Time Machine Testing Guide

**Status**: ✅ Fully Integrated and Ready for Testing
**Date**: December 15, 2025

---

## 🚀 Quick Start

Both servers are currently running:
- **Backend**: http://localhost:8000 ✅
- **Frontend**: http://localhost:5173 ✅

---

## ✅ Complete Testing Workflow

### 1. Open the Application

```bash
# Frontend should already be running at:
open http://localhost:5173
```

### 2. Create a New Manuscript

1. Click "Create New Manuscript" button
2. Enter a title (e.g., "Time Machine Test")
3. Click Create

### 3. Write Some Content

1. Click into the editor
2. Type a few paragraphs:
   ```
   Chapter 1: The Beginning

   Once upon a time, in a land far away, there lived a brave knight.
   He was known throughout the kingdom for his courage and wisdom.
   ```

3. Wait 5 seconds for auto-save (watch for "All changes saved" indicator)

### 4. Open Time Machine

1. Look for the **Time Machine** button in the top-right of the header (clock icon)
2. Click the button to open the Time Machine modal

### 5. Create a Manual Snapshot

1. In the Time Machine sidebar, click **"+ Create Snapshot"**
2. Enter a label: "Chapter 1 - First Draft"
3. Click OK
4. You should see "✅ Snapshot created!" alert
5. The new snapshot appears in the sidebar

### 6. Make More Edits

1. Close the Time Machine (click X or click outside)
2. Add more content to your manuscript:
   ```

   One day, he received a message from the king. The kingdom was in danger.
   Dark forces were gathering in the north, threatening to destroy everything.
   ```

3. Wait 5 seconds for auto-save

### 7. Create Another Snapshot

1. Open Time Machine again
2. Create another snapshot: "Chapter 1 - Second Draft"
3. Close Time Machine

### 8. Wait for Auto-Snapshot

1. Continue editing your manuscript
2. After 5 minutes, the AutoSavePlugin will automatically create a snapshot
3. Check the console logs for: "Created auto-snapshot for manuscript..."

### 9. View Snapshot History

1. Open Time Machine
2. You should see multiple snapshots in the sidebar:
   - Your manual snapshots
   - Auto-save snapshots (if 5 minutes have passed)
3. Each snapshot shows:
   - Label
   - Date/time
   - Word count
   - Trigger type badge (Manual, Auto, etc.)

### 10. Compare Versions (Diff Viewer)

1. Click on a snapshot in the sidebar to select it
2. Click **"View Changes"** button
3. The diff viewer appears showing:
   - Green highlighting for additions (<ins> tags)
   - Red highlighting for deletions (<del> tags)
4. Click "Close Diff" to return to timeline view

### 11. Restore a Previous Version

1. Select an older snapshot
2. Click **"Restore"** button
3. Confirm the restoration (your current work will be backed up)
4. The editor reloads with the restored content
5. Check the sidebar - a new backup snapshot was created automatically

### 12. Verify Backup Was Created

1. Open Time Machine again
2. You should see a new "Pre-restore backup" snapshot
3. This is your previous work, safely saved before restoration

---

## 🧪 Backend API Testing (Already Verified)

All backend endpoints are working correctly:

```bash
# Create snapshot
curl -X POST http://localhost:8000/api/versioning/snapshots \
  -H "Content-Type: application/json" \
  -d '{
    "manuscript_id": "test-ms-1",
    "content": "Once upon a time...",
    "trigger_type": "MANUAL",
    "label": "Test Snapshot",
    "word_count": 4
  }'

# List snapshots
curl http://localhost:8000/api/versioning/snapshots/test-ms-1

# Restore snapshot
curl -X POST http://localhost:8000/api/versioning/restore \
  -H "Content-Type: application/json" \
  -d '{
    "manuscript_id": "test-ms-1",
    "snapshot_id": "<SNAPSHOT_ID>",
    "create_backup": true
  }'

# Get diff
curl -X POST http://localhost:8000/api/versioning/diff \
  -H "Content-Type: application/json" \
  -d '{
    "manuscript_id": "test-ms-1",
    "snapshot_id_old": "<OLD_ID>",
    "snapshot_id_new": "<NEW_ID>"
  }'
```

**Results**: All ✅ Working correctly

---

## 🎨 UI Components

### Time Machine Modal

**Layout**:
```
┌─────────────────────────────────────────────────────┐
│ Time Machine                                     × │
│ Browse and restore previous versions               │
├──────────────┬──────────────────────────────────────┤
│              │                                      │
│  Snapshots   │       Timeline / Diff Viewer        │
│   Sidebar    │         (Main Area)                 │
│              │                                      │
│ [+ Create]   │  • Visual timeline with nodes       │
│              │  • Snapshot details                 │
│ Snapshot 1   │  • HTML diff viewer                 │
│ Snapshot 2   │                                      │
│ Snapshot 3   │                                      │
│              │                                      │
└──────────────┴──────────────────────────────────────┘
```

### Snapshot Card

Each snapshot shows:
- **Label**: "Chapter 1 - First Draft"
- **Badge**: Type (Manual, Auto, Chapter, Pre-AI, Session)
- **Date**: "Dec 15, 3:00 PM"
- **Word Count**: "243 words"
- **Actions** (when selected):
  - View Changes
  - Restore

### History Timeline

Visual timeline with:
- Vertical line connecting snapshots
- Bronze nodes for each snapshot
- Time gaps between snapshots
- Click to select and view details

### Diff Viewer

Side-by-side comparison showing:
- Green background for additions
- Red background for deletions
- Line-by-line changes
- Legend explaining colors

---

## 🐛 Edge Cases Handled

✅ **No snapshots yet**
- Shows empty state message
- Prompts to create first snapshot

✅ **Network errors**
- Error messages displayed in UI
- Graceful error handling with alerts

✅ **Failed restore**
- Alert message with error details
- Manuscript not changed

✅ **Failed diff generation**
- Alert message
- Fallback to snapshot details view

✅ **No older version for diff**
- Alert: "No older version to compare with"
- Cannot diff the oldest snapshot

✅ **Confirmation before restore**
- Requires user confirmation
- Explains that current work will be backed up

✅ **Auto-backup before restore**
- Automatically creates "Pre-restore backup"
- Prevents data loss

---

## 🔧 Configuration

### Auto-Snapshot Settings

In `ManuscriptEditor.tsx`:
```typescript
<AutoSavePlugin
  manuscriptId={manuscriptId}
  onSaveStatusChange={setSaveStatus}
  enableSnapshots={true}      // Enable auto-snapshots
  snapshotInterval={5}         // Minutes between snapshots
/>
```

**To adjust**:
- Set `enableSnapshots={false}` to disable auto-snapshots
- Change `snapshotInterval={10}` for 10-minute intervals
- Default: 5 minutes

### Snapshot Trigger Types

The system supports multiple trigger types:
- `MANUAL` - User-created snapshots
- `AUTO` - Auto-save snapshots
- `CHAPTER_COMPLETE` - After completing a chapter
- `PRE_GENERATION` - Before using AI features
- `SESSION_END` - When closing the editor

Currently implemented:
- ✅ MANUAL (via "Create Snapshot" button)
- ✅ AUTO (via AutoSavePlugin)
- ⏳ Others (planned for Week 3)

---

## 📊 What to Look For

### Success Indicators

1. ✅ Time Machine button appears in header
2. ✅ Modal opens when clicked
3. ✅ Snapshots are listed in sidebar
4. ✅ Can create manual snapshots
5. ✅ Can select snapshots
6. ✅ Can view diffs between versions
7. ✅ Can restore previous versions
8. ✅ Backup created before restore
9. ✅ Editor reloads with restored content
10. ✅ Console logs show auto-snapshot creation

### Browser Console

Watch for these messages:
```
Auto-saved manuscript ms-123456: 243 words
Created auto-snapshot for manuscript ms-123456
```

### Network Tab

Check these API calls:
- `POST /api/versioning/snapshots` - Create snapshot
- `GET /api/versioning/snapshots/{id}` - List snapshots
- `POST /api/versioning/restore` - Restore snapshot
- `POST /api/versioning/diff` - Get diff

All should return `{ success: true, data: {...} }`

---

## 🎯 Known Limitations

1. **Auto-snapshot debouncing**: First auto-snapshot won't occur until 5 minutes after the first edit
2. **Diff viewer**: Only shows manuscript content changes, not metadata changes
3. **Page reload on restore**: Editor reloads to refresh content (could be improved in Week 3)
4. **Modal size**: Fixed max-width, may not use full screen on large displays

---

## 🚀 Next Steps (Week 3)

1. Add keyboard shortcuts (Cmd+S for snapshot)
2. Pre-generation snapshots (before AI use)
3. Session-end snapshots
4. Improve restore UX (no page reload)
5. Add snapshot search/filter
6. Export snapshot as file
7. Snapshot annotations/notes

---

## ✅ Test Checklist

Use this checklist to verify all functionality:

### Basic Functionality
- [ ] Time Machine button visible in header
- [ ] Modal opens smoothly
- [ ] Modal can be closed
- [ ] Create manual snapshot works
- [ ] Snapshots appear in sidebar
- [ ] Snapshot cards show correct info

### Navigation
- [ ] Click snapshot to select
- [ ] Selected snapshot highlights
- [ ] Snapshot details appear
- [ ] Timeline view shows all snapshots
- [ ] Time gaps displayed correctly

### Diff Viewer
- [ ] "View Changes" button works
- [ ] Diff HTML renders correctly
- [ ] Additions highlighted green
- [ ] Deletions highlighted red
- [ ] Can close diff viewer

### Restore
- [ ] Restore button shows
- [ ] Confirmation dialog appears
- [ ] Restore completes successfully
- [ ] Backup snapshot created
- [ ] Editor shows restored content

### Auto-Save Integration
- [ ] Auto-save status indicator works
- [ ] Content saves every 5 seconds
- [ ] Auto-snapshots created every 5 minutes
- [ ] Console logs confirm snapshot creation

### Error Handling
- [ ] Network errors shown gracefully
- [ ] Empty state displayed when no snapshots
- [ ] Failed operations show error messages
- [ ] No console errors during normal use

---

## 🎉 Success Criteria

**Phase 1 Week 2 is complete when**:
- ✅ All basic functionality tests pass
- ✅ All navigation tests pass
- ✅ All diff viewer tests pass
- ✅ All restore tests pass
- ✅ Auto-save integration works
- ✅ Error handling works

**Current Status**: All ✅ Ready for testing!

---

**Happy Testing! 🚀**

If you encounter any issues, check:
1. Browser console for errors
2. Network tab for failed API calls
3. Backend logs: `tail -f backend/backend.log`
4. Frontend logs: `tail -f frontend/dev.log`
