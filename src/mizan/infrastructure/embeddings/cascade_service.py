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

import structlog

from mizan.domain.services.embedding_service import IEmbeddingService

logger = structlog.get_logger(__name__)


class CascadeEmbeddingService(IEmbeddingService):
    """
    Tries `primary` first; if it raises any exception, retries with `fallback`.

    Both services should produce vectors of the same dimension.
    A warning is logged whenever the fallback is used.
    """

    def __init__(self, primary: IEmbeddingService, fallback: IEmbeddingService) -> None:
        if primary.embedding_dimension != fallback.embedding_dimension:
            raise ValueError(
                f"Primary ({primary.model_name}, dim={primary.embedding_dimension}) and "
                f"fallback ({fallback.model_name}, dim={fallback.embedding_dimension}) must "
                f"have matching embedding dimensions. Vectors would be incompatible."
            )
        self._primary = primary
        self._fallback = fallback
        self._using_fallback: bool = False

    # ------------------------------------------------------------------
    # IEmbeddingService interface
    # ------------------------------------------------------------------

    @property
    def embedding_dimension(self) -> int:
        return self._primary.embedding_dimension

    @property
    def model_name(self) -> str:
        if self._using_fallback:
            return f"{self._fallback.model_name} [fallback]"
        return self._primary.model_name

    async def embed_text(self, text: str) -> list[float]:
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            result = await self._primary.embed_batch(texts)
            self._using_fallback = False
            return result
        except Exception as exc:
            logger.warning(
                "primary_embedding_failed",
                primary_model=self._primary.model_name,
                fallback_model=self._fallback.model_name,
                batch_size=len(texts),
                error=str(exc),
            )
            self._using_fallback = True
            return await self._fallback.embed_batch(texts)

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

    # Keep legacy alias for any code that accessed `.dimension` directly
    @property
    def dimension(self) -> int:
        return self.embedding_dimension
