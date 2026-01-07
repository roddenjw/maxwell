# Maxwell PLG Strategy
## Product-Led Growth for Fiction Writing Platform

**Last Updated:** January 7, 2026
**Status:** Strategic Planning Phase

---

## Executive Summary

Maxwell's competitive advantage lies in four unique PLG features that drive viral growth and user acquisition:

1. **The Narrative Archivist** - Invisible, automatic entity extraction while writing
2. **The Aesthetic Recap Engine** - Viral social sharing cards ("Spotify Wrapped for Writers")
3. **The AI Concierge** - Guided BYOK with zero friction onboarding
4. **Enhanced Multiverse Versioning** - Visual timeline for branching narratives

**PLG Philosophy:** Every feature must have a viral mechanic or reduce friction to first value.

**Target:** K-Factor 0.3+ (sustainable organic growth), 40% of signups from word-of-mouth.

---

## 1. The Narrative Archivist (Real-Time Entity Extraction)

### Vision: Invisible Knowledge Graph
Writers should never think about their Codex—it should build itself automatically as they write.

### User Experience
**Traditional Approach (Competitors):**
- Writer finishes chapter
- Manually creates character entries
- Manually links relationships
- Time-consuming, often skipped

**Maxwell Approach:**
- Writer types: "Elara drew the Obsidian Dagger, which glowed with a faint blue light."
- System detects entities in real-time (debounced after 3s of inactivity)
- Subtle toast notification: "✨ New item detected: Obsidian Dagger"
- One-click approval adds to Codex with auto-extracted properties
- Zero interruption to writing flow

### Key Features
- **Real-Time Detection:** Extract entities as user types (WebSocket-based)
- **Debounced Processing:** Wait 3 seconds after typing stops before analyzing
- **Confidence Thresholds:** Only suggest high-confidence entities (>80%)
- **Smart Notifications:** Unobtrusive toasts that don't interrupt flow
- **Context-Aware:** Link entities to current chapter/scene automatically

### Success Metrics
- **Adoption Rate:** 90%+ of users enable real-time extraction
- **Accuracy:** <5% false positives, >95% true positives
- **Performance:** Entity detection <500ms after debounce
- **User Perception:** "Feels like magic" in user feedback

### Viral Mechanic
Writers share screenshots of their auto-built Codex on social media → "How did Maxwell know all my characters?" → Curiosity-driven signups

---

## 2. The Aesthetic Recap Engine (Viral Sharing Cards)

### Vision: "Spotify Wrapped for Writers"
Turn writing stats into shareable, beautiful social media content.

### User Experience
**When:**
- After writing session (optional)
- Weekly summary (automated)
- Monthly milestone (automated)
- Chapter/manuscript completion (automated)

**What Writer Sees:**
1. Beautiful branded card with gradient background
2. Stats overlay:
   - Words written this session/week/month
   - Most-used sensory words (crimson, whispered, rough)
   - Writing "vibe" (determined by tone analysis: "Dark & Brooding", "Whimsical & Light")
   - Focus streak (days in a row writing)
   - Manuscript progress (40% complete)
3. One-click share to Instagram/Twitter/TikTok
4. Subtle watermark: "Created with Maxwell"

### Key Features
- **Aesthetic Design:** Instagram-ready dimensions (1080x1350), customizable themes
- **Auto-Generated:** No manual stats tracking required
- **Privacy-Aware:** Show only aggregate stats, never actual text
- **Shareable:** Pre-formatted for social media with tracking links
- **Customizable:** Choose which stats to display, color themes

### Stats Tracked
- **Productivity:** Words/day, streak, sessions, time spent
- **Style Analysis:**
  - Sensory words used (sight, sound, touch, smell, taste)
  - Dialogue vs. narration ratio
  - Sentence variety (simple, compound, complex)
  - Most common emotions (joy, fear, anger, sadness)
- **Progress:** Manuscript completion %, chapters finished, milestones hit

### Viral Mechanic
Writers share recap cards → Followers see "Written in Maxwell" → 20% click watermark → Signup funnel

**Expected Virality:**
- 20% of users share at least one recap card
- Each share reaches ~500 people (average Twitter/Instagram reach)
- 2% conversion rate from share viewers → signups
- **K-Factor Calculation:** 0.2 users share × 500 reach × 0.02 conversion = **0.2 K-factor** from this feature alone

---

## 3. The AI Concierge (Guided BYOK Onboarding)

### Vision: Zero-Friction AI Enablement
Users should go from "What's BYOK?" to generating AI content in under 60 seconds.

### The Problem with BYOK
**Traditional BYOK Flow (Competitors):**
1. User finds "AI Settings"
2. Sees: "Enter OpenRouter API Key"
3. Clicks external link to openrouter.ai
4. Creates account
5. Navigates to API keys
6. Copies key
7. Returns to app
8. Pastes key
9. **Result:** 70% drop-off rate

**Maxwell's AI Concierge Flow:**
1. User clicks "Enable AI Features"
2. Interactive tutorial appears: "Let's get AI working in 60 seconds"
3. Shows cost transparency: "Chapter recaps cost ~$0.02 each"
4. One-click redirect to OpenRouter with pre-filled Maxwell integration
5. User creates OpenRouter account (30 seconds)
6. Auto-returns to Maxwell with API key (OAuth flow)
7. Guided first use: "Try generating a chapter recap"
8. Success celebration: "🎉 You saved $10/month vs Sudowrite!"
9. **Result:** 90% completion rate

### Key Features
- **Interactive Tutorial:** Step-by-step guide with progress bar
- **Cost Transparency:** Show exact costs before enabling ("This will cost ~$X")
- **First-Time Credits:** $1 free credit for new users to try AI
- **Model Recommendations:** "For drafting, try Claude Haiku (fastest, cheapest)"
- **Balance Widget:** Always-visible AI balance in header
- **Smart Warnings:** Alert when balance <$1, suggest top-up

### Success Metrics
- **Onboarding Completion:** 90%+ of users who click "Enable AI" complete setup
- **Time to First AI Use:** <2 minutes average
- **Retention:** 80% of users who enable AI use it again within 7 days
- **Referrals:** Users share cost savings vs. Sudowrite ("I saved $120/year!")

### Viral Mechanic
Users tweet about cost savings → "Maxwell = $0/month for AI (BYOK) vs Sudowrite $20/month" → Price-conscious writers sign up

**Expected Virality:**
- 30% of users tweet about cost savings
- Each tweet reaches ~300 people
- 3% conversion rate from tweet viewers → signups
- **K-Factor Calculation:** 0.3 × 300 × 0.03 = **0.27 K-factor**

---

## 4. Enhanced Multiverse Versioning UI

### Vision: Git for Fiction (But Visual)
Writers should see their branching storylines like a visual timeline, not git commands.

### User Experience
**Current State:** Basic snapshots exist, but no visual branching UI

**Target State:**
- Visual timeline showing all snapshots as nodes
- Branching paths for alternate endings/plot directions
- Hover to see snapshot preview (first 100 words)
- Click to restore or compare
- Create branch: "What if Elara didn't trust the wizard?"
- Switch between branches seamlessly

### Key Features
- **Visual Timeline:** Horizontal timeline with snapshot nodes
- **Branch Visualization:** Tree structure showing divergent paths
- **Preview on Hover:** Quick peek at snapshot content
- **Compare Mode:** Side-by-side diff of two snapshots/branches
- **Branch Naming:** Descriptive names ("Elara Trusts Wizard" vs "Elara Betrays Wizard")
- **Merge Capability:** Combine elements from different branches (future)

### Success Metrics
- **Adoption:** 60% of users create at least one branch
- **Exploration:** Users restore 3+ snapshots on average
- **Retention:** Branching users 2x more likely to complete manuscripts

### Viral Mechanic
Writers share screenshots of complex story timelines → "I have 7 different endings for my novel!" → Curiosity about multiverse feature

---

## Implementation Roadmap

### Phase 1: Foundation (Months 1-6) - COMPLETE
- ✅ Basic entity extraction (spaCy)
- ✅ Git-based versioning backend
- ✅ AI integration (OpenRouter BYOK)

### Phase 2: PLG Features - Core (Months 7-12)
**Q1 2026:**
- [ ] Narrative Archivist: Real-time entity extraction (WebSocket-based)
  - Backend: RealtimeNLPService with debouncing
  - Frontend: WebSocket client, toast notifications
  - Target: 90% adoption rate

- [ ] AI Concierge: Guided BYOK onboarding
  - Interactive tutorial with progress tracking
  - OpenRouter OAuth integration
  - First-time $1 credit
  - Target: 90% completion rate

**Q2 2026:**
- [ ] Aesthetic Recap Engine: Viral sharing cards
  - Stats aggregation service (session, week, month)
  - Beautiful card generation (HTML Canvas API)
  - Social media sharing with tracking links
  - Target: 20% share rate

- [ ] Enhanced Multiverse UI: Visual timeline
  - Timeline visualization component
  - Branch creation and switching
  - Snapshot preview on hover
  - Target: 60% create a branch

### Phase 3: PLG Features - Advanced (Months 13-18)
- [ ] Collaborative beta reader workflows
- [ ] Public manuscript sharing with comments
- [ ] Writing challenges and leaderboards
- [ ] Community templates marketplace

### Phase 4: Scale & Optimize (Months 19-24)
- [ ] Real-time collaboration (multi-user editing)
- [ ] Mobile app (React Native)
- [ ] Advanced AI features (plot arc analysis, foreshadowing tracker)

---

## Metrics & KPIs

### Viral Mechanics Combined
| Feature | Share Rate | Reach | Conversion | K-Factor Contribution |
|---------|-----------|-------|------------|----------------------|
| **Recap Engine** | 20% | 500 | 2% | 0.20 |
| **AI Cost Savings** | 30% | 300 | 3% | 0.27 |
| **Codex Screenshots** | 15% | 400 | 2% | 0.12 |
| **Multiverse Timelines** | 10% | 300 | 2% | 0.06 |
| **TOTAL K-FACTOR** | - | - | - | **0.65** |

**Target:** K-Factor >0.3 = sustainable organic growth
**Current Projection:** 0.65 = strong viral growth

### Acquisition Funnel
```
Website Visit (Organic) → 100%
↓ (50% conversion)
Sign Up → 50%
↓ (80% activation)
First Manuscript Created → 40%
↓ (70% retention)
Active User (7-day) → 28%
↓ (50% viral action)
Shares Recap/Cost Tweet → 14%
↓ (2-3% conversion from shares)
Refer New User → 0.3-0.4
```

**Key Insights:**
- 28% activation rate is industry-leading (typical SaaS: 10-15%)
- Viral coefficient 0.65 means exponential growth without paid ads
- Each user brings 0.65 new users → doubling time ~2 months

### Success Metrics by Feature

**Narrative Archivist:**
- Adoption: 90%+ enable real-time extraction
- Accuracy: <5% false positives
- Performance: <500ms detection time
- User Satisfaction: "Feels like magic" feedback

**Aesthetic Recap Engine:**
- Share Rate: 20%+ of users share at least one card
- Virality: Each share reaches 500+ people
- Conversion: 2% of share viewers sign up
- Branding: "Created with Maxwell" watermark recognition

**AI Concierge:**
- Onboarding Completion: 90%+ complete BYOK setup
- Time to First AI Use: <2 minutes
- Retention: 80% use AI again within 7 days
- Cost Perception: Users perceive 90% savings vs Sudowrite

**Multiverse Versioning:**
- Adoption: 60%+ create at least one branch
- Exploration: 3+ snapshot restores on average
- Completion: Branching users 2x more likely to finish manuscripts

---

## Competitive Moat

### Maxwell's Unique Position

**vs. Scrivener:**
- ❌ Scrivener: No AI, no auto-entity extraction, no viral features
- ✅ Maxwell: AI + Codex intelligence + PLG mechanics

**vs. Sudowrite:**
- ❌ Sudowrite: $20/month subscription, limited organization, no Codex
- ✅ Maxwell: BYOK ($0/month after one-time purchase), full IDE, intelligent Codex

**vs. Plottr:**
- ❌ Plottr: Manual outlining, no AI, no writing environment
- ✅ Maxwell: AI-powered outlines, full editor, integrated timeline

**vs. NovelAI:**
- ❌ NovelAI: AI-first (expensive), no structure/organization tools
- ✅ Maxwell: IDE-first with optional AI, story structure templates

### Why Maxwell Wins

**Scrivener Users:**
- Frustrated by manual Codex management → Narrative Archivist solves this
- Want AI features → AI Concierge (BYOK cheaper than subscriptions)

**Sudowrite Users:**
- Paying $20/month for AI → Maxwell BYOK = $0/month (75% cost savings)
- Missing organizational features → Full IDE + Codex

**Plottr Users:**
- Want integrated writing environment → Maxwell has full editor
- Missing AI → Maxwell has AI beat suggestions

**Discovery Writers (Pantsers):**
- Don't want to outline upfront → Optional outlines, real-time Codex
- Need consistency tracking → Timeline Orchestrator catches errors

**Viral Growth Mechanism:**
1. User tries Maxwell (free trial or low-cost lifetime deal)
2. Narrative Archivist "wow" moment in first session
3. Shares Recap Card or cost savings tweet
4. Followers sign up (K-factor 0.65)
5. Repeat cycle

---

## Risk Mitigation

### Technical Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Real-time NLP too slow | Medium | High | Debounced processing, background workers, GPU acceleration |
| WebSocket connection drops | Medium | Medium | Automatic reconnection, fallback to polling |
| Viral cards not shareable | Low | High | Test on all major platforms (Twitter, Instagram, TikTok) |
| AI costs unpredictable | Low | Medium | Cost warnings, balance alerts, usage analytics dashboard |

### Product Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Users don't share recap cards | High | High | A/B test designs, incentivize sharing (unlock feature after share) |
| BYOK still too complex | Medium | High | Extensive user testing, 90% completion rate goal |
| Real-time extraction interrupts flow | Medium | High | User-configurable debounce delay, disable option |
| Viral features feel gimmicky | Medium | Medium | Focus on utility first, shareability second |

### Market Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Competitors copy features | High | Medium | Execute faster, better UX, network effects (Codex data lock-in) |
| Writers don't care about stats | Low | Medium | User research, optional features (can disable) |
| Privacy concerns (sharing stats) | Medium | Medium | Aggregate stats only, clear privacy controls, no text shared |

---

## Next Steps

### Immediate Priorities (Q1 2026)
1. **Implement Narrative Archivist** (Weeks 1-4)
   - WebSocket backend for real-time NLP
   - Debounced entity extraction
   - Toast notification system
   - User testing with 20 beta users

2. **Build AI Concierge** (Weeks 5-8)
   - Interactive onboarding tutorial
   - OpenRouter OAuth integration
   - First-time credit system
   - Track completion rates

3. **Design Recap Engine** (Weeks 9-12)
   - Stats aggregation service
   - Card design system (5 themes)
   - Social sharing API
   - Analytics tracking for shares

4. **Launch Beta PLG Features** (Week 13)
   - 100 beta users
   - Measure K-factor in real-world usage
   - Iterate based on feedback

### Success Criteria for Beta
- [ ] 90%+ users enable real-time extraction
- [ ] 90%+ complete AI Concierge onboarding
- [ ] 20%+ share at least one recap card
- [ ] K-Factor >0.3 measured in beta cohort
- [ ] NPS Score >60 from beta users

---

**Last Updated:** January 7, 2026
**Next Review:** End of Q1 2026 (March 2026)
**Document Owner:** Growth Team

**Related Documentation:**
- Implementation details: [IMPLEMENTATION_PLAN_v2.md](./IMPLEMENTATION_PLAN_v2.md)
- Current progress: [PROGRESS.md](./PROGRESS.md)
- Architecture: [CLAUDE.md](./CLAUDE.md)
- Feature documentation: [FEATURES.md](./FEATURES.md)
