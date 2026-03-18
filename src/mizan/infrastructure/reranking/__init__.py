"""
Re-ranking service factory — returns the configured reranker (or None).

When ENABLE_RERANKING=true, provides a CrossEncoderRerankerService
that re-scores top candidates for dramatically improved result quality.
When disabled (default), returns None and search works as before.
"""

from __future__ import annotations

from functools import lru_cache

from mizan.domain.services.reranking_service import IRerankerService


@lru_cache(maxsize=1)
def get_reranker_service() -> IRerankerService | None:
    """
    Return the configured reranker if enabled, None otherwise (cached singleton).

    Controlled by:
    - ENABLE_RERANKING (bool, default False)
    - RERANKER_MODEL (str, default jinaai/jina-reranker-v2-base-multilingual)
    """
    from mizan.infrastructure.config import get_settings

    settings = get_settings()
    if not settings.enable_reranking:
        return None

    from mizan.infrastructure.reranking.cross_encoder_service import (
        CrossEncoderRerankerService,
    )

    return CrossEncoderRerankerService(model_name=settings.reranker_model)
