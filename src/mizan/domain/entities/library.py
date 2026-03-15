"""
Domain entities for the Islamic Knowledge Library system.

These entities represent the core concepts of organizing and searching
Islamic texts (Quran, Tafsir, Hadith, etc.) using semantic embeddings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from mizan.domain.enums.library_enums import IndexingStatus, SourceType


@dataclass(frozen=True)
class LibrarySpace:
    """
    A named collection of Islamic text sources.

    Example: "Mizan Ana Kütüphanesi" containing Quran texts,
    Ibn Kathir Tafsir, and Sahih Bukhari.

    Attributes:
        id: Unique identifier
        name: Human-readable name
        description: Optional description
        created_at: Creation timestamp
    """

    id: UUID
    name: str
    description: str | None
    created_at: datetime

    @classmethod
    def create(cls, name: str, description: str | None = None) -> LibrarySpace:
        """Create a new library space with a generated UUID."""
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            created_at=datetime.utcnow(),
        )


@dataclass(frozen=True)
class TextSource:
    """
    A single Islamic text source within a library space.

    Represents a book, collection, or dataset (e.g., Quran Uthmani,
    Tafsir Ibn Kathir, Sahih Bukhari).

    Attributes:
        id: Unique identifier
        library_space_id: Parent library
        source_type: Type (QURAN, TAFSIR, HADITH, OTHER)
        title_arabic: Title in Arabic
        title_turkish: Title in Turkish (optional)
        title_english: Title in English (optional)
        author: Author name (optional)
        status: Current indexing status
        total_chunks: Total number of text chunks
        indexed_chunks: Number of chunks with embeddings
        embedding_model: Model name used for embeddings
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID
    library_space_id: UUID
    source_type: SourceType
    title_arabic: str
    title_turkish: str | None
    title_english: str | None
    author: str | None
    status: IndexingStatus
    total_chunks: int
    indexed_chunks: int
    embedding_model: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        library_space_id: UUID,
        source_type: SourceType,
        title_arabic: str,
        title_turkish: str | None = None,
        title_english: str | None = None,
        author: str | None = None,
    ) -> TextSource:
        """Create a new text source in PENDING status."""
        now = datetime.utcnow()
        return cls(
            id=uuid4(),
            library_space_id=library_space_id,
            source_type=source_type,
            title_arabic=title_arabic,
            title_turkish=title_turkish,
            title_english=title_english,
            author=author,
            status=IndexingStatus.PENDING,
            total_chunks=0,
            indexed_chunks=0,
            embedding_model=None,
            created_at=now,
            updated_at=now,
        )

    @property
    def is_fully_indexed(self) -> bool:
        """Whether all chunks have been embedded."""
        return self.status == IndexingStatus.INDEXED and self.total_chunks > 0

    @property
    def indexing_progress(self) -> float:
        """Indexing progress as a percentage (0.0-100.0)."""
        if self.total_chunks == 0:
            return 0.0
        return (self.indexed_chunks / self.total_chunks) * 100.0


@dataclass(frozen=True)
class TextChunk:
    """
    A segment of text from a source, with its semantic embedding.

    For Quran: one chunk = one verse (natural boundaries).
    For Tafsir/Hadith: paragraph or sliding-window segments.

    Attributes:
        id: Unique identifier
        text_source_id: Parent source
        chunk_index: Sequential position within the source
        content: The actual text content (Arabic)
        reference: Human-readable reference (e.g., '2:255', 'Bukhari 1:1')
        embedding: Semantic embedding vector (list of floats)
        metadata: Extra structured data (surah_no, verse_no, etc.)
        created_at: Creation timestamp
    """

    id: UUID
    text_source_id: UUID
    chunk_index: int
    content: str
    reference: str
    embedding: list[float] | None
    metadata: dict[str, Any]
    created_at: datetime

    @classmethod
    def create(
        cls,
        text_source_id: UUID,
        chunk_index: int,
        content: str,
        reference: str,
        metadata: dict[str, Any] | None = None,
    ) -> TextChunk:
        """Create a new text chunk without an embedding yet."""
        return cls(
            id=uuid4(),
            text_source_id=text_source_id,
            chunk_index=chunk_index,
            content=content,
            reference=reference,
            embedding=None,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
        )

    @property
    def has_embedding(self) -> bool:
        """Whether this chunk has been embedded."""
        return self.embedding is not None and len(self.embedding) > 0


@dataclass(frozen=True)
class VerseEmbedding:
    """
    Semantic embedding for a Quranic verse (linked to existing verses table).

    Kept separate from VerseModel to avoid polluting the pristine
    Quran text tables with ML artifacts.

    Attributes:
        id: Unique identifier
        verse_id: FK to verses.id
        surah_number: Denormalized for fast filtering
        verse_number: Denormalized for fast filtering
        embedding: The vector embedding
        model_name: Which model produced this embedding
        created_at: When this embedding was computed
    """

    id: UUID
    verse_id: UUID
    surah_number: int
    verse_number: int
    embedding: list[float]
    model_name: str
    created_at: datetime


@dataclass
class SemanticSearchResult:
    """
    A single result from semantic search.

    Attributes:
        chunk_id: ID of the matching chunk
        text_source_id: Parent source ID
        source_title: Human-readable source name
        source_type: Type of source
        reference: Reference string (e.g., '2:255')
        content: The matched text
        similarity_score: Cosine similarity (0.0-1.0, higher is better)
        metadata: Extra structured data from chunk
    """

    chunk_id: UUID
    text_source_id: UUID
    source_title: str
    source_type: SourceType
    reference: str
    content: str
    similarity_score: float
    metadata: dict[str, Any] = field(default_factory=dict)
