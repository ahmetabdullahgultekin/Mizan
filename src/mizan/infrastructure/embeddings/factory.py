"""
Embedding service factory — selects provider based on config.
"""

from __future__ import annotations

from functools import lru_cache

from mizan.domain.services.embedding_service import IEmbeddingService
from mizan.infrastructure.config import get_settings


@lru_cache(maxsize=1)
def get_embedding_service() -> IEmbeddingService:
    """
    Create and return the configured embedding service (cached singleton).

    Reads embedding_provider from settings:
    - 'local'  → SentenceTransformerEmbeddingService (offline)
    - 'gemini' → GeminiEmbeddingService (Google API)
    """
    settings = get_settings()

    if settings.embedding_provider == "gemini":
        from mizan.infrastructure.embeddings.gemini_embedding_service import (
            GeminiEmbeddingService,
        )
        return GeminiEmbeddingService(
            api_key=settings.gemini_api_key,
            model_name=settings.embedding_model,
        )

    # Default: local sentence-transformers
    from mizan.infrastructure.embeddings.sentence_transformer_service import (
        SentenceTransformerEmbeddingService,
    )
    return SentenceTransformerEmbeddingService(model_name=settings.embedding_model)
