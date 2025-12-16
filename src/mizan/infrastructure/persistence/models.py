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
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mizan.infrastructure.persistence.database import Base

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
