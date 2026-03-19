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

import structlog

from mizan.domain.services.reranking_service import IRerankerService

logger = structlog.get_logger(__name__)


class CrossEncoderRerankerService(IRerankerService):
    """
    Re-ranking service backed by a cross-encoder model (local, offline).

    The model is loaded lazily on first use and cached in memory.
    All heavy computation runs in a thread pool to avoid blocking the
    async event loop.

    Gracefully handles OOM and model-loading failures by falling back
    to the original ordering (no reranking) rather than crashing.

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
        self._load_failed: bool = False

    def _load_model(self) -> Any | None:
        """Load the cross-encoder model (blocking, cached).

        Returns None if the model cannot be loaded (e.g. OOM, missing deps).
        Subsequent calls after a failure return None immediately.
        """
        if self._load_failed:
            return None

        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError:
                logger.warning(
                    "reranker_import_failed",
                    detail="sentence-transformers not installed; reranking disabled",
                )
                self._load_failed = True
                return None

            try:
                # trust_remote_code needed for some models (e.g., jina-reranker)
                self._model = CrossEncoder(
                    self._model_name,
                    trust_remote_code="jina" in self._model_name.lower(),
                )
                logger.info(
                    "reranker_model_loaded",
                    model=self._model_name,
                )
            except MemoryError:
                logger.warning(
                    "reranker_oom",
                    model=self._model_name,
                    detail="Out of memory loading cross-encoder; reranking disabled",
                )
                self._load_failed = True
                return None
            except Exception as exc:
                logger.warning(
                    "reranker_load_error",
                    model=self._model_name,
                    error=str(exc),
                    detail="Failed to load cross-encoder model; reranking disabled",
                )
                self._load_failed = True
                return None

        return self._model

    @staticmethod
    def _sigmoid(x: float) -> float:
        """Map raw cross-encoder score to 0-1 via sigmoid."""
        return 1.0 / (1.0 + math.exp(-x))

    @property
    def is_available(self) -> bool:
        """Return True if the reranker model is loaded and usable."""
        if self._model is None and not self._load_failed:
            self._load_model()
        return self._model is not None and not self._load_failed

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

        Gracefully returns identity ordering on OOM or model failure.
        """
        if not documents:
            return []

        loop = asyncio.get_event_loop()

        def _score() -> list[tuple[int, float]] | None:
            model = self._load_model()
            if model is None:
                return None
            try:
                pairs = [[query, doc] for doc in documents]
                raw_scores = model.predict(pairs)
                # Normalize via sigmoid and pair with original index
                indexed = [(i, self._sigmoid(float(score))) for i, score in enumerate(raw_scores)]
                indexed.sort(key=lambda x: x[1], reverse=True)
                if top_k is not None:
                    indexed = indexed[:top_k]
                return indexed
            except MemoryError:
                logger.warning(
                    "reranker_oom_during_predict",
                    query=query[:80],
                    num_docs=len(documents),
                    detail="OOM during reranking; returning original order",
                )
                return None
            except Exception as exc:
                logger.warning(
                    "reranker_predict_error",
                    error=str(exc),
                    detail="Reranking failed; returning original order",
                )
                return None

        result = await loop.run_in_executor(None, _score)
        if result is None:
            # Fallback: return identity ordering so search still works
            effective_k = top_k if top_k is not None else len(documents)
            return [(i, 0.0) for i in range(min(effective_k, len(documents)))]
        return result

    @property
    def model_name(self) -> str:
        return self._model_name
