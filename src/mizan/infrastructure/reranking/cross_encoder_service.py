"""
Cross-encoder re-ranking service using sentence-transformers.

Uses jinaai/jina-reranker-v2-base-multilingual by default — a fast
multilingual cross-encoder with strong Arabic support (MIRACL 78.69),
running entirely offline without any API keys.

Model download (~278MB) happens automatically on first use.
"""

from __future__ import annotations

import asyncio
import math
from typing import Any

from mizan.domain.services.reranking_service import IRerankerService


class CrossEncoderRerankerService(IRerankerService):
    """
    Re-ranking service backed by a cross-encoder model (local, offline).

    The model is loaded lazily on first use and cached in memory.
    All heavy computation runs in a thread pool to avoid blocking the
    async event loop.

    Recommended model: jinaai/jina-reranker-v2-base-multilingual
    - Best Arabic MIRACL score (78.69) among fast models
    - Supports 100+ languages including Arabic (Classical + Modern)
    - ~278MB disk space
    - Runs on CPU in <100ms for 30 candidates
    - No API key required
    """

    def __init__(
        self,
        model_name: str = "jinaai/jina-reranker-v2-base-multilingual",
    ) -> None:
        self._model_name = model_name
        self._model: Any = None

    def _load_model(self) -> Any:
        """Load the cross-encoder model (blocking, cached)."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as exc:
                raise RuntimeError(
                    "sentence-transformers is not installed. "
                    "Install with: pip install sentence-transformers"
                ) from exc

            # trust_remote_code needed for some models (e.g., jina-reranker)
            self._model = CrossEncoder(
                self._model_name,
                trust_remote_code="jina" in self._model_name.lower(),
            )

        return self._model

    @staticmethod
    def _sigmoid(x: float) -> float:
        """Map raw cross-encoder score to 0-1 via sigmoid."""
        return 1.0 / (1.0 + math.exp(-x))

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int | None = None,
    ) -> list[tuple[int, float]]:
        """
        Score each (query, document) pair and return sorted indices + scores.

        Scores are normalized to 0-1 via sigmoid so they can replace
        cosine similarity scores in search results.
        """
        if not documents:
            return []

        loop = asyncio.get_event_loop()

        def _score() -> list[tuple[int, float]]:
            model = self._load_model()
            pairs = [[query, doc] for doc in documents]
            raw_scores = model.predict(pairs)
            # Normalize via sigmoid and pair with original index
            indexed = [
                (i, self._sigmoid(float(score)))
                for i, score in enumerate(raw_scores)
            ]
            indexed.sort(key=lambda x: x[1], reverse=True)
            if top_k is not None:
                indexed = indexed[:top_k]
            return indexed

        return await loop.run_in_executor(None, _score)

    @property
    def model_name(self) -> str:
        return self._model_name
