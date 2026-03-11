"""
Repository Interfaces for the Islamic Knowledge Library system.

These ports define data access contracts for library spaces,
text sources, chunks, and verse embeddings.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from mizan.domain.entities.library import (
    LibrarySpace,
    SemanticSearchResult,
    TextChunk,
    TextSource,
    VerseEmbedding,
)
from mizan.domain.enums.library_enums import IndexingStatus, SourceType


class ILibrarySpaceRepository(ABC):
    """Port for LibrarySpace persistence."""

    @abstractmethod
    async def create(self, space: LibrarySpace) -> LibrarySpace:
        """Persist a new library space."""
        ...

    @abstractmethod
    async def get_by_id(self, space_id: UUID) -> LibrarySpace | None:
        """Retrieve a library space by ID."""
        ...

    @abstractmethod
    async def get_all(self) -> list[LibrarySpace]:
        """Retrieve all library spaces."""
        ...

    @abstractmethod
    async def delete(self, space_id: UUID) -> bool:
        """Delete a library space and all its sources. Returns True if found."""
        ...


class ITextSourceRepository(ABC):
    """Port for TextSource persistence."""

    @abstractmethod
    async def create(self, source: TextSource) -> TextSource:
        """Persist a new text source."""
        ...

    @abstractmethod
    async def get_by_id(self, source_id: UUID) -> TextSource | None:
        """Retrieve a text source by ID."""
        ...

    @abstractmethod
    async def get_by_space(
        self,
        space_id: UUID,
        source_type: SourceType | None = None,
    ) -> list[TextSource]:
        """Retrieve all sources in a library space, optionally filtered by type."""
        ...

    @abstractmethod
    async def update_status(
        self,
        source_id: UUID,
        status: IndexingStatus,
        indexed_chunks: int | None = None,
        total_chunks: int | None = None,
        embedding_model: str | None = None,
    ) -> TextSource | None:
        """Update the indexing status of a source."""
        ...

    @abstractmethod
    async def delete(self, source_id: UUID) -> bool:
        """Delete a source and all its chunks. Returns True if found."""
        ...


class ITextChunkRepository(ABC):
    """Port for TextChunk persistence and vector search."""

    @abstractmethod
    async def create_batch(self, chunks: list[TextChunk]) -> list[TextChunk]:
        """Persist a batch of text chunks (without embeddings)."""
        ...

    @abstractmethod
    async def update_embedding(
        self,
        chunk_id: UUID,
        embedding: list[float],
    ) -> None:
        """Store the embedding vector for a chunk."""
        ...

    @abstractmethod
    async def update_embeddings_batch(
        self,
        updates: list[tuple[UUID, list[float]]],
    ) -> None:
        """Store embeddings for multiple chunks at once."""
        ...

    @abstractmethod
    async def get_by_source(self, source_id: UUID) -> list[TextChunk]:
        """Retrieve all chunks for a text source."""
        ...

    @abstractmethod
    async def semantic_search(
        self,
        query_embedding: list[float],
        library_space_id: UUID | None = None,
        source_types: list[SourceType] | None = None,
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> list[SemanticSearchResult]:
        """
        Find the most semantically similar chunks using cosine similarity.

        Args:
            query_embedding: Embedding of the search query
            library_space_id: Optional filter to a specific library
            source_types: Optional filter by source type(s)
            limit: Maximum number of results
            min_similarity: Minimum cosine similarity threshold (0.0-1.0)

        Returns:
            Ranked list of results (highest similarity first)
        """
        ...

    @abstractmethod
    async def delete_by_source(self, source_id: UUID) -> int:
        """Delete all chunks for a source. Returns number deleted."""
        ...


class IVerseEmbeddingRepository(ABC):
    """Port for VerseEmbedding persistence and verse similarity search."""

    @abstractmethod
    async def upsert(self, verse_embedding: VerseEmbedding) -> VerseEmbedding:
        """Insert or update a verse embedding."""
        ...

    @abstractmethod
    async def upsert_batch(self, embeddings: list[VerseEmbedding]) -> int:
        """Insert or update a batch of verse embeddings. Returns count."""
        ...

    @abstractmethod
    async def get_by_verse(
        self,
        surah_number: int,
        verse_number: int,
        model_name: str | None = None,
    ) -> VerseEmbedding | None:
        """Retrieve embedding for a specific verse."""
        ...

    @abstractmethod
    async def find_similar_verses(
        self,
        query_embedding: list[float],
        limit: int = 10,
        exclude_surah: int | None = None,
        exclude_verse: int | None = None,
    ) -> list[tuple[int, int, float]]:
        """
        Find verses most similar to a query embedding.

        Args:
            query_embedding: The reference embedding vector
            limit: Maximum results
            exclude_surah: Optionally exclude a specific surah (e.g., the query verse)
            exclude_verse: Optionally exclude a specific verse

        Returns:
            List of (surah_number, verse_number, similarity_score) tuples
        """
        ...

    @abstractmethod
    async def get_total_count(self, model_name: str | None = None) -> int:
        """Get total number of verse embeddings, optionally filtered by model."""
        ...
