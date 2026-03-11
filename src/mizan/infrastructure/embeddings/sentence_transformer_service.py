"""
Local embedding service using sentence-transformers.

Uses intfloat/multilingual-e5-base by default — a state-of-the-art
multilingual model with strong Arabic support (both Classical and Modern),
running entirely offline without any API keys.

Model download (~280MB) happens automatically on first use.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache

from mizan.domain.services.embedding_service import IEmbeddingService


class SentenceTransformerEmbeddingService(IEmbeddingService):
    """
    Embedding service backed by sentence-transformers (local, offline).

    The model is loaded lazily on first use and cached in memory.
    All heavy computation runs in a thread pool to avoid blocking the
    async event loop.

    Recommended model: intfloat/multilingual-e5-base
    - 768 dimensions
    - 100+ languages including Arabic (Classical + Modern)
    - ~280MB disk space
    - No API key required
    """

    def __init__(self, model_name: str = "intfloat/multilingual-e5-base") -> None:
        self._model_name = model_name
        self._model: object | None = None
        self._dimension: int | None = None

    def _load_model(self) -> object:
        """Load the sentence-transformer model (blocking, cached)."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore[import]
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is not installed. "
                    "Install with: pip install sentence-transformers"
                ) from exc

            self._model = SentenceTransformer(self._model_name)
            # Cache the dimension
            test_emb = self._model.encode(["test"])  # type: ignore[union-attr]
            self._dimension = int(test_emb.shape[1])

        return self._model

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts.

        For multilingual-e5 models, queries should be prefixed with
        'query: ' and passages with 'passage: ' for best results.
        The indexing_service handles this prefixing automatically.
        """
        loop = asyncio.get_event_loop()

        def _encode() -> list[list[float]]:
            model = self._load_model()
            embeddings = model.encode(  # type: ignore[union-attr]
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return [emb.tolist() for emb in embeddings]

        return await loop.run_in_executor(None, _encode)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def embedding_dimension(self) -> int:
        if self._dimension is None:
            # Load model to get dimension
            self._load_model()
        return self._dimension or 768


@lru_cache(maxsize=1)
def get_local_embedding_service(model_name: str) -> SentenceTransformerEmbeddingService:
    """Get a cached instance of the local embedding service."""
    return SentenceTransformerEmbeddingService(model_name)
