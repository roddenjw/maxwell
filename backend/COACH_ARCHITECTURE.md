# Two-Tier Coaching System Architecture

**Last Updated**: 2025-12-13

---

## Overview

Maxwell IDE uses a **two-tier coaching system** combining instant Python-based analysis with deep AI-powered learning.

### Fast Coach (Python - Real-time)
⚡ **Instant feedback** as you type
- Rule-based + statistical analysis
- No API calls, runs locally
- Always-on, passive assistance
- Shows inline in editor

### Smart Coach (LangChain - On-demand)
🧠 **Deep analysis** when requested
- AI-powered, context-aware
- Learns your patterns over time
- Provides narrative-level feedback
- Requires explicit user action

---

## Fast Coach (Python Services)

### Purpose
Provide **instant, lightweight feedback** that doesn't interrupt flow.

### Analysis Types

#### 1. **Style Analysis** (Real-time)
**Service**: `app/services/fast_coach/style_analyzer.py`

```python
class StyleAnalyzer:
    """Real-time style checks"""

    def analyze(self, text: str) -> List[Suggestion]:
        issues = []

        # Sentence length variation
        sentences = sent_tokenize(text)
        lengths = [len(s.split()) for s in sentences]
        if np.std(lengths) < 2:
            issues.append(Suggestion(
                type="STYLE",
                severity="INFO",
                message="Sentence lengths are very uniform. Consider varying for rhythm.",
                line=0,
                suggestion="Mix short punchy sentences with longer flowing ones."
            ))

        # Passive voice detection
        passive_count = detect_passive_voice(text)
        if passive_count / len(sentences) > 0.3:
            issues.append(Suggestion(
                type="VOICE",
                severity="WARNING",
                message=f"High passive voice usage ({passive_count} instances)",
                suggestion="Consider active voice for stronger prose."
            ))

        return issues
```

**Checks:**
- Sentence length variance (burstiness)
- Readability scores (Flesch-Kincaid)
- Paragraph length
- Passive voice percentage
- Adverb density (ly-words)
- Dialogue tag variety

---

#### 2. **Word Usage Analysis** (Real-time)
**Service**: `app/services/fast_coach/word_analyzer.py`

```python
class WordAnalyzer:
    """Track word usage patterns"""

    WEAK_WORDS = {"just", "really", "very", "quite", "rather", "actually"}
    TELLING_VERBS = {"felt", "thought", "knew", "realized", "wondered"}

    def analyze(self, text: str, context: Dict) -> List[Suggestion]:
        issues = []
        words = word_tokenize(text.lower())

        # Overused weak words
        for weak_word in self.WEAK_WORDS:
            count = words.count(weak_word)
            if count > 3:  # More than 3 in a scene
                issues.append(Suggestion(
                    type="WORD_CHOICE",
                    severity="INFO",
                    message=f"'{weak_word}' used {count} times in this scene",
                    highlight_word=weak_word,
                    suggestion=f"Consider removing or replacing '{weak_word}' for stronger prose."
                ))

        # "Telling" verbs
        for verb in self.TELLING_VERBS:
            if verb in text.lower():
                issues.append(Suggestion(
                    type="SHOW_NOT_TELL",
                    severity="INFO",
                    message=f"Potential telling: '{verb}'",
                    suggestion="Consider showing the emotion/thought through action or dialogue."
                ))

        # Repeated words (within proximity)
        word_positions = defaultdict(list)
        for i, word in enumerate(words):
            if len(word) > 3:  # Ignore short words
                word_positions[word].append(i)

        for word, positions in word_positions.items():
            for i in range(len(positions) - 1):
                if positions[i+1] - positions[i] < 20:  # Within 20 words
                    issues.append(Suggestion(
                        type="REPETITION",
                        severity="INFO",
                        message=f"'{word}' repeated within close proximity",
                        highlight_word=word
                    ))

        return issues
```

**Checks:**
- Weak intensifiers (just, really, very)
- "Telling" verbs (felt, thought, knew)
- Repeated words in proximity
- Cliché detection (regex patterns)
- Filter words (started to, began to)

---

#### 3. **Consistency Checker** (Real-time)
**Service**: `app/services/fast_coach/consistency_checker.py`

```python
class ConsistencyChecker:
    """Check against Codex for contradictions"""

    def __init__(self, db_session):
        self.db = db_session

    def check(self, text: str, manuscript_id: str) -> List[Suggestion]:
        issues = []
        doc = nlp(text)  # spaCy

        # Extract entities mentioned
        entities_mentioned = []
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "GPE", "LOC"]:
                entities_mentioned.append(ent.text)

        # Look up in Codex
        for entity_name in entities_mentioned:
            entity = self.db.query(Entity).filter(
                Entity.manuscript_id == manuscript_id,
                Entity.name == entity_name
            ).first()

            if entity:
                # Check attributes
                # Example: "her blue eyes" when Codex says "green eyes"
                conflicts = self.check_attribute_conflicts(text, entity)
                issues.extend(conflicts)

        return issues

    def check_attribute_conflicts(self, text: str, entity: Entity) -> List[Suggestion]:
        """Check for contradicting descriptions"""
        conflicts = []

        # Simple regex checks for common attributes
        if entity.type == "CHARACTER":
            # Eye color
            if "eyes" in entity.attributes:
                codex_color = entity.attributes["eyes"]
                pattern = rf"{entity.name}'s?\s+(\w+)\s+eyes"
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    text_color = match.group(1)
                    if text_color.lower() != codex_color.lower():
                        conflicts.append(Suggestion(
                            type="CONSISTENCY",
                            severity="WARNING",
                            message=f"Inconsistency: {entity.name}'s eyes are {codex_color} in Codex, but described as {text_color} here",
                            line=0,
                            suggestion=f"Update to '{codex_color}' or revise Codex entry."
                        ))

        return conflicts
```

**Checks:**
- Character attribute consistency (eye color, age, etc.)
- Timeline consistency (date/time references)
- Location consistency (established geography)
- Name consistency (aliases used correctly)

---

#### 4. **Pacing Analyzer** (Real-time)
**Service**: `app/services/fast_coach/pacing_analyzer.py`

```python
class PacingAnalyzer:
    """Analyze story pacing and tension"""

    def analyze_scene(self, text: str) -> PacingMetrics:
        doc = nlp(text)
        sentences = list(doc.sents)

        # Sentence length (action = short, description = long)
        avg_length = np.mean([len(list(s)) for s in sentences])

        # Action verb density
        action_verbs = sum(1 for token in doc if token.pos_ == "VERB" and "Pass" not in token.morph.get("Voice", []))
        verb_density = action_verbs / len(doc) if len(doc) > 0 else 0

        # Dialogue ratio
        dialogue_chars = len(re.findall(r'"[^"]*"', text))
        dialogue_ratio = dialogue_chars / len(text) if len(text) > 0 else 0

        # Tension score (heuristic)
        tension = (
            (1 - avg_length / 25) * 0.4 +  # Shorter sentences = higher tension
            verb_density * 0.4 +             # More verbs = more action
            (1 - dialogue_ratio) * 0.2       # Less dialogue = more description
        )

        return PacingMetrics(
            avg_sentence_length=avg_length,
            verb_density=verb_density,
            dialogue_ratio=dialogue_ratio,
            tension_score=tension,
            suggested_pace="FAST" if tension > 0.6 else "MODERATE" if tension > 0.4 else "SLOW"
        )
```

**Metrics:**
- Average sentence length
- Action verb density
- Dialogue vs. narration ratio
- Tension score (heuristic)
- Pace comparison to previous scenes

---

### Fast Coach UI Integration

**Editor Plugin**: `frontend/src/components/Editor/plugins/FastCoachPlugin.tsx`

```typescript
export function FastCoachPlugin() {
  const [editor] = useLexicalComposerContext();
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);

  useEffect(() => {
    return editor.registerUpdateListener(({ editorState }) => {
      // Debounced analysis (500ms)
      const timer = setTimeout(async () => {
        const text = editorState.read(() => {
          return $getRoot().getTextContent();
        });

        // Call Fast Coach API
        const response = await fetch('/api/fast-coach/analyze', {
          method: 'POST',
          body: JSON.stringify({ text, manuscriptId })
        });

        const results = await response.json();
        setSuggestions(results.suggestions);

        // Apply decorators for inline highlights
        editor.update(() => {
          applyHighlights(results.suggestions);
        });
      }, 500);

      return () => clearTimeout(timer);
    });
  }, [editor]);

  return (
    <div className="fast-coach-panel">
      {suggestions.map(s => (
        <SuggestionCard key={s.id} suggestion={s} />
      ))}
    </div>
  );
}
```

**Visual Feedback:**
- Yellow underline: INFO (style suggestions)
- Orange underline: WARNING (consistency issues)
- Purple wavy: Word choice suggestions
- Green highlight: Strengths to reinforce

---

## Smart Coach (LangChain Agent)

### Purpose
Provide **deep, context-aware analysis** that learns over time.

### When It Runs
- User explicitly requests feedback (button click)
- After completing a scene/chapter
- User asks a specific question

### What It Does Differently
1. **Uses Fast Coach output as context**
   ```python
   def analyze_scene(self, text: str, fast_coach_results: List[Suggestion]):
       prompt = f"""Analyze this scene:

{text}

The Fast Coach detected these issues:
{format_suggestions(fast_coach_results)}

Given your knowledge of the writer's patterns and the story's Codex, provide personalized feedback."""

       return await self.executor.ainvoke({"input": prompt})
   ```

2. **Learns from Fast Coach patterns**
   - If user repeatedly ignores "passive voice" warnings → deprioritize
   - If user always accepts "weak word" suggestions → make them stronger
   - Update WritingProfile based on Fast Coach metrics

3. **Provides narrative-level analysis**
   - "This scene's pacing feels rushed compared to your usual style"
   - "Character X hasn't appeared in 5 scenes - intentional?"
   - "The tension drops here - consider raising stakes"

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER TYPES TEXT                       │
└─────────────────┬───────────────────────────────────────┘
                  │
         ┌────────▼────────┐
         │  Editor State   │
         └────────┬────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
┌───▼────────────┐   ┌─────────▼──────────┐
│  FAST COACH    │   │   USER CLICKS      │
│  (Auto, 500ms) │   │  "Get Feedback"    │
└───┬────────────┘   └─────────┬──────────┘
    │                          │
    │ Python Analysis          │ LangChain Agent
    │ - Style                  │ - Reads Fast Coach results
    │ - Words                  │ - Queries Codex
    │ - Consistency            │ - Checks writing profile
    │ - Pacing                 │ - Uses tools autonomously
    │                          │
┌───▼────────────┐   ┌─────────▼──────────┐
│ Inline         │   │  Side Panel        │
│ Highlights     │   │  Deep Analysis     │
│ (underlines)   │   │  (paragraphs)      │
└────────────────┘   └────────────────────┘
```

---

## Implementation Plan Updates

### New Epic 3.5: Fast Coach (Python Real-time)
**Priority**: High | **Effort**: 3 days

**Tasks:**
1. **Day 1**: Style & Word analyzers
   - `style_analyzer.py` - readability, sentence variance, passive voice
   - `word_analyzer.py` - weak words, repetition, clichés

2. **Day 2**: Consistency & Pacing
   - `consistency_checker.py` - Codex integration
   - `pacing_analyzer.py` - tension metrics

3. **Day 3**: Editor integration
   - `FastCoachPlugin.tsx` - inline highlights
   - API endpoint `/api/fast-coach/analyze`
   - Debouncing and performance optimization

### Updated Epic 3.4: Smart Coach (LangChain)
**Changes:**
- Consumes Fast Coach results as context
- Learns from user reactions to Fast Coach suggestions
- Profile updates based on Fast Coach metrics
- Provides meta-analysis: "You tend to ignore passive voice warnings - is that intentional?"

---

## Data Flow

### Fast Coach Storage
```sql
-- Track which suggestions user accepts/ignores
CREATE TABLE fast_coach_reactions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    suggestion_type TEXT,  -- STYLE, WORD_CHOICE, CONSISTENCY, PACING
    reaction TEXT,          -- ACCEPTED, IGNORED, DISMISSED
    created_at DATETIME
);
```

### Smart Coach Integration
```python
class WritingCoach:
    def _build_system_prompt(self):
        # Include Fast Coach patterns
        fast_coach_stats = self.get_fast_coach_stats()

        return f"""You are a personalized writing coach.

**Fast Coach Patterns:**
- User accepts {fast_coach_stats['weak_words_accept_rate']}% of weak word suggestions
- User ignores {fast_coach_stats['passive_voice_ignore_rate']}% of passive voice warnings
- Most common accepted suggestion: {fast_coach_stats['top_accepted_type']}

When providing feedback, consider these patterns to avoid repeating unhelpful advice."""
```

---

## Performance Considerations

### Fast Coach (must be < 100ms)
- Uses pre-loaded spaCy model
- Caches Codex entities in memory
- Debounced to run 500ms after typing stops
- Only analyzes current paragraph + previous paragraph for context

### Smart Coach (can take 5-10 seconds)
- Shows loading indicator
- Streams results as they arrive
- Caches common queries
- User explicitly triggers, so latency acceptable

---

## User Experience

### Writing Flow
1. User types naturally
2. After 500ms pause → Fast Coach analyzes
3. Inline highlights appear (non-intrusive)
4. User hovers → sees quick suggestion
5. User continues writing OR clicks suggestion to accept/dismiss

### Deep Analysis
1. User finishes scene
2. Clicks "Get Coach Feedback" button
3. Modal shows: "Analyzing your scene..."
4. Results stream in:
   - Overall assessment
   - Specific issues (with context from Fast Coach)
   - Personalized suggestions based on patterns
5. User rates feedback helpful/not helpful
6. Profile updates for next time

---

## Benefits of Two-Tier System

1. **Instant + Thoughtful**: Real-time checks don't interrupt, deep analysis when needed
2. **Cost Effective**: Python is free, LLM only on-demand
3. **Learning Amplified**: Fast Coach patterns inform Smart Coach's advice
4. **Better UX**: Users get immediate value while AI thinks
5. **Offline Capable**: Fast Coach works without internet

---

## Next Steps

1. ✅ Database infrastructure (complete)
2. ⏸️ Fast Coach services (Week 2-3)
3. ⏸️ Smart Coach LangChain agent (Week 10-11)
4. ⏸️ Editor integration (Week 11)

---

**Total Architecture**:
- Fast Coach: 4 Python services, ~800 LOC
- Smart Coach: LangChain agent with tools
- Integration: FastCoachPlugin + API endpoints
- Storage: fast_coach_reactions table + WritingProfile
