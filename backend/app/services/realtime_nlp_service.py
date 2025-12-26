"""
Real-time NLP Service
Background entity extraction with debouncing for "magic" writing experience
"""

import asyncio
import time
from typing import Dict, List, Set, Optional
from datetime import datetime

from app.services.nlp_service import nlp_service
from app.models.entity import Entity


class RealtimeNLPService:
    """Background entity extraction with debouncing"""

    def __init__(self):
        self.debounce_delay = 2.0  # seconds - wait for user to stop typing
        self.max_text_size = 5000  # Max chars to analyze at once
        self.max_buffer_size = 10000  # Max chars in buffer before dropping
        self.processing_lock: Dict[str, asyncio.Lock] = {}  # One analysis at a time per manuscript
        self.active_connections: Dict[str, int] = {}  # Track connection count per manuscript
        self.max_connections_per_manuscript = 2  # Limit concurrent connections

        # Common words to exclude (false positives)
        self.EXCLUDE_WORDS = {
            # Common verbs
            'fed', 'made', 'found', 'had', 'saw', 'took', 'came', 'went', 'said', 'asked',
            'told', 'knew', 'thought', 'seemed', 'looked', 'felt', 'heard', 'gave', 'left',
            # Common adjectives
            'young', 'old', 'new', 'good', 'bad', 'great', 'small', 'large', 'long', 'short',
            'dark', 'light', 'black', 'white', 'red', 'blue', 'green',
            # Common nouns that aren't entities
            'man', 'woman', 'boy', 'girl', 'person', 'people', 'thing', 'place', 'time',
            'way', 'day', 'night', 'world', 'life', 'death', 'hand', 'face', 'eyes',
            # Pronouns/determiners
            'i', 'he', 'she', 'they', 'we', 'you', 'it', 'this', 'that', 'these', 'those',
        }

    def can_accept_connection(self, manuscript_id: str) -> bool:
        """Check if a new connection can be accepted for this manuscript"""
        return self.active_connections.get(manuscript_id, 0) < self.max_connections_per_manuscript

    def register_connection(self, manuscript_id: str):
        """Register a new connection for this manuscript"""
        self.active_connections[manuscript_id] = self.active_connections.get(manuscript_id, 0) + 1
        if manuscript_id not in self.processing_lock:
            self.processing_lock[manuscript_id] = asyncio.Lock()

    def unregister_connection(self, manuscript_id: str):
        """Unregister a connection for this manuscript"""
        if manuscript_id in self.active_connections:
            self.active_connections[manuscript_id] -= 1
            if self.active_connections[manuscript_id] <= 0:
                del self.active_connections[manuscript_id]
                if manuscript_id in self.processing_lock:
                    del self.processing_lock[manuscript_id]

    async def analyze_text_chunk(
        self,
        text: str,
        manuscript_id: str,
        existing_entities: List[str]
    ) -> Dict:
        """
        Analyze recent text additions for new entities

        Args:
            text: The text chunk to analyze
            manuscript_id: ID of the manuscript
            existing_entities: List of entity names already in Codex

        Returns:
            Dict with new_entities detected
        """
        if not text or not nlp_service.is_available():
            return {"new_entities": []}

        # Enforce text size limit
        if len(text) > self.max_text_size:
            text = text[-self.max_text_size:]  # Take last N chars

        # Get or create lock for this manuscript
        if manuscript_id not in self.processing_lock:
            self.processing_lock[manuscript_id] = asyncio.Lock()

        # Only process one chunk at a time per manuscript
        async with self.processing_lock[manuscript_id]:
            try:
                # Use spaCy to extract entities from new text
                doc = nlp_service.nlp(text)

                detected_entities = []
                existing_set = set(e.lower() for e in existing_entities)

                # Extract named entities
                for ent in doc.ents:
                    entity_name = ent.text.strip()

                    # Skip if already exists, too short, or in exclude list
                    if (entity_name.lower() in existing_set or
                        len(entity_name) < 2 or
                        entity_name.lower() in self.EXCLUDE_WORDS):
                        continue

                    # Map spaCy entity types to our types
                    entity_type = self._map_entity_type(ent.label_)

                    # Only include relevant entity types
                    if entity_type:
                        detected_entities.append({
                            "name": entity_name,
                            "type": entity_type,
                            "context": ent.sent.text if ent.sent else text[:200],
                            "confidence": "spacy_ner"
                        })

                # Also look for capitalized multi-word phrases (potential names/places)
                capitalized_phrases = self._extract_capitalized_phrases(doc, existing_set)
                detected_entities.extend(capitalized_phrases)

                # Remove duplicates (keep first occurrence, prioritize spaCy detections)
                seen = set()
                unique_entities = []
                for entity in detected_entities:
                    # Use just the name as key to avoid duplicate entities with different types
                    key = entity['name'].lower()
                    if key not in seen:
                        seen.add(key)
                        unique_entities.append(entity)

                return {
                    "new_entities": unique_entities[:5],  # Limit to 5 suggestions at a time
                    "timestamp": datetime.utcnow().isoformat()
                }

            except Exception as e:
                print(f"Error in analyze_text_chunk: {e}")
                return {"new_entities": []}

    def _map_entity_type(self, spacy_label: str) -> Optional[str]:
        """Map spaCy entity labels to our EntityType"""
        mapping = {
            'PERSON': 'CHARACTER',
            'GPE': 'LOCATION',  # Geopolitical entity
            'LOC': 'LOCATION',
            'FAC': 'LOCATION',  # Facility
            'ORG': 'LORE',      # Organizations as lore
            'EVENT': 'LORE',
            'WORK_OF_ART': 'ITEM',
            'PRODUCT': 'ITEM',
        }
        return mapping.get(spacy_label)

    def _extract_capitalized_phrases(
        self,
        doc,
        existing_entities: Set[str]
    ) -> List[Dict]:
        """Extract capitalized phrases and proper nouns (potential character names, items, locations)"""
        entities = []

        # Look for sequences of capitalized words
        i = 0
        while i < len(doc):
            token = doc[i]

            # Check if this is a capitalized word
            if token.is_alpha and token.text[0].isupper():
                # Skip if it's a common word or verb/adjective
                if (token.text.lower() in self.EXCLUDE_WORDS or
                    token.pos_ in ['VERB', 'AUX', 'ADJ', 'DET', 'PRON']):
                    i += 1
                    continue

                # Skip sentence-start words unless they're proper nouns
                if token.is_sent_start and token.pos_ != 'PROPN':
                    i += 1
                    continue

                phrase_tokens = [token]
                j = i + 1

                # Collect consecutive capitalized words
                while j < len(doc) and doc[j].is_alpha and doc[j].text[0].isupper():
                    phrase_tokens.append(doc[j])
                    j += 1

                phrase = ' '.join([t.text for t in phrase_tokens])

                # Skip if already exists or too short
                if phrase.lower() in existing_entities or len(phrase) < 2:
                    i = j
                    continue

                # Determine entity type
                # Single capitalized proper noun = likely CHARACTER
                # Multi-word phrase = likely ITEM or LOCATION
                if len(phrase_tokens) == 1:
                    # Check if it looks like a name (capitalized, PROPN tag)
                    if token.pos_ == 'PROPN':
                        entity_type = 'CHARACTER'
                    else:
                        i = j
                        continue
                elif len(phrase_tokens) == 2:
                    # Two-word phrases could be character names or items
                    # Use heuristic: if first word looks like title (Sir, Lord, etc)
                    first_word = phrase_tokens[0].text.lower()
                    if first_word in ['sir', 'lord', 'lady', 'king', 'queen', 'prince', 'princess', 'duke', 'duchess']:
                        entity_type = 'CHARACTER'
                    else:
                        entity_type = 'ITEM'
                else:
                    entity_type = 'LOCATION'

                entities.append({
                    "name": phrase,
                    "type": entity_type,
                    "context": phrase_tokens[0].sent.text if phrase_tokens[0].sent else "",
                    "confidence": "capitalization"
                })

                i = j
            else:
                i += 1

        return entities

    async def process_text_stream(
        self,
        manuscript_id: str,
        existing_entities: List[str],
        text_queue: asyncio.Queue
    ):
        """
        Process incoming text deltas with debouncing and backpressure

        Args:
            manuscript_id: ID of the manuscript
            existing_entities: List of existing entity names
            text_queue: Queue receiving text deltas from client
        """
        buffer = ""
        last_activity = time.time()
        idle_timeout = 300.0  # 5 minutes of inactivity before stopping

        while True:
            try:
                # Non-blocking check for new text
                try:
                    text_delta = await asyncio.wait_for(text_queue.get(), timeout=0.5)

                    # Enforce buffer size limit (backpressure)
                    if len(buffer) + len(text_delta) > self.max_buffer_size:
                        # Drop oldest text to make room
                        overflow = (len(buffer) + len(text_delta)) - self.max_buffer_size
                        buffer = buffer[overflow:]
                        print(f"⚠️  Buffer overflow for {manuscript_id}, dropping {overflow} chars")

                    buffer += text_delta
                    last_activity = time.time()
                except asyncio.TimeoutError:
                    pass

                # Check for idle timeout (cleanup inactive connections)
                time_since_activity = time.time() - last_activity
                if time_since_activity > idle_timeout:
                    print(f"⏱️  Idle timeout for {manuscript_id}, closing stream")
                    break

                # Check if enough time has passed since last activity (debounce)
                if buffer and time_since_activity >= self.debounce_delay:
                    # Analyze the buffered text
                    result = await self.analyze_text_chunk(
                        buffer,
                        manuscript_id,
                        existing_entities
                    )

                    # Clear buffer after analysis
                    buffer = ""

                    # Return detected entities
                    if result['new_entities']:
                        yield result

            except Exception as e:
                print(f"Error in process_text_stream: {e}")
                break


# Singleton instance
realtime_nlp_service = RealtimeNLPService()
