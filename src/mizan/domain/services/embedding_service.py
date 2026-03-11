"""
Embedding Service Interface (Port).

Defines the contract for generating semantic embeddings.
Implementations are provided by the infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class IEmbeddingService(ABC):
    """
    Port for semantic embedding generation.

    Implementations:
    - SentenceTransformerEmbeddingService (local, offline)
    - GeminiEmbeddingService (Google Gemini API)
    """

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """
        Generate a semantic embedding vector for a single text.

        Args:
            text: Text to embed (Arabic or multilingual)

        Returns:
            Embedding vector as a list of floats
        """
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts.

        More efficient than calling embed_text() in a loop.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors in the same order as input
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier of the underlying embedding model."""
        ...

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Dimensionality of the embedding vectors produced."""
        ...
