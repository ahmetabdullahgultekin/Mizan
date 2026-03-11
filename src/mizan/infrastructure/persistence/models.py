"""
SQLAlchemy database models.

These models map domain entities to database tables with pre-computed fields
for performance optimization.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from pgvector.sqlalchemy import Vector
    _PGVECTOR_AVAILABLE = True
except ImportError:
    # Graceful fallback: store as JSON if pgvector not installed yet
    from sqlalchemy import JSON as Vector  # type: ignore[assignment]
    _PGVECTOR_AVAILABLE = False

from mizan.infrastructure.persistence.database import Base
from mizan.domain.enums.library_enums import IndexingStatus, SourceType

if TYPE_CHECKING:
    pass


class SurahModel(Base):
    """
    Database model for Surah metadata.

    Stores surah-level information with pre-computed aggregates.
    """

    __tablename__ = "surahs"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)

    # Names
    name_arabic: Mapped[str] = mapped_column(String(100), nullable=False)
    name_english: Mapped[str] = mapped_column(String(100), nullable=False)
    name_transliteration: Mapped[str] = mapped_column(String(100), nullable=False)

    # Classification
    revelation_type: Mapped[str] = mapped_column(String(20), nullable=False)  # meccan/medinan
    revelation_order: Mapped[int] = mapped_column(Integer, nullable=False)
    basmalah_status: Mapped[str] = mapped_column(String(30), nullable=False)

    # Counts
    verse_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ruku_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Pre-computed aggregates (for performance)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    letter_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    abjad_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Integrity
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    verses: Mapped[list["VerseModel"]] = relationship(
        "VerseModel", back_populates="surah", lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index("ix_surahs_revelation_type", "revelation_type"),
        Index("ix_surahs_revelation_order", "revelation_order"),
    )

    def __repr__(self) -> str:
        return f"<Surah {self.id}: {self.name_arabic}>"


class VerseModel(Base):
    """
    Database model for verses (ayat).

    Stores verse content in multiple scripts with pre-computed analysis values.
    """

    __tablename__ = "verses"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Location (composite unique)
    surah_number: Mapped[int] = mapped_column(
        Integer, ForeignKey("surahs.id"), nullable=False
    )
    verse_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Text content (multiple scripts)
    text_uthmani: Mapped[str] = mapped_column(Text, nullable=False)
    text_uthmani_min: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_simple: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Pre-computed normalized forms (for fast search)
    text_normalized_full: Mapped[str] = mapped_column(Text, nullable=False)
    text_no_tashkeel: Mapped[str] = mapped_column(Text, nullable=False)

    # Qira'at variants stored as JSON
    qiraat_variants: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Structural divisions
    juz_number: Mapped[int] = mapped_column(Integer, nullable=False)
    hizb_number: Mapped[int] = mapped_column(Integer, nullable=False)
    ruku_number: Mapped[int] = mapped_column(Integer, nullable=False)
    manzil_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Sajdah information
    is_sajdah: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sajdah_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Pre-computed counts (for performance - 100x faster queries)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    letter_count: Mapped[int] = mapped_column(Integer, nullable=False)
    abjad_value_mashriqi: Mapped[int] = mapped_column(Integer, nullable=False)
    abjad_value_maghribi: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Integrity
    checksum: Mapped[str] = mapped_column(String(128), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    surah: Mapped["SurahModel"] = relationship("SurahModel", back_populates="verses")
    morphology: Mapped[list["MorphologyModel"]] = relationship(
        "MorphologyModel", back_populates="verse", lazy="selectin"
    )

    # Indexes for common queries
    __table_args__ = (
        UniqueConstraint("surah_number", "verse_number", name="uq_verse_location"),
        Index("ix_verses_surah_verse", "surah_number", "verse_number"),
        Index("ix_verses_juz", "juz_number"),
        Index("ix_verses_hizb", "hizb_number"),
        Index("ix_verses_manzil", "manzil_number"),
        Index("ix_verses_page", "page_number"),
        Index("ix_verses_sajdah", "is_sajdah"),
        # Full-text search on normalized text
        Index(
            "ix_verses_text_normalized",
            "text_normalized_full",
            postgresql_using="gin",
            postgresql_ops={"text_normalized_full": "gin_trgm_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<Verse {self.surah_number}:{self.verse_number}>"


class MorphologyModel(Base):
    """
    Database model for morphological analysis data.

    Stores MASAQ dataset entries for word-level analysis.
    """

    __tablename__ = "morphology"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Location
    surah_number: Mapped[int] = mapped_column(Integer, nullable=False)
    verse_number: Mapped[int] = mapped_column(Integer, nullable=False)
    word_number: Mapped[int] = mapped_column(Integer, nullable=False)
    segment_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Foreign key to verse
    verse_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("verses.id"), nullable=False
    )

    # Text forms
    word_uthmani: Mapped[str] = mapped_column(String(100), nullable=False)
    word_imlaei: Mapped[str] = mapped_column(String(100), nullable=False)
    segment_uthmani: Mapped[str | None] = mapped_column(String(50), nullable=True)
    segment_imlaei: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Morphological analysis
    morpheme_type: Mapped[str] = mapped_column(String(20), nullable=False)  # STEM, PREFIX, SUFFIX
    pos_tag: Mapped[str] = mapped_column(String(20), nullable=False)
    root: Mapped[str | None] = mapped_column(String(20), nullable=True)
    lemma: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pattern: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Grammatical features
    person: Mapped[str | None] = mapped_column(String(5), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(5), nullable=True)
    number: Mapped[str | None] = mapped_column(String(5), nullable=True)
    case_state: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mood_voice: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Syntactic information
    syntactic_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    irab_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    verse: Mapped["VerseModel"] = relationship("VerseModel", back_populates="morphology")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_morphology_location", "surah_number", "verse_number", "word_number"),
        Index("ix_morphology_root", "root"),
        Index("ix_morphology_lemma", "lemma"),
        Index("ix_morphology_pos", "pos_tag"),
        Index("ix_morphology_verse_id", "verse_id"),
    )

    def __repr__(self) -> str:
        return f"<Morphology {self.surah_number}:{self.verse_number}:{self.word_number}>"


# =============================================================================
# Islamic Knowledge Library Models (Tier 4 - Semantic Search)
# =============================================================================


class LibrarySpaceModel(Base):
    """
    Database model for a named collection of Islamic text sources.

    A library space groups related sources together (e.g., a research
    library containing Quran texts, Tafsir books, and Hadith collections).
    """

    __tablename__ = "library_spaces"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    sources: Mapped[list["TextSourceModel"]] = relationship(
        "TextSourceModel", back_populates="library_space", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_library_spaces_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<LibrarySpace {self.id}: {self.name}>"


class TextSourceModel(Base):
    """
    Database model for a single Islamic text source.

    Represents a book, collection, or dataset added to a library space.
    Tracks indexing progress (chunking + embedding generation).
    """

    __tablename__ = "text_sources"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    library_space_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("library_spaces.id"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # SourceType enum value
    title_arabic: Mapped[str] = mapped_column(String(500), nullable=False)
    title_turkish: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title_english: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=IndexingStatus.PENDING.value
    )  # IndexingStatus enum value
    total_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indexed_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    library_space: Mapped["LibrarySpaceModel"] = relationship(
        "LibrarySpaceModel", back_populates="sources"
    )
    chunks: Mapped[list["TextChunkModel"]] = relationship(
        "TextChunkModel", back_populates="source", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_text_sources_library_space", "library_space_id"),
        Index("ix_text_sources_type", "source_type"),
        Index("ix_text_sources_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<TextSource {self.id}: {self.title_arabic} [{self.status}]>"


class TextChunkModel(Base):
    """
    Database model for a segmented text chunk with its semantic embedding.

    For Quran: 1 chunk = 1 verse.
    For Tafsir/Hadith: paragraph or sliding-window segments (~300 words).
    The embedding column uses pgvector's VECTOR type for efficient similarity search.
    """

    __tablename__ = "text_chunks"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    text_source_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("text_sources.id"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[str] = mapped_column(String(200), nullable=False)
    # pgvector VECTOR(768) column for semantic embeddings
    # Using 768 dimensions (intfloat/multilingual-e5-base output size)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    source: Mapped["TextSourceModel"] = relationship(
        "TextSourceModel", back_populates="chunks"
    )

    __table_args__ = (
        Index("ix_text_chunks_source", "text_source_id"),
        Index("ix_text_chunks_source_index", "text_source_id", "chunk_index"),
        # HNSW index for fast approximate nearest-neighbor search
        # Created in migration with: USING hnsw (embedding vector_cosine_ops)
    )

    def __repr__(self) -> str:
        return f"<TextChunk {self.chunk_index}: {self.reference}>"


class VerseEmbeddingModel(Base):
    """
    Semantic embedding for a Quranic verse.

    Kept separate from VerseModel to avoid mixing ML artifacts with
    the pristine, integrity-verified Quran text tables.
    One verse can have multiple embeddings from different models.
    """

    __tablename__ = "verse_embeddings"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    verse_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("verses.id"), nullable=False
    )
    surah_number: Mapped[int] = mapped_column(Integer, nullable=False)
    verse_number: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    verse: Mapped["VerseModel"] = relationship("VerseModel")

    __table_args__ = (
        UniqueConstraint("verse_id", "model_name", name="uq_verse_embedding_model"),
        Index("ix_verse_embeddings_verse_id", "verse_id"),
        Index("ix_verse_embeddings_location", "surah_number", "verse_number"),
        Index("ix_verse_embeddings_model", "model_name"),
        # HNSW index for fast ANN search created in migration
    )
