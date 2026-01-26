"""
NLP service for entity and relationship extraction using spaCy
Handles automated detection of characters, locations, and relationships
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import re
import os
import json
import time

try:
    import spacy
    from spacy.tokens import Doc
    NLP_AVAILABLE = True
except ImportError:
    spacy = None
    Doc = None
    NLP_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    Anthropic = None
    ANTHROPIC_AVAILABLE = False


class NLPService:
    """Service for NLP-powered entity and relationship extraction"""

    def __init__(self):
        """Initialize NLP service with spaCy model and Anthropic client"""
        self.nlp = None
        self.NLP_AVAILABLE = NLP_AVAILABLE
        self.anthropic_client = None
        self.ANTHROPIC_AVAILABLE = ANTHROPIC_AVAILABLE

        if NLP_AVAILABLE:
            try:
                # Load large English model for better accuracy
                self.nlp = spacy.load("en_core_web_lg")
            except OSError:
                # Model not downloaded yet
                self.nlp = None
                self.NLP_AVAILABLE = False

        # Initialize Anthropic client for intelligent scene extraction
        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                try:
                    self.anthropic_client = Anthropic(api_key=api_key)
                except Exception as e:
                    print(f"⚠️  Failed to initialize Anthropic client: {e}")
                    self.ANTHROPIC_AVAILABLE = False
            else:
                print("⚠️  ANTHROPIC_API_KEY not set - intelligent scene extraction unavailable")
                self.ANTHROPIC_AVAILABLE = False

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

            # Extract description if available
            description = self._extract_description(ent, doc)

            # Calculate confidence based on spaCy label
            confidence = self._calculate_confidence(ent.label_)

            entity_dict = {
                "name": name,
                "type": entity_type,
                "context": context,
                "confidence": confidence
            }

            # Add description if found
            if description:
                entity_dict["description"] = description

            # Extract attributes for this entity from surrounding text
            if entity_type == "CHARACTER":
                extracted_attrs = self._extract_entity_attributes_from_context(ent.sent.text, name)
                if extracted_attrs:
                    entity_dict["extracted_attributes"] = extracted_attrs

            detected.append(entity_dict)

            seen_in_text.add(name.lower())

        # Also look for proper nouns not caught by NER
        proper_nouns = self._extract_proper_nouns(doc, known_names, seen_in_text)
        detected.extend(proper_nouns)

        # Extract entities from descriptive patterns (e.g., "The alhastra is a kind of...")
        pattern_entities = self._extract_from_descriptive_patterns(doc, known_names, seen_in_text)
        detected.extend(pattern_entities)

        # Remove partial names when full name exists
        # E.g., if "Piggy Bob" exists, remove "Piggy" and "Bob"
        detected = self._filter_partial_names(detected)

        # Remove duplicates (keep highest confidence version)
        detected = self._remove_duplicate_entities(detected)

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
        Extract proper nouns that might be entities missed by NER.
        Groups consecutive proper nouns together (e.g., "Farid Sa Garai" as one entity)

        Args:
            doc: spaCy Doc object
            known_names: Set of known entity names
            seen_in_text: Set of already detected entities

        Returns:
            List of potential entities
        """
        proper_nouns = []

        # Group consecutive proper nouns together
        i = 0
        tokens = list(doc)

        while i < len(tokens):
            token = tokens[i]

            # Look for proper nouns (PROPN)
            if token.pos_ == "PROPN":
                # Collect consecutive proper nouns, including connecting words
                name_parts = [token.text.strip()]
                j = i + 1

                # Look ahead for more consecutive proper nouns
                # Also include common connecting words like "of", "the", "and"
                connecting_words = {"of", "the", "and"}

                while j < len(tokens):
                    if tokens[j].pos_ == "PROPN":
                        name_parts.append(tokens[j].text.strip())
                        j += 1
                    elif tokens[j].text.lower() in connecting_words and j + 1 < len(tokens) and tokens[j + 1].pos_ == "PROPN":
                        # Include connecting word if followed by another PROPN
                        name_parts.append(tokens[j].text.strip())
                        j += 1
                    else:
                        break

                # Join into full name
                name = " ".join(name_parts)

                # Skip if already known or seen
                if name.lower() not in known_names and name.lower() not in seen_in_text:
                    # Skip common words and single letters
                    if len(name) > 1 and name.lower() not in {"the", "a", "an", "i"}:
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

                # Skip ahead past the grouped proper nouns
                i = j
            else:
                i += 1

        return proper_nouns

    def _extract_description(self, ent, doc) -> Optional[str]:
        """
        Extract description for an entity from surrounding context.
        Looks for patterns like "X is a..." or "X was a..."

        Args:
            ent: spaCy entity
            doc: spaCy Doc object

        Returns:
            Description string or None
        """
        entity_name_lower = ent.text.lower()
        sent = ent.sent

        # Look for descriptive patterns in the sentence
        sent_text = sent.text
        sent_lower = sent_text.lower()

        # Pattern: "The X is a..." or "X is a kind of..." etc.
        descriptive_patterns = [
            f"{entity_name_lower} is a",
            f"{entity_name_lower} was a",
            f"the {entity_name_lower} is",
            f"the {entity_name_lower} was",
            f"an {entity_name_lower} is",
            f"a {entity_name_lower} is"
        ]

        for pattern in descriptive_patterns:
            if pattern in sent_lower:
                # Extract from the pattern onwards
                start_idx = sent_lower.index(pattern)
                # Get the rest of the sentence after entity name
                description = sent_text[start_idx:].strip()

                # Clean up the description
                # Remove leading articles and entity name
                description = description.split(' is ', 1)[-1] if ' is ' in description else description
                description = description.split(' was ', 1)[-1] if ' was ' in description else description

                # Capitalize first letter
                if description:
                    description = description[0].upper() + description[1:]
                    return description

        # Also check next sentence for continuing description
        # Find sentence index
        for i, s in enumerate(doc.sents):
            if s == sent and i < len(list(doc.sents)) - 1:
                next_sent = list(doc.sents)[i + 1]
                next_lower = next_sent.text.lower()

                # If next sentence starts with descriptive words, include it
                if any(next_lower.startswith(word) for word in ['it ', 'this ', 'the creature', 'the beast']):
                    # Combine sentences
                    combined = sent.text + " " + next_sent.text
                    return combined.strip()

        return None

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
        entity_name_lower = token.text.lower()

        # Creature/Item/Lore indicators (check these first as they're more specific)
        creature_patterns = [
            "is a kind of", "is a type of", "is a species of",
            "creature", "beast", "monster", "animal", "insect", "arachnid",
            "lives in", "inhabits", "found in"
        ]
        if any(pattern in sent_text for pattern in creature_patterns):
            # Check if the entity name appears before these patterns
            if any(pattern in sent_text.split(entity_name_lower, 1)[-1][:100] for pattern in creature_patterns):
                return "LORE"

        # Item/object indicators
        item_patterns = ["weapon", "sword", "dagger", "artifact", "relic", "tool", "device"]
        if any(pattern in sent_text for pattern in item_patterns):
            return "ITEM"

        # Character indicators
        character_patterns = ["said", "asked", "thought", "felt", "looked", "walked",
                            "spoke", "replied", "answered", "whispered", "shouted",
                            "he ", "she ", "they ", "his ", "her ", "their "]
        if any(word in sent_text for word in character_patterns):
            return "CHARACTER"

        # Location indicators
        location_patterns = {"in", "at", "to", "from", "near", "within", "outside"}
        if token.i > 0 and token.nbor(-1).text.lower() in location_patterns:
            return "LOCATION"

        # Default to CHARACTER for capitalized words in dialogue/narrative
        return "CHARACTER"

    def _filter_partial_names(self, detected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter out partial names when a longer version exists.
        E.g., if "Farid Sa Garai Fol Jahan" exists, remove "Garai Fol Jahan"
        Or if "Piggy Bob" exists, remove "Piggy" and "Bob"

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
        kept_names = set()

        for entity in sorted_entities:
            entity_name_lower = entity["name"].lower()
            is_partial = False

            # Check if this name is contained in any already-kept longer name
            for kept_name in kept_names:
                # Check if this entity's name is a substring of a longer kept name
                # (accounting for word boundaries)
                words_in_entity = set(entity_name_lower.split())
                words_in_kept = set(kept_name.split())

                # If all words in this entity are in the kept name, and kept has more words, it's partial
                if words_in_entity.issubset(words_in_kept) and len(words_in_entity) < len(words_in_kept):
                    is_partial = True
                    break

                # Also check direct substring match (e.g., "Garai Fol Jahan" in "Farid Sa Garai Fol Jahan")
                if entity_name_lower in kept_name and entity_name_lower != kept_name:
                    is_partial = True
                    break

            if not is_partial:
                keep.append(entity)
                kept_names.add(entity_name_lower)

        return keep

    def _extract_from_descriptive_patterns(
        self,
        doc: "Doc",
        known_names: set,
        seen_in_text: set
    ) -> List[Dict[str, Any]]:
        """
        Extract entities from descriptive patterns even if not capitalized.
        E.g., "The alhastra is a kind of arachnid..."

        This catches entities that spaCy NER misses because they're lowercase
        or fictional/uncommon words.

        Args:
            doc: spaCy Doc object
            known_names: Set of known entity names
            seen_in_text: Set of already detected entities

        Returns:
            List of detected entities
        """
        pattern_entities = []

        # Patterns that indicate an entity description
        descriptive_patterns = [
            r"(?:the|an?)\s+(\w+)\s+(?:is|was)\s+(?:a kind of|a type of|a species of)",
            r"(?:the|an?)\s+(\w+)\s+(?:is|was)\s+a\s+\w+\s+(?:creature|beast|monster|animal)",
            r"(?:the|an?)\s+(\w+)\s+(?:lives|inhabits|dwells|hunts)",
        ]

        import re

        for sent in doc.sents:
            sent_text = sent.text
            sent_lower = sent_text.lower()

            for pattern in descriptive_patterns:
                matches = re.finditer(pattern, sent_lower, re.IGNORECASE)
                for match in matches:
                    entity_name = match.group(1).strip()

                    # Skip if already known or seen
                    if entity_name.lower() in known_names or entity_name.lower() in seen_in_text:
                        continue

                    # Skip common words
                    if entity_name.lower() in {"it", "this", "that", "there", "here", "one", "thing"}:
                        continue

                    # Extract description from the full sentence
                    description = self._extract_description_from_sentence(
                        entity_name, sent_text
                    )

                    # Determine type based on pattern
                    entity_type = "LORE"  # Default for creatures/beasts/etc

                    pattern_entities.append({
                        "name": entity_name.capitalize(),
                        "type": entity_type,
                        "context": sent_text.strip(),
                        "confidence": 0.75,  # Medium-high confidence for pattern matches
                        "description": description if description else None
                    })

                    seen_in_text.add(entity_name.lower())

        return [e for e in pattern_entities if e["description"]]  # Only return if we found a description

    def _extract_entity_attributes_from_context(self, context: str, entity_name: str) -> Optional[Dict[str, List[str]]]:
        """
        Extract categorized attributes for an entity from context sentence.

        Args:
            context: Context sentence/paragraph
            entity_name: Name of the entity

        Returns:
            Dictionary with categorized attributes or None
        """
        if not context or len(context) < 10:
            return None

        context_lower = context.lower()
        attributes = {}

        # Appearance keywords
        appearance_keywords = [
            "tall", "short", "thin", "fat", "slim", "muscular", "lean", "stocky",
            "hair", "eyes", "face", "beard", "scar", "young", "old", "elderly",
            "beautiful", "handsome", "ugly", "pale", "dark", "fair", "wore", "dressed",
            "blonde", "brunette", "redhead", "gray-haired", "silver", "curly", "straight"
        ]

        # Personality keywords
        personality_keywords = [
            "brave", "coward", "kind", "cruel", "wise", "foolish", "gentle", "harsh",
            "calm", "nervous", "confident", "shy", "stubborn", "flexible", "loyal",
            "treacherous", "honest", "deceitful", "patient", "impatient", "warm", "cold",
            "cheerful", "gloomy", "optimistic", "pessimistic", "friendly", "hostile"
        ]

        # Check for appearance words
        found_appearance = []
        for keyword in appearance_keywords:
            if keyword in context_lower:
                found_appearance.append(keyword)

        # Check for personality words
        found_personality = []
        for keyword in personality_keywords:
            if keyword in context_lower:
                found_personality.append(keyword)

        if found_appearance:
            attributes["appearance"] = found_appearance[:5]  # Limit to 5
        if found_personality:
            attributes["personality"] = found_personality[:5]

        return attributes if attributes else None

    def _extract_description_from_sentence(self, entity_name: str, sentence: str) -> Optional[str]:
        """
        Extract description for an entity from a sentence.

        Args:
            entity_name: Name of the entity
            sentence: Sentence text

        Returns:
            Description or None
        """
        entity_lower = entity_name.lower()
        sent_lower = sentence.lower()

        # Find where "is/was a" occurs after the entity name and extract what follows
        for verb in [' is ', ' was ']:
            # Try patterns like "the alhastra is" or just "alhastra is"
            for prefix in ['the ', 'an ', 'a ', '']:
                pattern = f"{prefix}{entity_lower}{verb}"
                if pattern in sent_lower:
                    # Find the position after the pattern
                    idx = sent_lower.find(pattern) + len(pattern)
                    # Extract everything after "is/was"
                    description = sentence[idx:].strip()
                    if description and len(description) > 3:  # Ensure it's not empty
                        # Capitalize first letter
                        return description[0].upper() + description[1:]

        return None

    def _remove_duplicate_entities(self, detected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate entities, keeping the one with highest confidence.

        Args:
            detected: List of detected entities

        Returns:
            Deduplicated list
        """
        seen = {}

        for entity in detected:
            name_lower = entity["name"].lower()

            if name_lower not in seen:
                seen[name_lower] = entity
            else:
                # Keep the one with higher confidence
                if entity["confidence"] > seen[name_lower]["confidence"]:
                    seen[name_lower] = entity

        return list(seen.values())

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

    def _is_dialogue(self, paragraph: str) -> bool:
        """
        Check if paragraph is primarily dialogue

        Args:
            paragraph: Text to check

        Returns:
            True if paragraph appears to be dialogue
        """
        # Count various quotation marks
        quote_count = (
            paragraph.count('"') +
            paragraph.count('"') +
            paragraph.count('"') +
            paragraph.count("'") +
            paragraph.count("'") +
            paragraph.count("'")
        )

        # Dialogue if has multiple quotes or starts with quote
        stripped = paragraph.strip()
        starts_with_quote = stripped.startswith(('"', '"', '"', "'", "'", "'"))

        return quote_count >= 2 or starts_with_quote

    def _detect_flashback_conservative(self, paragraph: str) -> bool:
        """
        Conservative flashback detection using word-boundary regex
        Requires multiple indicators to reduce false positives

        Args:
            paragraph: Text to check

        Returns:
            True if flashback detected with high confidence
        """
        import re

        # Exclude dialogue from flashback detection
        if self._is_dialogue(paragraph):
            return False

        # Flashback patterns with word boundaries
        FLASHBACK_PATTERNS = [
            r'\b(years?|months?|days?|decades?) (ago|earlier|before)\b',
            r'\b(remembered|recalled|thought back|reminisced)\b',
            r'\b(flashback|memory)\b',
            r'\b(had been|had gone|had seen|had done)\b.*\b(years?|ago)\b'
        ]

        # Count pattern matches
        matches = 0
        for pattern in FLASHBACK_PATTERNS:
            if re.search(pattern, paragraph, re.IGNORECASE):
                matches += 1

        # Conservative: require at least 2 different pattern matches
        return matches >= 2

    def _detect_characters_with_ner(self, para_doc, entity_lookup: dict) -> tuple[set, list]:
        """
        Detect characters using both entity_lookup and spaCy NER fallback

        Args:
            para_doc: spaCy Doc object
            entity_lookup: Dictionary of known entities

        Returns:
            Tuple of (registered_character_names, detected_person_names)
        """
        characters_in_para = set()
        detected_persons = []

        # Common pronouns, titles, and words to filter out
        FILTER_WORDS = {
            'I', 'You', 'He', 'She', 'They', 'We', 'It', 'Me', 'Him', 'Her', 'Us', 'Them',
            'Mr', 'Mrs', 'Ms', 'Dr', 'Sir', 'Lady', 'Lord', 'Master', 'Miss',
            'The', 'A', 'An', 'That', 'This', 'These', 'Those',
            'Come', 'Run', 'Go', 'Get', 'Make', 'Take', 'Give', 'Tell', 'Ask',
            'Jaw', 'Hand', 'Head', 'Face', 'Eye', 'Arm', 'Leg', 'Back', 'Heart',
            'Time', 'Day', 'Night', 'Way', 'Thing', 'Man', 'Woman', 'Boy', 'Girl',
            'God', 'Lord', 'Father', 'Mother', 'Brother', 'Sister', 'Son', 'Daughter'
        }

        # Common verbs that spaCy often mistakes as names
        COMMON_VERBS = {
            'run', 'come', 'go', 'get', 'make', 'take', 'give', 'tell', 'ask', 'see',
            'know', 'think', 'want', 'look', 'use', 'find', 'work', 'call', 'try', 'feel',
            'leave', 'put', 'mean', 'keep', 'let', 'begin', 'seem', 'help', 'talk', 'turn',
            'start', 'show', 'hear', 'play', 'run', 'move', 'live', 'believe', 'bring', 'happen'
        }

        # First pass: Check registered entities
        for token in para_doc:
            token_lower = token.text.lower()
            if token_lower in entity_lookup:
                entity = entity_lookup[token_lower]
                if entity.get("type") == "CHARACTER":
                    characters_in_para.add(entity["name"])

        # Second pass: NER fallback for unregistered characters
        for ent in para_doc.ents:
            if ent.label_ == "PERSON":
                person_name = ent.text.strip()
                person_lower = person_name.lower()

                # Clean up possessive forms (e.g., "Alnat's" -> "Alnat")
                if person_name.endswith("'s"):
                    person_name = person_name[:-2]
                    person_lower = person_name.lower()

                # More aggressive filtering:
                # 1. Must be at least 2 characters
                # 2. Not in filter words
                # 3. Not a common verb
                # 4. Not all uppercase (acronyms)
                # 5. Must start with capital letter
                # 6. If single word, must be at least 3 characters (avoids "Go", "Me", etc.)
                is_valid = (
                    len(person_name) >= 2 and
                    person_name not in FILTER_WORDS and
                    person_lower not in COMMON_VERBS and
                    not person_name.isupper() and
                    person_name[0].isupper() and
                    (len(person_name.split()) > 1 or len(person_name) >= 3)
                )

                if is_valid:
                    # Check if already in registered entities
                    is_registered = any(
                        person_name.lower() == name.lower()
                        for name in characters_in_para
                    )

                    if not is_registered:
                        # Check if it's a known entity name
                        name_in_lookup = any(
                            person_name.lower() in key or key in person_name.lower()
                            for key in entity_lookup.keys()
                        )

                        if not name_in_lookup and person_name not in detected_persons:
                            detected_persons.append(person_name)

        return characters_in_para, detected_persons

    def extract_scenes_with_llm(
        self,
        text: str,
        manuscript_id: str,
        known_entities: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract timeline scenes using LLM for intelligent understanding

        This method:
        1. Chunks text into meaningful segments (chapters, section breaks, etc.)
        2. Uses Claude API to understand and summarize each scene
        3. Extracts characters, locations, and key events
        4. Returns properly structured scene data

        Args:
            text: Full manuscript text
            manuscript_id: ID of the manuscript
            known_entities: List of registered characters and locations

        Returns:
            List of scene dictionaries with descriptions, characters, locations, etc.
        """
        if not self.ANTHROPIC_AVAILABLE or not self.anthropic_client:
            print("⚠️  Anthropic API not available - falling back to basic extraction")
            return self.extract_events(text, manuscript_id, known_entities)

        print("🎬 Using intelligent LLM-based scene extraction...")

        # Build character and location lists for the LLM
        character_names = []
        location_names = []
        if known_entities:
            for entity in known_entities:
                if entity.get("type") == "CHARACTER":
                    character_names.append(entity["name"])
                elif entity.get("type") == "LOCATION":
                    location_names.append(entity["name"])

        # Split text into chunks (by chapter or section breaks)
        chunks = self._chunk_text_into_scenes(text)
        print(f"📚 Split manuscript into {len(chunks)} potential scenes")

        scenes = []
        order_index = 0

        # Process each chunk with LLM
        for chunk_idx, chunk in enumerate(chunks):
            if not chunk.strip() or len(chunk.strip()) < 100:
                continue

            print(f"🔍 Analyzing chunk {chunk_idx + 1}/{len(chunks)}...")

            try:
                # Call Claude API to extract scene information
                prompt = self._build_scene_extraction_prompt(
                    chunk,
                    character_names,
                    location_names
                )

                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",  # Using Haiku - fastest and most accessible
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # Parse response
                scene_data = self._parse_scene_response(response.content[0].text)

                if scene_data and scene_data.get("description"):
                    scene_data["order_index"] = order_index
                    scene_data["metadata"] = scene_data.get("metadata", {})
                    scene_data["metadata"]["auto_generated"] = True
                    scene_data["metadata"]["chunk_index"] = chunk_idx
                    scene_data["metadata"]["word_count"] = len(chunk.split())

                    scenes.append(scene_data)
                    order_index += 1

                # Rate limiting: wait 1 second between API calls to avoid hitting rate limits
                # This is especially important for large manuscripts with many chunks
                time.sleep(1.0)

            except Exception as e:
                print(f"⚠️  Failed to process chunk {chunk_idx}: {e}")
                # On error, wait a bit longer before retrying next chunk
                time.sleep(2.0)
                continue

        print(f"✅ Extracted {len(scenes)} scenes using LLM")
        return scenes

    def _chunk_text_into_scenes(self, text: str) -> List[str]:
        """
        Chunk text into potential scenes based on structural markers

        Looks for:
        - Chapter breaks
        - Section breaks (*** or ---)
        - Major paragraph breaks
        """
        chunks = []

        # First, split by chapter markers
        chapter_pattern = r'\n\s*(Chapter|CHAPTER|Ch\.?)\s+\d+[^\n]*\n'
        chapters = re.split(chapter_pattern, text)

        for chapter in chapters:
            if not chapter.strip():
                continue

            # Look for section breaks within chapters
            section_breaks = re.split(r'\n\s*[*\-]{3,}\s*\n', chapter)

            for section in section_breaks:
                if not section.strip():
                    continue

                # If section is very long (> 2000 words), split by large paragraph breaks
                words = section.split()
                if len(words) > 2000:
                    # Split by double newlines and group paragraphs
                    paragraphs = section.split('\n\n')
                    current_chunk = []
                    current_word_count = 0

                    for para in paragraphs:
                        para_words = len(para.split())
                        if current_word_count + para_words > 1500 and current_chunk:
                            # Save current chunk
                            chunks.append('\n\n'.join(current_chunk))
                            current_chunk = [para]
                            current_word_count = para_words
                        else:
                            current_chunk.append(para)
                            current_word_count += para_words

                    if current_chunk:
                        chunks.append('\n\n'.join(current_chunk))
                else:
                    # Section is reasonable size, use as-is
                    chunks.append(section)

        return chunks

    def _build_scene_extraction_prompt(
        self,
        text: str,
        character_names: List[str],
        location_names: List[str]
    ) -> str:
        """Build prompt for Claude to extract scene information"""

        char_list = ", ".join(character_names) if character_names else "None registered yet"
        loc_list = ", ".join(location_names) if location_names else "None registered yet"

        return f"""Analyze this story excerpt and extract the key scene information.

EXCERPT:
{text[:3000]}

KNOWN CHARACTERS: {char_list}
KNOWN LOCATIONS: {loc_list}

Please provide a JSON response with:
1. "description": A concise 1-2 sentence summary of what happens in this scene
2. "characters": List of character names who appear (from known characters or detect new ones)
3. "location": Where the scene takes place (if identifiable)
4. "timestamp": When the scene occurs (e.g., "Morning", "Day 3", "1850", etc.) - only if explicitly mentioned
5. "event_type": One of: "SCENE", "CHAPTER", "FLASHBACK", "DREAM", "MONTAGE"
6. "key_events": List of 2-3 main actions/events that happen

Respond ONLY with valid JSON, no other text:
{{
  "description": "...",
  "characters": [...],
  "location": "..." or null,
  "timestamp": "..." or null,
  "event_type": "SCENE",
  "key_events": [...]
}}"""

    def _parse_scene_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse Claude's JSON response into scene data"""
        try:
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                # Convert to expected format
                return {
                    "description": data.get("description", ""),
                    "event_type": data.get("event_type", "SCENE"),
                    "timestamp": data.get("timestamp"),
                    "location": data.get("location"),
                    "characters": data.get("characters", []),
                    "metadata": {
                        "key_events": data.get("key_events", [])
                    }
                }
            return None
        except Exception as e:
            print(f"⚠️  Failed to parse scene response: {e}")
            return None

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

            # Check for flashback indicators using conservative detection
            if self._detect_flashback_conservative(paragraph):
                event_type = "FLASHBACK"
            else:
                event_type = "SCENE"

            # Extract characters mentioned in paragraph
            para_doc = self.nlp(paragraph[:1000])  # Limit to first 1000 chars for performance

            # Use NER fallback for character detection
            characters_in_para, detected_persons = self._detect_characters_with_ner(
                para_doc,
                entity_lookup
            )

            # Extract location
            location_in_para = None
            for token in para_doc:
                token_lower = token.text.lower()
                if token_lower in entity_lookup:
                    entity = entity_lookup[token_lower]
                    if entity.get("type") == "LOCATION" and not location_in_para:
                        location_in_para = entity["name"]

            # Extract timestamp
            timestamp = self._extract_timestamp(paragraph)

            # Detect scene transition
            prev_para = paragraphs[para_idx - 1] if para_idx > 0 else None
            has_transition = self._detect_scene_transition(paragraph, prev_para)

            # Check for location change (indicates new scene)
            prev_location = None
            if para_idx > 0 and len(events) > 0:
                prev_location = events[-1].get("location")
            location_changed = (location_in_para and prev_location and
                              location_in_para != prev_location)

            # Check for character set change (major cast change = new scene)
            character_set_changed = False
            if para_idx > 0 and len(events) > 0:
                prev_chars = set(events[-1].get("characters", []))
                current_chars = set(characters_in_para)
                # If less than 30% overlap in characters, likely a new scene
                if prev_chars and current_chars:
                    overlap = len(prev_chars & current_chars) / max(len(prev_chars), len(current_chars))
                    character_set_changed = overlap < 0.3

            # SIMPLIFIED: Create events more liberally for usability
            # Users can always delete unwanted events, but missing events is frustrating
            is_scene_boundary = (
                para_idx == 0 or  # First paragraph always
                has_transition or  # Explicit transitions
                location_changed or  # Location change
                character_set_changed or  # Character change
                timestamp is not None or  # Time jump
                (para_idx % 5 == 0)  # Every 5th paragraph as checkpoint
            )

            # Create event if it has meaningful content AND is a scene boundary
            if len(paragraph.strip()) > 50 and is_scene_boundary:
                # Use first sentence as description
                first_sentence = list(para_doc.sents)[0].text.strip() if list(para_doc.sents) else paragraph[:100]

                # Extract actions and emotional context
                actions = self._extract_actions(paragraph)
                emotional_context = self._extract_emotional_context(paragraph)

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
                        "has_transition": has_transition,
                        "location_changed": location_changed,
                        "character_set_changed": character_set_changed,
                        "detected_persons": detected_persons  # Unregistered characters from NER
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

        # Extract events using intelligent LLM-based extraction (falls back to basic if unavailable)
        events = self.extract_scenes_with_llm(text, manuscript_id, known_entities)

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
