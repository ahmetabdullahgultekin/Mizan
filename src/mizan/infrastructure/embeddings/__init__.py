"""
Infrastructure: Embedding Services.

Provides concrete implementations of IEmbeddingService:
- SentenceTransformerEmbeddingService: local, offline (recommended)
- GeminiEmbeddingService: Google Gemini API (optional)
"""

from mizan.infrastructure.embeddings.sentence_transformer_service import (
    SentenceTransformerEmbeddingService,
    get_local_embedding_service,
)
from mizan.infrastructure.embeddings.gemini_embedding_service import (
    GeminiEmbeddingService,
    get_gemini_embedding_service,
)

__all__ = [
    "SentenceTransformerEmbeddingService",
    "get_local_embedding_service",
    "GeminiEmbeddingService",
    "get_gemini_embedding_service",
]
