"""
Cascade embedding service — tries a primary provider, falls back to secondary on failure.

This allows high-quality Gemini embeddings with local model as offline fallback:

    EMBEDDING_PROVIDER=gemini
    EMBEDDING_FALLBACK_PROVIDER=local

Both providers must use the SAME embedding dimension so vectors stay compatible.
Mixing models with different dimensions in the same index will break similarity search.

Recommended combinations:
  - gemini (768-dim)  + local multilingual-e5-base (768-dim) ✅
  - gemini (768-dim)  + local bge-m3 (1024-dim)              ❌  dimension mismatch
"""

from __future__ import annotations

import logging

from mizan.domain.services.embedding_service import IEmbeddingService

logger = logging.getLogger(__name__)


class CascadeEmbeddingService(IEmbeddingService):
    """
    Tries `primary` first; if it raises any exception, retries with `fallback`.

    Both services should produce vectors of the same dimension.
    A warning is logged whenever the fallback is used.
    """

    def __init__(self, primary: IEmbeddingService, fallback: IEmbeddingService) -> None:
        if primary.dimension != fallback.dimension:
            raise ValueError(
                f"Primary ({primary.model_name}, dim={primary.dimension}) and "
                f"fallback ({fallback.model_name}, dim={fallback.dimension}) must "
                f"have matching embedding dimensions. Vectors would be incompatible."
            )
        self._primary = primary
        self._fallback = fallback
        self._using_fallback: bool = False

    # ------------------------------------------------------------------
    # IEmbeddingService interface
    # ------------------------------------------------------------------

    @property
    def dimension(self) -> int:
        return self._primary.dimension

    @property
    def model_name(self) -> str:
        if self._using_fallback:
            return f"{self._fallback.model_name} [fallback]"
        return self._primary.model_name

    async def embed_text(self, text: str) -> list[float]:
        try:
            result = await self._primary.embed_text(text)
            self._using_fallback = False
            return result
        except Exception as exc:
            logger.warning(
                "Primary embedding service failed (%s). "
                "Falling back to %s. Error: %s",
                self._primary.model_name,
                self._fallback.model_name,
                exc,
            )
            self._using_fallback = True
            return await self._fallback.embed_text(text)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        try:
            result = await self._primary.embed_texts(texts)
            self._using_fallback = False
            return result
        except Exception as exc:
            logger.warning(
                "Primary embedding service failed for batch of %d texts (%s). "
                "Falling back to %s. Error: %s",
                len(texts),
                self._primary.model_name,
                self._fallback.model_name,
                exc,
            )
            self._using_fallback = True
            return await self._fallback.embed_texts(texts)

    # ------------------------------------------------------------------
    # Status helpers (for health endpoint)
    # ------------------------------------------------------------------

    @property
    def is_using_fallback(self) -> bool:
        """True if the last operation used the fallback provider."""
        return self._using_fallback

    @property
    def primary_model(self) -> str:
        return self._primary.model_name

    @property
    def fallback_model(self) -> str:
        return self._fallback.model_name
