"""
Embedding service factory — selects provider based on config.

Supports three modes:

  EMBEDDING_PROVIDER=local          → SentenceTransformerEmbeddingService only
  EMBEDDING_PROVIDER=gemini         → GeminiEmbeddingService only
  EMBEDDING_PROVIDER=gemini + EMBEDDING_FALLBACK_PROVIDER=local
                                    → CascadeEmbeddingService (Gemini first, local on failure)

Both providers in cascade mode MUST use models with matching dimensions.
"""

from __future__ import annotations

from functools import lru_cache

from mizan.domain.services.embedding_service import IEmbeddingService
from mizan.infrastructure.config import Settings, get_settings


def _create_single_service(provider: str, model: str, settings: Settings) -> IEmbeddingService:
    """Instantiate a single embedding service for the given provider/model."""
    if provider == "gemini":
        from mizan.infrastructure.embeddings.gemini_embedding_service import (
            GeminiEmbeddingService,
        )
        return GeminiEmbeddingService(
            api_key=settings.gemini_api_key,
            model_name=model,
        )

    # Default: local sentence-transformers
    from mizan.infrastructure.embeddings.sentence_transformer_service import (
        SentenceTransformerEmbeddingService,
    )
    return SentenceTransformerEmbeddingService(model_name=model)


@lru_cache(maxsize=1)
def get_embedding_service() -> IEmbeddingService:
    """
    Create and return the configured embedding service (cached singleton).

    If EMBEDDING_FALLBACK_PROVIDER is set, returns a CascadeEmbeddingService
    that automatically retries with the fallback on any primary failure.
    """
    settings = get_settings()

    primary = _create_single_service(
        settings.embedding_provider,
        settings.embedding_model,
        settings,
    )

    if settings.embedding_fallback_provider:
        fallback = _create_single_service(
            settings.embedding_fallback_provider,
            settings.embedding_fallback_model,
            settings,
        )

        # Validate that both models produce the same embedding dimension.
        # Mismatched dimensions silently corrupt vector search at runtime.
        if primary.embedding_dimension != fallback.embedding_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: primary model '{settings.embedding_model}' "
                f"has dimension {primary.embedding_dimension}, but fallback model "
                f"'{settings.embedding_fallback_model}' has dimension {fallback.embedding_dimension}. "
                "Both models MUST have the same dimension for cascade mode to work."
            )

        from mizan.infrastructure.embeddings.cascade_service import CascadeEmbeddingService
        return CascadeEmbeddingService(primary=primary, fallback=fallback)

    return primary


def get_embedding_status() -> dict:
    """
    Return the current embedding configuration as a status dict.
    Suitable for the /health endpoint.
    """
    settings = get_settings()
    svc = get_embedding_service()

    from mizan.infrastructure.embeddings.cascade_service import CascadeEmbeddingService

    if isinstance(svc, CascadeEmbeddingService):
        return {
            "mode": "cascade",
            "primary": svc.primary_model,
            "fallback": svc.fallback_model,
            "currently_using_fallback": svc.is_using_fallback,
            "dimension": svc.dimension,
        }

    return {
        "mode": "single",
        "provider": settings.embedding_provider,
        "model": svc.model_name,
        "dimension": svc.dimension,
    }
