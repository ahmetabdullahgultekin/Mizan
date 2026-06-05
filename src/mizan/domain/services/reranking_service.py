"""
Re-ranking Service Interface (Port).

Defines the contract for re-ranking search results using cross-encoder models.
Implementations are provided by the infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class IRerankerService(ABC):
    """
    Port for cross-encoder re-ranking.

    Cross-encoders score (query, document) pairs jointly, producing
    much more accurate relevance scores than bi-encoder similarity.

    Implementations:
    - CrossEncoderRerankerService (local, offline via sentence-transformers)
    """

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int | None = None,
    ) -> list[tuple[int, float]]:
        """
        Re-rank documents by relevance to query.

        Args:
            query: The search query text.
            documents: List of document texts to re-rank.
            top_k: If set, return only the top-k results.

        Returns:
            List of (original_index, score) tuples sorted by score descending.
            Scores are normalized to 0-1 range via sigmoid.
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier of the underlying re-ranking model."""
        ...

    @property
    def is_multilingual(self) -> bool:
        """Whether the reranker can score non-English (e.g. Arabic/Turkish)
        (query, document) pairs meaningfully.

        Callers use this to decide whether to feed language-matched native text
        (Arabic verse text, Turkish translation) to the reranker for non-English
        queries. An English-only cross-encoder returns ``False`` so the search
        service does not feed it text it cannot score. Defaults to ``False`` for
        safety; multilingual implementations override it.
        """
        return False
