"""
Thesaurus Service
Provides synonym lookups using NLTK WordNet via TextBlob
"""

from typing import List, Dict, Optional
from collections import defaultdict


class ThesaurusService:
    """Service for looking up synonyms and related words"""

    def __init__(self):
        self._wordnet_available = False
        self._wn = None
        self._initialize_wordnet()

    def _initialize_wordnet(self):
        """Initialize WordNet from NLTK"""
        try:
            from nltk.corpus import wordnet as wn
            # Test that WordNet data is available
            wn.synsets('test')
            self._wn = wn
            self._wordnet_available = True
            print("📚 Thesaurus service initialized (WordNet)")
        except Exception as e:
            print(f"⚠️  Thesaurus service limited (WordNet not available): {e}")
            self._wordnet_available = False

    def is_available(self) -> bool:
        """Check if thesaurus functionality is available"""
        return self._wordnet_available

    def get_synonyms(
        self,
        word: str,
        max_results: int = 20,
        include_pos: bool = True
    ) -> Dict[str, any]:
        """
        Get synonyms for a word, organized by part of speech

        Args:
            word: The word to look up
            max_results: Maximum number of synonyms per category
            include_pos: Include part of speech information

        Returns:
            Dictionary with synonyms grouped by part of speech
        """
        word = word.lower().strip()

        if not word:
            return {"word": word, "synonyms": [], "found": False}

        if not self._wordnet_available:
            return self._fallback_synonyms(word)

        try:
            synsets = self._wn.synsets(word)

            if not synsets:
                return {"word": word, "synonyms": [], "found": False}

            # Organize by part of speech
            pos_map = {
                'n': 'noun',
                'v': 'verb',
                'a': 'adjective',
                's': 'adjective',  # satellite adjective
                'r': 'adverb'
            }

            synonyms_by_pos = defaultdict(set)
            definitions_by_pos = {}

            for synset in synsets:
                pos = synset.pos()
                pos_name = pos_map.get(pos, 'other')

                # Get lemmas (synonyms) from this synset
                for lemma in synset.lemmas():
                    lemma_name = lemma.name().replace('_', ' ')
                    # Don't include the original word
                    if lemma_name.lower() != word:
                        synonyms_by_pos[pos_name].add(lemma_name)

                # Store first definition for each POS
                if pos_name not in definitions_by_pos:
                    definitions_by_pos[pos_name] = synset.definition()

            # Convert to list format and limit results
            result_groups = []
            for pos_name in ['verb', 'noun', 'adjective', 'adverb']:
                if pos_name in synonyms_by_pos:
                    synonyms_list = list(synonyms_by_pos[pos_name])[:max_results]
                    if synonyms_list:
                        result_groups.append({
                            "part_of_speech": pos_name,
                            "definition": definitions_by_pos.get(pos_name, ""),
                            "words": sorted(synonyms_list)
                        })

            # Also get antonyms for reference
            antonyms = self._get_antonyms(word)

            return {
                "word": word,
                "found": len(result_groups) > 0,
                "groups": result_groups,
                "antonyms": antonyms[:10] if antonyms else []
            }

        except Exception as e:
            print(f"Thesaurus lookup error: {e}")
            return {"word": word, "synonyms": [], "found": False, "error": str(e)}

    def _get_antonyms(self, word: str) -> List[str]:
        """Get antonyms for a word"""
        if not self._wordnet_available:
            return []

        antonyms = set()
        try:
            for synset in self._wn.synsets(word):
                for lemma in synset.lemmas():
                    if lemma.antonyms():
                        for ant in lemma.antonyms():
                            antonyms.add(ant.name().replace('_', ' '))
        except Exception:
            pass
        return list(antonyms)

    def _fallback_synonyms(self, word: str) -> Dict[str, any]:
        """
        Fallback when WordNet is not available
        Returns a basic response with common writing synonyms
        """
        # Basic fallback for very common words
        common_synonyms = {
            "good": ["excellent", "great", "fine", "wonderful", "superb"],
            "bad": ["poor", "terrible", "awful", "dreadful", "horrible"],
            "big": ["large", "huge", "enormous", "vast", "immense"],
            "small": ["tiny", "little", "minute", "diminutive", "petite"],
            "happy": ["joyful", "pleased", "delighted", "content", "cheerful"],
            "sad": ["unhappy", "sorrowful", "melancholy", "gloomy", "dejected"],
            "said": ["stated", "replied", "remarked", "mentioned", "declared"],
            "walked": ["strolled", "marched", "strode", "trudged", "ambled"],
            "looked": ["gazed", "stared", "glanced", "peered", "observed"],
            "beautiful": ["gorgeous", "stunning", "lovely", "attractive", "elegant"],
        }

        if word in common_synonyms:
            return {
                "word": word,
                "found": True,
                "groups": [{
                    "part_of_speech": "general",
                    "definition": "",
                    "words": common_synonyms[word]
                }],
                "antonyms": [],
                "fallback": True
            }

        return {"word": word, "synonyms": [], "found": False, "fallback": True}

    def get_related_words(self, word: str, max_results: int = 10) -> Dict[str, any]:
        """
        Get related words including hypernyms and hyponyms

        Args:
            word: The word to look up
            max_results: Maximum results per category

        Returns:
            Dictionary with related words by relationship type
        """
        if not self._wordnet_available:
            return {"word": word, "found": False}

        word = word.lower().strip()

        try:
            synsets = self._wn.synsets(word)
            if not synsets:
                return {"word": word, "found": False}

            # Get the most common synset
            primary_synset = synsets[0]

            # Hypernyms (more general terms)
            hypernyms = set()
            for hyper in primary_synset.hypernyms():
                for lemma in hyper.lemmas():
                    hypernyms.add(lemma.name().replace('_', ' '))

            # Hyponyms (more specific terms)
            hyponyms = set()
            for hypo in primary_synset.hyponyms():
                for lemma in hypo.lemmas():
                    hyponyms.add(lemma.name().replace('_', ' '))

            # Meronyms (parts)
            meronyms = set()
            for mero in primary_synset.part_meronyms():
                for lemma in mero.lemmas():
                    meronyms.add(lemma.name().replace('_', ' '))

            # Holonyms (wholes)
            holonyms = set()
            for holo in primary_synset.part_holonyms():
                for lemma in holo.lemmas():
                    holonyms.add(lemma.name().replace('_', ' '))

            return {
                "word": word,
                "found": True,
                "definition": primary_synset.definition(),
                "broader_terms": list(hypernyms)[:max_results],
                "narrower_terms": list(hyponyms)[:max_results],
                "parts": list(meronyms)[:max_results],
                "part_of": list(holonyms)[:max_results]
            }

        except Exception as e:
            print(f"Related words lookup error: {e}")
            return {"word": word, "found": False, "error": str(e)}


# Singleton instance
thesaurus_service = ThesaurusService()
