# Inline Writing Feedback System Design

**Status:** Design Document
**Date:** February 3, 2026

---

## Overview

This document describes the architecture for inline writing feedback in Maxwell's editor. The system provides real-time visual feedback while writing, similar to how entity mentions are highlighted, but for grammar, spelling, style, and other writing issues.

### User Experience Goals

1. **Immediate Visual Feedback** - As writers type, issues appear as colored underlines
2. **Non-Intrusive** - Underlines don't interrupt writing flow
3. **Informative Hover** - Hover over an issue to see details and suggestions
4. **Quick Fixes** - One-click to apply suggested corrections
5. **Configurable** - Writers can enable/disable categories and adjust sensitivity
6. **Layered Analysis** - Real-time for basic issues, on-demand for deep analysis

---

## Visual Design

### Underline Colors (Following VS Code/Word conventions)

| Issue Type | Underline Style | Color |
|------------|-----------------|-------|
| Spelling | Wavy | Red (#DC2626) |
| Grammar | Wavy | Blue (#2563EB) |
| Style | Dotted | Amber (#D97706) |
| Consistency | Dashed | Purple (#7C3AED) |
| Voice | Dashed | Teal (#0D9488) |
| Readability | Dotted | Gray (#6B7280) |

### Hover Card Design

```
┌─────────────────────────────────────────┐
│ 🔤 Spelling Error                       │
├─────────────────────────────────────────┤
│ "recieve" may be misspelled             │
│                                         │
│ Suggestions:                            │
│ [receive] [relieve] [deceive]           │
│                                         │
│ ────────────────────────────────────────│
│ [✓ Fix]  [+ Add to Dictionary]  [Ignore]│
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 📝 Style Suggestion                     │
├─────────────────────────────────────────┤
│ "nodded in agreement" - redundant       │
│                                         │
│ "Nodded" already implies agreement.     │
│ Consider: "nodded" or show the          │
│ agreement through dialogue/action.      │
│                                         │
│ 💡 Teaching: Redundant phrases slow     │
│ pacing and can feel amateurish to       │
│ experienced readers.                    │
│                                         │
│ ────────────────────────────────────────│
│ [✓ Remove "in agreement"]        [Ignore]│
└─────────────────────────────────────────┘
```

---

## Architecture

### System Components

```
┌──────────────────────────────────────────────────────────────┐
│                        FRONTEND                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐     ┌──────────────────────────────┐   │
│  │ WritingIssue    │     │ ManuscriptEditor             │   │
│  │ HighlightPlugin │────▶│ (Lexical)                    │   │
│  │                 │     │                              │   │
│  │ - Decorations   │     │ ┌──────────────────────────┐ │   │
│  │ - Hover detect  │     │ │ Text with underlines     │ │   │
│  │ - Position calc │     │ │ ~~~spelling~~~           │ │   │
│  └────────┬────────┘     │ │ ...style issue...        │ │   │
│           │              │ └──────────────────────────┘ │   │
│           │              └──────────────────────────────────┘   │
│           │                                              │
│           ▼                                              │
│  ┌─────────────────┐     ┌─────────────────────────────┐│
│  │ WritingIssue    │     │ writingFeedbackStore        ││
│  │ HoverCard       │◀────│                             ││
│  │                 │     │ - issues: WritingIssue[]    ││
│  │ - Issue details │     │ - settings: FeedbackSettings││
│  │ - Suggestions   │     │ - applyFix()                ││
│  │ - Quick fix btn │     │ - ignoreIssue()             ││
│  └─────────────────┘     │ - addToDict()               ││
│                          └─────────────────────────────┘│
│                                     ▲                    │
│                                     │                    │
└─────────────────────────────────────┼────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │          BACKEND API              │
                    ├───────────────────────────────────┤
                    │                                   │
                    │  POST /api/feedback/realtime      │
                    │  - Debounced, ~500 char chunks    │
                    │  - Returns: spelling, grammar     │
                    │                                   │
                    │  POST /api/feedback/chapter       │
                    │  - Full chapter analysis          │
                    │  - Returns: all issue types       │
                    │                                   │
                    │  POST /api/feedback/manuscript    │
                    │  - Full manuscript analysis       │
                    │  - Returns: deep analysis         │
                    │                                   │
                    └───────────────────────────────────┘
```

### Analysis Tiers

| Tier | Trigger | Latency | Issue Types |
|------|---------|---------|-------------|
| **Real-time** | Typing (debounced 1s) | <500ms | Spelling, Basic Grammar |
| **Paragraph** | Paragraph complete | <2s | + Style, Overused Phrases |
| **Chapter** | Manual or on save | <10s | + Readability, Consistency, Voice |
| **Manuscript** | Manual only | <60s | + Cross-chapter consistency, Plot issues |

---

## Data Models

### WritingIssue (Frontend Type)

```typescript
interface WritingIssue {
  id: string;
  type: 'spelling' | 'grammar' | 'style' | 'consistency' | 'voice' | 'readability';
  severity: 'error' | 'warning' | 'info';

  // Position in editor
  startOffset: number;
  endOffset: number;

  // Issue details
  message: string;
  originalText: string;
  suggestions: string[];

  // Teaching moment (optional)
  teachingPoint?: string;

  // Metadata
  ruleId?: string;      // For ignoring specific rules
  category?: string;    // Sub-category
  confidence?: number;  // 0-1 for ML-based detection
}

interface FeedbackSettings {
  // Enable/disable by type
  spelling: boolean;
  grammar: boolean;
  style: boolean;
  consistency: boolean;
  voice: boolean;
  readability: boolean;

  // Sensitivity
  showInfoLevel: boolean;     // Show info-level suggestions
  minConfidence: number;      // 0-1, filter ML suggestions

  // Custom dictionary
  customDictionary: string[];

  // Ignored rules
  ignoredRules: string[];
}
```

### Backend Response

```python
@dataclass
class WritingFeedbackResponse:
    issues: List[WritingIssue]
    stats: Dict[str, int]  # Count by type
    analysis_time_ms: int
    tokens_analyzed: int

@dataclass
class WritingIssue:
    id: str
    type: str
    severity: str
    start_offset: int
    end_offset: int
    message: str
    original_text: str
    suggestions: List[str]
    teaching_point: Optional[str]
    rule_id: Optional[str]
    category: Optional[str]
    confidence: Optional[float]
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1)

#### Backend

**1. Create unified feedback service**

`backend/app/services/writing_feedback_service.py`:
- Combines all analyzers (grammar, style, readability, etc.)
- Returns unified WritingIssue format
- Supports different analysis depths (realtime, chapter, manuscript)

```python
class WritingFeedbackService:
    def __init__(self):
        self.grammar_analyzer = GrammarAnalyzer()
        self.style_analyzer = StyleAnalyzer()
        self.word_analyzer = WordAnalyzer()
        self.dialogue_analyzer = DialogueAnalyzer()
        self.readability_analyzer = ReadabilityAnalyzer()
        self.sentence_starter_analyzer = SentenceStarterAnalyzer()
        self.overused_phrases_analyzer = OverusedPhrasesAnalyzer()

    async def analyze_realtime(
        self,
        text: str,
        settings: FeedbackSettings,
        manuscript_id: Optional[str] = None
    ) -> WritingFeedbackResponse:
        """Fast analysis for real-time feedback (spelling, basic grammar)"""

    async def analyze_chapter(
        self,
        chapter_id: str,
        settings: FeedbackSettings
    ) -> WritingFeedbackResponse:
        """Full chapter analysis with all issue types"""

    async def analyze_manuscript(
        self,
        manuscript_id: str,
        settings: FeedbackSettings
    ) -> WritingFeedbackResponse:
        """Deep manuscript analysis with cross-chapter checks"""
```

**2. Create API endpoints**

`backend/app/api/routes/writing_feedback.py`:
```python
@router.post("/realtime")
async def analyze_realtime(request: RealtimeAnalysisRequest):
    """Real-time analysis for typing feedback"""

@router.post("/chapter/{chapter_id}")
async def analyze_chapter(chapter_id: str, settings: FeedbackSettings):
    """Full chapter analysis"""

@router.post("/manuscript/{manuscript_id}")
async def analyze_manuscript(manuscript_id: str, settings: FeedbackSettings):
    """Full manuscript analysis"""

@router.post("/apply-fix")
async def apply_fix(request: ApplyFixRequest):
    """Apply a suggested fix to the text"""

@router.get("/settings/{manuscript_id}")
async def get_settings(manuscript_id: str):
    """Get feedback settings for manuscript"""

@router.put("/settings/{manuscript_id}")
async def update_settings(manuscript_id: str, settings: FeedbackSettings):
    """Update feedback settings"""
```

#### Frontend

**3. Create Zustand store**

`frontend/src/stores/writingFeedbackStore.ts`:
```typescript
interface WritingFeedbackStore {
  // Issues by chapter
  issuesByChapter: Record<string, WritingIssue[]>;

  // Currently active issues (for current editor)
  activeIssues: WritingIssue[];

  // Settings
  settings: FeedbackSettings;

  // Loading states
  isAnalyzing: boolean;
  analysisProgress: number;

  // Actions
  setActiveIssues: (issues: WritingIssue[]) => void;
  analyzeRealtime: (text: string, chapterId: string) => Promise<void>;
  analyzeChapter: (chapterId: string) => Promise<void>;
  analyzeManuscript: (manuscriptId: string) => Promise<void>;

  applyFix: (issueId: string, suggestion: string) => void;
  ignoreIssue: (issueId: string) => void;
  addToDict: (word: string) => void;

  updateSettings: (settings: Partial<FeedbackSettings>) => void;
}
```

### Phase 2: Editor Integration (Week 2)

**4. Create WritingIssueHighlightPlugin**

`frontend/src/components/Editor/plugins/WritingIssueHighlightPlugin.tsx`:

```typescript
export default function WritingIssueHighlightPlugin({
  enabled = true,
}: WritingIssueHighlightPluginProps) {
  const [editor] = useLexicalComposerContext();
  const { activeIssues, analyzeRealtime, settings } = useWritingFeedbackStore();
  const [hoveredIssue, setHoveredIssue] = useState<WritingIssue | null>(null);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });

  // Debounced real-time analysis
  const debouncedAnalyze = useMemo(
    () => debounce((text: string, chapterId: string) => {
      analyzeRealtime(text, chapterId);
    }, 1000),
    [analyzeRealtime]
  );

  // Listen to editor changes
  useEffect(() => {
    return editor.registerUpdateListener(({ editorState }) => {
      editorState.read(() => {
        const text = $getRoot().getTextContent();
        debouncedAnalyze(text, currentChapterId);
      });
    });
  }, [editor, debouncedAnalyze]);

  // Apply decorations for issues
  useEffect(() => {
    editor.update(() => {
      // Clear existing decorations
      // Apply new decorations for each issue
      for (const issue of activeIssues) {
        applyIssueDecoration(issue);
      }
    });
  }, [activeIssues, editor]);

  // Handle hover detection (similar to EntityHighlightPlugin)
  // ...

  return hoveredIssue ? (
    <WritingIssueHoverCard
      issue={hoveredIssue}
      position={hoverPosition}
      onApplyFix={(suggestion) => applyFix(hoveredIssue.id, suggestion)}
      onIgnore={() => ignoreIssue(hoveredIssue.id)}
      onAddToDict={hoveredIssue.type === 'spelling' ? () => addToDict(hoveredIssue.originalText) : undefined}
    />
  ) : null;
}
```

**5. Create WritingIssueHoverCard**

`frontend/src/components/Editor/WritingIssueHoverCard.tsx`:

```typescript
interface WritingIssueHoverCardProps {
  issue: WritingIssue;
  position: { x: number; y: number };
  onApplyFix: (suggestion: string) => void;
  onIgnore: () => void;
  onAddToDict?: () => void;
}

export function WritingIssueHoverCard({
  issue,
  position,
  onApplyFix,
  onIgnore,
  onAddToDict,
}: WritingIssueHoverCardProps) {
  const typeConfig = ISSUE_TYPE_CONFIG[issue.type];

  return createPortal(
    <div style={{ position: 'fixed', left: position.x, top: position.y }}>
      {/* Header with icon and type */}
      <div className="flex items-center gap-2">
        <span>{typeConfig.icon}</span>
        <span className={typeConfig.headerClass}>{typeConfig.label}</span>
      </div>

      {/* Message */}
      <p>{issue.message}</p>

      {/* Suggestions */}
      {issue.suggestions.length > 0 && (
        <div className="suggestions">
          {issue.suggestions.map((suggestion, i) => (
            <button key={i} onClick={() => onApplyFix(suggestion)}>
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* Teaching point */}
      {issue.teachingPoint && (
        <div className="teaching-point">
          <span>💡</span>
          <p>{issue.teachingPoint}</p>
        </div>
      )}

      {/* Actions */}
      <div className="actions">
        {issue.suggestions[0] && (
          <button onClick={() => onApplyFix(issue.suggestions[0])}>
            ✓ Fix
          </button>
        )}
        {onAddToDict && (
          <button onClick={onAddToDict}>
            + Add to Dictionary
          </button>
        )}
        <button onClick={onIgnore}>Ignore</button>
      </div>
    </div>,
    document.body
  );
}
```

### Phase 3: Advanced Features (Week 3-4)

**6. CSS Decorations for Underlines**

`frontend/src/styles/writing-feedback.css`:
```css
/* Spelling errors - red wavy underline */
.writing-issue-spelling {
  text-decoration: underline wavy #DC2626;
  text-decoration-skip-ink: none;
  text-underline-offset: 2px;
}

/* Grammar errors - blue wavy underline */
.writing-issue-grammar {
  text-decoration: underline wavy #2563EB;
  text-decoration-skip-ink: none;
  text-underline-offset: 2px;
}

/* Style suggestions - amber dotted underline */
.writing-issue-style {
  text-decoration: underline dotted #D97706;
  text-decoration-skip-ink: none;
  text-underline-offset: 2px;
}

/* Consistency issues - purple dashed underline */
.writing-issue-consistency {
  text-decoration: underline dashed #7C3AED;
  text-decoration-skip-ink: none;
  text-underline-offset: 2px;
}

/* Voice issues - teal dashed underline */
.writing-issue-voice {
  text-decoration: underline dashed #0D9488;
  text-decoration-skip-ink: none;
  text-underline-offset: 2px;
}

/* Readability - gray dotted underline */
.writing-issue-readability {
  text-decoration: underline dotted #6B7280;
  text-decoration-skip-ink: none;
  text-underline-offset: 2px;
}

/* Hover state for all issues */
.writing-issue-spelling:hover,
.writing-issue-grammar:hover,
.writing-issue-style:hover,
.writing-issue-consistency:hover,
.writing-issue-voice:hover,
.writing-issue-readability:hover {
  background-color: rgba(0, 0, 0, 0.05);
  cursor: pointer;
}
```

**7. Settings Panel**

`frontend/src/components/Settings/WritingFeedbackSettings.tsx`:
- Toggle each issue type on/off
- Adjust sensitivity
- Manage custom dictionary
- Manage ignored rules

**8. Chapter/Manuscript Analysis Panel**

`frontend/src/components/FastCoach/DeepAnalysisPanel.tsx`:
- Trigger full chapter or manuscript analysis
- Show progress indicator
- Display summary of all issues found
- Click-to-navigate to issues in editor

---

## Integration Points

### With Existing Systems

1. **Fast Coach Panel** - Add new tabs for different analysis levels
2. **Editor Toolbar** - Add "Check Grammar" button for manual analysis
3. **Chapter Save** - Option to auto-analyze on save
4. **Export** - Option to show/hide issues in exported documents
5. **Settings Modal** - Global and per-manuscript feedback settings

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl+;` | Jump to next issue |
| `Cmd/Ctrl+Shift+;` | Jump to previous issue |
| `Cmd/Ctrl+.` | Apply first suggestion |
| `Cmd/Ctrl+Shift+G` | Toggle grammar checking |

---

## Performance Considerations

### Real-time Analysis

1. **Debouncing** - Wait 1 second after typing stops
2. **Chunking** - Only analyze recent paragraph (not whole chapter)
3. **Caching** - Cache results for unchanged text
4. **Worker Thread** - Run analysis in Web Worker if possible

### Decoration Rendering

1. **Virtual Rendering** - Only render visible decorations
2. **Batched Updates** - Batch decoration updates
3. **CSS-only** - Use CSS decorations, not DOM elements

### Backend

1. **LanguageTool Server** - Run locally for speed
2. **Caching** - Cache grammar check results
3. **Async** - All analysis is async, non-blocking

---

## Testing Plan

### Unit Tests

- `WritingFeedbackService` - Test each analyzer integration
- `WritingIssueHighlightPlugin` - Test decoration application
- `WritingIssueHoverCard` - Test rendering and interactions

### Integration Tests

- Real-time analysis flow
- Fix application
- Settings persistence

### Manual Testing

- Type with grammar errors, verify underlines appear
- Hover over issues, verify card appears
- Apply fixes, verify text changes
- Toggle settings, verify behavior changes
- Test with large documents (10k+ words)

---

## Migration Path

1. **Week 1**: Deploy backend infrastructure, no frontend changes
2. **Week 2**: Deploy frontend plugin (disabled by default)
3. **Week 3**: Enable for beta users, gather feedback
4. **Week 4**: Enable by default with opt-out

---

## Future Enhancements

1. **AI-Powered Suggestions** - Use LLM for context-aware fixes
2. **Learn from User** - Track accepted/rejected suggestions
3. **Genre-Specific Rules** - Different rules for fantasy vs. literary
4. **Collaboration** - Share custom dictionaries/rules
5. **Statistics** - Track improvement over time

---

## File Summary

### Backend (New Files)

```
backend/app/services/
├── writing_feedback_service.py      # Unified feedback service
├── languagetool_service.py          # LanguageTool integration
└── fast_coach/
    ├── grammar_analyzer.py          # Grammar checking
    ├── readability_analyzer.py      # Readability scores
    ├── sentence_starter_analyzer.py # Sentence variety
    └── overused_phrases_analyzer.py # Overused phrases

backend/app/api/routes/
└── writing_feedback.py              # Feedback API endpoints
```

### Frontend (New Files)

```
frontend/src/
├── components/
│   ├── Editor/
│   │   ├── plugins/
│   │   │   └── WritingIssueHighlightPlugin.tsx
│   │   └── WritingIssueHoverCard.tsx
│   ├── FastCoach/
│   │   ├── DeepAnalysisPanel.tsx
│   │   └── FeedbackSummary.tsx
│   └── Settings/
│       └── WritingFeedbackSettings.tsx
├── stores/
│   └── writingFeedbackStore.ts
├── styles/
│   └── writing-feedback.css
└── types/
    └── writingFeedback.ts
```

---

**Document Version:** 1.0
**Last Updated:** February 3, 2026
