"""Library spaces, text sources, text chunks, and verse embeddings.

Adds the Islamic Knowledge Library system with pgvector support for
semantic search across Quran, Tafsir, Hadith, and other Islamic texts.

Revision ID: 0002_library_and_embeddings
Revises: 0001_initial
Create Date: 2025-01-02

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_library_and_embeddings"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Embedding dimension for intfloat/multilingual-e5-base
EMBEDDING_DIM = 768


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # -------------------------------------------------------------------------
    # library_spaces
    # -------------------------------------------------------------------------
    op.create_table(
        "library_spaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_library_spaces_name", "library_spaces", ["name"])

    # -------------------------------------------------------------------------
    # text_sources
    # -------------------------------------------------------------------------
    op.create_table(
        "text_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("library_space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("title_arabic", sa.String(length=500), nullable=False),
        sa.Column("title_turkish", sa.String(length=500), nullable=True),
        sa.Column("title_english", sa.String(length=500), nullable=True),
        sa.Column("author", sa.String(length=300), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="PENDING"
        ),
        sa.Column("total_chunks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("indexed_chunks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding_model", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["library_space_id"], ["library_spaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_text_sources_library_space", "text_sources", ["library_space_id"]
    )
    op.create_index("ix_text_sources_type", "text_sources", ["source_type"])
    op.create_index("ix_text_sources_status", "text_sources", ["status"])

    # -------------------------------------------------------------------------
    # text_chunks  (with pgvector embedding column)
    # -------------------------------------------------------------------------
    op.create_table(
        "text_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text_source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("reference", sa.String(length=200), nullable=False),
        # pgvector column: stores 768-dimensional float vector
        sa.Column(
            "embedding",
            sa.Text().with_variant(
                sa.dialects.postgresql.ARRAY(sa.Float()),  # type: ignore[attr-defined]
                "postgresql",
            ),
            nullable=True,
        ),
        sa.Column(
            "metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False,
            server_default="{}"
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["text_source_id"], ["text_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Use raw SQL for the vector column type (pgvector syntax)
    op.execute(
        f"ALTER TABLE text_chunks "
        f"ALTER COLUMN embedding TYPE vector({EMBEDDING_DIM}) "
        f"USING embedding::vector({EMBEDDING_DIM})"
    )

    op.create_index("ix_text_chunks_source", "text_chunks", ["text_source_id"])
    op.create_index(
        "ix_text_chunks_source_index", "text_chunks", ["text_source_id", "chunk_index"]
    )

    # HNSW index for approximate nearest-neighbor search (cosine distance)
    # ef_construction=64 is a good default for accuracy/speed balance
    op.execute(
        "CREATE INDEX ix_text_chunks_embedding_hnsw ON text_chunks "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )

    # -------------------------------------------------------------------------
    # verse_embeddings  (semantic embeddings for existing Quran verses)
    # -------------------------------------------------------------------------
    op.create_table(
        "verse_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("surah_number", sa.Integer(), nullable=False),
        sa.Column("verse_number", sa.Integer(), nullable=False),
        sa.Column(
            "embedding",
            sa.Text().with_variant(
                sa.dialects.postgresql.ARRAY(sa.Float()),
                "postgresql",
            ),
            nullable=False,
        ),
        sa.Column("model_name", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["verse_id"], ["verses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("verse_id", "model_name", name="uq_verse_embedding_model"),
    )

    # Convert embedding column to native pgvector type
    op.execute(
        f"ALTER TABLE verse_embeddings "
        f"ALTER COLUMN embedding TYPE vector({EMBEDDING_DIM}) "
        f"USING embedding::vector({EMBEDDING_DIM})"
    )

    op.create_index("ix_verse_embeddings_verse_id", "verse_embeddings", ["verse_id"])
    op.create_index(
        "ix_verse_embeddings_location",
        "verse_embeddings",
        ["surah_number", "verse_number"],
    )
    op.create_index("ix_verse_embeddings_model", "verse_embeddings", ["model_name"])

    # HNSW index for verse similarity search
    op.execute(
        "CREATE INDEX ix_verse_embeddings_embedding_hnsw ON verse_embeddings "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.drop_index("ix_verse_embeddings_embedding_hnsw", table_name="verse_embeddings")
    op.drop_table("verse_embeddings")

    op.drop_index("ix_text_chunks_embedding_hnsw", table_name="text_chunks")
    op.drop_table("text_chunks")
    op.drop_table("text_sources")
    op.drop_table("library_spaces")

    op.execute("DROP EXTENSION IF EXISTS vector")
