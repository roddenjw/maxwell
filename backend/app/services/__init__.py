"""
Services for backend functionality
"""

# Import version_service (no external dependencies beyond pygit2)
from app.services.version_service import version_service, VersionService

# Import codex_service (no external dependencies beyond SQLAlchemy)
from app.services.codex_service import codex_service, CodexService

# Import timeline_service (no external dependencies beyond SQLAlchemy)
from app.services.timeline_service import timeline_service, TimelineService

# Optional imports for ML services (require chromadb, kuzu which need Python < 3.13)
try:
    from app.services.embedding_service import embedding_service, EmbeddingService
    EMBEDDING_AVAILABLE = True
except ImportError:
    embedding_service = None
    EmbeddingService = None
    EMBEDDING_AVAILABLE = False

try:
    from app.services.graph_service import graph_service, GraphService
    GRAPH_AVAILABLE = True
except ImportError:
    graph_service = None
    GraphService = None
    GRAPH_AVAILABLE = False

__all__ = [
    "codex_service",
    "CodexService",
    "timeline_service",
    "TimelineService",
    "embedding_service",
    "EmbeddingService",
    "graph_service",
    "GraphService",
    "version_service",
    "VersionService",
    "EMBEDDING_AVAILABLE",
    "GRAPH_AVAILABLE",
]
