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
            "stats": stats
        }

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


# Global instance
nlp_service = NLPService()
