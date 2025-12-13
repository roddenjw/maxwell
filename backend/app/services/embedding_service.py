"""
Embedding and vector search service using ChromaDB
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import os
from pathlib import Path

# Initialize data directory
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
CHROMA_DIR = DATA_DIR / "chroma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)


class EmbeddingService:
    """Service for managing embeddings and vector search"""

    def __init__(self):
        # Initialize sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Collection names
        self.SCENES_COLLECTION = "scene_embeddings"
        self.ENTITIES_COLLECTION = "entity_embeddings"
        self.COACH_MEMORY_PREFIX = "coach_memory"

    def get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.client.get_collection(name)
        except Exception:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a text"""
        return self.model.encode(text).tolist()

    def add_scene_embedding(
        self,
        scene_id: str,
        scene_text: str,
        manuscript_id: str,
        metadata: Dict[str, Any] = None
    ):
        """Add or update scene embedding"""
        collection = self.get_or_create_collection(self.SCENES_COLLECTION)

        embedding = self.embed_text(scene_text)

        metadata = metadata or {}
        metadata.update({
            "manuscript_id": manuscript_id,
            "scene_id": scene_id
        })

        collection.add(
            embeddings=[embedding],
            documents=[scene_text[:1000]],  # Store truncated text
            ids=[scene_id],
            metadatas=[metadata]
        )

    def find_similar_scenes(
        self,
        query: str,
        manuscript_id: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Find similar scenes using vector search"""
        collection = self.get_or_create_collection(self.SCENES_COLLECTION)

        query_embedding = self.embed_text(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            where={"manuscript_id": manuscript_id},
            n_results=top_k
        )

        # Format results
        similar_scenes = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                similar_scenes.append({
                    "scene_id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None,
                    "metadata": results['metadatas'][0][i] if 'metadatas' in results else {}
                })

        return similar_scenes

    def add_entity_embedding(
        self,
        entity_id: str,
        entity_data: str,
        manuscript_id: str,
        metadata: Dict[str, Any] = None
    ):
        """Add or update entity embedding"""
        collection = self.get_or_create_collection(self.ENTITIES_COLLECTION)

        embedding = self.embed_text(entity_data)

        metadata = metadata or {}
        metadata.update({
            "manuscript_id": manuscript_id,
            "entity_id": entity_id
        })

        collection.add(
            embeddings=[embedding],
            documents=[entity_data],
            ids=[entity_id],
            metadatas=[metadata]
        )

    def search_entities(
        self,
        query: str,
        manuscript_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for entities by semantic similarity"""
        collection = self.get_or_create_collection(self.ENTITIES_COLLECTION)

        query_embedding = self.embed_text(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            where={"manuscript_id": manuscript_id},
            n_results=top_k
        )

        # Format results
        entities = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                entities.append({
                    "entity_id": results['ids'][0][i],
                    "data": results['documents'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None,
                    "metadata": results['metadatas'][0][i] if 'metadatas' in results else {}
                })

        return entities

    def get_user_memory_collection(self, user_id: str):
        """Get or create user-specific memory collection for The Coach"""
        collection_name = f"{self.COACH_MEMORY_PREFIX}_{user_id}"
        return self.get_or_create_collection(collection_name)

    def add_coaching_memory(
        self,
        user_id: str,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Store a coaching interaction in user's long-term memory"""
        import uuid

        collection = self.get_user_memory_collection(user_id)
        embedding = self.embed_text(text)

        memory_id = str(uuid.uuid4())
        metadata = metadata or {}

        collection.add(
            embeddings=[embedding],
            documents=[text],
            ids=[memory_id],
            metadatas=[metadata]
        )

        return memory_id

    def search_coaching_memory(
        self,
        user_id: str,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Search user's coaching memory for relevant past interactions"""
        collection = self.get_user_memory_collection(user_id)

        query_embedding = self.embed_text(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Format results
        memories = []
        if results and results['documents']:
            for i in range(len(results['documents'][0])):
                memories.append({
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None,
                    "metadata": results['metadatas'][0][i] if 'metadatas' in results else {}
                })

        return memories

    def delete_scene_embedding(self, scene_id: str):
        """Delete a scene embedding"""
        collection = self.get_or_create_collection(self.SCENES_COLLECTION)
        try:
            collection.delete(ids=[scene_id])
        except Exception:
            pass  # Already deleted or doesn't exist

    def delete_manuscript_embeddings(self, manuscript_id: str):
        """Delete all embeddings for a manuscript"""
        scenes_collection = self.get_or_create_collection(self.SCENES_COLLECTION)
        entities_collection = self.get_or_create_collection(self.ENTITIES_COLLECTION)

        # Delete scenes
        try:
            scenes_collection.delete(where={"manuscript_id": manuscript_id})
        except Exception:
            pass

        # Delete entities
        try:
            entities_collection.delete(where={"manuscript_id": manuscript_id})
        except Exception:
            pass


# Global instance
embedding_service = EmbeddingService()
