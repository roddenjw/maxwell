# Maxwell PLG Implementation Strategy
## Product-Led Growth Features for Competitive Differentiation

**Last Updated:** December 24, 2025
**Status:** Strategic Planning Phase

---

## Executive Summary

Maxwell's competitive advantage lies in three unique features:
1. **The Narrative Archivist** - Invisible, automatic knowledge graph
2. **The Aesthetic Recap Engine** - Viral social sharing cards
3. **The AI Concierge** - Guided BYOK with zero friction

This document outlines the technical architecture and implementation roadmap for these features.

---

## 1. The Narrative Archivist (Background Entity Extraction)

### Current State
- ✅ spaCy NLP pipeline integrated
- ✅ Entity detection working (CHARACTER, LOCATION, ITEM, LORE)
- ⚠️ **Problem:** Requires manual "Analyze" button click
- ⚠️ **Problem:** Batch processing, not real-time

### Target State: "Magic" Experience
**User writes:** "Elara drew the Obsidian Dagger, which glowed with a faint blue light."

**System responds:**
1. Real-time detection (while typing, with debounce)
2. Subtle toast notification: "✨ New item detected: Obsidian Dagger"
3. One-click approval adds to Codex with auto-extracted properties
4. No interruption to writing flow

### Technical Architecture

#### Backend Changes

**1. WebSocket-Based Real-Time Processing**
```python
# New: /backend/app/services/realtime_nlp_service.py
from fastapi import WebSocket
import asyncio
from typing import Dict, Set

class RealtimeNLPService:
    """Background entity extraction with debouncing"""

    def __init__(self):
        self.pending_analysis: Dict[str, str] = {}
        self.debounce_delay = 2.0  # seconds

    async def analyze_text_chunk(self, text: str, manuscript_id: str):
        """Analyze recent text additions for entities"""
        # Use spaCy to extract entities from ONLY the new text
        entities = await self._extract_entities(text)

        # Cross-reference with existing Codex
        new_entities = await self._filter_new_entities(entities, manuscript_id)

        return {
            "new_entities": new_entities,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def start_background_watcher(self, websocket: WebSocket, manuscript_id: str):
        """Listen for text changes and analyze in background"""
        buffer = ""
        last_analysis = time.time()

        while True:
            # Receive text delta from frontend
            data = await websocket.receive_json()
            buffer += data.get("text_delta", "")

            # Debounce: Only analyze after 2 seconds of no typing
            if time.time() - last_analysis > self.debounce_delay and buffer:
                entities = await self.analyze_text_chunk(buffer, manuscript_id)
                await websocket.send_json(entities)
                buffer = ""
                last_analysis = time.time()
```

**2. New WebSocket Endpoint**
```python
# /backend/app/api/routes/realtime.py
from fastapi import APIRouter, WebSocket

router = APIRouter(prefix="/api/realtime", tags=["realtime"])

@router.websocket("/nlp/{manuscript_id}")
async def websocket_nlp_endpoint(websocket: WebSocket, manuscript_id: str):
    await websocket.accept()

    nlp_service = RealtimeNLPService()

    try:
        await nlp_service.start_background_watcher(websocket, manuscript_id)
    except WebSocketDisconnect:
        # Clean up
        pass
```

#### Frontend Changes

**1. WebSocket Hook**
```typescript
// /frontend/src/hooks/useRealtimeNLP.ts
import { useEffect, useRef } from 'react';
import { useCodexStore } from '@/stores/codexStore';

export function useRealtimeNLP(manuscriptId: string, enabled: boolean = true) {
  const ws = useRef<WebSocket | null>(null);
  const { addSuggestion } = useCodexStore();
  const textBuffer = useRef<string>('');

  useEffect(() => {
    if (!enabled) return;

    // Connect to WebSocket
    ws.current = new WebSocket(
      `ws://localhost:8000/api/realtime/nlp/${manuscriptId}`
    );

    ws.current.onmessage = (event) => {
      const { new_entities } = JSON.parse(event.data);

      // Show toast notification
      if (new_entities.length > 0) {
        showToast(`✨ ${new_entities.length} new entities detected`);

        // Add to suggestion queue
        new_entities.forEach(entity => addSuggestion(entity));
      }
    };

    return () => ws.current?.close();
  }, [manuscriptId, enabled]);

  // Send text deltas to backend
  const sendTextDelta = (text: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ text_delta: text }));
    }
  };

  return { sendTextDelta };
}
```

**2. Integrate with Editor**
```typescript
// Update ManuscriptEditor.tsx
import { useRealtimeNLP } from '@/hooks/useRealtimeNLP';

export default function ManuscriptEditor({ manuscriptId }) {
  const { sendTextDelta } = useRealtimeNLP(manuscriptId);

  const handleEditorChange = (editorState: EditorState) => {
    // Extract text delta (new characters typed)
    const newText = extractNewText(editorState);
    sendTextDelta(newText);
  };
}
```

**3. Subtle Notification UI**
```typescript
// /frontend/src/components/EntityToast.tsx
export function EntityToast({ entity }) {
  return (
    <div className="fixed bottom-4 right-4 bg-bronze/90 text-white px-4 py-3 rounded-lg shadow-lg animate-slide-up">
      <div className="flex items-center gap-3">
        <span className="text-2xl">✨</span>
        <div>
          <p className="font-semibold">New {entity.type} detected</p>
          <p className="text-sm opacity-90">{entity.name}</p>
        </div>
        <button
          onClick={() => approveEntity(entity)}
          className="ml-4 px-3 py-1 bg-white text-bronze rounded-sm text-sm"
        >
          Add to Codex
        </button>
      </div>
    </div>
  );
}
```

### Implementation Priority: **HIGH** (Phase 3)
**Effort:** 2-3 weeks
**Dependencies:** Existing NLP service, WebSocket support

---

## 2. The Aesthetic Recap Engine (Viral Stats Cards)

### Vision: "Spotify Wrapped for Writers"

**User Experience:**
1. Writer finishes a session
2. Clicks "Generate Recap" button (or automatic weekly)
3. Beautiful branded card appears with:
   - Words written this session/week
   - Most used sensory words
   - Writing "vibe" (derived from tone analysis)
   - Focus streak
   - Aesthetic background gradient
4. One-click share to Instagram/TikTok with watermark: "Written in Maxwell"

### Technical Architecture

#### Backend: Stats Aggregation Service

```python
# /backend/app/services/writing_stats_service.py
from datetime import datetime, timedelta
from collections import Counter
import spacy

class WritingStatsService:
    """Calculate writing statistics for recap cards"""

    SENSORY_WORDS = {
        'sight': ['crimson', 'glowing', 'shadowy', 'brilliant'],
        'sound': ['whispered', 'echoed', 'silence', 'roared'],
        'touch': ['rough', 'smooth', 'cold', 'warm'],
        'smell': ['fragrant', 'acrid', 'sweet', 'musty'],
        'taste': ['bitter', 'savory', 'sour', 'sweet']
    }

    async def generate_session_recap(
        self,
        manuscript_id: str,
        user_id: str,
        timeframe: str = 'session'  # 'session', 'day', 'week', 'month'
    ):
        """Generate stats for recap card"""

        # 1. Calculate time range
        if timeframe == 'session':
            start_time = await self._get_last_session_start(user_id)
        elif timeframe == 'week':
            start_time = datetime.utcnow() - timedelta(days=7)

        # 2. Fetch text written in timeframe
        text = await self._get_text_written_since(manuscript_id, start_time)

        # 3. Calculate metrics
        stats = {
            'word_count': len(text.split()),
            'character_count': len(text),
            'paragraph_count': text.count('\n\n'),

            # Advanced metrics
            'sensory_words': self._extract_sensory_words(text),
            'most_used_word': self._get_most_common_word(text),
            'writing_vibe': await self._analyze_emotional_tone(text),
            'focus_streak': await self._calculate_focus_time(user_id, start_time),

            # Comparison metrics
            'vs_yesterday': await self._compare_to_yesterday(manuscript_id, stats),
            'total_this_week': await self._get_week_total(manuscript_id),
        }

        return stats

    def _extract_sensory_words(self, text: str) -> Dict[str, List[str]]:
        """Find sensory words used"""
        words = text.lower().split()
        found = {}

        for sense, word_list in self.SENSORY_WORDS.items():
            matches = [w for w in words if w in word_list]
            if matches:
                found[sense] = Counter(matches).most_common(3)

        return found

    async def _analyze_emotional_tone(self, text: str) -> str:
        """Classify overall writing vibe"""
        # Use sentiment analysis
        doc = nlp_service.nlp(text[:5000])  # Sample

        sentiment = doc._.sentiment  # spaCy sentiment

        if sentiment > 0.5:
            return "Triumphant"
        elif sentiment > 0.2:
            return "Hopeful"
        elif sentiment > -0.2:
            return "Contemplative"
        elif sentiment > -0.5:
            return "Melancholic"
        else:
            return "Dramatic"
```

#### Backend: Image Generation Service

**Option A: PIL/Pillow (Python-based)**
```python
# /backend/app/services/recap_image_service.py
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64

class RecapImageGenerator:
    """Generate aesthetic recap cards"""

    TEMPLATE_PRESETS = {
        'dark': {
            'bg_gradient': ['#1a1a2e', '#16213e', '#0f3460'],
            'text_color': '#e94560',
            'accent_color': '#eaeaea'
        },
        'vintage': {
            'bg_gradient': ['#f4e8c1', '#e8d5b5', '#dcc7a8'],
            'text_color': '#5e3a24',
            'accent_color': '#8b5a3c'
        },
        'neon': {
            'bg_gradient': ['#0a0e27', '#1e2761', '#3d5a80'],
            'text_color': '#ee6c4d',
            'accent_color': '#98c1d9'
        }
    }

    def generate_recap_card(
        self,
        stats: Dict,
        template: str = 'dark',
        format: str = 'instagram_story'  # or 'twitter', 'square'
    ) -> bytes:
        """Generate shareable image"""

        # Dimensions
        if format == 'instagram_story':
            width, height = 1080, 1920
        elif format == 'square':
            width, height = 1080, 1080

        # Create canvas
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)

        # Apply gradient background
        self._draw_gradient(img, self.TEMPLATE_PRESETS[template]['bg_gradient'])

        # Load fonts
        title_font = ImageFont.truetype('fonts/EBGaramond-Bold.ttf', 80)
        stat_font = ImageFont.truetype('fonts/Inter-SemiBold.ttf', 60)
        label_font = ImageFont.truetype('fonts/Inter-Regular.ttf', 40)

        # Layout elements
        y_offset = 200

        # Title
        draw.text(
            (width//2, y_offset),
            "Your Writing Wrapped",
            font=title_font,
            fill=self.TEMPLATE_PRESETS[template]['text_color'],
            anchor='mm'
        )
        y_offset += 150

        # Main stat (word count)
        draw.text(
            (width//2, y_offset),
            f"{stats['word_count']:,}",
            font=ImageFont.truetype('fonts/EBGaramond-Bold.ttf', 120),
            fill=self.TEMPLATE_PRESETS[template]['accent_color'],
            anchor='mm'
        )
        y_offset += 100

        draw.text(
            (width//2, y_offset),
            "words written",
            font=label_font,
            fill=self.TEMPLATE_PRESETS[template]['text_color'],
            anchor='mm'
        )
        y_offset += 150

        # Sensory word highlight
        if stats.get('sensory_words'):
            sense, words = list(stats['sensory_words'].items())[0]
            draw.text(
                (width//2, y_offset),
                f"Most used sensory word:",
                font=label_font,
                fill=self.TEMPLATE_PRESETS[template]['text_color'],
                anchor='mm'
            )
            y_offset += 80

            draw.text(
                (width//2, y_offset),
                words[0][0].title(),
                font=stat_font,
                fill=self.TEMPLATE_PRESETS[template]['accent_color'],
                anchor='mm'
            )
            y_offset += 120

        # Writing vibe
        draw.text(
            (width//2, y_offset),
            f"Writing Vibe: {stats['writing_vibe']}",
            font=stat_font,
            fill=self.TEMPLATE_PRESETS[template]['text_color'],
            anchor='mm'
        )
        y_offset += 150

        # Watermark
        draw.text(
            (width//2, height - 100),
            "Written in Maxwell",
            font=ImageFont.truetype('fonts/EBGaramond-Regular.ttf', 40),
            fill=self.TEMPLATE_PRESETS[template]['text_color'] + '80',  # Semi-transparent
            anchor='mm'
        )

        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG', quality=95)
        return buffer.getvalue()

    def _draw_gradient(self, img: Image, colors: List[str]):
        """Apply vertical gradient"""
        draw = ImageDraw.Draw(img)
        width, height = img.size

        for i in range(height):
            # Interpolate between colors
            ratio = i / height
            if ratio < 0.5:
                color = self._interpolate_color(colors[0], colors[1], ratio * 2)
            else:
                color = self._interpolate_color(colors[1], colors[2], (ratio - 0.5) * 2)

            draw.line([(0, i), (width, i)], fill=color)
```

**Option B: Canvas API (Frontend-based - RECOMMENDED)**
```typescript
// /frontend/src/services/recapCardGenerator.ts
export class RecapCardGenerator {
  async generateCard(stats: WritingStats, template: 'dark' | 'vintage' | 'neon' = 'dark') {
    const canvas = document.createElement('canvas');
    canvas.width = 1080;
    canvas.height = 1920;
    const ctx = canvas.getContext('2d')!;

    // Draw gradient background
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    if (template === 'dark') {
      gradient.addColorStop(0, '#1a1a2e');
      gradient.addColorStop(0.5, '#16213e');
      gradient.addColorStop(1, '#0f3460');
    }
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Title
    ctx.font = 'bold 80px EB Garamond';
    ctx.fillStyle = '#e94560';
    ctx.textAlign = 'center';
    ctx.fillText('Your Writing Wrapped', 540, 200);

    // Main word count
    ctx.font = 'bold 120px EB Garamond';
    ctx.fillStyle = '#eaeaea';
    ctx.fillText(stats.word_count.toLocaleString(), 540, 400);

    ctx.font = '40px Inter';
    ctx.fillStyle = '#e94560';
    ctx.fillText('words written', 540, 500);

    // Sensory word
    if (stats.sensory_words.length > 0) {
      ctx.font = '40px Inter';
      ctx.fillText('Most used sensory word:', 540, 650);

      ctx.font = '60px Inter';
      ctx.fillStyle = '#eaeaea';
      ctx.fillText(stats.sensory_words[0], 540, 730);
    }

    // Writing vibe
    ctx.font = '60px Inter';
    ctx.fillStyle = '#e94560';
    ctx.fillText(`Writing Vibe: ${stats.writing_vibe}`, 540, 900);

    // Watermark
    ctx.font = '40px EB Garamond';
    ctx.fillStyle = 'rgba(233, 69, 96, 0.5)';
    ctx.fillText('Written in Maxwell', 540, 1820);

    // Convert to blob for download/share
    return new Promise<Blob>((resolve) => {
      canvas.toBlob((blob) => resolve(blob!), 'image/png');
    });
  }

  async shareToSocial(blob: Blob) {
    if (navigator.share) {
      const file = new File([blob], 'maxwell-recap.png', { type: 'image/png' });
      await navigator.share({
        files: [file],
        title: 'My Writing Progress',
        text: 'Check out my writing stats! #WritingCommunity #Maxwell'
      });
    } else {
      // Fallback: Download
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'maxwell-recap.png';
      a.click();
    }
  }
}
```

#### Frontend: Recap Modal Component

```typescript
// /frontend/src/components/RecapModal.tsx
import { useState, useEffect } from 'react';
import { RecapCardGenerator } from '@/services/recapCardGenerator';

export function RecapModal({ manuscriptId, onClose }) {
  const [stats, setStats] = useState(null);
  const [template, setTemplate] = useState('dark');
  const [previewUrl, setPreviewUrl] = useState('');
  const cardGen = new RecapCardGenerator();

  useEffect(() => {
    // Fetch stats
    fetch(`/api/stats/recap/${manuscriptId}?timeframe=week`)
      .then(r => r.json())
      .then(data => setStats(data.data));
  }, [manuscriptId]);

  useEffect(() => {
    if (stats) {
      cardGen.generateCard(stats, template).then(blob => {
        setPreviewUrl(URL.createObjectURL(blob));
      });
    }
  }, [stats, template]);

  const handleShare = async () => {
    const blob = await cardGen.generateCard(stats, template);
    await cardGen.shareToSocial(blob);
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="bg-vellum rounded-lg max-w-4xl w-full p-8">
        <h2 className="font-garamond text-3xl text-midnight mb-6">Your Writing Wrapped</h2>

        {/* Template selector */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={() => setTemplate('dark')}
            className={`px-4 py-2 rounded ${template === 'dark' ? 'bg-bronze text-white' : 'bg-slate-ui'}`}
          >
            Dark
          </button>
          <button
            onClick={() => setTemplate('vintage')}
            className={`px-4 py-2 rounded ${template === 'vintage' ? 'bg-bronze text-white' : 'bg-slate-ui'}`}
          >
            Vintage
          </button>
          <button
            onClick={() => setTemplate('neon')}
            className={`px-4 py-2 rounded ${template === 'neon' ? 'bg-bronze text-white' : 'bg-slate-ui'}`}
          >
            Neon
          </button>
        </div>

        {/* Preview */}
        {previewUrl && (
          <img src={previewUrl} alt="Recap card" className="w-full max-w-md mx-auto shadow-2xl rounded-lg mb-6" />
        )}

        {/* Actions */}
        <div className="flex gap-4 justify-center">
          <button
            onClick={handleShare}
            className="px-6 py-3 bg-bronze text-white rounded-lg font-semibold"
          >
            Share to Social
          </button>
          <button
            onClick={onClose}
            className="px-6 py-3 bg-slate-ui text-midnight rounded-lg"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
```

### Implementation Priority: **HIGHEST** (Phase 2)
**Effort:** 2 weeks
**ROI:** Highest for viral growth
**Dependencies:** Stats tracking system

---

## 3. The AI Concierge (Guided BYOK)

### Vision: "One-Click AI Setup"

**User Experience:**
1. User clicks "Enable AI Features"
2. Modal appears: "Add $5 to get started with AI assistance"
3. One Stripe payment, account created with OpenRouter automatically
4. User never sees API keys, developer dashboards, or complex setup
5. In-app balance display shows remaining credits

### Technical Architecture

#### Option A: OpenRouter Integration (RECOMMENDED)

**Why OpenRouter:**
- Aggregates 20+ LLM providers (OpenAI, Anthropic, Google, etc.)
- Single API key for all models
- Pay-as-you-go pricing
- No markup (you pass costs through)
- Has a credits system built-in

```python
# /backend/app/services/ai_wallet_service.py
import httpx
from sqlalchemy.orm import Session

class AIWalletService:
    """Manage user AI credits via OpenRouter"""

    OPENROUTER_API_URL = "https://openrouter.ai/api/v1"

    async def create_user_wallet(self, user_id: str, initial_balance: float = 5.0):
        """Create OpenRouter sub-account for user"""

        # OpenRouter doesn't have sub-accounts, so we track internally
        wallet = AIWallet(
            user_id=user_id,
            balance=initial_balance,
            total_deposited=initial_balance,
            created_at=datetime.utcnow()
        )

        db.add(wallet)
        db.commit()

        return wallet

    async def add_funds(self, user_id: str, amount: float, payment_method_id: str):
        """Add funds via Stripe"""

        # 1. Charge Stripe
        charge = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # cents
            currency='usd',
            payment_method=payment_method_id,
            metadata={'user_id': user_id, 'purpose': 'ai_credits'}
        )

        # 2. Update balance
        wallet = db.query(AIWallet).filter_by(user_id=user_id).first()
        wallet.balance += amount
        wallet.total_deposited += amount

        # 3. Log transaction
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            amount=amount,
            type='DEPOSIT',
            stripe_payment_id=charge.id
        )

        db.add(transaction)
        db.commit()

        return wallet

    async def deduct_usage(self, user_id: str, cost: float, model: str, tokens: int):
        """Deduct cost after AI generation"""

        wallet = db.query(AIWallet).filter_by(user_id=user_id).first()

        if wallet.balance < cost:
            raise InsufficientFundsError()

        wallet.balance -= cost

        transaction = WalletTransaction(
            wallet_id=wallet.id,
            amount=-cost,
            type='USAGE',
            metadata={
                'model': model,
                'tokens': tokens
            }
        )

        db.add(transaction)
        db.commit()

        return wallet

    async def call_ai_model(
        self,
        user_id: str,
        model: str,
        messages: List[Dict],
        max_tokens: int = 500
    ):
        """Make AI call and track costs"""

        # Check balance
        wallet = await self.get_wallet(user_id)
        estimated_cost = self._estimate_cost(model, max_tokens)

        if wallet.balance < estimated_cost:
            raise InsufficientFundsError(f"Need ${estimated_cost:.2f}, have ${wallet.balance:.2f}")

        # Call OpenRouter
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.OPENROUTER_API_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://maxwell.app",
                    "X-Title": "Maxwell IDE"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens
                }
            )

        result = response.json()

        # Calculate actual cost
        actual_cost = self._calculate_cost(
            model,
            result['usage']['prompt_tokens'],
            result['usage']['completion_tokens']
        )

        # Deduct from balance
        await self.deduct_usage(
            user_id,
            actual_cost,
            model,
            result['usage']['total_tokens']
        )

        return result['choices'][0]['message']['content']
```

#### Frontend: Wallet UI

```typescript
// /frontend/src/components/AI/WalletWidget.tsx
export function WalletWidget({ userId }) {
  const [wallet, setWallet] = useState(null);
  const [showTopUp, setShowTopUp] = useState(false);

  useEffect(() => {
    fetch(`/api/ai/wallet/${userId}`)
      .then(r => r.json())
      .then(data => setWallet(data.data));
  }, [userId]);

  if (!wallet) {
    return (
      <button
        onClick={() => setShowTopUp(true)}
        className="px-4 py-2 bg-bronze text-white rounded-lg"
      >
        Enable AI Features
      </button>
    );
  }

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-white border border-slate-ui rounded-lg">
      <div>
        <p className="text-xs text-faded-ink">AI Balance</p>
        <p className="text-lg font-semibold text-midnight">${wallet.balance.toFixed(2)}</p>
      </div>
      <button
        onClick={() => setShowTopUp(true)}
        className="px-3 py-1 text-sm bg-bronze text-white rounded"
      >
        Add Funds
      </button>

      {showTopUp && (
        <TopUpModal
          userId={userId}
          onClose={() => setShowTopUp(false)}
          onSuccess={() => {
            setShowTopUp(false);
            // Reload wallet
          }}
        />
      )}
    </div>
  );
}

// /frontend/src/components/AI/TopUpModal.tsx
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';

export function TopUpModal({ userId, onClose, onSuccess }) {
  const [amount, setAmount] = useState(5);
  const stripe = useStripe();
  const elements = useElements();

  const handleSubmit = async () => {
    const { error, paymentMethod } = await stripe.createPaymentMethod({
      type: 'card',
      card: elements.getElement(CardElement)
    });

    if (!error) {
      // Send to backend
      const response = await fetch('/api/ai/wallet/add-funds', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          amount: amount,
          payment_method_id: paymentMethod.id
        })
      });

      if (response.ok) {
        onSuccess();
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="bg-vellum rounded-lg max-w-md w-full p-8">
        <h2 className="font-garamond text-2xl text-midnight mb-4">Add AI Credits</h2>

        <div className="mb-6">
          <label className="block text-sm font-sans text-faded-ink mb-2">Amount</label>
          <div className="flex gap-2">
            {[5, 10, 20, 50].map(amt => (
              <button
                key={amt}
                onClick={() => setAmount(amt)}
                className={`px-4 py-2 rounded ${amount === amt ? 'bg-bronze text-white' : 'bg-slate-ui'}`}
              >
                ${amt}
              </button>
            ))}
          </div>

          <p className="text-xs text-faded-ink mt-2">
            ~{Math.floor(amount / 0.002)} AI generations (varies by model)
          </p>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-sans text-faded-ink mb-2">Payment Method</label>
          <CardElement className="p-3 border border-slate-ui rounded" />
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleSubmit}
            disabled={!stripe}
            className="flex-1 px-4 py-3 bg-bronze text-white rounded-lg font-semibold"
          >
            Add ${amount}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-3 bg-slate-ui text-midnight rounded-lg"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
```

### Implementation Priority: **MEDIUM** (Phase 4)
**Effort:** 3 weeks
**Dependencies:** User authentication, Stripe integration

---

## 4. Enhanced Multiverse Versioning UI

### Current State
- ✅ Git-based snapshots working
- ✅ Snapshot creation/restoration
- ⚠️ UI is utilitarian, not "magical"

### Target State: Visual Timeline

```typescript
// /frontend/src/components/TimeMachine/TimelineView.tsx
export function MultiverseTimeline({ manuscriptId }) {
  const [snapshots, setSnapshots] = useState([]);
  const [branches, setBranches] = useState([]);

  // Render as visual git-like graph
  return (
    <div className="relative">
      <svg className="w-full h-96">
        {/* Main timeline */}
        <line x1="50" y1="0" x2="50" y2="400" stroke="#9a6f47" strokeWidth="3" />

        {/* Snapshots as nodes */}
        {snapshots.map((snapshot, i) => (
          <g key={snapshot.id}>
            <circle
              cx="50"
              cy={i * 80 + 40}
              r="8"
              fill="#b48e55"
              className="cursor-pointer hover:r-12"
              onClick={() => restoreSnapshot(snapshot.id)}
            />
            <text x="80" y={i * 80 + 45} className="text-sm">
              {snapshot.label}
            </text>
          </g>
        ))}

        {/* Branches */}
        {branches.map((branch, i) => (
          <path
            d={`M 50,${branch.startY} Q 150,${branch.startY + 20} 150,${branch.endY}`}
            stroke="#e94560"
            strokeWidth="2"
            fill="none"
          />
        ))}
      </svg>
    </div>
  );
}
```

---

## Implementation Roadmap

### Phase 1: Foundation (Complete ✅)
- Database schema
- Basic NLP
- Versioning

### Phase 2: Viral Growth Engine (PRIORITY 1) - 3 weeks
**Goal:** Build the feature that drives PLG growth

1. **Week 1:** Stats tracking service
   - Session tracking
   - Word count analytics
   - Sensory word detection
   - Tone analysis

2. **Week 2:** Recap card generator
   - Canvas-based image generation
   - 3 aesthetic templates
   - Social sharing integration

3. **Week 3:** Polish & testing
   - Auto-generate weekly recaps
   - In-app notifications
   - A/B test templates

**Success Metric:** 30% of users share at least one recap card

### Phase 3: The Narrative Archivist (PRIORITY 2) - 3 weeks
**Goal:** Make worldbuilding effortless

1. **Week 1:** WebSocket infrastructure
   - Real-time text streaming
   - Debounced NLP processing

2. **Week 2:** Entity detection pipeline
   - Background extraction
   - Smart notifications
   - One-click approval

3. **Week 3:** UI polish
   - Toast notifications
   - Smooth animations
   - Entity preview cards

**Success Metric:** 50% reduction in manual Codex entries

### Phase 4: AI Concierge (PRIORITY 3) - 4 weeks
**Goal:** Make AI accessible and affordable

1. **Week 1:** OpenRouter integration
   - API wrapper
   - Cost calculator

2. **Week 2:** Wallet system
   - Database schema
   - Transaction logging
   - Balance tracking

3. **Week 3:** Stripe integration
   - Payment flow
   - Top-up modal

4. **Week 4:** AI features
   - Scene generation
   - Character dialogue
   - Prose suggestions

**Success Metric:** 40% of users add funds

---

## Metrics & KPIs

### PLG Metrics
- **Viral Coefficient:** Shares per user (Target: 0.5)
- **Time to Value:** Minutes from signup to first recap card (Target: <5 min)
- **Activation Rate:** Users who create 1st chapter (Target: 70%)

### Engagement Metrics
- **Daily Active Writers:** Users who write 100+ words/day
- **Retention:** D1, D7, D30 (Target: 40%, 25%, 15%)
- **Entity Approval Rate:** % of suggestions approved (Target: 60%)

### Monetization Metrics
- **BYOK Adoption:** % of users who add AI funds (Target: 40%)
- **ARPU:** Average revenue per user (Target: $8/mo)
- **Churn:** Monthly cancellation rate (Target: <5%)

---

## Technical Best Practices

### Performance
- WebSocket connection pooling
- Image generation caching (24hr TTL)
- Debounced NLP (2s delay)

### Security
- Rate limiting on AI calls (10/min per user)
- Stripe PCI compliance
- API key rotation (90 days)

### Scalability
- Async background jobs (Celery/Redis)
- CDN for recap cards (Cloudflare)
- Database read replicas for stats queries

---

## Competitive Moat

**Why competitors can't easily copy:**
1. **Network Effects:** More users → more viral shares → more users
2. **Data Moat:** Every generated recap trains better tone analysis
3. **Aesthetic Lock-in:** Users share branded cards, building Maxwell brand recognition

**Defensibility:**
- The "Wrapped" concept is familiar (Spotify, GitHub) but not yet done for writers
- Aesthetic templates become a design language users identify with
- Real-time NLP requires significant engineering investment

---

**Last Updated:** December 24, 2025
**Next Review:** After Phase 2 completion
