"""
NLP service for entity and relationship extraction using spaCy
Handles automated detection of characters, locations, and relationships
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import re

try:
    import spacy
    from spacy.tokens import Doc
    NLP_AVAILABLE = True
except ImportError:
    spacy = None
    Doc = None
    NLP_AVAILABLE = False


class NLPService:
    """Service for NLP-powered entity and relationship extraction"""

    def __init__(self):
        """Initialize NLP service with spaCy model"""
        self.nlp = None
        self.NLP_AVAILABLE = NLP_AVAILABLE

        if NLP_AVAILABLE:
            try:
                # Load large English model for better accuracy
                self.nlp = spacy.load("en_core_web_lg")
            except OSError:
                # Model not downloaded yet
                self.nlp = None
                self.NLP_AVAILABLE = False

    def is_available(self) -> bool:
        """Check if NLP service is available"""
        return self.NLP_AVAILABLE and self.nlp is not None

    def extract_entities(
        self,
        text: str,
        existing_entities: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract named entities from text

        Args:
            text: Text to analyze
            existing_entities: List of known entities to avoid duplicates

        Returns:
            List of detected entities with format:
            {
                "name": str,
                "type": str (CHARACTER, LOCATION, ITEM, LORE),
                "context": str (sentence where found),
                "confidence": float
            }
        """
        if not self.is_available():
            raise RuntimeError("NLP service not available. Install spaCy and download en_core_web_lg model.")

        # Process text
        doc = self.nlp(text)

        # Track existing entity names (case-insensitive)
        known_names = set()
        if existing_entities:
            for entity in existing_entities:
                known_names.add(entity["name"].lower())
                if "aliases" in entity:
                    for alias in entity.get("aliases", []):
                        known_names.add(alias.lower())

        # Extract entities
        detected = []
        seen_in_text = set()  # Avoid duplicates in same text

        for ent in doc.ents:
            # Map spaCy labels to Codex entity types
            entity_type = self._map_entity_type(ent.label_)

            if not entity_type:
                continue

            # Get entity name (capitalized)
            name = ent.text.strip()

            # Skip if already known or seen
            if name.lower() in known_names or name.lower() in seen_in_text:
                continue

            # Get surrounding context (sentence)
            context = ent.sent.text.strip()

            # Calculate confidence based on spaCy label
            confidence = self._calculate_confidence(ent.label_)

            detected.append({
                "name": name,
                "type": entity_type,
                "context": context,
                "confidence": confidence
            })

            seen_in_text.add(name.lower())

        # Also look for proper nouns not caught by NER
        proper_nouns = self._extract_proper_nouns(doc, known_names, seen_in_text)
        detected.extend(proper_nouns)

        # Remove partial names when full name exists
        # E.g., if "Piggy Bob" exists, remove "Piggy" and "Bob"
        detected = self._filter_partial_names(detected)

        # Sort by confidence
        detected.sort(key=lambda x: x["confidence"], reverse=True)

        return detected

    def _map_entity_type(self, spacy_label: str) -> Optional[str]:
        """
        Map spaCy entity labels to Codex types

        spaCy labels: PERSON, GPE (Geopolitical Entity), LOC, FAC (Facility),
                     ORG, PRODUCT, EVENT, WORK_OF_ART, etc.
        """
        mapping = {
            "PERSON": "CHARACTER",
            "GPE": "LOCATION",      # Countries, cities, states
            "LOC": "LOCATION",      # Non-GPE locations (mountains, bodies of water)
            "FAC": "LOCATION",      # Buildings, airports, highways
            "ORG": "LORE",          # Companies, agencies, institutions
            "PRODUCT": "ITEM",      # Objects, vehicles, foods
            "WORK_OF_ART": "ITEM",  # Titles of books, songs
            "EVENT": "LORE",        # Named hurricanes, battles, wars
        }
        return mapping.get(spacy_label)

    def _calculate_confidence(self, spacy_label: str) -> float:
        """Calculate confidence score based on entity label"""
        # PERSON entities are usually most reliable
        high_confidence = {"PERSON": 0.9}
        medium_confidence = {"GPE", "LOC", "FAC"}
        low_confidence = {"ORG", "PRODUCT", "WORK_OF_ART", "EVENT"}

        if spacy_label in high_confidence:
            return high_confidence[spacy_label]
        elif spacy_label in medium_confidence:
            return 0.7
        elif spacy_label in low_confidence:
            return 0.5
        else:
            return 0.3

    def _extract_proper_nouns(
        self,
        doc: "Doc",
        known_names: set,
        seen_in_text: set
    ) -> List[Dict[str, Any]]:
        """
        Extract proper nouns that might be entities missed by NER

        Args:
            doc: spaCy Doc object
            known_names: Set of known entity names
            seen_in_text: Set of already detected entities

        Returns:
            List of potential entities
        """
        proper_nouns = []

        for token in doc:
            # Look for proper nouns (PROPN)
            if token.pos_ == "PROPN":
                name = token.text.strip()

                # Skip if already known or seen
                if name.lower() in known_names or name.lower() in seen_in_text:
                    continue

                # Skip common words and single letters
                if len(name) <= 1 or name.lower() in {"the", "a", "an", "i"}:
                    continue

                # Get context
                context = token.sent.text.strip()

                # Infer type based on surrounding words (simple heuristic)
                entity_type = self._infer_type_from_context(token)

                if entity_type:
                    proper_nouns.append({
                        "name": name,
                        "type": entity_type,
                        "context": context,
                        "confidence": 0.4  # Lower confidence for heuristic detection
                    })

                    seen_in_text.add(name.lower())

        return proper_nouns

    def _infer_type_from_context(self, token) -> Optional[str]:
        """
        Infer entity type from surrounding words

        Args:
            token: spaCy Token object

        Returns:
            Entity type or None
        """
        # Look at surrounding tokens
        sent_text = token.sent.text.lower()

        # Character indicators
        if any(word in sent_text for word in ["said", "asked", "thought", "felt", "looked", "walked"]):
            return "CHARACTER"

        # Location indicators
        if any(word in sent_text for word in ["at", "in", "to", "from", "near"]):
            # Check if it's likely a place name
            if token.i > 0 and token.nbor(-1).text.lower() in {"in", "at", "to", "from", "near"}:
                return "LOCATION"

        # Default to CHARACTER for capitalized words in dialogue/narrative
        return "CHARACTER"

    def _filter_partial_names(self, detected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out partial names when a longer version exists.
        E.g., if "Piggy Bob" exists, remove "Piggy" and "Bob"

        Args:
            detected: List of detected entities

        Returns:
            Filtered list with partial names removed
        """
        if not detected:
            return detected

        # Sort by name length (longest first)
        sorted_entities = sorted(detected, key=lambda x: len(x["name"]), reverse=True)

        # Track names to keep
        keep = []
        kept_words = set()

        for entity in sorted_entities:
            name_words = entity["name"].split()

            # If this is a multi-word name, check if any single words should be removed
            if len(name_words) > 1:
                # Keep this entity
                keep.append(entity)
                # Mark individual words as "covered" by this longer name
                for word in name_words:
                    kept_words.add(word.lower())
            else:
                # Single word name - only keep if not already covered by a longer name
                if entity["name"].lower() not in kept_words:
                    keep.append(entity)

        return keep

    def extract_relationships(
        self,
        text: str,
        known_entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships between known entities

        Args:
            text: Text to analyze
            known_entities: List of known entities with names

        Returns:
            List of relationships with format:
            {
                "source_name": str,
                "target_name": str,
                "type": str (relationship type),
                "context": str (sentence where found),
                "strength": int
            }
        """
        if not self.is_available():
            raise RuntimeError("NLP service not available")

        # Build entity name lookup (case-insensitive)
        entity_lookup = {}
        for entity in known_entities:
            entity_lookup[entity["name"].lower()] = entity
            for alias in entity.get("aliases", []):
                entity_lookup[alias.lower()] = entity

        doc = self.nlp(text)

        relationships = []

        # Method 1: Co-occurrence in same sentence
        co_occurrences = self._find_co_occurrences(doc, entity_lookup)
        relationships.extend(co_occurrences)

        # Method 2: Dependency parsing for explicit relationships
        dependency_rels = self._find_dependency_relationships(doc, entity_lookup)
        relationships.extend(dependency_rels)

        return relationships

    def _find_co_occurrences(
        self,
        doc: "Doc",
        entity_lookup: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find entities that appear together in sentences

        Args:
            doc: spaCy Doc object
            entity_lookup: Dict mapping lowercase names to entities

        Returns:
            List of co-occurrence relationships
        """
        relationships = []

        for sent in doc.sents:
            sent_text = sent.text.lower()

            # Find all entities mentioned in this sentence
            mentioned = []
            for token in sent:
                if token.text.lower() in entity_lookup:
                    mentioned.append(entity_lookup[token.text.lower()])

            # Create relationships between all pairs
            for i, source in enumerate(mentioned):
                for target in mentioned[i + 1:]:
                    # Skip self-relationships
                    if source["name"] == target["name"]:
                        continue

                    # Infer relationship type
                    rel_type = self._infer_relationship_type(sent.text, source, target)

                    relationships.append({
                        "source_name": source["name"],
                        "target_name": target["name"],
                        "type": rel_type,
                        "context": sent.text.strip(),
                        "strength": 1
                    })

        return relationships

    def _find_dependency_relationships(
        self,
        doc: "Doc",
        entity_lookup: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Find relationships using dependency parsing

        Args:
            doc: spaCy Doc object
            entity_lookup: Dict mapping lowercase names to entities

        Returns:
            List of dependency-based relationships
        """
        relationships = []

        for token in doc:
            # Look for entities connected by verbs
            if token.pos_ == "VERB":
                # Find subject and object
                subject = None
                obj = None

                for child in token.children:
                    if child.dep_ in {"nsubj", "nsubjpass"}:
                        if child.text.lower() in entity_lookup:
                            subject = entity_lookup[child.text.lower()]
                    elif child.dep_ in {"dobj", "pobj"}:
                        if child.text.lower() in entity_lookup:
                            obj = entity_lookup[child.text.lower()]

                if subject and obj:
                    # Infer relationship type from verb
                    rel_type = self._infer_relationship_from_verb(token.lemma_)

                    relationships.append({
                        "source_name": subject["name"],
                        "target_name": obj["name"],
                        "type": rel_type,
                        "context": token.sent.text.strip(),
                        "strength": 1
                    })

        return relationships

    def _infer_relationship_type(
        self,
        context: str,
        source: Dict[str, Any],
        target: Dict[str, Any]
    ) -> str:
        """
        Infer relationship type from context

        Args:
            context: Sentence text
            source: Source entity
            target: Target entity

        Returns:
            Relationship type
        """
        context_lower = context.lower()

        # Romantic indicators
        if any(word in context_lower for word in ["love", "kiss", "marry", "romance", "heart"]):
            return "ROMANTIC"

        # Conflict indicators
        if any(word in context_lower for word in ["fight", "battle", "enemy", "hate", "kill", "attack"]):
            return "CONFLICT"

        # Family indicators
        if any(word in context_lower for word in ["mother", "father", "sister", "brother", "family", "son", "daughter"]):
            return "FAMILY"

        # Professional indicators
        if any(word in context_lower for word in ["work", "colleague", "boss", "employee", "partner"]):
            return "PROFESSIONAL"

        # Alliance indicators
        if any(word in context_lower for word in ["ally", "friend", "team", "together", "help"]):
            return "ALLIANCE"

        # Default to acquaintance
        return "ACQUAINTANCE"

    def _infer_relationship_from_verb(self, verb_lemma: str) -> str:
        """
        Infer relationship type from verb

        Args:
            verb_lemma: Lemmatized verb

        Returns:
            Relationship type
        """
        # Map verbs to relationship types
        verb_mapping = {
            "love": "ROMANTIC",
            "kiss": "ROMANTIC",
            "marry": "ROMANTIC",
            "fight": "CONFLICT",
            "attack": "CONFLICT",
            "kill": "CONFLICT",
            "help": "ALLIANCE",
            "support": "ALLIANCE",
            "work": "PROFESSIONAL",
            "meet": "ACQUAINTANCE",
            "know": "ACQUAINTANCE",
        }

        return verb_mapping.get(verb_lemma, "ACQUAINTANCE")

    def extract_entity_descriptions(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        Extract descriptive information about known entities from text.

        Args:
            text: Text to analyze
            entities: List of known entities with names

        Returns:
            Dictionary mapping entity names to categorized descriptions
        """
        if not self.is_available():
            raise RuntimeError("NLP service not available")

        doc = self.nlp(text)

        # Build entity lookup
        entity_lookup = {}
        for entity in entities:
            entity_lookup[entity["name"].lower()] = entity["name"]
            if "aliases" in entity:
                for alias in entity.get("aliases", []):
                    entity_lookup[alias.lower()] = entity["name"]

        # Store descriptions by entity
        descriptions = defaultdict(lambda: {
            "appearance": [],
            "personality": [],
            "actions": [],
            "background": []
        })

        for sent in doc.sents:
            sent_text = sent.text.strip()
            sent_lower = sent_text.lower()

            # Find which entities are mentioned in this sentence
            mentioned_entities = set()
            for token in sent:
                if token.text.lower() in entity_lookup:
                    mentioned_entities.add(entity_lookup[token.text.lower()])

            if not mentioned_entities:
                continue

            # For each mentioned entity, extract descriptive information
            for entity_name in mentioned_entities:
                # Look for descriptive patterns with "was/is/appeared/looked"
                if any(word in sent_lower for word in [" was ", " is ", " were ", " are ", " appeared ", " looked ", " seemed "]):
                    # Appearance keywords
                    if any(word in sent_lower for word in ["tall", "short", "hair", "eyes", "face", "appearance", "looked", "wore", "dressed"]):
                        descriptions[entity_name]["appearance"].append(sent_text)
                    # Personality keywords
                    elif any(word in sent_lower for word in ["brave", "kind", "cruel", "wise", "foolish", "personality", "character", "seemed", "felt"]):
                        descriptions[entity_name]["personality"].append(sent_text)

                # Background/history indicators
                if any(phrase in sent_lower for phrase in ["grew up", "was born", "came from", "lived in", "used to", "had been", "years ago"]):
                    descriptions[entity_name]["background"].append(sent_text)

                # Action sentences (where entity is the subject)
                for token in sent:
                    if token.pos_ == "VERB" and token.dep_ == "ROOT":
                        for child in token.children:
                            if child.dep_ in {"nsubj", "nsubjpass"}:
                                if child.text.lower() in entity_lookup and entity_lookup[child.text.lower()] == entity_name:
                                    # Only add action verbs, not state verbs
                                    if token.lemma_.lower() not in ["be", "have", "seem", "appear", "look"]:
                                        descriptions[entity_name]["actions"].append(sent_text)
                                    break

        # Clean up and deduplicate
        result = {}
        for entity_name, cats in descriptions.items():
            result[entity_name] = {
                category: list(set(items[:10]))  # Max 10 per category, deduplicated
                for category, items in cats.items()
                if items  # Only include non-empty categories
            }

        return result

    def analyze_manuscript(
        self,
        text: str,
        manuscript_id: str,
        existing_entities: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Full analysis of manuscript text

        Args:
            text: Manuscript text
            manuscript_id: Manuscript ID
            existing_entities: List of known entities

        Returns:
            Dict with extracted entities and relationships
        """
        if not self.is_available():
            raise RuntimeError("NLP service not available")

        # Extract entities
        entities = self.extract_entities(text, existing_entities)

        # Extract relationships (using both existing and newly detected entities)
        all_entities = (existing_entities or []) + entities
        relationships = self.extract_relationships(text, all_entities)

        # Extract descriptions for existing entities
        descriptions = {}
        if existing_entities:
            descriptions = self.extract_entity_descriptions(text, existing_entities)

        # Calculate statistics
        stats = {
            "text_length": len(text),
            "entities_found": len(entities),
            "relationships_found": len(relationships),
            "entity_breakdown": self._count_by_type(entities),
            "relationship_breakdown": self._count_by_type(relationships, key="type")
        }

        return {
            "manuscript_id": manuscript_id,
            "entities": entities,
            "relationships": relationships,
            "descriptions": descriptions,
            "stats": stats
        }

    def _extract_actions(self, text: str) -> List[str]:
        """
        Extract main actions/verbs from text to describe what happens

        Args:
            text: Text to analyze

        Returns:
            List of action verbs
        """
        if not self.is_available():
            return []

        doc = self.nlp(text[:500])  # Limit for performance
        actions = []

        # Extract main verbs (root verbs and their objects)
        for sent in doc.sents:
            for token in sent:
                # Look for main verbs
                if token.pos_ == "VERB" and token.dep_ in {"ROOT", "xcomp", "ccomp"}:
                    # Build verb phrase
                    verb_phrase = token.lemma_

                    # Add direct objects
                    for child in token.children:
                        if child.dep_ in {"dobj", "pobj", "attr"}:
                            verb_phrase += f" {child.text}"

                    actions.append(verb_phrase)

        return actions[:5]  # Return top 5 actions

    def _extract_emotional_context(self, text: str) -> Dict[str, Any]:
        """
        Extract emotional context and tone from text with sentiment analysis

        Args:
            text: Text to analyze

        Returns:
            Dict with emotional markers, sentiment score, and intensity
        """
        if not self.is_available():
            return {"tone": "neutral", "emotions": [], "sentiment": 0.0, "intensity": 0.0}

        doc = self.nlp(text[:500])

        # Emotion keywords with weights
        emotion_keywords = {
            "happy": {
                "keywords": ["smiled", "laughed", "joy", "delighted", "cheerful", "grinned",
                           "beaming", "ecstatic", "pleased", "content", "merry", "gleeful"],
                "weight": 1.0
            },
            "sad": {
                "keywords": ["cried", "wept", "sobbed", "tears", "sorrow", "grief",
                           "mourned", "depressed", "melancholy", "downcast", "dejected"],
                "weight": -0.8
            },
            "angry": {
                "keywords": ["shouted", "yelled", "furious", "rage", "angry", "snapped",
                           "enraged", "irate", "livid", "seething", "infuriated"],
                "weight": -0.6
            },
            "afraid": {
                "keywords": ["feared", "scared", "terrified", "panic", "trembled", "afraid",
                           "horrified", "dreaded", "alarmed", "frightened", "petrified"],
                "weight": -0.7
            },
            "surprised": {
                "keywords": ["shocked", "stunned", "amazed", "gasped", "startled",
                           "astonished", "astounded", "bewildered", "dumbfounded"],
                "weight": 0.3
            },
            "tense": {
                "keywords": ["nervous", "anxious", "worried", "tense", "uneasy",
                           "apprehensive", "restless", "edgy", "jittery"],
                "weight": -0.5
            },
            "loving": {
                "keywords": ["loved", "adored", "cherished", "embraced", "kissed",
                           "affectionate", "tender", "caring", "devoted"],
                "weight": 1.0
            },
            "excited": {
                "keywords": ["excited", "thrilled", "eager", "enthusiastic", "animated",
                           "electrified", "energized", "pumped"],
                "weight": 0.8
            }
        }

        detected_emotions = []
        emotion_scores = {}
        text_lower = text.lower()

        # Detect emotions with scoring
        for emotion, data in emotion_keywords.items():
            score = 0
            for keyword in data["keywords"]:
                if keyword in text_lower:
                    score += 1

            if score > 0:
                detected_emotions.append(emotion)
                emotion_scores[emotion] = score * data["weight"]

        # Calculate sentiment using spaCy's sentiment (if available) or keyword-based
        sentiment_score = 0.0
        if emotion_scores:
            sentiment_score = sum(emotion_scores.values()) / len(emotion_scores)

        # Calculate intensity (how strong the emotions are)
        intensity = min(len(detected_emotions) / 3.0, 1.0)  # Normalize to 0-1

        # Determine overall tone based on strongest emotion
        if emotion_scores:
            tone = max(emotion_scores, key=emotion_scores.get)
        elif sentiment_score > 0.2:
            tone = "positive"
        elif sentiment_score < -0.2:
            tone = "negative"
        else:
            tone = "neutral"

        # Additional linguistic analysis
        adjectives = [token.text for token in doc if token.pos_ == "ADJ"]
        adverbs = [token.text for token in doc if token.pos_ == "ADV"]

        return {
            "tone": tone,
            "emotions": detected_emotions,
            "sentiment": round(sentiment_score, 2),
            "intensity": round(intensity, 2),
            "emotion_scores": emotion_scores,
            "adjectives": adjectives[:5],  # Top 5 descriptive words
            "adverbs": adverbs[:3]
        }

    def _detect_scene_transition(self, current_para: str, previous_para: Optional[str] = None) -> bool:
        """
        Detect if there's a scene transition between paragraphs

        Args:
            current_para: Current paragraph
            previous_para: Previous paragraph (if available)

        Returns:
            True if scene transition detected
        """
        transition_markers = [
            "meanwhile",
            "later",
            "the next",
            "hours later",
            "days later",
            "weeks later",
            "somewhere else",
            "across town",
            "back at",
            "at the same time",
            "***",  # Scene break marker
            "---"   # Scene break marker
        ]

        current_lower = current_para.lower()

        # Check for explicit markers
        for marker in transition_markers:
            if marker in current_lower[:100]:  # Check first 100 chars
                return True

        return False

    def _count_by_type(
        self,
        items: List[Dict[str, Any]],
        key: str = "type"
    ) -> Dict[str, int]:
        """Count items by type"""
        counts = defaultdict(int)
        for item in items:
            counts[item[key]] += 1
        return dict(counts)

    # ==================== Timeline Event Extraction ====================

    def extract_events(
        self,
        text: str,
        known_entities: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract timeline events from text

        Args:
            text: Text to analyze
            known_entities: List of known entities (characters, locations)

        Returns:
            List of events with format:
            {
                "description": str,
                "event_type": str (SCENE, CHAPTER, FLASHBACK),
                "timestamp": str (e.g., "Day 3, Morning"),
                "location": str (location name if detected),
                "characters": List[str] (character names involved),
                "order_index": int
            }
        """
        if not self.is_available():
            raise RuntimeError("NLP service not available")

        # Build entity lookup
        entity_lookup = {}
        location_names = set()
        character_names = set()

        if known_entities:
            for entity in known_entities:
                entity_lookup[entity["name"].lower()] = entity
                if "aliases" in entity:
                    for alias in entity.get("aliases", []):
                        entity_lookup[alias.lower()] = entity

                if entity.get("type") == "LOCATION":
                    location_names.add(entity["name"].lower())
                elif entity.get("type") == "CHARACTER":
                    character_names.add(entity["name"].lower())

        doc = self.nlp(text)

        events = []
        order_index = 0

        # Method 1: Detect scene boundaries (paragraph breaks, chapter markers)
        paragraphs = text.split('\n\n')

        for para_idx, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue

            # Check for chapter markers
            if re.match(r'^(Chapter|CHAPTER|ch\.?)\s+\d+', paragraph.strip(), re.IGNORECASE):
                events.append({
                    "description": paragraph.strip()[:200],  # First 200 chars
                    "event_type": "CHAPTER",
                    "timestamp": self._extract_timestamp(paragraph),
                    "location": None,
                    "characters": [],
                    "order_index": order_index,
                    "metadata": {"paragraph_index": para_idx}
                })
                order_index += 1
                continue

            # Check for flashback indicators
            if any(phrase in paragraph.lower() for phrase in ["years ago", "remembered", "flashback", "had been", "used to"]):
                event_type = "FLASHBACK"
            else:
                event_type = "SCENE"

            # Extract characters mentioned in paragraph
            para_doc = self.nlp(paragraph[:1000])  # Limit to first 1000 chars for performance
            characters_in_para = set()
            location_in_para = None

            for token in para_doc:
                token_lower = token.text.lower()
                if token_lower in entity_lookup:
                    entity = entity_lookup[token_lower]
                    if entity.get("type") == "CHARACTER":
                        characters_in_para.add(entity["name"])
                    elif entity.get("type") == "LOCATION" and not location_in_para:
                        location_in_para = entity["name"]

            # Extract timestamp
            timestamp = self._extract_timestamp(paragraph)

            # Create event if it has meaningful content
            if len(paragraph.strip()) > 50:  # Skip very short paragraphs
                # Use first sentence as description
                first_sentence = list(para_doc.sents)[0].text.strip() if list(para_doc.sents) else paragraph[:100]

                # Extract actions and emotional context
                actions = self._extract_actions(paragraph)
                emotional_context = self._extract_emotional_context(paragraph)

                # Detect scene transition
                prev_para = paragraphs[para_idx - 1] if para_idx > 0 else None
                has_transition = self._detect_scene_transition(paragraph, prev_para)

                events.append({
                    "description": first_sentence[:200],
                    "event_type": event_type,
                    "timestamp": timestamp,
                    "location": location_in_para,
                    "characters": list(characters_in_para),
                    "order_index": order_index,
                    "metadata": {
                        "paragraph_index": para_idx,
                        "word_count": len(paragraph.split()),
                        "actions": actions,
                        "tone": emotional_context["tone"],
                        "emotions": emotional_context["emotions"],
                        "sentiment": emotional_context.get("sentiment", 0.0),
                        "intensity": emotional_context.get("intensity", 0.0),
                        "emotion_scores": emotional_context.get("emotion_scores", {}),
                        "adjectives": emotional_context.get("adjectives", []),
                        "adverbs": emotional_context.get("adverbs", []),
                        "has_transition": has_transition
                    }
                })
                order_index += 1

        return events

    def _extract_timestamp(self, text: str) -> Optional[str]:
        """
        Extract temporal expressions from text with enhanced patterns

        Examples:
        - "Day 3, Morning"
        - "June 1850"
        - "Three days later"
        - "Monday morning"
        - "At dawn"
        - "2 hours later"
        """
        text_lower = text.lower()

        # Pattern 1: "Day X" or "Day X, Time"
        day_match = re.search(r'day\s+(\d+)(?:,\s+(morning|afternoon|evening|night|dawn|dusk|midnight|noon))?', text_lower)
        if day_match:
            day_num = day_match.group(1)
            time_of_day = day_match.group(2) or ""
            return f"Day {day_num}{', ' + time_of_day.title() if time_of_day else ''}"

        # Pattern 2: Weekday + time of day
        weekday_match = re.search(r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(morning|afternoon|evening|night|dawn)', text_lower)
        if weekday_match:
            weekday = weekday_match.group(1).title()
            time_of_day = weekday_match.group(2).title()
            return f"{weekday} {time_of_day}"

        # Pattern 3: Relative time expressions (enhanced)
        relative_match = re.search(
            r'(the next day|next morning|next evening|later that day|'
            r'three days later|a week later|hours? later|minutes? later|'
            r'days? later|weeks? later|months? later|years? later|'
            r'moments? later|soon after|shortly after|'
            r'(\d+)\s+(hours?|days?|weeks?|months?|years?)\s+later)',
            text_lower
        )
        if relative_match:
            return relative_match.group(1).title()

        # Pattern 4: Month + Year or Date
        month_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2},?\s+)?(\d{4})', text_lower)
        if month_match:
            month = month_match.group(1).title()
            day = month_match.group(2).strip(', ') if month_match.group(2) else ""
            year = month_match.group(3)
            return f"{month} {day + ' ' if day else ''}{year}"

        # Pattern 5: Time of day keywords
        time_match = re.search(r'\b(at\s+)?(dawn|sunrise|morning|noon|midday|afternoon|dusk|sunset|evening|night|midnight)\b', text_lower)
        if time_match:
            return time_match.group(1).title()

        return None

    def analyze_timeline(
        self,
        text: str,
        manuscript_id: str,
        known_entities: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Full timeline analysis of manuscript text

        Args:
            text: Manuscript text
            manuscript_id: Manuscript ID
            known_entities: List of known entities

        Returns:
            Dict with extracted events and statistics
        """
        if not self.is_available():
            raise RuntimeError("NLP service not available")

        # Extract events
        events = self.extract_events(text, known_entities)

        # Calculate statistics
        stats = {
            "total_events": len(events),
            "event_types": self._count_by_type(events, key="event_type"),
            "events_with_timestamps": sum(1 for e in events if e.get("timestamp")),
            "events_with_locations": sum(1 for e in events if e.get("location")),
            "average_characters_per_event": sum(len(e.get("characters", [])) for e in events) / max(len(events), 1)
        }

        return {
            "manuscript_id": manuscript_id,
            "events": events,
            "stats": stats
        }


# Global instance
nlp_service = NLPService()
