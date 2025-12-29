# 📖 Chapter Recap Engine - User Guide

The **Recap Engine** uses Claude AI to generate beautiful, structured summaries of your chapters. It helps writers quickly review what happened in a chapter before continuing their story.

## ✨ Features

### What You Get
- **Summary**: 2-3 sentence overview of the chapter
- **Key Events**: Numbered list of major plot points (3-5 events)
- **Character Developments**: How characters change or reveal themselves
- **Themes**: Major thematic elements present in the chapter
- **Emotional Tone**: The chapter's emotional atmosphere
- **Narrative Arc**: Where this chapter sits in your story structure
- **Memorable Moments**: Standout scenes or lines

### Smart Caching
- **First Generation**: Takes 10-20 seconds (calls Claude API)
- **Cached Retrieval**: Instant (<0.1 seconds)
- **Auto-Invalidation**: Regenerates if chapter content changes
- **Cache Indicator**: Shows when recap was generated

## 🎯 How to Use

### Generating a Recap

1. **Open a Chapter** in the editor
2. **Click the "📖 Recap" button** in the toolbar (next to "🔍 Analyze")
3. **Wait 10-20 seconds** for AI analysis (first time)
4. **View the beautiful structured recap** in the modal

### Regenerating a Recap

If you've edited your chapter and want a fresh recap:

1. **Open the Recap modal**
2. **Click "Regenerate Recap"** at the bottom
3. **Wait for new analysis**
4. **See updated insights** based on current content

## 🔧 Technical Details

### API Endpoints
```
POST   /api/recap/chapter/:id         - Generate/retrieve chapter recap
GET    /api/recap/chapter/:id         - Get cached recap
DELETE /api/recap/chapter/:id         - Delete cached recap
POST   /api/recap/arc                 - Generate arc recap (multiple chapters)
GET    /api/recap/manuscript/:id/recaps - List all recaps
```

### Backend Tests
Run the test suite to verify everything works:
```bash
python3 test_recap_engine.py
```

Expected output:
- ✅ Backend connection successful
- ✅ Chapter recap generated with full structured data
- ✅ Caching working (0.01s retrieval)
- ✅ All endpoints functional

## 💡 Use Cases

### Before Writing the Next Chapter
Generate a recap to refresh your memory of what happened and where the story is going.

### After Major Revisions
Regenerate the recap to see how your edits changed the chapter's themes and emotional tone.

### Story Planning
Use recaps to identify pacing issues, theme consistency, or character arc development.

### Sharing Progress
Export recap insights to share with beta readers or writing partners.

## 🎨 UI Design

The modal features:
- **Parchment aesthetic** matching the app's vintage theme
- **Bronze accents** for headers and highlights
- **Gradient header** with sticky positioning
- **Responsive layout** that works on all screen sizes
- **Smooth animations** for a polished feel
- **Accessible design** with proper ARIA labels

## 🚀 Future Enhancements

Potential additions:
- **Arc Recaps**: Multi-chapter story arc summaries (backend ready!)
- **Export to PDF**: Download recaps as beautiful PDFs
- **Social Sharing**: Share recap cards on social media
- **Comparison View**: Compare recaps across revisions
- **Integration with Timeline**: Link events to timeline entries

## 📊 Performance

- **Backend**: Python FastAPI + Claude Sonnet 4
- **Caching**: Content hash-based invalidation
- **Database**: SQLite with JSON storage for structured data
- **Response Time**:
  - Cached: <100ms
  - Fresh: 10-20s (Claude API call)

## 🎉 Success!

The Recap Engine is fully integrated and ready to use! Click the 📖 button in any chapter to try it out.

---

**Built with Claude Code** 🤖
